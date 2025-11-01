"""
Lab-related data models for pyHaasAPI v2

Provides comprehensive data models for lab management operations.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator


class LabConfig(BaseModel):
    """Lab configuration parameters"""
    max_parallel: int = Field(default=10, description="Maximum parallel backtests")
    max_generations: int = Field(default=30, description="Maximum generations")
    max_epochs: int = Field(default=3, description="Maximum epochs")
    max_runtime: int = Field(default=0, description="Maximum runtime in seconds (0 = unlimited)")
    auto_restart: int = Field(default=0, description="Auto restart setting (0 = disabled, 1 = enabled)")
    
    @field_validator("max_parallel", "max_generations", "max_epochs")
    def validate_positive_integers(cls, v, info):
        """Validate positive integer values"""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
    
    @field_validator("max_runtime", "auto_restart")
    def validate_non_negative_integers(cls, v, info):
        """Validate non-negative integer values"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class LabSettings(BaseModel):
    """Lab settings configuration"""
    account_id: str = Field(alias="accountId", description="Account ID")
    market_tag: str = Field(alias="marketTag", description="Market tag")
    interval: int = Field(default=1, description="Data interval in minutes")
    trade_amount: float = Field(alias="tradeAmount", default=100.0, description="Trade amount")
    chart_style: int = Field(alias="chartStyle", default=300, description="Chart style ID")
    order_template: int = Field(alias="orderTemplate", default=500, description="Order template ID")
    leverage: float = Field(default=0.0, description="Leverage value")
    position_mode: int = Field(alias="positionMode", default=0, description="Position mode (0=ONE_WAY, 1=HEDGE)")
    margin_mode: int = Field(alias="marginMode", default=0, description="Margin mode (0=CROSS, 1=ISOLATED)")
    
    @field_validator("interval", "chart_style", "order_template", "position_mode", "margin_mode")
    def validate_positive_integers(cls, v, info):
        """Validate positive integer values"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
    
    @field_validator("trade_amount", "leverage")
    def validate_non_negative_floats(cls, v, info):
        """Validate non-negative float values"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class LabParameter(BaseModel):
    """Lab parameter configuration"""
    key: str = Field(description="Parameter key")
    value: Union[str, int, float, bool] = Field(description="Parameter value")
    param_type: int = Field(alias="type", description="Parameter type")
    options: List[Any] = Field(default_factory=list, description="Parameter options")
    is_included: bool = Field(alias="included", default=True, description="Whether parameter is included")
    is_selected: bool = Field(alias="selected", default=False, description="Whether parameter is selected")
    
    @field_validator("param_type")
    def validate_param_type(cls, v, info):
        """Validate parameter type"""
        valid_types = [0, 1, 2, 3, 4]  # INTEGER, DECIMAL, BOOLEAN, STRING, SELECTION
        if v not in valid_types:
            raise ValueError(f"Parameter type must be one of: {valid_types}")
        return v


class LabRecord(BaseModel):
    """Lab record for listing operations"""
    user_id: str = Field(alias="UID", description="User ID")
    lab_id: str = Field(alias="LID", description="Lab ID")
    script_id: str = Field(alias="SID", description="Script ID")
    name: str = Field(alias="N", description="Lab name")
    type: int = Field(alias="T", description="Lab type")
    status: int = Field(alias="S", description="Lab status")
    scheduled_backtests: int = Field(alias="SB", description="Scheduled backtests")
    completed_backtests: int = Field(alias="CB", description="Completed backtests")
    created_at: int = Field(alias="CA", description="Creation timestamp")
    updated_at: int = Field(alias="UA", description="Last update timestamp")
    started_at: int = Field(alias="SA", description="Started timestamp")
    running_since: int = Field(alias="RS", description="Running since timestamp")
    start_unix: int = Field(alias="SU", description="Start Unix timestamp")
    end_unix: int = Field(alias="EU", description="End Unix timestamp")
    send_email: bool = Field(alias="SE", description="Send email notification")
    cancel_reason: Optional[str] = Field(alias="CM", default=None, description="Cancel reason")
    
    @field_validator("status")
    def validate_status(cls, v, info):
        """Validate lab status"""
        # Status is an integer from the server
        valid_statuses = [0, 1, 2, 3, 4]  # Common status codes
        if v not in valid_statuses:
            # Log warning but don't fail validation
            import logging
            logging.warning(f"Unknown lab status: {v}")
        return v


