"""
MCP Server Module for pyHaasAPI

This module provides comprehensive MCP (Model Context Protocol) server functionality
for pyHaasAPI, enabling AI agents to have full control over the HaasOnline trading platform.

Key Components:
- mcp_server.py: Main MCP server implementation
- mcp_handlers.py: Tool handlers and business logic
- setup_mcp_server.py: Setup and configuration script

Documentation:
- MCP_AI_USAGE_GUIDE.md: Comprehensive usage documentation
- MCP_SERVER_OVERVIEW.md: Technical overview and architecture
"""

from .cursor_mcp_server import CursorPyHaasAPIMCPServer, cursor_mcp_server_instance
from .cursor_mcp_handlers import *

__all__ = [
    "CursorPyHaasAPIMCPServer",
    "cursor_mcp_server_instance",
    # All handlers are imported via * import
]



