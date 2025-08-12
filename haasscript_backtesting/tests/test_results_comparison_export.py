"""
Tests for results comparison and export functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ..results_manager.results_manager import ResultsManager
from ..results_manager.comparison_engine import ResultsComparisonEngine
from ..results_manager.export_system import ResultsExportSystem
from ..models import (
    ProcessedResults, ExecutionSummary, ExecutionMetrics, PerformanceData,
    Trade, TradeType, TradeStatus
)
from ..config import ConfigManager


class TestResultsComparison:
    """Test cases for results comparison functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.comparison_engine = ResultsComparisonEngine()
        
        # Create sample results for comparison
        self.results1 = self._create_sample_result("test_1", 15.5, 1.2, 8.5)
        self.results2 = self._create_sample_result("test_2", 12.3, 0.9, 12.1)
        self.results3 = self._create_sample_result("test_3", 18.7, 1.5, 6.2)
    
    def _create_sample_result(self, backtest_id: str, total_return: float, sharpe: float, drawdown: float) -> ProcessedResults:
        """Create a sample ProcessedResults for testing."""
        # Create sample trades
        trades = [
            Trade(
                trade_id=f"{backtest_id}_trade_1",
                timestamp=datetime(2024, 1, 1, 10, 0),
                trade_type=TradeType.ACTION_A,
                price=100.0,
                amount=1.0,
                fee=0.1,
                status=TradeStatus.CLOSED,
                profit_loss=50.0,
                duration=timedelta(hours=2)
            ),
            Trade(
                trade_id=f"{backtest_id}_trade_2",
                timestamp=datetime(2024, 1, 1, 14, 0),
                trade_type=TradeType.ACTION_B,
                price=150.0,
                amount=1.0,
                fee=0.1,
                status=TradeStatus.CLOSED,
                profit_loss=-20.0,
                duration=timedelta(hours=1)
            )
        ]
        
        # Create execution metrics
        metrics = ExecutionMetrics(
            total_return=total_return,
            annualized_return=total_return * 1.2,
            sharpe_ratio=sharpe,
            sortino_ratio=sharpe * 1.1,
            max_drawdown=drawdown,
            max_drawdown_duration=timedelta(days=2),
            volatility=15.0,
            beta=0.8,
            alpha=2.5,
            value_at_risk_95=-0.05,
            conditional_var_95=-0.08,
            calmar_ratio=total_return / drawdown if drawdown > 0 else 0,
            profit_factor=1.5,
            recovery_factor=total_return / drawdown if drawdown > 0 else 0,
            payoff_ratio=2.5
        )
        
        # Create performance data
        performance = PerformanceData(
            initial_balance=10000.0,
            final_balance=10000.0 + (total_return / 100 * 10000.0),
            peak_balance=11000.0,
            lowest_balance=9500.0,
            total_trades=len(trades),
            winning_trades=1,
            losing_trades=1,
            largest_win=50.0,
            largest_loss=-20.0,
            average_win=50.0,
            average_loss=-20.0,
            total_time_in_market=timedelta(hours=3),
            average_trade_duration=timedelta(hours=1.5),
            longest_winning_streak=1,
            longest_losing_streak=1
        )
        
        # Create execution summary
        summary = ExecutionSummary(
            backtest_id=backtest_id,
            script_name=f"Script_{backtest_id}",
            market_tag="BTC/USD",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            duration=timedelta(days=30),
            total_trades=len(trades),
            success_rate=50.0,
            final_balance=performance.final_balance,
            max_drawdown=drawdown,
            execution_time=timedelta(minutes=5)
        )
        
        return ProcessedResults(
            backtest_id=backtest_id,
            script_id=f"script_{backtest_id}",
            execution_summary=summary,
            execution_metrics=metrics,
            performance_data=performance,
            trade_history=trades
        )
    
    def test_compare_multiple_results(self):
        """Test comprehensive comparison of multiple results."""
        results_list = [self.results1, self.results2, self.results3]
        
        comparison = self.comparison_engine.compare_multiple_results(results_list)
        
        # Verify structure
        assert 'summary' in comparison
        assert 'basic_comparison' in comparison
        assert 'statistical_analysis' in comparison
        assert 'risk_adjusted_rankings' in comparison
        assert 'consistency_analysis' in comparison
        assert 'correlation_analysis' in comparison
        assert 'recommendations' in comparison
        
        # Verify summary
        assert comparison['summary']['total_results'] == 3
        
        # Verify basic comparison has key metrics
        basic_comp = comparison['basic_comparison']
        assert 'metrics_comparison' in basic_comp
        assert 'best_performers' in basic_comp
        
        # Check that key metrics are compared
        metrics_comp = basic_comp['metrics_comparison']
        expected_metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        for metric in expected_metrics:
            assert metric in metrics_comp
            assert 'best' in metrics_comp[metric]
            assert 'worst' in metrics_comp[metric]
            assert 'mean' in metrics_comp[metric]
    
    def test_compare_two_results(self):
        """Test detailed pairwise comparison."""
        comparison = self.comparison_engine.compare_two_results(self.results1, self.results2)
        
        # Verify structure
        assert 'comparison_pair' in comparison
        assert 'performance_differences' in comparison
        assert 'statistical_significance' in comparison
        assert 'risk_comparison' in comparison
        assert 'trade_pattern_comparison' in comparison
        assert 'winner' in comparison
        
        # Verify comparison pair info
        pair_info = comparison['comparison_pair']
        assert pair_info['result1_id'] == 'test_1'
        assert pair_info['result2_id'] == 'test_2'
        
        # Verify performance differences
        perf_diff = comparison['performance_differences']
        assert 'total_return_diff' in perf_diff
        assert 'sharpe_ratio_diff' in perf_diff
        
        # Verify winner determination
        winner = comparison['winner']
        assert 'winner' in winner
        assert 'score1' in winner
        assert 'score2' in winner
    
    def test_rank_results_by_criteria(self):
        """Test ranking results by multiple criteria."""
        results_list = [self.results1, self.results2, self.results3]
        criteria = ['total_return', 'sharpe_ratio', 'max_drawdown']
        weights = {'total_return': 0.4, 'sharpe_ratio': 0.4, 'max_drawdown': 0.2}
        
        ranking = self.comparison_engine.rank_results_by_criteria(results_list, criteria, weights)
        
        # Verify structure
        assert 'criteria' in ranking
        assert 'weights' in ranking
        assert 'criterion_scores' in ranking
        assert 'composite_scores' in ranking
        assert 'rankings' in ranking
        
        # Verify criteria and weights
        assert ranking['criteria'] == criteria
        assert ranking['weights'] == weights
        
        # Verify composite scores are sorted
        composite_scores = ranking['composite_scores']
        assert len(composite_scores) == 3
        
        # Scores should be in descending order
        for i in range(len(composite_scores) - 1):
            assert composite_scores[i]['composite_score'] >= composite_scores[i + 1]['composite_score']
    
    def test_statistical_analysis(self):
        """Test statistical analysis functionality."""
        results_list = [self.results1, self.results2, self.results3]
        
        statistical_analysis = self.comparison_engine._perform_statistical_analysis(results_list)
        
        # Verify structure
        assert 'normality_tests' in statistical_analysis
        assert 'pairwise_tests' in statistical_analysis
        assert 'anova_test' in statistical_analysis
        assert 'sample_sizes' in statistical_analysis
        
        # Verify sample sizes
        assert len(statistical_analysis['sample_sizes']) == 3
    
    def test_consistency_analysis(self):
        """Test consistency analysis."""
        results_list = [self.results1, self.results2, self.results3]
        
        consistency = self.comparison_engine._analyze_consistency(results_list)
        
        # Verify structure
        assert 'individual_consistency' in consistency
        assert 'consistency_ranking' in consistency
        assert 'methodology' in consistency
        
        # Verify individual consistency metrics
        individual = consistency['individual_consistency']
        for result in results_list:
            if result.backtest_id in individual:
                metrics = individual[result.backtest_id]
                assert 'return_consistency' in metrics
                assert 'streak_analysis' in metrics
                assert 'drawdown_consistency' in metrics
    
    def test_correlation_analysis(self):
        """Test correlation analysis."""
        results_list = [self.results1, self.results2, self.results3]
        
        correlation = self.comparison_engine._calculate_correlations(results_list)
        
        # Verify structure
        assert 'pairwise_correlations' in correlation
        assert 'average_correlation' in correlation
        assert 'interpretation' in correlation
        
        # Verify average correlation is a number
        assert isinstance(correlation['average_correlation'], float)
    
    def test_empty_results_handling(self):
        """Test handling of empty results list."""
        with pytest.raises(ValueError, match="At least 2 results are required"):
            self.comparison_engine.compare_multiple_results([])
        
        with pytest.raises(ValueError, match="At least 2 results are required"):
            self.comparison_engine.compare_multiple_results([self.results1])
    
    def test_recommendations_generation(self):
        """Test recommendations generation."""
        results_list = [self.results1, self.results2, self.results3]
        risk_rankings = {'composite_risk_scores': [
            {'backtest_id': 'test_3', 'composite_score': 1.5},
            {'backtest_id': 'test_1', 'composite_score': 1.2},
            {'backtest_id': 'test_2', 'composite_score': 0.9}
        ]}
        
        recommendations = self.comparison_engine._generate_recommendations(results_list, risk_rankings)
        
        # Should generate at least one recommendation
        assert len(recommendations) > 0
        assert isinstance(recommendations[0], str)


