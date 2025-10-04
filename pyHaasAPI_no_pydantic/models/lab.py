"""
Lab-specific data models for pyHaasAPI_no_pydantic

Provides all lab-related data models using dataclasses instead of Pydantic,
with custom validation and better performance.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from .base import BaseModel, Field
from .validation import (
    Validator,
    positive_int,
    non_negative_int,
    positive_float,
    non_negative_float,
    non_empty_string,
    enum_value,
    boolean_value,
    datetime_value,
    range_value,
)


@dataclass
class LabConfig(BaseModel):
    """Lab configuration parameters"""
    max_parallel: int = 10
    max_generations: int = 30
    max_epochs: int = 3
    max_runtime: int = 0
    auto_restart: int = 0
    
    def validate(self) -> None:
        """Validate lab configuration"""
        self.max_parallel = positive_int(self.max_parallel, "max_parallel")
        self.max_generations = positive_int(self.max_generations, "max_generations")
        self.max_epochs = positive_int(self.max_epochs, "max_epochs")
        self.max_runtime = non_negative_int(self.max_runtime, "max_runtime")
        self.auto_restart = non_negative_int(self.auto_restart, "auto_restart")


@dataclass
class LabSettings(BaseModel):
    """Lab settings configuration"""
    account_id: str = Field(alias="accountId")
    market_tag: str = Field(alias="marketTag")
    interval: int = 1
    trade_amount: float = Field(alias="tradeAmount", default=100.0)
    chart_style: int = Field(alias="chartStyle", default=300)
    order_template: int = Field(alias="orderTemplate", default=500)
    leverage: float = 0.0
    position_mode: int = Field(alias="positionMode", default=0)
    margin_mode: int = Field(alias="marginMode", default=0)
    
    def validate(self) -> None:
        """Validate lab settings"""
        self.account_id = non_empty_string(self.account_id, "account_id")
        self.market_tag = non_empty_string(self.market_tag, "market_tag")
        self.interval = positive_int(self.interval, "interval")
        self.trade_amount = positive_float(self.trade_amount, "trade_amount")
        self.chart_style = non_negative_int(self.chart_style, "chart_style")
        self.order_template = non_negative_int(self.order_template, "order_template")
        self.leverage = non_negative_float(self.leverage, "leverage")
        self.position_mode = range_value(self.position_mode, "position_mode", 0, 1)
        self.margin_mode = range_value(self.margin_mode, "margin_mode", 0, 1)


@dataclass
class LabParameter(BaseModel):
    """Lab parameter configuration"""
    key: str
    value: Union[str, int, float, bool]
    param_type: int = Field(alias="type")
    options: List[Any] = field(default_factory=list)
    is_included: bool = Field(alias="included", default=True)
    is_selected: bool = Field(alias="selected", default=False)
    
    def validate(self) -> None:
        """Validate lab parameter"""
        self.key = non_empty_string(self.key, "key")
        self.param_type = range_value(self.param_type, "param_type", 0, 4)  # 0-4 for param types
        self.is_included = boolean_value(self.is_included, "is_included")
        self.is_selected = boolean_value(self.is_selected, "is_selected")


@dataclass
class LabRecord(BaseModel):
    """Lab record for listing operations"""
    lab_id: str = Field(alias="labId")
    name: str
    script_id: str = Field(alias="scriptId")
    script_name: str = Field(alias="scriptName")
    account_id: str = Field(alias="accountId")
    market_tag: str = Field(alias="marketTag")
    status: str
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None)
    backtest_count: int = Field(alias="backtestCount", default=0)
    
    def validate(self) -> None:
        """Validate lab record"""
        self.lab_id = non_empty_string(self.lab_id, "lab_id")
        self.name = non_empty_string(self.name, "name")
        self.script_id = non_empty_string(self.script_id, "script_id")
        self.script_name = non_empty_string(self.script_name, "script_name")
        self.account_id = non_empty_string(self.account_id, "account_id")
        self.market_tag = non_empty_string(self.market_tag, "market_tag")
        
        valid_statuses = ["ACTIVE", "COMPLETED", "RUNNING", "FAILED", "CANCELLED"]
        self.status = enum_value(self.status, "status", valid_statuses)
        
        if self.created_at:
            self.created_at = datetime_value(self.created_at, "created_at")
        if self.updated_at:
            self.updated_at = datetime_value(self.updated_at, "updated_at")
        
        self.backtest_count = non_negative_int(self.backtest_count, "backtest_count")


@dataclass
class LabDetails(BaseModel):
    """Detailed lab information"""
    lab_id: str = Field(alias="labId")
    name: str
    script_id: str = Field(alias="scriptId")
    script_name: str = Field(alias="scriptName")
    settings: LabSettings
    config: LabConfig
    parameters: List[LabParameter] = field(default_factory=list)
    status: str
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None)
    backtest_count: int = Field(alias="backtestCount", default=0)
    
    def validate(self) -> None:
        """Validate lab details"""
        self.lab_id = non_empty_string(self.lab_id, "lab_id")
        self.name = non_empty_string(self.name, "name")
        self.script_id = non_empty_string(self.script_id, "script_id")
        self.script_name = non_empty_string(self.script_name, "script_name")
        
        # Validate nested objects
        if isinstance(self.settings, dict):
            self.settings = LabSettings.from_dict(self.settings)
        self.settings.validate()
        
        if isinstance(self.config, dict):
            self.config = LabConfig.from_dict(self.config)
        self.config.validate()
        
        # Validate parameters
        if isinstance(self.parameters, list):
            validated_params = []
            for param in self.parameters:
                if isinstance(param, dict):
                    param = LabParameter.from_dict(param)
                param.validate()
                validated_params.append(param)
            self.parameters = validated_params
        
        valid_statuses = ["ACTIVE", "COMPLETED", "RUNNING", "FAILED", "CANCELLED"]
        self.status = enum_value(self.status, "status", valid_statuses)
        
        if self.created_at:
            self.created_at = datetime_value(self.created_at, "created_at")
        if self.updated_at:
            self.updated_at = datetime_value(self.updated_at, "updated_at")
        
        self.backtest_count = non_negative_int(self.backtest_count, "backtest_count")


@dataclass
class StartLabExecutionRequest(BaseModel):
    """Request to start lab execution"""
    lab_id: str = Field(alias="labId")
    start_unix: int = Field(alias="startUnix")
    end_unix: int = Field(alias="endUnix")
    send_email: bool = Field(alias="sendEmail", default=False)
    
    def validate(self) -> None:
        """Validate execution request"""
        self.lab_id = non_empty_string(self.lab_id, "lab_id")
        self.start_unix = positive_int(self.start_unix, "start_unix")
        self.end_unix = positive_int(self.end_unix, "end_unix")
        self.send_email = boolean_value(self.send_email, "send_email")
        
        if self.end_unix <= self.start_unix:
            raise ValueError("end_unix must be after start_unix")


@dataclass
class LabExecutionUpdate(BaseModel):
    """Lab execution status update"""
    lab_id: str = Field(alias="labId")
    status: str
    progress: float = 0.0
    current_generation: int = Field(alias="currentGeneration", default=0)
    total_generations: int = Field(alias="totalGenerations", default=0)
    current_epoch: int = Field(alias="currentEpoch", default=0)
    total_epochs: int = Field(alias="totalEpochs", default=0)
    completed_backtests: int = Field(alias="completedBacktests", default=0)
    total_backtests: int = Field(alias="totalBacktests", default=0)
    estimated_completion: Optional[datetime] = Field(alias="estimatedCompletion", default=None)
    error_message: Optional[str] = Field(alias="errorMessage", default=None)
    
    def validate(self) -> None:
        """Validate execution update"""
        self.lab_id = non_empty_string(self.lab_id, "lab_id")
        
        valid_statuses = ["RUNNING", "COMPLETED", "FAILED", "CANCELLED", "PAUSED"]
        self.status = enum_value(self.status, "status", valid_statuses)
        
        self.progress = range_value(self.progress, "progress", 0.0, 1.0)
        self.current_generation = non_negative_int(self.current_generation, "current_generation")
        self.total_generations = non_negative_int(self.total_generations, "total_generations")
        self.current_epoch = non_negative_int(self.current_epoch, "current_epoch")
        self.total_epochs = non_negative_int(self.total_epochs, "total_epochs")
        self.completed_backtests = non_negative_int(self.completed_backtests, "completed_backtests")
        self.total_backtests = non_negative_int(self.total_backtests, "total_backtests")
        
        if self.estimated_completion:
            self.estimated_completion = datetime_value(self.estimated_completion, "estimated_completion")
    
    @property
    def is_running(self) -> bool:
        """Check if execution is running"""
        return self.status == "RUNNING"
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed"""
        return self.status == "COMPLETED"
    
    @property
    def is_failed(self) -> bool:
        """Check if execution failed"""
        return self.status == "FAILED"
    
    @property
    def is_cancelled(self) -> bool:
        """Check if execution was cancelled"""
        return self.status == "CANCELLED"
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage"""
        return self.progress * 100.0



