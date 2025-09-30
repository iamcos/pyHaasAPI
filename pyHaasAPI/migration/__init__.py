"""
Migration module for pyHaasAPI v2

This module provides compatibility layer and migration tools for transitioning
from pyHaasAPI v1 to v2.
"""

from .v1_compatibility import V1CompatibilityLayer, V1ToV2Migrator

__all__ = ["V1CompatibilityLayer", "V1ToV2Migrator"]
