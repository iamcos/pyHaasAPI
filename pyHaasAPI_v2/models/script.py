"""
Script models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScriptRecord:
    """Script record"""
    script_id: str
    name: str
    description: str
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    is_published: bool


@dataclass
class ScriptItem:
    """Script item with dependencies"""
    script_id: str
    name: str
    description: str
    source_code: str
    version: str
    author: str
    dependencies: List[str]
    parameters: List['ScriptParameter']
    created_at: datetime
    updated_at: datetime
    is_published: bool


@dataclass
class ScriptParameter:
    """Script parameter"""
    name: str
    type: str
    default_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    description: Optional[str] = None


@dataclass
class ScriptTest:
    """Script test"""
    test_id: str
    script_id: str
    test_name: str
    parameters: Dict[str, Any]
    expected_result: Any
    created_at: datetime
    updated_at: datetime


@dataclass
class ScriptCommand:
    """Script command"""
    command: str
    description: str
    parameters: List[ScriptParameter]
    return_type: str
    example: Optional[str] = None



