#!/usr/bin/env python3
"""
Create Top 5 Performing Bots - Simple Version

This script creates top 5 performing bots from labs that have backtests.
Starting small and scaling up as requested.
"""

import os
import sys
import json
import csv
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor, get_full_backtest_runtime_data
from pyHaasAPI.model import GetBacktestResultRequest, AddBotFromLabRequest

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Backtest result data"""
    backtest_id: str
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    pc_value: float
    realized_profits_usdt: float
    generation_idx: Optional[int]
    population_idx: Optional[int]
    market_tag: str

@dataclass
class BotCreationResult:
    """Result of creating a bot"""
    lab_id: str
    lab_name: str
    backtest_id: str
    bot_id: str
    bot_name: str
    roi: float
    win_rate: float
    creation_time: str
    status: str

class SimpleTopBotCreator:
    """Creates top 5 performing bots from labs with backtests"""
    
    def __init__(self, executor: RequestsExecutor):
        self.executor = executor
        self.output_dir = f"top_bots_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)
        self.bot_results = []
        
        # Labs with backtests (from our analysis)
        self.labs_with_backtests = [
            {
                'lab_id': '272bbb66-f2b3-4eae-8c32-714747dcb827',
                'lab_name': 'RSI-VWAP_LTC_feb23',
                'status': 3
            },
            {
                'lab_id': '6fe2213c-00bd-41d8-b4de-73adf1eac0e8',
                'lab_name': 'RSI-VWAP_BNB_3years',
                'status': 3
            },
            {
                'lab_id': '86a66f48-a75b-4d40-9d3e-8538a845a4fa',
                'lab_name': 'RSI-VWAP_ETH_Dec23',
                'status': 2
            },
            {
                'lab_id': '8a03fde1-c755-494c-a975-daeed1257518',
                'lab_name': 'RSI-VWAP_UNI_3years',
                'status': 3
            },
            {
                'lab_id': 'cb87a095-3410-4270-81f0-20f8df928696',
                'lab_name': 'RSI-VWAP_SOL_3years',
                'status': 3
            }
        ]
    
    def fetch_lab_backtests(self, lab_id: str, max_backtests: int = 100) -> List[Dict[str, Any]]:
        """Fetch backtests from a specific lab"""
        try:
            logger.info(f"Fetching up to {max_backtests} backtests from lab {lab_id[:8]}...")
            
            all_backtests = []
            next_page_id = 0
            page_size = 100
            
            while len(all_backtests) < max_backtests:
                request = GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=next_page_id,
                    page_lenght=page_size
                )
                
                response = api.get_backtest_result(self.executor, request)
                
                if not response or not response.items:
                    logger.info(f"No more backtests found for lab {lab_id[:8]}")
                    break
                
                backtests = response.items
                all_backtests.extend(backtests)
                logger.info(f"Fetched {len(backtests)} backtests, total: {len(all_backtests)}")
                
                # Get next page ID for pagination
                next_page_id = response.next_page_id
                if not next_page_id:
                    logger.info("Reached last page")
                    break
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            logger.info(f"Successfully fetched {len(all_backtests)} backtests from lab {lab_id[:8]}")
            return all_backtests[:max_backtests]
            
        except Exception as e:
            logger.error(f"Error fetching backtests from lab {lab_id[:8]}: {e}")
            return []
    
    def analyze_backtest(self, backtest_obj: Any, lab_id: str) -> Optional[BacktestResult]:
        """Analyze a single backtest and return performance data"""
        try:
            backtest_id = getattr(backtest_obj, 'backtest_id', None)
            if not backtest_id:
                logger.warning("Backtest missing backtest_id")
                return None
            
            logger.info(f"Analyzing backtest {backtest_id[:8]}...")
            
            # Get full runtime data for detailed analysis
            runtime_data = get_full_backtest_runtime_data(self.executor, lab_id, backtest_id)
            if not runtime_data:
                logger.warning(f"Could not get runtime data for {backtest_id[:8]}")
                return None
            
            # Extract basic info
            generation_idx = getattr(backtest_obj, 'generation_idx', None)
            population_idx = getattr(backtest_obj, 'population_idx', None)
            
            # Extract settings
            settings = getattr(backtest_obj, 'settings', None)
            market_tag = getattr(settings, 'market_tag', '') if settings else ''
            
            # Initialize analysis
            analysis = {
                'roi_percentage': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'max_drawdown': 0.0,
                'pc_value': 0.0,
                'realized_profits_usdt': 0.0
            }
            
            # Extract performance data from runtime Reports
            if hasattr(runtime_data, 'Reports') and runtime_data.Reports:
                report_key = list(runtime_data.Reports.keys())[0]
                report_data = runtime_data.Reports[report_key]
                
                # Extract performance metrics
                if hasattr(report_data, 'PR'):
                    pr_data = report_data.PR
                    analysis['realized_profits_usdt'] = float(pr_data.RP) if hasattr(pr_data, 'RP') else 0.0
                    analysis['roi_percentage'] = float(pr_data.ROI) if hasattr(pr_data, 'ROI') else 0.0
                    analysis['max_drawdown'] = float(pr_data.RM) if hasattr(pr_data, 'RM') else 0.0
                    analysis['pc_value'] = float(pr_data.PC) if hasattr(pr_data, 'PC') else 0.0
                
                # Extract trade statistics
                if hasattr(report_data, 'P'):
                    p_data = report_data.P
                    analysis['total_trades'] = int(p_data.C) if hasattr(p_data, 'C') else 0
                    winning_trades = int(p_data.W) if hasattr(p_data, 'W') else 0
                    analysis['win_rate'] = (winning_trades / analysis['total_trades']) if analysis['total_trades'] > 0 else 0.0
            
            # Create BacktestResult object
            backtest_result = BacktestResult(
                backtest_id=backtest_id,
                roi_percentage=analysis['roi_percentage'],
                win_rate=analysis['win_rate'],
                total_trades=analysis['total_trades'],
                max_drawdown=analysis['max_drawdown'],
                pc_value=analysis['pc_value'],
                realized_profits_usdt=analysis['realized_profits_usdt'],
                generation_idx=generation_idx,
                population_idx=population_idx,
                market_tag=market_tag
            )
            
            logger.info(f"Analysis complete: ROI={backtest_result.roi_percentage:.2f}%, Win Rate={backtest_result.win_rate:.1%}")
            return backtest_result
            
        except Exception as e:
            logger.error(f"Error analyzing backtest: {e}")
            return None
    
    def select_top_backtests(self, backtests: List[BacktestResult], top_count: int = 5) -> List[BacktestResult]:
        """Select top performing backtests based on ROI and other metrics"""
        try:
            if not backtests:
                return []
            
            # Filter for positive ROI backtests
            positive_backtests = [bt for bt in backtests if bt.roi_percentage > 0]
            logger.info(f"Found {len(positive_backtests)} backtests with positive ROI")
            
            if not positive_backtests:
                logger.warning("No positive ROI backtests found")
                return []
            
            # Sort by ROI (descending) and then by win rate (descending)
            sorted_backtests = sorted(
                positive_backtests,
                key=lambda x: (x.roi_percentage, x.win_rate, -x.max_drawdown),
                reverse=True
            )
            
            # Select top performers
            top_backtests = sorted_backtests[:top_count]
            
            logger.info(f"Selected top {len(top_backtests)} backtests:")
            for i, bt in enumerate(top_backtests, 1):
                logger.info(f"  {i}. ROI: {bt.roi_percentage:.2f}%, Win Rate: {bt.win_rate:.1%}, Trades: {bt.total_trades}")
            
            return top_backtests
            
        except Exception as e:
            logger.error(f"Error selecting top backtests: {e}")
            return []
    
    def create_bot_from_backtest(self, lab_id: str, lab_name: str, backtest: BacktestResult, account_id: str) -> Optional[BotCreationResult]:
        """Create a bot from a top performing backtest"""
        try:
            logger.info(f"Creating bot from backtest {backtest.backtest_id[:8]}...")
            
            # Generate bot name following the preferred format: lab_name, ROI, pop/gen
            generation_pop = ""
            if backtest.generation_idx is not None and backtest.population_idx is not None:
                generation_pop = f"G{backtest.generation_idx}P{backtest.population_idx}"
            elif backtest.generation_idx is not None:
                generation_pop = f"G{backtest.generation_idx}"
            
            bot_name = f"{lab_name[:20]}_{backtest.roi_percentage:.1f}%ROI_{generation_pop}".replace(" ", "_")
            
            # Create bot request
            bot_request = AddBotFromLabRequest(
                lab_id=lab_id,
                backtest_id=backtest.backtest_id,
                account_id=account_id,
                bot_name=bot_name,
                position_size=2000,  # Default position size
                market_tag=backtest.market_tag or "BINANCEFUTURES_BTC_USDT_PERPETUAL"
            )
            
            # Create the bot
            bot_response = api.add_bot_from_lab(self.executor, bot_request)
            
            if bot_response and hasattr(bot_response, 'bot_id'):
                bot_id = bot_response.bot_id
                logger.info(f"Successfully created bot: {bot_id[:8]} with name: {bot_name}")
                
                return BotCreationResult(
                    lab_id=lab_id,
                    lab_name=lab_name,
                    backtest_id=backtest.backtest_id,
                    bot_id=bot_id,
                    bot_name=bot_name,
                    roi=backtest.roi_percentage,
                    win_rate=backtest.win_rate,
                    creation_time=datetime.now().isoformat(),
                    status="created"
                )
            else:
                logger.error(f"Failed to create bot from backtest {backtest.backtest_id[:8]}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating bot from backtest {backtest.backtest_id[:8]}: {e}")
            return None
    
    def get_available_account(self) -> Optional[str]:
        """Get an available account ID for bot creation"""
        try:
            # Get all accounts
            accounts = api.get_all_accounts(self.executor)
            if not accounts:
                logger.error("No accounts found")
                return None
            
            # Get all bots to see which accounts are used
            bots = api.get_all_bots(self.executor)
            used_accounts = set()
            
            for bot in bots:
                if hasattr(bot, 'account_id') and bot.account_id:
                    used_accounts.add(bot.account_id)
            
            # Find available account
            for account in accounts:
                if account['AID'] not in used_accounts:
                    logger.info(f"Using account: {account['N']} (ID: {account['AID']})")
                    return account['AID']
            
            logger.warning("All accounts are in use by bots")
            return None
            
        except Exception as e:
            logger.error(f"Error getting available account: {e}")
            return None
    
    def process_single_lab(self, lab: Dict[str, Any]) -> bool:
        """Process a single lab: fetch backtests, analyze, create top 5 bots"""
        lab_id = lab['lab_id']
        lab_name = lab['lab_name']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Lab: {lab_name} (ID: {lab_id[:8]})")
        logger.info(f"{'='*60}")
        
        try:
            # Step 1: Fetch backtests
            backtests = self.fetch_lab_backtests(lab_id, max_backtests=100)
            if not backtests:
                logger.warning(f"No backtests found for lab {lab_name}")
                return False
            
            # Step 2: Analyze backtests
            logger.info(f"Analyzing {len(backtests)} backtests...")
            analyzed_backtests = []
            
            for i, backtest_obj in enumerate(backtests):
                logger.info(f"Analyzing backtest {i+1}/{len(backtests)}...")
                analysis = self.analyze_backtest(backtest_obj, lab_id)
                if analysis:
                    analyzed_backtests.append(analysis)
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            logger.info(f"Successfully analyzed {len(analyzed_backtests)} backtests")
            
            # Step 3: Select top 5 backtests
            top_backtests = self.select_top_backtests(analyzed_backtests, top_count=5)
            if not top_backtests:
                logger.warning(f"No top backtests selected for lab {lab_name}")
                return False
            
            # Step 4: Create bots from top backtests
            logger.info(f"Creating bots from top {len(top_backtests)} backtests...")
            bots_created = 0
            
            # Get available account
            account_id = self.get_available_account()
            if not account_id:
                logger.error(f"No available account for bot creation in lab {lab_name}")
                return False
            
            for i, backtest in enumerate(top_backtests):
                logger.info(f"Creating bot {i+1}/{len(top_backtests)} from backtest {backtest.backtest_id[:8]}...")
                bot_result = self.create_bot_from_backtest(lab_id, lab_name, backtest, account_id)
                
                if bot_result:
                    bots_created += 1
                    self.bot_results.append(bot_result)
                    logger.info(f"✅ Bot {i+1} created successfully")
                else:
                    logger.error(f"❌ Failed to create bot {i+1}")
                
                # Small delay between bot creations
                time.sleep(0.5)
            
            logger.info(f"Lab {lab_name} processing complete: {bots_created} bots created")
            return True
            
        except Exception as e:
            logger.error(f"Error processing lab {lab_name}: {e}")
            return False
    
    def save_results(self):
        """Save all results to files"""
        try:
            # Save bot creation results
            bot_results_file = os.path.join(self.output_dir, "bot_creation_results.csv")
            with open(bot_results_file, 'w', newline='', encoding='utf-8') as f:
                if self.bot_results:
                    writer = csv.DictWriter(f, fieldnames=self.bot_results[0].__dict__.keys())
                    writer.writeheader()
                    for result in self.bot_results:
                        writer.writerow(result.__dict__)
            
            # Save summary
            summary_file = os.path.join(self.output_dir, "summary.json")
            summary = {
                "total_labs_processed": len(self.labs_with_backtests),
                "total_bots_created": len(self.bot_results),
                "processing_timestamp": datetime.now().isoformat(),
                "output_directory": self.output_dir
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Results saved to {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting Simple Top Bot Creation for Labs with Backtests")
        logger.info("=" * 60)
        
        try:
            # Process labs one by one
            for i, lab in enumerate(self.labs_with_backtests, 1):
                logger.info(f"\n📊 Processing lab {i}/{len(self.labs_with_backtests)}: {lab['lab_name']}")
                
                # Process the lab
                success = self.process_single_lab(lab)
                
                if success:
                    logger.info(f"✅ Lab {lab['lab_name']} processed successfully")
                else:
                    logger.warning(f"⚠️ Lab {lab['lab_name']} processing failed or incomplete")
                
                # Save intermediate results
                self.save_results()
                
                # Small delay between labs
                if i < len(self.labs_with_backtests):
                    logger.info("Waiting 2 seconds before processing next lab...")
                    time.sleep(2)
            
            # Final results
            logger.info("\n🎉 All labs processed!")
            logger.info("=" * 60)
            
            total_bots = len(self.bot_results)
            logger.info(f"📊 Final Results:")
            logger.info(f"  • Labs processed: {len(self.labs_with_backtests)}")
            logger.info(f"  • Total bots created: {total_bots}")
            logger.info(f"  • Output directory: {self.output_dir}")
            
            # Save final results
            self.save_results()
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            # Save what we have so far
            self.save_results()

def main():
    """Main function"""
    # Initialize API connection
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        logger.error("API_EMAIL and API_PASSWORD must be set in .env file")
        return

    logger.info(f"🔌 Connecting to HaasOnline API: {api_host}:{api_port}")

    try:
        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )

        # Authenticate
        executor = haas_api.authenticate(api_email, api_password)
        logger.info("✅ Successfully connected to HaasOnline API")

    except Exception as e:
        logger.error(f"❌ Failed to connect to API: {e}")
        return

    # Create and run the simple top bot creator
    bot_creator = SimpleTopBotCreator(executor)
    bot_creator.run()

if __name__ == "__main__":
    main()

