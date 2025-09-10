"""
Analysis models for pyHaasAPI

This module contains data classes for comprehensive backtest analysis,
bot creation results, and lab analysis results.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class DrawdownEvent:
    """Individual drawdown event"""
    timestamp: str
    balance: float
    drawdown_amount: float
    drawdown_percentage: float

@dataclass
class DrawdownAnalysis:
    """Comprehensive drawdown analysis"""
    max_drawdown_percentage: float
    lowest_balance: float
    drawdown_count: int  # Number of times balance went below zero
    drawdown_events: List[DrawdownEvent]  # List of all drawdown events
    balance_history: List[float]  # Balance progression over time
    
    # Robustness analysis fields
    max_drawdown_duration_days: int = 0
    max_consecutive_losses: int = 0
    worst_drawdown_start: Optional[datetime] = None
    worst_drawdown_end: Optional[datetime] = None
    account_blowup_risk: bool = False
    safe_leverage_multiplier: float = 1.0

@dataclass
class BacktestAnalysis:
    """Comprehensive backtest analysis data"""
    backtest_id: str
    lab_id: str
    generation_idx: Optional[int]
    population_idx: Optional[int]
    market_tag: str
    script_id: str
    script_name: str
    
    # Performance metrics
    roi_percentage: float  # ROI from lab data
    calculated_roi_percentage: float  # ROI calculated from trades (ROE)
    roi_difference: float  # Difference between lab ROI and calculated ROI
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    pc_value: float
    
    # Additional metrics
    avg_profit_per_trade: float
    profit_factor: float
    sharpe_ratio: float
    
    # Balance information
    starting_balance: float  # Starting account balance
    final_balance: float     # Final account balance
    peak_balance: float      # Peak account balance reached
    
    # Timestamps
    analysis_timestamp: str
    
    # Optional fields (must be at the end)
    drawdown_analysis: Optional[DrawdownAnalysis] = None
    backtest_timestamp: Optional[str] = None


@dataclass
class BotCreationResult:
    """Result of bot creation"""
    bot_id: str
    bot_name: str
    backtest_id: str
    account_id: str
    market_tag: str
    leverage: float
    margin_mode: str
    position_mode: str
    trade_amount_usdt: float
    creation_timestamp: str
    success: bool
    activated: bool = False
    error_message: Optional[str] = None


@dataclass
class LabAnalysisResult:
    """Complete lab analysis result"""
    lab_id: str
    lab_name: str
    total_backtests: int
    analyzed_backtests: int
    top_backtests: List[BacktestAnalysis]
    bots_created: List[BotCreationResult]
    analysis_timestamp: str
    processing_time: float
