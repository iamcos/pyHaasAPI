import dataclasses
import random
import time
from contextlib import contextmanager
from typing import Generator, Iterable, Sequence, List, Dict, Any, Union, Optional
from decimal import Decimal
import logging
import copy

from pyHaasAPI_v1 import api, iterable_extensions
from pyHaasAPI_v1.api import Authenticated, SyncExecutor, get_lab_details, HaasApiError, update_lab_details
from pyHaasAPI_v1.domain import BacktestPeriod
from pyHaasAPI_v1.types import ParameterOption
from pyHaasAPI_v1.model import (
    CreateLabRequest,
    GetBacktestResultRequest,
    PaginatedResponse,
    StartLabExecutionRequest,
    LabBacktestResult,
    LabParameter,
    LabStatus,
    LabSettings,
    LabConfig,
    ScriptParameters,
    LabDetails,
    HaasScriptSettings
)
from pyHaasAPI_v1.tools.utils import fetch_all_lab_backtests
from pyHaasAPI_v1.parameters import ParameterRange, ParameterType
from loguru import logger as log


def generate_traditional_parameter_range(param_name: str, current_value: Union[int, float], param_type: str) -> List[str]:
    """
    Generate traditional linear parameter ranges (Min/Max/Step approach).
    
    This creates simple linear ranges that match what the web interface shows as:
    RSI length23MinMaxStep8Overbought30MinMaxStep13
    
    Args:
        param_name: Name of the parameter for range selection
        current_value: Current parameter value
        param_type: 'integer' or 'decimal'
        
    Returns:
        List of string values for traditional optimization
    """
    param_lower = param_name.lower()
    
    if param_type == 'integer':
        current_val = int(current_value)
        
        # RSI Length traditional range - REDUCED to prevent server overload
        if 'rsi' in param_lower and 'length' in param_lower:
            # Reasonable range: 10 to 25 step 3 (6 values)
            return [str(v) for v in range(10, 26, 3)]  # 10, 13, 16, 19, 22, 25
        
        # Overbought traditional range - REDUCED
        elif 'overbought' in param_lower:
            # Reasonable range: 20 to 35 step 5 (4 values)
            return [str(v) for v in range(20, 36, 5)]  # 20, 25, 30, 35
            
        # Oversold traditional range - REDUCED
        elif 'oversold' in param_lower:
            # Reasonable range: 65 to 80 step 5 (4 values)
            return [str(v) for v in range(65, 81, 5)]  # 65, 70, 75, 80
        
        # Interval traditional range - REDUCED
        elif 'interval' in param_lower:
            # Reasonable range: 1, 5, 15 (3 values)
            return ['1', '5', '15']
        
        # Stoploss traditional range - REDUCED
        elif 'stoploss' in param_lower or 'stop' in param_lower:
            # Reasonable range: 1 to 7 step 2 (4 values)
            return [str(v) for v in range(1, 8, 2)]  # 1, 3, 5, 7
        
        # Generic integer parameter - SAFE traditional linear range
        else:
            # Keep it small - just 4 values around current
            return [str(current_val - 1), str(current_val), str(current_val + 1), str(current_val + 2)]
    
    else:  # decimal
        current_val = float(current_value)
        
        # Traditional decimal range
        start = max(0.1, current_val - 2.0)
        end = current_val + 3.0
        step = 0.2
        values = []
        val = start
        while val <= end:
            values.append(str(round(val, 2)))
            val += step
        return values


