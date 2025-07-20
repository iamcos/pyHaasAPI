from enum import Enum
from typing import Any, Dict, List, Optional, Union, TypeVar, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationInfo
import random
from loguru import logger as log

# Move these from model.py
class ParameterType(Enum):
    """Types of parameters supported by HaasScript"""
    INTEGER = 0
    DECIMAL = 1
    BOOLEAN = 2
    STRING = 3
    SELECTION = 4

class ParameterRange:
    """Defines a range of values for a parameter"""
    def __init__(
        self, 
        start: Optional[Union[int, float]] = None,
        end: Optional[Union[int, float]] = None,
        step: Union[int, float] = 1,
        selection_values: Optional[List[Any]] = None
    ):
        self.start = start
        self.end = end
        self.step = step
        self.selection_values = selection_values or []
    
    def generate_range(self) -> List[Union[int, float]]:
        """Generate all values in the range"""
        if self.selection_values:
            return self.selection_values
            
        if not all([self.start, self.end]):
            return []
            
        if isinstance(self.start, float) or isinstance(self.end, float) or isinstance(self.step, float):
            values = []
            current = self.start
            while current <= self.end:
                values.append(round(current, 8))
                current += self.step
            return values
        return list(range(int(self.start), int(self.end) + 1, int(self.step)))

