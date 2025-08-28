"""
Unit tests for Parameter Optimization Interface.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mcp_tui_client.ui.optimization import (
    ParameterRange, OptimizationConfig, OptimizationResult,
    OptimizationAlgorithm, OptimizationStatus,
    ParameterOptimizationInterface, OptimizationProgressPanel
)


class TestParameterRange:
    """Test parameter range functionality"""
    
    def test_float_parameter_range(self):
        """Test float parameter range creation"""
        param = ParameterRange("test_param", 0.1, 1.0, 0.1, "float")
        assert param.name == "test_param"
        assert param.min_value == 0.1
        assert param.max_value == 1.0
        assert param.step == 0.1
        assert param.parameter_type == "float"
        assert param.current_value == 0.55  # (0.1 + 1.0) / 2
    
    def test_int_parameter_range(self):
        """Test integer parameter range creation"""
        param = ParameterRange("int_param", 10, 100, 5, "int")
        assert param.parameter_type == "int"
        assert param.current_value == 55  # (10 + 100) / 2
    
    def test_choice_parameter_range(self):
        """Test choice parameter range creation"""
        choices = ["option1", "option2", "option3"]
        param = ParameterRange("choice_param", 0, 0, parameter_type="choice", choices=choices)
        assert param.parameter_type == "choice"
        assert param.choices == choices
        assert param.current_value == "option1"  # First choice
    
    def test_bool_parameter_range(self):
        """Test boolean parameter range creation"""
        param = ParameterRange("bool_param", 0, 1, parameter_type="bool")
        assert param.parameter_type == "bool"
        assert param.current_value is False


class TestOptimizationConfig:
    """Test optimization configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = OptimizationConfig("test-lab")
        assert config.lab_id == "test-lab"
        assert config.algorithm == OptimizationAlgorithm.GENETIC
        assert config.max_iterations == 100
        assert config.population_size == 50
        assert config.objective_function == "sharpe_ratio"
        assert config.minimize is False
    
    def test_config_with_parameters(self):
        """Test configuration with parameter ranges"""
        param1 = ParameterRange("param1", 0, 10, parameter_type="float")
        param2 = ParameterRange("param2", 1, 5, parameter_type="int")
        
        config = OptimizationConfig("test-lab", parameter_ranges=[param1, param2])
        assert len(config.parameter_ranges) == 2
        assert config.parameter_ranges[0].name == "param1"
        assert config.parameter_ranges[1].name == "param2"


class TestOptimizationResult:
    """Test optimization result"""
    
    def test_result_creation(self):
        """Test optimization result creation"""
        result = OptimizationResult(
            iteration=1,
            parameters={"param1": 0.5, "param2": 10},
            objective_value=1.25,
            metrics={"return": 15.5, "drawdown": -5.2},
            execution_time=0.1
        )
        
        assert result.iteration == 1
        assert result.parameters["param1"] == 0.5
        assert result.objective_value == 1.25
        assert result.metrics["return"] == 15.5
        assert result.execution_time == 0.1
        assert result.timestamp is not None


class TestOptimizationProgressPanel:
    """Test optimization progress panel"""
    
    def test_progress_panel_initialization(self):
        """Test progress panel initialization"""
        panel = OptimizationProgressPanel()
        assert panel.current_iteration == 0
        assert panel.total_iterations == 0
        assert panel.best_result is None
        assert len(panel.results_history) == 0
        assert panel.start_time is None
    
    def test_progress_update(self):
        """Test progress update functionality"""
        panel = OptimizationProgressPanel()
        
        result = OptimizationResult(
            iteration=1,
            parameters={"param1": 0.5},
            objective_value=1.0,
            metrics={},
            execution_time=0.1
        )
        
        panel.update_progress(1, 10, result)
        
        assert panel.current_iteration == 1
        assert panel.total_iterations == 10
        assert panel.best_result == result
        assert len(panel.results_history) == 1
    
    def test_optimization_lifecycle(self):
        """Test optimization start/complete lifecycle"""
        panel = OptimizationProgressPanel()
        
        # Start optimization
        panel.start_optimization()
        assert panel.start_time is not None
        
        # Complete optimization
        panel.complete_optimization()
        # Should not raise any errors
    
    def test_optimization_failure(self):
        """Test optimization failure handling"""
        panel = OptimizationProgressPanel()
        
        panel.fail_optimization("Test error")
        # Should not raise any errors


class TestParameterOptimizationInterface:
    """Test parameter optimization interface"""
    
    def test_interface_initialization(self):
        """Test interface initialization"""
        interface = ParameterOptimizationInterface("test-lab")
        assert interface.lab_id == "test-lab"
        assert interface.config.lab_id == "test-lab"
        assert interface.status == OptimizationStatus.IDLE
    
    def test_config_validation(self):
        """Test configuration validation"""
        interface = ParameterOptimizationInterface("test-lab")
        
        # Empty config should be invalid
        assert not interface._validate_config()
        
        # Add parameter ranges
        interface.config.parameter_ranges = [
            ParameterRange("param1", 0, 10, parameter_type="float")
        ]
        
        # Should be valid now
        assert interface._validate_config()
        
        # Invalid max_iterations should be invalid
        interface.config.max_iterations = 0
        assert not interface._validate_config()
    
    @pytest.mark.asyncio
    async def test_optimization_mock_run(self):
        """Test mock optimization run"""
        interface = ParameterOptimizationInterface("test-lab")
        
        # Set up valid configuration
        interface.config.parameter_ranges = [
            ParameterRange("param1", 0, 10, parameter_type="float")
        ]
        interface.config.max_iterations = 5
        
        # Mock the progress panel
        interface.progress_panel = AsyncMock()
        interface.results_panel = AsyncMock()
        
        # Run optimization
        await interface._run_optimization()
        
        # Should complete without errors
        assert interface.status == OptimizationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__])