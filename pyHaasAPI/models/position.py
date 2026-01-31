"""
Position models for pyHaasAPI v2
Mapped from hs.position-information.def.lua
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from .common import BaseModel

@dataclass
class Position(BaseModel):
    """
    Bot Position (PositionContainer)
    Represents a position managed by a bot.
    """
    position_id: str = ""
    market: str = ""
    
    # Direction
    is_long: bool = False
    is_short: bool = False
    
    # Pricing & Performance
    enter_price: float = 0.0
    amount: float = 0.0
    profit: float = 0.0
    roi: float = 0.0
    
    # Timestamps (Unix)
    open_time: float = 0.0
    updated_time: float = 0.0
    close_time: float = 0.0
    
    # Calculated/Derived
    current_price: float = 0.0
    
@dataclass
class UserPosition(BaseModel):
    """
    User/Account Position (UserPositionContainer)
    Represents a position held in an exchange account/wallet.
    """
    market: str = ""
    account_id: str = ""
    
    # Direction
    is_long: bool = False
    is_short: bool = False
    
    # Pricing & Performance
    enter_price: float = 0.0
    amount: float = 0.0
    profit: float = 0.0
    roi: float = 0.0
