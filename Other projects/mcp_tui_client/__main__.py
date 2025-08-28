"""
Main entry point for running MCP TUI Client as a module.

This allows the package to be run with:
    python -m mcp_tui_client
"""

from .cli import main

if __name__ == "__main__":
    main()