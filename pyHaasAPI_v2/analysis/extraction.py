"""
Data extraction utilities for pyHaasAPI v2

This module provides data extraction capabilities for backtest analysis,
including trade data extraction, backtest summary generation, and
data validation utilities.

Based on the excellent v1 implementation from pyHaasAPI/analysis/extraction.py
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeData:
    """Individual trade data"""
    trade_id: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    quantity: float
    profit_loss: float
    fees: float
    duration_seconds: int
    side: str  # 'long' or 'short'
    market: str


@dataclass
class BacktestSummary:
    """Summary of backtest performance"""
    backtest_id: str
    lab_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    max_drawdown: float
    max_drawdown_pct: float
    starting_balance: float
    final_balance: float
    peak_balance: float
    trades: List[TradeData]
    backtest_timestamp: Optional[str] = None


class BacktestDataExtractor:
    """Extracts and processes backtest data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_backtest_summary(self, backtest_data: Dict[str, Any]) -> Optional[BacktestSummary]:
        """
        Extract backtest summary from raw backtest data
        
        Args:
            backtest_data: Raw backtest data from API
            
        Returns:
            BacktestSummary object or None if extraction fails
        """
        try:
            # Extract basic information
            backtest_id = backtest_data.get('backtest_id', '')
            lab_id = backtest_data.get('lab_id', '')
            
            # Extract trade data
            trades = self._extract_trades(backtest_data)
            if not trades:
                self.logger.warning(f"No trades found for backtest {backtest_id}")
                return None
            
            # Calculate summary metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.profit_loss > 0)
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0
            
            # Calculate P&L metrics
            total_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
            total_loss = abs(sum(t.profit_loss for t in trades if t.profit_loss < 0))
            net_profit = sum(t.profit_loss - t.fees for t in trades)
            
            # Calculate balance metrics
            starting_balance = backtest_data.get('starting_balance', 10000.0)
            final_balance = backtest_data.get('final_balance', starting_balance + net_profit)
            peak_balance = backtest_data.get('peak_balance', max(starting_balance, final_balance))
            
            # Calculate drawdown
            max_drawdown, max_drawdown_pct = self._calculate_drawdown(trades, starting_balance)
            
            return BacktestSummary(
                backtest_id=backtest_id,
                lab_id=lab_id,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_profit=total_profit,
                total_loss=total_loss,
                net_profit=net_profit,
                max_drawdown=max_drawdown,
                max_drawdown_pct=max_drawdown_pct,
                starting_balance=starting_balance,
                final_balance=final_balance,
                peak_balance=peak_balance,
                trades=trades,
                backtest_timestamp=backtest_data.get('timestamp')
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting backtest summary: {e}")
            return None
    
    def _extract_trades(self, backtest_data: Dict[str, Any]) -> List[TradeData]:
        """Extract trade data from backtest data"""
        trades = []
        
        try:
            # Look for trades in various possible locations
            trade_data = backtest_data.get('trades', [])
            if not trade_data:
                trade_data = backtest_data.get('trade_data', [])
            if not trade_data:
                trade_data = backtest_data.get('runtime_data', {}).get('trades', [])
            
            for trade in trade_data:
                try:
                    trade_obj = TradeData(
                        trade_id=str(trade.get('trade_id', '')),
                        entry_time=int(trade.get('entry_time', 0)),
                        exit_time=int(trade.get('exit_time', 0)),
                        entry_price=float(trade.get('entry_price', 0.0)),
                        exit_price=float(trade.get('exit_price', 0.0)),
                        quantity=float(trade.get('quantity', 0.0)),
                        profit_loss=float(trade.get('profit_loss', 0.0)),
                        fees=float(trade.get('fees', 0.0)),
                        duration_seconds=int(trade.get('duration_seconds', 0)),
                        side=str(trade.get('side', 'long')),
                        market=str(trade.get('market', ''))
                    )
                    trades.append(trade_obj)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Error parsing trade data: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error extracting trades: {e}")
        
        return trades
    
    def _calculate_drawdown(self, trades: List[TradeData], starting_balance: float) -> Tuple[float, float]:
        """Calculate maximum drawdown from trades"""
        if not trades:
            return 0.0, 0.0
        
        # Sort trades by exit time
        sorted_trades = sorted(trades, key=lambda t: t.exit_time)
        
        peak_balance = starting_balance
        max_drawdown = 0.0
        current_balance = starting_balance
        
        for trade in sorted_trades:
            current_balance += (trade.profit_loss - trade.fees)
            
            if current_balance > peak_balance:
                peak_balance = current_balance
            
            drawdown = peak_balance - current_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_pct = (max_drawdown / peak_balance) * 100 if peak_balance > 0 else 0.0
        
        return max_drawdown, max_drawdown_pct
    
    def extract_parameter_values(self, backtest_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract parameter values from backtest data"""
        try:
            # Look for parameters in various locations
            params = backtest_data.get('parameters', {})
            if not params:
                params = backtest_data.get('runtime_data', {}).get('parameters', {})
            if not params:
                params = backtest_data.get('parameter_values', {})
            
            # Convert all values to strings
            return {str(k): str(v) for k, v in params.items()}
            
        except Exception as e:
            self.logger.warning(f"Error extracting parameter values: {e}")
            return {}
    
    def validate_data_integrity(self, backtest_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate backtest data integrity and return validation results"""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'data_quality_score': 100.0
        }
        
        try:
            # Check required fields
            required_fields = ['backtest_id', 'lab_id']
            for field in required_fields:
                if field not in backtest_data or not backtest_data[field]:
                    validation_results['errors'].append(f"Missing required field: {field}")
                    validation_results['is_valid'] = False
            
            # Check trade data
            trades = self._extract_trades(backtest_data)
            if not trades:
                validation_results['warnings'].append("No trade data found")
                validation_results['data_quality_score'] -= 20.0
            
            # Check for data consistency
            if trades:
                # Check for negative durations
                negative_durations = sum(1 for t in trades if t.duration_seconds < 0)
                if negative_durations > 0:
                    validation_results['warnings'].append(f"{negative_durations} trades with negative duration")
                    validation_results['data_quality_score'] -= 10.0
                
                # Check for zero prices
                zero_prices = sum(1 for t in trades if t.entry_price <= 0 or t.exit_price <= 0)
                if zero_prices > 0:
                    validation_results['warnings'].append(f"{zero_prices} trades with zero or negative prices")
                    validation_results['data_quality_score'] -= 15.0
            
            # Ensure data quality score doesn't go below 0
            validation_results['data_quality_score'] = max(0.0, validation_results['data_quality_score'])
            
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {e}")
            validation_results['is_valid'] = False
            validation_results['data_quality_score'] = 0.0
        
        return validation_results
