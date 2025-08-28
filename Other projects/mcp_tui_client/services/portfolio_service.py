"""
Portfolio Performance Service

Provides portfolio tracking, performance analysis, risk metrics calculation,
and correlation analysis for trading strategies and positions.
"""

import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from ..utils.logging import get_logger
from ..utils.errors import handle_error, ErrorCategory, ErrorSeverity


class PositionType(Enum):
    """Position type enumeration"""
    LONG = "long"
    SHORT = "short"
    CLOSED = "closed"


class PerformanceMetric(Enum):
    """Performance metric enumeration"""
    TOTAL_RETURN = "total_return"
    ANNUALIZED_RETURN = "annualized_return"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    CALMAR_RATIO = "calmar_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    AVERAGE_WIN = "average_win"
    AVERAGE_LOSS = "average_loss"


@dataclass
class Position:
    """Portfolio position"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    position_type: PositionType
    entry_time: datetime
    strategy_id: Optional[str] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def __post_init__(self):
        """Calculate unrealized P&L"""
        if self.position_type == PositionType.LONG:
            self.unrealized_pnl = (self.current_price - self.entry_price) * self.quantity
        elif self.position_type == PositionType.SHORT:
            self.unrealized_pnl = (self.entry_price - self.current_price) * self.quantity
    
    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.current_price * abs(self.quantity)
    
    @property
    def total_pnl(self) -> float:
        """Total P&L (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def return_percent(self) -> float:
        """Return percentage"""
        cost_basis = self.entry_price * abs(self.quantity)
        return (self.total_pnl / cost_basis) * 100 if cost_basis > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'position_type': self.position_type.value,
            'entry_time': self.entry_time.isoformat(),
            'strategy_id': self.strategy_id,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'market_value': self.market_value,
            'total_pnl': self.total_pnl,
            'return_percent': self.return_percent
        }


@dataclass
class Trade:
    """Completed trade record"""
    symbol: str
    quantity: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    position_type: PositionType
    pnl: float
    strategy_id: Optional[str] = None
    commission: float = 0.0
    
    @property
    def return_percent(self) -> float:
        """Trade return percentage"""
        cost_basis = self.entry_price * abs(self.quantity)
        return (self.pnl / cost_basis) * 100 if cost_basis > 0 else 0.0
    
    @property
    def duration(self) -> timedelta:
        """Trade duration"""
        return self.exit_time - self.entry_time
    
    @property
    def is_winner(self) -> bool:
        """Check if trade was profitable"""
        return self.pnl > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
            'position_type': self.position_type.value,
            'pnl': self.pnl,
            'strategy_id': self.strategy_id,
            'commission': self.commission,
            'return_percent': self.return_percent,
            'duration_hours': self.duration.total_seconds() / 3600,
            'is_winner': self.is_winner
        }


