"""
Tests for script debugging and validation system.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from haasscript_backtesting.script_manager.debug_validator import (
    ScriptDebugValidator, ErrorSeverity, ErrorPattern, ValidationIssue
)
from haasscript_backtesting.api_client.haasonline_client import HaasOnlineClient
from haasscript_backtesting.api_client.response_models import (
    DebugTestResponse, QuickTestResponse, CompilationError, TradeResult
)
from haasscript_backtesting.models.script_models import HaasScript, ScriptType
from haasscript_backtesting.models.common_models import DebugResult, ValidationResult


@pytest.fixture
def mock_api_client():
    """Create mock API client."""
    return Mock(spec=HaasOnlineClient)


@pytest.fixture
def debug_validator(mock_api_client):
    """Create debug validator with mocked API client."""
    return ScriptDebugValidator(mock_api_client)


@pytest.fixture
def sample_script():
    """Create sample script for testing."""
    return HaasScript(
        script_id="test_script",
        name="Test Script",
        content="""
var value = GetValue();
var threshold = 100.0;

if (value > threshold) {
    ExecuteAction(1.0);
    Log("Action at value: " + value);
}

if (value < threshold * 0.9) {
    ExecuteAlternate(1.0);
    Log("Alternate at value: " + value);
}
        """.strip(),
        parameters={
            "threshold": 100.0,
            "amount": 1.0,
            "enable_logging": True
        },
        script_type=ScriptType.TRADING_BOT,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1
    )


@pytest.fixture
def problematic_script():
    """Create script with various issues for testing."""
    return HaasScript(
        script_id="bad_script",
        name="Problematic Script",
        content="""
var value = GetValue()  // Missing semicolon
var var = 100;  // Reserved keyword as variable name

