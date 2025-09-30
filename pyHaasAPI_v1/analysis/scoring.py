"""
Composite scoring and early-stopping utilities for backtests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .metrics import RunMetrics


@dataclass
class ScoreWeights:
    roi: float = 1.0
    drawdown: float = 2.0
    volatility: float = 0.5
    profit_factor: float = 1.0
    min_trades: int = 10
    min_profit_factor: float = 1.1


def composite_score(m: RunMetrics, w: ScoreWeights = ScoreWeights()) -> float:
    # Normalize some components to be broadly comparable
    roi_term = m.net_profit  # absolute PnL; ROI pct may be inconsistent per run horizon
    dd_penalty = -w.drawdown * m.max_drawdown
    vol_penalty = -w.volatility * m.volatility
    pf_bonus = w.profit_factor * (m.profit_factor if m.profit_factor != float('inf') else 3.0)

    base = w.roi * roi_term + dd_penalty + vol_penalty + pf_bonus

    # Hard gates
    if m.total_trades < w.min_trades:
        base *= 0.5
    if m.profit_factor < w.min_profit_factor and m.profit_factor != float('inf'):
        base *= 0.7

    return base