def generate_mixed_parameter_range(param_name: str, current_value: Union[int, float], param_type: str) -> List[str]:
    """
    Generate sophisticated mixed parameter ranges with specific values AND ranges.
    
    Examples:
    - RSI Length: [3, 5, 20, *range(40, 55, 2), 11, *range(12, 16, 1)]
    - Overbought: [15, 20, *range(25, 35, 2), 40, *range(70, 85, 5)]
    
    Args:
        param_name: Name of the parameter for intelligent range selection
        current_value: Current parameter value
        param_type: 'integer' or 'decimal'
        
    Returns:
        List of string values for optimization
    """
    param_lower = param_name.lower()
    
    if param_type == 'integer':
        current_val = int(current_value)
        
        # RSI Length optimization
        if 'rsi' in param_lower and 'length' in param_lower:
            # Mix specific proven RSI values with ranges
            specific_values = [5, 9, 14, 21]  # Common RSI periods
            range1 = list(range(10, 18, 2))   # Fine-tune around 14
            range2 = list(range(25, 35, 3))   # Test longer periods
            mixed_list = specific_values + range1 + range2
            return [str(v) for v in sorted(set(mixed_list))]
        
        # Overbought/Oversold levels
        elif 'overbought' in param_lower:
            specific_values = [20, 25, 30]    # Common overbought levels
            range1 = list(range(65, 85, 5))   # Higher sensitivity range
            mixed_list = specific_values + range1
            return [str(v) for v in sorted(set(mixed_list))]
            
        elif 'oversold' in param_lower:
            specific_values = [70, 75, 80]    # Common oversold levels  
            range1 = list(range(15, 35, 5))   # Lower sensitivity range
            mixed_list = specific_values + range1
            return [str(v) for v in sorted(set(mixed_list))]
        
        # Interval/Timeframe optimization
        elif 'interval' in param_lower:
            specific_values = [1, 5, 15, 60]  # Common timeframes (1m, 5m, 15m, 1h)
            range1 = list(range(2, 8, 2))     # Short-term range
            mixed_list = specific_values + range1
            return [str(v) for v in sorted(set(mixed_list))]
        
        # Stoploss optimization
        elif 'stoploss' in param_lower or 'stop' in param_lower:
            specific_values = [1, 2, 3, 5]    # Conservative stops
            range1 = list(range(7, 15, 2))    # Wider stops
            mixed_list = specific_values + range1
            return [str(v) for v in sorted(set(mixed_list))]
        
        # Generic integer parameter
        else:
            specific_values = [current_val]
            range1 = list(range(max(1, current_val - 3), current_val, 1))
            range2 = list(range(current_val + 1, current_val + 8, 2))
            mixed_list = specific_values + range1 + range2
            return [str(v) for v in sorted(set(mixed_list))]
    
    else:  # decimal
        current_val = float(current_value)
        
        # Decimal parameter optimization with mixed approach
        if 'multiplier' in param_lower or 'factor' in param_lower:
            specific_values = [0.5, 1.0, 1.5, 2.0]  # Common multipliers
            range1 = [round(x, 2) for x in [current_val + i * 0.25 for i in range(-2, 3)]]
            mixed_list = specific_values + range1
            return [str(v) for v in sorted(set(mixed_list))]
        
        # Generic decimal parameter
        else:
            specific_values = [current_val]
            range1 = [round(current_val + i * 0.1, 2) for i in range(-5, 6)]
            mixed_list = specific_values + range1
            return [str(v) for v in sorted(set([v for v in mixed_list if v > 0]))]

@dataclasses.dataclass
class ChangeHaasScriptParameterRequest:
    name: str
    options: list[ParameterOption]


def update_params(
    settings: Sequence[LabParameter],
    params: Iterable[ChangeHaasScriptParameterRequest],
):
    for param in params:
        param_name = param.name.lower()
        setting_idx = iterable_extensions.find_idx(
            settings, lambda s: param_name in s.key.lower()
        )

        if setting_idx is None:
            raise ValueError(f"Failed to find setting for changer haas script {param=}")

        settings[setting_idx].options = param.options


def wait_for_execution(executor: SyncExecutor[Authenticated], lab_id: str):
    while True:
        details = api.get_lab_details(executor, lab_id)
        match details.status:
            case LabStatus.COMPLETED:
                break
            case LabStatus.CANCELLED:
                break
            case _:
                pass

        time.sleep(5)


