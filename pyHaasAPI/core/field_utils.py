"""
Safe Field Access Utilities for pyHaasAPI v2

This module provides utilities for safe field access to prevent the 50% of runtime errors
caused by improper field mapping on API response objects.

CRITICAL: API response objects are NOT dictionaries - they are objects with attributes.
Use getattr() and hasattr() instead of .get() for all API response objects.
"""

from typing import Any, Optional, Dict, List, Union
from ..core.logging import get_logger

logger = get_logger("field_utils")


def safe_get_field(obj: Any, field_name: str, default: Any = None, required: bool = False) -> Any:
    """
    Safely get field from API object with proper error handling.
    
    This is the PRIMARY function for accessing API response fields.
    Use this instead of .get() on API response objects.
    
    Args:
        obj: API response object (NOT a dictionary)
        field_name: Name of the field to access
        default: Default value if field is missing
        required: Whether the field is required (raises error if missing)
        
    Returns:
        Field value or default
        
    Raises:
        ValueError: If required field is missing
    """
    if hasattr(obj, field_name):
        value = getattr(obj, field_name)
        if value is None and required:
            logger.error(f"Required field '{field_name}' is None in {type(obj).__name__}")
            raise ValueError(f"Required field '{field_name}' is None")
        return value
    else:
        if required:
            logger.error(f"Required field '{field_name}' missing from {type(obj).__name__}")
            raise ValueError(f"Required field '{field_name}' not found")
        else:
            logger.warning(f"Optional field '{field_name}' missing from {type(obj).__name__}")
            return default


def safe_get_nested_field(obj: Any, path: str, default: Any = None) -> Any:
    """
    Safely get nested field with path validation.
    
    Args:
        obj: API response object
        path: Dot-separated path to nested field (e.g., "settings.market_tag")
        default: Default value if path is broken
        
    Returns:
        Nested field value or default
    """
    current = obj
    for attr in path.split('.'):
        if hasattr(current, attr):
            current = getattr(current, attr)
        else:
            logger.warning(f"Path '{path}' broken at '{attr}' in {type(current).__name__}")
            return default
    return current


def safe_get_dict_field(data: Dict[str, Any], field_name: str, default: Any = None, required: bool = False) -> Any:
    """
    Safely get field from dictionary data.
    
    Use this for actual dictionary data, not API response objects.
    
    Args:
        data: Dictionary data
        field_name: Name of the field to access
        default: Default value if field is missing
        required: Whether the field is required
        
    Returns:
        Field value or default
        
    Raises:
        ValueError: If required field is missing
    """
    if field_name in data:
        value = data[field_name]
        if value is None and required:
            logger.error(f"Required field '{field_name}' is None in dictionary")
            raise ValueError(f"Required field '{field_name}' is None")
        return value
    else:
        if required:
            logger.error(f"Required field '{field_name}' missing from dictionary")
            raise ValueError(f"Required field '{field_name}' not found")
        else:
            logger.warning(f"Optional field '{field_name}' missing from dictionary")
            return default


def validate_api_response(response: Any, required_fields: Optional[List[str]] = None) -> bool:
    """
    Validate API response has required fields.
    
    Args:
        response: API response object
        required_fields: List of required field names
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If required fields are missing
    """
    if required_fields:
        for field in required_fields:
            if not hasattr(response, field):
                logger.error(f"Required field '{field}' missing from API response")
                raise ValueError(f"Required field '{field}' not found")
    return True


def map_api_response_to_model(api_data: Any, model_class: type, field_mapping: Optional[Dict[str, str]] = None) -> Any:
    """
    Map API response to Pydantic model with field mapping.
    
    Args:
        api_data: API response object
        model_class: Pydantic model class
        field_mapping: Mapping from model fields to API fields
        
    Returns:
        Instantiated model object
    """
    if field_mapping:
        mapped_data = {}
        for model_field, api_field in field_mapping.items():
            mapped_data[model_field] = safe_get_field(api_data, api_field)
        return model_class(**mapped_data)
    else:
        # Direct mapping - assumes field names match
        model_data = {}
        for field_name in model_class.__fields__.keys():
            model_data[field_name] = safe_get_field(api_data, field_name)
        return model_class(**model_data)


def safe_get_market_tag(lab_data: Any) -> str:
    """
    Safely extract market tag from lab data with comprehensive fallback logic.
    
    This addresses the most common field mapping issue in the codebase.
    
    Args:
        lab_data: Lab data object
        
    Returns:
        Market tag string or empty string
    """
    # Try multiple field paths for market tag
    market_tag_paths = [
        "ST.marketTag",
        "ST.market_tag", 
        "ST.market",
        "marketTag",
        "market_tag",
        "market"
    ]
    
    for path in market_tag_paths:
        try:
            if '.' in path:
                # Nested field
                market_tag = safe_get_nested_field(lab_data, path)
            else:
                # Direct field
                market_tag = safe_get_field(lab_data, path)
            
            if market_tag and market_tag.strip():
                logger.debug(f"Found market tag: {market_tag} via path: {path}")
                return market_tag.strip()
        except Exception as e:
            logger.debug(f"Failed to get market tag via path {path}: {e}")
            continue
    
    logger.warning("Market tag not found in lab data")
    return ""


