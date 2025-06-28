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

import time
import logging
from datetime import datetime
from typing import Dict, List, Any

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
        self.market_fetcher = MarketFetcher(authenticator.get_price_api())
        return True
    
    def create_optimized_lab(self, script_id: str, account_id: str, market: str) -> Dict[str, Any]:
        """Create lab with intelligent parameter optimization"""
        logger.info("📋 Creating optimized MadHatter lab...")
        
        try:
            lab_name = f"RefactoredMadHatter_BTC_USDT_{int(time.time())}"
            
            lab = api.create_lab(
                authenticator.get_executor(),
                CreateLabRequest(
                    script_id=script_id,
                    name=lab_name,
                    account_id=account_id,
                    market=market,
                    interval=1,
                    default_price_data_style="CandleStick"
                )
            )
            logger.info(f"✅ Lab created: {lab.lab_id}")
            
            # Get lab details
            lab_details = api.get_lab_details(authenticator.get_executor(), lab.lab_id)
            logger.info(f"📊 Lab has {len(lab_details.parameters)} parameters")
            
            # Analyze parameters for optimization
            optimization_plan = []
            for param in lab_details.parameters:
                analysis = self.parameter_optimizer.analyze_parameter_for_optimization(param)
                optimization_plan.append(analysis)
            
            # Setup optimization
            if not self.parameter_optimizer.setup_lab_optimization(
                authenticator.get_executor(), lab.lab_id, optimization_plan
            ):
                logger.warning("⚠️ Failed to setup optimization, continuing with default parameters")
            
            return {
                "lab": lab,
                "lab_details": lab_details,
                "optimization_plan": optimization_plan
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create lab: {e}")
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
                
                if status != last_status:
                    status_desc = LAB_STATUS.get(status, f'UNKNOWN({status})')
                    logger.info(f"  🔄 Status: {status} - {status_desc}")
                    last_status = status
                
                if status == '3':  # COMPLETED
                    logger.info("✅ Backtest completed successfully")
                    return True
                elif status in ['4', '5']:  # CANCELLED or ERROR
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