def backtest(
    executor: SyncExecutor[Authenticated], lab_id: str, period: BacktestPeriod
) -> PaginatedResponse[LabBacktestResult]:
    api.start_lab_execution(
        executor,
        StartLabExecutionRequest(
            lab_id=lab_id,
            start_unix=period.start_unix,
            end_unix=period.end_unix,
            send_email=False,
        ),
    )

    wait_for_execution(executor, lab_id)

    # Use centralized fetcher instead of direct API call with wrong page_lenght
    backtests = fetch_all_lab_backtests(executor, lab_id)
    
    # Create a PaginatedResponse-like object to maintain compatibility
    class BacktestResponse:
        def __init__(self, items):
            self.items = items
    
    return BacktestResponse(backtests)


@contextmanager
def get_lab_default_params(
    executor: SyncExecutor[Authenticated], script_id: str
) -> Generator[list[LabParameter], None, None]:
    """
    Creates buffer lab to get its default parameters options

    :param executor: Executor for Haas API interaction
    :param script_id: Script of lab
    :returns: Generator yielding list of LabParameter objects
    """
    accounts = api.get_accounts(executor)
    account = random.choice(accounts)

    markets = api.get_all_markets(executor)
    market = random.choice(markets)

    req = CreateLabRequest(
        script_id=script_id,
        name="buf_lab",
        account_id=account.account_id,
        market=market.market,
        interval=1,
        default_price_data_style="CandleStick",
    )
    lab_details = api.create_lab(executor, req)

    try:

        yield lab_details.parameters
    finally:
        api.delete_lab(executor, lab_details.lab_id)


def parse_parameter_type(param: Dict[str, Any]) -> ParameterType:
    """Determine parameter type from API response"""
    type_code = param.get('T', 3)  # Default to STRING if type not specified
    return ParameterType(type_code)

def get_lab_parameters(executor: SyncExecutor[Authenticated], lab_id: str) -> List[LabParameter]:
    """
    Retrieve and parse lab parameters
    
    Args:
        executor: Authenticated API executor
        lab_id: ID of the lab
        
    Returns:
        List of LabParameter objects
    """
    lab_details = api.get_lab_details(executor, lab_id)
    parameters = []
    
    for param_dict in lab_details.parameters:
        # Parse raw parameter dictionary
        param_type = parse_parameter_type(param_dict)
        
        # Extract options and current value
        options = param_dict.get('O', [])  # Options field from API
        current_value = options[0] if options else None
        
        # Create parameter range based on type
        range_config = None
        if param_type in (ParameterType.INTEGER, ParameterType.DECIMAL):
            if len(options) > 1:
                try:
                    values = [float(x) if param_type == ParameterType.DECIMAL else int(x) for x in options]
                    range_config = ParameterRange(
                        start=min(values),
                        end=max(values),
                        step=values[1] - values[0] if len(values) > 1 else 1
                    )
                except (ValueError, TypeError) as e:
                    log.warning(f"Failed to parse parameter values: {e}")
                    continue
        elif param_type == ParameterType.SELECTION:
            range_config = ParameterRange(selection_values=options)
        
        parameters.append(LabParameter(
            key=param_dict.get('K', ''),  # Key field from API
            type=param_type.value,  # Convert enum to int
            options=options,
            is_enabled=param_dict.get('I', True),
            is_selected=param_dict.get('IS', False)
        ))
    
    return parameters

