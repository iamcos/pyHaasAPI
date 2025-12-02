"""
Order API module for pyHaasAPI v2.

This module provides comprehensive order management functionality.
"""

try:
    from .order_api import OrderAPI
except ImportError:
    OrderAPI = None

__all__ = ["OrderAPI"]