@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot at a point in time"""
    timestamp: datetime
    total_value: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    
    @property
    def return_percent(self) -> float:
        """Portfolio return percentage from initial value"""
        # This would need initial portfolio value to calculate properly
        return 0.0  # Placeholder
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_value': self.total_value,
            'cash': self.cash,
            'positions_value': self.positions_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'total_pnl': self.total_pnl,
            'return_percent': self.return_percent
        }


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: timedelta
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    largest_win: float
    largest_loss: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_duration_days': self.max_drawdown_duration.days,
            'calmar_ratio': self.calmar_ratio,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss
        }


@dataclass
class RiskMetrics:
    """Portfolio risk metrics"""
    value_at_risk_95: float  # 95% VaR
    value_at_risk_99: float  # 99% VaR
    expected_shortfall_95: float  # 95% Expected Shortfall (CVaR)
    beta: float  # Beta vs benchmark
    correlation_to_benchmark: float
    tracking_error: float
    information_ratio: float
    downside_deviation: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value_at_risk_95': self.value_at_risk_95,
            'value_at_risk_99': self.value_at_risk_99,
            'expected_shortfall_95': self.expected_shortfall_95,
            'beta': self.beta,
            'correlation_to_benchmark': self.correlation_to_benchmark,
            'tracking_error': self.tracking_error,
            'information_ratio': self.information_ratio,
            'downside_deviation': self.downside_deviation
        }


class PortfolioPerformanceService:
    """Portfolio performance tracking and analysis service"""
    
    def __init__(self, mcp_client=None, initial_capital: float = 100000.0):
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        
        # Portfolio state
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Trade] = []
        self.portfolio_history: List[PortfolioSnapshot] = []
        
        # Performance tracking
        self.daily_returns: List[float] = []
        self.benchmark_returns: List[float] = []
        self.last_portfolio_value = initial_capital
        
        # Configuration
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.benchmark_symbol = "SPY"  # Default benchmark
        
        # Callbacks
        self.performance_callbacks: List[callable] = []
        self.position_callbacks: List[callable] = []
        
        # Background tasks
        self.update_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self) -> None:
        """Start the portfolio service"""
        try:
            self.running = True
            
            # Start background update task
            self.update_task = asyncio.create_task(self._update_loop())
            
            self.logger.info("Portfolio performance service started")
            
        except Exception as e:
            self.logger.error(f"Failed to start portfolio service: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the portfolio service"""
        try:
            self.running = False
            
            if self.update_task and not self.update_task.done():
                self.update_task.cancel()
                await self.update_task
            
            self.logger.info("Portfolio performance service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping portfolio service: {e}")
    
    def add_position(
        self, 
        symbol: str, 
        quantity: float, 
        entry_price: float,
        position_type: PositionType = PositionType.LONG,
        strategy_id: Optional[str] = None
    ) -> str:
        """Add new position to portfolio"""
        try:
            position = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=entry_price,
                current_price=entry_price,  # Will be updated
                position_type=position_type,
                entry_time=datetime.now(),
                strategy_id=strategy_id
            )
            
            position_key = f"{symbol}_{strategy_id or 'default'}"
            self.positions[position_key] = position
            
            # Update cash
            cost = entry_price * abs(quantity)
            self.current_cash -= cost
            
            # Notify callbacks
            self._notify_position_callbacks(position, "added")
            
            self.logger.info(f"Added position: {symbol} {quantity} @ {entry_price}")
            return position_key
            
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
            raise
    
    def close_position(
        self, 
        position_key: str, 
        exit_price: float,
        quantity: Optional[float] = None
    ) -> Optional[Trade]:
        """Close position (fully or partially)"""
        try:
            if position_key not in self.positions:
                return None
            
            position = self.positions[position_key]
            close_quantity = quantity or position.quantity
            
            # Calculate P&L
            if position.position_type == PositionType.LONG:
                pnl = (exit_price - position.entry_price) * close_quantity
            else:
                pnl = (position.entry_price - exit_price) * close_quantity
            
            # Create trade record
            trade = Trade(
                symbol=position.symbol,
                quantity=close_quantity,
                entry_price=position.entry_price,
                exit_price=exit_price,
                entry_time=position.entry_time,
                exit_time=datetime.now(),
                position_type=position.position_type,
                pnl=pnl,
                strategy_id=position.strategy_id
            )
            
            self.closed_trades.append(trade)
            
            # Update cash
            proceeds = exit_price * abs(close_quantity)
            self.current_cash += proceeds
            
            # Update or remove position
            if abs(close_quantity) >= abs(position.quantity):
                # Full close
                del self.positions[position_key]
                self.logger.info(f"Closed position: {position.symbol} @ {exit_price}")
            else:
                # Partial close
                position.quantity -= close_quantity
                position.realized_pnl += pnl
                self.logger.info(f"Partially closed position: {position.symbol} {close_quantity} @ {exit_price}")
            
            # Notify callbacks
            self._notify_position_callbacks(trade, "closed")
            
            return trade
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
    
    def update_position_prices(self, price_updates: Dict[str, float]) -> None:
        """Update current prices for positions"""
        try:
            for position in self.positions.values():
                if position.symbol in price_updates:
                    position.current_price = price_updates[position.symbol]
                    # Recalculate unrealized P&L
                    position.__post_init__()
            
        except Exception as e:
            self.logger.error(f"Error updating position prices: {e}")
    
    def get_portfolio_value(self) -> float:
        """Get current total portfolio value"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.current_cash + positions_value
    
    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)"""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        realized_pnl = sum(trade.pnl for trade in self.closed_trades)
        return unrealized_pnl + realized_pnl
    
    def get_positions(self) -> List[Position]:
        """Get all current positions"""
        return list(self.positions.values())
    
    def get_trades(self, limit: Optional[int] = None) -> List[Trade]:
        """Get closed trades"""
        trades = sorted(self.closed_trades, key=lambda t: t.exit_time, reverse=True)
        return trades[:limit] if limit else trades
    
    def get_portfolio_history(self, days: int = 30) -> List[PortfolioSnapshot]:
        """Get portfolio history for specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            snapshot for snapshot in self.portfolio_history 
            if snapshot.timestamp >= cutoff_date
        ]
    
    def calculate_performance_metrics(self, period_days: int = 365) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        try:
            # Get recent returns
            cutoff_date = datetime.now() - timedelta(days=period_days)
            recent_returns = [
                ret for i, ret in enumerate(self.daily_returns)
                if i >= len(self.daily_returns) - period_days
            ]
            
            if not recent_returns:
                # Return default metrics if no data
                return PerformanceMetrics(
                    total_return=0.0, annualized_return=0.0, volatility=0.0,
                    sharpe_ratio=0.0, sortino_ratio=0.0, max_drawdown=0.0,
                    max_drawdown_duration=timedelta(0), calmar_ratio=0.0,
                    win_rate=0.0, profit_factor=0.0, average_win=0.0,
                    average_loss=0.0, total_trades=0, winning_trades=0,
                    losing_trades=0, largest_win=0.0, largest_loss=0.0
                )
            
            # Calculate return metrics
            total_return = (self.get_portfolio_value() / self.initial_capital) - 1
            annualized_return = ((1 + total_return) ** (365 / period_days)) - 1
            
            # Calculate volatility
            volatility = statistics.stdev(recent_returns) * math.sqrt(252) if len(recent_returns) > 1 else 0.0
            
            # Calculate Sharpe ratio
            excess_return = annualized_return - self.risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0.0
            
            # Calculate Sortino ratio
            downside_returns = [ret for ret in recent_returns if ret < 0]
            downside_deviation = statistics.stdev(downside_returns) * math.sqrt(252) if len(downside_returns) > 1 else 0.0
            sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0.0
            
            # Calculate maximum drawdown
            max_drawdown, max_dd_duration = self._calculate_max_drawdown()
            
            # Calculate Calmar ratio
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
            
            # Calculate trade statistics
            trade_stats = self._calculate_trade_statistics()
            
            return PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                max_drawdown_duration=max_dd_duration,
                calmar_ratio=calmar_ratio,
                **trade_stats
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            raise
    
    def calculate_risk_metrics(self, confidence_level: float = 0.95) -> RiskMetrics:
        """Calculate risk metrics"""
        try:
            if not self.daily_returns:
                return RiskMetrics(
                    value_at_risk_95=0.0, value_at_risk_99=0.0,
                    expected_shortfall_95=0.0, beta=0.0,
                    correlation_to_benchmark=0.0, tracking_error=0.0,
                    information_ratio=0.0, downside_deviation=0.0
                )
            
            # Calculate VaR
            sorted_returns = sorted(self.daily_returns)
            var_95_idx = int(len(sorted_returns) * 0.05)
            var_99_idx = int(len(sorted_returns) * 0.01)
            
            var_95 = sorted_returns[var_95_idx] if var_95_idx < len(sorted_returns) else 0.0
            var_99 = sorted_returns[var_99_idx] if var_99_idx < len(sorted_returns) else 0.0
            
            # Calculate Expected Shortfall (CVaR)
            tail_returns = sorted_returns[:var_95_idx] if var_95_idx > 0 else [0.0]
            expected_shortfall_95 = statistics.mean(tail_returns) if tail_returns else 0.0
            
            # Calculate beta and correlation (if benchmark data available)
            beta = 0.0
            correlation = 0.0
            tracking_error = 0.0
            information_ratio = 0.0
            
            if len(self.benchmark_returns) == len(self.daily_returns) and len(self.benchmark_returns) > 1:
                # Calculate correlation
                correlation = self._calculate_correlation(self.daily_returns, self.benchmark_returns)
                
                # Calculate beta
                benchmark_variance = statistics.variance(self.benchmark_returns)
                if benchmark_variance > 0:
                    covariance = statistics.covariance(self.daily_returns, self.benchmark_returns)
                    beta = covariance / benchmark_variance
                
                # Calculate tracking error
                excess_returns = [p - b for p, b in zip(self.daily_returns, self.benchmark_returns)]
                tracking_error = statistics.stdev(excess_returns) if len(excess_returns) > 1 else 0.0
                
                # Calculate information ratio
                if tracking_error > 0:
                    information_ratio = statistics.mean(excess_returns) / tracking_error
            
            # Calculate downside deviation
            downside_returns = [ret for ret in self.daily_returns if ret < 0]
            downside_deviation = statistics.stdev(downside_returns) if len(downside_returns) > 1 else 0.0
            
            return RiskMetrics(
                value_at_risk_95=var_95,
                value_at_risk_99=var_99,
                expected_shortfall_95=expected_shortfall_95,
                beta=beta,
                correlation_to_benchmark=correlation,
                tracking_error=tracking_error,
                information_ratio=information_ratio,
                downside_deviation=downside_deviation
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            raise
    
    def calculate_strategy_correlation(self) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix between strategies"""
        try:
            # Group trades by strategy
            strategy_returns: Dict[str, List[float]] = {}
            
            for trade in self.closed_trades:
                strategy_id = trade.strategy_id or "default"
                if strategy_id not in strategy_returns:
                    strategy_returns[strategy_id] = []
                strategy_returns[strategy_id].append(trade.return_percent / 100)
            
            # Calculate correlation matrix
            correlation_matrix = {}
            strategies = list(strategy_returns.keys())
            
            for i, strategy1 in enumerate(strategies):
                correlation_matrix[strategy1] = {}
                for j, strategy2 in enumerate(strategies):
                    if i == j:
                        correlation_matrix[strategy1][strategy2] = 1.0
                    elif len(strategy_returns[strategy1]) > 1 and len(strategy_returns[strategy2]) > 1:
                        # Align returns by time (simplified - assumes same length)
                        min_len = min(len(strategy_returns[strategy1]), len(strategy_returns[strategy2]))
                        returns1 = strategy_returns[strategy1][-min_len:]
                        returns2 = strategy_returns[strategy2][-min_len:]
                        
                        correlation = self._calculate_correlation(returns1, returns2)
                        correlation_matrix[strategy1][strategy2] = correlation
                    else:
                        correlation_matrix[strategy1][strategy2] = 0.0
            
            return correlation_matrix
            
        except Exception as e:
            self.logger.error(f"Error calculating strategy correlation: {e}")
            return {}
    
    def get_drawdown_periods(self) -> List[Dict[str, Any]]:
        """Get all drawdown periods"""
        try:
            if len(self.portfolio_history) < 2:
                return []
            
            drawdowns = []
            peak_value = self.portfolio_history[0].total_value
            peak_date = self.portfolio_history[0].timestamp
            in_drawdown = False
            drawdown_start = None
            
            for snapshot in self.portfolio_history[1:]:
                if snapshot.total_value > peak_value:
                    # New peak
                    if in_drawdown:
                        # End of drawdown period
                        drawdown_depth = (peak_value - snapshot.total_value) / peak_value
                        drawdowns.append({
                            'start_date': drawdown_start,
                            'end_date': snapshot.timestamp,
                            'peak_value': peak_value,
                            'trough_value': min(s.total_value for s in self.portfolio_history 
                                              if drawdown_start <= s.timestamp <= snapshot.timestamp),
                            'depth_percent': drawdown_depth * 100,
                            'duration_days': (snapshot.timestamp - drawdown_start).days
                        })
                        in_drawdown = False
                    
                    peak_value = snapshot.total_value
                    peak_date = snapshot.timestamp
                
                elif snapshot.total_value < peak_value and not in_drawdown:
                    # Start of drawdown
                    in_drawdown = True
                    drawdown_start = snapshot.timestamp
            
            return drawdowns
            
        except Exception as e:
            self.logger.error(f"Error calculating drawdown periods: {e}")
            return []
    
    def add_performance_callback(self, callback: callable) -> None:
        """Add performance update callback"""
        self.performance_callbacks.append(callback)
    
    def add_position_callback(self, callback: callable) -> None:
        """Add position update callback"""
        self.position_callbacks.append(callback)
    
    async def _update_loop(self) -> None:
        """Background update loop"""
        while self.running:
            try:
                # Take portfolio snapshot
                await self._take_portfolio_snapshot()
                
                # Calculate daily return
                self._calculate_daily_return()
                
                # Notify performance callbacks
                self._notify_performance_callbacks()
                
                await asyncio.sleep(3600)  # Update hourly
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in portfolio update loop: {e}")
                await asyncio.sleep(60)
    
    async def _take_portfolio_snapshot(self) -> None:
        """Take portfolio snapshot"""
        try:
            current_value = self.get_portfolio_value()
            positions_value = sum(pos.market_value for pos in self.positions.values())
            unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            realized_pnl = sum(trade.pnl for trade in self.closed_trades)
            
            snapshot = PortfolioSnapshot(
                timestamp=datetime.now(),
                total_value=current_value,
                cash=self.current_cash,
                positions_value=positions_value,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                total_pnl=unrealized_pnl + realized_pnl
            )
            
            self.portfolio_history.append(snapshot)
            
            # Keep only recent history (e.g., last 2 years)
            cutoff_date = datetime.now() - timedelta(days=730)
            self.portfolio_history = [
                s for s in self.portfolio_history if s.timestamp >= cutoff_date
            ]
            
        except Exception as e:
            self.logger.error(f"Error taking portfolio snapshot: {e}")
    
    def _calculate_daily_return(self) -> None:
        """Calculate daily return"""
        try:
            current_value = self.get_portfolio_value()
            
            if self.last_portfolio_value > 0:
                daily_return = (current_value / self.last_portfolio_value) - 1
                self.daily_returns.append(daily_return)
                
                # Keep only recent returns
                if len(self.daily_returns) > 1000:
                    self.daily_returns = self.daily_returns[-1000:]
            
            self.last_portfolio_value = current_value
            
        except Exception as e:
            self.logger.error(f"Error calculating daily return: {e}")
    
    def _calculate_max_drawdown(self) -> Tuple[float, timedelta]:
        """Calculate maximum drawdown and duration"""
        try:
            if len(self.portfolio_history) < 2:
                return 0.0, timedelta(0)
            
            max_drawdown = 0.0
            max_duration = timedelta(0)
            peak_value = self.portfolio_history[0].total_value
            peak_date = self.portfolio_history[0].timestamp
            
            for snapshot in self.portfolio_history[1:]:
                if snapshot.total_value > peak_value:
                    peak_value = snapshot.total_value
                    peak_date = snapshot.timestamp
                else:
                    drawdown = (peak_value - snapshot.total_value) / peak_value
                    duration = snapshot.timestamp - peak_date
                    
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                        max_duration = duration
            
            return max_drawdown, max_duration
            
        except Exception as e:
            self.logger.error(f"Error calculating max drawdown: {e}")
            return 0.0, timedelta(0)
    
    def _calculate_trade_statistics(self) -> Dict[str, Any]:
        """Calculate trade-based statistics"""
        try:
            if not self.closed_trades:
                return {
                    'win_rate': 0.0, 'profit_factor': 0.0, 'average_win': 0.0,
                    'average_loss': 0.0, 'total_trades': 0, 'winning_trades': 0,
                    'losing_trades': 0, 'largest_win': 0.0, 'largest_loss': 0.0
                }
            
            winning_trades = [t for t in self.closed_trades if t.is_winner]
            losing_trades = [t for t in self.closed_trades if not t.is_winner]
            
            win_rate = len(winning_trades) / len(self.closed_trades)
            
            total_wins = sum(t.pnl for t in winning_trades)
            total_losses = abs(sum(t.pnl for t in losing_trades))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            average_win = statistics.mean([t.pnl for t in winning_trades]) if winning_trades else 0.0
            average_loss = statistics.mean([t.pnl for t in losing_trades]) if losing_trades else 0.0
            
            largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0.0
            largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0.0
            
            return {
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'average_win': average_win,
                'average_loss': average_loss,
                'total_trades': len(self.closed_trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'largest_win': largest_win,
                'largest_loss': largest_loss
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trade statistics: {e}")
            return {}
    
    def _calculate_correlation(self, series1: List[float], series2: List[float]) -> float:
        """Calculate correlation between two series"""
        try:
            if len(series1) != len(series2) or len(series1) < 2:
                return 0.0
            
            return statistics.correlation(series1, series2)
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return 0.0
    
    def _notify_performance_callbacks(self) -> None:
        """Notify performance callbacks"""
        try:
            for callback in self.performance_callbacks:
                callback(self.get_portfolio_value(), self.get_total_pnl())
        except Exception as e:
            self.logger.error(f"Error notifying performance callbacks: {e}")
    
    def _notify_position_callbacks(self, data: Any, action: str) -> None:
        """Notify position callbacks"""
        try:
            for callback in self.position_callbacks:
                callback(data, action)
        except Exception as e:
            self.logger.error(f"Error notifying position callbacks: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'running': self.running,
            'initial_capital': self.initial_capital,
            'current_value': self.get_portfolio_value(),
            'total_pnl': self.get_total_pnl(),
            'positions_count': len(self.positions),
            'trades_count': len(self.closed_trades),
            'history_points': len(self.portfolio_history),
            'daily_returns_count': len(self.daily_returns)
        }