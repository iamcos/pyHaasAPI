"""
Analysis CLI for pyHaasAPI v2

This module provides command-line interface for analysis operations
using the new v2 architecture with async support and type safety.
"""

import asyncio
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseCLI, CLIConfig
from ..core.logging import get_logger
from ..core.type_definitions import LabID, BotID
from ..exceptions import APIError, ValidationError

logger = get_logger("analysis_cli")


class AnalysisCLI(BaseCLI):
    """
    CLI for analysis operations.
    
    Provides command-line interface for lab analysis, bot analysis,
    performance metrics, and reporting operations.
    """

    def __init__(self, config: Optional[CLIConfig] = None):
        super().__init__(config)
        self.logger = get_logger("analysis_cli")

    async def run(self, args: List[str]) -> int:
        """
        Run the analysis CLI with the given arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parser = self.create_analysis_parser()
            parsed_args = parser.parse_args(args)
            
            # Update config from args
            self.update_config_from_args(parsed_args)
            
            # Connect to API
            if not await self.connect():
                self.logger.error("Failed to connect to API")
                return 1
            
            # Execute command
            if parsed_args.action == 'labs':
                return await self.analyze_labs(parsed_args)
            elif parsed_args.action == 'bots':
                return await self.analyze_bots(parsed_args)
            elif parsed_args.action == 'wfo':
                return await self.analyze_wfo(parsed_args)
            elif parsed_args.action == 'performance':
                return await self.analyze_performance(parsed_args)
            elif parsed_args.action == 'reports':
                return await self.generate_reports(parsed_args)
            elif parsed_args.action == 'labs-without-bots':
                return await self.analyze_labs_without_bots(parsed_args)
            else:
                self.logger.error(f"Unknown action: {parsed_args.action}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in analysis CLI: {e}")
            return 1

    def create_analysis_parser(self) -> argparse.ArgumentParser:
        """Create analysis-specific argument parser"""
        parser = argparse.ArgumentParser(
            description="Analysis operations for pyHaasAPI v2",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Analyze all labs
  python -m pyHaasAPI_v2.cli analysis labs --generate-reports
  
  # Analyze specific lab
  python -m pyHaasAPI_v2.cli analysis labs --lab-id lab123 --top-count 10
  
  # Analyze bots
  python -m pyHaasAPI_v2.cli analysis bots --performance-metrics
  
  # Walk Forward Optimization
  python -m pyHaasAPI_v2.cli analysis wfo --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31
  
  # Generate reports
  python -m pyHaasAPI_v2.cli analysis reports --format csv --output-dir reports/
            """
        )
        
        # Add common options
        parser = self.create_parser("Analysis operations")
        
        # Analysis-specific options
        parser.add_argument(
            'action',
            choices=['labs', 'bots', 'wfo', 'performance', 'reports', 'labs-without-bots'],
            help='Analysis action to perform'
        )
        parser.add_argument('--lab-id', help='Lab ID')
        parser.add_argument('--bot-id', help='Bot ID')
        parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
        parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
        parser.add_argument('--top-count', type=int, default=10, help='Number of top results to show')
        parser.add_argument('--generate-reports', action='store_true', help='Generate analysis reports')
        parser.add_argument('--performance-metrics', action='store_true', help='Include performance metrics')
        parser.add_argument('--format', choices=['json', 'csv', 'html', 'markdown'], default='csv', help='Report format')
        parser.add_argument('--output-dir', default='reports', help='Output directory for reports')
        parser.add_argument('--output-file', help='Output file path')
        parser.add_argument('--min-roi', type=float, help='Minimum ROI filter')
        parser.add_argument('--min-winrate', type=float, help='Minimum win rate filter')
        parser.add_argument('--min-trades', type=int, help='Minimum trades filter')
        parser.add_argument('--zero-drawdown-only', action='store_true', default=True, 
                           help='Only recommend strategies with zero or positive drawdown (default: True)')
        parser.add_argument('--allow-negative-drawdown', action='store_true', 
                           help='Allow strategies with negative drawdown (NOT RECOMMENDED)')
        parser.add_argument('--server', help='Server name (srv01, srv02, srv03)')
        
        return parser

    async def analyze_labs(self, args: argparse.Namespace) -> int:
        """Analyze labs"""
        try:
            self.logger.info("Analyzing labs...")
            
            if not self.analysis_service:
                self.logger.error("Analysis service not initialized")
                return 1
            
            # Get labs to analyze
            if args.lab_id:
                lab_ids = [args.lab_id]
            else:
                # Get all labs
                labs = await self.lab_service.get_all_labs()
                lab_ids = [lab.id for lab in labs]
            
            if not lab_ids:
                self.logger.info("No labs found to analyze")
                return 0
            
            self.logger.info(f"Analyzing {len(lab_ids)} labs...")
            
            # Analyze each lab
            results = []
            for lab_id in lab_ids:
                try:
                    # Enforce zero drawdown requirement unless explicitly overridden
                    if args.allow_negative_drawdown:
                        self.logger.warning("⚠️ WARNING: Allowing negative drawdown strategies - NOT RECOMMENDED!")
                    
                    result = await self.analysis_service.analyze_lab_comprehensive(
                        lab_id=lab_id,
                        top_count=args.top_count,
                        min_win_rate=args.min_winrate or 0.3,
                        min_trades=args.min_trades or 5,
                        sort_by="roe"
                    )
                    if result.success:
                        results.append(result.data)
                        self.logger.info(f"Analyzed lab {lab_id}: {len(result.data.top_backtests)} backtests")
                    else:
                        self.logger.warning(f"Failed to analyze lab {lab_id}: {result.error}")
                except Exception as e:
                    self.logger.warning(f"Error analyzing lab {lab_id}: {e}")
            
            if not results:
                self.logger.info("No successful lab analyses")
                return 0
            
            # Display results
            self._display_lab_analysis_results(results, args)
            
            # Generate reports if requested
            if args.generate_reports and self.reporting_service:
                await self._generate_lab_reports(results, args)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error analyzing labs: {e}")
            return 1

    async def analyze_bots(self, args: argparse.Namespace) -> int:
        """Analyze bots"""
        try:
            self.logger.info("Analyzing bots...")
            
            if not self.analysis_service:
                self.logger.error("Analysis service not initialized")
                return 1
            
            # Get bots to analyze
            if args.bot_id:
                bot_ids = [args.bot_id]
            else:
                # Get all bots
                bots = await self.bot_service.get_all_bots()
                bot_ids = [bot.id for bot in bots]
            
            if not bot_ids:
                self.logger.info("No bots found to analyze")
                return 0
            
            self.logger.info(f"Analyzing {len(bot_ids)} bots...")
            
            # Analyze each bot
            results = []
            for bot_id in bot_ids:
                try:
                    result = await self.analysis_service.analyze_bot(bot_id)
                    if result.success:
                        results.append(result.data)
                        self.logger.info(f"Analyzed bot {bot_id}")
                    else:
                        self.logger.warning(f"Failed to analyze bot {bot_id}: {result.error}")
                except Exception as e:
                    self.logger.warning(f"Error analyzing bot {bot_id}: {e}")
            
            if not results:
                self.logger.info("No successful bot analyses")
                return 0
            
            # Display results
            self._display_bot_analysis_results(results, args)
            
            # Generate reports if requested
            if args.generate_reports and self.reporting_service:
                await self._generate_bot_reports(results, args)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error analyzing bots: {e}")
            return 1

    async def analyze_wfo(self, args: argparse.Namespace) -> int:
        """Perform Walk Forward Optimization analysis"""
        try:
            if not args.lab_id:
                self.logger.error("Lab ID is required for WFO analysis")
                return 1
            
            if not args.start_date or not args.end_date:
                self.logger.error("Start date and end date are required for WFO analysis")
                return 1
            
            self.logger.info(f"Performing WFO analysis for lab {args.lab_id}...")
            
            if not self.analysis_service:
                self.logger.error("Analysis service not initialized")
                return 1
            
            # Parse dates
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
            
            # Perform WFO analysis
            result = await self.analysis_service.analyze_wfo(
                lab_id=args.lab_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if result.success:
                self.logger.info(f"Successfully completed WFO analysis for lab {args.lab_id}")
                
                # Display results
                self._display_wfo_results(result.data, args)
                
                # Generate report if requested
                if args.generate_reports and self.reporting_service:
                    await self._generate_wfo_report(result.data, args)
                
                return 0
            else:
                self.logger.error(f"Failed to perform WFO analysis: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in WFO analysis: {e}")
            return 1

    async def analyze_performance(self, args: argparse.Namespace) -> int:
        """Analyze performance metrics"""
        try:
            self.logger.info("Analyzing performance metrics...")
            
            if not self.analysis_service:
                self.logger.error("Analysis service not initialized")
                return 1
            
            # Get performance metrics
            result = await self.analysis_service.get_performance_metrics()
            
            if result.success:
                self.logger.info("Successfully retrieved performance metrics")
                
                # Display results
                self._display_performance_metrics(result.data, args)
                
                # Generate report if requested
                if args.generate_reports and self.reporting_service:
                    await self._generate_performance_report(result.data, args)
                
                return 0
            else:
                self.logger.error(f"Failed to get performance metrics: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error analyzing performance: {e}")
            return 1

    async def generate_reports(self, args: argparse.Namespace) -> int:
        """Generate analysis reports"""
        try:
            self.logger.info("Generating analysis reports...")
            
            if not self.reporting_service:
                self.logger.error("Reporting service not initialized")
                return 1
            
            # Generate comprehensive reports
            report_paths = []
            
            # Lab analysis report
            if args.lab_id:
                lab_result = await self.analysis_service.analyze_lab(args.lab_id)
                if lab_result.success:
                    path = await self.reporting_service.generate_analysis_report(
                        [lab_result.data],
                        report_type="lab_analysis",
                        format=args.format
                    )
                    report_paths.append(path)
            
            # Bot analysis report
            if args.bot_id:
                bot_result = await self.analysis_service.analyze_bot(args.bot_id)
                if bot_result.success:
                    path = await self.reporting_service.generate_bot_recommendations_report(
                        [bot_result.data],
                        report_type="bot_recommendations",
                        format=args.format
                    )
                    report_paths.append(path)
            
            # Generate bot recommendations with zero drawdown requirement
            if args.lab_id:
                recommendations = await self.analysis_service.generate_bot_recommendations(
                    lab_ids=[args.lab_id],
                    top_count=args.top_count,
                    min_win_rate=args.min_winrate or 0.6,
                    min_trades=args.min_trades or 10,
                    min_roi=args.min_roi or 50.0
                )
                if recommendations:
                    self.logger.info(f"Generated {len(recommendations)} bot recommendations (zero drawdown only)")
                    for rec in recommendations[:5]:  # Show top 5
                        self.logger.info(f"  - {rec['script_name']}: ROI {rec['roi_percentage']:.1f}%, WR {rec['win_rate']:.1%}, DD {rec['max_drawdown']:.2f}")
            
            if report_paths:
                self.logger.info(f"Generated {len(report_paths)} reports:")
                for path in report_paths:
                    print(f"  {path}")
                return 0
            else:
                self.logger.info("No reports generated")
                return 0
                
        except Exception as e:
            self.logger.error(f"Error generating reports: {e}")
            return 1

    def _display_lab_analysis_results(self, results: List[Any], args: argparse.Namespace) -> None:
        """Display lab analysis results"""
        print(f"\nLab Analysis Results ({len(results)} labs):")
        print("=" * 120)
        
        for result in results:
            print(f"\nLab: {result.lab_id}")
            print("-" * 100)
            print(f"{'Backtest ID':<20} {'ROI %':<10} {'Win Rate':<10} {'Trades':<10} {'Profit USDT':<15} {'Max DD':<15}")
            print("-" * 100)
            
            for backtest in result.top_backtests:
                dd_display = f"{backtest.max_drawdown:.2f}" if backtest.max_drawdown >= 0 else "❌ REJECTED"
                print(f"{backtest.backtest_id:<20} {backtest.roi_percentage:<10.2f} {backtest.win_rate:<10.2f} {backtest.total_trades:<10} {backtest.realized_profits_usdt:<15.2f} {dd_display:<15}")
            
            print("-" * 100)

    def _display_bot_analysis_results(self, results: List[Any], args: argparse.Namespace) -> None:
        """Display bot analysis results"""
        print(f"\nBot Analysis Results ({len(results)} bots):")
        print("=" * 100)
        
        for result in results:
            print(f"\nBot: {result.bot_id}")
            print("-" * 60)
            print(f"Status: {result.status}")
            print(f"Performance: {result.performance_metrics}")
            print(f"Recommendations: {result.recommendations}")
            print("-" * 60)

    def _display_wfo_results(self, result: Any, args: argparse.Namespace) -> None:
        """Display WFO analysis results"""
        print(f"\nWalk Forward Optimization Results:")
        print("=" * 80)
        print(f"Lab ID: {result.lab_id}")
        print(f"Periods: {len(result.periods)}")
        print(f"Average Performance: {result.average_performance}")
        print(f"Stability Score: {result.stability_score}")
        print("-" * 80)

    def _display_performance_metrics(self, metrics: Any, args: argparse.Namespace) -> None:
        """Display performance metrics"""
        print(f"\nPerformance Metrics:")
        print("=" * 60)
        print(f"Total Requests: {metrics.total_requests}")
        print(f"Success Rate: {metrics.success_rate:.2%}")
        print(f"Average Response Time: {metrics.average_response_time:.2f}s")
        print(f"Cache Hit Rate: {metrics.cache_hit_rate:.2%}")
        print("-" * 60)

    async def _generate_lab_reports(self, results: List[Any], args: argparse.Namespace) -> None:
        """Generate lab analysis reports"""
        if not self.reporting_service:
            return
        
        report_path = await self.reporting_service.generate_analysis_report(
            results,
            report_type="lab_analysis",
            format=args.format
        )
        self.logger.info(f"Lab analysis report generated: {report_path}")

    async def _generate_bot_reports(self, results: List[Any], args: argparse.Namespace) -> None:
        """Generate bot analysis reports"""
        if not self.reporting_service:
            return
        
        report_path = await self.reporting_service.generate_bot_recommendations_report(
            results,
            report_type="bot_recommendations",
            format=args.format
        )
        self.logger.info(f"Bot analysis report generated: {report_path}")

    async def _generate_wfo_report(self, result: Any, args: argparse.Namespace) -> None:
        """Generate WFO analysis report"""
        if not self.reporting_service:
            return
        
        report_path = await self.reporting_service.generate_wfo_report(
            result,
            report_type="wfo_analysis",
            format=args.format
        )
        self.logger.info(f"WFO analysis report generated: {report_path}")

    async def _generate_performance_report(self, metrics: Any, args: argparse.Namespace) -> None:
        """Generate performance metrics report"""
        if not self.reporting_service:
            return
        
        report_path = await self.reporting_service.generate_performance_report(
            metrics,
            report_type="performance_analysis",
            format=args.format
        )
        self.logger.info(f"Performance report generated: {report_path}")
    
    async def analyze_labs_without_bots(self, args: argparse.Namespace) -> int:
        """Analyze individual backtest files for labs without bots"""
        try:
            # Parse server from args
            server = getattr(args, 'server', None)
            if not server:
                self.logger.error("Server name required. Use --server <name>")
                return 1
            
            min_winrate = getattr(args, 'min_winrate', None) or 0.55
            
            print(f"🔍 Analyzing individual backtest files for labs without bots on {server}...")
            print(f"📊 Filter criteria: ZERO drawdown (max_drawdown == 0), {min_winrate*100:.0f}%+ win rate, sorted by ROE")
            
            # Import required modules
            from pathlib import Path
            import json
            import glob
            
            # Load snapshot to get labs without bots
            snapshot_files = glob.glob(f"unified_cache/snapshots/{server}_*.json")
            if not snapshot_files:
                print(f"❌ No snapshot found for {server}. Run download command first.")
                return 1
            
            # Get latest snapshot
            latest_snapshot = max(snapshot_files, key=lambda x: Path(x).stat().st_mtime)
            print(f"📁 Loading snapshot: {latest_snapshot}")
            
            with open(latest_snapshot, 'r') as f:
                snapshot_data = json.load(f)
            
            labs_without_bots = snapshot_data.get('labs_without_bots', [])
            if not labs_without_bots:
                print(f"✅ No labs without bots found on {server}")
                return 0
            
            print(f"📈 Found {len(labs_without_bots)} labs without bots")
            
            # Analyze each lab
            analysis_results = {}
            total_qualifying_backtests = 0
            
            for lab_id in labs_without_bots:
                print(f"\n🔍 Analyzing lab {lab_id[:8]}...")
                
                try:
                    # Find all backtest files for this lab (with server prefix)
                    backtest_files = glob.glob(f"unified_cache/backtests/{server}_{lab_id}_*.json")
                    if not backtest_files:
                        print(f"   ⚠️  No backtest files found for lab {lab_id[:8]}")
                        continue
                    
                    print(f"   📁 Found {len(backtest_files)} backtest files")
                    
                    # Load and analyze each backtest
                    qualifying_backtests = []
                    
                    for file in backtest_files:
                        try:
                            with open(file, 'r') as f:
                                bt = json.load(f)
                            
                            # Extract key metrics
                            max_drawdown = bt.get('max_drawdown', 0)
                            win_rate = bt.get('win_rate', 0)
                            roe = bt.get('roe', 0)
                            
                            # CRITICAL FILTERS - ZERO drawdown (exactly 0) + 55%+ win rate
                            if (max_drawdown == 0 and  # ZERO drawdown (exactly 0, not < 0.01)
                                win_rate >= min_winrate):  # 55%+ win rate
                                
                                qualifying_backtests.append({
                                    'backtest_id': bt.get('backtest_id', 'N/A'),
                                    'roi': bt.get('roi', 0),
                                    'roe': roe,
                                    'win_rate': win_rate,
                                    'max_drawdown': max_drawdown,
                                    'total_trades': bt.get('total_trades', 0),
                                    'realized_profits_usdt': bt.get('realized_profits_usdt', 0),
                                    'starting_balance': bt.get('starting_balance', 0),
                                    'file_path': str(file)
                                })
                        
                        except Exception as e:
                            print(f"   ⚠️  Error loading file {file}: {e}")
                            continue
                    
                    if not qualifying_backtests:
                        print(f"   ❌ No qualifying backtests found (ZERO drawdown + {min_winrate*100:.0f}%+ WR)")
                        continue
                    
                    # Sort by ROE descending (highest first)
                    qualifying_backtests.sort(key=lambda x: x.get('roe', 0), reverse=True)
                    top_5 = qualifying_backtests[:5]
                    
                    print(f"   ✅ Found {len(qualifying_backtests)} qualifying backtests")
                    roe_values = [f"{bt.get('roe', 0):.1f}%" for bt in top_5]
                    print(f"   🏆 Top 5 ROE: {roe_values}")
                    
                    # Store results
                    lab_name = next((lab['name'] for lab in snapshot_data.get('labs', []) if lab['lab_id'] == lab_id), lab_id[:8])
                    analysis_results[lab_id] = {
                        'lab_name': lab_name,
                        'total_qualifying': len(qualifying_backtests),
                        'top_5': top_5
                    }
                    
                    total_qualifying_backtests += len(qualifying_backtests)
                    
                except Exception as e:
                    print(f"   ❌ Error analyzing lab {lab_id[:8]}: {e}")
                    continue
            
            # Save analysis results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            analysis_file = f"unified_cache/analysis/{server}_top_backtests_{timestamp}.json"
            Path("unified_cache/analysis").mkdir(parents=True, exist_ok=True)
            
            analysis_data = {
                'server': server,
                'timestamp': datetime.now().isoformat(),
                'filter_criteria': {
                    'max_drawdown': 0,  # ZERO drawdown (exactly 0)
                    'min_winrate': min_winrate,
                    'sort_by': 'roe'  # Sort by ROE descending
                },
                'summary': {
                    'labs_analyzed': len(labs_without_bots),
                    'labs_with_qualifying_backtests': len(analysis_results),
                    'total_qualifying_backtests': total_qualifying_backtests,
                    'total_top_5_backtests': sum(len(result['top_5']) for result in analysis_results.values())
                },
                'results': analysis_results
            }
            
            with open(analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)
            
            # Summary
            print(f"\n🎉 Analysis completed for {server}!")
            print(f"📊 Summary:")
            print(f"   - Labs analyzed: {len(labs_without_bots)}")
            print(f"   - Labs with qualifying backtests: {len(analysis_results)}")
            print(f"   - Total qualifying backtests: {total_qualifying_backtests}")
            print(f"   - Total top 5 backtests: {sum(len(result['top_5']) for result in analysis_results.values())}")
            print(f"   - Analysis saved: {analysis_file}")
            
            # Show per-lab results
            print(f"\n📋 Per-lab results:")
            for lab_id, result in analysis_results.items():
                print(f"   - {result['lab_name']}: {result['total_qualifying']} qualifying, {len(result['top_5'])} top 5")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error analyzing labs without bots: {e}")
            import traceback
            traceback.print_exc()
            return 1
