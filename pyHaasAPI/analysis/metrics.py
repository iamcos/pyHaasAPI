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
    starting_balance: float = 0.0
    roi_pct: float = 0.0
    equity_curve: List[float] = None
    
    # Consecutive performance analysis
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    avg_win_streak: float = 0.0
    avg_loss_streak: float = 0.0
    current_streak: int = 0  # Positive for wins, negative for losses
    
    # Recovery & risk-adjusted metrics
    recovery_factor: float = 0.0  # Net profit / Max DD
    calmar_ratio: float = 0.0  # Annualized return / Max DD
    mar_ratio: float = 0.0  # CAGR / Max DD
    
    # Advanced drawdown metrics
    avg_drawdown: float = 0.0
    avg_drawdown_pct: float = 0.0
    drawdown_duration_avg_seconds: float = 0.0
    underwater_pct: float = 0.0  # % of time in drawdown
    pain_index: float = 0.0  # Sum of (DD depth × duration)
    
    # Trade quality metrics
    win_loss_ratio: float = 0.0  # Avg win / Avg loss
    edge_ratio: float = 0.0  # (Win% × Avg Win) / (Loss% × Avg Loss)
    profit_per_day: float = 0.0
    
    # Risk metrics
    var_95: float = 0.0  # 95% Value at Risk
    cvar_95: float = 0.0  # Conditional VaR (expected loss beyond VaR)
    skewness: float = 0.0  # Return distribution asymmetry
    kurtosis: float = 0.0  # Tail risk (fat tails)
    worst_trade_pct: float = 0.0  # Worst single trade as % of capital


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
    if not downside_values:
        return 0.0
    return _std(downside_values)


def _compute_consecutive_stats(trades: List[TradeData]) -> Dict[str, Any]:
    """
    Compute consecutive wins/losses statistics.
    
    Returns:
        Dictionary with max_wins, max_losses, avg_win_streak, avg_loss_streak, current_streak
    """
    if not trades:
        return {
            'max_wins': 0,
            'max_losses': 0,
            'avg_win_streak': 0.0,
            'avg_loss_streak': 0.0,
            'current_streak': 0
        }
    
    max_wins = 0
    max_losses = 0
    current_streak = 0
    win_streaks = []
    loss_streaks = []
    
    for trade in trades:
        is_win = trade.profit_loss > 0
        
        if is_win:
            if current_streak > 0:
                current_streak += 1
            else:
                if current_streak < 0:
                    loss_streaks.append(abs(current_streak))
                current_streak = 1
        else:
            if current_streak < 0:
                current_streak -= 1
            else:
                if current_streak > 0:
                    win_streaks.append(current_streak)
                current_streak = -1
        
        if current_streak > 0:
            max_wins = max(max_wins, current_streak)
        else:
            max_losses = max(max_losses, abs(current_streak))
    
    # Capture final streak
    if current_streak > 0:
        win_streaks.append(current_streak)
    elif current_streak < 0:
        loss_streaks.append(abs(current_streak))
    
    return {
        'max_wins': max_wins,
        'max_losses': max_losses,
        'avg_win_streak': _mean(win_streaks) if win_streaks else 0.0,
        'avg_loss_streak': _mean(loss_streaks) if loss_streaks else 0.0,
        'current_streak': current_streak
    }


def _compute_drawdown_details(equity_curve: List[Tuple[int, float]]) -> Dict[str, Any]:
    """
    Compute detailed drawdown statistics.
    
    Returns:
        Dictionary with avg_dd, avg_dd_pct, avg_duration, underwater_pct, pain_index
    """
    if not equity_curve or len(equity_curve) < 2:
        return {
            'avg_dd': 0.0,
            'avg_dd_pct': 0.0,
            'avg_duration': 0.0,
            'underwater_pct': 0.0,
            'pain_index': 0.0
        }
    
    drawdowns = []
    drawdown_durations = []
    underwater_periods = 0
    pain_total = 0.0
    
    peak = equity_curve[0][1]
    peak_idx = 0
    in_drawdown = False
    dd_start_idx = 0
    
    for idx, (timestamp, equity) in enumerate(equity_curve):
        if equity > peak:
            # New peak - end of drawdown if we were in one
            if in_drawdown:
                duration = idx - dd_start_idx
                drawdown_durations.append(duration)
                in_drawdown = False
            peak = equity
            peak_idx = idx
        else:
            # In drawdown
            dd = peak - equity
            dd_pct = (dd / peak * 100) if peak > 0 else 0.0
            
            if not in_drawdown:
                in_drawdown = True
                dd_start_idx = peak_idx
            
            drawdowns.append((dd, dd_pct))
            underwater_periods += 1
            pain_total += dd_pct  # Pain index accumulates DD depth
    
    total_periods = len(equity_curve)
    
    return {
        'avg_dd': _mean([d[0] for d in drawdowns]) if drawdowns else 0.0,
        'avg_dd_pct': _mean([d[1] for d in drawdowns]) if drawdowns else 0.0,
        'avg_duration': _mean(drawdown_durations) if drawdown_durations else 0.0,
        'underwater_pct': (underwater_periods / total_periods * 100) if total_periods > 0 else 0.0,
        'pain_index': pain_total
    }


