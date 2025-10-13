"""
Longest Backtest Service for pyHaasAPI v2

This service integrates the longest backtest algorithm from the CLI
into the orchestrator workflow for cutoff discovery.
"""

import asyncio
import time
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta

from ..core.logging import get_logger
from ..exceptions import LabError, LabExecutionError
from ..api.lab.lab_api import LabAPI
from ..api.market.market_api import MarketAPI
from ..api.backtest.backtest_api import BacktestAPI
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager
from .lab_clone_manager import LabCloneManager
from .lab_config_manager import LabConfigManager
from .sync_history_manager import SyncHistoryManager
from ..models.lab import StartLabExecutionRequest, LabExecutionUpdate

logger = get_logger("longest_backtest_service")


class LongestBacktestService:
    """
    Service for finding the longest working backtest period using the proven algorithm.
    
    This implements the EXACT algorithm from the CLI:
    1. Start with 36 months → if QUEUED, decrease by couple months
    2. When RUNNING → increase by week until QUEUED again
    3. Then decrease by 5 days until RUNNING again
    4. Then increase by 2 days until QUEUED again
    5. Then decrease by 1 day until RUNNING again
    6. DONE! - that's the longest working period
    """
    
    def __init__(self, lab_api: LabAPI, market_api: Optional[MarketAPI] = None, backtest_api: Optional[BacktestAPI] = None, client: Optional[AsyncHaasClient] = None, auth_manager: Optional[AuthenticationManager] = None):
        self.lab_api = lab_api
        self.market_api = market_api
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("longest_backtest_service")
        self.logger.info(f"🔍 LongestBacktestService initialized with client: {client is not None}, auth_manager: {auth_manager is not None}")
        # Optional helpers - will be created when needed
        self._clone_manager = None
        self._config_manager = None
        self.backtest_api = backtest_api
    
    @property
    def clone_manager(self) -> LabCloneManager:
        """Get or create clone manager with client and auth_manager"""
        if self._clone_manager is None:
            self.logger.info(f"🔍 Creating clone manager with client: {self.client is not None}, auth_manager: {self.auth_manager is not None}")
            self._clone_manager = LabCloneManager(self.lab_api, self.client, self.auth_manager)
        return self._clone_manager
    
    @property
    def config_manager(self) -> Optional[LabConfigManager]:
        """Get or create config manager with client and auth_manager"""
        if self._config_manager is None and self.market_api:
            self._config_manager = LabConfigManager(self.lab_api, self.market_api, self.client, self.auth_manager)
        return self._config_manager
    
    async def force_cancel_backtest(self, lab_id: str) -> bool:
        """Force cancel any existing backtest using v2 APIs."""
        try:
            self.logger.info(f"🛑 Force canceling any existing backtest for lab {lab_id}")
            
            # Use v2 API to cancel backtest
            try:
                await self.lab_api.cancel_lab_execution(lab_id)
                await asyncio.sleep(2)
                
                # Check if it's actually canceled
                status = await self.lab_api.get_lab_execution_status(lab_id)
                if status and status not in ['queued', 'running']:
                    self.logger.info("✅ Backtest canceled successfully")
                    return True
            except Exception as cancel_error:
                self.logger.warning(f"⚠️ Cancel API error: {cancel_error}")
            
            self.logger.warning("⚠️ Could not cancel backtest, but continuing...")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error canceling backtest: {e}")
            return True
    
    async def configure_lab_unix_timestamps(self, lab_id: str, start_unix: int, end_unix: int) -> bool:
        """Configure lab with Unix timestamps using v2 APIs."""
        try:
            # Get lab details using v2 API
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Update timestamps
            update_data = {
                'start_unix': start_unix,
                'end_unix': end_unix
            }
            
            result = await self.lab_api.update_lab_details(lab_id, update_data)
            
            if result:
                # Convert to readable dates for display
                start_date = time.strftime('%Y-%m-%d', time.gmtime(start_unix))
                end_date = time.strftime('%Y-%m-%d', time.gmtime(end_unix))
                duration_days = (end_unix - start_unix) // (24 * 3600)
                
                self.logger.info(f"📅 Configured: {start_date} → {end_date} ({duration_days} days)")
                return True
            else:
                self.logger.error(f"❌ Failed to update lab timestamps")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to configure timestamps: {e}")
            return False
    
    async def update_lab_name_with_date(self, lab_id: str, start_unix: int) -> bool:
        """Update lab name to include the new start date using v2 APIs."""
        try:
            lab_details = await self.lab_api.get_lab_details(lab_id)
            current_name = getattr(lab_details, 'name', '')
            date_pattern = r'\s+\d{2}[.-]\d{2}[.-]\d{4}$'
            base_name = re.sub(date_pattern, '', current_name)
            new_date = time.strftime('%d.%m.%Y', time.gmtime(start_unix))
            new_name = f"{base_name} {new_date}"
            
            update_data = {"name": new_name}
            result = await self.lab_api.update_lab_details(lab_id, update_data)
            
            if result:
                self.logger.info(f"📝 Updated lab name: '{current_name}' → '{new_name}'")
                return True
            else:
                self.logger.error(f"❌ Failed to update lab name")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update lab name: {e}")
            return False
    
    async def start_backtest(self, lab_id: str, start_unix: int = None, end_unix: int = None) -> str:
        """Start backtest while preserving lab configuration using v2 APIs."""
        try:
            # Get current lab details to preserve configuration
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Use provided dates or fall back to lab details
            start_unix_to_use = start_unix if start_unix is not None else getattr(lab_details, 'start_unix', None)
            end_unix_to_use = end_unix if end_unix is not None else getattr(lab_details, 'end_unix', None)
            
            if not start_unix_to_use or not end_unix_to_use:
                raise LabError("Start and end Unix timestamps are required")
            
            # Create start request using v2 API
            start_request = StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=start_unix_to_use,
                end_unix=end_unix_to_use,
                max_iterations=getattr(lab_details, 'max_iterations', 1500)
            )
            
            # Start the backtest using v2 API
            job_id = await self.lab_api.start_lab_execution(lab_id, start_request)
            
            if isinstance(job_id, dict) and job_id.get('Success') == False:
                error_msg = job_id.get('Error', '')
                if 'already active' in error_msg.lower():
                    return 'already_active'
                else:
                    self.logger.error(f"❌ Start failed: {error_msg}")
                    return 'failed'
            
            self.logger.info(f"🚀 Started backtest: {job_id}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start: {e}")
            return 'error'
    
    async def check_status_after_wait(self, lab_id: str, wait_seconds: int = 5) -> dict:
        """Check status after waiting using v2 APIs."""
        if wait_seconds > 0:
            self.logger.info(f"⏳ Waiting {wait_seconds} seconds...")
            await asyncio.sleep(wait_seconds)
        
        try:
            # Check status using v2 API
            status = await self.lab_api.get_lab_execution_status(lab_id)
            execution_update = await self.lab_api.get_lab_execution_update(lab_id)
            
            if execution_update:
                return {
                    'status': getattr(execution_update, 'status', status),
                    'is_running': getattr(execution_update, 'is_running', status == 'running'),
                    'progress': getattr(execution_update, 'progress', 0),
                    'generation': getattr(execution_update, 'generation', 0),
                    'population': getattr(execution_update, 'population', 0)
                }
            
            return {
                'status': status or 'unknown', 
                'is_running': status == 'running', 
                'progress': 0, 
                'generation': 0, 
                'population': 0
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Error checking status: {e}")
            return {'status': 'error', 'is_running': False, 'progress': 0, 'generation': 0, 'population': 0}
    
    async def test_period(self, lab_id: str, start_unix: int, end_unix: int, period_name: str) -> bool:
        """Test if a specific period works - FAST and PROPER status checking using v2 APIs."""
        try:
            # Convert to readable dates for display
            start_date = time.strftime('%Y-%m-%d', time.gmtime(start_unix))
            end_date = time.strftime('%Y-%m-%d', time.gmtime(end_unix))
            duration_days = (end_unix - start_unix) // (24 * 3600)
            
            self.logger.info(f"🧪 Testing {period_name}: {start_date} → {end_date} ({duration_days} days)")
            
            # CRITICAL: Cancel any existing backtest before starting new one
            await self.force_cancel_backtest(lab_id)
            await asyncio.sleep(2)  # Reduced wait time
            
            # Configure timestamps
            if not await self.configure_lab_unix_timestamps(lab_id, start_unix, end_unix):
                return False
            
            # Start backtest with the specific dates
            job_id = await self.start_backtest(lab_id, start_unix, end_unix)
            if job_id in ['failed', 'error']:
                self.logger.error(f"❌ Failed to start backtest")
                return False
            
            # FAST status checking - wait 5 seconds and check once
            self.logger.info(f"⏳ Waiting 5 seconds for {period_name}...")
            await asyncio.sleep(5)
            
            # Check status ONCE - if running, it's working
            status = await self.check_status_after_wait(lab_id, 0)  # No additional wait
            self.logger.info(f"📊 Status: {status['status']} | Running: {status['is_running']} | Progress: {status['progress']}%")
            
            # Simple check: if running, it works
            is_running = (status['status'] == 'RUNNING' or 
                         status['status'] == 2 or 
                         status['is_running'])
            
            if is_running:
                self.logger.info(f"✅ {period_name} WORKS! Backtest is running.")
                # Cancel this backtest
                await self.force_cancel_backtest(lab_id)
                return True
            else:
                self.logger.info(f"⏳ {period_name} is QUEUED - not working yet")
                # Cancel this backtest
                await self.force_cancel_backtest(lab_id)
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error testing {period_name}: {e}")
            # Try to cancel on error
            try:
                await self.force_cancel_backtest(lab_id)
            except:
                pass
            return False
    
    async def find_longest_working_period(self, lab_id: str) -> Tuple[Optional[int], Optional[int], str, bool]:
        """Find the longest period using the exact algorithm: 36→34→33→!→33+2w→33+3w→!→33+2w+5d→!→33+2w+6d→!"""
        try:
            self.logger.info(f"🔍 Finding longest working period for lab {lab_id}")

            # Get lab info using v2 API
            lab_details = await self.lab_api.get_lab_details(lab_id)
            market_tag = None
            if hasattr(lab_details, 'settings') and hasattr(lab_details.settings, 'market_tag'):
                market_tag = lab_details.settings.market_tag

            self.logger.info(f"📊 Lab: {getattr(lab_details, 'name', 'Unknown')}")
            self.logger.info(f"🏷️ Market: {market_tag}")

            # Force cancel any existing backtest
            await self.force_cancel_backtest(lab_id)
            await asyncio.sleep(3)  # Wait for cancellation

            # Current time in Unix
            end_unix = int(time.time())

            # EXACT ALGORITHM: Start with 36 months, step down until RUNNING
            self.logger.info(f"📋 STEP 1: Start with 36 months, step down until RUNNING")

            # 36 months in seconds (36 * 30.44 * 24 * 3600)
            months_36_seconds = 36 * 30.44 * 24 * 3600  # ≈ 94,371,840 seconds
            current_seconds = months_36_seconds
            start_unix = end_unix - current_seconds

            # Step down by months until we find RUNNING
            while current_seconds > 0:
                period_name = f"{current_seconds // (30.44 * 24 * 3600):.1f} months"
                self.logger.info(f"🧪 Testing {period_name}...")

                if await self.test_period(lab_id, start_unix, end_unix, period_name):
                    self.logger.info(f"✅ Found initial RUNNING period: {current_seconds // (30.44 * 24 * 3600):.1f} months")
                    break
                else:
                    # Decrease by 1 month (30.44 days)
                    current_seconds -= 30.44 * 24 * 3600  # 1 month in seconds
                    start_unix = end_unix - current_seconds
                    self.logger.info(f"⏳ {period_name} was QUEUED, trying {current_seconds // (30.44 * 24 * 3600):.1f} months...")

            if current_seconds <= 0:
                self.logger.info(f"❌ No RUNNING period found")
                return None, None, "none", False

            # STEP 2: Now step UP by weeks to find the optimal point
            self.logger.info(f"📋 STEP 2: Step UP by weeks to find optimal point")

            # Try adding weeks until we hit QUEUED again
            week_seconds = 7 * 24 * 3600
            weeks_added = 0
            max_weeks = 20  # Don't go beyond 20 weeks

            while weeks_added < max_weeks:
                test_seconds = current_seconds + (weeks_added + 1) * week_seconds
                test_start_unix = end_unix - test_seconds
                test_days = test_seconds // (24 * 3600)

                self.logger.info(f"🧪 Testing {test_days} days ({current_seconds // (30.44 * 24 * 3600):.1f} months + {weeks_added + 1} weeks)...")

                if await self.test_period(lab_id, test_start_unix, end_unix, f"{test_days} days"):
                    weeks_added += 1
                    self.logger.info(f"✅ {test_days} days still RUNNING, trying {test_days + 7} days...")
                else:
                    self.logger.info(f"⏳ {test_days} days is QUEUED - found upper limit")
                    break

            # Update current_seconds to the optimal point
            current_seconds += weeks_added * week_seconds

            # STEP 3: Fine-tune by adding days
            self.logger.info(f"📋 STEP 3: Fine-tune by adding days")

            day_seconds = 24 * 3600
            days_added = 0
            max_days = 10  # Don't go beyond 10 days

            while days_added < max_days:
                test_seconds = current_seconds + (days_added + 1) * day_seconds
                test_start_unix = end_unix - test_seconds
                test_days = test_seconds // (24 * 3600)

                self.logger.info(f"🧪 Testing {test_days} days (+{days_added + 1} days)...")

                if await self.test_period(lab_id, test_start_unix, end_unix, f"{test_days} days"):
                    days_added += 1
                    self.logger.info(f"✅ {test_days} days still RUNNING, trying {test_days + 1} days...")
                else:
                    self.logger.info(f"⏳ {test_days} days is QUEUED - found optimal point")
                    break

            # Update current_seconds to the final optimal point
            current_seconds += days_added * day_seconds

            # Final result
            final_start_unix = end_unix - current_seconds
            final_days = current_seconds // (24 * 3600)
            final_period_name = f"{final_days} days"

            self.logger.info(f"🎉 SUCCESS! Longest working period: {final_period_name}")
            self.logger.info(f"   Period: {time.strftime('%Y-%m-%d', time.gmtime(final_start_unix))} → {time.strftime('%Y-%m-%d', time.gmtime(end_unix))}")
            self.logger.info(f"   Duration: {final_days} days")
            self.logger.info(f"   Optimal point found!")

            # Update lab name with new start date
            self.logger.info(f"📝 Updating lab name with new start date...")
            await self.update_lab_name_with_date(lab_id, final_start_unix)

            return final_start_unix, end_unix, final_period_name, True

        except Exception as e:
            self.logger.error(f"❌ Error finding longest period: {e}")
            return None, None, "error", False

    async def orchestrate_clone_config_sync_and_find_cutoff(
        self,
        template_lab_id: str,
        account_id: str,
        stage_label: str,
        markets: List[str],
    ) -> Dict[str, Any]:
        """
        Orchestrate the complete workflow: clone, configure, sync history, and find cutoff.
        
        Args:
            template_lab_id: ID of the template lab to clone
            account_id: Account ID to assign to cloned labs
            stage_label: Stage label for naming
            markets: List of market symbols to process
            
        Returns:
            Dict with results for each market
        """
        try:
            self.logger.info(f"🎯 Starting orchestrated workflow for {len(markets)} markets")
            
            # Step 1: Clone labs to markets
            self.logger.info(f"📋 Step 1: Cloning template lab to {len(markets)} markets")
            
            # Map markets to market tags (markets are already coin symbols)
            market_mapping = {
                'BTC': 'BTC_USDT_PERPETUAL',
                'TRX': 'TRX_USDT_PERPETUAL', 
                'ADA': 'ADA_USDT_PERPETUAL'
            }
            
            target_markets = {market: market_mapping.get(market, f"{market}_USDT_PERPETUAL") for market in markets}
            
            cloned_labs = await self.clone_manager.clone_to_markets(
                template_lab_id=template_lab_id,
                target_markets=target_markets,
                account_id=account_id,
                stage_label=stage_label
            )
            
            self.logger.info(f"✅ Cloned {len(cloned_labs)} labs")
            
            # Step 2: Configure labs (rename and set trade amounts)
            self.logger.info(f"📋 Step 2: Configuring cloned labs")
            
            # Get script name from template lab
            template_details = await self.lab_api.get_lab_details(template_lab_id)
            script_name = getattr(template_details, 'script_name', 'Unknown')
            
            for market, lab_id in cloned_labs.items():
                try:
                    # Rename lab
                    await self.config_manager.rename_lab(
                        lab_id=lab_id,
                        stage_label=stage_label,
                        coin=market,
                        script_name=script_name
                    )
                    
                    # Set trade amount
                    await self.config_manager.set_trade_amount_usdt_equivalent(
                        lab_id=lab_id,
                        usdt_amount=2000.0
                    )
                    
                    self.logger.info(f"✅ Configured lab for {market}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to configure lab for {market}: {e}")
            
            # Step 3: Sync history for all markets
            self.logger.info(f"📋 Step 3: Syncing history for {len(target_markets)} markets")
            
            market_tags = list(target_markets.values())
            sync_results = await self.sync_history_manager.sync_36_months(market_tags)
            
            self.logger.info(f"✅ History sync completed for {len(sync_results)} markets")
            
            # Step 4: Find cutoff for each lab
            self.logger.info(f"📋 Step 4: Finding cutoff for {len(cloned_labs)} labs")
            
            results = {}
            
            for market, lab_id in cloned_labs.items():
                try:
                    self.logger.info(f"🔍 Finding cutoff for {market} (lab {lab_id})")
                    
                    cutoff_result = await self.find_longest_working_period(lab_id)
                    start_unix, end_unix, period_name, success = cutoff_result
                    
                    if success:
                        results[market] = {
                            'lab_id': lab_id,
                            'start_unix': start_unix,
                            'end_unix': end_unix,
                            'period_name': period_name,
                            'success': True,
                            'start_date': time.strftime('%Y-%m-%d', time.gmtime(start_unix)) if start_unix else None,
                            'end_date': time.strftime('%Y-%m-%d', time.gmtime(end_unix)) if end_unix else None
                        }
                        self.logger.info(f"✅ {market}: {period_name} ({time.strftime('%Y-%m-%d', time.gmtime(start_unix))} → {time.strftime('%Y-%m-%d', time.gmtime(end_unix))})")
                    else:
                        results[market] = {
                            'lab_id': lab_id,
                            'success': False,
                            'error': period_name
                        }
                        self.logger.error(f"❌ {market}: Failed to find cutoff - {period_name}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error finding cutoff for {market}: {e}")
                    results[market] = {
                        'lab_id': lab_id,
                        'success': False,
                        'error': str(e)
                    }
            
            # Summary
            successful = sum(1 for r in results.values() if r.get('success', False))
            self.logger.info(f"🎉 Orchestration complete: {successful}/{len(markets)} markets successful")
            
            return {
                'template_lab_id': template_lab_id,
                'account_id': account_id,
                'stage_label': stage_label,
                'markets': markets,
                'cloned_labs': cloned_labs,
                'sync_results': sync_results,
                'cutoff_results': results,
                'successful_count': successful,
                'total_count': len(markets)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in orchestrated workflow: {e}")
            raise LabError(f"Orchestrated workflow failed: {e}")

    @property
    def sync_history_manager(self) -> SyncHistoryManager:
        """Get or create sync history manager"""
        if not hasattr(self, '_sync_history_manager'):
            from .sync_history_manager import SyncHistoryManager
            self._sync_history_manager = SyncHistoryManager(
                self.market_api, 
                self.backtest_api, 
                self.client, 
                self.auth_manager
            )
        return self._sync_history_manager