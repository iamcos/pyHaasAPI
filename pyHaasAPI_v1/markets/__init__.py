"""
Markets module for pyHaasAPI

This module provides market discovery, classification, and management tools
for HaasOnline trading operations across different exchanges and market types.
"""

from .discovery import MarketDiscovery, MarketInfo, MarketType
from .classification import MarketClassifier, ExchangeInfo
from .filtering import MarketFilter, FilterCriteria

__all__ = [
    'MarketDiscovery',
    'MarketInfo', 
    'MarketType',
    'MarketClassifier',
    'ExchangeInfo',
    'MarketFilter',
    'FilterCriteria'
]