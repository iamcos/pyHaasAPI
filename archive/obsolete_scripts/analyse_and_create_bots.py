#!/usr/bin/env python3
"""
Analyse and Create Bots - Unified Analysis and Bot Creation Tool

This CLI tool provides comprehensive functionality for:
- Lab analysis with detailed backtest data extraction
- Bot creation with proper configuration
- Unified caching system
- Detailed CSV reporting
- Clean, organized output

Usage:
    python analyse_and_create_bots.py analyze <lab_id> [--top N] [--create-bots] [--output-dir DIR]
    python analyse_and_create_bots.py create-bots <lab_id> [--top N] [--output-dir DIR]
    python analyse_and_create_bots.py list-labs [--status STATUS]
"""

import os
import sys
import json
import csv
import logging
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor, get_full_backtest_runtime_data
from pyHaasAPI.model import GetBacktestResultRequest, AddBotFromLabRequest, LabStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'unified_cache/haas_cli_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Reduce verbosity of other loggers
logging.getLogger('pyHaasAPI').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

@dataclass
class BacktestAnalysis:
    """Comprehensive backtest analysis data"""
    backtest_id: str
    lab_id: str
    generation_idx: Optional[int]
    population_idx: Optional[int]
    market_tag: str
    script_id: str
    script_name: str
    
    # Performance metrics
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    pc_value: float
    
    # Additional metrics
    avg_profit_per_trade: float
    profit_factor: float
    sharpe_ratio: float
    
    # Timestamps
    analysis_timestamp: str
    backtest_timestamp: Optional[str] = None

@dataclass
class BotCreationResult:
    """Result of bot creation"""
    bot_id: str
    bot_name: str
    backtest_id: str
    account_id: str
    market_tag: str
    leverage: float
    margin_mode: str
    position_mode: str
    creation_timestamp: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class LabAnalysisResult:
    """Complete lab analysis result"""
    lab_id: str
    lab_name: str
    total_backtests: int
    analyzed_backtests: int
    top_backtests: List[BacktestAnalysis]
    bots_created: List[BotCreationResult]
    analysis_timestamp: str
    processing_time: float

