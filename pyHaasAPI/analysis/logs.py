"""
Backtest log analyzer: fetch and classify errors/warnings from backtest logs.
Parameter-agnostic; relies on message patterns only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Patterns for common issues
_PATTERNS = {
    'insufficient_funds': re.compile(r"insufficient (funds|balance)|not enough (funds|balance)|insufficient margin", re.I),
    'order_rejected': re.compile(r"order rejected|reduce only conflict|min (notional|qty)|invalid quantity|price precision", re.I),
    'rate_limit': re.compile(r"rate limit|429", re.I),
    'timeout': re.compile(r"timeout|504|gateway timeout", re.I),
    'server_error': re.compile(r"5\d\d|internal server error", re.I),
    'script_error': re.compile(r"exception|traceback|division by zero|index out of range|keyerror|typeerror|valueerror", re.I),
    'warning': re.compile(r"warn|warning", re.I),
}


@dataclass
class BacktestRunAudit:
    backtest_id: str
    flags: Dict[str, bool]
    counts: Dict[str, int]
    first_error: Optional[str]
    first_error_at_index: Optional[int]


def analyze_logs(backtest_id: str, log_lines: List[str]) -> BacktestRunAudit:
    flags = {k: False for k in _PATTERNS}
    counts = {k: 0 for k in _PATTERNS}

    first_error = None
    first_error_idx: Optional[int] = None

    for idx, line in enumerate(log_lines):
        for key, pattern in _PATTERNS.items():
            if pattern.search(line or ""):
                counts[key] += 1
                flags[key] = True
                if first_error is None and key in {'insufficient_funds','order_rejected','timeout','server_error','script_error'}:
                    first_error = line.strip()
                    first_error_idx = idx

    return BacktestRunAudit(
        backtest_id=backtest_id,
        flags=flags,
        counts=counts,
        first_error=first_error,
        first_error_at_index=first_error_idx,
    )
