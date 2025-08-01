"""
Enhanced Bot Editing API Functions

This module provides comprehensive bot editing capabilities including:
- Individual parameter editing
- Group-based parameter editing  
- Parameter validation
- Comprehensive bot data retrieval
- Closed positions retrieval
"""

import logging
from typing import Any, Dict, List
from .api import (
    get_bot, get_bot_runtime, get_bot_runtime_logbook, 
    get_bot_script_parameters, edit_bot_parameter, HaasApiError,
    SyncExecutor, Authenticated, HaasBot
)

log = logging.getLogger(__name__)


def get_bot_closed_positions(executor: SyncExecutor[Authenticated], bot_id: str, next_page_id: int = -1, page_length: int = 250) -> list[dict]:
    """
    Get closed positions for a bot.

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        next_page_id: For pagination, default -1 (start)
        page_length: Number of positions to fetch, default 250

    Returns:
        List of closed position dictionaries
    """
    response = executor.execute(
        endpoint="Bot",
        response_type=dict,
        query_params={
            "channel": "GET_RUNTIME_CLOSED_POSITIONS",
            "botid": bot_id,
            "nextpageid": next_page_id,
            "pagelength": page_length,
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )
    return response.get("Data", [])


def get_comprehensive_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> dict:
    """
    Get a comprehensive bot object combining all data sources.
    This mimics what the web interface does by combining:
    - GET_BOT (basic info)
    - GET_RUNTIME (runtime data + parameters)
    - GET_RUNTIME_LOGBOOK (logs)
    - GET_RUNTIME_CLOSED_POSITIONS (closed positions)

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot

    Returns:
        Comprehensive bot dictionary with all available data
    """
    try:
        # Get basic bot info
        basic_bot = get_bot(executor, bot_id)
        
        # Get runtime data (includes script parameters)
        runtime_data = get_bot_runtime(executor, bot_id)
        
        # Get recent logs
        logs = get_bot_runtime_logbook(executor, bot_id, page_length=50)
        
        # Get closed positions
        closed_positions = get_bot_closed_positions(executor, bot_id)
        
        # Combine all data
        comprehensive_bot = {
            "basic_info": basic_bot.model_dump() if hasattr(basic_bot, 'model_dump') else basic_bot,
            "runtime_data": runtime_data,
            "recent_logs": logs,
            "closed_positions": closed_positions,
            "script_parameters": runtime_data.get("InputFields", {}),
            "bot_id": bot_id
        }
        
        return comprehensive_bot
        
    except Exception as e:
        log.error(f"Failed to get comprehensive bot data for {bot_id}: {e}")
        raise HaasApiError(f"Failed to get comprehensive bot data: {e}")


def edit_bot_parameter_by_name(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    parameter_name: str, 
    new_value: Any
) -> HaasBot:
    """
    Edit a single bot parameter by its human-readable name.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        parameter_name: Human-readable parameter name (e.g., "Stop Loss (%)")
        new_value: New value for the parameter
        
    Returns:
        Updated HaasBot object
        
    Raises:
        HaasApiError: If parameter not found or update fails
    """
    # Get current bot and parameters
    bot = get_bot(executor, bot_id)
    script_params = get_bot_script_parameters(executor, bot_id)
    
    # Find parameter by name
    param_key = None
    param_details = None
    
    for key, details in script_params.items():
        if isinstance(details, dict) and details.get("N") == parameter_name:
            param_key = key
            param_details = details
            break
    
    if not param_key:
        available_params = [details.get("N", "Unknown") for details in script_params.values() 
                          if isinstance(details, dict)]
        raise HaasApiError(f"Parameter '{parameter_name}' not found. Available parameters: {available_params}")
    
    # Validate value against constraints
    param_type = param_details.get("T")
    min_val = param_details.get("MIN")
    max_val = param_details.get("MAX")
    
    # Type conversion and validation
    try:
        if param_type == 0:  # Numeric
            new_value = float(new_value)
            if min_val is not None and new_value < min_val:
                raise ValueError(f"Value {new_value} is below minimum {min_val}")
            if max_val is not None and new_value > max_val:
                raise ValueError(f"Value {new_value} is above maximum {max_val}")
        elif param_type == 2:  # Boolean
            if isinstance(new_value, str):
                new_value = new_value.lower() == "true"
        elif param_type == 3:  # Options/Enum
            options = param_details.get("O", {})
            if new_value not in options:
                raise ValueError(f"Value '{new_value}' not in available options: {list(options.keys())}")
    except ValueError as e:
        raise HaasApiError(f"Parameter validation failed: {e}")
    
    # Update the parameter in the bot's settings
    if not bot.settings.script_parameters:
        bot.settings.script_parameters = {}
    
    # Use the full key for the update
    full_key = param_details.get("K", param_key)
    bot.settings.script_parameters[full_key] = new_value
    
    # Apply the update
    return edit_bot_parameter(executor, bot)


def edit_bot_parameters_by_group(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    group_name: str, 
    parameters: Dict[str, Any]
) -> HaasBot:
    """
    Edit multiple bot parameters that belong to the same group.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        group_name: Name of the parameter group (e.g., "MadHatter BBands")
        parameters: Dictionary of parameter names to new values
        
    Returns:
        Updated HaasBot object
        
    Raises:
        HaasApiError: If group not found or any parameter update fails
    """
    # Get current bot and parameters
    bot = get_bot(executor, bot_id)
    script_params = get_bot_script_parameters(executor, bot_id)
    
    # Find all parameters in the group
    group_params = {}
    for key, details in script_params.items():
        if isinstance(details, dict) and details.get("G") == group_name:
            param_name = details.get("N")
            if param_name in parameters:
                group_params[key] = details
    
    if not group_params:
        available_groups = set(details.get("G", "") for details in script_params.values() 
                             if isinstance(details, dict))
        raise HaasApiError(f"Group '{group_name}' not found. Available groups: {list(available_groups)}")
    
    # Update each parameter
    if not bot.settings.script_parameters:
        bot.settings.script_parameters = {}
    
    for param_key, param_details in group_params.items():
        param_name = param_details.get("N")
        new_value = parameters[param_name]
        
        # Validate value
        param_type = param_details.get("T")
        min_val = param_details.get("MIN")
        max_val = param_details.get("MAX")
        
        try:
            if param_type == 0:  # Numeric
                new_value = float(new_value)
                if min_val is not None and new_value < min_val:
                    raise ValueError(f"Parameter '{param_name}': value {new_value} is below minimum {min_val}")
                if max_val is not None and new_value > max_val:
                    raise ValueError(f"Parameter '{param_name}': value {new_value} is above maximum {max_val}")
            elif param_type == 2:  # Boolean
                if isinstance(new_value, str):
                    new_value = new_value.lower() == "true"
            elif param_type == 3:  # Options/Enum
                options = param_details.get("O", {})
                if new_value not in options:
                    raise ValueError(f"Parameter '{param_name}': value '{new_value}' not in available options: {list(options.keys())}")
        except ValueError as e:
            raise HaasApiError(f"Parameter validation failed: {e}")
        
        # Use the full key for the update
        full_key = param_details.get("K", param_key)
        bot.settings.script_parameters[full_key] = new_value
    
    # Apply all updates
    return edit_bot_parameter(executor, bot)


def validate_bot_parameters(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    parameters: Dict[str, Any]
) -> Dict[str, List[str]]:
    """
    Validate parameter values against their constraints without applying changes.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        parameters: Dictionary of parameter names to values to validate
        
    Returns:
        Dictionary with 'valid' and 'invalid' parameter lists
    """
    script_params = get_bot_script_parameters(executor, bot_id)
    
    valid_params = []
    invalid_params = []
    
    for param_name, new_value in parameters.items():
        # Find parameter by name
        param_details = None
        for key, details in script_params.items():
            if isinstance(details, dict) and details.get("N") == param_name:
                param_details = details
                break
        
        if not param_details:
            invalid_params.append(f"Parameter '{param_name}' not found")
            continue
        
        # Validate value
        param_type = param_details.get("T")
        min_val = param_details.get("MIN")
        max_val = param_details.get("MAX")
        
        try:
            if param_type == 0:  # Numeric
                new_value = float(new_value)
                if min_val is not None and new_value < min_val:
                    invalid_params.append(f"'{param_name}': value {new_value} is below minimum {min_val}")
                    continue
                if max_val is not None and new_value > max_val:
                    invalid_params.append(f"'{param_name}': value {new_value} is above maximum {max_val}")
                    continue
            elif param_type == 2:  # Boolean
                if isinstance(new_value, str):
                    new_value = new_value.lower() == "true"
            elif param_type == 3:  # Options/Enum
                options = param_details.get("O", {})
                if new_value not in options:
                    invalid_params.append(f"'{param_name}': value '{new_value}' not in available options: {list(options.keys())}")
                    continue
            
            valid_params.append(param_name)
            
        except ValueError as e:
            invalid_params.append(f"'{param_name}': {e}")
    
    return {
        "valid": valid_params,
        "invalid": invalid_params
    }


def get_bot_parameter_groups(executor: SyncExecutor[Authenticated], bot_id: str) -> Dict[str, List[str]]:
    """
    Get all parameter groups and their parameters for a bot.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        
    Returns:
        Dictionary mapping group names to lists of parameter names
    """
    script_params = get_bot_script_parameters(executor, bot_id)
    
    groups = {}
    for key, details in script_params.items():
        if isinstance(details, dict):
            group_name = details.get("G", "Ungrouped")
            param_name = details.get("N", "Unknown")
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(param_name)
    
    return groups


def get_bot_parameter_metadata(executor: SyncExecutor[Authenticated], bot_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get detailed metadata for all bot parameters including constraints and options.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        
    Returns:
        Dictionary mapping parameter names to their metadata
    """
    script_params = get_bot_script_parameters(executor, bot_id)
    
    metadata = {}
    for key, details in script_params.items():
        if isinstance(details, dict):
            param_name = details.get("N", "Unknown")
            metadata[param_name] = {
                "key": details.get("K", key),
                "type": details.get("T"),
                "min": details.get("MIN"),
                "max": details.get("MAX"),
                "step": details.get("ST"),
                "group": details.get("G"),
                "description": details.get("D"),
                "tooltip": details.get("TT"),
                "options": details.get("O"),
                "current_value": details.get("V"),
                "extended_key": details.get("EK")
            }
    
    return metadata 