class UnifiedCacheManager:
    """Manages unified caching system"""
    
    def __init__(self, base_dir: str = "unified_cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.base_dir / "backtests").mkdir(exist_ok=True)
        (self.base_dir / "reports").mkdir(exist_ok=True)
        (self.base_dir / "logs").mkdir(exist_ok=True)
    
    def get_backtest_cache_path(self, lab_id: str, backtest_id: str) -> Path:
        """Get cache path for backtest data"""
        return self.base_dir / "backtests" / f"{lab_id}_{backtest_id}.json"
    
    def get_report_path(self, lab_id: str, timestamp: str) -> Path:
        """Get report path for lab analysis"""
        return self.base_dir / "reports" / f"lab_analysis_{lab_id}_{timestamp}.csv"
    
    def cache_backtest_data(self, lab_id: str, backtest_id: str, data: Dict[str, Any]) -> None:
        """Cache backtest data"""
        cache_path = self.get_backtest_cache_path(lab_id, backtest_id)
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_backtest_cache(self, lab_id: str, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Load cached backtest data"""
        cache_path = self.get_backtest_cache_path(lab_id, backtest_id)
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_analysis_report(self, result: LabAnalysisResult) -> Path:
        """Save analysis report to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.get_report_path(result.lab_id, timestamp)
        
        with open(report_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Lab ID', 'Lab Name', 'Total Backtests', 'Analyzed Backtests',
                'Backtest ID', 'Generation', 'Population', 'Market', 'Script ID', 'Script Name',
                'ROI %', 'Win Rate %', 'Total Trades', 'Max Drawdown %', 'Realized Profits USDT',
                'PC Value', 'Avg Profit/Trade', 'Profit Factor', 'Sharpe Ratio',
                'Analysis Timestamp'
            ])
            
            # Write data rows
            for backtest in result.top_backtests:
                writer.writerow([
                    result.lab_id, result.lab_name, result.total_backtests, result.analyzed_backtests,
                    backtest.backtest_id, backtest.generation_idx, backtest.population_idx,
                    backtest.market_tag, backtest.script_id, backtest.script_name,
                    backtest.roi_percentage, backtest.win_rate * 100, backtest.total_trades,
                    backtest.max_drawdown, backtest.realized_profits_usdt,
                    backtest.pc_value, backtest.avg_profit_per_trade, backtest.profit_factor,
                    backtest.sharpe_ratio, backtest.analysis_timestamp
                ])
        
        return report_path

class HaasAnalyzer:
    """Main analyzer class"""
    
    def __init__(self, cache_manager: UnifiedCacheManager):
        self.cache_manager = cache_manager
        self.executor = None
        self.accounts = None
    
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            # Create API connection
            haas_api = api.RequestsExecutor(
                host=os.getenv('API_HOST', '127.0.0.1'),
                port=int(os.getenv('API_PORT', 8090)),
                state=api.Guest()
            )
            
            # Authenticate
            self.executor = haas_api.authenticate(
                os.getenv('API_EMAIL'),
                os.getenv('API_PASSWORD')
            )
            
            logger.info("✅ Successfully connected to HaasOnline API")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to HaasOnline API: {e}")
            return False
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get available accounts"""
        if self.accounts is None:
            try:
                self.accounts = api.get_all_accounts(self.executor)
                logger.info(f"📋 Found {len(self.accounts)} accounts")
            except Exception as e:
                logger.error(f"❌ Failed to get accounts: {e}")
                self.accounts = []
        return self.accounts
    
    def analyze_backtest(self, lab_id: str, backtest_obj) -> Optional[BacktestAnalysis]:
        """Analyze a single backtest with full data extraction"""
        try:
            backtest_id = backtest_obj.backtest_id
            logger.info(f"🔍 Analyzing backtest {backtest_id[:8]}...")
            
            # Check cache first
            cached_data = self.cache_manager.load_backtest_cache(lab_id, backtest_id)
            if cached_data:
                logger.info(f"📁 Using cached data for {backtest_id[:8]}")
                return self._create_analysis_from_cache(cached_data, lab_id, backtest_obj)
            
            # Get full runtime data
            runtime_data = get_full_backtest_runtime_data(self.executor, lab_id, backtest_id)
            if not runtime_data:
                logger.warning(f"⚠️ Could not get runtime data for {backtest_id[:8]}")
                return None
            
            # Extract basic info
            generation_idx = getattr(backtest_obj, 'generation_idx', None)
            population_idx = getattr(backtest_obj, 'population_idx', None)
            
            # Extract settings
            settings = getattr(backtest_obj, 'settings', None)
            market_tag = getattr(settings, 'market_tag', '') if settings else ''
            script_id = getattr(settings, 'script_id', '') if settings else ''
            script_name = getattr(settings, 'script_name', '') if settings else ''
            
            # Initialize analysis
            analysis_data = {
                'roi_percentage': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'max_drawdown': 0.0,
                'realized_profits_usdt': 0.0,
                'pc_value': 0.0,
                'avg_profit_per_trade': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0
            }
            
            # Extract performance data from runtime Reports
            if hasattr(runtime_data, 'Reports') and runtime_data.Reports:
                report_key = list(runtime_data.Reports.keys())[0]
                report_data = runtime_data.Reports[report_key]
                
                # Extract performance metrics
                if hasattr(report_data, 'PR'):
                    pr_data = report_data.PR
                    analysis_data['realized_profits_usdt'] = float(pr_data.RP) if hasattr(pr_data, 'RP') else 0.0
                    analysis_data['roi_percentage'] = float(pr_data.ROI) if hasattr(pr_data, 'ROI') else 0.0
                    analysis_data['max_drawdown'] = float(pr_data.RM) if hasattr(pr_data, 'RM') else 0.0
                    analysis_data['pc_value'] = float(pr_data.PC) if hasattr(pr_data, 'PC') else 0.0
                
                # Extract trade statistics
                if hasattr(report_data, 'P'):
                    p_data = report_data.P
                    analysis_data['total_trades'] = int(p_data.C) if hasattr(p_data, 'C') else 0
                    winning_trades = int(p_data.W) if hasattr(p_data, 'W') else 0
                    analysis_data['win_rate'] = (winning_trades / analysis_data['total_trades']) if analysis_data['total_trades'] > 0 else 0.0
                
                # Calculate additional metrics
                if analysis_data['total_trades'] > 0:
                    analysis_data['avg_profit_per_trade'] = analysis_data['realized_profits_usdt'] / analysis_data['total_trades']
                
                # Calculate profit factor (simplified)
                if analysis_data['realized_profits_usdt'] > 0:
                    analysis_data['profit_factor'] = analysis_data['realized_profits_usdt'] / abs(analysis_data['max_drawdown']) if analysis_data['max_drawdown'] != 0 else 0.0
            
            # Create analysis object
            analysis = BacktestAnalysis(
                backtest_id=backtest_id,
                lab_id=lab_id,
                generation_idx=generation_idx,
                population_idx=population_idx,
                market_tag=market_tag,
                script_id=script_id,
                script_name=script_name,
                roi_percentage=analysis_data['roi_percentage'],
                win_rate=analysis_data['win_rate'],
                total_trades=analysis_data['total_trades'],
                max_drawdown=analysis_data['max_drawdown'],
                realized_profits_usdt=analysis_data['realized_profits_usdt'],
                pc_value=analysis_data['pc_value'],
                avg_profit_per_trade=analysis_data['avg_profit_per_trade'],
                profit_factor=analysis_data['profit_factor'],
                sharpe_ratio=analysis_data['sharpe_ratio'],
                analysis_timestamp=datetime.now().isoformat()
            )
            
            # Cache the data
            cache_data = asdict(analysis)
            cache_data['runtime_data'] = runtime_data.model_dump() if hasattr(runtime_data, 'model_dump') else str(runtime_data)
            self.cache_manager.cache_backtest_data(lab_id, backtest_id, cache_data)
            
            logger.info(f"✅ Analysis complete: ROI={analysis.roi_percentage:.2f}%, Win Rate={analysis.win_rate:.1%}, Trades={analysis.total_trades}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing backtest: {e}")
            return None
    
    def _create_analysis_from_cache(self, cached_data: Dict[str, Any], lab_id: str, backtest_obj) -> BacktestAnalysis:
        """Create analysis from cached data"""
        return BacktestAnalysis(
            backtest_id=cached_data['backtest_id'],
            lab_id=lab_id,
            generation_idx=cached_data['generation_idx'],
            population_idx=cached_data['population_idx'],
            market_tag=cached_data['market_tag'],
            script_id=cached_data['script_id'],
            script_name=cached_data['script_name'],
            roi_percentage=cached_data['roi_percentage'],
            win_rate=cached_data['win_rate'],
            total_trades=cached_data['total_trades'],
            max_drawdown=cached_data['max_drawdown'],
            realized_profits_usdt=cached_data['realized_profits_usdt'],
            pc_value=cached_data['pc_value'],
            avg_profit_per_trade=cached_data['avg_profit_per_trade'],
            profit_factor=cached_data['profit_factor'],
            sharpe_ratio=cached_data['sharpe_ratio'],
            analysis_timestamp=cached_data['analysis_timestamp']
        )
    
    def analyze_lab(self, lab_id: str, top_count: int = 5) -> LabAnalysisResult:
        """Analyze a lab and return top performing backtests"""
        start_time = time.time()
        logger.info(f"🚀 Starting analysis of lab {lab_id[:8]}...")
        
        try:
            # Get lab details
            labs = api.get_all_labs(self.executor)
            lab = next((l for l in labs if l.lab_id == lab_id), None)
            if not lab:
                raise ValueError(f"Lab {lab_id} not found")
            
            lab_name = lab.name
            logger.info(f"📊 Lab: {lab_name}")
            
            # Get backtests
            request = GetBacktestResultRequest(
                lab_id=lab_id,
                next_page_id=0,
                page_lenght=100
            )
            
            response = api.get_backtest_result(self.executor, request)
            if not response or not hasattr(response, 'items'):
                raise ValueError("No backtests found")
            
            backtests = response.items
            total_backtests = len(backtests)
            logger.info(f"📈 Found {total_backtests} backtests")
            
            # Analyze backtests
            analyzed_backtests = []
            for i, backtest in enumerate(backtests, 1):
                logger.info(f"📊 Analyzing backtest {i}/{total_backtests}")
                analysis = self.analyze_backtest(lab_id, backtest)
                if analysis:
                    analyzed_backtests.append(analysis)
            
            # Select top performers
            positive_backtests = [bt for bt in analyzed_backtests if bt.roi_percentage > 0]
            sorted_backtests = sorted(
                positive_backtests,
                key=lambda x: (x.roi_percentage, x.win_rate, -x.max_drawdown),
                reverse=True
            )
            
            top_backtests = sorted_backtests[:top_count]
            
            logger.info(f"🏆 Selected top {len(top_backtests)} backtests:")
            for i, bt in enumerate(top_backtests, 1):
                logger.info(f"  {i}. ROI: {bt.roi_percentage:.2f}%, Win Rate: {bt.win_rate:.1%}, Trades: {bt.total_trades}")
            
            processing_time = time.time() - start_time
            
            return LabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_name,
                total_backtests=total_backtests,
                analyzed_backtests=len(analyzed_backtests),
                top_backtests=top_backtests,
                bots_created=[],
                analysis_timestamp=datetime.now().isoformat(),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing lab: {e}")
            raise
    
    def create_bot_from_backtest(self, backtest: BacktestAnalysis, bot_name: str) -> Optional[BotCreationResult]:
        """Create a bot from a backtest analysis"""
        try:
            # Get accounts
            accounts = self.get_accounts()
            if not accounts:
                raise ValueError("No accounts available")
            
            # Use first account
            account = accounts[0]
            account_id = account['AID']
            
            logger.info(f"🤖 Creating bot: {bot_name}")
            logger.info(f"📊 From backtest: {backtest.backtest_id[:8]}")
            logger.info(f"🏪 Market: {backtest.market_tag}")
            logger.info(f"💳 Account: {account_id[:8]}")
            
            # Create bot request
            request = AddBotFromLabRequest(
                lab_id=backtest.lab_id,
                backtest_id=backtest.backtest_id,
                bot_name=bot_name,
                account_id=account_id,
                market=backtest.market_tag,
                leverage=20.0
            )
            
            # Create bot
            bot_response = api.add_bot_from_lab(self.executor, request)
            if not bot_response or not hasattr(bot_response, 'bot_id'):
                raise ValueError("Failed to create bot")
            
            bot_id = bot_response.bot_id
            logger.info(f"✅ Bot created successfully: {bot_id[:8]}")
            
            # Configure bot settings
            self._configure_bot_settings(account_id, backtest.market_tag)
            
            return BotCreationResult(
                bot_id=bot_id,
                bot_name=bot_name,
                backtest_id=backtest.backtest_id,
                account_id=account_id,
                market_tag=backtest.market_tag,
                leverage=20.0,
                margin_mode="CROSS",
                position_mode="HEDGE",
                creation_timestamp=datetime.now().isoformat(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating bot: {e}")
            return BotCreationResult(
                bot_id="",
                bot_name=bot_name,
                backtest_id=backtest.backtest_id,
                account_id="",
                market_tag=backtest.market_tag,
                leverage=20.0,
                margin_mode="CROSS",
                position_mode="HEDGE",
                creation_timestamp=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            )
    
    def _configure_bot_settings(self, account_id: str, market_tag: str) -> None:
        """Configure bot margin settings"""
        try:
            # Set margin settings: HEDGE mode, CROSS margin, 20x leverage
            api.set_position_mode(self.executor, account_id, market_tag, 1)  # HEDGE
            api.set_margin_mode(self.executor, account_id, market_tag, 0)    # CROSS
            api.set_leverage(self.executor, account_id, market_tag, 20.0)    # 20x leverage
            
            logger.info(f"✅ Bot configured with HEDGE, CROSS, 20x leverage")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not configure bot settings: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Analyse and Create Bots - Unified Analysis and Bot Creation Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a lab and optionally create bots')
    analyze_parser.add_argument('lab_id', help='Lab ID to analyze')
    analyze_parser.add_argument('--top', type=int, default=5, help='Number of top backtests to select (default: 5)')
    analyze_parser.add_argument('--create-bots', action='store_true', help='Create bots from top backtests')
    analyze_parser.add_argument('--output-dir', default='unified_cache', help='Output directory (default: unified_cache)')
    
    # Create bots command
    create_parser = subparsers.add_parser('create-bots', help='Create bots from a lab')
    create_parser.add_argument('lab_id', help='Lab ID to create bots from')
    create_parser.add_argument('--top', type=int, default=5, help='Number of top backtests to select (default: 5)')
    create_parser.add_argument('--output-dir', default='unified_cache', help='Output directory (default: unified_cache)')
    
    # List labs command
    list_parser = subparsers.add_parser('list-labs', help='List available labs')
    list_parser.add_argument('--status', choices=['active', 'completed', 'all'], default='all', help='Filter by lab status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize cache manager
    cache_manager = UnifiedCacheManager(args.output_dir if hasattr(args, 'output_dir') else 'unified_cache')
    
    # Initialize analyzer
    analyzer = HaasAnalyzer(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        logger.error("❌ Failed to connect to API. Exiting.")
        return
    
    try:
        if args.command == 'analyze':
            # Analyze lab
            result = analyzer.analyze_lab(args.lab_id, args.top)
            
            # Save report
            report_path = cache_manager.save_analysis_report(result)
            logger.info(f"📄 Analysis report saved to: {report_path}")
            
            # Create bots if requested
            if args.create_bots:
                logger.info("🤖 Creating bots from top backtests...")
                bots_created = []
                
                for i, backtest in enumerate(result.top_backtests, 1):
                    # Create bot name following the convention: lab_name_ROI_pop/gen
                    lab_name_clean = result.lab_name.replace(' ', '_').replace('-', '_')[:20]
                    roi_str = f"{backtest.roi_percentage:.0f}"
                    pop_gen_str = f"{backtest.population_idx or 0}_{backtest.generation_idx or 0}"
                    bot_name = f"{lab_name_clean}_{roi_str}_{pop_gen_str}"
                    
                    bot_result = analyzer.create_bot_from_backtest(backtest, bot_name)
                    if bot_result:
                        bots_created.append(bot_result)
                
                result.bots_created = bots_created
                logger.info(f"✅ Created {len(bots_created)} bots successfully")
            
            # Print summary
            print(f"\n{'='*60}")
            print(f"📊 LAB ANALYSIS SUMMARY")
            print(f"{'='*60}")
            print(f"Lab ID: {result.lab_id}")
            print(f"Lab Name: {result.lab_name}")
            print(f"Total Backtests: {result.total_backtests}")
            print(f"Analyzed Backtests: {result.analyzed_backtests}")
            print(f"Top Backtests Selected: {len(result.top_backtests)}")
            print(f"Bots Created: {len(result.bots_created)}")
            print(f"Processing Time: {result.processing_time:.2f} seconds")
            print(f"Report Saved: {report_path}")
            print(f"{'='*60}")
        
        elif args.command == 'create-bots':
            # Analyze and create bots
            result = analyzer.analyze_lab(args.lab_id, args.top)
            
            # Create bots
            logger.info("🤖 Creating bots from top backtests...")
            bots_created = []
            
            for i, backtest in enumerate(result.top_backtests, 1):
                lab_name_clean = result.lab_name.replace(' ', '_').replace('-', '_')[:20]
                roi_str = f"{backtest.roi_percentage:.0f}"
                pop_gen_str = f"{backtest.population_idx or 0}_{backtest.generation_idx or 0}"
                bot_name = f"{lab_name_clean}_{roi_str}_{pop_gen_str}"
                
                bot_result = analyzer.create_bot_from_backtest(backtest, bot_name)
                if bot_result:
                    bots_created.append(bot_result)
            
            logger.info(f"✅ Created {len(bots_created)} bots successfully")
            
            # Save report
            result.bots_created = bots_created
            report_path = cache_manager.save_analysis_report(result)
            logger.info(f"📄 Report saved to: {report_path}")
        
        elif args.command == 'list-labs':
            # List labs
            labs = api.get_all_labs(analyzer.executor)
            
            print(f"\n{'='*80}")
            print(f"📋 AVAILABLE LABS")
            print(f"{'='*80}")
            print(f"{'Lab ID':<36} {'Name':<30} {'Status':<10}")
            print(f"{'-'*80}")
            
            for lab in labs:
                status = "Active" if lab.status == LabStatus.ACTIVE else "Completed"
                if args.status == 'all' or (args.status == 'active' and lab.status == LabStatus.ACTIVE) or (args.status == 'completed' and lab.status == LabStatus.COMPLETED):
                    print(f"{lab.lab_id:<36} {lab.name[:30]:<30} {status:<10}")
            
            print(f"{'='*80}")
            print(f"Total labs: {len(labs)}")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