class TestResultsExport:
    """Test cases for results export functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.export_system = ResultsExportSystem()
        self.sample_result = self._create_sample_result()
    
    def _create_sample_result(self) -> ProcessedResults:
        """Create a sample ProcessedResults for testing."""
        # Create sample trades
        trades = [
            Trade(
                trade_id="trade_1",
                timestamp=datetime(2024, 1, 1, 10, 0),
                trade_type=TradeType.ACTION_A,
                price=100.0,
                amount=1.0,
                fee=0.1,
                status=TradeStatus.CLOSED,
                profit_loss=50.0,
                duration=timedelta(hours=2)
            )
        ]
        
        # Create execution metrics
        metrics = ExecutionMetrics(
            total_return=15.5,
            annualized_return=18.6,
            sharpe_ratio=1.2,
            sortino_ratio=1.32,
            max_drawdown=8.5,
            max_drawdown_duration=timedelta(days=2),
            volatility=15.0,
            beta=0.8,
            alpha=2.5,
            value_at_risk_95=-0.05,
            conditional_var_95=-0.08,
            calmar_ratio=1.82,
            profit_factor=1.5,
            recovery_factor=1.82,
            payoff_ratio=2.5
        )
        
        # Create performance data
        performance = PerformanceData(
            initial_balance=10000.0,
            final_balance=11550.0,
            peak_balance=11000.0,
            lowest_balance=9500.0,
            total_trades=1,
            winning_trades=1,
            losing_trades=0,
            largest_win=50.0,
            largest_loss=0.0,
            average_win=50.0,
            average_loss=0.0,
            total_time_in_market=timedelta(hours=2),
            average_trade_duration=timedelta(hours=2),
            longest_winning_streak=1,
            longest_losing_streak=0
        )
        
        # Create execution summary
        summary = ExecutionSummary(
            backtest_id="test_export",
            script_name="Test Script",
            market_tag="BTC/USD",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            duration=timedelta(days=30),
            total_trades=1,
            success_rate=100.0,
            final_balance=11550.0,
            max_drawdown=8.5,
            execution_time=timedelta(minutes=5)
        )
        
        return ProcessedResults(
            backtest_id="test_export",
            script_id="script_test",
            execution_summary=summary,
            execution_metrics=metrics,
            performance_data=performance,
            trade_history=trades
        )
    
    def test_export_json_detailed(self):
        """Test detailed JSON export."""
        result = self.export_system.export_results(self.sample_result, 'json')
        
        # Should return bytes
        assert isinstance(result, bytes)
        
        # Should be valid JSON
        data = json.loads(result.decode('utf-8'))
        
        # Verify structure
        assert 'metadata' in data
        assert 'execution_summary' in data
        assert 'performance_metrics' in data
        assert 'performance_data' in data
        assert 'trade_history' in data
        assert 'trade_summary' in data
        
        # Verify metadata
        metadata = data['metadata']
        assert metadata['backtest_id'] == 'test_export'
        assert metadata['export_format'] == 'json_detailed'
    
    def test_export_json_summary(self):
        """Test summary JSON export."""
        result = self.export_system.export_results(self.sample_result, 'json_summary')
        
        # Should return bytes
        assert isinstance(result, bytes)
        
        # Should be valid JSON
        data = json.loads(result.decode('utf-8'))
        
        # Verify structure
        assert 'backtest_id' in data
        assert 'summary' in data
        assert 'key_metrics' in data
        
        # Verify key metrics structure
        key_metrics = data['key_metrics']
        assert 'risk_adjusted' in key_metrics
        assert 'risk_metrics' in key_metrics
        assert 'performance' in key_metrics
    
    def test_export_csv_trades(self):
        """Test CSV export for trades."""
        result = self.export_system.export_results(
            self.sample_result, 
            'csv', 
            {'csv_type': 'trades'}
        )
        
        # Should return bytes
        assert isinstance(result, bytes)
        
        # Should contain CSV headers
        csv_content = result.decode('utf-8')
        assert 'Trade ID' in csv_content
        assert 'Timestamp' in csv_content
        assert 'Type' in csv_content
        assert 'Price' in csv_content
    
    def test_export_csv_metrics(self):
        """Test CSV export for metrics."""
        result = self.export_system.export_results(
            self.sample_result, 
            'csv', 
            {'csv_type': 'metrics'}
        )
        
        # Should return bytes
        assert isinstance(result, bytes)
        
        # Should contain metrics
        csv_content = result.decode('utf-8')
        assert 'Metric' in csv_content
        assert 'Value' in csv_content
        assert 'Total Return' in csv_content
    
    def test_export_lab_compatible(self):
        """Test lab-compatible export format."""
        result = self.export_system.export_results(self.sample_result, 'lab_compatible')
        
        # Should return bytes
        assert isinstance(result, bytes)
        
        # Should be valid JSON
        data = json.loads(result.decode('utf-8'))
        
        # Verify lab-compatible structure
        assert 'backtest_id' in data
        assert 'execution_summary' in data
        assert 'performance_metrics' in data
        assert 'trade_history' in data
        assert 'performance_data' in data
        assert 'export_metadata' in data
        
        # Verify export metadata
        metadata = data['export_metadata']
        assert metadata['compatible_with'] == 'lab_system'
        assert 'format_version' in metadata
    
    def test_export_database_format(self):
        """Test database-friendly export format."""
        result = self.export_system.export_results(self.sample_result, 'database')
        
        # Should return bytes
        assert isinstance(result, bytes)
        
        # Should be valid JSON
        data = json.loads(result.decode('utf-8'))
        
        # Verify database structure
        assert 'backtest_execution' in data
        assert 'execution_metrics' in data
        assert 'performance_data' in data
        assert 'trades' in data
        
        # Verify each table has required fields
        execution = data['backtest_execution']
        assert 'id' in execution
        assert 'created_at' in execution
        
        metrics = data['execution_metrics']
        assert 'backtest_id' in metrics
        assert 'created_at' in metrics
    
    def test_export_comparison_results(self):
        """Test export of comparison results."""
        comparison_data = {
            'summary': {
                'total_results': 2,
                'comparison_date': datetime.now().isoformat()
            },
            'basic_comparison': {
                'metrics_comparison': {
                    'total_return': {
                        'best': 15.5,
                        'worst': 12.3,
                        'mean': 13.9,
                        'std_dev': 2.26
                    }
                }
            }
        }
        
        result = self.export_system.export_comparison_results(comparison_data, 'json')
        
        # Should return bytes
        assert isinstance(result, bytes)
        
        # Should be valid JSON
        data = json.loads(result.decode('utf-8'))
        assert 'summary' in data
        assert 'basic_comparison' in data
    
    def test_get_supported_formats(self):
        """Test getting supported export formats."""
        formats = self.export_system.get_supported_formats()
        
        # Should return list of strings
        assert isinstance(formats, list)
        assert len(formats) > 0
        
        # Should include expected formats
        expected_formats = ['json', 'csv', 'excel', 'lab_compatible', 'database']
        for fmt in expected_formats:
            assert fmt in formats
    
    def test_get_format_options(self):
        """Test getting format-specific options."""
        json_options = self.export_system.get_format_options('json')
        
        # Should return dictionary
        assert isinstance(json_options, dict)
        
        # Should have expected options
        assert 'include_raw_data' in json_options
    
    def test_unsupported_format_error(self):
        """Test error handling for unsupported formats."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            self.export_system.export_results(self.sample_result, 'unsupported_format')