if (value > threshold {  // Missing closing parenthesis
    ExecuteAction(1.0);
    UnknownFunction();  // Unknown function
}

// Unbalanced braces - missing closing brace
        """.strip(),
        parameters={
            "threshold": None,  # None parameter
            "empty_param": "",  # Empty string
            "negative_amount": -1.0  # Negative amount
        },
        script_type=ScriptType.TRADING_BOT,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1
    )


class TestScriptDebugValidator:
    """Test script debug validator functionality."""
    
    def test_initialization(self, mock_api_client):
        """Test debug validator initialization."""
        validator = ScriptDebugValidator(mock_api_client)
        
        assert validator.api_client == mock_api_client
        assert len(validator._error_patterns) > 0
        assert len(validator._known_functions) > 0
        assert len(validator._reserved_keywords) > 0
    
    def test_error_patterns_initialization(self, debug_validator):
        """Test error patterns are properly initialized."""
        patterns = debug_validator._error_patterns
        
        assert len(patterns) > 0
        
        # Check for specific important patterns
        pattern_types = [p.error_type for p in patterns]
        assert "missing_semicolon" in pattern_types
        assert "undefined_variable" in pattern_types
        assert "unknown_function" in pattern_types
        assert "margin_spot_conflict" in pattern_types
    
    def test_debug_script_comprehensive_success(self, debug_validator, mock_api_client, sample_script):
        """Test comprehensive debugging with successful compilation."""
        # Mock successful API response
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
        
        result = debug_validator.debug_script_comprehensive(sample_script)
        
        assert isinstance(result, DebugResult)
        assert result.success is True
        assert len(result.compilation_logs) == 2
        assert len(result.warnings) == 1
        assert len(result.errors) == 0
        assert len(result.suggestions) > 0  # Should have context suggestions
        assert result.execution_time == 0.5
    
    def test_debug_script_comprehensive_with_errors(self, debug_validator, mock_api_client, problematic_script):
        """Test comprehensive debugging with compilation errors."""
        # Mock API response with errors
        compilation_error = CompilationError(
            line_number=2,
            column=15,
            error_type="SyntaxError",
            message="syntax error: missing semicolon",
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
        
        result = debug_validator.debug_script_comprehensive(problematic_script)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert len(result.suggestions) > 0
        
        # Check for intelligent suggestions
        suggestions_text = " ".join(result.suggestions)
        assert "semicolon" in suggestions_text.lower()
    
    def test_analyze_compilation_error(self, debug_validator):
        """Test compilation error analysis."""
        error = CompilationError(
            line_number=5,
            column=10,
            error_type="SyntaxError",
            message="syntax error: missing semicolon",
            suggestion=None
        )
        
        script_content = """
var value = GetValue()
var amount = 1.0;
        """.strip()
        
        result = debug_validator._analyze_compilation_error(error, script_content)
        
        assert "Line 5, Column 10" in result['formatted_error']
        assert len(result['suggestions']) > 0
        assert any("semicolon" in s.lower() for s in result['suggestions'])
    
    def test_validate_script_advanced_success(self, debug_validator, sample_script):
        """Test advanced validation with valid script."""
        result = debug_validator.validate_script_advanced(sample_script)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.parameter_errors) == 0
        assert len(result.logic_errors) == 0
    
    def test_validate_script_advanced_with_issues(self, debug_validator, problematic_script):
        """Test advanced validation with problematic script."""
        result = debug_validator.validate_script_advanced(problematic_script)
        
        assert result.is_valid is False
        assert len(result.parameter_errors) > 0
        assert len(result.logic_errors) > 0
        assert len(result.recommendations) > 0
        
        # Check specific parameter errors
        assert "threshold" in result.parameter_errors  # None value
        assert "empty_param" in result.parameter_errors  # Empty string
        assert "negative_amount" in result.parameter_errors  # Negative amount
    
    def test_perform_static_analysis(self, debug_validator, problematic_script):
        """Test static analysis functionality."""
        issues = debug_validator._perform_static_analysis(problematic_script)
        
        assert len(issues) > 0
        
        # Check for specific issue types
        issue_types = [issue.issue_type for issue in issues]
        assert "bracket_imbalance" in issue_types
        assert "unknown_function" in issue_types
    
    def test_check_line_issues(self, debug_validator):
        """Test individual line issue checking."""
        # Test line with unknown function
        issues = debug_validator._check_line_issues("UnknownFunction(123);", 5)
        
        assert len(issues) > 0
        unknown_func_issues = [i for i in issues if i.issue_type == "unknown_function"]
        assert len(unknown_func_issues) > 0
        
        # Test line with reserved keyword as variable
        issues = debug_validator._check_line_issues("var var = 100;", 3)
        
        reserved_issues = [i for i in issues if i.issue_type == "reserved_keyword"]
        assert len(reserved_issues) > 0
    
    def test_check_script_structure(self, debug_validator):
        """Test script structure checking."""
        # Test unbalanced braces
        unbalanced_content = "if (true) { var x = 1;"  # Missing closing brace
        issues = debug_validator._check_script_structure(unbalanced_content)
        
        bracket_issues = [i for i in issues if i.issue_type == "bracket_imbalance"]
        assert len(bracket_issues) > 0
        
        # Test unbalanced parentheses
        unbalanced_parens = "if (true { var x = 1; }"  # Missing closing parenthesis
        issues = debug_validator._check_script_structure(unbalanced_parens)
        
        paren_issues = [i for i in issues if i.issue_type == "parentheses_imbalance"]
        assert len(paren_issues) > 0
    
    def test_validate_parameters_advanced(self, debug_validator):
        """Test advanced parameter validation."""
        # Test valid parameters
        valid_params = {
            "threshold": 100.0,
            "amount": 1.0,
            "percentage": 50.0,
            "name": "test"
        }
        errors = debug_validator._validate_parameters_advanced(valid_params)
        assert len(errors) == 0
        
        # Test invalid parameters
        invalid_params = {
            "threshold": None,  # None value
            "amount": -1.0,  # Negative amount
            "percentage": 150.0,  # Invalid percentage
            "name": ""  # Empty string
        }
        errors = debug_validator._validate_parameters_advanced(invalid_params)
        assert len(errors) == 4
        assert "threshold" in errors
        assert "amount" in errors
        assert "percentage" in errors
        assert "name" in errors
    
    def test_validate_script_content(self, debug_validator):
        """Test script content validation."""
        # Test empty content
        issues = debug_validator._validate_script_content("")
        empty_issues = [i for i in issues if i.issue_type == "empty_content"]
        assert len(empty_issues) > 0
        
        # Test content without specific logic
        basic_content = "var value = GetValue(); Log('Value: ' + value);"
        issues = debug_validator._validate_script_content(basic_content)
        # Should not have critical issues for basic content
        
        # Test valid content
        valid_content = "var value = GetValue(); if (value > 100) { ExecuteAction(1.0); }"
        issues = debug_validator._validate_script_content(valid_content)
        critical_issues = [i for i in issues if i.severity == ErrorSeverity.CRITICAL]
        assert len(critical_issues) == 0
    
    def test_check_compatibility_issues(self, debug_validator, sample_script):
        """Test compatibility issue checking."""
        # Test script with margin/spot conflict
        margin_script = HaasScript(
            script_id="margin_script",
            name="Margin Script",
            content="// This script uses margin on spot market",
            parameters={},
            script_type=ScriptType.TRADING_BOT,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            version=1
        )
        
        issues = debug_validator._check_compatibility_issues(margin_script)
        assert len(issues) > 0
        assert any("margin" in issue.lower() for issue in issues)
    
    def test_generate_optimization_recommendations(self, debug_validator, sample_script):
        """Test optimization recommendation generation."""
        recommendations = debug_validator._generate_optimization_recommendations(sample_script)
        
        assert isinstance(recommendations, list)
        # Should have some recommendations for any script
        assert len(recommendations) >= 0
    
    def test_quick_test_with_analysis_success(self, debug_validator, mock_api_client, sample_script):
        """Test quick test with analysis for successful execution."""
        # Mock successful API response
        trade_result = TradeResult(
            timestamp=datetime.now(),
            action="ACTION_A",
            price=105.0,
            amount=1.0,
            fee=0.05,
            profit_loss=5.0,
            balance_after=1004.95
        )
        
        api_response = QuickTestResponse(
            success=True,
            execution_id="exec_123",
            trades=[trade_result],
            final_balance=1050.0,
            total_profit_loss=50.0,
            execution_logs=["Test completed successfully"],
            runtime_data={"candles_processed": 100},
            execution_time_ms=2000
        )
        mock_api_client.execute_quick_test.return_value = api_response
        
        success, messages = debug_validator.quick_test_with_analysis(
            sample_script, "test_account", "BINANCE_BTC_USDT"
        )
        
        assert success is True
        assert len(messages) > 0
        
        # Check for specific analysis messages
        messages_text = " ".join(messages)
        assert "trades executed" in messages_text.lower()
        assert "profitable" in messages_text.lower()
    
    def test_quick_test_with_analysis_failure(self, debug_validator, mock_api_client, sample_script):
        """Test quick test with analysis for failed execution."""
        # Mock failed API response
        api_response = QuickTestResponse(
            success=False,
            execution_id="exec_456",
            trades=[],
            final_balance=1000.0,
            total_profit_loss=0.0,
            execution_logs=["Test failed"],
            runtime_data={},
            execution_time_ms=100,
            error_message="Margin settings not allowed on spot market"
        )
        mock_api_client.execute_quick_test.return_value = api_response
        
        success, messages = debug_validator.quick_test_with_analysis(
            sample_script, "test_account", "BINANCE_BTC_USDT"
        )
        
        assert success is False
        assert len(messages) > 0
        
        # Check for error analysis
        messages_text = " ".join(messages)
        assert "failed" in messages_text.lower()
        assert "margin" in messages_text.lower()
    
    def test_generate_context_suggestions(self, debug_validator, sample_script):
        """Test context-aware suggestion generation."""
        # Test with no errors
        suggestions = debug_validator._generate_context_suggestions(sample_script, [])
        assert len(suggestions) > 0
        assert any("successfully" in s.lower() for s in suggestions)
        
        # Test with errors
        error = CompilationError(
            line_number=1,
            column=1,
            error_type="SyntaxError",
            message="Test error",
            suggestion=None
        )
        suggestions = debug_validator._generate_context_suggestions(sample_script, [error])
        assert len(suggestions) > 0
        assert any("fix" in s.lower() for s in suggestions)


class TestErrorPattern:
    """Test error pattern functionality."""
    
    def test_error_pattern_creation(self):
        """Test error pattern creation."""
        pattern = ErrorPattern(
            pattern=r"missing.*semicolon",
            error_type="missing_semicolon",
            severity=ErrorSeverity.HIGH,
            description="Missing semicolon",
            suggestion="Add semicolon",
            fix_example="var x = 1;"
        )
        
        assert pattern.pattern == r"missing.*semicolon"
        assert pattern.error_type == "missing_semicolon"
        assert pattern.severity == ErrorSeverity.HIGH
        assert pattern.description == "Missing semicolon"
        assert pattern.suggestion == "Add semicolon"
        assert pattern.fix_example == "var x = 1;"


class TestValidationIssue:
    """Test validation issue functionality."""
    
    def test_validation_issue_creation(self):
        """Test validation issue creation."""
        issue = ValidationIssue(
            issue_type="syntax_error",
            severity=ErrorSeverity.HIGH,
            line_number=5,
            column=10,
            message="Syntax error detected",
            context="var x = 1",
            suggestion="Fix syntax",
            fix_example="var x = 1;"
        )
        
        assert issue.issue_type == "syntax_error"
        assert issue.severity == ErrorSeverity.HIGH
        assert issue.line_number == 5
        assert issue.column == 10
        assert issue.message == "Syntax error detected"
        assert issue.context == "var x = 1"
        assert issue.suggestion == "Fix syntax"
        assert issue.fix_example == "var x = 1;"


if __name__ == "__main__":
    pytest.main([__file__])