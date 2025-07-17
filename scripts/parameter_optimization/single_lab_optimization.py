#!/usr/bin/env python3
"""
Single Lab Parameter Optimization Test - Refactored

This script demonstrates the refactored approach using centralized utilities:
1. Uses centralized authentication
2. Uses centralized market data fetching
3. Uses centralized parameter optimization
4. Creates one MadHatter lab on BINANCE BTC/USDT with intelligent parameter optimization
5. Runs backtest and activates top 3 bots
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import our refactored utilities
from utils.auth.authenticator import authenticator
from utils.market_data.market_fetcher import MarketFetcher
from utils.lab_management.parameter_optimizer import ParameterOptimizer

# Import pyHaasAPI modules
from pyHaasAPI import api
from pyHaasAPI.model import (
    CreateLabRequest, StartLabExecutionRequest, 
    GetBacktestResultRequest, AddBotFromLabRequest
)

# Import configuration
from config.settings import (
    DEFAULT_BACKTEST_HOURS, DEFAULT_TIMEOUT_MINUTES,
    BOT_SCRIPTS, LAB_STATUS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SingleLabOptimizer:
    """Refactored single lab optimizer using centralized utilities"""
    
    def __init__(self):
        self.market_fetcher = None
        self.parameter_optimizer = ParameterOptimizer()
        
    def setup(self) -> bool:
        """Setup authentication and utilities"""
        # Authenticate
        if not authenticator.authenticate():
            return False
        
        # Setup market fetcher
        self.market_fetcher = MarketFetcher(authenticator.get_executor())
        return True
    
    def create_optimized_lab(self, script_id: str, account_id: str, market: str) -> Dict[str, Any]:
        """Create lab with intelligent parameter optimization using working pattern"""
        logger.info("📋 Creating optimized MadHatter lab...")
        logger.info(f"  Script ID: {script_id}")
        logger.info(f"  Account ID: {account_id}")
        logger.info(f"  Market: {market}")
        
        try:
            # Step 1: Create the lab using the working pattern
            logger.info("  🔧 Step 1: Creating lab with working pattern...")
            
            # Parse market string to get CloudMarket object
            # market format: "BINANCE_BTC_USDT_"
            parts = market.replace("_", "").split()
            if len(parts) >= 3:
                exchange_code = parts[0]
                primary = parts[1]
                secondary = parts[2]
            else:
                # Fallback to BINANCE_BTC_USDT
                exchange_code = "BINANCE"
                primary = "BTC"
                secondary = "USDT"
            
            # Create CloudMarket object
            from pyHaasAPI.model import CloudMarket
            cloud_market = CloudMarket(
                category="",
                price_source=exchange_code,
                primary=primary,
                secondary=secondary
            )
            
            # Create lab request using working pattern
            lab_request = CreateLabRequest.with_generated_name(
                script_id=script_id,
                account_id=account_id,
                market=cloud_market,
                exchange_code=exchange_code,
                interval=1,
                default_price_data_style="CandleStick"
            )
            
            lab = api.create_lab(authenticator.get_executor(), lab_request)
            logger.info(f"  ✅ Lab created: {lab.name} (ID: {lab.lab_id})")
            
            # Step 2: Get script details for parameter analysis
            logger.info("  🔧 Step 2: Analyzing script parameters...")
            script_details = api.get_script_record(authenticator.get_executor(), script_id)
            
            # Step 3: Create optimization plan
            logger.info("  🔧 Step 3: Creating optimization plan...")
            optimization_plan = self._create_optimization_plan(script_details)
            
            # Step 4: Apply optimization to lab
            logger.info("  🔧 Step 4: Applying parameter optimization...")
            success = self.setup_lab_optimization(authenticator.get_executor(), lab.lab_id, optimization_plan)
            
            if success:
                logger.info("  ✅ Lab optimization completed successfully!")
                return {"lab": lab, "optimization_plan": optimization_plan}
            else:
                logger.error("  ❌ Lab optimization failed!")
                return None
                
        except Exception as e:
            logger.error(f"  ❌ Error creating optimized lab: {e}")
            return None
    
    def update_lab_market_tag(self, lab_id: str, market_tag: str):
        """Update lab market tag after creation, preserving account_id"""
        logger.info(f"🔄 Updating lab market tag to: {market_tag}")
        
        try:
            # Get current lab details
            lab_details = api.get_lab_details(authenticator.get_executor(), lab_id)
            
            # --- FIX: Preserve account_id ---
            original_account_id = lab_details.settings.account_id
            if not original_account_id or original_account_id == "":
                logger.warning(f"⚠️ account_id is empty before update! (lab_id={lab_id})")
            
            # Update the market tag in settings
            lab_details.settings.market_tag = market_tag
            lab_details.settings.account_id = original_account_id
            
            # Update lab details using the API
            updated_details = api.update_lab_details(
                authenticator.get_executor(),
                lab_details
            )
            
            logger.info(f"✅ Lab market tag updated successfully")
            return updated_details
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to update lab market tag: {e}")
            # Continue anyway, as this is not critical
            return None
    
    def run_backtest(self, lab_id: str, backtest_hours: int = None) -> Dict[str, Any]:
        """Run backtest with specified duration"""
        if backtest_hours is None:
            backtest_hours = DEFAULT_BACKTEST_HOURS
            
        logger.info(f"🚀 Starting {backtest_hours}-hour backtest...")
        
        try:
            now = int(time.time())
            start_unix = now - (backtest_hours * 3600)
            end_unix = now
            
            api.start_lab_execution(
                authenticator.get_executor(),
                StartLabExecutionRequest(
                    lab_id=lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=False
                )
            )
            
            logger.info(f"✅ Backtest started")
            return {
                "lab_id": lab_id,
                "start_unix": start_unix,
                "end_unix": end_unix,
                "duration_hours": backtest_hours
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to start backtest: {e}")
            return None
    
    def wait_for_completion(self, lab_id: str, timeout_minutes: int = None) -> bool:
        """Wait for backtest to complete"""
        if timeout_minutes is None:
            timeout_minutes = DEFAULT_TIMEOUT_MINUTES
            
        logger.info(f"⏳ Waiting for backtest completion (timeout: {timeout_minutes} minutes)...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        last_status = None
        
        while time.time() - start_time < timeout_seconds:
            try:
                details = api.get_lab_details(authenticator.get_executor(), lab_id)
                status = getattr(details, 'status', None)
                
                # Handle LabStatus enum objects
                if hasattr(status, 'value'):
                    # It's an enum, get the value
                    status_value = status.value
                    status_str = str(status_value)
                    status_name = status.name if hasattr(status, 'name') else f'UNKNOWN({status_value})'
                else:
                    # It's a regular value
                    status_str = str(status) if status is not None else None
                    status_name = LAB_STATUS.get(status_str, f'UNKNOWN({status_str})')
                
                if status_str != last_status:
                    logger.info(f"  🔄 Status: {status_str} - {status_name}")
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
    
    def get_backtest_results(self, lab_id: str) -> Dict[str, Any]:
        """Get backtest results and analyze performance"""
        logger.info("📊 Getting backtest results...")
        
        try:
            results = api.get_backtest_result(
                authenticator.get_executor(),
                GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=0,
                    page_lenght=1000
                )
            )
            
            if not results.items:
                logger.error("❌ No backtest results found")
                return None
            
            # Sort by ROI
            sorted_results = sorted(results.items, key=lambda x: x.summary.ReturnOnInvestment if x.summary else 0, reverse=True)
            
            analysis = {
                "total_configurations": len(results.items),
                "best_roi": sorted_results[0].summary.ReturnOnInvestment if sorted_results[0].summary else 0,
                "best_backtest_id": sorted_results[0].backtest_id,
                "best_parameters": getattr(sorted_results[0], 'parameters', {}),
                "top_3_results": sorted_results[:3],
                "all_results": results.items
            }
            
            logger.info(f"✅ Results analyzed:")
            logger.info(f"   Total configurations: {analysis['total_configurations']}")
            logger.info(f"   Best ROI: {analysis['best_roi']:.2f}%")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to get results: {e}")
            return None
    
    def activate_top_bots(self, lab_id: str, top_results: List[Any]) -> List[Dict[str, Any]]:
        """Activate top 3 bots from backtest results"""
        logger.info("🤖 Activating top 3 bots...")
        
        activated_bots = []
        
        for i, result in enumerate(top_results[:3], 1):
            try:
                roi = result.summary.ReturnOnInvestment if result.summary else 0
                logger.info(f"  🚀 Activating bot {i} (ROI: {roi:.2f}%)")
                
                bot = api.add_bot_from_lab(
                    authenticator.get_executor(),
                    AddBotFromLabRequest(
                        lab_id=lab_id,
                        backtest_id=result.backtest_id,
                        name=f"RefactoredTop{i}_MadHatter_BTC_USDT_{int(time.time())}"
                    )
                )
                
                activated_bots.append({
                    "rank": i,
                    "bot_id": bot.bot_id,
                    "backtest_id": result.backtest_id,
                    "roi": roi,
                    "parameters": getattr(result, 'parameters', {})
                })
                
                logger.info(f"    ✅ Bot activated: {bot.bot_id}")
                
            except Exception as e:
                logger.error(f"    ❌ Failed to activate bot {i}: {e}")
        
        return activated_bots
    
    def setup_lab_optimization(self, executor, lab_id: str, optimization_plan: List[Dict[str, Any]]) -> bool:
        """Setup lab parameters with optimization plan using working EXAMPLE lab pattern, preserving market_tag/account_id"""
        logger.info("🔧 Setting up lab optimization...")
        
        try:
            # Get current lab details
            lab_details = api.get_lab_details(executor, lab_id)

            # --- FIX: Preserve market_tag and account_id ---
            original_market_tag = lab_details.settings.market_tag
            original_account_id = lab_details.settings.account_id
            if not original_market_tag or original_market_tag == "":
                logger.warning(f"⚠️ market_tag is empty before update! (lab_id={lab_id})")
            if not original_account_id or original_account_id == "":
                logger.warning(f"⚠️ account_id is empty before update! (lab_id={lab_id})")

            # Update parameters directly in lab_details object (working pattern)
            updated_parameters = []
            for param in lab_details.parameters:
                key = param.get('K', '')
                current_value = param.get('O', [None])[0] if param.get('O') else None
                # Find corresponding optimization plan
                plan_item = next((item for item in optimization_plan if item['key'] == key), None)
                if plan_item:
                    param['O'] = [str(plan_item['value'])]
                updated_parameters.append(param)
            lab_details.parameters = updated_parameters
            # --- FIX: Always restore original market_tag and account_id before update ---
            lab_details.settings.market_tag = original_market_tag
            lab_details.settings.account_id = original_account_id
            api.update_lab_details(executor, lab_details)
            logger.info(f"✅ Lab optimization applied successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error applying lab optimization: {e}")
            return False
    
    def _determine_optimization_range(self, key: str, current_value: Any, decimals: int, param_type: int) -> List[float]:
        """Determine intelligent optimization range for a parameter - using working EXAMPLE lab pattern"""
        try:
            current = float(current_value)
        except (ValueError, TypeError):
            return [current_value]
        
        # Use smaller, more focused ranges like the working EXAMPLE lab
        if 'length' in key.lower():
            # For length parameters, use 3-5 values around current
            if current <= 10:
                values = [max(1, current-2), current, current+2]
            else:
                values = [max(1, current-3), current, current+3]
                
        elif 'fast' in key.lower():
            # For MACD Fast, use 5 values like working example
            values = [9, 14, 19, 24, 29]
            
        elif 'slow' in key.lower():
            # For MACD Slow, use 8 values like working example
            values = [30, 40, 50, 60, 70, 80, 90, 100]
            
        elif 'signal' in key.lower():
            # For MACD Signal, use 7 values like working example
            values = [6, 7, 8, 9, 10, 11, 12]
            
        elif 'buy' in key.lower():
            # For RSI Buy Level, use 4 values like working example
            values = [20, 25, 30, 35]
            
        elif 'sell' in key.lower():
            # For RSI Sell Level, use 4 values like working example
            values = [65, 70, 75, 80]
            
        elif 'devup' in key.lower() or 'devdown' in key.lower():
            # For BBands Dev, use 2 values like working example
            values = [1, 2]
            
        elif 'bbands length' in key.lower():
            # For BBands Length, use 5 values like working example
            values = [8, 9, 10, 11, 12]
            
        else:
            # Default: use 3 values around current
            if param_type == 0:  # INTEGER
                values = [max(1, current-1), current, current+1]
            else:  # DECIMAL
                values = [round(current * 0.8, decimals), current, round(current * 1.2, decimals)]
        
        logger.info(f"    📊 {key}: {current} → {values} ({len(values)} values)")
        return values
    
    def run_test(self):
        """Run the complete optimization test"""
        logger.info("🚀 Refactored Single Lab Parameter Optimization Test - MadHatter Bot")
        logger.info("=" * 70)
        
        # 1. Setup
        if not self.setup():
            return
        
        # 2. Get markets and find BTC/USDT
        markets = self.market_fetcher.get_markets_efficiently(["BINANCE"])
        pair_to_markets = self.market_fetcher.find_trading_pairs(markets, ["BTC/USDT"])
        
        if not pair_to_markets or "BTC/USDT" not in pair_to_markets:
            logger.error("❌ BTC/USDT market not found")
            return
        
        btc_market = pair_to_markets["BTC/USDT"][0]
        
        # 3. Get MadHatter script
        scripts = self.market_fetcher.get_bot_scripts(
            authenticator.get_executor(), 
            [BOT_SCRIPTS["MadHatter"]]
        )
        
        if not scripts:
            logger.error("❌ MadHatter Bot not found")
            return
        
        script = scripts[BOT_SCRIPTS["MadHatter"]]
        
        # 4. Get account
        accounts = self.market_fetcher.get_accounts(authenticator.get_executor())
        if not accounts:
            logger.error("❌ No accounts available")
            return
        account = accounts[0]
        logger.info(f"📋 Using account: {account.name} (ID: {account.account_id})")
        
        # 5. Create optimized lab
        lab_result = self.create_optimized_lab(
            script_id=script.script_id,
            account_id=account.account_id,
            market=self.market_fetcher.format_market_string(btc_market)
        )
        
        if not lab_result:
            return
        
        # 6. Run backtest
        backtest_result = self.run_backtest(lab_result['lab'].lab_id)
        if not backtest_result:
            return
        
        # 7. Wait for completion
        if not self.wait_for_completion(lab_result['lab'].lab_id):
            return
        
        # 8. Get results
        analysis = self.get_backtest_results(lab_result['lab'].lab_id)
        if not analysis:
            return
        
        # 9. Activate top 3 bots
        activated_bots = self.activate_top_bots(lab_result['lab'].lab_id, analysis['top_3_results'])
        
        # 10. Summary
        logger.info(f"\n{'='*70}")
        logger.info("📋 REFACTORED TEST SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Lab created: {lab_result['lab'].lab_id}")
        logger.info(f"✅ Configurations tested: {analysis['total_configurations']}")
        logger.info(f"✅ Best ROI: {analysis['best_roi']:.2f}%")
        logger.info(f"✅ Bots activated: {len(activated_bots)}")
        
        logger.info(f"\n🏆 Top 3 Results:")
        for i, result in enumerate(analysis['top_3_results'], 1):
            roi = result.summary.ReturnOnInvestment if result.summary else 0
            params = getattr(result, 'parameters', {})
            logger.info(f"  {i}. ROI: {roi:.2f}%, Parameters: {params}")
        
        logger.info(f"\n🤖 Activated Bots:")
        for bot in activated_bots:
            logger.info(f"  Rank {bot['rank']}: Bot {bot['bot_id']} (ROI: {bot['roi']:.2f}%)")
        
        logger.info(f"\n🎉 Refactored test completed successfully!")

def main():
    """Main function"""
    optimizer = SingleLabOptimizer()
    optimizer.run_test()

if __name__ == "__main__":
    main() 
        try:
            current = float(current_value)
        except (ValueError, TypeError):
            return [current_value]
        
        # Use smaller, more focused ranges like the working EXAMPLE lab
        if 'length' in key.lower():
            # For length parameters, use 3-5 values around current
            if current <= 10:
                values = [max(1, current-2), current, current+2]
            else:
                values = [max(1, current-3), current, current+3]
                
        elif 'fast' in key.lower():
            # For MACD Fast, use 5 values like working example
            values = [9, 14, 19, 24, 29]
            
        elif 'slow' in key.lower():
            # For MACD Slow, use 8 values like working example
            values = [30, 40, 50, 60, 70, 80, 90, 100]
            
        elif 'signal' in key.lower():
            # For MACD Signal, use 7 values like working example
            values = [6, 7, 8, 9, 10, 11, 12]
            
        elif 'buy' in key.lower():
            # For RSI Buy Level, use 4 values like working example
            values = [20, 25, 30, 35]
            
        elif 'sell' in key.lower():
            # For RSI Sell Level, use 4 values like working example
            values = [65, 70, 75, 80]
            
        elif 'devup' in key.lower() or 'devdown' in key.lower():
            # For BBands Dev, use 2 values like working example
            values = [1, 2]
            
        elif 'bbands length' in key.lower():
            # For BBands Length, use 5 values like working example
            values = [8, 9, 10, 11, 12]
            
        else:
            # Default: use 3 values around current
            if param_type == 0:  # INTEGER
                values = [max(1, current-1), current, current+1]
            else:  # DECIMAL
                values = [round(current * 0.8, decimals), current, round(current * 1.2, decimals)]
        
        logger.info(f"    📊 {key}: {current} → {values} ({len(values)} values)")
        return values
    
    def run_test(self):
        """Run the complete optimization test"""
        logger.info("🚀 Refactored Single Lab Parameter Optimization Test - MadHatter Bot")
        logger.info("=" * 70)
        
        # 1. Setup
        if not self.setup():
            return
        
        # 2. Get markets and find BTC/USDT
        markets = self.market_fetcher.get_markets_efficiently(["BINANCE"])
        pair_to_markets = self.market_fetcher.find_trading_pairs(markets, ["BTC/USDT"])
        
        if not pair_to_markets or "BTC/USDT" not in pair_to_markets:
            logger.error("❌ BTC/USDT market not found")
            return
        
        btc_market = pair_to_markets["BTC/USDT"][0]
        
        # 3. Get MadHatter script
        scripts = self.market_fetcher.get_bot_scripts(
            authenticator.get_executor(), 
            [BOT_SCRIPTS["MadHatter"]]
        )
        
        if not scripts:
            logger.error("❌ MadHatter Bot not found")
            return
        
        script = scripts[BOT_SCRIPTS["MadHatter"]]
        
        # 4. Get account
        accounts = self.market_fetcher.get_accounts(authenticator.get_executor())
        if not accounts:
            logger.error("❌ No accounts available")
            return
        account = accounts[0]
        logger.info(f"📋 Using account: {account.name} (ID: {account.account_id})")
        
        # 5. Create optimized lab
        lab_result = self.create_optimized_lab(
            script_id=script.script_id,
            account_id=account.account_id,
            market=self.market_fetcher.format_market_string(btc_market)
        )
        
        if not lab_result:
            return
        
        # 6. Run backtest
        backtest_result = self.run_backtest(lab_result['lab'].lab_id)
        if not backtest_result:
            return
        
        # 7. Wait for completion
        if not self.wait_for_completion(lab_result['lab'].lab_id):
            return
        
        # 8. Get results
        analysis = self.get_backtest_results(lab_result['lab'].lab_id)
        if not analysis:
            return
        
        # 9. Activate top 3 bots
        activated_bots = self.activate_top_bots(lab_result['lab'].lab_id, analysis['top_3_results'])
        
        # 10. Summary
        logger.info(f"\n{'='*70}")
        logger.info("📋 REFACTORED TEST SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Lab created: {lab_result['lab'].lab_id}")
        logger.info(f"✅ Configurations tested: {analysis['total_configurations']}")
        logger.info(f"✅ Best ROI: {analysis['best_roi']:.2f}%")
        logger.info(f"✅ Bots activated: {len(activated_bots)}")
        
        logger.info(f"\n🏆 Top 3 Results:")
        for i, result in enumerate(analysis['top_3_results'], 1):
            roi = result.summary.ReturnOnInvestment if result.summary else 0
            params = getattr(result, 'parameters', {})
            logger.info(f"  {i}. ROI: {roi:.2f}%, Parameters: {params}")
        
        logger.info(f"\n🤖 Activated Bots:")
        for bot in activated_bots:
            logger.info(f"  Rank {bot['rank']}: Bot {bot['bot_id']} (ROI: {bot['roi']:.2f}%)")
        
        logger.info(f"\n🎉 Refactored test completed successfully!")

def main():
    """Main function"""
    optimizer = SingleLabOptimizer()
    optimizer.run_test()

if __name__ == "__main__":
    main() 
        try:
            current = float(current_value)
        except (ValueError, TypeError):
            return [current_value]
        
        # Use smaller, more focused ranges like the working EXAMPLE lab
        if 'length' in key.lower():
            # For length parameters, use 3-5 values around current
            if current <= 10:
                values = [max(1, current-2), current, current+2]
            else:
                values = [max(1, current-3), current, current+3]
                
        elif 'fast' in key.lower():
            # For MACD Fast, use 5 values like working example
            values = [9, 14, 19, 24, 29]
            
        elif 'slow' in key.lower():
            # For MACD Slow, use 8 values like working example
            values = [30, 40, 50, 60, 70, 80, 90, 100]
            
        elif 'signal' in key.lower():
            # For MACD Signal, use 7 values like working example
            values = [6, 7, 8, 9, 10, 11, 12]
            
        elif 'buy' in key.lower():
            # For RSI Buy Level, use 4 values like working example
            values = [20, 25, 30, 35]
            
        elif 'sell' in key.lower():
            # For RSI Sell Level, use 4 values like working example
            values = [65, 70, 75, 80]
            
        elif 'devup' in key.lower() or 'devdown' in key.lower():
            # For BBands Dev, use 2 values like working example
            values = [1, 2]
            
        elif 'bbands length' in key.lower():
            # For BBands Length, use 5 values like working example
            values = [8, 9, 10, 11, 12]
            
        else:
            # Default: use 3 values around current
            if param_type == 0:  # INTEGER
                values = [max(1, current-1), current, current+1]
            else:  # DECIMAL
                values = [round(current * 0.8, decimals), current, round(current * 1.2, decimals)]
        
        logger.info(f"    📊 {key}: {current} → {values} ({len(values)} values)")
        return values
    
    def run_test(self):
        """Run the complete optimization test"""
        logger.info("🚀 Refactored Single Lab Parameter Optimization Test - MadHatter Bot")
        logger.info("=" * 70)
        
        # 1. Setup
        if not self.setup():
            return
        
        # 2. Get markets and find BTC/USDT
        markets = self.market_fetcher.get_markets_efficiently(["BINANCE"])
        pair_to_markets = self.market_fetcher.find_trading_pairs(markets, ["BTC/USDT"])
        
        if not pair_to_markets or "BTC/USDT" not in pair_to_markets:
            logger.error("❌ BTC/USDT market not found")
            return
        
        btc_market = pair_to_markets["BTC/USDT"][0]
        
        # 3. Get MadHatter script
        scripts = self.market_fetcher.get_bot_scripts(
            authenticator.get_executor(), 
            [BOT_SCRIPTS["MadHatter"]]
        )
        
        if not scripts:
            logger.error("❌ MadHatter Bot not found")
            return
        
        script = scripts[BOT_SCRIPTS["MadHatter"]]
        
        # 4. Get account
        accounts = self.market_fetcher.get_accounts(authenticator.get_executor())
        if not accounts:
            logger.error("❌ No accounts available")
            return
        account = accounts[0]
        logger.info(f"📋 Using account: {account.name} (ID: {account.account_id})")
        
        # 5. Create optimized lab
        lab_result = self.create_optimized_lab(
            script_id=script.script_id,
            account_id=account.account_id,
            market=self.market_fetcher.format_market_string(btc_market)
        )
        
        if not lab_result:
            return
        
        # 6. Run backtest
        backtest_result = self.run_backtest(lab_result['lab'].lab_id)
        if not backtest_result:
            return
        
        # 7. Wait for completion
        if not self.wait_for_completion(lab_result['lab'].lab_id):
            return
        
        # 8. Get results
        analysis = self.get_backtest_results(lab_result['lab'].lab_id)
        if not analysis:
            return
        
        # 9. Activate top 3 bots
        activated_bots = self.activate_top_bots(lab_result['lab'].lab_id, analysis['top_3_results'])
        
        # 10. Summary
        logger.info(f"\n{'='*70}")
        logger.info("📋 REFACTORED TEST SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Lab created: {lab_result['lab'].lab_id}")
        logger.info(f"✅ Configurations tested: {analysis['total_configurations']}")
        logger.info(f"✅ Best ROI: {analysis['best_roi']:.2f}%")
        logger.info(f"✅ Bots activated: {len(activated_bots)}")
        
        logger.info(f"\n🏆 Top 3 Results:")
        for i, result in enumerate(analysis['top_3_results'], 1):
            roi = result.summary.ReturnOnInvestment if result.summary else 0
            params = getattr(result, 'parameters', {})
            logger.info(f"  {i}. ROI: {roi:.2f}%, Parameters: {params}")
        
        logger.info(f"\n🤖 Activated Bots:")
        for bot in activated_bots:
            logger.info(f"  Rank {bot['rank']}: Bot {bot['bot_id']} (ROI: {bot['roi']:.2f}%)")
        
        logger.info(f"\n🎉 Refactored test completed successfully!")

def main():
    """Main function"""
    optimizer = SingleLabOptimizer()
    optimizer.run_test()

if __name__ == "__main__":
    main() 