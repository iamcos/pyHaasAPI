"""
Advanced script debugging and validation system with intelligent error parsing.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from ..models.script_models import HaasScript
from ..models.common_models import DebugResult, ValidationResult
from ..api_client.haasonline_client import HaasOnlineClient
from ..api_client.request_models import DebugTestRequest, QuickTestRequest
from ..api_client.response_models import CompilationError


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorPattern:
    """Pattern for matching and suggesting fixes for common errors."""
    pattern: str
    error_type: str
    severity: ErrorSeverity
    description: str
    suggestion: str
    fix_example: Optional[str] = None


@dataclass
class ValidationIssue:
    """Detailed validation issue with context and suggestions."""
    issue_type: str
    severity: ErrorSeverity
    line_number: Optional[int]
    column: Optional[int]
    message: str
    context: str
    suggestion: str
    fix_example: Optional[str] = None


class ScriptDebugValidator:
    """
    Advanced script debugging and validation system.
    
    Provides intelligent error parsing, common issue detection,
    and actionable suggestions for HaasScript development.
    """
    
    def __init__(self, api_client: HaasOnlineClient):
        """Initialize debug validator with API client.
        
        Args:
            api_client: HaasOnline API client for debug operations
        """
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Initialize error patterns for intelligent suggestions
        self._error_patterns = self._initialize_error_patterns()
        
        # Dynamic function validation - will be populated from API/RAG
        self._known_functions = set()
        self._functions_loaded = False
        
        # Load functions dynamically
        self._load_known_functions()
        
        self._reserved_keywords = {
            'var', 'function', 'if', 'else', 'for', 'while', 'do', 'switch', 'case',
            'break', 'continue', 'return', 'true', 'false', 'null', 'undefined'
        }
    
    def debug_script_comprehensive(self, script: HaasScript) -> DebugResult:
        """
        Perform comprehensive script debugging with intelligent error analysis.
        
        Args:
            script: HaasScript to debug
            
        Returns:
            Enhanced DebugResult with intelligent suggestions
        """
        self.logger.info(f"Starting comprehensive debug for script: {script.name}")
        
        try:
            # Execute API debug test
            request = DebugTestRequest(
                script_id=script.script_id,
                script_content=script.content,
                parameters=script.parameters
            )
            response = self.api_client.execute_debug_test(request)
            
            # Analyze compilation errors with intelligent suggestions
            enhanced_errors = []
            intelligent_suggestions = []
            
            for error in response.errors:
                error_analysis = self._analyze_compilation_error(error, script.content)
                enhanced_errors.append(error_analysis['formatted_error'])
                if error_analysis['suggestions']:
                    intelligent_suggestions.extend(error_analysis['suggestions'])
            
            # Perform additional static analysis
            static_issues = self._perform_static_analysis(script)
            for issue in static_issues:
                if issue.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                    enhanced_errors.append(f"Static Analysis: {issue.message}")
                intelligent_suggestions.append(issue.suggestion)
            
            # Generate context-aware suggestions
            context_suggestions = self._generate_context_suggestions(script, response.errors)
            intelligent_suggestions.extend(context_suggestions)
            
            # Remove duplicate suggestions
            unique_suggestions = list(dict.fromkeys(intelligent_suggestions))
            
            result = DebugResult(
                success=response.success and len(static_issues) == 0,
                compilation_logs=response.compilation_logs,
                warnings=response.warnings,
                errors=enhanced_errors,
                suggestions=unique_suggestions,
                execution_time=response.execution_time_ms / 1000.0
            )
            
            self.logger.info(f"Debug completed for {script.name}: {len(enhanced_errors)} errors, {len(unique_suggestions)} suggestions")
            return result
            
        except Exception as e:
            self.logger.error(f"Debug execution failed for script {script.name}: {e}")
            return DebugResult(
                success=False,
                compilation_logs=[],
                warnings=[],
                errors=[f"Debug execution failed: {str(e)}"],
                suggestions=["Check network connection and API credentials", "Verify script ID is valid"]
            )
    
    def validate_script_advanced(self, script: HaasScript) -> ValidationResult:
        """
        Perform advanced script validation with detailed issue analysis.
        
        Args:
            script: HaasScript to validate
            
        Returns:
            Enhanced ValidationResult with detailed issues
        """
        self.logger.info(f"Starting advanced validation for script: {script.name}")
        
        parameter_errors = {}
        logic_errors = []
        compatibility_issues = []
        recommendations = []
        
        # Validate parameters with enhanced checks
        param_issues = self._validate_parameters_advanced(script.parameters)
        parameter_errors.update(param_issues)
        
        # Validate script content
        content_issues = self._validate_script_content(script.content)
        logic_errors.extend([issue.message for issue in content_issues if issue.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]])
        compatibility_issues.extend([issue.message for issue in content_issues if issue.severity == ErrorSeverity.MEDIUM])
        recommendations.extend([issue.suggestion for issue in content_issues if issue.severity == ErrorSeverity.LOW])
        
        # Check for common compatibility issues
        compat_issues = self._check_compatibility_issues(script)
        compatibility_issues.extend(compat_issues)
        
        # Generate optimization recommendations
        optimization_recs = self._generate_optimization_recommendations(script)
        recommendations.extend(optimization_recs)
        
        is_valid = len(parameter_errors) == 0 and len(logic_errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            parameter_errors=parameter_errors,
            logic_errors=logic_errors,
            compatibility_issues=compatibility_issues,
            recommendations=recommendations
        )
    
    def quick_test_with_analysis(
        self, 
        script: HaasScript, 
        account_id: str, 
        market_tag: str,
        interval: int = 60
    ) -> Tuple[bool, List[str]]:
        """
        Perform quick test with runtime error analysis.
        
        Args:
            script: HaasScript to test
            account_id: Account ID for testing
            market_tag: Market tag for testing
            interval: Candle interval in minutes
            
        Returns:
            Tuple of (success, list of analysis messages)
        """
        self.logger.info(f"Quick testing with analysis: {script.name}")
        
        try:
            request = QuickTestRequest(
                script_id=script.script_id,
                account_id=account_id,
                market_tag=market_tag,
                interval=interval,
                script_content=script.content,
                parameters=script.parameters
            )
            response = self.api_client.execute_quick_test(request)
            
            analysis_messages = []
            
            if response.success:
                # Analyze execution behavior
                if len(response.trades) == 0:
                    analysis_messages.append("⚠️  No trades executed - check execution conditions")
                else:
                    analysis_messages.append(f"✅ {len(response.trades)} trades executed successfully")
                    
                    # Analyze trade patterns (generic approach)
                    trade_actions = [t.action.upper() for t in response.trades]
                    unique_actions = set(trade_actions)
                    
                    if len(unique_actions) == 1:
                        analysis_messages.append(f"⚠️  Only {list(unique_actions)[0]} actions detected - check other conditions")
                
                # Analyze performance
                if response.total_profit_loss > 0:
                    analysis_messages.append(f"📈 Profitable: +{response.total_profit_loss:.2f}")
                elif response.total_profit_loss < 0:
                    analysis_messages.append(f"📉 Loss: {response.total_profit_loss:.2f}")
                else:
                    analysis_messages.append("➖ Break-even result")
                
                # Analyze execution logs for warnings
                warning_keywords = ['warning', 'error', 'failed', 'invalid']
                for log in response.execution_logs:
                    if any(keyword in log.lower() for keyword in warning_keywords):
                        analysis_messages.append(f"⚠️  Log warning: {log}")
            else:
                analysis_messages.append(f"❌ Quick test failed: {response.error_message}")
                
                # Analyze common failure patterns (generic approach)
                if response.error_message:
                    error_msg = response.error_message.lower()
                    # Generic error pattern analysis without hardcoded assumptions
                    analysis_messages.append(f"💡 Error analysis: {response.error_message}")
                    
                    # Look for common error keywords and provide generic suggestions
                    if 'insufficient' in error_msg:
                        analysis_messages.append("💡 Suggestion: Check account balance and amounts")
                    elif 'not found' in error_msg:
                        analysis_messages.append("💡 Suggestion: Verify identifiers and formats")
                    elif 'invalid' in error_msg:
                        analysis_messages.append("💡 Suggestion: Check parameter values and types")
            
            return response.success, analysis_messages
            
        except Exception as e:
            self.logger.error(f"Quick test analysis failed for script {script.name}: {e}")
            return False, [f"❌ Quick test failed: {str(e)}"]
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize common error patterns for intelligent suggestions."""
        # Load patterns from configuration or external source
        # This should be configurable and not hardcoded
        try:
            return self._load_error_patterns_from_config()
        except Exception:
            # Return minimal patterns if config loading fails
            return [
                ErrorPattern(
                    pattern=r"syntax error.*missing.*semicolon",
                    error_type="missing_semicolon",
                    severity=ErrorSeverity.HIGH,
                    description="Missing semicolon at end of statement",
                    suggestion="Add semicolon (;) at the end of the statement",
                    fix_example="var variable = value;"
                ),
                ErrorPattern(
                    pattern=r"undefined.*variable.*(\w+)",
                    error_type="undefined_variable",
                    severity=ErrorSeverity.HIGH,
                    description="Variable used before declaration",
                    suggestion="Declare variable with 'var' keyword before use",
                    fix_example="var myVariable = 0;"
                ),
                ErrorPattern(
                    pattern=r"function.*(\w+).*not.*found",
                    error_type="unknown_function",
                    severity=ErrorSeverity.CRITICAL,
                    description="Unknown function call",
                    suggestion="Check function name spelling or verify it's available",
                    fix_example="Check documentation for correct function names"
                ),
                ErrorPattern(
                    pattern=r"missing.*closing.*bracket",
                    error_type="missing_bracket",
                    severity=ErrorSeverity.HIGH,
                    description="Missing closing bracket",
                    suggestion="Add missing closing bracket } or )",
                    fix_example="if (condition) { /* code */ }"
                )
            ]
    
    def _load_error_patterns_from_config(self) -> List[ErrorPattern]:
        """Load error patterns from configuration file or database."""
        # This should load from a configuration file, database, or API
        # For now, return empty list to indicate not implemented
        return []
    
    def _load_known_functions(self) -> None:
        """Load known functions from API or configuration."""
        try:
            # Try to load from API first
            functions = self._load_functions_from_api()
            if functions:
                self._known_functions = set(functions)
                self._functions_loaded = True
                self.logger.info(f"Loaded {len(functions)} functions from API")
                return
            
            # Fallback to configuration or RAG
            functions = self._load_functions_from_config()
            if functions:
                self._known_functions = set(functions)
                self._functions_loaded = True
                self.logger.info(f"Loaded {len(functions)} functions from config")
                return
            
            # No functions loaded - disable function validation
            self._functions_loaded = False
            self.logger.warning("No functions loaded - function validation disabled")
            
        except Exception as e:
            self.logger.error(f"Failed to load known functions: {e}")
            self._functions_loaded = False
    
    def _load_functions_from_api(self) -> Optional[List[str]]:
        """Load available functions from API."""
        try:
            # This would call an API endpoint to get available functions
            # For now, return None to indicate not implemented
            return None
        except Exception as e:
            self.logger.debug(f"API function loading failed: {e}")
            return None
    
    def _load_functions_from_config(self) -> Optional[List[str]]:
        """Load available functions from configuration."""
        try:
            # This would load from a configuration file or database
            # For now, return None to indicate not implemented
            return None
        except Exception as e:
            self.logger.debug(f"Config function loading failed: {e}")
            return None
    
    def _analyze_compilation_error(self, error: CompilationError, script_content: str) -> Dict[str, Any]:
        """Analyze compilation error and provide intelligent suggestions."""
        formatted_error = f"Line {error.line_number}, Column {error.column}: {error.message}"
        suggestions = []
        
        # Check against known error patterns
        for pattern in self._error_patterns:
            if re.search(pattern.pattern, error.message, re.IGNORECASE):
                suggestions.append(f"💡 {pattern.suggestion}")
                if pattern.fix_example:
                    suggestions.append(f"📝 Example: {pattern.fix_example}")
                break
        
        # Add context-specific suggestions
        if error.line_number > 0:
            lines = script_content.split('\n')
            if error.line_number <= len(lines):
                error_line = lines[error.line_number - 1].strip()
                
                # Analyze the specific line for common issues
                if not error_line.endswith(';') and not error_line.endswith('{') and not error_line.endswith('}'):
                    suggestions.append("💡 Consider adding semicolon at end of line")
                
                if '(' in error_line and error_line.count('(') != error_line.count(')'):
                    suggestions.append("💡 Check parentheses balance")
                
                if '{' in error_line and error_line.count('{') != error_line.count('}'):
                    suggestions.append("💡 Check curly braces balance")
        
        return {
            'formatted_error': formatted_error,
            'suggestions': suggestions
        }
    
    def _perform_static_analysis(self, script: HaasScript) -> List[ValidationIssue]:
        """Perform static analysis of script content."""
        issues = []
        lines = script.content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith('//'):
                continue
            
            # Check for common issues
            issues.extend(self._check_line_issues(line_stripped, line_num))
        
        # Check overall script structure
        issues.extend(self._check_script_structure(script.content))
        
        return issues
    
    def _check_line_issues(self, line: str, line_num: int) -> List[ValidationIssue]:
        """Check individual line for common issues."""
        issues = []
        
        # Check for unknown functions (only if we have loaded function list)
        if self._functions_loaded:
            function_calls = re.findall(r'(\w+)\s*\(', line)
            for func_name in function_calls:
                if func_name not in self._known_functions and func_name not in self._reserved_keywords:
                    issues.append(ValidationIssue(
                        issue_type="unknown_function",
                        severity=ErrorSeverity.MEDIUM,
                        line_number=line_num,
                        column=line.find(func_name),
                        message=f"Unknown function '{func_name}' may cause runtime error",
                        context=line,
                        suggestion=f"Verify '{func_name}' is a valid function",
                        fix_example="Check documentation for correct function names"
                    ))
        
        # Check for potential variable naming issues
        var_declarations = re.findall(r'var\s+(\w+)', line)
        for var_name in var_declarations:
            if var_name in self._reserved_keywords:
                issues.append(ValidationIssue(
                    issue_type="reserved_keyword",
                    severity=ErrorSeverity.HIGH,
                    line_number=line_num,
                    column=line.find(var_name),
                    message=f"Variable name '{var_name}' is a reserved keyword",
                    context=line,
                    suggestion=f"Choose a different variable name instead of '{var_name}'",
                    fix_example=f"var my{var_name.capitalize()} = value;"
                ))
        
        return issues
    
    def _check_script_structure(self, content: str) -> List[ValidationIssue]:
        """Check overall script structure for issues."""
        issues = []
        
        # Check bracket balance
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(ValidationIssue(
                issue_type="bracket_imbalance",
                severity=ErrorSeverity.CRITICAL,
                line_number=None,
                column=None,
                message=f"Unbalanced braces: {open_braces} opening, {close_braces} closing",
                context="Entire script",
                suggestion="Check that every opening brace { has a matching closing brace }",
                fix_example="if (condition) { /* code */ }"
            ))
        
        # Check parentheses balance
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            issues.append(ValidationIssue(
                issue_type="parentheses_imbalance",
                severity=ErrorSeverity.CRITICAL,
                line_number=None,
                column=None,
                message=f"Unbalanced parentheses: {open_parens} opening, {close_parens} closing",
                context="Entire script",
                suggestion="Check that every opening parenthesis ( has a matching closing parenthesis )",
                fix_example="if (condition) { /* code */ }"
            ))
        
        return issues
    
    def _validate_parameters_advanced(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Perform advanced parameter validation."""
        errors = {}
        
        for param_name, param_value in parameters.items():
            # Basic null check
            if param_value is None:
                errors[param_name] = "Parameter value cannot be None"
                continue
            
            # Type-specific validation
            if isinstance(param_value, str):
                if not param_value.strip():
                    errors[param_name] = "String parameter cannot be empty"
            elif isinstance(param_value, (int, float)):
                # Generic numeric validation - no assumptions about parameter meaning
                if param_value != param_value:  # Check for NaN
                    errors[param_name] = "Numeric parameter cannot be NaN"
                elif not isinstance(param_value, (int, float)):
                    errors[param_name] = "Expected numeric value"
        
        return errors
    
    def _validate_script_content(self, content: str) -> List[ValidationIssue]:
        """Validate script content for common issues."""
        issues = []
        
        if not content.strip():
            issues.append(ValidationIssue(
                issue_type="empty_content",
                severity=ErrorSeverity.CRITICAL,
                line_number=None,
                column=None,
                message="Script content cannot be empty",
                context="Entire script",
                suggestion="Add script logic",
                fix_example="var variable = value;\nif (condition) { /* action */ }"
            ))
        
        return issues
    
    def _check_compatibility_issues(self, script: HaasScript) -> List[str]:
        """Check for common compatibility issues."""
        issues = []
        
        # Generic compatibility checks without hardcoded assumptions
        # This should be configurable based on the actual script platform
        
        # For now, return empty list - compatibility rules should come from configuration
        return issues
    
    def _generate_optimization_recommendations(self, script: HaasScript) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Parameter recommendations
        if len(script.parameters) == 0:
            recommendations.append("Consider adding configurable parameters for flexibility")
        elif len(script.parameters) > 20:
            recommendations.append("Consider reducing number of parameters for simplicity")
        
        # Content recommendations
        if len(script.content.split('\n')) > 200:
            recommendations.append("Consider breaking large script into smaller functions")
        
        # Performance recommendations
        if 'for' in script.content.lower() or 'while' in script.content.lower():
            recommendations.append("Review loops for performance optimization")
        
        return recommendations
    
    def _generate_context_suggestions(self, script: HaasScript, errors: List[CompilationError]) -> List[str]:
        """Generate context-aware suggestions based on script and errors."""
        suggestions = []
        
        if len(errors) == 0:
            suggestions.append("✅ Script compiled successfully - ready for testing")
        else:
            suggestions.append(f"🔧 Fix {len(errors)} compilation error(s) before testing")
        
        # Generic script suggestions without hardcoded function names
        if len(script.parameters) > 0 and 'var' not in script.content:
            suggestions.append("💡 Consider using script parameters in your logic with variable declarations")
        
        return suggestions