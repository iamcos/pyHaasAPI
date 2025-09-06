"""
Analysis models for pyHaasAPI

This module contains data classes for comprehensive backtest analysis,
bot creation results, and lab analysis results.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


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
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    pc_value: float
    
    # Additional metrics
    avg_profit_per_trade: float
    profit_factor: float
    sharpe_ratio: float
    
    # Timestamps
    analysis_timestamp: str
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
