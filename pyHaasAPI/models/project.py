from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class LabProjectConfig:
    """Configuration for a lab in a project"""
    lab_id: str
    lab_name: str
    server_name: str
    script_id: str = ""
    market_tag: str = ""
    priority: int = 1
    enabled: bool = True
    added_at: datetime = field(default_factory=datetime.now)

@dataclass
class BacktestStep:
    """A backtesting step within a project"""
    step_id: str
    name: str
    lab_ids: List[str] = field(default_factory=list)
    analysis_criteria: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class ProjectConfig:
    """Complete project configuration"""
    name: str
    description: str = ""
    labs: List[LabProjectConfig] = field(default_factory=list)
    steps: List[BacktestStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
