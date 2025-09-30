"""
Bot configuration settings
"""

from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    """Bot configuration settings"""
    
    # Default bot settings
    default_leverage: float = Field(default=20.0, env="BOT_DEFAULT_LEVERAGE")
    default_position_mode: int = Field(default=1, env="BOT_DEFAULT_POSITION_MODE")  # HEDGE
    default_margin_mode: int = Field(default=0, env="BOT_DEFAULT_MARGIN_MODE")  # CROSS
    default_trade_amount: float = Field(default=2000.0, env="BOT_DEFAULT_TRADE_AMOUNT")
    
    # Bot naming
    name_template: str = Field(
        default="{lab_name} - {script_name} - {roi} pop/{population_idx} gen/{generation_idx} WR{win_rate}%",
        env="BOT_NAME_TEMPLATE"
    )
    
    # Bot limits
    max_bots_per_account: int = Field(default=1, env="BOT_MAX_PER_ACCOUNT")
    max_total_bots: int = Field(default=100, env="BOT_MAX_TOTAL")
    
    # Bot creation
    auto_activate: bool = Field(default=False, env="BOT_AUTO_ACTIVATE")
    verify_after_creation: bool = Field(default=True, env="BOT_VERIFY_AFTER_CREATION")
    creation_timeout: float = Field(default=30.0, env="BOT_CREATION_TIMEOUT")
    
    # Bot management
    enable_monitoring: bool = Field(default=True, env="BOT_ENABLE_MONITORING")
    monitoring_interval: int = Field(default=60, env="BOT_MONITORING_INTERVAL")  # seconds
    health_check_interval: int = Field(default=300, env="BOT_HEALTH_CHECK_INTERVAL")  # seconds
    
    # Risk management
    max_risk_per_bot: float = Field(default=0.02, env="BOT_MAX_RISK_PER_BOT")  # 2%
    max_total_risk: float = Field(default=0.1, env="BOT_MAX_TOTAL_RISK")  # 10%
    stop_loss_threshold: float = Field(default=0.05, env="BOT_STOP_LOSS_THRESHOLD")  # 5%
    
    # Performance thresholds
    min_roi_for_activation: float = Field(default=0.0, env="BOT_MIN_ROI_FOR_ACTIVATION")
    min_win_rate_for_activation: float = Field(default=0.0, env="BOT_MIN_WIN_RATE_FOR_ACTIVATION")
    max_drawdown_for_deactivation: float = Field(default=0.2, env="BOT_MAX_DRAWDOWN_FOR_DEACTIVATION")  # 20%
    
    # Account management
    distribute_to_individual_accounts: bool = Field(default=True, env="BOT_DISTRIBUTE_ACCOUNTS")
    account_naming_template: str = Field(
        default="[Sim] {sequence}-{balance}k",
        env="BOT_ACCOUNT_NAMING_TEMPLATE"
    )
    
    # Bot cleanup
    auto_cleanup_failed: bool = Field(default=True, env="BOT_AUTO_CLEANUP_FAILED")
    cleanup_interval: int = Field(default=3600, env="BOT_CLEANUP_INTERVAL")  # 1 hour
    failed_bot_retention_hours: int = Field(default=24, env="BOT_FAILED_RETENTION_HOURS")
    
    # Validation
    validate_bot_config: bool = Field(default=True, env="BOT_VALIDATE_CONFIG")
    validate_account_balance: bool = Field(default=True, env="BOT_VALIDATE_ACCOUNT_BALANCE")
    min_account_balance: float = Field(default=1000.0, env="BOT_MIN_ACCOUNT_BALANCE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"    
    @field_validator("default_leverage")
    @classmethod
    def validate_leverage(cls, v):
        """Validate leverage value"""
        if v <= 0:
            raise ValueError("Leverage must be positive")
        return v
    
    @field_validator("default_position_mode")
    @classmethod
    def validate_position_mode(cls, v):
        """Validate position mode"""
        valid_modes = [0, 1]  # ONE_WAY, HEDGE
        if v not in valid_modes:
            raise ValueError(f"Position mode must be one of: {valid_modes}")
        return v
    
    @field_validator("default_margin_mode")
    @classmethod
    def validate_margin_mode(cls, v):
        """Validate margin mode"""
        valid_modes = [0, 1]  # CROSS, ISOLATED
        if v not in valid_modes:
            raise ValueError(f"Margin mode must be one of: {valid_modes}")
        return v
    
    @field_validator("default_trade_amount")
    @classmethod
    def validate_trade_amount(cls, v):
        """Validate trade amount"""
        if v <= 0:
            raise ValueError("Trade amount must be positive")
        return v
    
    @field_validator("max_bots_per_account", "max_total_bots")
    @classmethod
    def validate_bot_limits(cls, v):
        """Validate bot limits"""
        if v <= 0:
            raise ValueError("Bot limits must be positive")
        return v
    
    @field_validator("creation_timeout", "monitoring_interval", "health_check_interval", "cleanup_interval")
    @classmethod
    def validate_timeouts(cls, v):
        """Validate timeout values"""
        if v <= 0:
            raise ValueError("Timeout values must be positive")
        return v
    
    @field_validator("max_risk_per_bot", "max_total_risk", "stop_loss_threshold", "max_drawdown_for_deactivation")
    @classmethod
    def validate_risk_thresholds(cls, v):
        """Validate risk thresholds"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Risk thresholds must be between 0.0 and 1.0")
        return v
    
    @field_validator("min_roi_for_activation")
    @classmethod
    def validate_min_roi(cls, v):
        """Validate minimum ROI"""
        if v < 0:
            raise ValueError("Minimum ROI must be non-negative")
        return v
    
    @field_validator("min_win_rate_for_activation")
    @classmethod
    def validate_min_win_rate(cls, v):
        """Validate minimum win rate"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Minimum win rate must be between 0.0 and 1.0")
        return v
    
    @field_validator("min_account_balance")
    @classmethod
    def validate_min_account_balance(cls, v):
        """Validate minimum account balance"""
        if v <= 0:
            raise ValueError("Minimum account balance must be positive")
        return v
    
    @property
    def position_mode_name(self) -> str:
        """Get position mode name"""
        return "HEDGE" if self.default_position_mode == 1 else "ONE_WAY"
    
    @property
    def margin_mode_name(self) -> str:
        """Get margin mode name"""
        return "CROSS" if self.default_margin_mode == 0 else "ISOLATED"
    
    def get_bot_name(self, **kwargs) -> str:
        """Generate bot name using template"""
        try:
            return self.name_template.format(**kwargs)
        except KeyError as e:
            # Fallback to simple naming if template fails
            return f"Bot-{kwargs.get('script_name', 'Unknown')}-{kwargs.get('roi', '0')}"
    
    def get_account_name(self, sequence: str, balance: float) -> str:
        """Generate account name using template"""
        try:
            return self.account_naming_template.format(sequence=sequence, balance=int(balance/1000))
        except KeyError:
            # Fallback to simple naming
            return f"Account-{sequence}-{int(balance/1000)}k"
    
    def get_bot_config(self) -> Dict[str, Any]:
        """Get default bot configuration"""
        return {
            "leverage": self.default_leverage,
            "position_mode": self.default_position_mode,
            "margin_mode": self.default_margin_mode,
            "trade_amount": self.default_trade_amount,
        }
    
    def validate_bot_risk(self, bot_count: int, total_risk: float) -> bool:
        """Validate bot risk limits"""
        if bot_count > self.max_total_bots:
            return False
        if total_risk > self.max_total_risk:
            return False
        return True
