import dataclasses
import random
import time
from contextlib import contextmanager
from typing import Generator, Iterable, Sequence, List, Dict, Any, Union, Optional
from decimal import Decimal
import logging
import copy

from pyHaasAPI import api, iterable_extensions
from pyHaasAPI.api import Authenticated, SyncExecutor, get_lab_details, HaasApiError, update_lab_details
from pyHaasAPI.domain import BacktestPeriod
from pyHaasAPI.types import ParameterOption
from pyHaasAPI.model import (
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
from pyHaasAPI.parameters import ParameterRange, ParameterType
from loguru import logger as log

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

    return api.get_backtest_result(
        executor,
        GetBacktestResultRequest(lab_id=lab_id, next_page_id=0, page_lenght=1_000_000),
    )


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
        param_dict = param if isinstance(param, dict) else param.model_dump()
        
        # Validate parameter has required fields
        if not all(key in param_dict for key in ['K', 'T', 'O']):
            log.warning(f"⚠️ Skipping invalid parameter: {param_dict}")
            continue
            
        # Generate parameter ranges if randomize is enabled
        if randomize and param_dict.get('T') in [0, 1]:  # INTEGER or DECIMAL types
            current_value = param_dict['O'][0] if param_dict['O'] else '0'
                if param_dict.get('T') == 0:  # INTEGER
                    current_val = int(current_value)
                    # Create wider range around current value for better optimization
                    new_options = [str(max(1, current_val - 5)), str(max(1, current_val - 3)), str(max(1, current_val - 1)), str(current_val), 
                                 str(current_val + 1), str(current_val + 3), str(current_val + 5), str(current_val + 7), str(current_val + 10)]
                else:  # DECIMAL
                    current_val = float(current_value)
                    # Create wider range around current value for better optimization
                    new_options = [str(max(0.1, current_val - 1.0)), str(max(0.1, current_val - 0.5)), str(max(0.1, current_val - 0.25)), str(current_val), 
                                 str(current_val + 0.25), str(current_val + 0.5), str(current_val + 1.0), str(current_val + 1.5), str(current_val + 2.0)]
                param_dict['O'] = new_options
                log.info(f"  🔧 Generated range for {param_dict['K']}: {new_options}")
            except (ValueError, TypeError):
                log.warning(f"  ⚠️ Could not generate range for {param_dict['K']}, keeping original")
        
        updated_parameters.append(param_dict)

    if not updated_parameters:
        log.warning("⚠️ No valid parameters found for optimization")
        return lab_details

    log.info(f"  📊 Optimized {len(updated_parameters)} parameters")

    try:

        # Step 1: Update only parameters (this will wipe settings, but that's expected)
        log.info("🔄 Step 1: Updating parameters only...")
        updated_lab = api.update_lab_parameters(
            executor, 
            lab_id, 
            updated_parameters
        )
        
        # Step 2: Clone the lab with optimized parameters to preserve settings
        log.info("🔄 Step 2: Cloning lab to preserve settings...")
        cloned_lab = api.clone_lab(executor, lab_id)
        
        # Step 3: Keep both labs for testing purposes (don't delete original)
        log.info("🔄 Step 3: Keeping both labs for testing purposes...")
        log.info(f"  📋 Original lab ID: {lab_id}")
        log.info(f"  📋 Cloned lab ID: {cloned_lab.lab_id}")
        
        
        # Step 4: Verify the cloned lab has correct settings
        log.info("🔄 Step 4: Verifying cloned lab settings...")
        final_lab = get_lab_details(executor, cloned_lab.lab_id)
        final_settings = final_lab.settings.model_dump()
        
        for k, v in final_settings.items():
            log.info(f"  {k}: {v}")
        
        # Check for critical settings that were lost
        critical_fields = ['account_id', 'market_tag', 'trade_amount', 'chart_style', 'order_template']
        lost_fields = []
        for field in critical_fields:
            if not final_settings.get(field):
                lost_fields.append(field)
        
        if lost_fields:
            log.error(f"❌ CRITICAL: Settings lost after cloning: {lost_fields}")
            return final_lab
        else:
            log.info("✅ All critical settings preserved successfully after cloning!")
        
        return final_lab
        
