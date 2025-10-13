"""
Sync History Manager for pyHaasAPI v2

Handles history synchronization for markets using the BacktestAPI.
"""

import asyncio
from typing import List, Dict, Any, Optional
from ..core.logging import get_logger
from ..exceptions import LabError
from ..api.market.market_api import MarketAPI
from ..api.backtest.backtest_api import BacktestAPI
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager

logger = get_logger("sync_history_manager")


class SyncHistoryManager:
    """Manages history synchronization for markets."""
    
    def __init__(self, market_api: MarketAPI, backtest_api: BacktestAPI, client: Optional[AsyncHaasClient] = None, auth_manager: Optional[AuthenticationManager] = None):
        self.market_api = market_api
        self.backtest_api = backtest_api
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("sync_history_manager")
    
    async def sync_36_months(self, market_tags: List[str]) -> Dict[str, Any]:
        """
        Sync 36 months of history for the specified markets using v2 APIs.
        
        Args:
            market_tags: List of market tags to sync
            
        Returns:
            Dict with sync results for each market
        """
        try:
            self.logger.info(f"🔄 Syncing 36 months history for {len(market_tags)} markets")
            
            results = {}
            
            for market_tag in market_tags:
                try:
                    self.logger.info(f"📊 Syncing history for {market_tag}")
                    
                    # Check current history status using v2 API
                    try:
                        status = await self.backtest_api.get_history_status(market_tag)
                        
                        if status and hasattr(status, 'Data'):
                            data = status.Data
                            current_status = getattr(data, 'Status', 0)
                            
                            if current_status == 3:  # Already synced
                                self.logger.info(f"✅ {market_tag} already synced (Status: {current_status})")
                                results[market_tag] = {"status": "already_synced", "status_code": current_status}
                                continue
                    except Exception as status_error:
                        self.logger.warning(f"⚠️ Could not check status for {market_tag}: {status_error}")
                    
                    # Start history sync using v2 API
                    try:
                        sync_result = await self.backtest_api.sync_market_history(market_tag, months=36)
                        
                        if sync_result:
                            self.logger.info(f"🚀 Started history sync for {market_tag}")
                            results[market_tag] = {"status": "sync_started", "result": sync_result}
                        else:
                            self.logger.warning(f"⚠️ Failed to start sync for {market_tag}")
                            results[market_tag] = {"status": "sync_failed"}
                    except Exception as sync_error:
                        self.logger.warning(f"⚠️ Sync API not available for {market_tag}: {sync_error}")
                        # Fallback: assume sync is needed and will be handled by the system
                        results[market_tag] = {"status": "sync_needed", "note": "API not available, assuming sync needed"}
                    
                except Exception as e:
                    self.logger.error(f"❌ Error syncing {market_tag}: {e}")
                    results[market_tag] = {"status": "error", "error": str(e)}
            
            # Wait a bit for syncs to start
            self.logger.info("⏳ Waiting for history syncs to initialize...")
            await asyncio.sleep(5)
            
            # Check final status
            for market_tag in market_tags:
                try:
                    status = await self.backtest_api.get_history_status(market_tag)
                    if status and hasattr(status, 'Data'):
                        data = status.Data
                        final_status = getattr(data, 'Status', 0)
                        self.logger.info(f"📊 {market_tag} final status: {final_status}")
                        results[market_tag]["final_status"] = final_status
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not check final status for {market_tag}: {e}")
            
            self.logger.info(f"🎉 History sync completed for {len(market_tags)} markets")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing history: {e}")
            raise LabError(f"Failed to sync history: {e}")
    
    async def wait_for_sync_completion(
        self,
        market_tags: List[str],
        max_wait_minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Wait for history sync completion for specified markets using v2 APIs.
        
        Args:
            market_tags: List of market tags to monitor
            max_wait_minutes: Maximum time to wait in minutes
            
        Returns:
            Dict with final sync status for each market
        """
        try:
            self.logger.info(f"⏳ Waiting for sync completion (max {max_wait_minutes} minutes)")
            
            results = {}
            wait_seconds = 0
            max_wait_seconds = max_wait_minutes * 60
            
            while wait_seconds < max_wait_seconds:
                all_complete = True
                
                for market_tag in market_tags:
                    try:
                        status = await self.backtest_api.get_history_status(market_tag)
                        if status and hasattr(status, 'Data'):
                            data = status.Data
                            sync_status = getattr(data, 'Status', 0)
                            
                            if sync_status == 3:  # Complete
                                if market_tag not in results:
                                    self.logger.info(f"✅ {market_tag} sync completed")
                                    results[market_tag] = {"status": "completed", "status_code": sync_status}
                            else:
                                all_complete = False
                                if market_tag not in results:
                                    results[market_tag] = {"status": "in_progress", "status_code": sync_status}
                        else:
                            all_complete = False
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error checking status for {market_tag}: {e}")
                        all_complete = False
                
                if all_complete:
                    self.logger.info("🎉 All history syncs completed!")
                    break
                
                await asyncio.sleep(10)  # Check every 10 seconds
                wait_seconds += 10
                
                if wait_seconds % 60 == 0:  # Log every minute
                    self.logger.info(f"⏳ Still waiting... ({wait_seconds // 60} minutes elapsed)")
            
            if wait_seconds >= max_wait_seconds:
                self.logger.warning(f"⚠️ Timeout reached ({max_wait_minutes} minutes)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error waiting for sync completion: {e}")
            raise LabError(f"Failed to wait for sync completion: {e}")