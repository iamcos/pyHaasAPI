"""
Tests for the trading metrics calculation engine.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from ..results_manager.metrics_calculator import TradingMetricsCalculator
from ..models import Trade, PerformanceData, TradeType, TradeStatus


class TestTradingMetricsCalculator:
    """Test cases for TradingMetricsCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = TradingMetricsCalculator(risk_free_rate=0.02)
        
        # Create sample trade history
        self.sample_trades = [
            Trade(
                trade_id="trade_1",
                timestamp=datetime(2024, 1, 1, 10, 0),
                trade_type=TradeType.ACTION_A,
                price=100.0,
                amount=1.0,
                fee=0.1,
                status=TradeStatus.CLOSED,
                profit_loss=50.0,
                duration=timedelta(hours=2)
            ),
            Trade(
                trade_id="trade_2",
                timestamp=datetime(2024, 1, 1, 14, 0),
                trade_type=TradeType.ACTION_B,
                price=150.0,
                amount=1.0,
                fee=0.1,
                status=TradeStatus.CLOSED,
                profit_loss=-20.0,
                duration=timedelta(hours=1)
            ),
            Trade(
                trade_id="trade_3",
                timestamp=datetime(2024, 1, 2, 9, 0),
                trade_type=TradeType.ACTION_A,
                price=120.0,
                amount=1.5,
                fee=0.15,
                status=TradeStatus.CLOSED,
                profit_loss=75.0,
                duration=timedelta(hours=3)
            )
        ]
        
        # Create sample performance data
        self.sample_performance = PerformanceData(
            initial_balance=10000.0,
            final_balance=10105.0,
            peak_balance=10175.0,
            lowest_balance=9980.0,
            total_trades=3,
            winning_trades=2,
            losing_trades=1,
            largest_win=75.0,
            largest_loss=-20.0,
            average_win=62.5,
            average_loss=-20.0,
            total_time_in_market=timedelta(hours=6),
            average_trade_duration=timedelta(hours=2),
            longest_winning_streak=2,
            longest_losing_streak=1
        )
    
    def test_calculate_comprehensive_metrics_with_trades(self):
        """Test comprehensive metrics calculation with valid trades."""
        metrics = self.calculator.calculate_comprehensive_metrics(
            trade_history=self.sample_trades,
            performance_data=self.sample_performance,
            initial_balance=10000.0
        )
        
        # Verify basic metrics
        assert metrics.total_return > 0  # Should be profitable
        assert metrics.volatility >= 0
        assert metrics.max_drawdown >= 0
        assert metrics.profit_factor > 0
        
        # Verify risk-adjusted ratios
        assert isinstance(metrics.sharpe_ratio, float)
        assert isinstance(metrics.sortino_ratio, float)
        assert isinstance(metrics.calmar_ratio, float)
        
        # Verify risk metrics
        assert isinstance(metrics.value_at_risk_95, float)
        assert isinstance(metrics.conditional_var_95, float)
    
    def test_calculate_comprehensive_metrics_empty_trades(self):
        """Test metrics calculation with empty trade history."""
        metrics = self.calculator.calculate_comprehensive_metrics(
            trade_history=[],
            performance_data=self.sample_performance,
            initial_balance=10000.0
        )
        
        # All metrics should be zero for empty trades
        assert metrics.total_return == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.volatility == 0.0
        assert metrics.max_drawdown == 0.0
    
    def test_calculate_risk_metrics(self):
        """Test risk metrics calculation."""
        returns = [0.01, -0.005, 0.02, -0.01, 0.015, -0.008, 0.012]
        
        risk_metrics = self.calculator.calculate_risk_metrics(returns)
        
        # Verify all expected metrics are present
        expected_keys = [
            'mean_return', 'volatility', 'skewness', 'kurtosis',
            'var_95', 'var_99', 'cvar_95', 'cvar_99',
            'downside_deviation', 'max_consecutive_losses',
            'positive_periods', 'negative_periods'
        ]
        
        for key in expected_keys:
            assert key in risk_metrics
            assert isinstance(risk_metrics[key], (int, float))
        
        # Verify logical relationships
        assert risk_metrics['positive_periods'] + risk_metrics['negative_periods'] <= len(returns)
        assert risk_metrics['var_99'] <= risk_metrics['var_95']  # 99% VaR should be more extreme
    
    def test_calculate_performance_attribution(self):
        """Test performance attribution analysis."""
        attribution = self.calculator.calculate_performance_attribution(self.sample_trades)
        
        # Verify structure
        assert 'time_attribution' in attribution
        assert 'size_attribution' in attribution
        assert 'duration_attribution' in attribution
        assert 'total_trades' in attribution
        
        # Verify time attribution
        time_attr = attribution['time_attribution']
        assert 'hourly_attribution' in time_attr
        assert isinstance(time_attr['hourly_attribution'], dict)
        
        # Verify size attribution
        size_attr = attribution['size_attribution']
        assert 'size_buckets' in size_attr
        assert 'quartiles' in size_attr
        
        # Verify duration attribution
        duration_attr = attribution['duration_attribution']
        assert 'duration_buckets' in duration_attr
        assert 'avg_duration_hours' in duration_attr
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation with known values."""
        # Create returns with known characteristics
        daily_returns = [0.01] * 10 + [-0.005] * 5  # Mix of positive and negative returns
        
        sharpe = self.calculator._calculate_sharpe_ratio(daily_returns, 0.1)  # 10% volatility
        
        # Sharpe ratio should be a finite number
        assert isinstance(sharpe, float)
        assert not (sharpe == float('inf') or sharpe == float('-inf'))
    
    def test_sortino_ratio_calculation(self):
        """Test Sortino ratio calculation."""
        daily_returns = [0.02, -0.01, 0.015, -0.008, 0.01, -0.005]
        
        sortino = self.calculator._calculate_sortino_ratio(daily_returns)
        
        # Sortino ratio should be a finite number
        assert isinstance(sortino, float)
        assert not (sortino == float('inf') or sortino == float('-inf'))
    
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        max_dd, duration = self.calculator._calculate_max_drawdown(self.sample_trades, 10000.0)
        
        # Drawdown should be non-negative percentage
        assert max_dd >= 0
        assert isinstance(duration, timedelta)
    
    def test_var_cvar_calculation(self):
        """Test VaR and CVaR calculations."""
        returns = [-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.05]
        
        var_95 = self.calculator._calculate_var(returns, 0.95)
        cvar_95 = self.calculator._calculate_cvar(returns, 0.95)
        
        # CVaR should be more extreme than VaR
        assert cvar_95 <= var_95
        assert isinstance(var_95, float)
        assert isinstance(cvar_95, float)
    
    def test_beta_alpha_calculation(self):
        """Test beta and alpha calculation with benchmark."""
        returns = [0.01, -0.005, 0.02, -0.01, 0.015]
        benchmark_returns = [0.008, -0.003, 0.015, -0.008, 0.012]
        
        beta, alpha = self.calculator._calculate_beta_alpha(returns, benchmark_returns)
        
        # Beta and alpha should be finite numbers
        assert isinstance(beta, float)
        assert isinstance(alpha, float)
        assert not (beta == float('inf') or beta == float('-inf'))
        assert not (alpha == float('inf') or alpha == float('-inf'))
    
    def test_beta_alpha_no_benchmark(self):
        """Test beta and alpha calculation without benchmark."""
        returns = [0.01, -0.005, 0.02, -0.01, 0.015]
        
        beta, alpha = self.calculator._calculate_beta_alpha(returns, None)
        
        # Should return zeros when no benchmark provided
        assert beta == 0.0
        assert alpha == 0.0
    
    def test_time_attribution_analysis(self):
        """Test time-based performance attribution."""
        attribution = self.calculator._calculate_time_attribution(self.sample_trades)
        
        assert 'hourly_attribution' in attribution
        assert 'best_hour' in attribution
        assert 'worst_hour' in attribution
        
        # Verify hourly stats structure
        hourly_stats = attribution['hourly_attribution']
        for hour, stats in hourly_stats.items():
            assert 'total_pnl' in stats
            assert 'avg_pnl' in stats
            assert 'trade_count' in stats
            assert 'win_rate' in stats
            assert 0 <= stats['win_rate'] <= 100
    
    def test_size_attribution_analysis(self):
        """Test size-based performance attribution."""
        attribution = self.calculator._calculate_size_attribution(self.sample_trades)
        
        assert 'size_buckets' in attribution
        assert 'quartiles' in attribution
        
        # Verify quartiles
        quartiles = attribution['quartiles']
        assert 'q1' in quartiles
        assert 'q2' in quartiles
        assert 'q3' in quartiles
        assert quartiles['q1'] <= quartiles['q2'] <= quartiles['q3']
    
    def test_duration_attribution_analysis(self):
        """Test duration-based performance attribution."""
        attribution = self.calculator._calculate_duration_attribution(self.sample_trades)
        
        assert 'duration_buckets' in attribution
        assert 'avg_duration_hours' in attribution
        
        # Verify average duration is reasonable
        avg_duration = attribution['avg_duration_hours']
        assert avg_duration > 0
        assert avg_duration < 24 * 365  # Less than a year
    
    def test_consecutive_losses_calculation(self):
        """Test maximum consecutive losses calculation."""
        returns = [0.01, -0.005, -0.01, -0.008, 0.02, -0.003]
        
        max_consecutive = self.calculator._calculate_max_consecutive_losses(returns)
        
        # Should find the streak of 3 consecutive losses
        assert max_consecutive == 3
    
    def test_empty_returns_handling(self):
        """Test handling of empty returns lists."""
        risk_metrics = self.calculator.calculate_risk_metrics([])
        
        # Should return empty dict for empty returns
        assert risk_metrics == {}
        
        # Test other methods with empty returns
        var = self.calculator._calculate_var([], 0.95)
        cvar = self.calculator._calculate_cvar([], 0.95)
        
        assert var == 0.0
        assert cvar == 0.0
    
    def test_single_trade_metrics(self):
        """Test metrics calculation with single trade."""
        single_trade = [self.sample_trades[0]]
        
        metrics = self.calculator.calculate_comprehensive_metrics(
            trade_history=single_trade,
            performance_data=self.sample_performance,
            initial_balance=10000.0
        )
        
        # Should handle single trade gracefully
        assert isinstance(metrics.total_return, float)
        assert metrics.volatility >= 0
    
    def test_risk_free_rate_impact(self):
        """Test impact of different risk-free rates."""
        calculator_low = TradingMetricsCalculator(risk_free_rate=0.01)
        calculator_high = TradingMetricsCalculator(risk_free_rate=0.05)
        
        daily_returns = [0.01, 0.02, -0.005, 0.015, -0.01]
        
        sharpe_low = calculator_low._calculate_sharpe_ratio(daily_returns, 0.1)
        sharpe_high = calculator_high._calculate_sharpe_ratio(daily_returns, 0.1)
        
        # Higher risk-free rate should generally result in lower Sharpe ratio
        # (assuming positive returns)
        if sum(daily_returns) > 0:
            assert sharpe_low >= sharpe_high