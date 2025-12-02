"""
Bot Service module for pyHaasAPI v2.

This module provides business logic for bot management.
"""

try:
    from .bot_service import BotService, BotCreationResult, MassBotCreationResult, BotValidationResult
except ImportError:
    BotService = BotCreationResult = MassBotCreationResult = BotValidationResult = None

__all__ = ["BotService", "BotCreationResult", "MassBotCreationResult", "BotValidationResult"]