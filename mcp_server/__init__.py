"""
MCP Server for HaasOnline API Integration
Provides Model Context Protocol server for trading bot automation and lab management.
"""

__version__ = "1.0.0"
__author__ = "HaasOnline Trading Bot Automation"

from .server import HaasMCPServer

__all__ = ["HaasMCPServer"]