class LabDetails(BaseModel):
    """Detailed lab information"""
    lab_id: str = Field(alias="labId", description="Lab ID")
    name: str = Field(description="Lab name")
    script_id: str = Field(alias="scriptId", description="Script ID")
    script_name: str = Field(alias="scriptName", description="Script name")
    settings: LabSettings = Field(description="Lab settings")
    config: LabConfig = Field(description="Lab configuration")
    parameters: List[LabParameter] = Field(default_factory=list, description="Lab parameters")
    status: str = Field(description="Lab status")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None, description="Last update timestamp")
    backtest_count: int = Field(alias="backtestCount", default=0, description="Number of backtests")
    
    @field_validator("status")
    def validate_status(cls, v, info):
        """Validate lab status"""
        valid_statuses = ["ACTIVE", "COMPLETED", "RUNNING", "FAILED", "CANCELLED"]
        if v.upper() not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v.upper()


class StartLabExecutionRequest(BaseModel):
    """Request to start lab execution"""
    model_config = ConfigDict(populate_by_name=True)
    
    lab_id: str = Field(alias="labId", description="Lab ID to execute")
    start_unix: int = Field(alias="startUnix", description="Start time in Unix timestamp")
    end_unix: int = Field(alias="endUnix", description="End time in Unix timestamp")
    send_email: bool = Field(alias="sendEmail", default=False, description="Whether to send email notification")
    
    @field_validator("start_unix", "end_unix")
    @classmethod
    def validate_unix_timestamps(cls, v):
        """Validate Unix timestamps"""
        if v <= 0:
            raise ValueError("Unix timestamp must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_end_after_start(self):
        """Validate that end time is after start time"""
        if self.end_unix <= self.start_unix:
            raise ValueError("End time must be after start time")
        return self


class LabExecutionUpdate(BaseModel):
    """Lab execution status update"""
    lab_id: str = Field(alias="labId", description="Lab ID")
    status: str = Field(description="Execution status")
    progress: float = Field(default=0.0, description="Execution progress (0.0 to 1.0)")
    current_generation: int = Field(alias="currentGeneration", default=0, description="Current generation")
    total_generations: int = Field(alias="totalGenerations", default=0, description="Total generations")
    current_epoch: int = Field(alias="currentEpoch", default=0, description="Current epoch")
    total_epochs: int = Field(alias="totalEpochs", default=0, description="Total epochs")
    completed_backtests: int = Field(alias="completedBacktests", default=0, description="Completed backtests")
    total_backtests: int = Field(alias="totalBacktests", default=0, description="Total backtests")
    estimated_completion: Optional[datetime] = Field(alias="estimatedCompletion", default=None, description="Estimated completion time")
    error_message: Optional[str] = Field(alias="errorMessage", default=None, description="Error message if failed")
    
    @field_validator("status")
    def validate_status(cls, v, info):
        """Validate execution status"""
        valid_statuses = ["RUNNING", "COMPLETED", "FAILED", "CANCELLED", "PAUSED"]
        if v.upper() not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v.upper()
    
    @field_validator("progress")
    def validate_progress(cls, v, info):
        """Validate progress value"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Progress must be between 0.0 and 1.0")
        return v
    
    @field_validator("current_generation", "total_generations", "current_epoch", "total_epochs", "completed_backtests", "total_backtests")
    def validate_non_negative_integers(cls, v, info):
        """Validate non-negative integer values"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
    
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
