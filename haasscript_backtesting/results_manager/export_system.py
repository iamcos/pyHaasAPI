"""
Enhanced export system for backtest results.
"""

import json
import csv
import io
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from ..models import ProcessedResults, Trade


logger = logging.getLogger(__name__)


class ResultsExportSystem:
    """
    Enhanced export system for backtest results.
    
    Supports multiple formats:
    - JSON (detailed and summary)
    - CSV (trades, metrics, summary)
    - Excel (multi-sheet workbook)
    - Database formats
    - Lab-compatible formats
    """
    
    def __init__(self):
        """Initialize export system."""
        self.logger = logging.getLogger(__name__)
    
    def export_results(self, results: ProcessedResults, format: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Export results in specified format with options.
        
        Args:
            results: ProcessedResults to export
            format: Export format ('json', 'csv', 'excel', 'json_summary')
            options: Optional export configuration
            
        Returns:
            Exported data as bytes
        """
        options = options or {}
        
        self.logger.info(f"Exporting results for {results.backtest_id} in {format} format")
        
        try:
            if format.lower() == 'json':
                return self._export_json_detailed(results, options)
            elif format.lower() == 'json_summary':
                return self._export_json_summary(results, options)
            elif format.lower() == 'csv':
                return self._export_csv_comprehensive(results, options)
            elif format.lower() == 'excel':
                return self._export_excel_workbook(results, options)
            elif format.lower() == 'lab_compatible':
                return self._export_lab_compatible(results, options)
            elif format.lower() == 'database':
                return self._export_database_format(results, options)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Export failed for format {format}: {e}")
            raise
    
    def export_comparison_results(self, comparison_data: Dict[str, Any], format: str) -> bytes:
        """
        Export comparison analysis results.
        
        Args:
            comparison_data: Comparison analysis data
            format: Export format
            
        Returns:
            Exported comparison data as bytes
        """
        self.logger.info(f"Exporting comparison results in {format} format")
        
        if format.lower() == 'json':
            return json.dumps(comparison_data, indent=2, default=str).encode('utf-8')
        elif format.lower() == 'csv':
            return self._export_comparison_csv(comparison_data)
        elif format.lower() == 'excel':
            return self._export_comparison_excel(comparison_data)
        else:
            raise ValueError(f"Unsupported comparison export format: {format}")
    
    def _export_json_detailed(self, results: ProcessedResults, options: Dict[str, Any]) -> bytes:
        """Export detailed JSON with all available data."""
        export_data = {
            'metadata': {
                'backtest_id': results.backtest_id,
                'script_id': results.script_id,
                'export_timestamp': datetime.now().isoformat(),
                'export_format': 'json_detailed',
                'processing_time': results.processing_time
            },
            'execution_summary': {
                'backtest_id': results.execution_summary.backtest_id,
                'script_name': results.execution_summary.script_name,
                'market_tag': results.execution_summary.market_tag,
                'start_date': results.execution_summary.start_date.isoformat(),
                'end_date': results.execution_summary.end_date.isoformat(),
                'duration_days': results.execution_summary.duration.days,
                'total_trades': results.execution_summary.total_trades,
                'success_rate': results.execution_summary.success_rate,
                'final_balance': results.execution_summary.final_balance,
                'max_drawdown': results.execution_summary.max_drawdown,
                'execution_time_seconds': results.execution_summary.execution_time.total_seconds()
            },
            'performance_metrics': results.execution_metrics.to_dict(),
            'performance_data': {
                'initial_balance': results.performance_data.initial_balance,
                'final_balance': results.performance_data.final_balance,
                'peak_balance': results.performance_data.peak_balance,
                'lowest_balance': results.performance_data.lowest_balance,
                'total_trades': results.performance_data.total_trades,
                'winning_trades': results.performance_data.winning_trades,
                'losing_trades': results.performance_data.losing_trades,
                'win_rate': results.performance_data.win_rate,
                'profit_factor': results.performance_data.profit_factor,
                'largest_win': results.performance_data.largest_win,
                'largest_loss': results.performance_data.largest_loss,
                'average_win': results.performance_data.average_win,
                'average_loss': results.performance_data.average_loss,
                'total_time_in_market_hours': results.performance_data.total_time_in_market.total_seconds() / 3600,
                'average_trade_duration_hours': results.performance_data.average_trade_duration.total_seconds() / 3600,
                'longest_winning_streak': results.performance_data.longest_winning_streak,
                'longest_losing_streak': results.performance_data.longest_losing_streak
            },
            'trade_history': [
                {
                    'trade_id': trade.trade_id,
                    'timestamp': trade.timestamp.isoformat(),
                    'trade_type': trade.trade_type.value,
                    'price': trade.price,
                    'amount': trade.amount,
                    'fee': trade.fee,
                    'status': trade.status.value,
                    'profit_loss': trade.profit_loss,
                    'duration_hours': trade.duration.total_seconds() / 3600 if trade.duration else None,
                    'value': trade.value,
                    'net_value': trade.net_value
                }
                for trade in results.trade_history
            ]
        }
        
        # Add chart data if available
        if results.chart_data:
            export_data['chart_data'] = {
                'timestamps': [ts.isoformat() for ts in results.chart_data.timestamps],
                'equity_curve': results.chart_data.equity_curve,
                'drawdown_curve': results.chart_data.drawdown_curve,
                'trade_markers': results.chart_data.trade_markers,
                'indicators': results.chart_data.indicators
            }
        
        # Add raw data if requested
        if options.get('include_raw_data', False):
            export_data['raw_data'] = {
                'runtime_data': results.raw_runtime_data,
                'logs': results.raw_logs
            }
        
        # Add trade summary
        export_data['trade_summary'] = results.get_trade_summary()
        
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    def _export_json_summary(self, results: ProcessedResults, options: Dict[str, Any]) -> bytes:
        """Export summary JSON with key metrics only."""
        summary_data = {
            'backtest_id': results.backtest_id,
            'script_id': results.script_id,
            'export_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_return': results.execution_metrics.total_return,
                'sharpe_ratio': results.execution_metrics.sharpe_ratio,
                'max_drawdown': results.execution_metrics.max_drawdown,
                'profit_factor': results.execution_metrics.profit_factor,
                'total_trades': len(results.trade_history),
                'win_rate': results.performance_data.win_rate,
                'final_balance': results.performance_data.final_balance,
                'duration_days': results.execution_summary.duration.days
            },
            'key_metrics': {
                'risk_adjusted': {
                    'sharpe_ratio': results.execution_metrics.sharpe_ratio,
                    'sortino_ratio': results.execution_metrics.sortino_ratio,
                    'calmar_ratio': results.execution_metrics.calmar_ratio
                },
                'risk_metrics': {
                    'volatility': results.execution_metrics.volatility,
                    'max_drawdown': results.execution_metrics.max_drawdown,
                    'value_at_risk_95': results.execution_metrics.value_at_risk_95
                },
                'performance': {
                    'total_return': results.execution_metrics.total_return,
                    'annualized_return': results.execution_metrics.annualized_return,
                    'profit_factor': results.execution_metrics.profit_factor
                }
            }
        }
        
        return json.dumps(summary_data, indent=2, default=str).encode('utf-8')
    
    def _export_csv_comprehensive(self, results: ProcessedResults, options: Dict[str, Any]) -> bytes:
        """Export comprehensive CSV with multiple sections."""
        output = io.StringIO()
        
        # Export type selection
        export_type = options.get('csv_type', 'trades')  # 'trades', 'metrics', 'summary'
        
        if export_type == 'trades':
            # Trade history CSV
            writer = csv.writer(output)
            writer.writerow([
                'Trade ID', 'Timestamp', 'Type', 'Price', 'Amount', 'Fee', 
                'Status', 'Profit/Loss', 'Duration (hours)', 'Value', 'Net Value'
            ])
            
            for trade in results.trade_history:
                writer.writerow([
                    trade.trade_id,
                    trade.timestamp.isoformat(),
                    trade.trade_type.value,
                    trade.price,
                    trade.amount,
                    trade.fee,
                    trade.status.value,
                    trade.profit_loss or 0,
                    trade.duration.total_seconds() / 3600 if trade.duration else 0,
                    trade.value,
                    trade.net_value
                ])
        
        elif export_type == 'metrics':
            # Performance metrics CSV
            writer = csv.writer(output)
            writer.writerow(['Metric', 'Value'])
            
            metrics_dict = results.execution_metrics.to_dict()
            for metric, value in metrics_dict.items():
                writer.writerow([metric.replace('_', ' ').title(), value])
        
        elif export_type == 'summary':
            # Summary CSV
            writer = csv.writer(output)
            writer.writerow(['Category', 'Metric', 'Value'])
            
            # Basic info
            writer.writerow(['Basic', 'Backtest ID', results.backtest_id])
            writer.writerow(['Basic', 'Script ID', results.script_id])
            writer.writerow(['Basic', 'Total Trades', len(results.trade_history)])
            writer.writerow(['Basic', 'Duration (days)', results.execution_summary.duration.days])
            
            # Performance metrics
            writer.writerow(['Performance', 'Total Return (%)', results.execution_metrics.total_return])
            writer.writerow(['Performance', 'Annualized Return (%)', results.execution_metrics.annualized_return])
            writer.writerow(['Performance', 'Profit Factor', results.execution_metrics.profit_factor])
            writer.writerow(['Performance', 'Win Rate (%)', results.performance_data.win_rate])
            
            # Risk metrics
            writer.writerow(['Risk', 'Max Drawdown (%)', results.execution_metrics.max_drawdown])
            writer.writerow(['Risk', 'Volatility (%)', results.execution_metrics.volatility])
            writer.writerow(['Risk', 'Sharpe Ratio', results.execution_metrics.sharpe_ratio])
            writer.writerow(['Risk', 'Sortino Ratio', results.execution_metrics.sortino_ratio])
        
        return output.getvalue().encode('utf-8')
    
    def _export_excel_workbook(self, results: ProcessedResults, options: Dict[str, Any]) -> bytes:
        """Export Excel workbook with multiple sheets."""
        try:
            import pandas as pd
            from io import BytesIO
            
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Metric': [
                        'Backtest ID', 'Script ID', 'Total Return (%)', 'Annualized Return (%)',
                        'Sharpe Ratio', 'Sortino Ratio', 'Max Drawdown (%)', 'Volatility (%)',
                        'Profit Factor', 'Win Rate (%)', 'Total Trades', 'Duration (days)'
                    ],
                    'Value': [
                        results.backtest_id, results.script_id, results.execution_metrics.total_return,
                        results.execution_metrics.annualized_return, results.execution_metrics.sharpe_ratio,
                        results.execution_metrics.sortino_ratio, results.execution_metrics.max_drawdown,
                        results.execution_metrics.volatility, results.execution_metrics.profit_factor,
                        results.performance_data.win_rate, len(results.trade_history),
                        results.execution_summary.duration.days
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Trade history sheet
                if results.trade_history:
                    trades_data = []
                    for trade in results.trade_history:
                        trades_data.append({
                            'Trade ID': trade.trade_id,
                            'Timestamp': trade.timestamp,
                            'Type': trade.trade_type.value,
                            'Price': trade.price,
                            'Amount': trade.amount,
                            'Fee': trade.fee,
                            'Status': trade.status.value,
                            'Profit/Loss': trade.profit_loss or 0,
                            'Duration (hours)': trade.duration.total_seconds() / 3600 if trade.duration else 0,
                            'Value': trade.value,
                            'Net Value': trade.net_value
                        })
                    
                    pd.DataFrame(trades_data).to_excel(writer, sheet_name='Trades', index=False)
                
                # Metrics sheet
                metrics_dict = results.execution_metrics.to_dict()
                metrics_data = {
                    'Metric': [k.replace('_', ' ').title() for k in metrics_dict.keys()],
                    'Value': list(metrics_dict.values())
                }
                pd.DataFrame(metrics_data).to_excel(writer, sheet_name='Metrics', index=False)
                
                # Performance data sheet
                perf_data = {
                    'Metric': [
                        'Initial Balance', 'Final Balance', 'Peak Balance', 'Lowest Balance',
                        'Total Trades', 'Winning Trades', 'Losing Trades', 'Win Rate (%)',
                        'Largest Win', 'Largest Loss', 'Average Win', 'Average Loss',
                        'Longest Winning Streak', 'Longest Losing Streak'
                    ],
                    'Value': [
                        results.performance_data.initial_balance, results.performance_data.final_balance,
                        results.performance_data.peak_balance, results.performance_data.lowest_balance,
                        results.performance_data.total_trades, results.performance_data.winning_trades,
                        results.performance_data.losing_trades, results.performance_data.win_rate,
                        results.performance_data.largest_win, results.performance_data.largest_loss,
                        results.performance_data.average_win, results.performance_data.average_loss,
                        results.performance_data.longest_winning_streak, results.performance_data.longest_losing_streak
                    ]
                }
                pd.DataFrame(perf_data).to_excel(writer, sheet_name='Performance', index=False)
            
            output.seek(0)
            return output.read()
            
        except ImportError:
            self.logger.warning("pandas/openpyxl not available, falling back to CSV format")
            return self._export_csv_comprehensive(results, {'csv_type': 'summary'})
    
    def _export_lab_compatible(self, results: ProcessedResults, options: Dict[str, Any]) -> bytes:
        """Export in lab-compatible format for integration."""
        lab_format = {
            'backtest_id': results.backtest_id,
            'script_id': results.script_id,
            'execution_summary': {
                'start_date': results.execution_summary.start_date.isoformat(),
                'end_date': results.execution_summary.end_date.isoformat(),
                'duration_days': results.execution_summary.duration.days,
                'total_trades': results.execution_summary.total_trades,
                'success_rate': results.execution_summary.success_rate,
                'final_balance': results.execution_summary.final_balance
            },
            'performance_metrics': {
                'total_return': results.execution_metrics.total_return,
                'sharpe_ratio': results.execution_metrics.sharpe_ratio,
                'max_drawdown': results.execution_metrics.max_drawdown,
                'profit_factor': results.execution_metrics.profit_factor,
                'volatility': results.execution_metrics.volatility,
                'win_rate': results.performance_data.win_rate
            },
            'trade_history': [
                {
                    'timestamp': trade.timestamp.isoformat(),
                    'type': trade.trade_type.value,
                    'price': trade.price,
                    'amount': trade.amount,
                    'fee': trade.fee,
                    'profit_loss': trade.profit_loss or 0
                }
                for trade in results.trade_history
            ],
            'performance_data': {
                'initial_balance': results.performance_data.initial_balance,
                'final_balance': results.performance_data.final_balance,
                'total_trades': results.performance_data.total_trades,
                'winning_trades': results.performance_data.winning_trades,
                'losing_trades': results.performance_data.losing_trades,
                'win_rate': results.performance_data.win_rate,
                'profit_factor': results.performance_data.profit_factor
            },
            'export_metadata': {
                'format_version': '1.0',
                'export_timestamp': datetime.now().isoformat(),
                'compatible_with': 'lab_system'
            }
        }
        
        return json.dumps(lab_format, indent=2, default=str).encode('utf-8')
    
    def _export_database_format(self, results: ProcessedResults, options: Dict[str, Any]) -> bytes:
        """Export in database-friendly format."""
        db_format = {
            'backtest_execution': {
                'id': results.backtest_id,
                'script_id': results.script_id,
                'started_at': results.execution_summary.start_date.isoformat(),
                'completed_at': results.execution_summary.end_date.isoformat(),
                'duration_seconds': results.execution_summary.duration.total_seconds(),
                'total_trades': len(results.trade_history),
                'final_balance': results.performance_data.final_balance,
                'created_at': datetime.now().isoformat()
            },
            'execution_metrics': {
                'backtest_id': results.backtest_id,
                **results.execution_metrics.to_dict(),
                'created_at': datetime.now().isoformat()
            },
            'performance_data': {
                'backtest_id': results.backtest_id,
                'initial_balance': results.performance_data.initial_balance,
                'final_balance': results.performance_data.final_balance,
                'peak_balance': results.performance_data.peak_balance,
                'lowest_balance': results.performance_data.lowest_balance,
                'total_trades': results.performance_data.total_trades,
                'winning_trades': results.performance_data.winning_trades,
                'losing_trades': results.performance_data.losing_trades,
                'win_rate': results.performance_data.win_rate,
                'profit_factor': results.performance_data.profit_factor,
                'created_at': datetime.now().isoformat()
            },
            'trades': [
                {
                    'backtest_id': results.backtest_id,
                    'trade_id': trade.trade_id,
                    'timestamp': trade.timestamp.isoformat(),
                    'trade_type': trade.trade_type.value,
                    'price': trade.price,
                    'amount': trade.amount,
                    'fee': trade.fee,
                    'status': trade.status.value,
                    'profit_loss': trade.profit_loss,
                    'duration_seconds': trade.duration.total_seconds() if trade.duration else None,
                    'created_at': datetime.now().isoformat()
                }
                for trade in results.trade_history
            ]
        }
        
        return json.dumps(db_format, indent=2, default=str).encode('utf-8')
    
    def _export_comparison_csv(self, comparison_data: Dict[str, Any]) -> bytes:
        """Export comparison results as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Summary
        writer.writerow(['Comparison Summary'])
        writer.writerow(['Total Results', comparison_data.get('summary', {}).get('total_results', 0)])
        writer.writerow(['Comparison Date', comparison_data.get('summary', {}).get('comparison_date', '')])
        writer.writerow([])
        
        # Basic comparison metrics
        if 'basic_comparison' in comparison_data:
            writer.writerow(['Metric Comparison'])
            writer.writerow(['Metric', 'Best', 'Worst', 'Mean', 'Std Dev'])
            
            metrics_comp = comparison_data['basic_comparison'].get('metrics_comparison', {})
            for metric, stats in metrics_comp.items():
                writer.writerow([
                    metric.replace('_', ' ').title(),
                    stats.get('best', ''),
                    stats.get('worst', ''),
                    stats.get('mean', ''),
                    stats.get('std_dev', '')
                ])
        
        return output.getvalue().encode('utf-8')
    
    def _export_comparison_excel(self, comparison_data: Dict[str, Any]) -> bytes:
        """Export comparison results as Excel workbook."""
        try:
            import pandas as pd
            from io import BytesIO
            
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary = comparison_data.get('summary', {})
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Metrics comparison
                if 'basic_comparison' in comparison_data:
                    metrics_data = []
                    metrics_comp = comparison_data['basic_comparison'].get('metrics_comparison', {})
                    
                    for metric, stats in metrics_comp.items():
                        metrics_data.append({
                            'Metric': metric.replace('_', ' ').title(),
                            'Best': stats.get('best', ''),
                            'Worst': stats.get('worst', ''),
                            'Mean': stats.get('mean', ''),
                            'Std Dev': stats.get('std_dev', ''),
                            'Range': stats.get('range', '')
                        })
                    
                    if metrics_data:
                        pd.DataFrame(metrics_data).to_excel(writer, sheet_name='Metrics', index=False)
                
                # Rankings
                if 'risk_adjusted_rankings' in comparison_data:
                    rankings_data = comparison_data['risk_adjusted_rankings'].get('composite_risk_scores', [])
                    if rankings_data:
                        pd.DataFrame(rankings_data).to_excel(writer, sheet_name='Rankings', index=False)
            
            output.seek(0)
            return output.read()
            
        except ImportError:
            self.logger.warning("pandas/openpyxl not available, falling back to CSV format")
            return self._export_comparison_csv(comparison_data)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return [
            'json',
            'json_summary', 
            'csv',
            'excel',
            'lab_compatible',
            'database'
        ]
    
    def get_format_options(self, format: str) -> Dict[str, Any]:
        """Get available options for a specific format."""
        options = {
            'json': {
                'include_raw_data': 'Include raw API response data',
                'include_chart_data': 'Include chart visualization data'
            },
            'csv': {
                'csv_type': 'Type of CSV export (trades, metrics, summary)'
            },
            'excel': {
                'include_charts': 'Include chart sheets (if supported)'
            },
            'lab_compatible': {
                'format_version': 'Lab format version compatibility'
            },
            'database': {
                'table_prefix': 'Prefix for database table names'
            }
        }
        
        return options.get(format, {})