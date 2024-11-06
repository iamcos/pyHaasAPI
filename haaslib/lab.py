import dataclasses
import random
import time
from contextlib import contextmanager
from typing import Generator, Iterable, Sequence, List, Dict, Any, Union
from decimal import Decimal

from haaslib import api, iterable_extensions
from haaslib.api import Authenticated, SyncExecutor
from haaslib.domain import BacktestPeriod, MarketTag
from haaslib.model import (
    CreateLabRequest,
    GetBacktestResultRequest,
    PaginatedResponse,
    StartLabExecutionRequest,
    LabBacktestResult,
    LabParameter,
    ParameterOption,
    LabStatus,
    LabParameter,
    ParameterType,
    ParameterRange,
    LabSettings,
    LabConfig,
)


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
    Creates buffer lab to get it's default parameters options

    :param executor: Executor for Haas API interaction
    :param script_id: Script of lab
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

    yield lab_details.parameters

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
                is_decimal = param_type == ParameterType.DECIMAL
                decimals = 3 if is_decimal else 0
                
                range_config = ParameterRange(
                    start=min(options),
                    end=max(options),
                    step=options[1] - options[0] if len(options) > 1 else 1,
                    decimals=decimals
                )
        elif param_type == ParameterType.SELECTION:
            range_config = ParameterRange(selection_values=options)
        
        parameters.append(LabParameter(
            name=param_dict.get('K', ''),  # Key field from API
            param_type=param_type,
            current_value=current_value,
            range_config=range_config,
            is_enabled=param_dict.get('I', True),  # IsEnabled field from API
            is_specific=param_dict.get('IS', False)  # IsSpecific field from API
        ))
    
    return parameters

def update_lab_parameter_ranges(
    executor: SyncExecutor[Authenticated],
    lab_id: str,
    parameter_configs: Dict[str, Union[ParameterRange, List[Any]]]
) -> None:
    """
    Update lab parameters with new ranges or selection values
    
    Args:
        executor: Authenticated API executor
        lab_id: ID of the lab
        parameter_configs: Dict mapping parameter names to either:
            - ParameterRange for numeric parameters
            - List of values for selection parameters
    """
    lab_details = api.get_lab_details(executor, lab_id)
    
    # Convert config to proper model (using the consolidated LabConfig)
    lab_config = LabConfig(
        max_population=lab_details.config.max_population,
        max_generations=lab_details.config.max_generations,
        max_elites=lab_details.config.max_elites,
        mix_rate=lab_details.config.mix_rate,
        adjust_rate=lab_details.config.adjust_rate
    )
    
    settings = LabSettings(
        BotId=lab_details.settings.bot_id,
        BotName=lab_details.settings.bot_name,
        AccountId=lab_details.settings.account_id,
        MarketTag=lab_details.settings.market_tag,
        PositionMode=lab_details.settings.position_mode,
        MarginMode=lab_details.settings.margin_mode,
        Leverage=lab_details.settings.leverage,
        TradeAmount=lab_details.settings.trade_amount,
        Interval=lab_details.settings.interval,
        ChartStyle=lab_details.settings.chart_style,
        OrderTemplate=lab_details.settings.order_template,
        ScriptParameters=lab_details.settings.script_parameters
    )
    
    # Update parameters with new ranges/values
    updated_parameters = []
    for param in lab_details.parameters:
        param_dict = param.copy()
        param_key = param_dict.get('K', '')
        if param_key in parameter_configs:
            param_config = parameter_configs[param_key]
            if isinstance(param_config, ParameterRange):
                param_dict['O'] = param_config.generate_values()
            elif isinstance(param_config, list):
                param_dict['O'] = param_config
        updated_parameters.append(param_dict)
    
    # Create update request
    api.update_lab_details(
        executor=executor,
        lab_id=lab_id,
        config=lab_config,
        settings=settings,
        name=lab_details.name,
        lab_type=lab_details.type
    )