def _compute_risk_metrics(pnl: List[float], starting_balance: float) -> Dict[str, Any]:
    """
    Compute risk metrics: VaR, CVaR, skewness, kurtosis.
    
    Returns:
        Dictionary with var_95, cvar_95, skewness, kurtosis, worst_trade_pct
    """
    if not pnl:
        return {
            'var_95': 0.0,
            'cvar_95': 0.0,
            'skewness': 0.0,
            'kurtosis': 0.0,
            'worst_trade_pct': 0.0
        }
    
    sorted_pnl = sorted(pnl)
    n = len(sorted_pnl)
    
    # VaR at 95% confidence (5th percentile loss)
    var_idx = max(0, int(n * 0.05))
    var_95 = abs(sorted_pnl[var_idx]) if var_idx < n else 0.0
    
    # CVaR (expected loss beyond VaR)
    tail_losses = [abs(p) for p in sorted_pnl[:var_idx+1] if p < 0]
    cvar_95 = _mean(tail_losses) if tail_losses else 0.0
    
    # Skewness (asymmetry)
    mean_pnl = _mean(pnl)
    std_pnl = _std(pnl)
    if std_pnl > 0 and n > 2:
        skewness = sum(((x - mean_pnl) / std_pnl) ** 3 for x in pnl) / n
    else:
        skewness = 0.0
    
    # Kurtosis (tail risk)
    if std_pnl > 0 and n > 3:
        kurtosis = sum(((x - mean_pnl) / std_pnl) ** 4 for x in pnl) / n - 3  # Excess kurtosis
    else:
        kurtosis = 0.0
    
    # Worst trade as % of capital
    worst_trade = min(pnl) if pnl else 0.0
    worst_trade_pct = (abs(worst_trade) / starting_balance * 100) if starting_balance > 0 else 0.0
    
    return {
        'var_95': var_95,
        'cvar_95': cvar_95,
        'skewness': skewness,
        'kurtosis': kurtosis,
        'worst_trade_pct': worst_trade_pct
    }


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
    
    # Consecutive performance analysis
    consecutive_stats = _compute_consecutive_stats(trades)
    
    # Recovery metrics
    recovery_factor = (net_profit / max_dd) if max_dd > 0 else 0.0
    
    # Estimate annualized return for Calmar (assuming we have duration data)
    total_duration_days = exposure / 86400 if exposure > 0 else 1
    annualized_return = (net_profit / summary.starting_balance * 365 / total_duration_days) if summary.starting_balance > 0 and total_duration_days > 0 else 0.0
    calmar_ratio = (annualized_return / max_dd_pct) if max_dd_pct > 0 else 0.0
    
    # Advanced drawdown metrics
    drawdown_stats = _compute_drawdown_details(curve)
    
    # Trade quality metrics
    win_loss_ratio = (avg_win / abs(avg_loss)) if avg_loss != 0 else 0.0
    edge_ratio = ((p_win * avg_win) / ((1 - p_win) * abs(avg_loss))) if avg_loss != 0 and p_win < 1 else 0.0
    profit_per_day = (net_profit / total_duration_days) if total_duration_days > 0 else 0.0
    
    # Risk metrics
    risk_stats = _compute_risk_metrics(pnl, summary.starting_balance)
    
    return RunMetrics(
        backtest_id=summary.backtest_id,
        total_trades=summary.total_trades,
        win_rate_pct=win_rate * 100,
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
        starting_balance=summary.starting_balance,
        roi_pct=(net_profit / summary.starting_balance * 100) if summary.starting_balance > 0 else 0.0,
        equity_curve=[p for _, p in curve],
        
        # Consecutive stats
        max_consecutive_wins=consecutive_stats['max_wins'],
        max_consecutive_losses=consecutive_stats['max_losses'],
        avg_win_streak=consecutive_stats['avg_win_streak'],
        avg_loss_streak=consecutive_stats['avg_loss_streak'],
        current_streak=consecutive_stats['current_streak'],
        
        # Recovery metrics
        recovery_factor=recovery_factor,
        calmar_ratio=calmar_ratio,
        mar_ratio=calmar_ratio,  # Using same as Calmar for now
        
        # Advanced drawdown
        avg_drawdown=drawdown_stats['avg_dd'],
        avg_drawdown_pct=drawdown_stats['avg_dd_pct'],
        drawdown_duration_avg_seconds=drawdown_stats['avg_duration'],
        underwater_pct=drawdown_stats['underwater_pct'],
        pain_index=drawdown_stats['pain_index'],
        
        # Trade quality
        win_loss_ratio=win_loss_ratio,
        edge_ratio=edge_ratio,
        profit_per_day=profit_per_day,
        
        # Risk metrics
        var_95=risk_stats['var_95'],
        cvar_95=risk_stats['cvar_95'],
        skewness=risk_stats['skewness'],
        kurtosis=risk_stats['kurtosis'],
        worst_trade_pct=risk_stats['worst_trade_pct']
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