def safe_get_account_id(lab_data: Any) -> str:
    """
    Safely extract account ID from lab data with fallback logic.
    
    Args:
        lab_data: Lab data object
        
    Returns:
        Account ID string or empty string
    """
    account_id_paths = [
        "ST.accountId",
        "ST.account_id",
        "accountId",
        "account_id"
    ]
    
    for path in account_id_paths:
        try:
            if '.' in path:
                account_id = safe_get_nested_field(lab_data, path)
            else:
                account_id = safe_get_field(lab_data, path)
            
            if account_id and account_id.strip():
                logger.debug(f"Found account ID: {account_id} via path: {path}")
                return account_id.strip()
        except Exception as e:
            logger.debug(f"Failed to get account ID via path {path}: {e}")
            continue
    
    logger.warning("Account ID not found in lab data")
    return ""


def safe_get_status(response: Any) -> str:
    """
    Safely extract status from API response.
    
    Args:
        response: API response object
        
    Returns:
        Status string or "UNKNOWN"
    """
    status = safe_get_field(response, "status", "UNKNOWN")
    if status == "UNKNOWN":
        logger.warning(f"Status unknown for {type(response).__name__}")
    return status


def safe_get_success_flag(response: Any) -> bool:
    """
    Safely extract success flag from API response.
    
    Args:
        response: API response object
        
    Returns:
        True if successful, False otherwise
    """
    # Check if response has Success field
    success = safe_get_field(response, "Success", None)
    if success is not None:
        # Response has Success field - use it
        if not success:
            error_msg = safe_get_field(response, "Error", "Unknown error")
            logger.warning(f"API request failed: {error_msg}")
        return success
    
    # No Success field - check if response has data (indicates success)
    data = safe_get_field(response, "Data", None)
    if data is not None:
        # Response has Data field - assume success
        logger.debug("API response has Data field, assuming success")
        return True
    
    # Check if response is a list or dict with content (direct data response)
    if isinstance(response, (list, dict)) and response:
        logger.debug("API response is direct data, assuming success")
        return True
    
    # No success indicators found
    logger.warning("API response has no success indicators")
    return False


def log_field_mapping_issues(obj: Any, context: str = "") -> None:
    """
    Log field mapping issues for debugging.
    
    Args:
        obj: Object to inspect
        context: Context for logging
    """
    if hasattr(obj, '__dict__'):
        available_fields = list(obj.__dict__.keys())
        logger.debug(f"Available fields in {type(obj).__name__} {context}: {available_fields}")
    else:
        logger.debug(f"Object {type(obj).__name__} {context} has no __dict__ attribute")


# Field mapping constants for common API fields
API_FIELD_MAPPING = {
    # Lab fields
    "lab_id": ["LID", "labId", "lab_id"],
    "name": ["N", "name", "lab_name"],
    "script_id": ["SID", "scriptId", "script_id"],
    "script_name": ["SN", "scriptName", "script_name"],
    "status": ["S", "status", "lab_status"],
    "config": ["C", "config", "lab_config"],
    "settings": ["ST", "settings", "lab_settings"],
    
    # Bot fields
    "bot_id": ["BID", "botId", "bot_id"],
    "bot_name": ["BN", "botName", "bot_name"],
    "account_id": ["AID", "accountId", "account_id"],
    "market_tag": ["MT", "marketTag", "market_tag"],
    "leverage": ["L", "leverage", "bot_leverage"],
    "position_mode": ["PM", "positionMode", "position_mode"],
    "margin_mode": ["MM", "marginMode", "margin_mode"],
    
    # Account fields
    "exchange": ["E", "exchange", "account_exchange"],
    "type": ["T", "type", "account_type"],
    "wallets": ["B", "wallets", "balances"],
    "balance": ["BAL", "balance", "account_balance"]
}


def get_field_variants(field_name: str) -> List[str]:
    """
    Get all possible field name variants for a given field.
    
    Args:
        field_name: Base field name
        
    Returns:
        List of possible field name variants
    """
    return API_FIELD_MAPPING.get(field_name, [field_name])


def safe_get_field_with_variants(obj: Any, field_name: str, default: Any = None) -> Any:
    """
    Safely get field trying multiple variants.
    
    Args:
        obj: API response object
        field_name: Base field name
        default: Default value
        
    Returns:
        Field value or default
    """
    variants = get_field_variants(field_name)
    
    for variant in variants:
        try:
            value = safe_get_field(obj, variant)
            if value is not None:
                logger.debug(f"Found field '{field_name}' as '{variant}'")
                return value
        except Exception:
            continue
    
    logger.warning(f"Field '{field_name}' not found in any variant: {variants}")
    return default
