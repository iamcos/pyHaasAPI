"""
Bot-related data models for pyHaasAPI v2

Provides comprehensive data models for bot management operations.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from .common import BaseEntityModel


class BotConfiguration(BaseModel):
    """Bot configuration settings"""
    leverage: float = Field(default=20.0, description="Leverage value")
    position_mode: int = Field(alias="positionMode", default=1, description="Position mode (0=ONE_WAY, 1=HEDGE)")
    margin_mode: int = Field(alias="marginMode", default=0, description="Margin mode (0=CROSS, 1=ISOLATED)")
    trade_amount: float = Field(alias="tradeAmount", default=2000.0, description="Trade amount in USDT")
    interval: int = Field(default=15, description="Data interval in minutes")
    chart_style: int = Field(alias="chartStyle", default=300, description="Chart style ID")
    order_template: int = Field(alias="orderTemplate", default=500, description="Order template ID")
    
    @field_validator("leverage")
    def validate_leverage(cls, v, info):
        """Validate leverage value"""
        if v <= 0:
            raise ValueError("Leverage must be positive")
        return v
    
    @field_validator("position_mode")
    def validate_position_mode(cls, v, info):
        """Validate position mode"""
        if v not in [0, 1]:
            raise ValueError("Position mode must be 0 (ONE_WAY) or 1 (HEDGE)")
        return v
    
    @field_validator("margin_mode")
    def validate_margin_mode(cls, v, info):
        """Validate margin mode"""
        if v not in [0, 1]:
            raise ValueError("Margin mode must be 0 (CROSS) or 1 (ISOLATED)")
        return v
    
    @field_validator("trade_amount")
    def validate_trade_amount(cls, v, info):
        """Validate trade amount"""
        if v <= 0:
            raise ValueError("Trade amount must be positive")
        return v
    
    @field_validator("interval", "chart_style", "order_template")
    def validate_positive_integers(cls, v, info):
        """Validate positive integer values"""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
    
    @property
    def position_mode_name(self) -> str:
        """Get position mode name"""
        return "HEDGE" if self.position_mode == 1 else "ONE_WAY"
    
    @property
    def margin_mode_name(self) -> str:
        """Get margin mode name"""
        return "CROSS" if self.margin_mode == 0 else "ISOLATED"


class BotRecord(BaseModel):
    """Bot record for listing operations"""
    bot_id: str = Field(alias="botId", description="Bot ID")
    bot_name: str = Field(alias="botName", description="Bot name")
    script_id: str = Field(alias="scriptId", description="Script ID")
    script_name: str = Field(alias="scriptName", description="Script name")
    account_id: str = Field(alias="accountId", description="Account ID")
    market_tag: str = Field(alias="marketTag", description="Market tag")
    status: str = Field(description="Bot status")
    is_active: bool = Field(alias="isActive", default=False, description="Whether bot is active")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None, description="Last update timestamp")
    
    @field_validator("status")
    def validate_status(cls, v, info):
        """Validate bot status"""
        valid_statuses = ["ACTIVE", "INACTIVE", "PAUSED", "ERROR", "STOPPED"]
        if v.upper() not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v.upper()


class BotDetails(BaseModel):
    """Detailed bot information"""
    bot_id: str = Field(alias="botId", description="Bot ID")
    bot_name: str = Field(alias="botName", description="Bot name")
    script_id: str = Field(alias="scriptId", description="Script ID")
    script_name: str = Field(alias="scriptName", description="Script name")
    script_version: int = Field(alias="scriptVersion", description="Script version")
    account_id: str = Field(alias="accountId", description="Account ID")
    market_tag: str = Field(alias="marketTag", description="Market tag")
    configuration: BotConfiguration = Field(description="Bot configuration")
    status: str = Field(description="Bot status")
    is_active: bool = Field(alias="isActive", default=False, description="Whether bot is active")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None, description="Last update timestamp")
    
    @field_validator("status")
    def validate_status(cls, v, info):
        """Validate bot status"""
        valid_statuses = ["ACTIVE", "INACTIVE", "PAUSED", "ERROR", "STOPPED"]
        if v.upper() not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v.upper()


class CreateBotRequest(BaseModel):
    """Request to create a new bot"""
    bot_name: str = Field(alias="botName", description="Bot name")
    script_id: str = Field(alias="scriptId", description="Script ID")
    account_id: str = Field(alias="accountId", description="Account ID")
    market_tag: str = Field(alias="marketTag", description="Market tag")
    configuration: BotConfiguration = Field(description="Bot configuration")
    
    @field_validator("bot_name")
    def validate_bot_name(cls, v, info):
        """Validate bot name"""
        if not v or not isinstance(v, str):
            raise ValueError("Bot name must be a non-empty string")
        return v.strip()


class CreateBotFromLabRequest(BaseModel):
    """Request to create a bot from lab backtest"""
    lab_id: str = Field(alias="labId", description="Lab ID")
    backtest_id: str = Field(alias="backtestId", description="Backtest ID")
    bot_name: str = Field(alias="botName", description="Bot name")
    account_id: str = Field(alias="accountId", description="Account ID")
    configuration: Optional[BotConfiguration] = Field(default=None, description="Bot configuration (optional)")
    
    @field_validator("bot_name")
    def validate_bot_name(cls, v, info):
        """Validate bot name"""
        if not v or not isinstance(v, str):
            raise ValueError("Bot name must be a non-empty string")
        return v.strip()


class BotOrder(BaseModel):
    """Bot order information"""
    order_id: str = Field(alias="orderId", description="Order ID")
    bot_id: str = Field(alias="botId", description="Bot ID")
    symbol: str = Field(description="Trading symbol")
    side: str = Field(description="Order side (BUY/SELL)")
    order_type: str = Field(alias="orderType", description="Order type")
    quantity: float = Field(description="Order quantity")
    price: Optional[float] = Field(default=None, description="Order price")
    status: str = Field(description="Order status")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None, description="Last update timestamp")
    
    @field_validator("side")
    def validate_side(cls, v, info):
        """Validate order side"""
        if v.upper() not in ["BUY", "SELL"]:
            raise ValueError("Order side must be BUY or SELL")
        return v.upper()
    
    @field_validator("order_type")
    def validate_order_type(cls, v, info):
        """Validate order type"""
        valid_types = ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
        if v.upper() not in valid_types:
            raise ValueError(f"Order type must be one of: {valid_types}")
        return v.upper()
    
    @field_validator("quantity")
    def validate_quantity(cls, v, info):
        """Validate quantity"""
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v
    
    @field_validator("price")
    def validate_price(cls, v, info):
        """Validate price"""
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v


class BotPosition(BaseModel):
    """Bot position information"""
    position_id: str = Field(alias="positionId", description="Position ID")
    bot_id: str = Field(alias="botId", description="Bot ID")
    symbol: str = Field(description="Trading symbol")
    side: str = Field(description="Position side (LONG/SHORT)")
    size: float = Field(description="Position size")
    entry_price: float = Field(alias="entryPrice", description="Entry price")
    current_price: Optional[float] = Field(alias="currentPrice", default=None, description="Current price")
    unrealized_pnl: Optional[float] = Field(alias="unrealizedPnl", default=None, description="Unrealized P&L")
    realized_pnl: Optional[float] = Field(alias="realizedPnl", default=None, description="Realized P&L")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None, description="Last update timestamp")
    
    @field_validator("side")
    def validate_side(cls, v, info):
        """Validate position side"""
        if v.upper() not in ["LONG", "SHORT"]:
            raise ValueError("Position side must be LONG or SHORT")
        return v.upper()
    
    @field_validator("size")
    def validate_size(cls, v, info):
        """Validate position size"""
        if v <= 0:
            raise ValueError("Position size must be positive")
        return v
    
    @field_validator("entry_price")
    def validate_entry_price(cls, v, info):
        """Validate entry price"""
        if v <= 0:
            raise ValueError("Entry price must be positive")
        return v
    
    @field_validator("current_price")
    def validate_current_price(cls, v, info):
        """Validate current price"""
        if v is not None and v <= 0:
            raise ValueError("Current price must be positive")
        return v


class BotRuntimeData(BaseModel):
    """Bot runtime data"""
    bot_id: str = Field(alias="botId", description="Bot ID")
    bot_name: str = Field(alias="botName", description="Bot name")
    status: str = Field(description="Bot status")
    is_active: bool = Field(alias="isActive", default=False, description="Whether bot is active")
    performance: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    orders: List[BotOrder] = Field(default_factory=list, description="Bot orders")
    positions: List[BotPosition] = Field(default_factory=list, description="Bot positions")
    last_update: Optional[datetime] = Field(alias="lastUpdate", default=None, description="Last update timestamp")
    
    @field_validator("status")
    def validate_status(cls, v, info):
        """Validate bot status"""
        valid_statuses = ["ACTIVE", "INACTIVE", "PAUSED", "ERROR", "STOPPED"]
        if v.upper() not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v.upper()
    
    @property
    def total_orders(self) -> int:
        """Get total number of orders"""
        return len(self.orders)
    
    @property
    def active_orders(self) -> List[BotOrder]:
        """Get active orders"""
        return [order for order in self.orders if order.status in ["NEW", "PARTIALLY_FILLED"]]
    
    @property
    def total_positions(self) -> int:
        """Get total number of positions"""
        return len(self.positions)
    
    @property
    def total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum(pos.unrealized_pnl or 0 for pos in self.positions)
    
    @property
    def total_realized_pnl(self) -> float:
        """Get total realized P&L"""
        return sum(pos.realized_pnl or 0 for pos in self.positions)


class BotActivationRequest(BaseModel):
    """Request to activate a bot"""
    bot_id: str = Field(alias="botId", description="Bot ID")
    clean_reports: bool = Field(alias="cleanReports", default=False, description="Whether to clean reports")
    
    @field_validator("bot_id")
    def validate_bot_id(cls, v, info):
        """Validate bot ID"""
        if not v or not isinstance(v, str):
            raise ValueError("Bot ID must be a non-empty string")
        return v


class BotDeactivationRequest(BaseModel):
    """Request to deactivate a bot"""
    bot_id: str = Field(alias="botId", description="Bot ID")
    cancel_orders: bool = Field(alias="cancelOrders", default=False, description="Whether to cancel orders")
    
    @field_validator("bot_id")
    def validate_bot_id(cls, v, info):
        """Validate bot ID"""
        if not v or not isinstance(v, str):
            raise ValueError("Bot ID must be a non-empty string")
        return v


class BotParameterUpdate(BaseModel):
    """Bot parameter update request"""
    bot_id: str = Field(alias="botId", description="Bot ID")
    parameter_name: str = Field(alias="parameterName", description="Parameter name")
    parameter_value: Union[str, int, float, bool] = Field(alias="parameterValue", description="Parameter value")
    
    @field_validator("bot_id")
    def validate_bot_id(cls, v, info):
        """Validate bot ID"""
        if not v or not isinstance(v, str):
            raise ValueError("Bot ID must be a non-empty string")
        return v
    
    @field_validator("parameter_name")
    def validate_parameter_name(cls, v, info):
        """Validate parameter name"""
        if not v or not isinstance(v, str):
            raise ValueError("Parameter name must be a non-empty string")
        return v.strip()


class BotAccountMigration(BaseModel):
    """Bot account migration request"""
    bot_id: str = Field(alias="botId", description="Bot ID")
    new_account_id: str = Field(alias="newAccountId", description="New account ID")
    
    @field_validator("bot_id")
    def validate_bot_id(cls, v, info):
        """Validate bot ID"""
        if not v or not isinstance(v, str):
            raise ValueError("Bot ID must be a non-empty string")
        return v
    
    @field_validator("new_account_id")
    def validate_new_account_id(cls, v, info):
        """Validate new account ID"""
        if not v or not isinstance(v, str):
            raise ValueError("New account ID must be a non-empty string")
        return v
