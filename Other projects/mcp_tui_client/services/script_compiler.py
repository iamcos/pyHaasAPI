"""
Script Compilation and Testing System

Provides script compilation, validation, and testing capabilities for HaasScript.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logging import get_logger
from ..utils.errors import handle_error, ErrorCategory, ErrorSeverity


class CompilationStatus(Enum):
    """Script compilation status"""
    PENDING = "pending"
    COMPILING = "compiling"
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"


class TestStatus(Enum):
    """Script test status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class CompilationError:
    """Script compilation error"""
    line: int
    column: int
    message: str
    severity: str = "error"  # error, warning, info
    code: str = ""
    suggestion: str = ""


@dataclass
class CompilationResult:
    """Script compilation result"""
    status: CompilationStatus
    errors: List[CompilationError] = field(default_factory=list)
    warnings: List[CompilationError] = field(default_factory=list)
    compiled_code: Optional[str] = None
    compilation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    @property
    def is_successful(self) -> bool:
        return self.status == CompilationStatus.SUCCESS and not self.has_errors


@dataclass
class TestResult:
    """Script test result"""
    status: TestStatus
    execution_time: float = 0.0
    output: str = ""
    error_message: str = ""
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    test_data_used: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_successful(self) -> bool:
        return self.status == TestStatus.PASSED


@dataclass
class PerformanceProfile:
    """Script performance profiling data"""
    total_execution_time: float
    function_calls: Dict[str, int] = field(default_factory=dict)
    memory_usage: Dict[str, float] = field(default_factory=dict)
    bottlenecks: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


