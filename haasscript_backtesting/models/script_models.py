"""
Data models for HaasScript management and validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class ScriptType(Enum):
    """HaasScript types supported by the system."""
    TRADE_BOT = 1
    INDICATOR = 2
    INSURANCE = 3
    MARKET_MAKER = 4


@dataclass
class HaasScript:
    """Represents a HaasScript with its metadata and content."""
    script_id: str
    name: str
    content: str
    parameters: Dict[str, Any]
    script_type: ScriptType
    created_at: datetime
    modified_at: datetime
    version: int = 1
    is_cloned: bool = False
    original_script_id: Optional[str] = None
    
    def clone(self, new_name: str) -> 'HaasScript':
        """Create a cloned copy of this script for debugging."""
        return HaasScript(
            script_id=f"{self.script_id}_clone_{datetime.now().timestamp()}",
            name=new_name,
            content=self.content,
            parameters=self.parameters.copy(),
            script_type=self.script_type,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            version=1,
            is_cloned=True,
            original_script_id=self.script_id
        )


@dataclass
class ScriptCapabilities:
    """Available functions, indicators, and syntax information for HaasScript."""
    available_functions: List[str]
    available_indicators: List[str]
    syntax_rules: Dict[str, str]
    parameter_types: Dict[str, type]
    examples: List[str]


@dataclass
class DebugResult:
    """Result of script debug compilation."""
    success: bool
    compilation_logs: List[str]
    warnings: List[str]
    errors: List[str]
    suggestions: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    
    @property
    def has_errors(self) -> bool:
        """Check if debug result contains errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if debug result contains warnings."""
        return len(self.warnings) > 0


@dataclass
class ValidationResult:
    """Result of script parameter and logic validation."""
    is_valid: bool
    parameter_errors: Dict[str, str]
    logic_errors: List[str]
    compatibility_issues: List[str]
    recommendations: List[str] = field(default_factory=list)


@dataclass
class QuickTestResult:
    """Result of quick script testing with minimal data."""
    success: bool
    runtime_data: Dict[str, Any]
    execution_logs: List[str]
    trade_signals: List[Dict[str, Any]]
    performance_summary: Dict[str, float]
    execution_time: float
    memory_usage: float
    error_message: Optional[str] = None