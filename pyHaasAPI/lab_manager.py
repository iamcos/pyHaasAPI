"""
Lab Manager for HaasOnline Labs
Consolidated lab creation, parameter optimization, and backtest management
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, StartLabExecutionRequest, CloudMarket
from pyHaasAPI.parameter_handler import ParameterHandler
from pyHaasAPI.parameters import LabSettings as ParametersLabSettings
from pyHaasAPI.tools.utils import BacktestFetcher, BacktestFetchConfig

logger = logging.getLogger(__name__)

@dataclass
class LabConfig:
    """Lab configuration settings"""
    max_parallel: int = 10
    max_generations: int = 30
    max_epochs: int = 3
    max_runtime: int = 0
    auto_restart: int = 0

@dataclass
class LabSettings:
    """Lab settings configuration"""
    leverage: float = 0
    position_mode: int = 0
    margin_mode: int = 0
    interval: int = 1
    chart_style: int = 300
    trade_amount: float = 100
    order_template: int = 500
    price_data_style: str = "CandleStick"

class LabManager:
    """Comprehensive lab management with parameter optimization"""
    
    def __init__(self, executor):
        self.executor = executor
        self.parameter_handler = ParameterHandler()
        
    def create_optimized_lab(self, 
                           script_id: str, 
                           account_id: str, 
                           market: CloudMarket,
                           exchange_code: str,
                           lab_name: Optional[str] = None,
                           config: Optional[LabConfig] = None,
                           settings: Optional[LabSettings] = None) -> Dict[str, Any]:
        """
        Create a lab with parameter optimization, ensuring no invalid labs slow down the system
        """
        logger.info("📋 Creating optimized lab...")
        
        # Clean up any invalid labs first
        self.cleanup_invalid_labs()
        
        logger.info(f"  Script ID: {script_id}")
        logger.info(f"  Account ID: {account_id}")
        logger.info(f"  Market: {market.primary}/{market.secondary}")
        logger.info(f"  Exchange: {exchange_code}")
        
        # Step 1: Create lab
        logger.info("  🔧 Step 1: Creating lab...")
        
        if lab_name:
            logger.info(f"  📝 Note: Custom name '{lab_name}' provided but using auto-generated name for compatibility")
        
        # Generate lab name
        auto_name = f"{settings.interval if settings else 1}_{market.primary}_{market.secondary}_{script_id}_{account_id}"
        
        # Create lab request
        req = CreateLabRequest.with_generated_name(
            script_id=script_id,
            account_id=account_id,
            market=market,
            exchange_code=exchange_code,
            interval=settings.interval if settings else 1,
            default_price_data_style="CandleStick"
        )
        
        # Override with custom settings if provided
        if settings:
            req.trade_amount = settings.trade_amount
            req.chart_style = settings.chart_style
            req.order_template = settings.order_template
            req.leverage = settings.leverage
            req.position_mode = settings.position_mode
            req.margin_mode = settings.margin_mode
        
        lab = api.create_lab(self.executor, req)
        logger.info(f"  ✅ Lab created: {lab.name} (ID: {lab.lab_id})")
        
        # Debug: Check settings after creation
        lab_details = api.get_lab_details(self.executor, lab.lab_id)
        logger.info(f"  [DEBUG] After creation: market_tag={getattr(lab_details.settings, 'market_tag', 'NOT_FOUND')}, account_id={getattr(lab_details.settings, 'account_id', 'NOT_FOUND')}")
        
        # Debug: Log raw API response
        logger.info(f"  [DEBUG] Raw API response after creation: {lab_details.model_dump()}")
        
        # Debug: Log ST data for model creation
        st_data = {
            'botId': getattr(lab_details.settings, 'bot_id', ''),
            'botName': getattr(lab_details.settings, 'bot_name', ''),
            'accountId': getattr(lab_details.settings, 'account_id', ''),
            'marketTag': getattr(lab_details.settings, 'market_tag', ''),
            'positionMode': getattr(lab_details.settings, 'position_mode', 0),
            'marginMode': getattr(lab_details.settings, 'margin_mode', 0),
            'leverage': getattr(lab_details.settings, 'leverage', 0.0),
            'tradeAmount': getattr(lab_details.settings, 'trade_amount', 0.0),
            'interval': getattr(lab_details.settings, 'interval', 1),
            'chartStyle': getattr(lab_details.settings, 'chart_style', 0),
            'orderTemplate': getattr(lab_details.settings, 'order_template', 0),
            'scriptParameters': getattr(lab_details.settings, 'script_parameters', {})
        }
        logger.info(f"  [DEBUG] ST data for model creation: {st_data}")
        logger.info(f"  [DEBUG] ST accountId value: {st_data['accountId']}")
        logger.info(f"  [DEBUG] ST marketTag value: {st_data['marketTag']}")
        
        # Check if lab was created with correct settings
        if (lab_details.settings.market_tag and 
            lab_details.settings.account_id and 
            lab_details.settings.trade_amount > 0):
            
            logger.info("  ✅ Lab created with correct settings - skipping parameter optimization")
            logger.info(f"    Market Tag: {lab_details.settings.market_tag}")
            logger.info(f"    Account ID: {lab_details.settings.account_id}")
            logger.info(f"    Trade Amount: {lab_details.settings.trade_amount}")
            logger.info(f"    Chart Style: {lab_details.settings.chart_style}")
            logger.info(f"    Order Template: {lab_details.settings.order_template}")
            
            # Skip parameter optimization to preserve settings
            return lab_details
        
        # Only optimize parameters if settings are missing (legacy behavior)
        logger.info("  🔧 Lab created with missing settings - optimizing parameters...")
        
        # Optimize parameters with ranges
        try:
            from pyHaasAPI.lab import update_lab_parameter_ranges
            optimized_lab = update_lab_parameter_ranges(self.executor, lab_details.lab_id)
            logger.info("  ✅ Parameters optimized successfully")
            return optimized_lab
        except Exception as e:
            logger.error(f"  ❌ Parameter optimization failed: {e}")
            return lab_details
    
    def _apply_parameter_optimization(self, lab_id: str, optimization_plan: List[Dict[str, Any]]) -> bool:
        """Apply optimization plan to lab parameters using the working pattern, preserving market_tag and account_id"""
        logger.info("🔧 Setting up lab optimization...")
        
        try:
            # Get current lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            logger.info(f"  [DEBUG] Before optimization: market_tag={getattr(lab_details.settings, 'market_tag', None)}, account_id={getattr(lab_details.settings, 'account_id', None)}")

            # --- FIX: Preserve market_tag and account_id ---
            original_market_tag = lab_details.settings.market_tag
            original_account_id = lab_details.settings.account_id
            if not original_market_tag or original_market_tag == "":
                logger.warning(f"⚠️ market_tag is empty before update! (lab_id={lab_id})")
            if not original_account_id or original_account_id == "":
                logger.warning(f"⚠️ account_id is empty before update! (lab_id={lab_id})")

            # Apply optimization using the parameter handler
            updated_parameters = self.parameter_handler.apply_optimization_to_lab(
                lab_details.parameters, 
                optimization_plan
            )
            
            # Update lab details
            lab_details.parameters = updated_parameters
            # --- FIX: Always restore original market_tag and account_id before update ---
            lab_details.settings.market_tag = original_market_tag
            lab_details.settings.account_id = original_account_id
            logger.info(f"  [DEBUG] Before update: market_tag={getattr(lab_details.settings, 'market_tag', None)}, account_id={getattr(lab_details.settings, 'account_id', None)}")
            api.update_lab_details(self.executor, lab_details)
            
            # Validate the optimization
            stats = self.parameter_handler.validate_lab_parameters(updated_parameters)
            logger.info(f"  📊 Optimization stats: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Error applying parameter optimization: {e}")
            return False
    
    def run_backtest(self, lab_id: str, hours: int = 120, timeout_minutes: int = 30) -> Dict[str, Any]:
        """
        Run backtest with specified duration and wait for completion
        
        Args:
            lab_id: Lab ID to run backtest on
            hours: Number of hours to backtest
            timeout_minutes: Timeout for completion wait
            
        Returns:
            Dict containing backtest results
        """
        logger.info(f"🚀 Starting {hours}-hour backtest...")
        
        try:
            # Calculate time range
            now = int(time.time())
            start_unix = now - (hours * 3600)
            end_unix = now
            
            # Start backtest
            api.start_lab_execution(
                self.executor,
                StartLabExecutionRequest(
                    lab_id=lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=False
                )
            )
            
            logger.info(f"✅ Backtest started")
            
            # Wait for completion
            success = self._wait_for_completion(lab_id, timeout_minutes)
            
            if success:
                # Get results
                results = self._get_backtest_results(lab_id)
                return {
                    "success": True,
                    "lab_id": lab_id,
                    "start_unix": start_unix,
                    "end_unix": end_unix,
                    "duration_hours": hours,
                    "results": results
                }
            else:
                return {
                    "success": False,
                    "lab_id": lab_id,
                    "error": "Backtest failed or timed out"
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to start backtest: {e}")
            return {
                "success": False,
                "lab_id": lab_id,
                "error": str(e)
            }
    
    def _wait_for_completion(self, lab_id: str, timeout_minutes: int) -> bool:
        """Wait for backtest to complete"""
        logger.info(f"⏳ Waiting for backtest completion (timeout: {timeout_minutes} minutes)...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        last_status = None
        
        while time.time() - start_time < timeout_seconds:
            try:
                details = api.get_lab_details(self.executor, lab_id)
                status = getattr(details, 'status', None)
                
                # Handle LabStatus enum objects
                if hasattr(status, 'value'):
                    status_value = status.value
                    status_str = str(status_value)
                else:
                    status_str = str(status) if status is not None else None
                
                if status_str != last_status:
                    logger.info(f"  🔄 Status: {status_str}")
                    last_status = status_str
                
                if status_str == '3':  # COMPLETED
                    logger.info("✅ Backtest completed successfully")
                    return True
                elif status_str in ['4', '5']:  # CANCELLED or ERROR
                    logger.error("❌ Backtest failed")
                    return False
                else:
                    time.sleep(30)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error checking status: {e}")
                time.sleep(30)
        
        logger.error("⏰ Backtest timed out")
        return False
    
    def _get_backtest_results(self, lab_id: str) -> Dict[str, Any]:
        """Get backtest results and analyze performance"""
        logger.info("📊 Getting backtest results...")
        
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Get backtest results using centralized fetcher
            fetcher = BacktestFetcher(self.executor, BacktestFetchConfig(page_size=100))
            backtest_results = fetcher.fetch_all_backtests(lab_id)
            
            if not backtest_results:
                return {"error": "No backtest results found"}
            
            # Analyze top performers
            top_results = self._analyze_top_performers(backtest_results)
            
            return {
                "total_results": len(backtest_results),
                "top_performers": top_results,
                "lab_status": lab_details.status
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting backtest results: {e}")
            return {"error": str(e)}
    
    def _analyze_top_performers(self, results: List[Any]) -> List[Dict[str, Any]]:
        """Analyze and return top performing backtest results"""
        if not results:
            return []
        
        # Sort by ROI (assuming ROI is available in summary)
        sorted_results = sorted(
            results, 
            key=lambda x: getattr(x.summary, 'ReturnOnInvestment', 0),
            reverse=True
        )
        
        top_results = []
        for i, result in enumerate(sorted_results[:3]):  # Top 3
            top_results.append({
                "rank": i + 1,
                "backtest_id": result.backtest_id,
                "roi": getattr(result.summary, 'ReturnOnInvestment', 0),
                "realized_profit": getattr(result.summary, 'RealizedProfits', 0),
                "fee_costs": getattr(result.summary, 'FeeCosts', 0),
                "parameters": result.parameters
            })
        
        return top_results
    
    def activate_top_bots(self, lab_id: str, top_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Activate top performing bots from backtest results"""
        logger.info("🤖 Activating top performing bots...")
        
        activated_bots = []
        for result in top_results:
            try:
                bot_name = f"TopBot_{result['rank']}_{int(time.time())}"
                
                # Add bot from lab result
                api.add_bot_from_lab(
                    self.executor,
                    {
                        "lab_id": lab_id,
                        "backtest_id": result['backtest_id'],
                        "bot_name": bot_name,
                        "account_id": "",  # Will be set by API
                        "market": None,    # Will be set by API
                        "leverage": 0
                    }
                )
                
                activated_bots.append({
                    "bot_name": bot_name,
                    "backtest_id": result['backtest_id'],
                    "roi": result['roi']
                })
                
                logger.info(f"  ✅ Activated bot: {bot_name} (ROI: {result['roi']:.2f}%)")
                
            except Exception as e:
                logger.error(f"  ❌ Failed to activate bot: {e}")
        
        return activated_bots

    def cleanup_invalid_labs(self):
        """Clean up labs with invalid parameters or stuck in queue that slow down the system"""
        logger.info("🧹 Cleaning up invalid/stuck labs...")
        
        try:
            all_labs = api.get_all_labs(self.executor)
            labs_to_delete = []
            
            for lab in all_labs:
                # Check if lab is stuck in queue for too long
                if lab.status.value in [0, 1]:  # QUEUED or RUNNING
                    time_in_queue = int(time.time()) - lab.created_at
                    if time_in_queue > 300:  # 5 minutes
                        logger.warning(f"⚠️ Lab {lab.lab_id} stuck in queue for {time_in_queue}s - marking for deletion")
                        labs_to_delete.append(lab)
                        continue
                
                # Check lab details for invalid settings
                try:
                    lab_details = api.get_lab_details(self.executor, lab.lab_id)
                    settings = lab_details.settings
                    
                    # Check for critical missing settings
                    market_tag = getattr(settings, 'market_tag', '')
                    account_id = getattr(settings, 'account_id', '')
                    trade_amount = getattr(settings, 'trade_amount', 0)
                    chart_style = getattr(settings, 'chart_style', 0)
                    order_template = getattr(settings, 'order_template', 0)
                    
                    if (not market_tag or market_tag == '' or 
                        not account_id or account_id == '' or
                        trade_amount <= 0 or chart_style <= 0 or order_template <= 0):
                        logger.warning(f"⚠️ Lab {lab.lab_id} has invalid settings - marking for deletion")
                        logger.warning(f"  Market: '{market_tag}', Account: '{account_id}', Trade: {trade_amount}, Chart: {chart_style}, Order: {order_template}")
                        labs_to_delete.append(lab)
                        continue
                    
                    # Check for invalid parameters
                    invalid_params = 0
                    for param in lab_details.parameters:
                        if isinstance(param, dict):
                            options = param.get('O', [])
                        else:
                            options = getattr(param, 'options', [])
                        
                        if not options or (isinstance(options, list) and all(o == '' for o in options)):
                            invalid_params += 1
                    
                    if invalid_params > len(lab_details.parameters) * 0.5:  # More than 50% invalid
                        logger.warning(f"⚠️ Lab {lab.lab_id} has {invalid_params}/{len(lab_details.parameters)} invalid parameters - marking for deletion")
                        labs_to_delete.append(lab)
                        continue
                        
                except Exception as e:
                    logger.error(f"❌ Error checking lab {lab.lab_id}: {e}")
                    labs_to_delete.append(lab)
                    continue
            
            # Delete invalid labs
            for lab in labs_to_delete:
                try:
                    logger.info(f"🗑️ Deleting invalid lab: {lab.lab_id} ({lab.name})")
                    api.delete_lab(self.executor, lab.lab_id)
                except Exception as e:
                    logger.error(f"❌ Failed to delete lab {lab.lab_id}: {e}")
            
            if labs_to_delete:
                logger.info(f"✅ Cleaned up {len(labs_to_delete)} invalid labs")
            else:
                logger.info("✅ No invalid labs found")
                
        except Exception as e:
            logger.error(f"❌ Error during lab cleanup: {e}") 