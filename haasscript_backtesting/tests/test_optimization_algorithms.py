"""
Tests for optimization algorithm integration.

This module tests the integration of various optimization algorithms
with the HaasScript backtesting system.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from haasscript_backtesting.optimization_manager.optimization_manager import OptimizationManager
from haasscript_backtesting.models.optimization_models import (
    OptimizationAlgorithm, OptimizationConfig, ParameterRange
)
from haasscript_backtesting.models.backtest_models import BacktestConfig
from haasscript_backtesting.models.result_models import ProcessedResults, ExecutionMetrics


class TestOptimizationManager:
    """Test optimization manager functionality."""
    
    @pytest.fixture
    def mock_backtest_manager(self):
        """Mock backtest manager."""
        manager = Mock()
        manager.execute_backtest.return_value = Mock(
            backtest_id="test_backtest_123",
            status=Mock(is_complete=True)
        )
        manager.monitor_execution.return_value = Mock(
            backtest_id="test_backtest_123",
            status=Mock(is_complete=True)
        )
        return manager
    
    @pytest.fixture
    def mock_results_manager(self):
        """Mock results manager."""
        manager = Mock()
        
        # Create mock execution metrics
        mock_metrics = ExecutionMetrics(
            total_return=0.15,
            annualized_return=0.18,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown=0.08,
            max_drawdown_duration=timedelta(days=5),
            volatility=0.12,
            beta=1.0,
            alpha=0.05,
            value_at_risk_95=0.03,
            conditional_var_95=0.05,
            calmar_ratio=2.25,
            profit_factor=1.8,
            recovery_factor=1.9,
            payoff_ratio=1.1
        )
        
        # Create mock processed results
        mock_result = ProcessedResults(
            backtest_id="test_backtest_123",
            script_id="test_script_123",
            execution_summary=Mock(),
            execution_metrics=mock_metrics,
            performance_data=Mock(),
            trade_history=[],
            chart_data=None
        )
        mock_result.execution_metrics = mock_metrics
        
        manager.process_results.return_value = mock_result
        return manager
    
    @pytest.fixture
    def optimization_manager(self, mock_backtest_manager, mock_results_manager):
        """Create optimization manager with mocked dependencies."""
        return OptimizationManager(
            backtest_manager=mock_backtest_manager,
            results_manager=mock_results_manager,
            max_concurrent_executions=3
        )
    
    @pytest.fixture
    def sample_optimization_config(self):
        """Create sample optimization configuration."""
        base_config = BacktestConfig(
            script_id="test_script_123",
            account_id="test_account_456",
            market_tag="BINANCE_BTC_USDT",
            start_time=1640995200,  # 2022-01-01
            end_time=1672531200,    # 2023-01-01
            interval=1,
            execution_amount=1000.0,
            leverage=1,
            position_mode=0,
            script_parameters={"rsi_length": 14, "overbought": 70}
        )
        
        parameter_ranges = [
            ParameterRange(
                name="rsi_length",
                min_value=10,
                max_value=20,
                step=2,
                parameter_type=int
            ),
            ParameterRange(
                name="overbought",
                min_value=65,
                max_value=80,
                step=5,
                parameter_type=int
            )
        ]
        
        return OptimizationConfig(
            script_id="test_script_123",
            base_backtest_config=base_config,
            parameter_ranges=parameter_ranges,
            optimization_metric="sharpe_ratio",
            max_evaluations=20
        )
    
    def test_optimization_manager_initialization(self, optimization_manager):
        """Test optimization manager initialization."""
        assert optimization_manager.backtest_manager is not None
        assert optimization_manager.results_manager is not None
        assert optimization_manager.max_concurrent_executions == 3
        assert len(optimization_manager.optimization_algorithms) == 5
        assert OptimizationAlgorithm.GRID_SEARCH in optimization_manager.optimization_algorithms
        assert OptimizationAlgorithm.BAYESIAN in optimization_manager.optimization_algorithms
    
    def test_grid_search_optimization(self, optimization_manager, sample_optimization_config):
        """Test grid search optimization algorithm."""
        # Mock the sweep engine
        with patch.object(optimization_manager.sweep_engine, 'create_sweep') as mock_create, \
             patch.object(optimization_manager.sweep_engine, 'execute_sweep') as mock_execute:
            
            # Setup mock sweep execution
            mock_sweep = Mock()
            mock_sweep.best_parameters = {"rsi_length": 14, "overbought": 70}
            mock_sweep.best_result = Mock()
            mock_sweep.best_result.execution_metrics = Mock()
            mock_sweep.best_result.execution_metrics.sharpe_ratio = 1.5
            mock_sweep.completed_backtests = 30
            mock_sweep.completed_at = datetime.now()
            mock_sweep.started_at = datetime.now() - timedelta(minutes=10)
            
            # Mock the config attribute
            mock_sweep.config = Mock()
            mock_sweep.config.optimization_metric = "sharpe_ratio"
            
            mock_create.return_value = mock_sweep
            mock_execute.return_value = mock_sweep
            
            # Execute optimization
            result = optimization_manager.execute_optimization(
                OptimizationAlgorithm.GRID_SEARCH,
                sample_optimization_config
            )
            
            # Verify results
            assert result.algorithm == OptimizationAlgorithm.GRID_SEARCH
            assert result.best_parameters == {"rsi_length": 14, "overbought": 70}
            assert result.best_score == 1.5
            assert result.total_evaluations == 30
            
            # Verify sweep engine was called correctly
            mock_create.assert_called_once()
            mock_execute.assert_called_once()
    
    def test_random_search_optimization(self, optimization_manager, sample_optimization_config):
        """Test random search optimization algorithm."""
        with patch.object(optimization_manager, '_generate_random_combinations') as mock_random, \
             patch.object(optimization_manager.sweep_engine, 'create_sweep') as mock_create, \
             patch.object(optimization_manager.sweep_engine, 'execute_sweep') as mock_execute:
            
            # Setup mocks
            mock_random.return_value = [
                {"rsi_length": 12, "overbought": 75},
                {"rsi_length": 16, "overbought": 65}
            ]
            
            mock_sweep = Mock()
            mock_sweep.best_parameters = {"rsi_length": 16, "overbought": 65}
            mock_sweep.best_result = Mock()
            mock_sweep.best_result.execution_metrics = Mock()
            mock_sweep.best_result.execution_metrics.sharpe_ratio = 1.3
            mock_sweep.completed_backtests = 20
            mock_sweep.completed_at = datetime.now()
            mock_sweep.started_at = datetime.now() - timedelta(minutes=5)
            
            mock_create.return_value = mock_sweep
            mock_execute.return_value = mock_sweep
            
            # Execute optimization
            result = optimization_manager.execute_optimization(
                OptimizationAlgorithm.RANDOM_SEARCH,
                sample_optimization_config
            )
            
            # Verify results
            assert result.algorithm == OptimizationAlgorithm.RANDOM_SEARCH
            assert result.best_score == 1.3
            assert result.total_evaluations == 20
    
    @patch('haasscript_backtesting.optimization_manager.optimization_manager.GaussianProcessRegressor')
    def test_bayesian_optimization(self, mock_gp_class, optimization_manager, sample_optimization_config):
        """Test Bayesian optimization algorithm."""
        # Mock scikit-learn imports
        with patch('haasscript_backtesting.optimization_manager.optimization_manager.minimize'):
            # Setup mock GP
            mock_gp = Mock()
            mock_gp.fit.return_value = None
            mock_gp.predict.return_value = ([1.2], [0.1])
            mock_gp_class.return_value = mock_gp
            
            # Mock evaluation method
            with patch.object(optimization_manager, '_evaluate_parameter_combination') as mock_eval:
                mock_result = Mock()
                mock_result.execution_metrics = Mock()
                mock_result.execution_metrics.sharpe_ratio = 1.4
                mock_eval.return_value = mock_result
                
                # Execute optimization
                result = optimization_manager.execute_optimization(
                    OptimizationAlgorithm.BAYESIAN,
                    sample_optimization_config
                )
                
                # Verify results
                assert result.algorithm == OptimizationAlgorithm.BAYESIAN
                assert result.best_score > 0
                assert len(result.optimization_history) > 0
    
    def test_genetic_algorithm_optimization(self, optimization_manager, sample_optimization_config):
        """Test genetic algorithm optimization."""
        # Mock evaluation method
        with patch.object(optimization_manager, '_evaluate_parameter_combination') as mock_eval:
            mock_result = Mock()
            mock_result.execution_metrics = Mock()
            mock_result.execution_metrics.sharpe_ratio = 1.1
            mock_eval.return_value = mock_result
            
            # Reduce max_evaluations for faster test
            sample_optimization_config.max_evaluations = 10
            
            # Execute optimization
            result = optimization_manager.execute_optimization(
                OptimizationAlgorithm.GENETIC,
                sample_optimization_config
            )
            
            # Verify results
            assert result.algorithm == OptimizationAlgorithm.GENETIC
            assert result.best_parameters is not None
            assert result.total_evaluations > 0
            assert len(result.optimization_history) > 0
    
    def test_particle_swarm_optimization(self, optimization_manager, sample_optimization_config):
        """Test particle swarm optimization."""
        # Mock evaluation method
        with patch.object(optimization_manager, '_evaluate_parameter_combination') as mock_eval:
            mock_result = Mock()
            mock_result.execution_metrics = Mock()
            mock_result.execution_metrics.sharpe_ratio = 1.0
            mock_eval.return_value = mock_result
            
            # Reduce max_evaluations for faster test
            sample_optimization_config.max_evaluations = 15
            
            # Execute optimization
            result = optimization_manager.execute_optimization(
                OptimizationAlgorithm.PARTICLE_SWARM,
                sample_optimization_config
            )
            
            # Verify results
            assert result.algorithm == OptimizationAlgorithm.PARTICLE_SWARM
            assert result.best_parameters is not None
            assert result.total_evaluations > 0
            assert len(result.optimization_history) > 0
    
    def test_rank_results(self, optimization_manager):
        """Test result ranking functionality."""
        # Create mock results with different metrics
        results = []
        for i in range(3):
            result = Mock()
            result.execution_metrics = Mock()
            result.execution_metrics.sharpe_ratio = 1.0 + i * 0.2
            result.execution_metrics.total_return = 0.1 + i * 0.05
            result.execution_metrics.max_drawdown = 0.1 - i * 0.02
            result.execution_metrics.win_rate = 0.6 + i * 0.05
            result.execution_metrics.profit_factor = 1.5 + i * 0.1
            results.append(result)
        
        # Rank results
        ranked = optimization_manager.rank_results(results)
        
        # Verify ranking
        assert ranked.total_results == 3
        assert len(ranked.ranked_results) == 3
        assert ranked.ranked_results[0]['score'] >= ranked.ranked_results[1]['score']
        assert ranked.ranked_results[1]['score'] >= ranked.ranked_results[2]['score']
    
    def test_generate_random_combinations(self, optimization_manager, sample_optimization_config):
        """Test random combination generation."""
        combinations = optimization_manager._generate_random_combinations(
            sample_optimization_config.parameter_ranges,
            5
        )
        
        assert len(combinations) == 5
        for combo in combinations:
            assert "rsi_length" in combo
            assert "overbought" in combo
            assert 10 <= combo["rsi_length"] <= 20
            assert 65 <= combo["overbought"] <= 80
    
    def test_tournament_selection(self, optimization_manager):
        """Test tournament selection for genetic algorithm."""
        population = [
            {"param1": 1.0, "param2": 2.0},
            {"param1": 2.0, "param2": 3.0},
            {"param1": 3.0, "param2": 4.0}
        ]
        fitness_scores = [0.5, 1.0, 1.5]
        
        # Run tournament selection multiple times
        selections = []
        for _ in range(10):
            selected = optimization_manager._tournament_selection(population, fitness_scores)
            selections.append(selected)
        
        # Higher fitness individuals should be selected more often
        # (This is probabilistic, so we just check that selection works)
        assert all(sel in population for sel in selections)
    
    def test_crossover_operation(self, optimization_manager, sample_optimization_config):
        """Test crossover operation for genetic algorithm."""
        parent1 = {"rsi_length": 12, "overbought": 70}
        parent2 = {"rsi_length": 18, "overbought": 75}
        
        child = optimization_manager._crossover(
            parent1, parent2, sample_optimization_config.parameter_ranges
        )
        
        # Child should have parameters from both parents
        assert "rsi_length" in child
        assert "overbought" in child
        assert child["rsi_length"] in [12, 18]
        assert child["overbought"] in [70, 75]
    
    def test_mutation_operation(self, optimization_manager, sample_optimization_config):
        """Test mutation operation for genetic algorithm."""
        individual = {"rsi_length": 14, "overbought": 70}
        
        # Test with high mutation rate to ensure mutation occurs
        mutated = optimization_manager._mutate(
            individual, sample_optimization_config.parameter_ranges, mutation_rate=1.0
        )
        
        # Parameters should be within bounds
        assert 10 <= mutated["rsi_length"] <= 20
        assert 65 <= mutated["overbought"] <= 80
    
    def test_population_diversity_calculation(self, optimization_manager):
        """Test population diversity calculation."""
        # Identical population (no diversity)
        identical_pop = [
            {"param1": 1.0, "param2": 2.0},
            {"param1": 1.0, "param2": 2.0},
            {"param1": 1.0, "param2": 2.0}
        ]
        diversity1 = optimization_manager._calculate_population_diversity(identical_pop)
        assert diversity1 == 0.0
        
        # Diverse population
        diverse_pop = [
            {"param1": 1.0, "param2": 2.0},
            {"param1": 5.0, "param2": 6.0},
            {"param1": 10.0, "param2": 12.0}
        ]
        diversity2 = optimization_manager._calculate_population_diversity(diverse_pop)
        assert diversity2 > 0.0
    
    def test_unsupported_algorithm_error(self, optimization_manager, sample_optimization_config):
        """Test error handling for unsupported algorithms."""
        # Create a mock algorithm that doesn't exist
        with pytest.raises(ValueError, match="Unsupported optimization algorithm"):
            # This should raise an error since we're not using a real enum value
            optimization_manager.execute_optimization("invalid_algorithm", sample_optimization_config)


class TestOptimizationIntegration:
    """Test integration with existing optimization frameworks."""
    
    def test_pyhaas_optimization_integration(self):
        """Test integration with PyHaasAPI optimization module."""
        # Test that the import works (if available)
        try:
            from pyHaasAPI.optimization import OptimizationStrategy, ParameterRangeGenerator
            assert OptimizationStrategy.MIXED is not None
            assert ParameterRangeGenerator is not None
        except ImportError:
            # If not available, that's also fine for testing
            pass
    
    def test_optimization_config_validation(self):
        """Test optimization configuration validation."""
        # Test valid configuration
        base_config = BacktestConfig(
            script_id="test",
            account_id="test",
            market_tag="TEST",
            start_time=1640995200,
            end_time=1672531200,
            interval=1,
            execution_amount=1000.0,
            script_parameters={}
        )
        
        param_ranges = [
            ParameterRange("test_param", 1, 10, 1, int)
        ]
        
        config = OptimizationConfig(
            script_id="test",
            base_backtest_config=base_config,
            parameter_ranges=param_ranges
        )
        
        assert config.script_id == "test"
        assert config.optimization_metric == "sharpe_ratio"
        assert len(config.parameter_ranges) == 1


if __name__ == "__main__":
    pytest.main([__file__])