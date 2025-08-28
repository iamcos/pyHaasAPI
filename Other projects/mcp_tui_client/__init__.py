"""
MCP TUI Client - Terminal User Interface for HaasOnline MCP Server

A comprehensive terminal-based interface for managing HaasOnline trading operations
through the Model Context Protocol (MCP) server.

This package provides:
- Real-time dashboard with system monitoring
- Comprehensive bot management interface
- Advanced lab management and backtesting
- Script editor with syntax highlighting
- Node-based workflow designer
- Market data visualization
- Performance analytics and reporting
- Configuration management
"""

__version__ = "0.1.0"
__author__ = "HaasOnline Development Team"
__email__ = "dev@haasonline.com"
__description__ = "Terminal User Interface for HaasOnline MCP Server"
__license__ = "MIT"
__url__ = "https://github.com/haasonline/mcp-tui-client"

# Public API exports
from .app import MCPTUIApp
from .services.config import ConfigurationService
from .services.mcp_client import MCPClientService

__all__ = [
    "MCPTUIApp",
    "ConfigurationService", 
    "MCPClientService",
]