"""
MCP Server Endpoints
Organized endpoint modules for different functionality areas.
"""

# Only import modules that actually exist
from . import lab_management

__all__ = [
    "lab_management"
]