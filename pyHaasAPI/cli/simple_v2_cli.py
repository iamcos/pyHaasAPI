#!/usr/bin/env python3
"""
Simplified pyHaasAPI v2 CLI - Based on proven v1 patterns

This is a simplified v2 CLI that removes unnecessary dependencies and follows
the proven working patterns from v1 CLI.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Use the working v1 imports
from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.api import RequestsExecutor, Guest, get_all_labs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleV2CLI:
    """Simplified v2 CLI using proven v1 patterns"""
    
    def __init__(self):
        self.executor = None
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        
    def connect(self) -> bool:
        """Connect using proven v1 authentication pattern"""
        try:
            # Get credentials from environment
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                logger.error("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Create API connection using proven v1 pattern
            haas_api = RequestsExecutor(
                host='127.0.0.1',
                port=8090,
                state=Guest()
            )
            
            # Authenticate (handles email/password + OTC internally)
            self.executor = haas_api.authenticate(email, password)
            
            # Initialize analyzer
            self.analyzer = HaasAnalyzer(self.cache)
            self.analyzer.connect()
            
            logger.info("✅ Successfully connected to HaasOnline API")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to HaasOnline API: {e}")
            return False
    
    def analyze_labs(self, min_winrate: float = 55.0, sort_by: str = "roe") -> Dict[str, Any]:
        """Analyze all labs with zero drawdown requirement"""
        try:
            logger.info("🔍 Analyzing labs with zero drawdown requirement...")
            
            # Get all labs
            labs = get_all_labs(self.executor)
            if not labs:
                logger.warning("No labs found")
                return {}
            
            results = {}
            
            for lab in labs:
                try:
                    # Extract lab_id from lab object
                    if hasattr(lab, 'lab_id'):
                        lab_id = lab.lab_id
                    elif hasattr(lab, 'id'):
                        lab_id = lab.id
                    elif isinstance(lab, dict):
                        lab_id = lab.get('lab_id', lab.get('id', 'unknown'))
                    else:
                        lab_id = str(lab)
                    
                    logger.info(f"📊 Analyzing lab: {lab_id}")
                    
                    # Analyze lab
                    result = self.analyzer.analyze_lab(
                        lab_id=lab_id,
                        top_count=50  # Get more backtests for filtering
                    )
                    
                    if result and result.top_backtests:
                        # Filter for zero drawdown and minimum win rate
                        filtered_backtests = [
                            bt for bt in result.top_backtests 
                            if bt.max_drawdown >= 0 and bt.win_rate >= (min_winrate/100.0)
                        ]
                        
                        # Sort by the specified metric
                        if sort_by == "roi":
                            filtered_backtests.sort(key=lambda x: x.roi_percentage, reverse=True)
                        elif sort_by == "roe":
                            # Calculate ROE (Return on Equity)
                            filtered_backtests.sort(key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
                        elif sort_by == "winrate":
                            filtered_backtests.sort(key=lambda x: x.win_rate, reverse=True)
                        
                        zero_dd_backtests = filtered_backtests
                        
                        if zero_dd_backtests:
                            results[lab_id] = {
                                'lab_name': result.lab_name,
                                'script_name': result.script_name,
                                'market_tag': result.market_tag,
                                'total_backtests': len(zero_dd_backtests),
                                'top_backtests': zero_dd_backtests[:5],  # Top 5
                                'average_roi': sum(bt.roi_percentage for bt in zero_dd_backtests) / len(zero_dd_backtests),
                                'best_roi': max(bt.roi_percentage for bt in zero_dd_backtests),
                                'average_win_rate': sum(bt.win_rate for bt in zero_dd_backtests) / len(zero_dd_backtests),
                                'best_win_rate': max(bt.win_rate for bt in zero_dd_backtests)
                            }
                            logger.info(f"✅ Lab {lab_id}: {len(zero_dd_backtests)} qualifying backtests")
                        else:
                            logger.warning(f"⚠️ Lab {lab_id}: No zero drawdown backtests found")
                    else:
                        logger.warning(f"⚠️ Lab {lab_id}: No backtests found")
                        
                except Exception as e:
                    logger.error(f"❌ Error analyzing lab {lab_id}: {e}")
                    continue
            
            logger.info(f"🎯 Analysis complete - {len(results)} labs with qualifying backtests")
            return results
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return {}
    
    def create_bots(self, lab_results: Dict[str, Any], bots_per_lab: int = 2) -> List[Dict[str, Any]]:
        """Create top bots for each lab with zero drawdown"""
        try:
            logger.info(f"🤖 Creating top {bots_per_lab} bots for each lab...")
            
            created_bots = []
            
            for lab_id, lab_data in lab_results.items():
                try:
                    logger.info(f"📊 Creating bots for lab: {lab_id}")
                    
                    # Get top backtests for bot creation
                    top_backtests = lab_data['top_backtests'][:bots_per_lab]
                    
                    for i, backtest in enumerate(top_backtests):
                        try:
                            # Create bot with proper naming convention
                            bot_name = f"{lab_data['lab_name']} - {lab_data['script_name']} - {backtest.roi_percentage:.1f}% pop/gen {backtest.win_rate*100:.0f}%"
                            
                            # Create bot from backtest
                            bot_result = self.analyzer.create_bot_from_backtest(
                                backtest_id=backtest.backtest_id,
                                bot_name=bot_name,
                                trade_amount_usdt=2000.0,  # $2000 USDT
                                leverage=20.0,  # 20x leverage
                                margin_mode="CROSS",  # Cross margin
                                position_mode="HEDGE"  # Hedge mode
                            )
                            
                            if bot_result and bot_result.success:
                                created_bots.append({
                                    'lab_id': lab_id,
                                    'bot_id': bot_result.bot_id,
                                    'bot_name': bot_result.bot_name,
                                    'backtest_id': backtest.backtest_id,
                                    'roi_percentage': backtest.roi_percentage,
                                    'win_rate': backtest.win_rate,
                                    'max_drawdown': backtest.max_drawdown,
                                    'total_trades': backtest.total_trades
                                })
                                logger.info(f"✅ Created bot: {bot_result.bot_name}")
                            else:
                                logger.error(f"❌ Failed to create bot for backtest {backtest.backtest_id}")
                                
                        except Exception as e:
                            logger.error(f"❌ Error creating bot {i+1} for lab {lab_id}: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"❌ Error processing lab {lab_id}: {e}")
                    continue
            
            logger.info(f"🎯 Bot creation complete - {len(created_bots)} bots created")
            return created_bots
            
        except Exception as e:
            logger.error(f"❌ Bot creation failed: {e}")
            return []
    
    def print_analysis_report(self, lab_results: Dict[str, Any]):
        """Print analysis report"""
        print("\n" + "="*80)
        print("📊 LAB ANALYSIS REPORT - ZERO DRAWDOWN BOTS ONLY")
        print("="*80)
        
        for lab_id, data in lab_results.items():
            print(f"\n🔬 Lab: {data['lab_name']} ({lab_id[:8]})")
            print(f"   Script: {data['script_name']}")
            print(f"   Market: {data['market_tag']}")
            print(f"   Qualifying Bots: {data['total_backtests']}")
            print(f"   Average ROI: {data['average_roi']:.2f}%")
            print(f"   Best ROI: {data['best_roi']:.2f}%")
            print(f"   Average Win Rate: {data['average_win_rate']:.2f}%")
            print(f"   Best Win Rate: {data['best_win_rate']:.2f}%")
            
            print(f"   Top Performers:")
            for i, bt in enumerate(data['top_backtests'][:5], 1):
                print(f"     {i}. ROI: {bt.roi_percentage:.2f}% | WR: {bt.win_rate*100:.1f}% | Trades: {bt.total_trades} | DD: {bt.max_drawdown:.2f}")
        
        print("="*80)
    
    def print_bot_creation_report(self, created_bots: List[Dict[str, Any]]):
        """Print bot creation report"""
        print("\n" + "="*80)
        print("🤖 BOT CREATION REPORT")
        print("="*80)
        
        for bot in created_bots:
            print(f"\n✅ Bot Created:")
            print(f"   Lab ID: {bot['lab_id'][:8]}")
            print(f"   Bot ID: {bot['bot_id'][:8]}")
            print(f"   Name: {bot['bot_name']}")
            print(f"   ROI: {bot['roi_percentage']:.2f}%")
            print(f"   Win Rate: {bot['win_rate']*100:.1f}%")
            print(f"   Max Drawdown: {bot['max_drawdown']:.2f}")
            print(f"   Total Trades: {bot['total_trades']}")
        
        print(f"\n🎯 Total Bots Created: {len(created_bots)}")
        print("="*80)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Simplified pyHaasAPI v2 CLI - Zero Drawdown Analysis & Bot Creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze labs and create top 2 bots for each
  python -m pyHaasAPI_v2.cli.simple_v2_cli --analyze --create-bots --bots-per-lab 2
  
  # Analyze with custom win rate threshold
  python -m pyHaasAPI_v2.cli.simple_v2_cli --analyze --min-winrate 60
  
  # Just analyze without creating bots
  python -m pyHaasAPI_v2.cli.simple_v2_cli --analyze
        """
    )
    
    parser.add_argument('--analyze', action='store_true', help='Analyze labs with zero drawdown requirement')
    parser.add_argument('--create-bots', action='store_true', help='Create bots from analysis results')
    parser.add_argument('--min-winrate', type=float, default=55.0, help='Minimum win rate percentage (default: 55)')
    parser.add_argument('--bots-per-lab', type=int, default=2, help='Number of bots to create per lab (default: 2)')
    parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate'], default='roe', help='Sort by metric (default: roe)')
    
    args = parser.parse_args()
    
    if not args.analyze and not args.create_bots:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = SimpleV2CLI()
    
    # Connect to API
    if not cli.connect():
        logger.error("Failed to connect to API")
        return 1
    
    try:
        lab_results = {}
        
        # Analyze labs if requested
        if args.analyze:
            lab_results = cli.analyze_labs(
                min_winrate=args.min_winrate,
                sort_by=args.sort_by
            )
            
            if lab_results:
                cli.print_analysis_report(lab_results)
            else:
                logger.warning("No qualifying labs found")
                return 0
        
        # Create bots if requested
        if args.create_bots:
            if not lab_results:
                # Re-analyze if not already done
                lab_results = cli.analyze_labs(
                    min_winrate=args.min_winrate,
                    sort_by=args.sort_by
                )
            
            if lab_results:
                created_bots = cli.create_bots(lab_results, args.bots_per_lab)
                if created_bots:
                    cli.print_bot_creation_report(created_bots)
                else:
                    logger.warning("No bots were created")
            else:
                logger.warning("No qualifying labs found for bot creation")
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
