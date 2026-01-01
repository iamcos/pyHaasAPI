"""
Metrics computation for HaasOnline backtests (parameter-agnostic).

This module derives robust, risk-aware metrics from BacktestSummary and TradeData
without assuming any specific parameter names. It operates purely on outcomes
(trades, P&L timeline, counts) and can be applied to any strategy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

from .extraction import BacktestSummary, TradeData


@dataclass
class RunMetrics:
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


def _equity_curve(trades: List[TradeData]) -> List[Tuple[int, float]]:
    """Return equity curve as (exit_time, cumulative_net_profit)."""
    sorted_trades = sorted(trades, key=lambda t: t.exit_time)
    equity = 0.0
    curve: List[Tuple[int, float]] = []
    for t in sorted_trades:
        equity += (t.profit_loss - t.fees)
        curve.append((t.exit_time, equity))
    return curve


def _max_drawdown(curve: List[Tuple[int, float]]) -> Tuple[float, float]:
    """Compute max drawdown (absolute, percent relative to peak)."""
    if not curve:
        return 0.0, 0.0
    peak = curve[0][1]
    max_dd = 0.0
    max_dd_pct = 0.0
    for _, value in curve:
        if value > peak:
            peak = value
        dd = peak - value
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = (dd / peak * 100.0) if peak != 0 else 0.0
    return max_dd, max_dd_pct


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: List[float]) -> float:
    if not values or len(values) < 2:
        return 0.0
    mu = _mean(values)
    var = sum((x - mu) ** 2 for x in values) / (len(values) - 1)
    return var ** 0.5


def _downside_std(values: List[float], floor: float = 0.0) -> float:
    downs = [min(0.0, x - floor) for x in values]
    # Convert negatives to magnitudes
    downs = [-d for d in downs if d < 0]
    return _std(downs)


def _pnl_series(trades: List[TradeData]) -> List[float]:
    return [(t.profit_loss - t.fees) for t in trades]


def compute_metrics(summary: BacktestSummary) -> RunMetrics:
    trades = summary.trades

    pnl = _pnl_series(trades)
    gross_profit = sum(x for x in pnl if x > 0)
    gross_loss = abs(sum(x for x in pnl if x < 0))
    fees = sum(t.fees for t in trades)
    net_profit = sum(pnl)

    win_rate = summary.win_rate
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    avg_win_values = [x for x in pnl if x > 0]
    avg_loss_values = [x for x in pnl if x < 0]
    avg_win = _mean(avg_win_values)
    avg_loss = _mean(avg_loss_values)
    avg_trade_pnl = _mean(pnl)

    # Expectancy per trade: p(win)*avg_win + p(loss)*avg_loss
    p_win = (summary.winning_trades / summary.total_trades) if summary.total_trades else 0.0
    p_loss = 1.0 - p_win
    expectancy = p_win * avg_win + p_loss * avg_loss

    curve = _equity_curve(trades)
    max_dd, max_dd_pct = _max_drawdown(curve)

    # Simple volatility proxy from trade PnL series
    vol = _std(pnl)
    downside_vol = _downside_std(pnl, floor=0.0)
    sharpe = (avg_trade_pnl / vol) if vol > 0 else 0.0
    sortino = (avg_trade_pnl / downside_vol) if downside_vol > 0 else 0.0

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