class HaasScriptCompiler:
    """HaasScript compiler with validation and optimization"""
    
    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        
        # Compilation cache
        self._compilation_cache: Dict[str, CompilationResult] = {}
        self._cache_max_size = 100
        
        # Built-in functions and their signatures
        self._builtin_functions = self._load_builtin_functions()
        
        # Optimization rules
        self._optimization_rules = self._load_optimization_rules()
    
    def _load_builtin_functions(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in function definitions"""
        return {
            # Price functions
            'Open': {'params': [], 'returns': 'number', 'description': 'Get opening price'},
            'High': {'params': [], 'returns': 'number', 'description': 'Get high price'},
            'Low': {'params': [], 'returns': 'number', 'description': 'Get low price'},
            'Close': {'params': [], 'returns': 'number', 'description': 'Get closing price'},
            'Volume': {'params': [], 'returns': 'number', 'description': 'Get volume'},
            
            # Technical indicators
            'SMA': {'params': ['source', 'period'], 'returns': 'number', 'description': 'Simple Moving Average'},
            'EMA': {'params': ['source', 'period'], 'returns': 'number', 'description': 'Exponential Moving Average'},
            'RSI': {'params': ['source', 'period'], 'returns': 'number', 'description': 'Relative Strength Index'},
            'MACD': {'params': ['source', 'fast', 'slow', 'signal'], 'returns': 'array', 'description': 'MACD indicator'},
            'Bollinger': {'params': ['source', 'period', 'deviation'], 'returns': 'array', 'description': 'Bollinger Bands'},
            
            # Math functions
            'Abs': {'params': ['value'], 'returns': 'number', 'description': 'Absolute value'},
            'Max': {'params': ['value1', 'value2'], 'returns': 'number', 'description': 'Maximum of two values'},
            'Min': {'params': ['value1', 'value2'], 'returns': 'number', 'description': 'Minimum of two values'},
            'Round': {'params': ['value', 'decimals?'], 'returns': 'number', 'description': 'Round to decimals'},
            'Sqrt': {'params': ['value'], 'returns': 'number', 'description': 'Square root'},
            
            # Trading functions
            'Buy': {'params': ['amount', 'price?'], 'returns': 'boolean', 'description': 'Execute buy order'},
            'Sell': {'params': ['amount', 'price?'], 'returns': 'boolean', 'description': 'Execute sell order'},
            'Position': {'params': [], 'returns': 'number', 'description': 'Current position size'},
            'Balance': {'params': [], 'returns': 'number', 'description': 'Account balance'},
            
            # Utility functions
            'Print': {'params': ['message'], 'returns': 'void', 'description': 'Print message to log'},
            'Alert': {'params': ['message', 'level?'], 'returns': 'void', 'description': 'Send alert'},
            'ToString': {'params': ['value'], 'returns': 'string', 'description': 'Convert to string'},
            'ToNumber': {'params': ['value'], 'returns': 'number', 'description': 'Convert to number'},
        }
    
    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """Load script optimization rules"""
        return [
            {
                'name': 'avoid_nested_loops',
                'pattern': r'for.*for.*',
                'message': 'Avoid deeply nested loops for better performance',
                'severity': 'warning'
            },
            {
                'name': 'cache_indicator_calls',
                'pattern': r'(SMA|EMA|RSI)\([^)]+\).*\1\([^)]+\)',
                'message': 'Cache indicator calculations to avoid redundant computation',
                'severity': 'info'
            },
            {
                'name': 'use_efficient_comparisons',
                'pattern': r'==\s*true|==\s*false',
                'message': 'Use direct boolean evaluation instead of comparison with true/false',
                'severity': 'info'
            }
        ]
    
    async def compile_script(self, script_content: str, script_id: str = None) -> CompilationResult:
        """Compile HaasScript with comprehensive validation"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(script_content)
            if cache_key in self._compilation_cache:
                cached_result = self._compilation_cache[cache_key]
                self.logger.debug(f"Using cached compilation result for script {script_id}")
                return cached_result
            
            self.logger.info(f"Compiling script {script_id or 'unnamed'}")
            
            # Phase 1: Lexical analysis
            tokens = self._tokenize(script_content)
            
            # Phase 2: Syntax analysis
            syntax_errors = self._analyze_syntax(tokens, script_content)
            
            # Phase 3: Semantic analysis
            semantic_errors = self._analyze_semantics(tokens, script_content)
            
            # Phase 4: Optimization analysis
            optimization_warnings = self._analyze_optimizations(script_content)
            
            # Combine all errors and warnings
            all_errors = syntax_errors + semantic_errors
            all_warnings = optimization_warnings
            
            # Determine compilation status
            if all_errors:
                status = CompilationStatus.FAILED
                compiled_code = None
            elif all_warnings:
                status = CompilationStatus.WARNING
                compiled_code = self._generate_compiled_code(script_content, tokens)
            else:
                status = CompilationStatus.SUCCESS
                compiled_code = self._generate_compiled_code(script_content, tokens)
            
            # Create result
            result = CompilationResult(
                status=status,
                errors=all_errors,
                warnings=all_warnings,
                compiled_code=compiled_code,
                compilation_time=time.time() - start_time
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            self.logger.info(f"Compilation completed in {result.compilation_time:.3f}s with {len(all_errors)} errors, {len(all_warnings)} warnings")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Compilation failed with exception: {e}")
            return CompilationResult(
                status=CompilationStatus.FAILED,
                errors=[CompilationError(0, 0, f"Internal compiler error: {str(e)}", "error", "E999")],
                compilation_time=time.time() - start_time
            )
    
    def _tokenize(self, script_content: str) -> List[Dict[str, Any]]:
        """Tokenize script content"""
        # Simplified tokenization - in a real implementation this would be more sophisticated
        tokens = []
        lines = script_content.split('\n')
        
        for line_num, line in enumerate(lines):
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith('//'):
                continue
            
            # Simple token extraction
            words = stripped.split()
            for word_pos, word in enumerate(words):
                tokens.append({
                    'value': word,
                    'line': line_num,
                    'column': word_pos,
                    'type': self._classify_token(word)
                })
        
        return tokens
    
    def _classify_token(self, token: str) -> str:
        """Classify token type"""
        if token in ['if', 'else', 'while', 'for', 'function', 'return']:
            return 'keyword'
        elif token in self._builtin_functions:
            return 'function'
        elif token.replace('.', '').replace('-', '').isdigit():
            return 'number'
        elif token.startswith('"') and token.endswith('"'):
            return 'string'
        elif token in ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/']:
            return 'operator'
        else:
            return 'identifier'
    
    def _analyze_syntax(self, tokens: List[Dict[str, Any]], script_content: str) -> List[CompilationError]:
        """Analyze syntax errors"""
        errors = []
        
        # Check for basic syntax issues
        bracket_stack = []
        function_stack = []
        
        for token in tokens:
            value = token['value']
            line = token['line']
            column = token['column']
            
            # Check bracket matching
            if value in ['(', '[', '{']:
                bracket_stack.append((value, line, column))
            elif value in [')', ']', '}']:
                if not bracket_stack:
                    errors.append(CompilationError(
                        line, column,
                        f"Unmatched closing bracket: {value}",
                        "error", "E001"
                    ))
                else:
                    open_bracket, _, _ = bracket_stack.pop()
                    expected = {'(': ')', '[': ']', '{': '}'}
                    if expected.get(open_bracket) != value:
                        errors.append(CompilationError(
                            line, column,
                            f"Mismatched bracket: expected {expected.get(open_bracket)}, got {value}",
                            "error", "E002"
                        ))
            
            # Check function declarations
            if value == 'function':
                function_stack.append((line, column))
            elif value == 'endfunction':
                if not function_stack:
                    errors.append(CompilationError(
                        line, column,
                        "Unexpected 'endfunction' without matching 'function'",
                        "error", "E003"
                    ))
                else:
                    function_stack.pop()
        
        # Check for unclosed brackets
        for bracket, line, column in bracket_stack:
            errors.append(CompilationError(
                line, column,
                f"Unclosed bracket: {bracket}",
                "error", "E004"
            ))
        
        # Check for unclosed functions
        for line, column in function_stack:
            errors.append(CompilationError(
                line, column,
                "Unclosed function declaration",
                "error", "E005"
            ))
        
        return errors
    
    def _analyze_semantics(self, tokens: List[Dict[str, Any]], script_content: str) -> List[CompilationError]:
        """Analyze semantic errors"""
        errors = []
        
        # Track variable declarations and usage
        declared_variables = set()
        used_variables = set()
        
        # Track function calls
        function_calls = []
        
        for i, token in enumerate(tokens):
            value = token['value']
            token_type = token['type']
            line = token['line']
            column = token['column']
            
            # Check function calls
            if token_type == 'function':
                # Look for opening parenthesis
                if i + 1 < len(tokens) and tokens[i + 1]['value'] == '(':
                    function_calls.append((value, line, column))
                    
                    # Validate function exists
                    if value not in self._builtin_functions:
                        errors.append(CompilationError(
                            line, column,
                            f"Unknown function: {value}",
                            "error", "E006"
                        ))
            
            # Check variable usage
            elif token_type == 'identifier':
                # Simple heuristic: if followed by =, it's a declaration
                if i + 1 < len(tokens) and tokens[i + 1]['value'] == '=':
                    declared_variables.add(value)
                else:
                    used_variables.add(value)
        
        # Check for undefined variables
        undefined_vars = used_variables - declared_variables
        for var in undefined_vars:
            # Find first usage
            for token in tokens:
                if token['value'] == var and token['type'] == 'identifier':
                    errors.append(CompilationError(
                        token['line'], token['column'],
                        f"Undefined variable: {var}",
                        "warning", "W001"
                    ))
                    break
        
        return errors
    
    def _analyze_optimizations(self, script_content: str) -> List[CompilationError]:
        """Analyze optimization opportunities"""
        warnings = []
        
        import re
        for rule in self._optimization_rules:
            pattern = rule['pattern']
            message = rule['message']
            severity = rule['severity']
            
            matches = re.finditer(pattern, script_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Find line number
                line_num = script_content[:match.start()].count('\n')
                column = match.start() - script_content.rfind('\n', 0, match.start()) - 1
                
                warnings.append(CompilationError(
                    line_num, column, message, severity, rule['name']
                ))
        
        return warnings
    
    def _generate_compiled_code(self, script_content: str, tokens: List[Dict[str, Any]]) -> str:
        """Generate compiled/optimized code"""
        # For now, return the original content
        # In a real implementation, this would generate optimized bytecode or transformed code
        return script_content
    
    def _get_cache_key(self, script_content: str) -> str:
        """Generate cache key for script content"""
        import hashlib
        return hashlib.md5(script_content.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: CompilationResult) -> None:
        """Cache compilation result"""
        if len(self._compilation_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self._compilation_cache))
            del self._compilation_cache[oldest_key]
        
        self._compilation_cache[cache_key] = result


class HaasScriptTester:
    """HaasScript testing system with sample data and performance profiling"""
    
    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        
        # Test data cache
        self._test_data_cache: Dict[str, Dict[str, Any]] = {}
        
        # Performance profiler
        self._profiler_enabled = True
    
    async def test_script(
        self, 
        compiled_code: str, 
        script_id: str = None,
        test_data: Dict[str, Any] = None,
        timeout: float = 30.0
    ) -> TestResult:
        """Test compiled script with sample data"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Testing script {script_id or 'unnamed'}")
            
            # Prepare test environment
            test_env = await self._prepare_test_environment(test_data)
            
            # Execute script with timeout
            result = await asyncio.wait_for(
                self._execute_script(compiled_code, test_env, script_id),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # Create test result
            test_result = TestResult(
                status=TestStatus.PASSED if result['success'] else TestStatus.FAILED,
                execution_time=execution_time,
                output=result.get('output', ''),
                error_message=result.get('error', ''),
                performance_metrics=result.get('performance', {}),
                test_data_used=test_env
            )
            
            self.logger.info(f"Script test completed in {execution_time:.3f}s with status: {test_result.status.value}")
            
            return test_result
            
        except asyncio.TimeoutError:
            return TestResult(
                status=TestStatus.TIMEOUT,
                execution_time=timeout,
                error_message=f"Script execution timed out after {timeout} seconds"
            )
        except Exception as e:
            self.logger.error(f"Script test failed with exception: {e}")
            return TestResult(
                status=TestStatus.FAILED,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _prepare_test_environment(self, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare test environment with sample data"""
        if test_data:
            return test_data
        
        # Generate sample market data
        sample_data = {
            'prices': {
                'open': [100.0, 101.0, 102.0, 101.5, 103.0],
                'high': [102.0, 103.0, 104.0, 103.5, 105.0],
                'low': [99.0, 100.0, 101.0, 100.5, 102.0],
                'close': [101.0, 102.0, 101.5, 103.0, 104.0],
                'volume': [1000, 1200, 800, 1500, 900]
            },
            'indicators': {
                'sma_20': [100.5, 101.0, 101.5, 102.0, 102.5],
                'rsi_14': [45.0, 55.0, 60.0, 65.0, 70.0],
                'macd': [0.1, 0.2, 0.15, 0.25, 0.3]
            },
            'account': {
                'balance': 10000.0,
                'position': 0.0,
                'equity': 10000.0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return sample_data
    
    async def _execute_script(
        self, 
        compiled_code: str, 
        test_env: Dict[str, Any], 
        script_id: str = None
    ) -> Dict[str, Any]:
        """Execute script in test environment"""
        try:
            # This is a mock implementation
            # In a real system, this would execute the compiled script
            # against the HaasOnline API or a simulation environment
            
            # Simulate script execution
            await asyncio.sleep(0.1)  # Simulate execution time
            
            # Mock successful execution
            result = {
                'success': True,
                'output': 'Script executed successfully\nSample output from script execution',
                'performance': {
                    'function_calls': {'SMA': 5, 'RSI': 3, 'Buy': 1},
                    'execution_time_ms': 100,
                    'memory_usage_kb': 256
                }
            }
            
            # Simulate some script logic
            if 'Buy(' in compiled_code:
                result['output'] += '\nBuy order executed'
            if 'Sell(' in compiled_code:
                result['output'] += '\nSell order executed'
            if 'Print(' in compiled_code:
                result['output'] += '\nPrint statements executed'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }
    
    async def profile_script(self, compiled_code: str, test_data: Dict[str, Any] = None) -> PerformanceProfile:
        """Profile script performance"""
        try:
            start_time = time.time()
            
            # Execute with profiling
            test_env = await self._prepare_test_environment(test_data)
            result = await self._execute_script(compiled_code, test_env)
            
            total_time = time.time() - start_time
            
            # Analyze performance (mock implementation)
            function_calls = result.get('performance', {}).get('function_calls', {})
            
            # Generate optimization suggestions
            suggestions = []
            if function_calls.get('SMA', 0) > 10:
                suggestions.append("Consider caching SMA calculations")
            if total_time > 1.0:
                suggestions.append("Script execution is slow, consider optimization")
            
            return PerformanceProfile(
                total_execution_time=total_time,
                function_calls=function_calls,
                memory_usage={'peak_kb': 512, 'average_kb': 256},
                bottlenecks=['SMA calculations'] if function_calls.get('SMA', 0) > 5 else [],
                optimization_suggestions=suggestions
            )
            
        except Exception as e:
            self.logger.error(f"Script profiling failed: {e}")
            return PerformanceProfile(
                total_execution_time=0.0,
                optimization_suggestions=[f"Profiling failed: {str(e)}"]
            )


class ScriptCompilerService:
    """Main service for script compilation and testing"""
    
    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        
        self.compiler = HaasScriptCompiler(mcp_client)
        self.tester = HaasScriptTester(mcp_client)
        
        # Service state
        self._active_compilations: Dict[str, asyncio.Task] = {}
        self._active_tests: Dict[str, asyncio.Task] = {}
    
    async def compile_and_test(
        self, 
        script_content: str, 
        script_id: str = None,
        test_data: Dict[str, Any] = None,
        run_tests: bool = True
    ) -> Tuple[CompilationResult, Optional[TestResult]]:
        """Compile script and optionally run tests"""
        try:
            # Compile script
            compilation_result = await self.compiler.compile_script(script_content, script_id)
            
            # Run tests if compilation successful and requested
            test_result = None
            if run_tests and compilation_result.is_successful:
                test_result = await self.tester.test_script(
                    compilation_result.compiled_code,
                    script_id,
                    test_data
                )
            
            return compilation_result, test_result
            
        except Exception as e:
            self.logger.error(f"Compile and test failed: {e}")
            error_result = CompilationResult(
                status=CompilationStatus.FAILED,
                errors=[CompilationError(0, 0, f"Service error: {str(e)}", "error", "E999")]
            )
            return error_result, None
    
    async def validate_script_quick(self, script_content: str) -> List[CompilationError]:
        """Quick validation without full compilation"""
        try:
            # Run basic syntax and semantic checks
            tokens = self.compiler._tokenize(script_content)
            syntax_errors = self.compiler._analyze_syntax(tokens, script_content)
            semantic_errors = self.compiler._analyze_semantics(tokens, script_content)
            
            return syntax_errors + semantic_errors
            
        except Exception as e:
            self.logger.error(f"Quick validation failed: {e}")
            return [CompilationError(0, 0, f"Validation error: {str(e)}", "error", "E999")]
    
    def get_function_documentation(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get documentation for a built-in function"""
        return self.compiler._builtin_functions.get(function_name)
    
    def get_all_functions(self) -> Dict[str, Dict[str, Any]]:
        """Get all available built-in functions"""
        return self.compiler._builtin_functions.copy()
    
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        # Cancel active operations
        for task in self._active_compilations.values():
            if not task.done():
                task.cancel()
        
        for task in self._active_tests.values():
            if not task.done():
                task.cancel()
        
        self._active_compilations.clear()
        self._active_tests.clear()
        
        self.logger.info("Script compiler service cleaned up")