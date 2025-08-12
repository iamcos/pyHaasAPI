"""
Tests for parameter sweep execution engine.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from haasscript_backtesting.models.optimization_models import (
    SweepConfig, SweepExecution, SweepStatus, ParameterRange
)
from haasscript_backtesting.models.backtest_models import BacktestConfig, BacktestExecution, ExecutionStatus, ExecutionStatusType
from haasscript_backtesting.models.result_models import ProcessedResults, ExecutionMetrics
from haasscript_backtesting.models.common_models import ResourceUsage
from haasscript_backtesting.optimization_manager.parameter_sweep_engine import ParameterSweepEngine


@pytest.fixture
def mock_backtest_manager():
    """Mock backtest manager for testing."""
    manager = Mock()
    
    # Mock execution status
    mock_status = ExecutionStatus(
        status=ExecutionStatusType.COMPLETED,
        progress_percentage=100.0,
        current_phase="completed",
        estimated_completion=None,
        resource_usage=ResourceUsage(
            cpu_percent=50.0,
            memory_mb=512.0,
            disk_io_mb=10.0,
            network_io_mb=5.0,
            active_connections=2
        )
    )
    
    # Mock backtest execution
    mock_execution = BacktestExecution(
        backtest_id="test-backtest-1",
        script_id="test-script",
        config=Mock(),
        status=mock_status,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        error_message=None
    )
    
    manager.execute_backtest.return_value = mock_execution
    manager.monitor_execution.return_value = mock_execution
    
    return manager


@pytest.fixture
def mock_results_manager():
    """Mock results manager for testing."""
    manager = Mock()
    
    # Mock processed results
    mock_metrics = ExecutionMetrics(
        total_return=0.15,
        annualized_return=0.18,
        sharpe_ratio=1.5,
        sortino_ratio=1.8,
        max_drawdown=0.05,
        max_drawdown_duration=timedelta(days=10),
        volatility=0.12,
        beta=1.0,
        alpha=0.05,
        value_at_risk_95=0.02,
        conditional_var_95=0.03,
        calmar_ratio=3.0,
        profit_factor=1.8,
        recovery_factor=2.5,
        payoff_ratio=1.2
    )
    
    mock_results = ProcessedResults(
        backtest_id="test-backtest-1",
        script_id="test-script",
        execution_summary=Mock(),
        execution_metrics=mock_metrics,
        performance_data=Mock(),
        trade_history=[],
        chart_data=None
    )
    
    manager.process_results.return_value = mock_results
    
    return manager


@pytest.fixture
def parameter_ranges():
    """Sample parameter ranges for testing."""
    return [
        ParameterRange(
            name="rsi_period",
            min_value=10,
            max_value=20,
            step=5,
            parameter_type=int
        ),
        ParameterRange(
            name="ma_period", 
            min_value=20,
            max_value=30,
            step=10,
            parameter_type=int
        )
    ]


@pytest.fixture
def base_config():
    """Base backtest configuration for testing."""
    return BacktestConfig(
        script_id="test-script",
        account_id="test-account",
        market_tag="BTCUSDT",
        start_time=1640995200,  # 2022-01-01
        end_time=1672531200,    # 2023-01-01
        interval=60,            # 1 hour in minutes
        execution_amount=1000.0,
        script_parameters={"base_param": 100},
        leverage=0
    )


@pytest.fixture
def sweep_config(base_config, parameter_ranges):
    """Sample sweep configuration for testing."""
    return SweepConfig(
        name="test-sweep",
        base_config=base_config,
        parameter_ranges=parameter_ranges,
        optimization_metric="sharpe_ratio",
        max_concurrent_executions=2
    )


@pytest.fixture
def sweep_engine(mock_backtest_manager, mock_results_manager):
    """Parameter sweep engine for testing."""
    return ParameterSweepEngine(
        backtest_manager=mock_backtest_manager,
        results_manager=mock_results_manager,
        max_concurrent_executions=2
    )


class TestParameterRange:
    """Test parameter range functionality."""
    
    def test_generate_values(self):
        """Test parameter value generation."""
        param_range = ParameterRange(
            name="test_param",
            min_value=10,
            max_value=20,
            step=5,
            parameter_type=int
        )
        
        values = param_range.generate_values()
        assert values == [10, 15, 20]
    
    def test_total_combinations(self):
        """Test total combinations calculation."""
        param_range = ParameterRange(
            name="test_param",
            min_value=10,
            max_value=15,
            step=2,
            parameter_type=int
        )
        
        assert param_range.total_combinations == 3  # 10, 12, 14


class TestSweepConfig:
    """Test sweep configuration functionality."""
    
    def test_total_combinations(self, sweep_config):
        """Test total combinations calculation."""
        # rsi_period: 3 values (10, 15, 20)
        # ma_period: 2 values (20, 30)
        # Total: 3 * 2 = 6
        assert sweep_config.total_combinations == 6
    
    def test_generate_parameter_sets(self, sweep_config):
        """Test parameter set generation."""
        parameter_sets = sweep_config.generate_parameter_sets()
        
        assert len(parameter_sets) == 6
        
        # Check first combination
        assert parameter_sets[0] == {"rsi_period": 10, "ma_period": 20}
        
        # Check last combination
        assert parameter_sets[-1] == {"rsi_period": 20, "ma_period": 30}
    
    def test_empty_parameter_ranges(self):
        """Test with empty parameter ranges."""
        base_config = BacktestConfig(
            script_id="test-script",
            account_id="test-account",
            market_tag="BTCUSDT",
            start_time=1640995200,
            end_time=1672531200,
            interval=60,
            execution_amount=1000.0,
            script_parameters={"base_param": 100}
        )
        
        config = SweepConfig(
            name="empty-test",
            base_config=base_config,
            parameter_ranges=[],
            optimization_metric="sharpe_ratio"
        )
        
        assert config.total_combinations == 1
        assert config.generate_parameter_sets() == [{}]


class TestParameterSweepEngine:
    """Test parameter sweep engine functionality."""
    
    def test_validate_parameter_ranges_valid(self, sweep_engine, parameter_ranges):
        """Test validation of valid parameter ranges."""
        errors = sweep_engine.validate_parameter_ranges(parameter_ranges)
        assert errors == []
    
    def test_validate_parameter_ranges_invalid_range(self, sweep_engine):
        """Test validation with invalid range."""
        invalid_range = ParameterRange(
            name="invalid",
            min_value=20,
            max_value=10,  # max < min
            step=5,
            parameter_type=int
        )
        
        errors = sweep_engine.validate_parameter_ranges([invalid_range])
        assert len(errors) == 1
        assert "min_value must be less than max_value" in errors[0]
    
    def test_validate_parameter_ranges_invalid_step(self, sweep_engine):
        """Test validation with invalid step."""
        invalid_range = ParameterRange(
            name="invalid",
            min_value=10,
            max_value=20,
            step=0,  # Invalid step
            parameter_type=int
        )
        
        errors = sweep_engine.validate_parameter_ranges([invalid_range])
        assert len(errors) == 1
        assert "step must be positive" in errors[0]
    
    def test_validate_parameter_ranges_too_many_combinations(self, sweep_engine):
        """Test validation with too many combinations."""
        large_range = ParameterRange(
            name="large",
            min_value=1,
            max_value=2000,
            step=1,
            parameter_type=int
        )
        
        errors = sweep_engine.validate_parameter_ranges([large_range])
        assert len(errors) == 1
        assert "generates" in errors[0] and "values" in errors[0]
    
    def test_create_sweep_valid(self, sweep_engine, sweep_config):
        """Test creating a valid sweep."""
        sweep_execution = sweep_engine.create_sweep(sweep_config)
        
        assert sweep_execution.sweep_id is not None
        assert sweep_execution.config == sweep_config
        assert sweep_execution.status == SweepStatus.PENDING
        assert sweep_execution.total_backtests == 6
        assert sweep_execution.sweep_id in sweep_engine.active_sweeps
    
    def test_create_sweep_invalid(self, sweep_engine):
        """Test creating sweep with invalid parameters."""
        base_config = BacktestConfig(
            script_id="test-script",
            account_id="test-account",
            market_tag="BTCUSDT",
            start_time=1640995200,
            end_time=1672531200,
            interval=60,
            execution_amount=1000.0,
            script_parameters={"base_param": 100}
        )
        
        invalid_range = ParameterRange(
            name="invalid",
            min_value=20,
            max_value=10,
            step=5,
            parameter_type=int
        )
        
        invalid_config = SweepConfig(
            name="invalid-sweep",
            base_config=base_config,
            parameter_ranges=[invalid_range],
            optimization_metric="sharpe_ratio"
        )
        
        with pytest.raises(ValueError):
            sweep_engine.create_sweep(invalid_config)
    
    def test_add_progress_callback(self, sweep_engine, sweep_config):
        """Test adding progress callbacks."""
        sweep_execution = sweep_engine.create_sweep(sweep_config)
        
        callback = Mock()
        sweep_engine.add_progress_callback(sweep_execution.sweep_id, callback)
        
        assert len(sweep_engine.progress_callbacks[sweep_execution.sweep_id]) == 1
    
    def test_create_backtest_config(self, sweep_engine):
        """Test creating backtest config with parameter overrides."""
        base_config = BacktestConfig(
            script_id="test-script",
            account_id="test-account",
            market_tag="BTCUSDT",
            start_time=1640995200,
            end_time=1672531200,
            interval=60,
            execution_amount=1000.0,
            script_parameters={"base_param": 100}
        )
        
        parameters = {"rsi_period": 15, "ma_period": 25}
        
        new_config = sweep_engine._create_backtest_config(base_config, parameters)
        
        assert new_config.script_id == base_config.script_id
        assert new_config.script_parameters["base_param"] == 100  # Original param
        assert new_config.script_parameters["rsi_period"] == 15   # Override
        assert new_config.script_parameters["ma_period"] == 25    # Override
    
    def test_get_sweep_status(self, sweep_engine, sweep_config):
        """Test getting sweep status."""
        sweep_execution = sweep_engine.create_sweep(sweep_config)
        
        status = sweep_engine.get_sweep_status(sweep_execution.sweep_id)
        assert status == sweep_execution
        
        # Test non-existent sweep
        status = sweep_engine.get_sweep_status("non-existent")
        assert status is None
    
    def test_cancel_sweep(self, sweep_engine, sweep_config):
        """Test cancelling a sweep."""
        sweep_execution = sweep_engine.create_sweep(sweep_config)
        sweep_execution.status = SweepStatus.RUNNING
        
        result = sweep_engine.cancel_sweep(sweep_execution.sweep_id)
        assert result is True
        assert sweep_execution.status == SweepStatus.CANCELLED
        
        # Test cancelling non-existent sweep
        result = sweep_engine.cancel_sweep("non-existent")
        assert result is False
    
    def test_cleanup_completed_sweeps(self, sweep_engine, sweep_config):
        """Test cleaning up old completed sweeps."""
        # Create completed sweep
        sweep_execution = sweep_engine.create_sweep(sweep_config)
        sweep_execution.status = SweepStatus.COMPLETED
        sweep_execution.completed_at = datetime.now() - timedelta(hours=25)
        
        # Create recent sweep
        recent_sweep = sweep_engine.create_sweep(sweep_config)
        recent_sweep.status = SweepStatus.COMPLETED
        recent_sweep.completed_at = datetime.now() - timedelta(hours=1)
        
        initial_count = len(sweep_engine.active_sweeps)
        cleaned_count = sweep_engine.cleanup_completed_sweeps(max_age_hours=24)
        
        assert cleaned_count == 1
        assert len(sweep_engine.active_sweeps) == initial_count - 1
        assert recent_sweep.sweep_id in sweep_engine.active_sweeps
        assert sweep_execution.sweep_id not in sweep_engine.active_sweeps


class TestSweepExecution:
    """Test sweep execution functionality."""
    
    def test_progress_percentage(self, sweep_config):
        """Test progress percentage calculation."""
        sweep_execution = SweepExecution(
            sweep_id="test",
            config=sweep_config,
            status=SweepStatus.RUNNING,
            started_at=datetime.now(),
            total_backtests=10,
            completed_backtests=3
        )
        
        assert sweep_execution.progress_percentage == 30.0
    
    def test_is_complete(self, sweep_config):
        """Test completion check."""
        sweep_execution = SweepExecution(
            sweep_id="test",
            config=sweep_config,
            status=SweepStatus.RUNNING,
            started_at=datetime.now()
        )
        
        assert not sweep_execution.is_complete
        
        sweep_execution.status = SweepStatus.COMPLETED
        assert sweep_execution.is_complete
    
    def test_update_best_result(self, sweep_config):
        """Test updating best result."""
        sweep_execution = SweepExecution(
            sweep_id="test",
            config=sweep_config,
            status=SweepStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # First result
        metrics1 = ExecutionMetrics(
            total_return=0.10,
            annualized_return=0.12,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=0.05,
            max_drawdown_duration=timedelta(days=5),
            volatility=0.10,
            beta=1.0,
            alpha=0.02,
            value_at_risk_95=0.015,
            conditional_var_95=0.025,
            calmar_ratio=2.0,
            profit_factor=1.5,
            recovery_factor=2.0,
            payoff_ratio=1.0
        )
        result1 = ProcessedResults(
            backtest_id="test-1",
            script_id="test-script",
            execution_summary=Mock(),
            execution_metrics=metrics1,
            performance_data=Mock(),
            trade_history=[],
            chart_data=None
        )
        
        sweep_execution.update_best_result(result1, {"param": 1})
        assert sweep_execution.best_result == result1
        assert sweep_execution.best_parameters == {"param": 1}
        
        # Better result
        metrics2 = ExecutionMetrics(
            total_return=0.15,
            annualized_return=0.18,
            sharpe_ratio=1.5,  # Better Sharpe ratio
            sortino_ratio=1.8,
            max_drawdown=0.03,
            max_drawdown_duration=timedelta(days=3),
            volatility=0.08,
            beta=1.0,
            alpha=0.05,
            value_at_risk_95=0.012,
            conditional_var_95=0.020,
            calmar_ratio=5.0,
            profit_factor=2.0,
            recovery_factor=3.0,
            payoff_ratio=1.5
        )
        result2 = ProcessedResults(
            backtest_id="test-2",
            script_id="test-script",
            execution_summary=Mock(),
            execution_metrics=metrics2,
            performance_data=Mock(),
            trade_history=[],
            chart_data=None
        )
        
        sweep_execution.update_best_result(result2, {"param": 2})
        assert sweep_execution.best_result == result2
        assert sweep_execution.best_parameters == {"param": 2}
        
        # Worse result (should not update)
        metrics3 = ExecutionMetrics(
            total_return=0.05,
            annualized_return=0.06,
            sharpe_ratio=0.8,  # Worse Sharpe ratio
            sortino_ratio=1.0,
            max_drawdown=0.08,
            max_drawdown_duration=timedelta(days=15),
            volatility=0.15,
            beta=1.0,
            alpha=0.01,
            value_at_risk_95=0.025,
            conditional_var_95=0.035,
            calmar_ratio=0.6,
            profit_factor=1.2,
            recovery_factor=1.5,
            payoff_ratio=0.8
        )
        result3 = ProcessedResults(
            backtest_id="test-3",
            script_id="test-script",
            execution_summary=Mock(),
            execution_metrics=metrics3,
            performance_data=Mock(),
            trade_history=[],
            chart_data=None
        )
        
        sweep_execution.update_best_result(result3, {"param": 3})
        assert sweep_execution.best_result == result2  # Should remain result2
        assert sweep_execution.best_parameters == {"param": 2}