class ScriptParameter(BaseModel):
    """Script parameter model"""
    key: str = Field(alias="K")
    param_type: int = Field(alias="T")
    value: Optional[Any] = Field(None)
    options: List[Any] = Field(alias="O")
    is_included: bool = Field(alias="I")
    is_selected: bool = Field(alias="IS")
    name: Optional[str] = None
    
    @field_validator('name', mode='before')
    @classmethod
    def extract_name(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Extract parameter name from key"""
        key = info.data.get('K', '')
        return key.split('.')[-1] if key else ''
    
    @property
    def group_path(self) -> List[str]:
        """Get parameter group hierarchy"""
        parts = self.key.split(".")
        return [p.strip() for p in parts if p and not p[0].isdigit()]

    def update_range(self, param_range: ParameterRange) -> None:
        """Update parameter options with values from range"""
        self.options = [str(val) for val in param_range.generate_range()]

class ParameterGroup:
    """Group of related parameters"""
    def __init__(self, name: str):
        self.name = name
        self.parameters: Dict[str, ScriptParameter] = {}
        self.subgroups: Dict[str, "ParameterGroup"] = {}
    
    def add_parameter(self, param: ScriptParameter) -> None:
        """Add parameter to appropriate group/subgroup"""
        path = param.group_path
        
        if len(path) == 1:
            self.parameters[param.name] = param
        else:
            subgroup_name = path[0]
            if subgroup_name not in self.subgroups:
                self.subgroups[subgroup_name] = ParameterGroup(subgroup_name)
            
            updated_key = ".".join(path[1:])
            updated_param = ScriptParameter(
                K=updated_key,
                T=param.param_type,
                O=param.options,
                I=param.is_included,
                IS=param.is_selected
            )
            self.subgroups[subgroup_name].add_parameter(updated_param)



# Add ParameterOption definition
ParameterOption = Union[str, int, float, bool]

# Add ParameterRange class that was in model.py
class ParameterRange:
    def __init__(self, start: Union[int, float], end: Union[int, float], step: Union[int, float] = 1):
        self.start = start
        self.end = end
        self.step = step
    
    def generate_range(self) -> List[Union[int, float]]:
        """Generate a list of values within the range"""
        if isinstance(self.start, float) or isinstance(self.end, float) or isinstance(self.step, float):
            # Handle floating point ranges
            values = []
            current = self.start
            while current <= self.end:
                values.append(round(current, 8))  # Round to avoid floating point errors
                current += self.step
            return values
        else:
            # Handle integer ranges
            return list(range(self.start, self.end + 1, self.step))
    
    def generate_values(self) -> List[Union[int, float]]:
        """Generate a random subset of values from the range"""
        all_values = self.generate_range()
        return random.sample(all_values, min(len(all_values), 10))  # Return up to 10 random values

class LabParameter(BaseModel):
    """Lab parameter model"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    key: str = Field(alias="K")
    type: int = Field(alias="T")
    options: list[str] = Field(alias="O", default_factory=list)
    is_enabled: bool = Field(alias="I", default=True)
    is_selected: bool = Field(alias="IS", default=False)
    
    @property
    def current_value(self) -> Any:
        """Get the current value from options"""
        return self.options[0] if self.options else None
    
    @property
    def possible_values(self) -> list[str]:
        """Get all possible values"""
        return self.options
    
    @property
    def is_setting_group(self) -> bool:
        """Check if this is a settings group header"""
        return self.name.endswith(".Settings")
    
    @property
    def display_name(self) -> str:
        """Get clean display name without the prefix numbers"""
        parts = self.name.split(".")
        return parts[-1].strip() if parts else self.name
    
    @property
    def group_path(self) -> list[str]:
        """Get the parameter group hierarchy"""
        return [p.strip() for p in self.name.split(".") if p and not p[0].isdigit()]

    @property
    def name(self) -> str:
        """Get parameter name from key"""
        key_value = str(self.key)  # Get the actual value
        parts = key_value.split(".")
        if len(parts) > 1:
            return parts[-1].strip()
        return key_value.split("-")[-1].strip()

class ScriptParameters(BaseModel):
    """Handles script parameter management"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )
    
    parameters: List[LabParameter] = Field(default_factory=list)
    
    def __iter__(self):
        return iter(self.parameters)

    @classmethod
    def from_api_response(cls, raw_parameters: List[Dict[str, Any]]) -> "ScriptParameters":
        """Create ScriptParameters from raw API response"""
        params = []
        for param_dict in raw_parameters:
            param = LabParameter(
                key=param_dict.get('K', ''),
                type=param_dict.get('T', 3),  # Default to STRING type
                options=param_dict.get('O', []),
                is_enabled=param_dict.get('I', True),
                is_selected=param_dict.get('IS', False)
            )
            params.append(param)
        return cls(parameters=params)

class LabStatus(int, Enum):
    """Lab execution status"""
    CREATED = 0
    QUEUED = 1
    RUNNING = 2
    COMPLETED = 3
    CANCELLED = 4

    def __eq__(self, other):
        if isinstance(other, (LabStatus, int)):
            return self.value == other
        return False
    
class BacktestStatus(Enum):
    """Status of a lab backtest"""
    QUEUED = 0
    EXECUTING = 1
    CANCELLED = 2
    DONE = 3
    
class LabAlgorithm(Enum):
    """Lab optimization algorithm types"""
    BRUTE_FORCE = 0
    INTELLIGENT = 1
    RANDOM = 2
    CLUSTER = 3


class LabConfig(BaseModel):
    """Lab configuration model"""
    model_config = ConfigDict(populate_by_name=True)
    
    max_population: int = Field(alias="MP")
    max_generations: int = Field(alias="MG")
    max_elites: int = Field(alias="ME")
    mix_rate: float = Field(alias="MR")
    adjust_rate: float = Field(alias="AR")
    
class LabSettings(BaseModel):
    """Unified lab settings model that handles both API and friendly names"""
    model_config = ConfigDict(populate_by_name=True)
    
    bot_id: Optional[str] = Field(alias=["botId", "BotId"], default="")
    bot_name: Optional[str] = Field(alias=["botName", "BotName"], default="")
    account_id: Optional[str] = Field(alias=["accountId", "AccountId"], default="")
    market_tag: Optional[str] = Field(alias="marketTag", default="")
    position_mode: int = Field(alias=["positionMode", "PositionMode"], default=0)
    margin_mode: int = Field(alias=["marginMode", "MarginMode"], default=0)
    leverage: float = Field(alias=["leverage", "Leverage"], default=0.0)
    trade_amount: float = Field(alias=["tradeAmount", "TradeAmount"], default=100.0)
    interval: int = Field(alias=["interval", "Interval"], default=15)
    chart_style: int = Field(alias=["chartStyle", "ChartStyle"], default=300)
    order_template: int = Field(alias=["orderTemplate", "OrderTemplate"], default=500)
    script_parameters: Optional[Dict[str, Any]] = Field(alias=["scriptParameters", "ScriptParameters"], default_factory=dict)
    
    @field_validator('bot_id', 'bot_name', 'account_id', 'market_tag', mode='before')
    @classmethod
    def handle_null_strings(cls, v):
        """Convert null to empty string for string fields, but preserve valid strings"""
        if v is None:
            return ""
        elif isinstance(v, str):
            return v  # Preserve valid strings
        else:
            return str(v)  # Convert other types to string
    
    @field_validator('script_parameters', mode='before')
    @classmethod
    def handle_null_dict(cls, v):
        """Convert null to empty dict for script_parameters"""
        return {} if v is None else v



