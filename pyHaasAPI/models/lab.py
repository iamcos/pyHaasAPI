"""
Lab-related data models for pyHaasAPI v2

Provides comprehensive data models for lab management operations.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from dataclasses import dataclass, field

from .common import BaseModel
from .backtest import BacktestResult


@dataclass
class LabConfig(BaseModel):
    """Lab configuration parameters"""
    max_parallel: int = 10
    max_generations: int = 30
    max_epochs: int = 3
    max_runtime: int = 0
    auto_restart: int = 0


@dataclass
class LabSettings(BaseModel):
    """Lab settings configuration"""
    account_id: str = ""
    market_tag: str = ""
    interval: int = 1
    trade_amount: float = 100.0
    chart_style: int = 300
    order_template: int = 500
    leverage: float = 0.0
    position_mode: int = 0
    margin_mode: int = 0


@dataclass
class LabParameter(BaseModel):
    """Lab parameter configuration"""
    key: str = ""
    value: Union[str, int, float, bool] = ""
    param_type: int = 0
    options: List[Any] = field(default_factory=list)
    is_included: bool = True
    is_selected: bool = False


@dataclass
class LabRecord(BaseModel):
    """Lab record for listing operations"""
    user_id: str = ""
    UID: str = ""  # Fixed case to match API response
    lab_id: str = ""
    script_id: str = ""
    name: str = ""
    type: int = 0
    status: int = 0
    scheduled_backtests: int = 0
    completed_backtests: int = 0
    created_at: int = 0
    updated_at: int = 0
    started_at: int = 0
    running_since: int = 0
    start_unix: int = 0
    end_unix: int = 0
    send_email: bool = False
    cancel_reason: Optional[str] = None


@dataclass
class LabDetails(BaseModel):
    """Detailed lab information"""
    lab_id: str = ""
    name: str = ""
    script_id: str = ""
    script_name: str = ""
    settings: LabSettings = field(default_factory=LabSettings)
    config: LabConfig = field(default_factory=LabConfig)
    parameters: List[LabParameter] = field(default_factory=list)
    status: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    backtests: List['BacktestResult'] = field(default_factory=list)
    
    @property
    def backtest_count(self) -> int:
        """Get total number of backtests"""
        return len(self.backtests)
    
    @property
    def completed_count(self) -> int:
        """Get number of completed backtests"""
        return sum(1 for bt in self.backtests if bt.status == 1) # Assuming 1 is completed


@dataclass
class StartLabExecutionRequest(BaseModel):
    """Request to start lab execution"""
    lab_id: str = ""
    start_unix: int = 0
    end_unix: int = 0
    send_email: bool = False


@dataclass
class LabExecutionUpdate(BaseModel):
    """Lab execution status update"""
    lab_id: str = ""
    status: str = ""
    progress: float = 0.0
    current_generation: int = 0
    total_generations: int = 0
    current_epoch: int = 0
    total_epochs: int = 0
    completed_backtests: int = 0
    total_backtests: int = 0
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    
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