def update_lab_parameter_ranges_traditional(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    randomize: bool = True
) -> LabDetails:
    """Update parameter ranges for a lab using TRADITIONAL linear ranges (Min/Max/Step approach)."""
    lab_details = get_lab_details(executor, lab_id)

    # --- FIX: Deep copy all settings fields ---
    original_settings = lab_details.settings
    settings_dict = original_settings.model_dump(by_alias=True)

    # Log what we're preserving
    log.info(f"🔧 Preserving settings before TRADITIONAL parameter update:")
    for k, v in settings_dict.items():
        log.info(f"  {k}: {v}")

    # Convert parameters to proper format and validate
    updated_parameters = []
    for param in lab_details.parameters:
        # Handle both dict and object parameters
        if isinstance(param, dict):
            param_dict = param
        elif hasattr(param, 'model_dump'):
            param_dict = param.model_dump()
        else:
            # Fallback for other object types
            param_dict = dict(param) if hasattr(param, '__iter__') else str(param)
        
        # Validate parameter has required fields
        if not all(key in param_dict for key in ['K', 'T', 'O']):
            log.warning(f"⚠️ Skipping invalid parameter: {param_dict}")
            continue
            
        # Generate TRADITIONAL parameter ranges if randomize is enabled
        if randomize and param_dict.get('T') in [0, 1]:  # INTEGER or DECIMAL types
            current_value = param_dict['O'][0] if param_dict['O'] else '0'
            
            # Check if the value is actually numeric (not a boolean or string)
            try:
                # Try to parse as float first to handle both int and decimal
                current_val = float(current_value)
                
                # Skip if it's a boolean value (0.0 or 1.0) or if the original was a string
                if str(current_value).lower() in ['true', 'false'] or param_dict.get('T') == 3:
                    log.info(f"  ⏭️ Skipping non-numeric parameter {param_dict['K']}: {current_value}")
                    updated_parameters.append(param_dict)
                    continue
                
                if param_dict.get('T') == 0:  # INTEGER
                    current_val = int(current_val)
                    new_options = generate_traditional_parameter_range(param_dict['K'], current_val, 'integer')
                else:  # DECIMAL
                    new_options = generate_traditional_parameter_range(param_dict['K'], current_val, 'decimal')
                param_dict['O'] = new_options
                # Enable optimization for this parameter
                param_dict['I'] = True
                log.info(f"  🔧 Generated TRADITIONAL range for {param_dict['K']}: {new_options}")
            except (ValueError, TypeError):
                log.info(f"  ⏭️ Skipping non-numeric parameter {param_dict['K']}: {current_value}")
        
        # Ensure the parameter has the enabled field set properly
        if 'I' not in param_dict:
            param_dict['I'] = len(param_dict.get('O', [])) > 1  # Enable if has multiple options
        
        updated_parameters.append(param_dict)

    if not updated_parameters:
        log.warning("⚠️ No valid parameters found for optimization")
        return lab_details

    # Count how many parameters got ranges
    ranged_params = sum(1 for p in updated_parameters if len(p.get('O', [])) > 1)
    log.info(f"  📊 Total parameters: {len(updated_parameters)}")
    log.info(f"  📊 Parameters with ranges: {ranged_params}")
    log.info(f"  📊 Parameters without ranges: {len(updated_parameters) - ranged_params}")

    try:
        # Step 1: Update parameters directly (simpler approach)
        log.info("🔄 Step 1: Updating TRADITIONAL parameters directly...")
        
        # Convert dictionaries to ScriptParameter objects
        from pyHaasAPI_v1.parameters import ScriptParameter
        script_parameters = []
        for param_dict in updated_parameters:
            script_param = ScriptParameter(
                K=param_dict['K'],
                T=param_dict['T'],
                O=param_dict['O'],
                I=param_dict['I'],
                IS=param_dict['IS']
            )
            script_parameters.append(script_param)
        
        # Get current lab details and update with new parameters
        current_lab = get_lab_details(executor, lab_id)
        current_lab.parameters = updated_parameters
        
        updated_lab = update_lab_details(executor, current_lab)
        
        log.info("✅ TRADITIONAL parameters updated successfully!")
        return updated_lab
        
    except Exception as e:
        log.error(f"❌ Error during TRADITIONAL lab parameter update: {e}")
        return lab_details


