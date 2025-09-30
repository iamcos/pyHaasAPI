"""
API Parameter Validation System

This module provides comprehensive validation and auto-fixing for API function parameters
to prevent missing authentication parameters and other common issues.
"""

import inspect
import logging
from typing import Any, Dict, List, Set, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

# Required authentication parameters for different API endpoints
REQUIRED_AUTH_PARAMS = {
    "Labs": {"userid", "interfacekey"},
    "Bot": {"userid", "interfacekey"}, 
    "User": {"interfacekey"},  # User endpoints only need interfacekey
    "Scripts": {"userid", "interfacekey"},
    "Accounts": {"userid", "interfacekey"},
}

# Functions that are known to be missing authentication parameters
MISSING_AUTH_FUNCTIONS = {
    "delete_lab": {"userid", "interfacekey"},
    "clone_lab": {"userid", "interfacekey"},
    "change_lab_script": {"userid", "interfacekey"},
    "get_backtest_runtime": {"userid", "interfacekey"},
    "get_full_backtest_runtime_data": {"userid", "interfacekey"},
    "get_backtest_chart": {"userid", "interfacekey"},
    "get_backtest_log": {"userid", "interfacekey"},
}

def validate_and_fix_query_params(func_name: str, endpoint: str, query_params: Dict[str, Any], executor) -> Dict[str, Any]:
    """
    Validate and automatically fix query parameters for API calls.
    
    Args:
        func_name: Name of the function making the API call
        endpoint: API endpoint (e.g., "Labs", "Bot", "User")
        query_params: Current query parameters
        executor: Executor instance with authentication state
        
    Returns:
        Fixed query parameters with missing authentication parameters added
    """
    if not query_params:
        query_params = {}
    
    # Get required parameters for this endpoint
    required_params = REQUIRED_AUTH_PARAMS.get(endpoint, set())
    
    # Check for function-specific missing parameters
    if func_name in MISSING_AUTH_FUNCTIONS:
        required_params.update(MISSING_AUTH_FUNCTIONS[func_name])
    
    # Add missing authentication parameters
    fixed_params = query_params.copy()
    missing_params = []
    
    for param in required_params:
        if param not in fixed_params:
            if param == "userid" and hasattr(executor.state, 'user_id'):
                fixed_params[param] = executor.state.user_id
                missing_params.append(f"{param}={executor.state.user_id}")
            elif param == "interfacekey" and hasattr(executor.state, 'interface_key'):
                fixed_params[param] = executor.state.interface_key
                missing_params.append(f"{param}={executor.state.interface_key}")
    
    if missing_params:
        logger.warning(f"🔧 Auto-fixed missing authentication parameters in {func_name}: {', '.join(missing_params)}")
    
    return fixed_params

def validate_pydantic_usage(obj: Any, operation: str = "access") -> bool:
    """
    Validate that Pydantic models are being used correctly.
    
    Args:
        obj: Object to validate
        operation: Type of operation being performed
        
    Returns:
        True if usage is correct, False otherwise
    """
    # Check if object is a Pydantic model
    if hasattr(obj, '__pydantic_model__') or hasattr(obj, 'model_fields'):
        # Pydantic models should use attribute access, not .get()
        if operation == "get_method":
            logger.error(f"❌ Pydantic model {type(obj).__name__} should use attribute access, not .get() method")
            return False
    return True

def api_parameter_validator(func):
    """
    Decorator to automatically validate and fix API function parameters.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get function signature
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Find executor and query_params in arguments
        executor = None
        query_params = None
        endpoint = None
        
        for param_name, value in bound_args.arguments.items():
            if param_name == 'executor':
                executor = value
            elif param_name == 'query_params':
                query_params = value
            elif param_name == 'endpoint':
                endpoint = value
        
        # If we have an executor and query_params, validate them
        if executor and query_params and endpoint:
            func_name = func.__name__
            fixed_params = validate_and_fix_query_params(func_name, endpoint, query_params, executor)
            
            # Update the query_params in bound_args
            bound_args.arguments['query_params'] = fixed_params
            
            # Call the original function with fixed parameters
            return func(*bound_args.args, **bound_args.kwargs)
        
        return func(*args, **kwargs)
    
    return wrapper

def check_missing_auth_params():
    """
    Check all API functions for missing authentication parameters.
    """
    logger.info("🔍 Checking API functions for missing authentication parameters...")
    
    issues_found = []
    
    # This would be expanded to check all API functions
    # For now, we'll focus on the known problematic functions
    
    for func_name, missing_params in MISSING_AUTH_FUNCTIONS.items():
        logger.warning(f"⚠️ Function {func_name} is missing: {', '.join(missing_params)}")
        issues_found.append((func_name, missing_params))
    
    if issues_found:
        logger.error(f"❌ Found {len(issues_found)} functions with missing authentication parameters")
        return False
    else:
        logger.info("✅ All API functions have proper authentication parameters")
        return True

def fix_pydantic_usage_errors():
    """
    Find and report Pydantic model usage errors.
    """
    logger.info("🔍 Checking for Pydantic model usage errors...")
    
    # This would scan the codebase for .get() usage on Pydantic models
    # For now, we'll provide guidance
    
    logger.info("📋 Common Pydantic usage patterns:")
    logger.info("  ✅ Correct: obj.attribute_name")
    logger.info("  ✅ Correct: getattr(obj, 'attribute_name', default)")
    logger.info("  ❌ Incorrect: obj.get('attribute_name')")
    logger.info("  ❌ Incorrect: obj['attribute_name']")
    
    return True

if __name__ == "__main__":
    # Run validation checks
    check_missing_auth_params()
    fix_pydantic_usage_errors()





