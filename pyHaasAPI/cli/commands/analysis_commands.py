"""
Analysis command handlers - Direct calls to AnalysisService
"""

from typing import Any
from ..base import BaseCLI


class AnalysisCommands:
    """Analysis command handlers - thin wrappers around AnalysisService"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle analysis commands"""
        analysis_service = self.cli.analysis_service
        
        if not analysis_service:
            self.cli.logger.error("Analysis service not initialized")
            return 1
        
        try:
            if action == 'labs':
                # Analyze labs using AnalysisService
                if args.lab_id:
                    # Single lab analysis
                    result = await analysis_service.analyze_lab_comprehensive(
                        lab_id=args.lab_id,
                        top_count=args.top_count or 10,
                        min_win_rate=(args.min_winrate / 100.0) if args.min_winrate else 0.3,
                        min_trades=args.min_trades or 5,
                        sort_by=args.sort_by or 'roe'
                    )
                    results = [result]
                else:
                    # Multiple labs analysis
                    lab_service = self.cli.lab_service
                    if not lab_service:
                        self.cli.logger.error("Lab service not initialized")
                        return 1
                    
                    labs = await self.cli.lab_api.get_labs()
                    results = await analysis_service.analyze_multiple_labs(
                        lab_ids=[lab.lab_id for lab in labs],
                        top_count=args.top_count or 10,
                        min_win_rate=(args.min_winrate / 100.0) if args.min_winrate else 0.3,
                        min_trades=args.min_trades or 5,
                        sort_by=args.sort_by or 'roe'
                    )
                
                # Format output
                output_data = []
                for result in results:
                    output_data.append({
                        'lab_id': result.lab_id,
                        'lab_name': result.lab_name,
                        'total_backtests': result.total_backtests,
                        'average_roi': result.average_roi,
                        'best_roi': result.best_roi,
                        'average_win_rate': result.average_win_rate,
                        'top_performers_count': len(result.top_performers)
                    })
                
                self.cli.format_output(output_data, args.output_format, args.output_file)
                
                # Generate reports if requested
                if args.generate_reports:
                    from ...services.reporting import ReportConfig, ReportType, ReportFormat
                    reporting_service = self.cli.reporting_service
                    if reporting_service:
                        config = ReportConfig(
                            report_type=ReportType.LAB_ANALYSIS,
                            format=ReportFormat.CSV if args.output_format == 'csv' else ReportFormat.JSON
                        )
                        report_result = await reporting_service.generate_analysis_report(results, config)
                        self.cli.logger.info(f"Report generated: {report_result.report_path}")
                
                return 0
                
            elif action == 'bots':
                # Bot performance analysis - use BotAPI directly
                bot_api = self.cli.bot_api
                if not bot_api:
                    self.cli.logger.error("Bot API not initialized")
                    return 1
                
                bots = await bot_api.get_all_bots()
                
                # Format bot performance data
                bot_data = []
                for bot in bots:
                    bot_data.append({
                        'bot_id': self.cli.safe_get(bot, 'bot_id', ''),
                        'bot_name': self.cli.safe_get(bot, 'bot_name', ''),
                        'status': self.cli.safe_get(bot, 'status', ''),
                        'market_tag': self.cli.safe_get(bot, 'market_tag', ''),
                        'account_id': self.cli.safe_get(bot, 'account_id', ''),
                    })
                
                self.cli.format_output(bot_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'performance':
                # Get analysis statistics
                stats = await analysis_service.get_analysis_statistics()
                self.cli.format_output([stats], args.output_format, args.output_file)
                return 0
                
            else:
                self.cli.logger.error(f"Unknown analysis action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing analysis command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1



