#!/usr/bin/env python3
"""
MCP TUI Client Launcher

Simple launcher script for the MCP TUI Client application.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import and run the application
from mcp_tui_client.app import main

if __name__ == "__main__":
    main()