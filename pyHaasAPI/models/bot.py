"""
Bot-related data models for pyHaasAPI v2

Provides comprehensive data models for bot management operations.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from dataclasses import dataclass, field

from .common import BaseEntityModel, BaseModel
from .trade import Trade


@dataclass
class BotConfiguration(BaseModel):
    """Bot configuration settings"""
    leverage: float = 20.0
    position_mode: int = 1  # 0=ONE_WAY, 1=HEDGE
    margin_mode: int = 0    # 0=CROSS, 1=ISOLATED
    trade_amount: float = 2000.0
    interval: int = 15
    chart_style: int = 300
    order_template: int = 500
    
    @property
    def position_mode_name(self) -> str:
        """Get position mode name"""
        return "HEDGE" if self.position_mode == 1 else "ONE_WAY"
    
    @property
    def margin_mode_name(self) -> str:
        """Get margin mode name"""
        return "CROSS" if self.margin_mode == 0 else "ISOLATED"


@dataclass
class BotRecord(BaseModel):
    """Bot record for listing operations"""
    bot_id: str = ""
    bot_name: str = ""
    script_id: str = ""
    script_name: str = ""
    account_id: str = ""
    market_tag: str = ""
    status: str = ""
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Summary data from API (used when trades list is empty)
    summary_roi: float = 0.0
    summary_win_rate: float = 0.0
    summary_max_drawdown: float = 0.0
    summary_net_profit: float = 0.0
    
    # Internal state for calculations
    _trades: List[Trade] = field(default_factory=list, repr=False)
    starting_balance: float = 10000.0
    
    @property
    def total_trades(self) -> int:
        """Get total number of trades from history"""
        return len(self._trades)
    
    @property
    def roi(self) -> float:
        """Calculate ROI percentage from trade history"""
        balance = self.starting_balance
        if not self._trades:
            return self.summary_roi
        if balance <= 0:
            return 0.0
        return (self.net_profit / balance) * 100.0

    @property
    def net_profit(self) -> float:
        if not self._trades:
            return self.summary_net_profit
        return sum(t.net_profit for t in self._trades)

    @property
    def win_rate(self) -> float:
        if not self._trades:
            return self.summary_win_rate
        wins = sum(1 for t in self._trades if t.is_win)
        return (wins / len(self._trades)) * 100.0 if self._trades else 0.0

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.profit_loss for t in self._trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self._trades if t.profit_loss < 0))
        return gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    @property
    def avg_profit(self) -> float:
        return self.net_profit / len(self._trades) if self._trades else 0.0


@dataclass
class BotDetails(BaseModel):
    """Detailed bot information"""
    bot_id: str = ""
    bot_name: str = ""
    script_id: str = ""
    script_name: str = ""
    script_version: int = 0
    account_id: str = ""
    market_tag: str = ""
    configuration: BotConfiguration = field(default_factory=BotConfiguration)
    status: str = ""
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Summary data from API (used when trades list is empty)
    summary_roi: float = 0.0
    summary_win_rate: float = 0.0
    summary_max_drawdown: float = 0.0
    summary_net_profit: float = 0.0
    
    # Detailed analytics
    trades: List[Trade] = field(default_factory=list)
    starting_balance: float = 10000.0
    
    @property
    def total_trades(self) -> int:
        """Get total number of trades from history"""
        return len(self.trades)
    
    @property
    def roi(self) -> float:
        """Calculate ROI percentage from trade history"""
        if not self.trades:
            return self.summary_roi
        balance = self.configuration.trade_amount if self.configuration.trade_amount > 0 else self.starting_balance
        if balance <= 0:
            return 0.0
        return (self.net_profit / balance) * 100.0

    @property
    def net_profit(self) -> float:
        if not self.trades:
            return self.summary_net_profit
        return sum(t.net_profit for t in self.trades)
    
    @property
    def win_rate(self) -> float:
        if not self.trades:
            return self.summary_win_rate
        wins = sum(1 for t in self.trades if t.is_win)
        return (wins / len(self.trades)) * 100.0 if self.trades else 0.0
    
    @property
    def profit_factor(self) -> float:
        if not self.trades:
            return 0.0 # Or map from summary if available
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        return gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    @property
    def avg_profit(self) -> float:
        if not self.trades:
            return self.net_profit / self.total_trades if self.total_trades > 0 else 0.0
        return self.net_profit / len(self.trades) if self.trades else 0.0

    @property
    def max_drawdown(self) -> float:
        if not self.trades:
            return self.summary_max_drawdown
        balance = self.starting_balance
        peak = self.starting_balance
        mdd = 0.0
        for t in self.trades:
            balance += t.net_profit
            peak = max(peak, balance)
            drawdown = (peak - balance) / peak if peak > 0 else 0.0
            mdd = max(mdd, drawdown)
        return mdd * 100.0


@dataclass
class CreateBotRequest(BaseModel):
    """Request to create a new bot"""
    bot_name: str = ""
    script_id: str = ""
    account_id: str = ""
    market_tag: str = ""
    configuration: BotConfiguration = field(default_factory=BotConfiguration)


@dataclass
class CreateBotFromLabRequest(BaseModel):
    """Request to create a bot from lab backtest"""
    lab_id: str = ""
    backtest_id: str = ""
    bot_name: str = ""
    account_id: str = ""
    configuration: Optional[BotConfiguration] = None


@dataclass
class BotOrder(BaseModel):
    """Bot order information"""
    order_id: str = ""
    bot_id: str = ""
    symbol: str = ""
    side: str = ""
    order_type: str = ""
    quantity: float = 0.0
    price: Optional[float] = None
    status: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class BotPosition(BaseModel):
    """Bot position information"""
    position_id: str = ""
    bot_id: str = ""
    symbol: str = ""
    side: str = ""
    size: float = 0.0
    entry_price: float = 0.0
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class BotRuntimeData(BaseModel):
    """Bot runtime data"""
    bot_id: str = ""
    bot_name: str = ""
    status: str = ""
    is_active: bool = False
    starting_balance: float = 10000.0
    trades: List[Trade] = field(default_factory=list)
    orders: List[BotOrder] = field(default_factory=list)
    positions: List[BotPosition] = field(default_factory=list)
    last_update: Optional[datetime] = None

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def net_profit(self) -> float:
        return sum(t.net_profit for t in self.trades)

    @property
    def roi(self) -> float:
        if self.starting_balance <= 0 or not self.trades:
            return 0.0
        return (self.net_profit / self.starting_balance) * 100.0

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.is_win)
        return (wins / len(self.trades)) * 100.0

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        return gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    @property
    def avg_profit(self) -> float:
        return self.net_profit / len(self.trades) if self.trades else 0.0

    @property
    def max_drawdown(self) -> float:
        if not self.trades:
            return 0.0
        balance = self.starting_balance
        peak = self.starting_balance
        mdd = 0.0
        for t in self.trades:
            balance += t.net_profit
            peak = max(peak, balance)
            drawdown = (peak - balance) / peak if peak > 0 else 0.0
            mdd = max(mdd, drawdown)
        return mdd * 100.0
    last_update: Optional[datetime] = None
    
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
        # Safe access handling None values
        return sum((pos.unrealized_pnl or 0.0) for pos in self.positions)
    
    @property
    def total_realized_pnl(self) -> float:
        """Get total realized P&L"""
        # Safe access handling None values
        return sum((pos.realized_pnl or 0.0) for pos in self.positions)


@dataclass
class BotActivationRequest(BaseModel):
    """Request to activate a bot"""
    bot_id: str = ""
    clean_reports: bool = False


@dataclass
class BotDeactivationRequest(BaseModel):
    """Request to deactivate a bot"""
    bot_id: str = ""
    cancel_orders: bool = False


@dataclass
class BotParameterUpdate(BaseModel):
    """Bot parameter update request"""
    bot_id: str = ""
    parameter_name: str = ""
    parameter_value: Union[str, int, float, bool] = ""


@dataclass
class BotAccountMigration(BaseModel):
    """Bot account migration request"""
    bot_id: str = ""
    new_account_id: str = ""
