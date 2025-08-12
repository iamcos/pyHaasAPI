"""
Core script management functionality for HaasScript operations.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from ..models import (
    HaasScript, ScriptCapabilities, DebugResult, ValidationResult, QuickTestResult,
    ScriptType
)
from ..config import ConfigManager
from ..api_client.haasonline_client import HaasOnlineClient
from ..api_client.request_models import (
    ScriptRecordRequest, DebugTestRequest, QuickTestRequest
)
from ..api_client.response_models import CompilationError
from .debug_validator import ScriptDebugValidator


class ScriptManager:
    """Manages HaasScript lifecycle including loading, modification, debugging, and validation."""
    
    def __init__(self, config_manager: ConfigManager, api_client: HaasOnlineClient):
        """Initialize script manager with configuration and API client.
        
        Args:
            config_manager: Configuration manager instance
            api_client: HaasOnline API client instance
        """
        self.config = config_manager
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Initialize debug validator
        self.debug_validator = ScriptDebugValidator(api_client)
        
        # Cache for loaded scripts
        self._script_cache: Dict[str, HaasScript] = {}
        self._capabilities_cache: Optional[ScriptCapabilities] = None
    
    def load_script(self, script_id: str, force_reload: bool = False) -> HaasScript:
        """Load a HaasScript from the server.
        
        Args:
            script_id: Unique identifier for the script
            force_reload: Whether to bypass cache and reload from server
            
        Returns:
            HaasScript object with content and metadata
            
        Raises:
            ValueError: If script_id is invalid
            ConnectionError: If unable to connect to HaasOnline server
            RuntimeError: If script loading fails
        """
        if not script_id:
            raise ValueError("script_id cannot be empty")
        
        # Check cache first unless force reload
        if not force_reload and script_id in self._script_cache:
            self.logger.debug(f"Returning cached script: {script_id}")
            return self._script_cache[script_id]
        
        self.logger.info(f"Loading script from server: {script_id}")
        
        try:
            # Make actual API call to GET_SCRIPT_RECORD
            request = ScriptRecordRequest(script_id=script_id)
            response = self.api_client.get_script_record(request)
            
            script = HaasScript(
                script_id=response.script_id,
                name=response.name,
                content=response.content,
                parameters=response.parameters,
                script_type=ScriptType(response.script_type),
                created_at=response.created_at,
                modified_at=response.modified_at,
                version=1  # Default version for loaded scripts
            )
            
            # Cache the loaded script
            self._script_cache[script_id] = script
            
            self.logger.info(f"Successfully loaded script: {script.name}")
            return script
            
        except Exception as e:
            self.logger.error(f"Failed to load script {script_id}: {e}")
            raise RuntimeError(f"Script loading failed: {e}")
    
    def debug_script(self, script: HaasScript) -> DebugResult:
        """Debug and compile a HaasScript to check for errors.
        
        Args:
            script: HaasScript to debug
            
        Returns:
            DebugResult with compilation status and messages
        """
        self.logger.info(f"Debugging script: {script.name}")
        
        try:
            # Make actual API call to EXECUTE_DEBUGTEST
            request = DebugTestRequest(
                script_id=script.script_id,
                script_content=script.content,
                parameters=script.parameters
            )
            response = self.api_client.execute_debug_test(request)
            
            # Convert compilation errors to string format for compatibility
            error_messages = [
                f"Line {err.line_number}, Column {err.column}: {err.message}"
                for err in response.errors
            ]
            
            result = DebugResult(
                success=response.success,
                compilation_logs=response.compilation_logs,
                warnings=response.warnings,
                errors=error_messages,
                suggestions=self._generate_error_suggestions(error_messages),
                execution_time=response.execution_time_ms / 1000.0  # Convert to seconds
            )
            
            if result.success:
                self.logger.info(f"Script debug successful: {script.name}")
            else:
                self.logger.warning(f"Script debug found {len(result.errors)} errors in: {script.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Debug execution failed for script {script.name}: {e}")
            return DebugResult(
                success=False,
                compilation_logs=[],
                warnings=[],
                errors=[f"Debug execution failed: {str(e)}"],
                suggestions=["Check script syntax and try again"]
            )
    
    def debug_script_comprehensive(self, script: HaasScript) -> DebugResult:
        """
        Perform comprehensive script debugging with intelligent error analysis.
        
        This method provides enhanced debugging with:
        - Intelligent error pattern matching
        - Context-aware suggestions
        - Static code analysis
        - Performance recommendations
        
        Args:
            script: HaasScript to debug comprehensively
            
        Returns:
            Enhanced DebugResult with intelligent suggestions
        """
        return self.debug_validator.debug_script_comprehensive(script)
    
    def validate_script(self, script: HaasScript) -> ValidationResult:
        """Validate script parameters and logic.
        
        Args:
            script: HaasScript to validate
            
        Returns:
            ValidationResult with validation status and issues
        """
        self.logger.info(f"Validating script: {script.name}")
        
        parameter_errors = {}
        logic_errors = []
        compatibility_issues = []
        recommendations = []
        
        # Validate parameters
        for param_name, param_value in script.parameters.items():
            if param_value is None:
                parameter_errors[param_name] = "Parameter value cannot be None"
            elif isinstance(param_value, str) and not param_value.strip():
                parameter_errors[param_name] = "Parameter value cannot be empty"
        
        # Basic logic validation (would be more sophisticated in real implementation)
        if not script.content.strip():
            logic_errors.append("Script content cannot be empty")
        
        # Generic compatibility checks - no hardcoded assumptions
        
        # Generate recommendations
        if len(script.parameters) == 0:
            recommendations.append("Consider adding configurable parameters for flexibility")
        
        is_valid = len(parameter_errors) == 0 and len(logic_errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            parameter_errors=parameter_errors,
            logic_errors=logic_errors,
            compatibility_issues=compatibility_issues,
            recommendations=recommendations
        )
    
    def validate_script_advanced(self, script: HaasScript) -> ValidationResult:
        """
        Perform advanced script validation with detailed issue analysis.
        
        This method provides enhanced validation with:
        - Advanced parameter validation
        - Script structure analysis
        - Compatibility issue detection
        - Optimization recommendations
        
        Args:
            script: HaasScript to validate
            
        Returns:
            Enhanced ValidationResult with detailed analysis
        """
        return self.debug_validator.validate_script_advanced(script)
    
    def clone_script(self, script_id: str, new_name: Optional[str] = None) -> str:
        """Clone a script for debugging purposes.
        
        This creates a local copy of the script that can be modified without
        affecting the original. Useful for debugging Haas-provided scripts.
        
        Args:
            script_id: ID of script to clone
            new_name: Optional new name for cloned script
            
        Returns:
            ID of the newly cloned script
        """
        original_script = self.load_script(script_id)
        
        if new_name is None:
            new_name = f"{original_script.name}_clone_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate new unique ID for cloned script
        cloned_id = f"clone_{uuid.uuid4().hex[:8]}"
        
        # Create cloned script with new ID and name
        cloned_script = HaasScript(
            script_id=cloned_id,
            name=new_name,
            content=original_script.content,
            parameters=original_script.parameters.copy(),
            script_type=original_script.script_type,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            version=1
        )
        
        # Cache the cloned script
        self._script_cache[cloned_script.script_id] = cloned_script
        
        self.logger.info(f"Cloned script {original_script.name} to {new_name} (ID: {cloned_id})")
        return cloned_script.script_id
    
    def update_parameters(self, script: HaasScript, params: Dict[str, Any]) -> HaasScript:
        """Update script parameters with new values.
        
        Args:
            script: HaasScript to update
            params: New parameter values
            
        Returns:
            Updated HaasScript object
        """
        self.logger.info(f"Updating parameters for script: {script.name}")
        
        # Validate new parameters
        for param_name, param_value in params.items():
            if param_name not in script.parameters:
                self.logger.warning(f"Adding new parameter {param_name} to script {script.name}")
        
        # Update parameters
        script.parameters.update(params)
        script.modified_at = datetime.now()
        script.version += 1
        
        # Update cache
        self._script_cache[script.script_id] = script
        
        self.logger.info(f"Updated {len(params)} parameters for script: {script.name}")
        return script
    
    def get_script_capabilities(self) -> ScriptCapabilities:
        """Get available HaasScript functions, indicators, and syntax information.
        
        This method fetches capabilities dynamically from the HaasOnline API
        or RAG system to avoid hardcoding script-specific information.
        
        Returns:
            ScriptCapabilities with available functions and syntax
        """
        if self._capabilities_cache is not None:
            return self._capabilities_cache
        
        self.logger.info("Loading HaasScript capabilities from API")
        
        try:
            # Try to fetch capabilities from HaasOnline API
            capabilities = self._fetch_capabilities_from_api()
            
            if capabilities is None:
                # Fallback to RAG system or configuration
                capabilities = self._fetch_capabilities_from_rag()
            
            if capabilities is None:
                # Final fallback to minimal capabilities
                self.logger.warning("Could not fetch capabilities, using minimal set")
                capabilities = self._get_minimal_capabilities()
            
            self._capabilities_cache = capabilities
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Failed to load script capabilities: {e}")
            # Return minimal capabilities as fallback
            return self._get_minimal_capabilities()
    
    def _fetch_capabilities_from_api(self) -> Optional[ScriptCapabilities]:
        """Fetch script capabilities from HaasOnline API."""
        try:
            # This would use a hypothetical GET_SCRIPT_CAPABILITIES endpoint
            # or GET_COMMANDS endpoint to get available functions
            self.logger.debug("Attempting to fetch capabilities from HaasOnline API")
            
            # For now, return None to indicate API method not available
            # In a real implementation, this would make an API call
            return None
            
        except Exception as e:
            self.logger.debug(f"API capabilities fetch failed: {e}")
            return None
    
    def _fetch_capabilities_from_rag(self) -> Optional[ScriptCapabilities]:
        """Fetch script capabilities from RAG system."""
        try:
            # This would query the RAG system for HaasScript documentation
            # and extract available functions, indicators, and syntax rules
            self.logger.debug("Attempting to fetch capabilities from RAG system")
            
            # For now, return None to indicate RAG method not implemented
            # In a real implementation, this would query the RAG database
            return None
            
        except Exception as e:
            self.logger.debug(f"RAG capabilities fetch failed: {e}")
            return None
    
    def _get_minimal_capabilities(self) -> ScriptCapabilities:
        """Get minimal script capabilities as fallback."""
        return ScriptCapabilities(
            available_functions=[],  # Empty - will be populated dynamically
            available_indicators=[],  # Empty - will be populated dynamically
            syntax_rules={},  # Empty - will be populated dynamically
            parameter_types={
                "int": int,
                "double": float,
                "string": str,
                "bool": bool
            },
            examples=[]  # Empty - will be populated dynamically
        )
    
    def quick_test_script(
        self, 
        script: HaasScript, 
        account_id: str, 
        market_tag: str, 
        interval: int = 60,
        execution_amount: float = 1.0
    ) -> QuickTestResult:
        """Execute a quick test of the script with minimal data.
        
        Args:
            script: HaasScript to test
            account_id: Account ID for testing
            market_tag: Market tag (e.g., "EXCHANGE_SYMBOL_PAIR")
            interval: Candle interval in minutes
            execution_amount: Execution amount for testing
            
        Returns:
            QuickTestResult with execution data and performance
        """
        self.logger.info(f"Quick testing script: {script.name}")
        
        try:
            # Make actual API call to EXECUTE_QUICKTEST
            request = QuickTestRequest(
                script_id=script.script_id,
                account_id=account_id,
                market_tag=market_tag,
                interval=interval,
                script_content=script.content,
                parameters=script.parameters,
                execution_amount=execution_amount
            )
            response = self.api_client.execute_quick_test(request)
            
            # Convert trade results to trade signals format
            trade_signals = [
                {
                    'type': trade.action.lower(),
                    'price': trade.price,
                    'amount': trade.amount,
                    'timestamp': trade.timestamp.isoformat()
                }
                for trade in response.trades
            ]
            
            result = QuickTestResult(
                success=response.success,
                runtime_data=response.runtime_data,
                execution_logs=response.execution_logs,
                trade_signals=trade_signals,
                performance_summary={
                    'final_balance': response.final_balance,
                    'total_profit_loss': response.total_profit_loss,
                    'total_trades': len(response.trades)
                },
                execution_time=response.execution_time_ms / 1000.0,  # Convert to seconds
                memory_usage=0.0,  # Not provided by API
                error_message=response.error_message
            )
            
            if result.success:
                self.logger.info(f"Quick test successful for script: {script.name}")
            else:
                self.logger.warning(f"Quick test failed for script: {script.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Quick test execution failed for script {script.name}: {e}")
            return QuickTestResult(
                success=False,
                runtime_data={},
                execution_logs=[],
                trade_signals=[],
                performance_summary={},
                execution_time=0.0,
                memory_usage=0.0,
                error_message=str(e)
            )
    
    def quick_test_with_analysis(
        self, 
        script: HaasScript, 
        account_id: str, 
        market_tag: str,
        interval: int = 60
    ) -> Tuple[bool, List[str]]:
        """
        Execute quick test with intelligent runtime analysis.
        
        This method provides enhanced quick testing with:
        - Execution behavior analysis
        - Performance evaluation
        - Runtime error detection
        - Actionable suggestions
        
        Args:
            script: HaasScript to test
            account_id: Account ID for testing
            market_tag: Market tag for testing
            interval: Candle interval in minutes
            
        Returns:
            Tuple of (success, list of analysis messages)
        """
        return self.debug_validator.quick_test_with_analysis(script, account_id, market_tag, interval)
    
    def save_script(self, script: HaasScript) -> bool:
        """Save script changes to local cache.
        
        Note: This saves to local cache only. For Haas-provided scripts,
        use clone_script() first to create a modifiable copy.
        
        Args:
            script: HaasScript to save
            
        Returns:
            True if save successful
        """
        try:
            script.modified_at = datetime.now()
            script.version += 1
            self._script_cache[script.script_id] = script
            
            self.logger.info(f"Saved script to cache: {script.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save script {script.name}: {e}")
            return False
    
    def get_cached_scripts(self) -> List[HaasScript]:
        """Get all scripts currently in cache.
        
        Returns:
            List of cached HaasScript objects
        """
        return list(self._script_cache.values())
    
    def clear_cache(self) -> None:
        """Clear the script cache."""
        self._script_cache.clear()
        self._capabilities_cache = None
        self.logger.info("Script cache cleared")
    
    def validate_parameters(self, script: HaasScript, new_params: Dict[str, Any]) -> Dict[str, str]:
        """Validate new parameter values against script requirements.
        
        Args:
            script: HaasScript to validate parameters for
            new_params: New parameter values to validate
            
        Returns:
            Dictionary of parameter names to error messages (empty if all valid)
        """
        errors = {}
        
        for param_name, param_value in new_params.items():
            # Basic validation
            if param_value is None:
                errors[param_name] = "Parameter value cannot be None"
                continue
            
            # Type validation based on existing parameters
            if param_name in script.parameters:
                existing_value = script.parameters[param_name]
                if existing_value is not None and type(param_value) != type(existing_value):
                    errors[param_name] = f"Parameter type mismatch: expected {type(existing_value).__name__}, got {type(param_value).__name__}"
            
            # Value validation
            if isinstance(param_value, str) and not param_value.strip():
                errors[param_name] = "String parameter cannot be empty"
            elif isinstance(param_value, (int, float)):
                # Generic numeric validation - no assumptions about parameter meaning
                if param_value != param_value:  # Check for NaN
                    errors[param_name] = "Numeric parameter cannot be NaN"
        
        return errors
    
    def _generate_error_suggestions(self, errors: List[str]) -> List[str]:
        """Generate intelligent suggestions for common script errors."""
        suggestions = []
        
        for error in errors:
            error_lower = error.lower()
            
            if 'syntax' in error_lower:
                suggestions.append("Check for missing semicolons, brackets, or quotes")
            elif 'undefined' in error_lower and 'variable' in error_lower:
                suggestions.append("Ensure all variables are declared before use")
            elif 'function' in error_lower and 'not found' in error_lower:
                suggestions.append("Verify function name spelling and availability")
            elif 'parameter' in error_lower:
                suggestions.append("Check parameter types and values")
            else:
                suggestions.append("Review script logic and documentation")
        
        return suggestions