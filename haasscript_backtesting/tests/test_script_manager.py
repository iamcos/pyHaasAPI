"""
Tests for script management operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

from haasscript_backtesting.script_manager.script_manager import ScriptManager
from haasscript_backtesting.config.config_manager import ConfigManager
from haasscript_backtesting.api_client.haasonline_client import HaasOnlineClient
from haasscript_backtesting.api_client.response_models import (
    ScriptRecordResponse, DebugTestResponse, QuickTestResponse,
    CompilationError, TradeResult, ExecutionStatus
)
from haasscript_backtesting.models.script_models import HaasScript, ScriptType
from haasscript_backtesting.models.script_models import DebugResult, ValidationResult, QuickTestResult


@pytest.fixture
def mock_config_manager():
    """Create mock configuration manager."""
    return Mock(spec=ConfigManager)


@pytest.fixture
def mock_api_client():
    """Create mock API client."""
    return Mock(spec=HaasOnlineClient)


@pytest.fixture
def script_manager(mock_config_manager, mock_api_client):
    """Create script manager with mocked dependencies."""
    return ScriptManager(mock_config_manager, mock_api_client)


@pytest.fixture
def sample_script():
    """Create sample HaasScript for testing."""
    return HaasScript(
        script_id="test_script_123",
        name="Test Script",
        content="var value = GetValue();\nif (value > 100) {\n    ExecuteAction(1.0);\n}",
        parameters={
            "threshold": 100.0,
            "amount": 1.0,
            "enable_logging": True
        },
        script_type=ScriptType.TRADING_BOT,
        created_at=datetime(2023, 1, 1),
        modified_at=datetime(2023, 1, 1),
        version=1
    )


class TestScriptManager:
    """Test script manager functionality."""
    
    def test_initialization(self, mock_config_manager, mock_api_client):
        """Test script manager initialization."""
        manager = ScriptManager(mock_config_manager, mock_api_client)
        
        assert manager.config == mock_config_manager
        assert manager.api_client == mock_api_client
        assert manager._script_cache == {}
        assert manager._capabilities_cache is None
    
    def test_load_script_success(self, script_manager, mock_api_client):
        """Test successful script loading."""
        # Mock API response
        api_response = ScriptRecordResponse(
            script_id="test_script",
            name="Test Script",
            content="// test content",
            script_type=1,
            parameters={"param1": "value1"},
            created_at=datetime(2023, 1, 1),
            modified_at=datetime(2023, 1, 1),
            compile_logs=["Compilation successful"],
            is_valid=True
        )
        mock_api_client.get_script_record.return_value = api_response
        
        # Load script
        result = script_manager.load_script("test_script")
        
        # Verify result
        assert isinstance(result, HaasScript)
        assert result.script_id == "test_script"
        assert result.name == "Test Script"
        assert result.content == "// test content"
        assert result.parameters == {"param1": "value1"}
        
        # Verify API call
        mock_api_client.get_script_record.assert_called_once()
        call_args = mock_api_client.get_script_record.call_args[0][0]
        assert call_args.script_id == "test_script"
        
        # Verify caching
        assert "test_script" in script_manager._script_cache
    
    def test_load_script_cached(self, script_manager, mock_api_client, sample_script):
        """Test loading script from cache."""
        # Pre-populate cache
        script_manager._script_cache["test_script"] = sample_script
        
        # Load script
        result = script_manager.load_script("test_script")
        
        # Verify result comes from cache
        assert result == sample_script
        
        # Verify API not called
        mock_api_client.get_script_record.assert_not_called()
    
    def test_load_script_force_reload(self, script_manager, mock_api_client, sample_script):
        """Test force reload bypasses cache."""
        # Pre-populate cache
        script_manager._script_cache["test_script"] = sample_script
        
        # Mock API response
        api_response = ScriptRecordResponse(
            script_id="test_script",
            name="Updated Script",
            content="// updated content",
            script_type=1,
            parameters={"param1": "updated_value"},
            created_at=datetime(2023, 1, 1),
            modified_at=datetime(2023, 1, 2),
            compile_logs=[],
            is_valid=True
        )
        mock_api_client.get_script_record.return_value = api_response
        
        # Load script with force reload
        result = script_manager.load_script("test_script", force_reload=True)
        
        # Verify API was called despite cache
        mock_api_client.get_script_record.assert_called_once()
        
        # Verify updated content
        assert result.name == "Updated Script"
        assert result.content == "// updated content"
    
    def test_load_script_invalid_id(self, script_manager):
        """Test loading script with invalid ID."""
        with pytest.raises(ValueError, match="script_id cannot be empty"):
            script_manager.load_script("")
    
    def test_debug_script_success(self, script_manager, mock_api_client, sample_script):
        """Test successful script debugging."""
        # Mock API response
        api_response = DebugTestResponse(
            success=True,
            compilation_logs=["Compilation started", "Compilation completed"],
            errors=[],
            warnings=["Unused variable detected"],
            execution_time_ms=500,
            memory_usage_mb=5.0,
            is_valid=True
        )
        mock_api_client.execute_debug_test.return_value = api_response
        
        # Debug script
        result = script_manager.debug_script(sample_script)
        
        # Verify result
        assert isinstance(result, DebugResult)
        assert result.success is True
        assert len(result.compilation_logs) == 2
        assert len(result.warnings) == 1
        assert len(result.errors) == 0
        assert result.execution_time == 0.5  # Converted from ms
        
        # Verify API call
        mock_api_client.execute_debug_test.assert_called_once()
        call_args = mock_api_client.execute_debug_test.call_args[0][0]
        assert call_args.script_id == sample_script.script_id
        assert call_args.script_content == sample_script.content
    
    def test_debug_script_with_errors(self, script_manager, mock_api_client, sample_script):
        """Test script debugging with compilation errors."""
        # Mock API response with errors
        compilation_error = CompilationError(
            line_number=5,
            column=10,
            error_type="SyntaxError",
            message="Missing semicolon",
            suggestion="Add semicolon at end of line"
        )
        
        api_response = DebugTestResponse(
            success=False,
            compilation_logs=["Compilation started", "Compilation failed"],
            errors=[compilation_error],
            warnings=[],
            execution_time_ms=100,
            memory_usage_mb=2.0,
            is_valid=False
        )
        mock_api_client.execute_debug_test.return_value = api_response
        
        # Debug script
        result = script_manager.debug_script(sample_script)
        
        # Verify result
        assert result.success is False
        assert len(result.errors) == 1
        assert "Line 5, Column 10: Missing semicolon" in result.errors[0]
        assert len(result.suggestions) > 0
    
    def test_validate_script(self, script_manager, sample_script):
        """Test script validation."""
        result = script_manager.validate_script(sample_script)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.parameter_errors) == 0
        assert len(result.logic_errors) == 0
    
    def test_validate_script_with_issues(self, script_manager):
        """Test script validation with issues."""
        # Create script with issues
        problematic_script = HaasScript(
            script_id="bad_script",
            name="Bad Script",
            content="",  # Empty content
            parameters={
                "empty_param": "",  # Empty string parameter
                "none_param": None  # None parameter
            },
            script_type=ScriptType.TRADING_BOT,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            version=1
        )
        
        result = script_manager.validate_script(problematic_script)
        
        assert result.is_valid is False
        assert len(result.parameter_errors) == 2
        assert len(result.logic_errors) == 1
        assert "empty_param" in result.parameter_errors
        assert "none_param" in result.parameter_errors
        assert "Script content cannot be empty" in result.logic_errors
    
    def test_clone_script(self, script_manager, mock_api_client, sample_script):
        """Test script cloning."""
        # Mock load_script to return sample script
        script_manager._script_cache[sample_script.script_id] = sample_script
        
        # Clone script
        cloned_id = script_manager.clone_script(sample_script.script_id, "Cloned Script")
        
        # Verify cloned script
        assert cloned_id.startswith("clone_")
        assert cloned_id in script_manager._script_cache
        
        cloned_script = script_manager._script_cache[cloned_id]
        assert cloned_script.name == "Cloned Script"
        assert cloned_script.content == sample_script.content
        assert cloned_script.parameters == sample_script.parameters
        assert cloned_script.script_id != sample_script.script_id
    
    def test_clone_script_auto_name(self, script_manager, sample_script):
        """Test script cloning with automatic name generation."""
        script_manager._script_cache[sample_script.script_id] = sample_script
        
        cloned_id = script_manager.clone_script(sample_script.script_id)
        cloned_script = script_manager._script_cache[cloned_id]
        
        assert "clone_" in cloned_script.name
        assert sample_script.name in cloned_script.name
    
    def test_update_parameters(self, script_manager, sample_script):
        """Test parameter updates."""
        new_params = {
            "threshold": 150.0,
            "new_param": "new_value"
        }
        
        updated_script = script_manager.update_parameters(sample_script, new_params)
        
        assert updated_script.parameters["threshold"] == 150.0
        assert updated_script.parameters["new_param"] == "new_value"
        assert updated_script.parameters["amount"] == 1.0  # Unchanged
        assert updated_script.version == 2  # Incremented
    
    def test_quick_test_script(self, script_manager, mock_api_client, sample_script):
        """Test quick script testing."""
        # Mock API response
        trade_result = TradeResult(
            timestamp=datetime(2023, 1, 1, 12, 0),
            action="ACTION_A",
            price=105.0,
            amount=1.0,
            fee=0.05,
            profit_loss=0.0,
            balance_after=999.95
        )
        
        api_response = QuickTestResponse(
            success=True,
            execution_id="exec_123",
            trades=[trade_result],
            final_balance=1050.0,
            total_profit_loss=50.0,
            execution_logs=["Test completed"],
            runtime_data={"candles_processed": 100},
            execution_time_ms=2000
        )
        mock_api_client.execute_quick_test.return_value = api_response
        
        # Execute quick test
        result = script_manager.quick_test_script(
            sample_script,
            account_id="test_account",
            market_tag="BINANCE_BTC_USDT"
        )
        
        # Verify result
        assert isinstance(result, QuickTestResult)
        assert result.success is True
        assert len(result.trade_signals) == 1
        assert result.trade_signals[0]["type"] == "action_a"
        assert result.trade_signals[0]["price"] == 105.0
        assert result.performance_summary["final_balance"] == 1050.0
        assert result.execution_time == 2.0  # Converted from ms
    
    def test_validate_parameters(self, script_manager, sample_script):
        """Test parameter validation."""
        # Valid parameters
        valid_params = {
            "threshold": 200.0,
            "amount": 2.0
        }
        errors = script_manager.validate_parameters(sample_script, valid_params)
        assert len(errors) == 0
        
        # Invalid parameters
        invalid_params = {
            "threshold": None,  # None value
            "amount": "invalid",  # Type mismatch
            "empty_string": "",  # Empty string
            "negative_value": -1.0  # Negative value
        }
        errors = script_manager.validate_parameters(sample_script, invalid_params)
        assert len(errors) == 4
        assert "threshold" in errors
        assert "amount" in errors
        assert "empty_string" in errors
        assert "negative_value" in errors
    
    def test_save_script(self, script_manager, sample_script):
        """Test script saving."""
        original_version = sample_script.version
        
        result = script_manager.save_script(sample_script)
        
        assert result is True
        assert sample_script.version == original_version + 1
        assert sample_script.script_id in script_manager._script_cache
    
    def test_get_cached_scripts(self, script_manager, sample_script):
        """Test getting cached scripts."""
        script_manager._script_cache[sample_script.script_id] = sample_script
        
        cached_scripts = script_manager.get_cached_scripts()
        
        assert len(cached_scripts) == 1
        assert cached_scripts[0] == sample_script
    
    def test_clear_cache(self, script_manager, sample_script):
        """Test cache clearing."""
        script_manager._script_cache[sample_script.script_id] = sample_script
        script_manager._capabilities_cache = Mock()
        
        script_manager.clear_cache()
        
        assert len(script_manager._script_cache) == 0
        assert script_manager._capabilities_cache is None
    
    def test_get_script_capabilities(self, script_manager):
        """Test getting script capabilities."""
        capabilities = script_manager.get_script_capabilities()
        
        assert capabilities is not None
        assert len(capabilities.available_functions) > 0
        assert len(capabilities.available_indicators) > 0
        assert len(capabilities.syntax_rules) > 0
        
        # Test caching
        capabilities2 = script_manager.get_script_capabilities()
        assert capabilities == capabilities2


if __name__ == "__main__":
    pytest.main([__file__])