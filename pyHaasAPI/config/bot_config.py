"""
Bot configuration settings for pyHaasAPI v2
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    """Bot configuration settings"""
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "env_prefix": "BOT_",
    }
    
    # Default bot settings
    default_trade_amount_usdt: float = Field(default=2000.0, env="BOT_DEFAULT_TRADE_AMOUNT_USDT")
    default_leverage: float = Field(default=20.0, env="BOT_DEFAULT_LEVERAGE")
    default_margin_mode: str = Field(default="CROSS", env="BOT_DEFAULT_MARGIN_MODE")
    default_position_mode: str = Field(default="HEDGE", env="BOT_DEFAULT_POSITION_MODE")
    
    # Bot creation settings
    auto_activate: bool = Field(default=False, env="BOT_AUTO_ACTIVATE")
    max_bots_per_lab: int = Field(default=10, env="BOT_MAX_BOTS_PER_LAB")
    
    # Bot management settings
    enable_health_checks: bool = Field(default=True, env="BOT_ENABLE_HEALTH_CHECKS")
    health_check_interval: int = Field(default=300, env="BOT_HEALTH_CHECK_INTERVAL")  # seconds
    
    @field_validator("default_leverage")
    @classmethod
    def validate_leverage(cls, v):
        """Validate leverage"""
        if v < 1:
            raise ValueError("Leverage must be at least 1")
        return v
    
    @field_validator("default_margin_mode")
    @classmethod
    def validate_margin_mode(cls, v):
        """Validate margin mode"""
        valid_modes = ["CROSS", "ISOLATED"]
        if v.upper() not in valid_modes:
            raise ValueError(f"Margin mode must be one of: {valid_modes}")
        return v.upper()
    
    @field_validator("default_position_mode")
    @classmethod
    def validate_position_mode(cls, v):
        """Validate position mode"""
        valid_modes = ["HEDGE", "ONEWAY"]
        if v.upper() not in valid_modes:
            raise ValueError(f"Position mode must be one of: {valid_modes}")
        return v.upper()
    
    @field_validator("default_trade_amount_usdt")
    @classmethod
    def validate_trade_amount(cls, v):
        """Validate trade amount"""
        if v <= 0:
            raise ValueError("Trade amount must be positive")
        return v