def update_lab_parameter_ranges(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    randomize: bool = True
) -> LabDetails:
    """Update parameter ranges for a lab, preserving ALL critical settings and validating parameters."""
    lab_details = get_lab_details(executor, lab_id)

    # --- FIX: Deep copy all settings fields ---
    original_settings = lab_details.settings
    settings_dict = original_settings.model_dump(by_alias=True)

    # Log what we're preserving
    log.info(f"🔧 Preserving settings before parameter update:")
    for k, v in settings_dict.items():
        log.info(f"  {k}: {v}")

    # Convert parameters to proper format and validate
    updated_parameters = []
    for param in lab_details.parameters:
        # Handle both dict and object parameters
        if isinstance(param, dict):
            param_dict = param
        elif hasattr(param, 'model_dump'):
            param_dict = param.model_dump()
        else:
            # Fallback for other object types
            param_dict = dict(param) if hasattr(param, '__iter__') else str(param)
        
        # Validate parameter has required fields
        if not all(key in param_dict for key in ['K', 'T', 'O']):
            log.warning(f"⚠️ Skipping invalid parameter: {param_dict}")
            continue
            
        # Generate parameter ranges if randomize is enabled
        if randomize and param_dict.get('T') in [0, 1]:  # INTEGER or DECIMAL types
            current_value = param_dict['O'][0] if param_dict['O'] else '0'
            
            # Check if the value is actually numeric (not a boolean or string)
            try:
                # Try to parse as float first to handle both int and decimal
                current_val = float(current_value)
                
                # Skip if it's a boolean value (0.0 or 1.0) or if the original was a string
                if str(current_value).lower() in ['true', 'false'] or param_dict.get('T') == 3:
                    log.info(f"  ⏭️ Skipping non-numeric parameter {param_dict['K']}: {current_value}")
                    updated_parameters.append(param_dict)
                    continue
                
                if param_dict.get('T') == 0:  # INTEGER
                    current_val = int(current_val)
                    new_options = generate_mixed_parameter_range(param_dict['K'], current_val, 'integer')
                else:  # DECIMAL
                    new_options = generate_mixed_parameter_range(param_dict['K'], current_val, 'decimal')
                param_dict['O'] = new_options
                # Enable optimization for this parameter
                param_dict['I'] = True
                log.info(f"  🔧 Generated range for {param_dict['K']}: {new_options}")
            except (ValueError, TypeError):
                log.info(f"  ⏭️ Skipping non-numeric parameter {param_dict['K']}: {current_value}")
        
        # Ensure the parameter has the enabled field set properly
        if 'I' not in param_dict:
            param_dict['I'] = len(param_dict.get('O', [])) > 1  # Enable if has multiple options
        
        updated_parameters.append(param_dict)

    if not updated_parameters:
        log.warning("⚠️ No valid parameters found for optimization")
        return lab_details

    # Count how many parameters got ranges
    ranged_params = sum(1 for p in updated_parameters if len(p.get('O', [])) > 1)
    log.info(f"  📊 Total parameters: {len(updated_parameters)}")
    log.info(f"  📊 Parameters with ranges: {ranged_params}")
    log.info(f"  📊 Parameters without ranges: {len(updated_parameters) - ranged_params}")

    try:
        # Step 1: Update parameters directly (simpler approach)
        log.info("🔄 Step 1: Updating parameters directly...")
        
        # Convert dictionaries to ScriptParameter objects
        from pyHaasAPI_v1.parameters import ScriptParameter
        script_parameters = []
        for param_dict in updated_parameters:
            script_param = ScriptParameter(
                K=param_dict['K'],
                T=param_dict['T'],
                O=param_dict['O'],
                I=param_dict['I'],
                IS=param_dict['IS']
            )
            script_parameters.append(script_param)
        
        # Get current lab details and update with new parameters
        current_lab = get_lab_details(executor, lab_id)
        current_lab.parameters = updated_parameters
        
        updated_lab = update_lab_details(executor, current_lab)
        
        log.info("✅ Parameters updated successfully!")
        return updated_lab
        
    except Exception as e:
        log.error(f"❌ Error during lab parameter update: {e}")
        return lab_details
        
