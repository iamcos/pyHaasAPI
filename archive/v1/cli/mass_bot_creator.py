#!/usr/bin/env python3
"""
Mass Bot Creator for pyHaasAPI

This tool creates bots for the top 5 backtests from every complete lab on the server,
assigning each bot to an individual account with $2000 USDT trading balance.
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI_v1 import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI_v1.api import RequestsExecutor, get_all_labs, get_lab_details, get_all_accounts
from pyHaasAPI_v1.analysis.models import BacktestAnalysis, BotCreationResult, LabAnalysisResult
from pyHaasAPI_v1.analysis.robustness import StrategyRobustnessAnalyzer, RobustnessMetrics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MassBotCreationResult:
    """Result of mass bot creation process"""
    total_labs_processed: int
    total_bots_created: int
    successful_creations: int
    failed_creations: int
    labs_with_errors: List[str]
    bot_results: List[BotCreationResult]
    processing_time: float


class MassBotCreator:
    """Tool for creating bots from all complete labs"""
    
    def __init__(self):
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.accounts = []
        self.account_index = 0
        self.results = []
        self.start_time = time.time()
        
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            logger.info("🔌 Connecting to HaasOnline API...")
            
            # Initialize analyzer
            self.analyzer = HaasAnalyzer(self.cache)
            
            # Connect
            if not self.analyzer.connect():
                logger.error("❌ Failed to connect to HaasOnline API")
                return False
                
            # Get available accounts
            self.accounts = self.analyzer.get_accounts()
            logger.info(f"📋 Found {len(self.accounts)} available accounts")
            
            logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_complete_labs(self) -> List[Any]:
        """Get all complete labs from the server"""
        try:
            logger.info("📋 Fetching all labs...")
            all_labs = get_all_labs(self.analyzer.executor)
            
            # Show lab statuses for debugging
            logger.info("📋 Lab statuses:")
            status_counts = {}
            for lab in all_labs:
                lab_status = getattr(lab, 'status', None)
                lab_name = getattr(lab, 'name', 'Unknown')
                status_str = str(lab_status)
                status_counts[status_str] = status_counts.get(status_str, 0) + 1
                logger.info(f"  - {lab_name}: status={lab_status}")
            
            logger.info(f"📊 Status distribution: {status_counts}")
            
            # Filter for labs that have backtests - try to find completed labs
            complete_labs = []
            for lab in all_labs:
                lab_status = getattr(lab, 'status', None)
                # Check if status indicates completion (might be LabStatus.COMPLETED or similar)
                if lab_status is not None and str(lab_status).upper() in ['COMPLETED', 'COMPLETE', 'FINISHED', 'DONE']:
                    complete_labs.append(lab)
                # Also try numeric values if status has a value attribute
                elif hasattr(lab_status, 'value') and lab_status.value >= 1:
                    complete_labs.append(lab)
            
            logger.info(f"📊 Found {len(complete_labs)} labs with backtests out of {len(all_labs)} total labs")
            return complete_labs
            
        except Exception as e:
            logger.error(f"❌ Error fetching labs: {e}")
            return []
    
    def get_next_account(self) -> Optional[Dict]:
        """Get the next available account for bot assignment"""
        if not self.accounts:
            logger.error("❌ No accounts available")
            return None
            
        # Use round-robin assignment
        account = self.accounts[self.account_index % len(self.accounts)]
        self.account_index += 1
        
        return account
    
    def analyze_lab_and_create_bots(self, lab: Any, top_count: int = 5, activate: bool = False, dry_run: bool = False,
                                  target_usdt_amount: float = 2000.0, trade_amount_method: str = 'usdt',
                                  wallet_percentage: float = None, analyze_count: int = 100,
                                  min_backtests: int = 100, min_winrate: float = 0.0) -> List[BotCreationResult]:
        """Analyze a single lab and create bots from top backtests"""
        # Get lab ID and name
        lab_id = getattr(lab, 'lab_id', None)
        lab_name = getattr(lab, 'name', 'Unknown')
        
        logger.info(f"🔍 Analyzing lab: {lab_name} ({lab_id})")
        
        try:
            # Analyze the lab with specified analyze_count
            analysis_result = self.analyzer.analyze_lab(lab_id, top_count=analyze_count)
            
            if not analysis_result or not analysis_result.top_backtests:
                logger.warning(f"⚠️  No backtests found for lab {lab_name}")
                return []
            
            # Check if lab has minimum required backtests
            total_backtests = len(analysis_result.top_backtests)
            if total_backtests < min_backtests:
                logger.warning(f"⚠️  Lab {lab_name} has only {total_backtests} backtests (minimum required: {min_backtests}) - skipping")
                return []
            
            logger.info(f"📊 Found {total_backtests} backtests for {lab_name} (analyzing top {min(analyze_count, total_backtests)})")
            
            # Apply win rate filter if specified
            filtered_backtests = analysis_result.top_backtests
            if min_winrate > 0.0:
                filtered_backtests = [bt for bt in analysis_result.top_backtests if bt.win_rate >= min_winrate]
                logger.info(f"📊 After win rate filter (>= {min_winrate:.1%}): {len(filtered_backtests)} backtests")
                
                if not filtered_backtests:
                    logger.warning(f"⚠️ No backtests meet the minimum win rate requirement of {min_winrate:.1%}")
                    return []
            
            # Create bots from top backtests
            bot_results = []
            for i, backtest in enumerate(filtered_backtests[:top_count]):
                try:
                    # Get next available account
                    account = self.get_next_account()
                    if not account:
                        logger.error(f"❌ No accounts available for bot creation")
                        break
                    
                    logger.info(f"🤖 Creating bot {i+1}/{top_count} from backtest {backtest.backtest_id}")
                    
                    # Create bot name following the convention: LabName - ScriptName - ROI pop/gen WR%
                    lab_name_clean = analysis_result.lab_name.replace('_', ' ').replace('-', ' ')
                    roi_str = f"{backtest.roi_percentage:.0f}"
                    pop_gen_str = f"{backtest.population_idx or 0}/{backtest.generation_idx or 0}"
                    win_rate_percent = f"{backtest.win_rate * 100:.0f}%"
                    bot_name = f"{lab_name_clean} - {backtest.script_name} - {roi_str} {pop_gen_str} {win_rate_percent}"
                    
                    if dry_run:
                        logger.info(f"   Would create bot: {bot_name}")
                        logger.info(f"   Would set trade amount to: {target_usdt_amount} USDT equivalent")
                        # Create a mock bot result for dry run counting
                        mock_bot_result = BotCreationResult(
                            bot_id="dry-run-mock",
                            bot_name=bot_name,
                            backtest_id=backtest.backtest_id,
                            account_id="dry-run-account",
                            market_tag=backtest.market_tag,
                            leverage=20.0,
                            margin_mode="CROSS",
                            position_mode="HEDGE",
                            trade_amount_usdt=target_usdt_amount,
                            creation_timestamp=datetime.now().isoformat(),
                            success=True,
                            activated=False,
                            error_message=None
                        )
                        bot_results.append(mock_bot_result)
                        continue
                    
                    # Create bot with proper configuration
                    bot_result = self.analyzer.create_bot_from_backtest(
                        backtest=backtest,
                        bot_name=bot_name
                    )
                    
                    if bot_result and bot_result.success:
                        logger.info(f"✅ Created bot: {bot_result.bot_name}")
                        logger.info(f"💰 Trade amount: {bot_result.trade_amount_usdt:.4f} base currency (${target_usdt_amount} USDT equivalent)")
                        
                        # Activate bot if requested
                        if activate:
                            activation_success = self.analyzer.activate_bot(bot_result.bot_id)
                            if activation_success:
                                logger.info(f"🚀 Bot activated for live trading")
                            else:
                                logger.warning(f"⚠️ Bot created but activation failed")
                        
                        bot_results.append(bot_result)
                    else:
                        logger.error(f"❌ Failed to create bot from backtest {backtest.backtest_id}")
                        if bot_result and bot_result.error_message:
                            logger.error(f"   Error: {bot_result.error_message}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creating bot {i+1} for lab {lab_name}: {e}")
                    continue
            
            logger.info(f"🎯 Created {len(bot_results)} bots for lab {lab_name}")
            return bot_results
            
        except Exception as e:
            logger.error(f"❌ Error analyzing lab {lab_name}: {e}")
            return []
    
    def run_mass_creation(self) -> MassBotCreationResult:
        """Run the complete mass bot creation process"""
        logger.info("🚀 Starting Mass Bot Creation Process")
        logger.info("=" * 60)
        
        # Connect to API
        if not self.connect():
            return MassBotCreationResult(
                total_labs_processed=0,
                total_bots_created=0,
                successful_creations=0,
                failed_creations=0,
                labs_with_errors=[],
                bot_results=[],
                processing_time=0
            )
        
        # Get complete labs
        complete_labs = self.get_complete_labs()
        if not complete_labs:
            logger.warning("⚠️  No complete labs found")
            return MassBotCreationResult(
                total_labs_processed=0,
                total_bots_created=0,
                successful_creations=0,
                failed_creations=0,
                labs_with_errors=[],
                bot_results=[],
                processing_time=time.time() - self.start_time
            )
        
        # Process each lab
        all_bot_results = []
        labs_with_errors = []
        successful_creations = 0
        failed_creations = 0
        
        for i, lab in enumerate(complete_labs):
            lab_name = getattr(lab, 'name', f'Lab-{i+1}')
            logger.info(f"📋 Processing lab {i+1}/{len(complete_labs)}: {lab_name}")
            
            try:
                bot_results = self.analyze_lab_and_create_bots(lab)
                all_bot_results.extend(bot_results)
                
                # Count successes and failures
                for bot_result in bot_results:
                    if bot_result.success:
                        successful_creations += 1
                    else:
                        failed_creations += 1
                        
            except Exception as e:
                logger.error(f"❌ Failed to process lab {lab_name}: {e}")
                labs_with_errors.append(lab_name)
                continue
        
        # Calculate processing time
        processing_time = time.time() - self.start_time
        
        # Create result
        result = MassBotCreationResult(
            total_labs_processed=len(complete_labs),
            total_bots_created=len(all_bot_results),
            successful_creations=successful_creations,
            failed_creations=failed_creations,
            labs_with_errors=labs_with_errors,
            bot_results=all_bot_results,
            processing_time=processing_time
        )
        
        # Print summary
        self.print_summary(result)
        
        return result
    
    def _filter_labs(self, all_labs: List[Any], lab_ids: List[str] = None, exclude_lab_ids: List[str] = None) -> List[Any]:
        """Filter labs based on inclusion/exclusion criteria"""
        filtered_labs = []
        
        for lab in all_labs:
            lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            
            # If specific lab IDs are provided, only include those
            if lab_ids:
                if lab_id in lab_ids:
                    filtered_labs.append(lab)
                continue
            
            # If exclude lab IDs are provided, skip those
            if exclude_lab_ids:
                if lab_id in exclude_lab_ids:
                    continue
            
            # If no filters, include all labs
            filtered_labs.append(lab)
        
        return filtered_labs
    
    def create_bots_for_labs(self, top_count: int = 5, activate: bool = False, dry_run: bool = False,
                           lab_ids: List[str] = None, exclude_lab_ids: List[str] = None,
                           target_usdt_amount: float = 2000.0, trade_amount_method: str = 'usdt',
                           wallet_percentage: float = None, analyze_count: int = 100,
                           min_backtests: int = 100, min_winrate: float = 0.0) -> MassBotCreationResult:
        """Create bots for labs with flexible selection and calculation methods"""
        logger.info("🚀 Starting mass bot creation process...")
        self.start_time = time.time()
        
        # Get all complete labs
        all_complete_labs = self.get_complete_labs()
        if not all_complete_labs:
            logger.warning("⚠️ No complete labs found")
            return MassBotCreationResult(
                total_labs_processed=0,
                total_bots_created=0,
                successful_creations=0,
                failed_creations=0,
                labs_with_errors=[],
                bot_results=[],
                processing_time=0.0
            )
        
        # Filter labs based on selection criteria
        complete_labs = self._filter_labs(all_complete_labs, lab_ids, exclude_lab_ids)
        
        if not complete_labs:
            logger.warning("⚠️ No labs match the selection criteria")
            return MassBotCreationResult(
                total_labs_processed=0,
                total_bots_created=0,
                successful_creations=0,
                failed_creations=0,
                labs_with_errors=[],
                bot_results=[],
                processing_time=0.0
            )
        
        logger.info(f"📋 Found {len(complete_labs)} labs to process")
        
        all_bot_results = []
        successful_creations = 0
        failed_creations = 0
        labs_with_errors = []
        
        # Process each lab
        for i, lab in enumerate(complete_labs):
            lab_name = getattr(lab, 'name', f'Lab-{i+1}')
            logger.info(f"🔬 Processing lab {i+1}/{len(complete_labs)}: {lab_name}")
            
            try:
                bot_results = self.analyze_lab_and_create_bots(
                    lab, top_count, activate, dry_run, 
                    target_usdt_amount, trade_amount_method, wallet_percentage,
                    analyze_count, min_backtests, min_winrate
                )
                all_bot_results.extend(bot_results)
                
                # Count successes and failures
                for bot_result in bot_results:
                    if bot_result.success:
                        successful_creations += 1
                    else:
                        failed_creations += 1
                
                if not bot_results and not dry_run:
                    labs_with_errors.append(lab_name)
                
            except Exception as e:
                logger.error(f"❌ Error processing lab {lab_name}: {e}")
                labs_with_errors.append(lab_name)
                continue
        
        # Calculate processing time
        processing_time = time.time() - self.start_time
        
        # Create result
        result = MassBotCreationResult(
            total_labs_processed=len(complete_labs),
            total_bots_created=len(all_bot_results),
            successful_creations=successful_creations,
            failed_creations=failed_creations,
            labs_with_errors=labs_with_errors,
            bot_results=all_bot_results,
            processing_time=processing_time
        )
        
        # Print summary
        self.print_summary(result)
        
        return result
    
    def print_summary(self, result: MassBotCreationResult):
        """Print a comprehensive summary of the bot creation process"""
        logger.info("=" * 60)
        logger.info("📊 MASS BOT CREATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📋 Total labs processed: {result.total_labs_processed}")
        logger.info(f"🤖 Total bots created: {result.total_bots_created}")
        logger.info(f"✅ Successful creations: {result.successful_creations}")
        logger.info(f"❌ Failed creations: {result.failed_creations}")
        logger.info(f"⏱️  Processing time: {result.processing_time:.2f} seconds")
        
        if result.labs_with_errors:
            logger.info(f"⚠️  Labs with errors: {len(result.labs_with_errors)}")
            for lab_name in result.labs_with_errors:
                logger.info(f"   - {lab_name}")
        
        # Show some example bot names
        if result.bot_results:
            logger.info("🎯 Sample created bots:")
            for i, bot in enumerate(result.bot_results[:5]):
                if bot.success:
                    logger.info(f"   {i+1}. {bot.bot_name}")
            if len(result.bot_results) > 5:
                logger.info(f"   ... and {len(result.bot_results) - 5} more")
        
        # Success rate
        if result.total_bots_created > 0:
            success_rate = (result.successful_creations / result.total_bots_created) * 100
            logger.info(f"📈 Success rate: {success_rate:.1f}%")
        
        logger.info("=" * 60)
        
        if result.successful_creations > 0:
            logger.info("🎉 Mass bot creation completed successfully!")
        else:
            logger.warning("⚠️  No bots were created successfully")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Mass Bot Creator - Create bots from top backtests across all labs',
        epilog='''
Examples:
  # Create top 5 bots from all labs and activate them
  python -m pyHaasAPI.cli.mass_bot_creator --top-count 5 --activate
  
  # Create bots only from labs with 50+ backtests and 60%+ win rate
  python -m pyHaasAPI.cli.mass_bot_creator --min-backtests 50 --min-winrate 0.6
  
  # Create bots from specific labs only
  python -m pyHaasAPI.cli.mass_bot_creator --lab-ids lab1,lab2 --top-count 3
  
  # Dry run to see what would be created
  python -m pyHaasAPI.cli.mass_bot_creator --dry-run --top-count 3
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--top-count', type=int, default=5,
                       help='Number of top backtests to create bots for per lab (default: 5)')
    parser.add_argument('--analyze-count', type=int, default=100,
                       help='Number of backtests to analyze per lab (default: 100)')
    parser.add_argument('--min-backtests', type=int, default=100,
                       help='Minimum number of backtests required to process a lab (default: 100)')
    parser.add_argument('--min-winrate', type=float, default=0.0,
                       help='Minimum win rate for bot creation (0.0-1.0, default: 0.0 - no filter)')
    parser.add_argument('--activate', action='store_true',
                       help='Activate created bots for live trading')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without creating bots')
    
    # Lab selection options
    lab_group = parser.add_mutually_exclusive_group()
    lab_group.add_argument('--lab-ids', nargs='+', type=str,
                          help='Create bots only for specific lab IDs')
    lab_group.add_argument('--exclude-lab-ids', nargs='+', type=str,
                          help='Create bots for all complete labs except these IDs')
    
    # Trade amount options
    parser.add_argument('--target-amount', type=float, default=2000.0,
                       help='Target USDT amount for trade amounts (default: 2000.0)')
    parser.add_argument('--method', choices=['usdt', 'wallet_percentage'], default='usdt',
                       help='Trade amount calculation method (default: usdt)')
    parser.add_argument('--wallet-percentage', type=float,
                       help='Percentage of wallet to use (for wallet_percentage method)')
    
    args = parser.parse_args()
    
    try:
        creator = MassBotCreator()
        
        if not creator.connect():
            sys.exit(1)
        
        # Create bots with specified criteria
        result =         creator.create_bots_for_labs(
            top_count=args.top_count,
            activate=args.activate,
            dry_run=args.dry_run,
            lab_ids=args.lab_ids,
            exclude_lab_ids=args.exclude_lab_ids,
            target_usdt_amount=args.target_amount,
            trade_amount_method=args.method,
            wallet_percentage=args.wallet_percentage,
            analyze_count=args.analyze_count,
            min_backtests=args.min_backtests,
            min_winrate=args.min_winrate
        )
        
        # Exit with appropriate code
        if result.successful_creations > 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n❌ Mass bot creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
