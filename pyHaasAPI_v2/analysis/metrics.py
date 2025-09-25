"""
Advanced Metrics computation for pyHaasAPI v2

This module provides sophisticated performance metrics computation for backtest analysis,
including risk-aware metrics, parameter-agnostic calculations, and comprehensive
performance analysis.

Based on the excellent v1 implementation from pyHaasAPI/analysis/metrics.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import math

from .extraction import BacktestSummary, TradeData


@dataclass
class RunMetrics:
    """Comprehensive performance metrics for a backtest run"""
    backtest_id: str
    total_trades: int
    win_rate_pct: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    fees: float
    profit_factor: float
    expectancy: float
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe: float
    sortino: float
    volatility: float
    exposure_seconds: int
    avg_trade_duration_seconds: float


def _mean(values: List[float]) -> float:
    """Calculate mean of values, returning 0 for empty list"""
    return sum(values) / len(values) if values else 0.0


def _std(values: List[float]) -> float:
    """Calculate standard deviation of values"""
    if len(values) < 2:
        return 0.0
    
    mean_val = _mean(values)
    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def _downside_std(values: List[float], floor: float = 0.0) -> float:
    """Calculate downside deviation (standard deviation of values below floor)"""
    downside_values = [x for x in values if x < floor]
    return _std(downside_values)


def _equity_curve(trades: List[TradeData]) -> List[Tuple[int, float]]:
    """Return equity curve as (exit_time, cumulative_net_profit)"""
    if not trades:
        return []
    
    # Sort trades by exit time
    sorted_trades = sorted(trades, key=lambda t: t.exit_time)
    
    curve = []
    cumulative_pnl = 0.0
    
    for trade in sorted_trades:
        cumulative_pnl += (trade.profit_loss - trade.fees)
        curve.append((trade.exit_time, cumulative_pnl))
    
    return curve


def _max_drawdown(curve: List[Tuple[int, float]]) -> Tuple[float, float]:
    """Calculate maximum drawdown and percentage from equity curve"""
    if not curve:
        return 0.0, 0.0
    
    peak = curve[0][1]
    max_dd = 0.0
    max_dd_pct = 0.0
    
    for _, equity in curve:
        if equity > peak:
            peak = equity
        
        drawdown = peak - equity
        if drawdown > max_dd:
            max_dd = drawdown
            max_dd_pct = (drawdown / peak) * 100 if peak > 0 else 0.0
    
    return max_dd, max_dd_pct


def _pnl_series(trades: List[TradeData]) -> List[float]:
    """Extract P&L series from trades"""
    return [(t.profit_loss - t.fees) for t in trades]


def compute_metrics(summary: BacktestSummary) -> RunMetrics:
    """
    Compute comprehensive performance metrics from backtest summary
    
    This function provides parameter-agnostic, risk-aware metrics that can be
    applied to any trading strategy.
    
    Args:
        summary: BacktestSummary containing trade data and basic metrics
        
    Returns:
        RunMetrics object with comprehensive performance analysis
    """
    trades = summary.trades

    # Basic P&L calculations
    pnl = _pnl_series(trades)
    gross_profit = sum(x for x in pnl if x > 0)
    gross_loss = abs(sum(x for x in pnl if x < 0))
    fees = sum(t.fees for t in trades)
    net_profit = sum(pnl)

    # Win rate and profit factor
    win_rate = summary.win_rate
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    # Average calculations
    avg_win_values = [x for x in pnl if x > 0]
    avg_loss_values = [x for x in pnl if x < 0]
    avg_win = _mean(avg_win_values)
    avg_loss = _mean(avg_loss_values)
    avg_trade_pnl = _mean(pnl)

    # Expectancy calculation: p(win)*avg_win + p(loss)*avg_loss
    p_win = (summary.winning_trades / summary.total_trades) if summary.total_trades else 0.0
    p_loss = 1.0 - p_win
    expectancy = p_win * avg_win + p_loss * avg_loss

    # Drawdown analysis
    curve = _equity_curve(trades)
    max_dd, max_dd_pct = _max_drawdown(curve)

    # Risk metrics
    vol = _std(pnl)
    downside_vol = _downside_std(pnl, floor=0.0)
    sharpe = (avg_trade_pnl / vol) if vol > 0 else 0.0
    sortino = (avg_trade_pnl / downside_vol) if downside_vol > 0 else 0.0

    # Exposure and duration
    exposure = sum(t.duration_seconds for t in trades)
    avg_dur = exposure / summary.total_trades if summary.total_trades else 0.0

    return RunMetrics(
        backtest_id=summary.backtest_id,
        total_trades=summary.total_trades,
        win_rate_pct=win_rate,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net_profit,
        fees=fees,
        profit_factor=profit_factor,
        expectancy=expectancy,
        avg_trade_pnl=avg_trade_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        max_drawdown=max_dd,
        max_drawdown_pct=max_dd_pct,
        sharpe=sharpe,
        sortino=sortino,
        volatility=vol,
        exposure_seconds=exposure,
        avg_trade_duration_seconds=avg_dur,
    )


def calculate_risk_score(metrics: RunMetrics, backtest_data: Dict[str, Any]) -> float:
    """
    Calculate risk score (0-100, lower is better)
    
    Based on the excellent v1 implementation from interactive_analyzer.py
    
    Args:
        metrics: RunMetrics object
        backtest_data: Additional backtest data for risk assessment
        
    Returns:
        Risk score from 0-100 (lower is better)
    """
    risk_factors = []
    
    # Drawdown risk
    if metrics.max_drawdown > 0:
        risk_factors.append(min(metrics.max_drawdown_pct * 2, 50))
    
    # Volatility risk
    if metrics.volatility > 0:
        risk_factors.append(min(metrics.volatility * 100, 30))
    
    # Low win rate risk
    if metrics.win_rate_pct < 50:
        risk_factors.append((50 - metrics.win_rate_pct) * 0.5)
    
    # High leverage risk (if we can detect it)
    if metrics.net_profit > backtest_data.get('starting_balance', 10000) * 2:
        risk_factors.append(20)
    
    return min(sum(risk_factors), 100)


def calculate_stability_score(metrics: RunMetrics) -> float:
    """
    Calculate stability score (0-100, higher is better)
    
    Based on the excellent v1 implementation from interactive_analyzer.py
    
    Args:
        metrics: RunMetrics object
        
    Returns:
        Stability score from 0-100 (higher is better)
    """
    stability_factors = []
    
    # Win rate stability
    stability_factors.append(metrics.win_rate_pct * 0.4)
    
    # Profit factor stability
    if metrics.profit_factor > 1:
        stability_factors.append(min(metrics.profit_factor * 10, 30))
    
    # Sharpe ratio stability
    if metrics.sharpe > 0:
        stability_factors.append(min(metrics.sharpe * 10, 20))
    
    # Low drawdown stability
    if metrics.max_drawdown_pct < 20:
        stability_factors.append(10)
    
    return min(sum(stability_factors), 100)


def calculate_composite_score(metrics: RunMetrics, weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate composite score combining multiple metrics
    
    Args:
        metrics: RunMetrics object
        weights: Optional weights for different metrics
        
    Returns:
        Composite score
    """
    if weights is None:
        weights = {
            'profit_factor': 0.3,
            'sharpe': 0.25,
            'win_rate': 0.2,
            'expectancy': 0.15,
            'max_drawdown': 0.1
        }
    
    # Normalize metrics to 0-1 scale
    profit_factor_score = min(metrics.profit_factor / 3.0, 1.0)  # Cap at 3.0
    sharpe_score = min(max(metrics.sharpe / 2.0, 0), 1.0)  # Cap at 2.0
    win_rate_score = metrics.win_rate_pct / 100.0
    expectancy_score = min(max(metrics.expectancy / 100.0, 0), 1.0)  # Cap at 100
    drawdown_score = max(1.0 - (metrics.max_drawdown_pct / 50.0), 0)  # Penalty for >50% DD
    
    # Calculate weighted composite score
    composite = (
        weights['profit_factor'] * profit_factor_score +
        weights['sharpe'] * sharpe_score +
        weights['win_rate'] * win_rate_score +
        weights['expectancy'] * expectancy_score +
        weights['max_drawdown'] * drawdown_score
    )
    
    return composite * 100  # Scale to 0-100
