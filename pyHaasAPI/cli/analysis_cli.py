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
            choices=['labs', 'bots', 'wfo', 'performance', 'reports'],
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
