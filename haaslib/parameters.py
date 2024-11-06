from enum import Enum
from typing import Any, Dict, List, Optional, Union, TypeVar, Literal
from pydantic import BaseModel, Field, ConfigDict

# Move these from model.py
class ParameterType(Enum):
    """Types of parameters supported by HaasScript"""
    INTEGER = 0
    DECIMAL = 1
    BOOLEAN = 2
    STRING = 3
    SELECTION = 4

class ScriptParameter(BaseModel):
    """Individual script parameter model"""
    model_config = ConfigDict(populate_by_name=True)
    
    key: str = Field(alias="K")
    param_type: ParameterType = Field(alias="T")
    options: List[str] = Field(alias="O")
    is_enabled: bool = Field(alias="I")
    is_selected: bool = Field(alias="IS")
    
    @property
    def value(self) -> Union[int, float, bool, str]:
        """Convert the current option to its proper type"""
        if not self.options:
            return None
            
        raw_value = self.options[0]
        
        try:
            match self.param_type:
                case ParameterType.INTEGER:
                    return int(raw_value)
                case ParameterType.DECIMAL:
                    return float(raw_value)
                case ParameterType.BOOLEAN:
                    return raw_value.lower() == "true"
                case _:
                    return raw_value
        except (ValueError, TypeError):
            return raw_value
    
    @property
    def name(self) -> str:
        """Extract clean parameter name from key"""
        parts = self.key.split(".")
        if len(parts) > 1:
            return parts[-1].strip()
        return self.key.split("-")[-1].strip()
    
    @property
    def group_path(self) -> List[str]:
        """Get parameter group hierarchy"""
        parts = self.key.split(".")
        return [p.strip() for p in parts if p and not p[0].isdigit()]

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
                I=param.is_enabled,
                IS=param.is_selected
            )
            self.subgroups[subgroup_name].add_parameter(updated_param)

class ScriptParameters(BaseModel):
    """Universal script parameter handler"""
    raw_parameters: List[ScriptParameter] = Field(default_factory=list)
    _grouped_parameters: Optional[ParameterGroup] = None
    
    @classmethod
    def from_api_response(cls, params_data: List[Dict[str, Any]]) -> "ScriptParameters":
        """Create from API response data"""
        parameters = [ScriptParameter(**param) for param in params_data]
        return cls(raw_parameters=parameters)
    
    def _ensure_grouped(self) -> None:
        """Lazy initialization of grouped parameters"""
        if self._grouped_parameters is None:
            root = ParameterGroup("root")
            for param in self.raw_parameters:
                root.add_parameter(param)
            self._grouped_parameters = root
    
    def get_parameter(self, path: str) -> Optional[ScriptParameter]:
        """Get parameter by its full path"""
        self._ensure_grouped()
        
        current = self._grouped_parameters
        parts = path.split(".")
        
        for part in parts[:-1]:
            if part in current.subgroups:
                current = current.subgroups[part]
            else:
                return None
        
        return current.parameters.get(parts[-1])
    
    def get_group(self, path: str) -> Optional[ParameterGroup]:
        """Get parameter group by path"""
        self._ensure_grouped()
        
        current = self._grouped_parameters
        for part in path.split("."):
            if part in current.subgroups:
                current = current.subgroups[part]
            else:
                return None
        return current
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to simple dictionary"""
        result = {}
        
        def process_group(group: ParameterGroup, prefix: str = ""):
            for name, param in group.parameters.items():
                full_name = f"{prefix}{name}" if prefix else name
                result[full_name] = param.value
            
            for name, subgroup in group.subgroups.items():
                new_prefix = f"{prefix}{name}." if prefix else f"{name}."
                process_group(subgroup, new_prefix)
        
        self._ensure_grouped()
        process_group(self._grouped_parameters)
        return result 

# Add ParameterOption definition
ParameterOption = Union[str, int, float, bool]

# Add ParameterRange class that was in model.py
class ParameterRange(BaseModel):
    """Configuration for parameter value ranges"""
    start: Optional[Union[int, float]] = None
    end: Optional[Union[int, float]] = None
    step: Optional[Union[int, float]] = None
    decimals: int = 0
    selection_values: List[ParameterOption] = Field(default_factory=list)
    
    def generate_values(self) -> List[ParameterOption]:
        """Generate all possible values for this parameter"""
        if self.selection_values:
            return self.selection_values
            
        if None in (self.start, self.end, self.step):
            return []
            
        values = []
        current = self.start
        while current <= self.end:
            if self.decimals > 0:
                values.append(round(current, self.decimals))
            else:
                values.append(int(current))
            current += self.step
        return values

class LabParameter(BaseModel):
    """Lab parameter model"""
    model_config = ConfigDict(populate_by_name=True)
    
    key: str = Field(alias="K")
    type: int = Field(alias="T")
    options: list[str] = Field(alias="O")
    is_enabled: bool = Field(alias="I")
    is_selected: bool = Field(alias="IS")
    
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
        parts = self.key.split(".")
        if len(parts) > 1:
            return parts[-1].strip()
        return self.key.split("-")[-1].strip()

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
    
    max_positions: int = Field(alias="MP")
    max_generations: int = Field(alias="MG")
    max_evaluations: int = Field(alias="ME")
    min_roi: float = Field(alias="MR")
    acceptable_risk: float = Field(alias="AR")
    
class LabSettings(BaseModel):
    """Unified lab settings model that handles both API and friendly names"""
    model_config = ConfigDict(populate_by_name=True)
    
    bot_id: str = Field(alias=["botId", "BotId"], default="")
    bot_name: str = Field(alias=["botName", "BotName"], default="")
    account_id: str = Field(alias=["accountId", "AccountId"], default="")
    market_tag: str = Field(alias=["marketTag", "MarketTag"], default="")
    position_mode: int = Field(alias=["positionMode", "PositionMode"], default=0)
    margin_mode: int = Field(alias=["marginMode", "MarginMode"], default=0)
    leverage: float = Field(alias=["leverage", "Leverage"], default=0.0)
    trade_amount: float = Field(alias=["tradeAmount", "TradeAmount"], default=100.0)
    interval: int = Field(alias=["interval", "Interval"], default=15)
    chart_style: int = Field(alias=["chartStyle", "ChartStyle"], default=300)
    order_template: int = Field(alias=["orderTemplate", "OrderTemplate"], default=500)
    script_parameters: Dict[str, Any] = Field(alias=["scriptParameters", "ScriptParameters"], default_factory=dict)



