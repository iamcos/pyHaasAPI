"""
Wallet models for pyHaasAPI v2
Mapped from hs.wallet.def.lua
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from .common import BaseModel

@dataclass
class WalletBalance(BaseModel):
    """
    Wallet Balance (Balance)
    Represents the balance of a specific coin/asset.
    """
    coin: str = ""
    available: float = 0.0
    locked: float = 0.0
    total: float = 0.0
    
@dataclass
class Wallet(BaseModel):
    """
    Full Wallet container
    """
    account_id: str = ""
    balances: Dict[str, WalletBalance] = field(default_factory=dict)
