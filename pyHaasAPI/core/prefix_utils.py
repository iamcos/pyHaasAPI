"""
Prefix Utilities for pyHaasAPI v2.

Centralizes account and bot naming prefixes for better organization and clarity.
"""

from enum import Enum
from typing import Optional

class AccountPrefix(str, Enum):
    LIVE = "[Live]"
    SIM = "[Sim]"
    PAPER = "[Paper]"
    VAULT = "[Vault]"
    LAB = "[Lab]"

class PrefixUtils:
    @staticmethod
    def ensure_account_prefix(name: str, prefix: AccountPrefix) -> str:
        """Ensures the account name has the correct prefix."""
        p_val = prefix.value
        if name.startswith(p_val):
            return name
        
        # Remove any other known prefixes first
        for p in AccountPrefix:
            if name.startswith(p.value):
                name = name[len(p.value):].strip()
                break
                
        return f"{p_val} {name}"

    @staticmethod
    def is_simulated(name: str) -> bool:
        """Checks if the account name implies it is simulated."""
        return name.startswith(AccountPrefix.SIM.value) or name.startswith(AccountPrefix.PAPER.value)

    @staticmethod
    def get_clean_name(name: str) -> str:
        """Removes all known prefixes from a name."""
        for p in AccountPrefix:
            if name.startswith(p.value):
                return name[len(p.value):].strip()
        return name
