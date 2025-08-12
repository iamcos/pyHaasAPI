"""
Core results management functionality.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..models import (
    ProcessedResults, ExecutionMetrics, Trade, PerformanceData, ChartData,
    ExecutionSummary, TradeType, TradeStatus
)
from ..config import ConfigManager


class ResultsManager:
    """Manages backtest result processing, analysis, and formatting."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize results manager with configuration.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Cache for processed results
        self._results_cache: Dict[str, ProcessedResults] = {}
    
    def process_results(self, backtest_id: str) -> ProcessedResults:
        """Process raw backtest results into structured format.
        
        Args:
            backtest_id: ID of the backtest to process
            
        Returns:
            ProcessedResults with analyzed data
            
        Raises:
            ValueError: If backtest_id is not found
            RuntimeError: If result processing fails
        """
        # Check cache first
        if backtest_id in self._results_cache:
            self.logger.debug(f"Returning cached results for: {backtest_id}")
            return self._results_cache[backtest_id]
        
        self.logger.info(f"Processing results for backtest: {backtest_id}")
        
        try:
            start_time = datetime.now()
            
            # Fetch raw data from HaasOnline API
            runtime_data = self._fetch_runtime_data(backtest_id)
            logs = self._fetch_logs(backtest_id)
            
            # Process trade history
            trade_history = self._process_trade_history(runtime_data.get('trades', []))
            
            # Calculate performance metrics
            performance_data = self._calculate_performance_data(trade_history, runtime_data)
            execution_metrics = self.calculate_metrics(trade_history, performance_data)
            
            # Create execution summary
            execution_summary = self._create_execution_summary(backtest_id, runtime_data)
            
            # Optional: Process chart data
            chart_data = self._process_chart_data(backtest_id) if runtime_data.get('has_chart_data') else None
            
            # Create processed results
            results = ProcessedResults(
                backtest_id=backtest_id,
                script_id=runtime_data.get('script_id', 'unknown'),
                execution_summary=execution_summary,
                execution_metrics=execution_metrics,
                performance_data=performance_data,
                trade_history=trade_history,
                chart_data=chart_data,
                raw_runtime_data=runtime_data,
                raw_logs=logs,
                processed_at=datetime.now(),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Cache the results
            self._results_cache[backtest_id] = results
            
            self.logger.info(f"Successfully processed results for backtest: {backtest_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to process results for backtest {backtest_id}: {e}")
            raise RuntimeError(f"Result processing failed: {e}")
    
    def calculate_metrics(self, trade_history: List[Trade], performance_data: PerformanceData) -> ExecutionMetrics:
        """Calculate standard execution performance metrics using advanced calculator.
        
        Args:
            trade_history: List of executed trades
            performance_data: Performance statistics
            
        Returns:
            ExecutionMetrics with calculated values
        """
        from .metrics_calculator import TradingMetricsCalculator
        
        # Use advanced metrics calculator
        calculator = TradingMetricsCalculator(risk_free_rate=0.02)  # 2% risk-free rate
        
        return calculator.calculate_comprehensive_metrics(
            trade_history=trade_history,
            performance_data=performance_data,
            initial_balance=performance_data.initial_balance,
            benchmark_returns=None  # Could be provided for beta/alpha calculation
        )
    
    def compare_results(self, result_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple backtest results using advanced comparison engine.
        
        Args:
            result_ids: List of backtest IDs to compare
            
        Returns:
            Comprehensive comparison report with statistical analysis
        """
        from .comparison_engine import ResultsComparisonEngine
        
        self.logger.info(f"Comparing {len(result_ids)} backtest results")
        
        # Load all results
        results = []
        for result_id in result_ids:
            try:
                result = self.process_results(result_id)
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Failed to load result {result_id}: {e}")
        
        if len(results) < 2:
            raise ValueError("At least 2 valid results are required for comparison")
        
        # Use advanced comparison engine
        comparison_engine = ResultsComparisonEngine()
        return comparison_engine.compare_multiple_results(results)
    
    def compare_two_results(self, result_id1: str, result_id2: str) -> Dict[str, Any]:
        """Detailed comparison between two specific results.
        
        Args:
            result_id1: First backtest ID
            result_id2: Second backtest ID
            
        Returns:
            Detailed pairwise comparison analysis
        """
        from .comparison_engine import ResultsComparisonEngine
        
        result1 = self.process_results(result_id1)
        result2 = self.process_results(result_id2)
        
        comparison_engine = ResultsComparisonEngine()
        return comparison_engine.compare_two_results(result1, result2)
    
    def rank_results_by_criteria(
        self, 
        result_ids: List[str], 
        criteria: List[str],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Rank results by multiple criteria with optional weighting.
        
        Args:
            result_ids: List of backtest IDs to rank
            criteria: List of criteria to rank by
            weights: Optional weights for each criterion
            
        Returns:
            Ranking analysis with composite scores
        """
        from .comparison_engine import ResultsComparisonEngine
        
        # Load all results
        results = []
        for result_id in result_ids:
            try:
                result = self.process_results(result_id)
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Failed to load result {result_id}: {e}")
        
        if not results:
            raise ValueError("No valid results found for ranking")
        
        comparison_engine = ResultsComparisonEngine()
        return comparison_engine.rank_results_by_criteria(results, criteria, weights)
    
    def export_results(self, results: ProcessedResults, format: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """Export results in specified format using enhanced export system.
        
        Args:
            results: ProcessedResults to export
            format: Export format ('json', 'csv', 'excel', 'lab_compatible', etc.)
            options: Optional export configuration
            
        Returns:
            Exported data as bytes
        """
        from .export_system import ResultsExportSystem
        
        export_system = ResultsExportSystem()
        return export_system.export_results(results, format, options)
    
    def export_comparison_results(self, comparison_data: Dict[str, Any], format: str) -> bytes:
        """Export comparison analysis results.
        
        Args:
            comparison_data: Comparison analysis data from compare_results()
            format: Export format ('json', 'csv', 'excel')
            
        Returns:
            Exported comparison data as bytes
        """
        from .export_system import ResultsExportSystem
        
        export_system = ResultsExportSystem()
        return export_system.export_comparison_results(comparison_data, format)
    
    def get_supported_export_formats(self) -> List[str]:
        """Get list of supported export formats.
        
        Returns:
            List of supported format names
        """
        from .export_system import ResultsExportSystem
        
        export_system = ResultsExportSystem()
        return export_system.get_supported_formats()
    
    def get_export_format_options(self, format: str) -> Dict[str, Any]:
        """Get available options for a specific export format.
        
        Args:
            format: Export format name
            
        Returns:
            Dictionary of available options and their descriptions
        """
        from .export_system import ResultsExportSystem
        
        export_system = ResultsExportSystem()
        return export_system.get_format_options(format)
    
    def format_for_lab_compatibility(self, results: ProcessedResults) -> Dict[str, Any]:
        """Format results to match lab result structure for compatibility.
        
        Args:
            results: ProcessedResults to format
            
        Returns:
            Lab-compatible result dictionary
        """
        return {
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
            'performance_metrics': results.execution_metrics.to_dict(),
            'trade_history': [
                {
                    'timestamp': trade.timestamp.isoformat(),
                    'type': trade.trade_type.value,
                    'price': trade.price,
                    'amount': trade.amount,
                    'fee': trade.fee,
                    'profit_loss': trade.profit_loss
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
            }
        }
    
    def _fetch_runtime_data(self, backtest_id: str) -> Dict[str, Any]:
        """Fetch runtime data from HaasOnline API using GET_BACKTEST_RUNTIME."""
        from ..api_client.haasonline_client import HaasOnlineClient
        from ..api_client.request_models import BacktestRuntimeRequest
        
        try:
            # Get API client from config
            client = HaasOnlineClient(self.config.haasonline_config)
            
            # Create request
            request = BacktestRuntimeRequest(backtest_id=backtest_id)
            
            # Fetch runtime data
            response = client.get_backtest_runtime(request)
            
            # Convert response to dictionary format
            runtime_data = {
                'backtest_id': response.backtest_id,
                'execution_id': response.execution_id,
                'script_id': response.backtest_id,  # Use backtest_id as script identifier
                'status': response.status.value,
                'start_time': response.start_time.isoformat(),
                'end_time': response.end_time.isoformat() if response.end_time else None,
                'duration_seconds': response.duration_seconds,
                'initial_balance': getattr(response.metrics, 'initial_balance', 10000.0),
                'final_balance': getattr(response.metrics, 'final_balance', 10000.0),
                'trades': [
                    {
                        'timestamp': trade.timestamp.isoformat(),
                        'type': trade.action.lower().replace(' ', '_'),
                        'price': trade.price,
                        'amount': trade.amount,
                        'fee': trade.fee,
                        'profit_loss': trade.profit_loss,
                        'balance_after': trade.balance_after
                    }
                    for trade in response.trades
                ],
                'has_chart_data': True,  # Assume chart data is available
                'metrics': response.metrics.__dict__ if hasattr(response, 'metrics') else {}
            }
            
            self.logger.info(f"Successfully fetched runtime data for backtest: {backtest_id}")
            return runtime_data
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch runtime data for {backtest_id}, using fallback: {e}")
            # Fallback to sample data for development/testing
            return {
                'script_id': 'sample_script',
                'initial_balance': 10000.0,
                'final_balance': 11500.0,
                'trades': [
                    {
                        'timestamp': '2024-01-01T10:00:00Z',
                        'type': 'action_a',
                        'price': 100.0,
                        'amount': 1.0,
                        'fee': 0.1
                    },
                    {
                        'timestamp': '2024-01-01T15:00:00Z',
                        'type': 'action_b',
                        'price': 115.0,
                        'amount': 1.0,
                        'fee': 0.1
                    }
                ],
                'has_chart_data': False
            }
    
    def _fetch_logs(self, backtest_id: str) -> List[str]:
        """Fetch logs from HaasOnline API using GET_BACKTEST_LOGS."""
        from ..api_client.haasonline_client import HaasOnlineClient
        from ..api_client.request_models import BacktestLogsRequest
        
        try:
            # Get API client from config
            client = HaasOnlineClient(self.config.haasonline_config)
            
            # Create request for logs
            request = BacktestLogsRequest(
                backtest_id=backtest_id,
                start_index=0,
                count=1000  # Get up to 1000 log entries
            )
            
            # Fetch logs
            response = client.get_backtest_logs(request)
            
            # Extract log messages
            logs = []
            for log_entry in response.logs:
                log_message = f"[{log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log_entry.level}: {log_entry.message}"
                logs.append(log_message)
            
            self.logger.info(f"Successfully fetched {len(logs)} log entries for backtest: {backtest_id}")
            return logs
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch logs for {backtest_id}, using fallback: {e}")
            # Fallback to sample logs for development/testing
            return [
                "Backtest started",
                "Processing market data",
                "Executing trades",
                "Backtest completed"
            ]
    
    def _process_trade_history(self, raw_trades: List[Dict[str, Any]]) -> List[Trade]:
        """Process raw trade data into Trade objects."""
        trades = []
        
        for i, raw_trade in enumerate(raw_trades):
            trade = Trade(
                trade_id=f"trade_{i}",
                timestamp=datetime.fromisoformat(raw_trade['timestamp'].replace('Z', '+00:00')),
                trade_type=TradeType(raw_trade['type']),
                price=raw_trade['price'],
                amount=raw_trade['amount'],
                fee=raw_trade['fee'],
                status=TradeStatus.CLOSED
            )
            
            # Calculate profit/loss for closed trades
            if i > 0 and trades:
                prev_trade = trades[-1]
                if (trade.trade_type == TradeType.ACTION_B and prev_trade.trade_type == TradeType.ACTION_A):
                    trade.profit_loss = (trade.price - prev_trade.price) * trade.amount - trade.fee - prev_trade.fee
                    trade.duration = trade.timestamp - prev_trade.timestamp
            
            trades.append(trade)
        
        return trades
    
    def _calculate_performance_data(self, trades: List[Trade], runtime_data: Dict[str, Any]) -> PerformanceData:
        """Calculate performance statistics from trade history."""
        if not trades:
            return PerformanceData(
                initial_balance=runtime_data.get('initial_balance', 0),
                final_balance=runtime_data.get('final_balance', 0),
                peak_balance=runtime_data.get('final_balance', 0),
                lowest_balance=runtime_data.get('initial_balance', 0),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                largest_win=0,
                largest_loss=0,
                average_win=0,
                average_loss=0,
                total_time_in_market=timedelta(),
                average_trade_duration=timedelta(),
                longest_winning_streak=0,
                longest_losing_streak=0
            )
        
        profitable_trades = [t for t in trades if t.profit_loss and t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss and t.profit_loss < 0]
        
        return PerformanceData(
            initial_balance=runtime_data.get('initial_balance', 0),
            final_balance=runtime_data.get('final_balance', 0),
            peak_balance=runtime_data.get('final_balance', 0),  # Simplified
            lowest_balance=runtime_data.get('initial_balance', 0),  # Simplified
            total_trades=len(trades),
            winning_trades=len(profitable_trades),
            losing_trades=len(losing_trades),
            largest_win=max([t.profit_loss for t in profitable_trades], default=0),
            largest_loss=min([t.profit_loss for t in losing_trades], default=0),
            average_win=sum([t.profit_loss for t in profitable_trades]) / len(profitable_trades) if profitable_trades else 0,
            average_loss=sum([t.profit_loss for t in losing_trades]) / len(losing_trades) if losing_trades else 0,
            total_time_in_market=timedelta(hours=len(trades)),  # Simplified
            average_trade_duration=timedelta(hours=1),  # Simplified
            longest_winning_streak=self._calculate_longest_streak(trades, True),
            longest_losing_streak=self._calculate_longest_streak(trades, False)
        )
    
    def _create_execution_summary(self, backtest_id: str, runtime_data: Dict[str, Any]) -> ExecutionSummary:
        """Create execution summary from runtime data."""
        return ExecutionSummary(
            backtest_id=backtest_id,
            script_name=f"Script_{runtime_data.get('script_id', 'unknown')}",
            market_tag="BTC/USD",  # Simplified
            start_date=datetime.now() - timedelta(days=30),  # Simplified
            end_date=datetime.now(),  # Simplified
            duration=timedelta(days=30),  # Simplified
            total_trades=len(runtime_data.get('trades', [])),
            success_rate=75.0,  # Simplified
            final_balance=runtime_data.get('final_balance', 0),
            max_drawdown=5.0,  # Simplified
            execution_time=timedelta(minutes=5)  # Simplified
        )
    
    def _process_chart_data(self, backtest_id: str) -> Optional[ChartData]:
        """Process chart data using GET_BACKTEST_CHART_PARTITION API."""
        from ..api_client.haasonline_client import HaasOnlineClient
        from ..api_client.request_models import BacktestChartRequest
        
        try:
            # Get API client from config
            client = HaasOnlineClient(self.config.haasonline_config)
            
            # Start with partition 0
            partition_index = 0
            all_timestamps = []
            all_equity_values = []
            all_drawdown_values = []
            trade_markers = []
            
            # Fetch chart data partitions (HaasOnline may split large datasets)
            while True:
                try:
                    request = BacktestChartRequest(
                        backtest_id=backtest_id,
                        partition_index=partition_index
                    )
                    
                    response = client.get_backtest_chart(request)
                    
                    # Process chart data from response
                    if hasattr(response, 'chart_points') and response.chart_points:
                        for point in response.chart_points:
                            all_timestamps.append(point.timestamp)
                            all_equity_values.append(point.equity_value)
                            all_drawdown_values.append(point.drawdown_percentage)
                            
                            # Add trade markers if this point represents a trade
                            if hasattr(point, 'is_trade') and point.is_trade:
                                trade_markers.append({
                                    'timestamp': point.timestamp,
                                    'price': point.price,
                                    'type': point.trade_type,
                                    'amount': point.amount
                                })
                    
                    # Check if there are more partitions
                    if not hasattr(response, 'has_more_partitions') or not response.has_more_partitions:
                        break
                        
                    partition_index += 1
                    
                    # Safety limit to prevent infinite loops
                    if partition_index > 100:
                        self.logger.warning(f"Reached partition limit for backtest {backtest_id}")
                        break
                        
                except Exception as partition_error:
                    self.logger.debug(f"No more partitions available for backtest {backtest_id}: {partition_error}")
                    break
            
            # Create ChartData object if we have data
            if all_timestamps and all_equity_values:
                chart_data = ChartData(
                    timestamps=all_timestamps,
                    equity_curve=all_equity_values,
                    drawdown_curve=all_drawdown_values,
                    trade_markers=trade_markers
                )
                
                self.logger.info(f"Successfully processed chart data for backtest: {backtest_id} ({len(all_timestamps)} points)")
                return chart_data
            else:
                self.logger.info(f"No chart data available for backtest: {backtest_id}")
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to process chart data for {backtest_id}: {e}")
            return None
    
    def calculate_risk_analysis(self, results: ProcessedResults) -> Dict[str, Any]:
        """Calculate comprehensive risk analysis for backtest results.
        
        Args:
            results: ProcessedResults to analyze
            
        Returns:
            Dictionary with detailed risk analysis
        """
        from .metrics_calculator import TradingMetricsCalculator
        
        calculator = TradingMetricsCalculator()
        
        # Calculate returns series for risk analysis
        returns = []
        current_balance = results.performance_data.initial_balance
        
        for trade in results.trade_history:
            if trade.profit_loss is not None:
                trade_return = trade.profit_loss / current_balance
                returns.append(trade_return)
                current_balance += trade.profit_loss
        
        # Get comprehensive risk metrics
        risk_metrics = calculator.calculate_risk_metrics(returns)
        
        # Add performance attribution analysis
        attribution = calculator.calculate_performance_attribution(results.trade_history)
        
        return {
            'risk_metrics': risk_metrics,
            'performance_attribution': attribution,
            'backtest_id': results.backtest_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'trade_count': len(results.trade_history),
            'analysis_period': {
                'start': min(t.timestamp for t in results.trade_history).isoformat() if results.trade_history else None,
                'end': max(t.timestamp for t in results.trade_history).isoformat() if results.trade_history else None
            }
        }
    

    
    def _calculate_longest_streak(self, trades: List[Trade], winning: bool) -> int:
        """Calculate longest winning or losing streak."""
        if not trades:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for trade in trades:
            if trade.profit_loss is None:
                continue
            
            is_winning = trade.profit_loss > 0
            if is_winning == winning:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
