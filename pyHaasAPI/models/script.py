"""
Script models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from .common import BaseModel


@dataclass
class CompilationResult(BaseModel):
    """Compilation result information"""
    is_valid: bool = False
    compile_logs: List[str] = field(default_factory=list)
    command_details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class ScriptRecord(BaseModel):
    """Script record with compilation status"""
    script_id: str = ""
    name: str = ""
    description: str = ""
    version: str = ""
    author: str = ""
    command_name: str = ""
    is_valid: bool = False
    is_compatible: bool = False
    compilation_result: Optional[CompilationResult] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_published: bool = False

@dataclass
class ScriptParameter(BaseModel):
    """Script parameter"""
    name: str = ""
    type: str = ""
    default_value: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    description: Optional[str] = None

@dataclass
class ScriptItem(BaseModel):
    """Script item with dependencies and compilation status"""
    script_id: str = ""
    name: str = ""
    description: str = ""
    source_code: str = ""
    version: str = ""
    author: str = ""
    command_name: str = ""
    is_valid: bool = False
    is_compatible: bool = False
    compilation_result: Optional[CompilationResult] = None
    dependencies: List[str] = field(default_factory=list)
    parameters: List[ScriptParameter] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_published: bool = False

@dataclass
class ScriptTest(BaseModel):
    """Script test"""
    test_id: str = ""
    script_id: str = ""
    test_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_result: Any = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ScriptCommand(BaseModel):
    """Script command"""
    command: str = ""
    description: str = ""
    parameters: List[ScriptParameter] = field(default_factory=list)
    return_type: str = ""
    example: Optional[str] = None



