import dataclasses
import random
import time
from contextlib import contextmanager
from typing import Generator, Iterable, Sequence, List, Dict, Any, Union, Optional
from decimal import Decimal
import logging

from haaslib import api, iterable_extensions
from haaslib.api import Authenticated, SyncExecutor, get_lab_details, HaasApiError
from haaslib.domain import BacktestPeriod
from haaslib.types import ParameterOption
from haaslib.model import (
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
    LabDetails
)
from haaslib.parameters import ParameterRange, ParameterType

log = logging.getLogger(__name__)

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
    """Update parameter ranges for a lab"""
    lab_details = get_lab_details(executor, lab_id)
    
    # Convert parameters to proper format
    updated_parameters = []
    for param in lab_details.parameters:
        param_dict = param if isinstance(param, dict) else param.model_dump(by_alias=True)
        param_type = param_dict.get('T', 3)  # Default to STRING
        current_value = param_dict.get('O', [None])[0]
        
        new_param = {
            'K': param_dict.get('K', ''),
            'T': param_type,
            'I': param_dict.get('I', True),
            'IS': param_dict.get('IS', False),
            'O': []  # Will be filled below
        }
        
        try:
            if param_type == 0:  # INTEGER
                if current_value and str(current_value).replace('.', '').isdigit():
                    base = int(float(current_value))
                    new_param['O'] = [str(v) for v in [max(1, base - 2), base, base + 2]]
            elif param_type == 1:  # DECIMAL
                if current_value and any(c.isdigit() for c in str(current_value)):
                    base = float(current_value)
                    new_param['O'] = [str(round(v, 8)) for v in [base * 0.8, base, base * 1.2]]
            elif param_type == 2:  # BOOLEAN
                new_param['O'] = ['True', 'False']
            else:
                new_param['O'] = param_dict.get('O', [])  # Keep original options
        except (ValueError, TypeError) as e:
            log.warning(f"Failed to update parameter {param_dict.get('K', '')}: {e}")
            new_param['O'] = param_dict.get('O', [])
            
        updated_parameters.append(new_param)
    
    # Update lab details with new parameters
    lab_details.parameters = updated_parameters
    
    # Send update to API
    try:
        return api.update_lab_details(executor, lab_details)
    except HaasApiError as e:
        log.error(f"Failed to update lab parameters: {e}")
        raise

def generate_test_range(param_type: ParameterType, current_value: Optional[str]) -> Optional[list]:
    """
    Generate a 3-value test range based on parameter type and current value
    
    :param param_type: Type of the parameter
    :param current_value: Current parameter value as string
    :return: List of 3 test values or None if range cannot be generated
    """
    try:
        if param_type == ParameterType.INTEGER:
            base = int(float(current_value)) if current_value else 10
            # Return [lower, current, higher]
            return [
                max(1, base - 2),  # Lower bound
                base,              # Current value
                base + 2          # Higher bound
            ]
            
        elif param_type == ParameterType.DECIMAL:
            base = float(current_value) if current_value else 1.0
            # Return [80%, 100%, 120%] of current value
            return [
                round(base * 0.8, 8),  # 80% of current
                base,                  # Current value
                round(base * 1.2, 8)   # 120% of current
            ]
            
    except (ValueError, TypeError):
        return None
    return None
