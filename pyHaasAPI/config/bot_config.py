"""
Bot configuration settings
"""
import os
from dataclasses import dataclass, field
from typing import Dict, Any
from .env_utils import get_env

@dataclass
class BotConfig:
    """Bot configuration settings"""
    
    # Default bot settings
    default_leverage: float = field(default_factory=lambda: get_env("BOT_DEFAULT_LEVERAGE", 20.0, float))
    default_position_mode: int = field(default_factory=lambda: get_env("BOT_DEFAULT_POSITION_MODE", 1, int))  # HEDGE
    default_margin_mode: int = field(default_factory=lambda: get_env("BOT_DEFAULT_MARGIN_MODE", 0, int))  # CROSS
    default_trade_amount: float = field(default_factory=lambda: get_env("BOT_DEFAULT_TRADE_AMOUNT", 2000.0, float))
    
    # Bot naming
    name_template: str = field(default_factory=lambda: get_env(
        "BOT_NAME_TEMPLATE",
        "{lab_name} - {script_name} - {roi} pop/{population_idx} gen/{generation_idx} WR{win_rate}%"
    ))
    
    # Bot limits
    max_bots_per_account: int = field(default_factory=lambda: get_env("BOT_MAX_PER_ACCOUNT", 1, int))
    max_total_bots: int = field(default_factory=lambda: get_env("BOT_MAX_TOTAL", 100, int))
    
    # Bot creation
    auto_activate: bool = field(default_factory=lambda: get_env("BOT_AUTO_ACTIVATE", False, bool))
    verify_after_creation: bool = field(default_factory=lambda: get_env("BOT_VERIFY_AFTER_CREATION", True, bool))
    creation_timeout: float = field(default_factory=lambda: get_env("BOT_CREATION_TIMEOUT", 30.0, float))
    
    # Bot management
    enable_monitoring: bool = field(default_factory=lambda: get_env("BOT_ENABLE_MONITORING", True, bool))
    monitoring_interval: int = field(default_factory=lambda: get_env("BOT_MONITORING_INTERVAL", 60, int))  # seconds
    health_check_interval: int = field(default_factory=lambda: get_env("BOT_HEALTH_CHECK_INTERVAL", 300, int))  # seconds
    
    # Risk management
    max_risk_per_bot: float = field(default_factory=lambda: get_env("BOT_MAX_RISK_PER_BOT", 0.02, float))  # 2%
    max_total_risk: float = field(default_factory=lambda: get_env("BOT_MAX_TOTAL_RISK", 0.1, float))  # 10%
    stop_loss_threshold: float = field(default_factory=lambda: get_env("BOT_STOP_LOSS_THRESHOLD", 0.05, float))  # 5%
    
    # Performance thresholds
    min_roi_for_activation: float = field(default_factory=lambda: get_env("BOT_MIN_ROI_FOR_ACTIVATION", 0.0, float))
    min_win_rate_for_activation: float = field(default_factory=lambda: get_env("BOT_MIN_WIN_RATE_FOR_ACTIVATION", 0.0, float))
    max_drawdown_for_deactivation: float = field(default_factory=lambda: get_env("BOT_MAX_DRAWDOWN_FOR_DEACTIVATION", 0.2, float))  # 20%
    
    # Account management
    distribute_to_individual_accounts: bool = field(default_factory=lambda: get_env("BOT_DISTRIBUTE_ACCOUNTS", True, bool))
    account_naming_template: str = field(default_factory=lambda: get_env(
        "BOT_ACCOUNT_NAMING_TEMPLATE",
        "[Sim] {sequence}-{balance}k"
    ))
    
    # Bot cleanup
    auto_cleanup_failed: bool = field(default_factory=lambda: get_env("BOT_AUTO_CLEANUP_FAILED", True, bool))
    cleanup_interval: int = field(default_factory=lambda: get_env("BOT_CLEANUP_INTERVAL", 3600, int))  # 1 hour
    failed_bot_retention_hours: int = field(default_factory=lambda: get_env("BOT_FAILED_RETENTION_HOURS", 24, int))
    
    # Validation
    validate_bot_config: bool = field(default_factory=lambda: get_env("BOT_VALIDATE_CONFIG", True, bool))
    validate_account_balance: bool = field(default_factory=lambda: get_env("BOT_VALIDATE_ACCOUNT_BALANCE", True, bool))
    min_account_balance: float = field(default_factory=lambda: get_env("BOT_MIN_ACCOUNT_BALANCE", 1000.0, float))
    
    def __post_init__(self):
        """Validate configuration"""
        self.validate_leverage()
        self.validate_position_mode()
        self.validate_margin_mode()
        self.validate_trade_amount()
        self.validate_bot_limits()
        self.validate_timeouts()
        self.validate_risk_thresholds()
        self.validate_min_roi()
        self.validate_min_win_rate()
        self.validate_min_account_balance()

    def validate_leverage(self):
        if self.default_leverage <= 0:
            raise ValueError("Leverage must be positive")

    def validate_position_mode(self):
        valid_modes = [0, 1]  # ONE_WAY, HEDGE
        if self.default_position_mode not in valid_modes:
            raise ValueError(f"Position mode must be one of: {valid_modes}")

    def validate_margin_mode(self):
        valid_modes = [0, 1]  # CROSS, ISOLATED
        if self.default_margin_mode not in valid_modes:
            raise ValueError(f"Margin mode must be one of: {valid_modes}")

    def validate_trade_amount(self):
        if self.default_trade_amount <= 0:
            raise ValueError("Trade amount must be positive")

    def validate_bot_limits(self):
        if self.max_bots_per_account <= 0:
            raise ValueError("Bot limits must be positive")
        if self.max_total_bots <= 0:
            raise ValueError("Bot limits must be positive")

    def validate_timeouts(self):
        for val in [self.creation_timeout, self.monitoring_interval, self.health_check_interval, self.cleanup_interval]:
            if val <= 0:
                raise ValueError("Timeout values must be positive")

    def validate_risk_thresholds(self):
        for val in [self.max_risk_per_bot, self.max_total_risk, self.stop_loss_threshold, self.max_drawdown_for_deactivation]:
            if not 0.0 <= val <= 1.0:
                raise ValueError("Risk thresholds must be between 0.0 and 1.0")

    def validate_min_roi(self):
        if self.min_roi_for_activation < 0:
            raise ValueError("Minimum ROI must be non-negative")

    def validate_min_win_rate(self):
        if not 0.0 <= self.min_win_rate_for_activation <= 1.0:
            raise ValueError("Minimum win rate must be between 0.0 and 1.0")

    def validate_min_account_balance(self):
        if self.min_account_balance <= 0:
            raise ValueError("Minimum account balance must be positive")

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
            # Note: template expects {balance} in k, user code might pass raw balance
            # The previous code did int(balance/1000) inside format? No, in caller.
            # Wait, previous code did: return self.account_naming_template.format(sequence=sequence, balance=int(balance/1000))
            # I should replicate that logic inside this method.
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
