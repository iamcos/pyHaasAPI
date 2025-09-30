#!/usr/bin/env python3
"""
BacktestObject - Unified backtest data aggregation and management
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetadata:
    """Core backtest metadata"""
    backtest_id: str
    lab_id: str
    script_id: str
    script_name: str
    account_id: str
    market_tag: str
    status: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    is_archived: bool = False


@dataclass
class BacktestRuntime:
    """Runtime statistics and performance data"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_profit: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    execution_time_ms: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestPosition:
    """Individual position/trade data"""
    position_id: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    side: str  # 'long' or 'short'
    profit_loss: float
    fees: float = 0.0
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestLogs:
    """Execution logs and debug information"""
    compilation_errors: List[str] = field(default_factory=list)
    runtime_errors: List[str] = field(default_factory=list)
    debug_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_logs: str = ""


class BacktestObject:
    """
    Unified backtest data object that aggregates all backtest information
    with lazy loading for heavy data like chart partitions.
    """
    
    def __init__(self, executor, lab_id: str, backtest_id: str):
        self.executor = executor
        self.lab_id = lab_id
        self.backtest_id = backtest_id
        
        # Core data - loaded immediately
        self.metadata: Optional[BacktestMetadata] = None
        self.runtime: Optional[BacktestRuntime] = None
        self.logs: Optional[BacktestLogs] = None
        
        # Heavy data - loaded on demand
        self._positions: Optional[List[BacktestPosition]] = None
        self._chart_partition: Optional[Dict[str, Any]] = None
        
        # Load core data immediately
        self._load_core_data()
    
    def _load_core_data(self):
        """Load essential backtest data from a single, comprehensive API call."""
        try:
            from pyHaasAPI_v1 import api
            from pyHaasAPI_v1.model import BacktestRuntimeData, Report

            full_runtime_data: BacktestRuntimeData = api.get_full_backtest_runtime_data(self.executor, self.lab_id, self.backtest_id)

            start_time_dt = datetime.fromtimestamp(full_runtime_data.ActivatedSince) if full_runtime_data.ActivatedSince else None
            end_time_dt = datetime.fromtimestamp(full_runtime_data.Timestamp) if full_runtime_data.Timestamp else None

            self.metadata = BacktestMetadata(
                backtest_id=self.backtest_id,
                lab_id=self.lab_id,
                script_id=full_runtime_data.ScriptId,
                script_name=full_runtime_data.ScriptName,
                account_id=full_runtime_data.AccountId,
                market_tag=full_runtime_data.PriceMarket,
                status=full_runtime_data.Chart.Status if full_runtime_data.Chart else 0,
                start_time=start_time_dt,
                end_time=end_time_dt,
                execution_start=start_time_dt,
                execution_end=end_time_dt,
                is_archived=False  # This info is not in the new model
            )

            report_key = f"{full_runtime_data.AccountId}_{full_runtime_data.PriceMarket}"
            report_data: Optional[Report] = full_runtime_data.Reports.get(report_key)

            if report_data:
                # Calculate win rate properly: winning_trades / total_trades
                total_trades = report_data.P.C
                winning_trades = report_data.P.W
                win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0

                self.runtime = BacktestRuntime(
                    total_trades=total_trades,
                    winning_trades=winning_trades,
                    losing_trades=total_trades - winning_trades, # Calculate losing trades
                    win_rate=win_rate,  # Use calculated win rate instead of potentially incorrect API value
                    total_profit=report_data.PR.RP,
                    max_drawdown=report_data.PR.RM,
                    sharpe_ratio=report_data.T.SHR,
                    profit_factor=report_data.T.PF,
                    execution_time_ms=0, # This info is not in the new model
                    raw_data=report_data.model_dump()
                )
            else:
                self.runtime = BacktestRuntime()


            self.logs = BacktestLogs(
                compilation_errors=full_runtime_data.CompilerErrors,
                runtime_errors=[],  # Not directly available
                debug_messages=full_runtime_data.ExecutionLog,
                warnings=[],  # Not directly available
                raw_logs=json.dumps(full_runtime_data.ExecutionLog)
            )

            self._positions = []
            for pos_data in full_runtime_data.FinishedPositions:
                try:
                    # Determine exit price from exit orders
                    exit_price = 0
                    if pos_data.exo:
                        exit_price = pos_data.exo[0].p

                    self._positions.append(BacktestPosition(
                        position_id=pos_data.pg,
                        entry_time=datetime.fromtimestamp(pos_data.ot),
                        exit_time=datetime.fromtimestamp(pos_data.ct),
                        entry_price=pos_data.ap,
                        exit_price=exit_price,
                        quantity=pos_data.t,
                        side='long' if pos_data.d == 2 else 'short',
                        profit_loss=pos_data.rp,
                        fees=pos_data.fe,
                        raw_data=pos_data.model_dump()
                    ))
                except Exception as pos_e:
                    logger.warning(f"Error processing position data: {pos_e} - {pos_data}")

            self._chart_partition = full_runtime_data.Chart.model_dump() if full_runtime_data.Chart else {}

        except Exception as e:
            logger.error(f"Error loading core backtest data for {self.backtest_id}: {e}")
            raise
    
    
    
    @property
    def positions(self) -> List[BacktestPosition]:
        """Returns the loaded positions."""
        return self._positions or []

    @property
    def chart_partition(self) -> Optional[Dict[str, Any]]:
        """Lazy load chart partition data."""
        if self._chart_partition is None:
            self._load_chart_partition()
        return self._chart_partition

    def _load_chart_partition(self):
        """Load chart partition data using the Labs API."""
        try:
            from pyHaasAPI_v1 import api
            result = api.get_backtest_chart_partition(self.executor, self.lab_id, self.backtest_id)
            if result and result.get("Success"):
                self._chart_partition = result.get("Data", {})
            else:
                logger.warning(f"Could not load chart partition for {self.backtest_id}")
        except Exception as e:
            logger.error(f"Error loading chart partition for {self.backtest_id}: {e}")