class TestResultsManagerIntegration:
    """Test integration of comparison and export in ResultsManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock config manager
        self.mock_config = Mock(spec=ConfigManager)
        self.results_manager = ResultsManager(self.mock_config)
    
    def test_compare_results_integration(self):
        """Test integration of comparison engine in results manager."""
        # Mock process_results to return sample data
        with patch.object(self.results_manager, 'process_results') as mock_process:
            mock_process.return_value = Mock()
            
            # Mock the comparison engine import and usage
            with patch('haasscript_backtesting.results_manager.comparison_engine.ResultsComparisonEngine') as mock_comparison_engine:
                mock_engine = Mock()
                mock_comparison_engine.return_value = mock_engine
                mock_engine.compare_multiple_results.return_value = {'test': 'comparison'}
                
                result = self.results_manager.compare_results(['test1', 'test2'])
                
                # Verify comparison engine was used
                mock_comparison_engine.assert_called_once()
                mock_engine.compare_multiple_results.assert_called_once()
                assert result == {'test': 'comparison'}
    
    def test_export_results_integration(self):
        """Test integration of export system in results manager."""
        # Create mock result
        mock_result = Mock()
        
        # Mock the export system import and usage
        with patch('haasscript_backtesting.results_manager.export_system.ResultsExportSystem') as mock_export_system:
            mock_system = Mock()
            mock_export_system.return_value = mock_system
            mock_system.export_results.return_value = b'test export data'
            
            result = self.results_manager.export_results(mock_result, 'json')
            
            # Verify export system was used
            mock_export_system.assert_called_once()
            mock_system.export_results.assert_called_once_with(mock_result, 'json', None)
            assert result == b'test export data'
    
    def test_get_supported_export_formats(self):
        """Test getting supported export formats through results manager."""
        with patch('haasscript_backtesting.results_manager.export_system.ResultsExportSystem') as mock_export_system:
            mock_system = Mock()
            mock_export_system.return_value = mock_system
            mock_system.get_supported_formats.return_value = ['json', 'csv']
            
            formats = self.results_manager.get_supported_export_formats()
            
            assert formats == ['json', 'csv']
            mock_system.get_supported_formats.assert_called_once()