#!/usr/bin/env python3
"""
Create Top 5 Performing Bots for New Server

This script:
1. Analyzes each lab to find those with ≥10 backtests
2. Fetches and analyzes backtests for performance metrics
3. Selects top 5 performers based on ROI, win rate, drawdown
4. Creates bots with proper naming (including win rate like WR0.62)
5. Confirms bot creation and saves results to CSV

Usage: python create_top_bots_new_server.py
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
from pyHaasAPI.api import (
    RequestsExecutor, 
    get_full_backtest_runtime_data,
    configure_bot_settings
)
from pyHaasAPI.model import GetBacktestResultRequest, AddBotFromLabRequest

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'top_bots_new_server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Reduce verbosity of other loggers
logging.getLogger('pyHaasAPI').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

@dataclass
class BacktestAnalysis:
    """Backtest analysis result"""
    backtest_id: str
    lab_id: str
    lab_name: str
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    pc_value: float
    realized_profits_usdt: float
    fees_usdt: float
    market_tag: str
    generation_idx: Optional[int]
    population_idx: Optional[int]
    script_id: str
    start_time: str
    end_time: str
    total_positions: int
    winning_trades: int
    losing_trades: int
    orders: int
    beats_buy_hold: bool

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
    account_id: str
    market: str
    creation_time: str
    status: str

class TopBotCreator:
    """Creates top 5 performing bots from labs with ≥10 backtests"""
    
    def __init__(self, executor: RequestsExecutor):
        self.executor = executor
        self.output_dir = f"top_bots_new_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)
        self.lab_analyses = []
        self.bot_results = []
        self.labs_with_many_backtests = []
    
    def analyze_lab_backtest_count(self) -> List[Dict[str, Any]]:
        """Analyze all labs to find those with >100 backtests"""
        logger.info("🔍 Analyzing labs to find those with ≥10 backtests...")
        
        try:
            labs = api.get_all_labs(self.executor)
            logger.info(f"Found {len(labs)} total labs")
            
            labs_with_backtests = []
            
            for i, lab in enumerate(labs, 1):
                lab_id = getattr(lab, 'lab_id', '')
                lab_name = getattr(lab, 'name', 'Unknown')
                lab_status = getattr(lab, 'status', 0)
                
                logger.info(f"Analyzing lab {i}/{len(labs)}: {lab_name}")
                
                # Check if lab is completed
                if lab_status not in [2, 3]:  # 2=completed, 3=completed with results
                    logger.info(f"  ⏭️ Lab {lab_name} not completed (status: {lab_status})")
                    continue
                
                # Fetch backtests to check count
                try:
                    request = GetBacktestResultRequest(
                        lab_id=lab_id,
                        next_page_id=0,
                        page_lenght=100  # Get up to 100 backtests to check
                    )
                    
                    response = api.get_backtest_result(self.executor, request)
                    if response and hasattr(response, 'items'):
                        backtest_count = len(response.items)
                        logger.info(f"  📊 Lab {lab_name} has {backtest_count} backtests")
                        
                        if backtest_count >= 10:  # Lower threshold to 10 backtests
                            labs_with_backtests.append({
                                'lab_id': lab_id,
                                'lab_name': lab_name,
                                'backtest_count': backtest_count,
                                'status': lab_status
                            })
                            logger.info(f"  ✅ Lab {lab_name} qualifies for analysis! ({backtest_count} backtests)")
                        elif backtest_count > 0:
                            logger.info(f"  ⏭️ Lab {lab_name} has {backtest_count} backtests (<10)")
                        else:
                            logger.info(f"  ⏭️ Lab {lab_name} has no backtests yet")
                    else:
                        logger.warning(f"  ⚠️ Could not get backtest response for lab {lab_name}")
                        
                except Exception as e:
                    logger.warning(f"  ⚠️ Error checking lab {lab_name}: {e}")
                    continue
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.5)
            
            logger.info(f"✅ Found {len(labs_with_backtests)} labs with ≥10 backtests")
            self.labs_with_many_backtests = labs_with_backtests
            return labs_with_backtests
            
        except Exception as e:
            logger.error(f"❌ Error analyzing labs: {e}")
            return []
    
    def fetch_lab_backtests(self, lab_id: str, max_backtests: int = 100) -> List[Dict[str, Any]]:
        """Fetch backtests from a specific lab"""
        logger.info(f"📥 Fetching up to {max_backtests} backtests from lab {lab_id[:8]}...")
        
        try:
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
                if not response or not hasattr(response, 'items'):
                    logger.warning(f"No response or items for lab {lab_id[:8]}")
                    break
                
                page_backtests = response.items
                if not page_backtests:
                    logger.info(f"No more backtests for lab {lab_id[:8]}")
                    break
                
                all_backtests.extend(page_backtests)
                logger.info(f"Fetched {len(page_backtests)} backtests (total: {len(all_backtests)})")
                
                # Check if we have more pages
                if hasattr(response, 'next_page_id') and response.next_page_id:
                    next_page_id = response.next_page_id
                else:
                    break
                
                # Small delay between requests
                time.sleep(0.2)
            
            logger.info(f"✅ Fetched {len(all_backtests)} backtests from lab {lab_id[:8]}")
            return all_backtests[:max_backtests]
            
        except Exception as e:
            logger.error(f"❌ Error fetching backtests from lab {lab_id[:8]}: {e}")
            return []
    
    def analyze_backtest(self, backtest: Any, lab_id: str, lab_name: str) -> Optional[BacktestAnalysis]:
        """Analyze a single backtest for performance metrics using summary data"""
        try:
            backtest_id = getattr(backtest, 'backtest_id', '')
            if not backtest_id:
                logger.warning(f"Backtest has no ID")
                return None
            
            logger.info(f"🔍 Analyzing backtest {backtest_id[:8]}...")
            
            # Extract performance metrics from summary
            summary = getattr(backtest, 'summary', None)
            if not summary:
                logger.warning(f"Backtest {backtest_id[:8]} has no summary data")
                return None
            
            # Get ROI from summary
            roi = getattr(summary, 'ReturnOnInvestment', 0.0)
            
            # Get win rate from trades data
            win_rate = 0.0
            trades = getattr(summary, 'Trades', None)
            if trades and hasattr(trades, 'winning_trades') and hasattr(trades, 'losing_trades'):
                winning = getattr(trades, 'winning_trades', 0)
                losing = getattr(trades, 'losing_trades', 0)
                total = winning + losing
                if total > 0:
                    win_rate = winning / total
            
            # Get total trades
            total_trades = 0
            if trades and hasattr(trades, 'total_trades'):
                total_trades = getattr(trades, 'total_trades', 0)
            
            # Get max drawdown (if available)
            max_drawdown = 0.0
            if hasattr(summary, 'MaxDrawdown'):
                max_drawdown = getattr(summary, 'MaxDrawdown', 0.0)
            
            # Skip backtests with no meaningful data
            if roi == 0.0 and total_trades == 0:
                logger.debug(f"Backtest {backtest_id[:8]} has no trading data, skipping")
                return None
            
            # Get generation and population info
            generation_idx = getattr(backtest, 'generation_idx', 0)
            population_idx = getattr(backtest, 'population_idx', 0)
            
            # Get market info
            market = getattr(backtest, 'market_tag', 'Unknown')
            
            # Create analysis dictionary
            analysis = {
                'backtest_id': backtest_id,
                'lab_id': lab_id,
                'lab_name': lab_name,
                'roi_percentage': roi,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'max_drawdown': max_drawdown,
                'pc_value': 0.0,
                'realized_profits_usdt': getattr(summary, 'RealizedProfits', 0.0),
                'fees_usdt': getattr(summary, 'FeeCosts', 0.0),
                'market_tag': market,
                'generation_idx': generation_idx,
                'population_idx': population_idx,
                'script_id': getattr(backtest, 'script_id', ''),
                'start_time': '',
                'end_time': '',
                'total_positions': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'orders': 0,
                'beats_buy_hold': False
            }
            
            # Determine if beats buy & hold
            pc_value = analysis['pc_value']
            roi_value = analysis['roi_percentage']
            analysis['beats_buy_hold'] = roi_value >= pc_value
            
            # Skip backtests with no meaningful data
            if analysis['roi_percentage'] == 0.0 and analysis['total_trades'] == 0:
                logger.warning(f"Backtest {backtest_id[:8]} has no meaningful data")
                return None
            
            # Create BacktestAnalysis object
            return BacktestAnalysis(**analysis)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing backtest {getattr(backtest, 'backtest_id', 'unknown')}: {e}")
            return None
    
    def select_top_backtests(self, analyses: List[BacktestAnalysis], top_count: int = 5) -> List[BacktestAnalysis]:
        """Select top performing backtests based on multiple criteria"""
        if not analyses:
            return []
        
        logger.info(f"🏆 Selecting top {top_count} backtests from {len(analyses)} candidates...")
        
        # Score each backtest based on multiple criteria
        scored_analyses = []
        for analysis in analyses:
            # Skip backtests with no trades
            if analysis.total_trades == 0:
                continue
            
            # Calculate composite score
            # ROI weight: 40%, Win Rate weight: 30%, Drawdown weight: 20%, Trade count weight: 10%
            roi_score = min(analysis.roi_percentage / 1000.0, 1.0) * 0.4  # Normalize ROI to 0-1
            win_rate_score = analysis.win_rate * 0.3
            drawdown_score = max(0, 1.0 - (analysis.max_drawdown / 100.0)) * 0.2  # Lower drawdown = higher score
            trade_score = min(analysis.total_trades / 100.0, 1.0) * 0.1  # Normalize trade count
            
            composite_score = roi_score + win_rate_score + drawdown_score + trade_score
            
            scored_analyses.append((analysis, composite_score))
        
        # Sort by composite score (highest first)
        scored_analyses.sort(key=lambda x: x[1], reverse=True)
        
        # Select top performers
        top_analyses = [analysis for analysis, score in scored_analyses[:top_count]]
        
        logger.info(f"✅ Selected top {len(top_analyses)} backtests:")
        for i, analysis in enumerate(top_analyses, 1):
            logger.info(f"  {i}. ROI: {analysis.roi_percentage:.2f}%, WR: {analysis.win_rate:.2f}, Trades: {analysis.total_trades}")
        
        return top_analyses
    
    def create_bot_name(self, analysis: BacktestAnalysis, lab_name: str) -> str:
        """Create bot name with win rate and other key metrics"""
        # Extract base lab name (remove status prefix)
        base_lab_name = lab_name
        if ' - ' in lab_name:
            base_lab_name = lab_name.split(' - ', 1)[1]
        
        # Format win rate as WR0.62
        win_rate_str = f"WR{analysis.win_rate:.2f}".replace('.', '')
        
        # Format ROI as ROI2389
        roi_str = f"ROI{int(analysis.roi_percentage)}"
        
        # Add generation/population if available
        gen_pop_str = ""
        if analysis.generation_idx is not None and analysis.population_idx is not None:
            gen_pop_str = f"_G{analysis.generation_idx}P{analysis.population_idx}"
        
        # Create final name
        bot_name = f"{base_lab_name}_{win_rate_str}_{roi_str}{gen_pop_str}"
        
        # Clean up name (remove special characters, limit length)
        bot_name = bot_name.replace('(', '').replace(')', '').replace(' ', '_')
        bot_name = bot_name[:50]  # Limit length
        
        return bot_name
    
    def create_bot_from_backtest(self, analysis: BacktestAnalysis) -> Optional[BotCreationResult]:
        """Create a bot from a backtest analysis"""
        try:
            logger.info(f"🤖 Creating bot from backtest {analysis.backtest_id[:8]}...")
            
            # Get available account
            accounts = api.get_all_accounts(self.executor)
            if not accounts:
                logger.error("❌ No accounts available")
                return None
            
            # Use first available account
            account = accounts[0]
            
            # Extract account ID - accounts are dictionaries with AID field
            if isinstance(account, dict):
                account_id = account.get('AID', '')
            else:
                account_id = getattr(account, 'account_id', '')
                if not account_id:
                    account_id = getattr(account, 'id', '')
                    if not account_id:
                        account_id = getattr(account, 'Id', '')
            
            if not account_id:
                logger.error("❌ Account has no ID")
                return None
            
            logger.info(f"Using account: {account_id[:8]}...")
            
            # Create bot name
            bot_name = self.create_bot_name(analysis, analysis.lab_name)
            logger.info(f"Bot name: {bot_name}")
            
            # Get market from analysis
            market = analysis.market_tag or 'BINANCEFUTURES_BTC_USDT_PERPETUAL'
            
            # Create bot using AddBotFromLabRequest
            from pyHaasAPI.model import AddBotFromLabRequest
            
            request = AddBotFromLabRequest(
                lab_id=analysis.lab_id,
                backtest_id=analysis.backtest_id,
                account_id=account_id,
                bot_name=bot_name,
                market=market,
                leverage=20  # Set 20x leverage
            )
            
            new_bot = api.add_bot_from_lab(self.executor, request)
            if not new_bot:
                logger.error(f"❌ Failed to create bot from backtest {analysis.backtest_id[:8]}")
                return None
            
            bot_id = getattr(new_bot, 'bot_id', None)
            if not bot_id:
                logger.error(f"❌ Bot created but has no ID")
                return None
            
            logger.info(f"✅ Bot created successfully: {bot_id[:8]}...")
            
            # Configure bot settings (HEDGE, CROSS, 20x leverage)
            try:
                configure_result = configure_bot_settings(
                    self.executor,
                    bot_id,
                    position_mode=1,  # HEDGE
                    margin_mode=0,     # CROSS
                    leverage=20.0
                )
                
                if configure_result.get("success"):
                    logger.info(f"✅ Bot {bot_id[:8]} configured with HEDGE, CROSS, 20x leverage")
                else:
                    logger.warning(f"⚠️ Bot {bot_id[:8]} configuration failed: {configure_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error configuring bot {bot_id[:8]}: {e}")
            
            # Create result object
            result = BotCreationResult(
                lab_id=analysis.lab_id,
                lab_name=analysis.lab_name,
                backtest_id=analysis.backtest_id,
                bot_id=bot_id,
                bot_name=bot_name,
                roi=analysis.roi_percentage,
                win_rate=analysis.win_rate,
                account_id=account_id,
                market=market,
                creation_time=datetime.now().isoformat(),
                status="created"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error creating bot from backtest {analysis.backtest_id[:8]}: {e}")
            return None
    
    def process_lab(self, lab_info: Dict[str, Any]) -> bool:
        """Process a single lab to create top 5 bots"""
        lab_id = lab_info['lab_id']
        lab_name = lab_info['lab_name']
        backtest_count = lab_info['backtest_count']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔬 Processing Lab: {lab_name}")
        logger.info(f"📊 Backtest Count: {backtest_count}")
        logger.info(f"{'='*60}")
        
        try:
            # Fetch backtests
            backtests = self.fetch_lab_backtests(lab_id, max_backtests=100)
            if not backtests:
                logger.warning(f"⚠️ No backtests found for lab {lab_name}")
                return False
            
            # Analyze backtests
            logger.info(f"🔍 Analyzing {len(backtests)} backtests...")
            analyses = []
            
            for i, backtest in enumerate(backtests, 1):
                logger.info(f"Analyzing backtest {i}/{len(backtests)}...")
                analysis = self.analyze_backtest(backtest, lab_id, lab_name)
                if analysis:
                    analyses.append(analysis)
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
            
            if not analyses:
                logger.warning(f"⚠️ No valid analyses for lab {lab_name}")
                return False
            
            logger.info(f"✅ Analyzed {len(analyses)} backtests successfully")
            
            # Select top backtests (up to 5, or all if fewer than 5)
            top_count = min(5, len(analyses))
            top_analyses = self.select_top_backtests(analyses, top_count=top_count)
            if not top_analyses:
                logger.warning(f"⚠️ No top backtests selected for lab {lab_name}")
                return False
            
            # Create bots from top backtests
            logger.info(f"🤖 Creating bots from top {len(top_analyses)} backtests (out of {len(analyses)} total)...")
            bots_created = 0
            
            for i, analysis in enumerate(top_analyses, 1):
                logger.info(f"Creating bot {i}/{len(top_analyses)}...")
                result = self.create_bot_from_backtest(analysis)
                if result:
                    self.bot_results.append(result)
                    bots_created += 1
                    logger.info(f"✅ Bot {i} created successfully")
                else:
                    logger.warning(f"⚠️ Failed to create bot {i}")
                
                # Small delay between bot creations
                time.sleep(1)
            
            logger.info(f"✅ Lab {lab_name} processing complete: {bots_created} bots created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing lab {lab_name}: {e}")
            return False
    
    def save_results(self):
        """Save all results to files"""
        try:
            # Save lab analyses
            if self.lab_analyses:
                lab_file = os.path.join(self.output_dir, "lab_analyses.csv")
                with open(lab_file, 'w', newline='', encoding='utf-8') as f:
                    if self.lab_analyses:
                        writer = csv.DictWriter(f, fieldnames=self.lab_analyses[0].__dict__.keys())
                        writer.writeheader()
                        for analysis in self.lab_analyses:
                            writer.writerow(analysis.__dict__)
                logger.info(f"Lab analyses saved to: {lab_file}")
            
            # Save bot creation results
            if self.bot_results:
                bot_file = os.path.join(self.output_dir, "bot_creation_results.csv")
                with open(bot_file, 'w', newline='', encoding='utf-8') as f:
                    if self.bot_results:
                        writer = csv.DictWriter(f, fieldnames=self.bot_results[0].__dict__.keys())
                        writer.writeheader()
                        for result in self.bot_results:
                            writer.writerow(result.__dict__)
                logger.info(f"Bot creation results saved to: {bot_file}")
            
            # Save summary
            summary_file = os.path.join(self.output_dir, "summary.json")
            summary = {
                "total_labs_analyzed": len(self.labs_with_many_backtests),
                "total_bots_created": len(self.bot_results),
                "processing_timestamp": datetime.now().isoformat(),
                "output_directory": self.output_dir,
                "labs_processed": [lab['lab_name'] for lab in self.labs_with_many_backtests]
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Results saved to {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting Top Bot Creation for New Server")
        logger.info("=" * 60)
        
        try:
            # Step 1: Analyze labs to find those with ≥10 backtests
            labs_with_backtests = self.analyze_lab_backtest_count()
            if not labs_with_backtests:
                logger.error("❌ No labs found with ≥10 backtests")
                return
            
            # Step 2: Process each lab to create top 5 bots
            for i, lab_info in enumerate(labs_with_backtests, 1):
                logger.info(f"\n📊 Processing lab {i}/{len(labs_with_backtests)}: {lab_info['lab_name']}")
                
                success = self.process_lab(lab_info)
                
                if success:
                    logger.info(f"✅ Lab {lab_info['lab_name']} processed successfully")
                else:
                    logger.warning(f"⚠️ Lab {lab_info['lab_name']} processing failed or incomplete")
                
                # Save intermediate results
                self.save_results()
                
                # Delay between labs
                if i < len(labs_with_backtests):
                    logger.info("Waiting 3 seconds before processing next lab...")
                    time.sleep(3)
            
            # Final results
            logger.info("\n🎉 All labs processed!")
            logger.info("=" * 60)
            
            total_bots = len(self.bot_results)
            logger.info(f"📊 Final Results:")
            logger.info(f"  • Labs processed: {len(labs_with_backtests)}")
            logger.info(f"  • Total bots created: {total_bots}")
            logger.info(f"  • Output directory: {self.output_dir}")
            
            # Save final results
            self.save_results()
            
            # Confirm bot creation
            if total_bots > 0:
                logger.info(f"\n✅ SUCCESS: {total_bots} bots have been created!")
                logger.info("Bot details:")
                for i, result in enumerate(self.bot_results, 1):
                    logger.info(f"  {i}. {result.bot_name} (ID: {result.bot_id[:8]}...) - ROI: {result.roi:.2f}%, WR: {result.win_rate:.2f}")
            else:
                logger.warning("⚠️ No bots were created. Check the logs above for errors.")
            
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
        
        # Create and run the bot creator
        creator = TopBotCreator(executor)
        creator.run()
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to API: {e}")

if __name__ == "__main__":
    main()
