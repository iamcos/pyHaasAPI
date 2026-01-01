"""
CLI module for pyHaasAPI

This module provides command-line interfaces for common pyHaasAPI operations.
"""

from .simple_cli import main as simple_cli_main

__all__ = [
    'simple_cli_main'
]
