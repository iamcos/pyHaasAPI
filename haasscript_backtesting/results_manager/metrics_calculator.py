"""
Advanced trading metrics calculation engine.
"""

import logging
import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

from ..models import Trade, PerformanceData, ExecutionMetrics


logger = logging.getLogger(__name__)


class TradingMetricsCalculator:
    """
    Advanced trading metrics calculation engine.
    
    Calculates comprehensive trading performance metrics including:
    - Risk-adjusted returns (Sharpe, Sortino, Calmar ratios)
    - Drawdown analysis (maximum, average, duration)
    - Risk metrics (VaR, CVaR, volatility)
    - Performance ratios (profit factor, payoff ratio, recovery factor)
    - Statistical measures (skewness, kurtosis, correlation)
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize metrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
    
    def calculate_comprehensive_metrics(
        self, 
        trade_history: List[Trade], 
        performance_data: PerformanceData,
        initial_balance: float,
        benchmark_returns: Optional[List[float]] = None
    ) -> ExecutionMetrics:
        """
        Calculate comprehensive trading metrics from trade history.
        
        Args:
            trade_history: List of executed trades
            performance_data: Basic performance statistics
            initial_balance: Starting balance for calculations
            benchmark_returns: Optional benchmark returns for beta/alpha calculation
            
        Returns:
            ExecutionMetrics with all calculated values
        """
        if not trade_history:
            return self._create_empty_metrics()
        
        self.logger.info(f"Calculating metrics for {len(trade_history)} trades")
        
        # Calculate returns series
        returns = self._calculate_returns_series(trade_history, initial_balance)
        daily_returns = self._aggregate_to_daily_returns(trade_history, returns)
        
        # Basic return metrics
        total_return = self._calculate_total_return(initial_balance, performance_data.final_balance)
        annualized_return = self._calculate_annualized_return(total_return, trade_history)
        
        # Risk metrics
        volatility = self._calculate_volatility(daily_returns)
        max_drawdown, max_dd_duration = self._calculate_max_drawdown(trade_history, initial_balance)
        
        # Risk-adjusted ratios
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns, volatility)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        calmar_ratio = self._calculate_calmar_ratio(annualized_return, max_drawdown)
        
        # Value at Risk metrics
        var_95 = self._calculate_var(daily_returns, 0.95)
        cvar_95 = self._calculate_cvar(daily_returns, 0.95)
        
        # Performance ratios
        profit_factor = performance_data.profit_factor
        recovery_factor = self._calculate_recovery_factor(total_return, max_drawdown)
        payoff_ratio = self._calculate_payoff_ratio(performance_data)
        
        # Market-relative metrics (if benchmark provided)
        beta, alpha = self._calculate_beta_alpha(daily_returns, benchmark_returns)
        
        return ExecutionMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            volatility=volatility,
            beta=beta,
            alpha=alpha,
            value_at_risk_95=var_95,
            conditional_var_95=cvar_95,
            calmar_ratio=calmar_ratio,
            profit_factor=profit_factor,
            recovery_factor=recovery_factor,
            payoff_ratio=payoff_ratio
        )
    
    def calculate_risk_metrics(self, returns: List[float]) -> Dict[str, float]:
        """
        Calculate comprehensive risk metrics.
        
        Args:
            returns: List of return values
            
        Returns:
            Dictionary of risk metrics
        """
        if not returns:
            return {}
        
        returns_array = np.array(returns)
        
        # Basic statistics
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array, ddof=1)
        
        # Distribution metrics
        skewness = stats.skew(returns_array)
        kurtosis = stats.kurtosis(returns_array)
        
        # Tail risk metrics
        var_99 = self._calculate_var(returns, 0.99)
        cvar_99 = self._calculate_cvar(returns, 0.99)
        
        # Downside metrics
        downside_returns = [r for r in returns if r < 0]
        downside_deviation = np.std(downside_returns) if downside_returns else 0.0
        
        # Maximum consecutive losses
        max_consecutive_losses = self._calculate_max_consecutive_losses(returns)
        
        return {
            'mean_return': mean_return,
            'volatility': std_return,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'var_95': self._calculate_var(returns, 0.95),
            'var_99': var_99,
            'cvar_95': self._calculate_cvar(returns, 0.95),
            'cvar_99': cvar_99,
            'downside_deviation': downside_deviation,
            'max_consecutive_losses': max_consecutive_losses,
            'positive_periods': len([r for r in returns if r > 0]),
            'negative_periods': len([r for r in returns if r < 0])
        }
    
    def calculate_performance_attribution(
        self, 
        trade_history: List[Trade],
        market_segments: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate performance attribution by different factors.
        
        Args:
            trade_history: List of executed trades
            market_segments: Optional market segment definitions
            
        Returns:
            Performance attribution analysis
        """
        if not trade_history:
            return {}
        
        # Time-based attribution
        time_attribution = self._calculate_time_attribution(trade_history)
        
        # Trade size attribution
        size_attribution = self._calculate_size_attribution(trade_history)
        
        # Duration attribution
        duration_attribution = self._calculate_duration_attribution(trade_history)
        
        return {
            'time_attribution': time_attribution,
            'size_attribution': size_attribution,
            'duration_attribution': duration_attribution,
            'total_trades': len(trade_history),
            'analysis_date': datetime.now().isoformat()
        }
    
    def _calculate_returns_series(self, trades: List[Trade], initial_balance: float) -> List[float]:
        """Calculate returns series from trade history."""
        returns = []
        current_balance = initial_balance
        
        for trade in trades:
            if trade.profit_loss is not None:
                trade_return = trade.profit_loss / current_balance
                returns.append(trade_return)
                current_balance += trade.profit_loss
        
        return returns
    
    def _aggregate_to_daily_returns(self, trades: List[Trade], returns: List[float]) -> List[float]:
        """Aggregate trade returns to daily returns."""
        if not trades or not returns:
            return []
        
        # Group trades by date
        daily_groups = {}
        for i, trade in enumerate(trades):
            if i < len(returns):
                date_key = trade.timestamp.date()
                if date_key not in daily_groups:
                    daily_groups[date_key] = []
                daily_groups[date_key].append(returns[i])
        
        # Sum returns for each day
        daily_returns = []
        for date in sorted(daily_groups.keys()):
            daily_return = sum(daily_groups[date])
            daily_returns.append(daily_return)
        
        return daily_returns
    
    def _calculate_total_return(self, initial_balance: float, final_balance: float) -> float:
        """Calculate total return percentage."""
        if initial_balance <= 0:
            return 0.0
        return ((final_balance - initial_balance) / initial_balance) * 100
    
    def _calculate_annualized_return(self, total_return: float, trades: List[Trade]) -> float:
        """Calculate annualized return."""
        if not trades:
            return 0.0
        
        # Calculate time period in years
        start_date = min(trade.timestamp for trade in trades)
        end_date = max(trade.timestamp for trade in trades)
        days = (end_date - start_date).days
        years = max(days / 365.25, 1/365.25)  # Minimum 1 day
        
        # Annualize the return
        return ((1 + total_return / 100) ** (1 / years) - 1) * 100
    
    def _calculate_volatility(self, daily_returns: List[float]) -> float:
        """Calculate annualized volatility."""
        if len(daily_returns) < 2:
            return 0.0
        
        daily_vol = np.std(daily_returns, ddof=1)
        return daily_vol * math.sqrt(252)  # Annualize assuming 252 trading days
    
    def _calculate_sharpe_ratio(self, daily_returns: List[float], volatility: float) -> float:
        """Calculate Sharpe ratio."""
        if not daily_returns or volatility == 0:
            return 0.0
        
        mean_daily_return = np.mean(daily_returns)
        daily_risk_free = self.risk_free_rate / 252  # Daily risk-free rate
        
        excess_return = mean_daily_return - daily_risk_free
        daily_sharpe = excess_return / (volatility / math.sqrt(252))
        
        return daily_sharpe * math.sqrt(252)  # Annualize
    
    def _calculate_sortino_ratio(self, daily_returns: List[float]) -> float:
        """Calculate Sortino ratio using downside deviation."""
        if not daily_returns:
            return 0.0
        
        mean_return = np.mean(daily_returns)
        daily_risk_free = self.risk_free_rate / 252
        
        # Calculate downside deviation
        downside_returns = [r for r in daily_returns if r < daily_risk_free]
        if not downside_returns:
            return float('inf') if mean_return > daily_risk_free else 0.0
        
        downside_deviation = np.std(downside_returns, ddof=1)
        
        if downside_deviation == 0:
            return 0.0
        
        excess_return = mean_return - daily_risk_free
        daily_sortino = excess_return / downside_deviation
        
        return daily_sortino * math.sqrt(252)  # Annualize
    
    def _calculate_calmar_ratio(self, annualized_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio."""
        if max_drawdown == 0:
            return float('inf') if annualized_return > 0 else 0.0
        return (annualized_return / 100) / abs(max_drawdown / 100)
    
    def _calculate_max_drawdown(self, trades: List[Trade], initial_balance: float) -> Tuple[float, timedelta]:
        """Calculate maximum drawdown and its duration."""
        if not trades:
            return 0.0, timedelta()
        
        # Build equity curve
        equity_curve = [initial_balance]
        current_balance = initial_balance
        
        for trade in trades:
            if trade.profit_loss is not None:
                current_balance += trade.profit_loss
                equity_curve.append(current_balance)
        
        # Calculate drawdowns
        peak = equity_curve[0]
        max_dd = 0.0
        max_dd_duration = timedelta()
        current_dd_start = None
        
        for i, balance in enumerate(equity_curve):
            if balance > peak:
                peak = balance
                current_dd_start = None
            else:
                # In drawdown
                if current_dd_start is None and i < len(trades):
                    current_dd_start = trades[i].timestamp
                
                drawdown = (peak - balance) / peak * 100
                if drawdown > max_dd:
                    max_dd = drawdown
                    if current_dd_start and i < len(trades):
                        max_dd_duration = trades[i].timestamp - current_dd_start
        
        return max_dd, max_dd_duration
    
    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """Calculate Value at Risk at given confidence level."""
        if not returns:
            return 0.0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return sorted_returns[index] if index < len(sorted_returns) else 0.0
    
    def _calculate_cvar(self, returns: List[float], confidence: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)."""
        var = self._calculate_var(returns, confidence)
        tail_returns = [r for r in returns if r <= var]
        return np.mean(tail_returns) if tail_returns else 0.0
    
    def _calculate_recovery_factor(self, total_return: float, max_drawdown: float) -> float:
        """Calculate recovery factor."""
        if max_drawdown == 0:
            return float('inf') if total_return > 0 else 0.0
        return (total_return / 100) / abs(max_drawdown / 100)
    
    def _calculate_payoff_ratio(self, performance_data: PerformanceData) -> float:
        """Calculate payoff ratio (average win / average loss)."""
        if performance_data.average_loss == 0:
            return float('inf') if performance_data.average_win > 0 else 0.0
        return performance_data.average_win / abs(performance_data.average_loss)
    
    def _calculate_beta_alpha(
        self, 
        returns: List[float], 
        benchmark_returns: Optional[List[float]]
    ) -> Tuple[float, float]:
        """Calculate beta and alpha relative to benchmark."""
        if not benchmark_returns or len(returns) != len(benchmark_returns):
            return 0.0, 0.0
        
        try:
            # Calculate beta using linear regression
            returns_array = np.array(returns)
            benchmark_array = np.array(benchmark_returns)
            
            covariance = np.cov(returns_array, benchmark_array)[0, 1]
            benchmark_variance = np.var(benchmark_array, ddof=1)
            
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 0.0
            
            # Calculate alpha
            mean_return = np.mean(returns_array)
            mean_benchmark = np.mean(benchmark_array)
            daily_risk_free = self.risk_free_rate / 252
            
            alpha = mean_return - (daily_risk_free + beta * (mean_benchmark - daily_risk_free))
            alpha_annualized = alpha * 252  # Annualize
            
            return beta, alpha_annualized
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate beta/alpha: {e}")
            return 0.0, 0.0
    
    def _calculate_max_consecutive_losses(self, returns: List[float]) -> int:
        """Calculate maximum consecutive losing periods."""
        max_consecutive = 0
        current_consecutive = 0
        
        for return_val in returns:
            if return_val < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _calculate_time_attribution(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate performance attribution by time periods."""
        if not trades:
            return {}
        
        # Group by hour of day
        hourly_pnl = {}
        for trade in trades:
            if trade.profit_loss is not None:
                hour = trade.timestamp.hour
                if hour not in hourly_pnl:
                    hourly_pnl[hour] = []
                hourly_pnl[hour].append(trade.profit_loss)
        
        # Calculate statistics for each hour
        hourly_stats = {}
        for hour, pnl_list in hourly_pnl.items():
            hourly_stats[hour] = {
                'total_pnl': sum(pnl_list),
                'avg_pnl': np.mean(pnl_list),
                'trade_count': len(pnl_list),
                'win_rate': len([p for p in pnl_list if p > 0]) / len(pnl_list) * 100
            }
        
        return {
            'hourly_attribution': hourly_stats,
            'best_hour': max(hourly_stats.keys(), key=lambda h: hourly_stats[h]['total_pnl']) if hourly_stats else None,
            'worst_hour': min(hourly_stats.keys(), key=lambda h: hourly_stats[h]['total_pnl']) if hourly_stats else None
        }
    
    def _calculate_size_attribution(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate performance attribution by trade size."""
        if not trades:
            return {}
        
        # Define size buckets based on trade amounts
        amounts = [trade.amount for trade in trades if trade.amount > 0]
        if not amounts:
            return {}
        
        # Create quartile buckets
        q1, q2, q3 = np.percentile(amounts, [25, 50, 75])
        
        size_buckets = {
            'small': [],
            'medium_small': [],
            'medium_large': [],
            'large': []
        }
        
        for trade in trades:
            if trade.profit_loss is not None and trade.amount > 0:
                if trade.amount <= q1:
                    size_buckets['small'].append(trade.profit_loss)
                elif trade.amount <= q2:
                    size_buckets['medium_small'].append(trade.profit_loss)
                elif trade.amount <= q3:
                    size_buckets['medium_large'].append(trade.profit_loss)
                else:
                    size_buckets['large'].append(trade.profit_loss)
        
        # Calculate statistics for each bucket
        bucket_stats = {}
        for bucket_name, pnl_list in size_buckets.items():
            if pnl_list:
                bucket_stats[bucket_name] = {
                    'total_pnl': sum(pnl_list),
                    'avg_pnl': np.mean(pnl_list),
                    'trade_count': len(pnl_list),
                    'win_rate': len([p for p in pnl_list if p > 0]) / len(pnl_list) * 100
                }
        
        return {
            'size_buckets': bucket_stats,
            'quartiles': {'q1': q1, 'q2': q2, 'q3': q3}
        }
    
    def _calculate_duration_attribution(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate performance attribution by trade duration."""
        duration_trades = [trade for trade in trades if trade.duration is not None and trade.profit_loss is not None]
        
        if not duration_trades:
            return {}
        
        # Group by duration buckets
        duration_buckets = {
            'very_short': [],  # < 1 hour
            'short': [],       # 1-6 hours
            'medium': [],      # 6-24 hours
            'long': [],        # 1-7 days
            'very_long': []    # > 7 days
        }
        
        for trade in duration_trades:
            duration_hours = trade.duration.total_seconds() / 3600
            
            if duration_hours < 1:
                duration_buckets['very_short'].append(trade.profit_loss)
            elif duration_hours < 6:
                duration_buckets['short'].append(trade.profit_loss)
            elif duration_hours < 24:
                duration_buckets['medium'].append(trade.profit_loss)
            elif duration_hours < 168:  # 7 days
                duration_buckets['long'].append(trade.profit_loss)
            else:
                duration_buckets['very_long'].append(trade.profit_loss)
        
        # Calculate statistics for each bucket
        bucket_stats = {}
        for bucket_name, pnl_list in duration_buckets.items():
            if pnl_list:
                bucket_stats[bucket_name] = {
                    'total_pnl': sum(pnl_list),
                    'avg_pnl': np.mean(pnl_list),
                    'trade_count': len(pnl_list),
                    'win_rate': len([p for p in pnl_list if p > 0]) / len(pnl_list) * 100
                }
        
        return {
            'duration_buckets': bucket_stats,
            'avg_duration_hours': np.mean([t.duration.total_seconds() / 3600 for t in duration_trades])
        }
    
    def _create_empty_metrics(self) -> ExecutionMetrics:
        """Create empty execution metrics for backtests with no trades."""
        return ExecutionMetrics(
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_duration=timedelta(),
            volatility=0.0,
            beta=0.0,
            alpha=0.0,
            value_at_risk_95=0.0,
            conditional_var_95=0.0,
            calmar_ratio=0.0,
            profit_factor=0.0,
            recovery_factor=0.0,
            payoff_ratio=0.0
        )