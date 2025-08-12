#!/usr/bin/env python3
"""
Advanced Heuristics Analysis System

This module implements multiple analysis heuristics for identifying top-performing
and diverse backtest configurations, as outlined in the development plan:
- Equity Curve Stability
- Performance Metrics
- Trades Analysis
- Risk Analysis
- Trades Distribution
- Realized vs Open Profit Analysis
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from data_extractor import BacktestSummary, TradeData
import logging

logger = logging.getLogger(__name__)

@dataclass
class HeuristicScore:
    """Individual heuristic score with explanation"""
    name: str
    score: float
    max_score: float
    explanation: str
    details: Dict[str, Any]

@dataclass
class ConfigurationAnalysis:
    """Complete analysis of a backtest configuration"""
    backtest_id: str
    backtest_summary: BacktestSummary
    heuristic_scores: List[HeuristicScore]
    overall_score: float
    rank: int
    diversity_factors: Dict[str, float]
    recommendation: str

class HeuristicsAnalyzer:
    """Main class for applying multiple heuristics to backtest results"""
    
    def __init__(self, weight_config: Optional[Dict[str, float]] = None):
        """
        Initialize with configurable weights for different heuristics
        
        Args:
            weight_config: Dictionary of heuristic weights (defaults to equal weighting)
        """
        self.weights = weight_config or {
            'equity_curve_stability': 1.0,
            'performance_metrics': 1.0,
            'trades_analysis': 1.0,
            'risk_analysis': 1.0,
            'trades_distribution': 1.0,
            'realized_vs_open': 1.0
        }
    
    def analyze_equity_curve_stability(self, backtest_summary: BacktestSummary) -> HeuristicScore:
        """
        Analyze equity curve stability using trade-by-trade profit progression.
        
        Measures:
        - Drawdown periods and recovery
        - Volatility of returns
        - Consistency of profit generation
        """
        trades = backtest_summary.trades
        if not trades:
            return HeuristicScore(
                name="Equity Curve Stability",
                score=0.0,
                max_score=100.0,
                explanation="No trades available for analysis",
                details={}
            )
        
        # Calculate cumulative profit progression
        cumulative_profits = []
        running_total = 0.0
        for trade in sorted(trades, key=lambda t: t.exit_time):
            running_total += trade.profit_loss
            cumulative_profits.append(running_total)
        
        # Calculate metrics
        profits_array = np.array(cumulative_profits)
        
        # Drawdown analysis
        peak = np.maximum.accumulate(profits_array)
        drawdown = (peak - profits_array) / np.maximum(peak, 1.0)  # Avoid division by zero
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0
        avg_drawdown = np.mean(drawdown) if len(drawdown) > 0 else 0.0
        
        # Volatility analysis
        if len(profits_array) > 1:
            returns = np.diff(profits_array)
            volatility = np.std(returns) if len(returns) > 0 else 0.0
            mean_return = np.mean(returns) if len(returns) > 0 else 0.0
            sharpe_ratio = mean_return / volatility if volatility > 0 else 0.0
        else:
            volatility = 0.0
            sharpe_ratio = 0.0
        
        # Stability score calculation (0-100)
        drawdown_score = max(0, 100 - (max_drawdown * 200))  # Penalize high drawdowns
        volatility_score = max(0, 100 - (volatility / max(abs(backtest_summary.total_profit), 1) * 100))
        sharpe_score = min(100, max(0, sharpe_ratio * 20 + 50))  # Normalize Sharpe ratio
        
        overall_score = (drawdown_score + volatility_score + sharpe_score) / 3
        
        return HeuristicScore(
            name="Equity Curve Stability",
            score=overall_score,
            max_score=100.0,
            explanation=f"Stability based on drawdown ({max_drawdown:.2%}), volatility, and Sharpe ratio ({sharpe_ratio:.2f})",
            details={
                'max_drawdown': max_drawdown,
                'avg_drawdown': avg_drawdown,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'drawdown_score': drawdown_score,
                'volatility_score': volatility_score,
                'sharpe_score': sharpe_score
            }
        )
    
    def analyze_performance_metrics(self, backtest_summary: BacktestSummary) -> HeuristicScore:
        """
        Analyze core performance metrics.
        
        Measures:
        - ROI efficiency
        - Profit factor
        - Win rate
        - Average win vs average loss
        """
        trades = backtest_summary.trades
        if not trades:
            return HeuristicScore(
                name="Performance Metrics",
                score=0.0,
                max_score=100.0,
                explanation="No trades available for analysis",
                details={}
            )
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.profit_loss > 0])
        losing_trades = len([t for t in trades if t.profit_loss < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Profit factor calculation
        gross_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in trades if t.profit_loss < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average win/loss
        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0.0
        avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0.0
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        # ROI efficiency (ROI per trade)
        roi_per_trade = backtest_summary.roi / total_trades if total_trades > 0 else 0.0
        
        # Score calculation (0-100)
        roi_score = min(100, max(0, backtest_summary.roi / 10))  # Scale ROI to 0-100
        profit_factor_score = min(100, max(0, (profit_factor - 1) * 50))  # PF > 1 is good
        win_rate_score = win_rate * 100  # Direct percentage
        win_loss_score = min(100, max(0, win_loss_ratio * 25))  # Scale ratio
        
        overall_score = (roi_score + profit_factor_score + win_rate_score + win_loss_score) / 4
        
        return HeuristicScore(
            name="Performance Metrics",
            score=overall_score,
            max_score=100.0,
            explanation=f"Performance based on ROI ({backtest_summary.roi:.1f}%), win rate ({win_rate:.1%}), profit factor ({profit_factor:.2f})",
            details={
                'roi': backtest_summary.roi,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'win_loss_ratio': win_loss_ratio,
                'roi_per_trade': roi_per_trade,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'avg_win': avg_win,
                'avg_loss': avg_loss
            }
        )
    
    def analyze_trades_analysis(self, backtest_summary: BacktestSummary) -> HeuristicScore:
        """
        Analyze trade characteristics and patterns.
        
        Measures:
        - Trade frequency and timing
        - Position holding periods
        - Trade size consistency
        - Entry/exit efficiency
        """
        trades = backtest_summary.trades
        if not trades:
            return HeuristicScore(
                name="Trades Analysis",
                score=0.0,
                max_score=100.0,
                explanation="No trades available for analysis",
                details={}
            )
        
        # Holding period analysis
        holding_periods = []
        for trade in trades:
            if trade.exit_time > trade.entry_time:
                holding_period = (trade.exit_time - trade.entry_time) / 3600  # Hours
                holding_periods.append(holding_period)
        
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0.0
        holding_period_std = np.std(holding_periods) if len(holding_periods) > 1 else 0.0
        
        # Trade size analysis
        trade_amounts = [trade.trade_amount for trade in trades if trade.trade_amount > 0]
        avg_trade_amount = np.mean(trade_amounts) if trade_amounts else 0.0
        trade_amount_std = np.std(trade_amounts) if len(trade_amounts) > 1 else 0.0
        trade_size_consistency = 1 - (trade_amount_std / avg_trade_amount) if avg_trade_amount > 0 else 0.0
        
        # Entry/exit efficiency (price improvement)
        price_improvements = []
        for trade in trades:
            if trade.direction == 1:  # Long position
                improvement = (trade.exit_price - trade.entry_price) / trade.entry_price
            else:  # Short position
                improvement = (trade.entry_price - trade.exit_price) / trade.entry_price
            price_improvements.append(improvement)
        
        avg_price_improvement = np.mean(price_improvements) if price_improvements else 0.0
        
        # Trade frequency (trades per day)
        if trades:
            time_span = (max(t.exit_time for t in trades) - min(t.entry_time for t in trades)) / 86400  # Days
            trade_frequency = len(trades) / time_span if time_span > 0 else 0.0
        else:
            trade_frequency = 0.0
        
        # Score calculation
        frequency_score = min(100, trade_frequency * 10)  # Reasonable frequency
        consistency_score = trade_size_consistency * 100
        efficiency_score = min(100, max(0, (avg_price_improvement + 0.1) * 500))  # Scale improvement
        holding_score = min(100, max(0, 100 - (holding_period_std / max(avg_holding_period, 1) * 50)))
        
        overall_score = (frequency_score + consistency_score + efficiency_score + holding_score) / 4
        
        return HeuristicScore(
            name="Trades Analysis",
            score=overall_score,
            max_score=100.0,
            explanation=f"Trade analysis: {len(trades)} trades, avg holding {avg_holding_period:.1f}h, consistency {trade_size_consistency:.2f}",
            details={
                'total_trades': len(trades),
                'avg_holding_period': avg_holding_period,
                'holding_period_std': holding_period_std,
                'trade_size_consistency': trade_size_consistency,
                'avg_price_improvement': avg_price_improvement,
                'trade_frequency': trade_frequency,
                'avg_trade_amount': avg_trade_amount
            }
        )
    
    def analyze_risk_analysis(self, backtest_summary: BacktestSummary) -> HeuristicScore:
        """
        Analyze risk characteristics.
        
        Measures:
        - Maximum consecutive losses
        - Risk-adjusted returns
        - Downside deviation
        - Recovery factor
        """
        trades = backtest_summary.trades
        if not trades:
            return HeuristicScore(
                name="Risk Analysis",
                score=0.0,
                max_score=100.0,
                explanation="No trades available for analysis",
                details={}
            )
        
        # Sort trades by exit time
        sorted_trades = sorted(trades, key=lambda t: t.exit_time)
        
        # Consecutive losses analysis
        max_consecutive_losses = 0
        current_consecutive_losses = 0
        consecutive_loss_amounts = []
        current_loss_amount = 0.0
        
        for trade in sorted_trades:
            if trade.profit_loss < 0:
                current_consecutive_losses += 1
                current_loss_amount += abs(trade.profit_loss)
            else:
                if current_consecutive_losses > 0:
                    consecutive_loss_amounts.append(current_loss_amount)
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
                current_consecutive_losses = 0
                current_loss_amount = 0.0
        
        # Handle case where backtest ends with losses
        if current_consecutive_losses > 0:
            consecutive_loss_amounts.append(current_loss_amount)
            max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        max_consecutive_loss_amount = max(consecutive_loss_amounts) if consecutive_loss_amounts else 0.0
        
        # Downside deviation
        negative_returns = [trade.profit_loss for trade in trades if trade.profit_loss < 0]
        downside_deviation = np.std(negative_returns) if len(negative_returns) > 1 else 0.0
        
        # Recovery factor (total profit / max drawdown)
        cumulative_profits = []
        running_total = 0.0
        for trade in sorted_trades:
            running_total += trade.profit_loss
            cumulative_profits.append(running_total)
        
        if cumulative_profits:
            peak = np.maximum.accumulate(cumulative_profits)
            drawdown = peak - cumulative_profits
            max_drawdown_amount = np.max(drawdown) if len(drawdown) > 0 else 0.0
            recovery_factor = backtest_summary.total_profit / max_drawdown_amount if max_drawdown_amount > 0 else float('inf')
        else:
            recovery_factor = 0.0
        
        # Risk-adjusted return (Calmar ratio approximation)
        calmar_ratio = backtest_summary.roi / (max_drawdown_amount / 1000) if max_drawdown_amount > 0 else 0.0
        
        # Score calculation (lower risk = higher score)
        consecutive_loss_score = max(0, 100 - (max_consecutive_losses * 10))
        drawdown_score = max(0, 100 - (max_drawdown_amount / max(abs(backtest_summary.total_profit), 1) * 100))
        recovery_score = min(100, max(0, recovery_factor * 10))
        calmar_score = min(100, max(0, calmar_ratio * 5))
        
        overall_score = (consecutive_loss_score + drawdown_score + recovery_score + calmar_score) / 4
        
        return HeuristicScore(
            name="Risk Analysis",
            score=overall_score,
            max_score=100.0,
            explanation=f"Risk metrics: max consecutive losses {max_consecutive_losses}, recovery factor {recovery_factor:.2f}",
            details={
                'max_consecutive_losses': max_consecutive_losses,
                'max_consecutive_loss_amount': max_consecutive_loss_amount,
                'downside_deviation': downside_deviation,
                'recovery_factor': recovery_factor,
                'calmar_ratio': calmar_ratio,
                'max_drawdown_amount': max_drawdown_amount
            }
        )
    
    def analyze_trades_distribution(self, backtest_summary: BacktestSummary) -> HeuristicScore:
        """
        Analyze distribution of trades across time and profit ranges.
        
        Measures:
        - Temporal distribution of trades
        - Profit/loss distribution
        - Trade clustering analysis
        """
        trades = backtest_summary.trades
        if not trades:
            return HeuristicScore(
                name="Trades Distribution",
                score=0.0,
                max_score=100.0,
                explanation="No trades available for analysis",
                details={}
            )
        
        # Temporal distribution
        trade_times = [trade.exit_time for trade in trades]
        if len(trade_times) > 1:
            time_span = max(trade_times) - min(trade_times)
            time_intervals = np.diff(sorted(trade_times))
            avg_interval = np.mean(time_intervals) if len(time_intervals) > 0 else 0.0
            interval_std = np.std(time_intervals) if len(time_intervals) > 1 else 0.0
            temporal_consistency = 1 - (interval_std / avg_interval) if avg_interval > 0 else 0.0
        else:
            temporal_consistency = 1.0
        
        # Profit/loss distribution
        profits = [trade.profit_loss for trade in trades]
        profit_mean = np.mean(profits)
        profit_std = np.std(profits) if len(profits) > 1 else 0.0
        profit_skewness = self._calculate_skewness(profits)
        
        # Distribution of profit ranges
        profit_ranges = {
            'large_wins': len([p for p in profits if p > profit_mean + profit_std]),
            'small_wins': len([p for p in profits if 0 < p <= profit_mean + profit_std]),
            'small_losses': len([p for p in profits if profit_mean - profit_std <= p < 0]),
            'large_losses': len([p for p in profits if p < profit_mean - profit_std])
        }
        
        # Distribution balance (prefer more small wins than large losses)
        distribution_balance = (profit_ranges['small_wins'] + profit_ranges['large_wins']) / len(profits)
        
        # Score calculation
        temporal_score = temporal_consistency * 100
        distribution_score = distribution_balance * 100
        skewness_score = max(0, 100 - abs(profit_skewness) * 20)  # Prefer less skewed distributions
        
        overall_score = (temporal_score + distribution_score + skewness_score) / 3
        
        return HeuristicScore(
            name="Trades Distribution",
            score=overall_score,
            max_score=100.0,
            explanation=f"Distribution analysis: temporal consistency {temporal_consistency:.2f}, balance {distribution_balance:.2f}",
            details={
                'temporal_consistency': temporal_consistency,
                'profit_skewness': profit_skewness,
                'distribution_balance': distribution_balance,
                'profit_ranges': profit_ranges,
                'avg_interval': avg_interval if 'avg_interval' in locals() else 0.0
            }
        )
    
    def analyze_realized_vs_open(self, backtest_summary: BacktestSummary) -> HeuristicScore:
        """
        Analyze realized vs open profit characteristics.
        
        Measures:
        - Profit realization efficiency
        - Open position management
        - Exit timing quality
        """
        trades = backtest_summary.trades
        if not trades:
            return HeuristicScore(
                name="Realized vs Open Profit",
                score=0.0,
                max_score=100.0,
                explanation="No trades available for analysis",
                details={}
            )
        
        # Since we're analyzing completed backtests, all profits are realized
        # We can analyze the efficiency of profit realization by looking at
        # the relationship between entry/exit prices and final profits
        
        total_potential_profit = 0.0
        total_realized_profit = 0.0
        efficient_exits = 0
        
        for trade in trades:
            # Calculate potential profit based on price movement
            if trade.direction == 1:  # Long
                price_movement = (trade.exit_price - trade.entry_price) / trade.entry_price
            else:  # Short
                price_movement = (trade.entry_price - trade.exit_price) / trade.entry_price
            
            potential_profit = price_movement * trade.trade_amount
            total_potential_profit += potential_profit
            total_realized_profit += trade.profit_loss
            
            # Check if exit was efficient (realized profit close to potential)
            if potential_profit != 0:
                efficiency = trade.profit_loss / potential_profit
                if 0.8 <= efficiency <= 1.2:  # Within 20% of potential
                    efficient_exits += 1
        
        # Realization efficiency
        realization_efficiency = total_realized_profit / total_potential_profit if total_potential_profit != 0 else 0.0
        exit_efficiency = efficient_exits / len(trades) if trades else 0.0
        
        # Profit consistency (how consistent are the profit amounts)
        profit_amounts = [abs(trade.profit_loss) for trade in trades if trade.profit_loss != 0]
        profit_consistency = 1 - (np.std(profit_amounts) / np.mean(profit_amounts)) if len(profit_amounts) > 1 and np.mean(profit_amounts) > 0 else 0.0
        
        # Score calculation
        realization_score = min(100, max(0, realization_efficiency * 100 + 50))
        exit_score = exit_efficiency * 100
        consistency_score = max(0, profit_consistency * 100)
        
        overall_score = (realization_score + exit_score + consistency_score) / 3
        
        return HeuristicScore(
            name="Realized vs Open Profit",
            score=overall_score,
            max_score=100.0,
            explanation=f"Profit realization: efficiency {realization_efficiency:.2f}, exit quality {exit_efficiency:.2f}",
            details={
                'realization_efficiency': realization_efficiency,
                'exit_efficiency': exit_efficiency,
                'profit_consistency': profit_consistency,
                'total_potential_profit': total_potential_profit,
                'total_realized_profit': total_realized_profit,
                'efficient_exits': efficient_exits
            }
        )
    
    def _calculate_skewness(self, data: List[float]) -> float:
        """Calculate skewness of a dataset"""
        if len(data) < 3:
            return 0.0
        
        data_array = np.array(data)
        mean = np.mean(data_array)
        std = np.std(data_array)
        
        if std == 0:
            return 0.0
        
        skewness = np.mean(((data_array - mean) / std) ** 3)
        return skewness
    
    def analyze_configuration(self, backtest_summary: BacktestSummary) -> ConfigurationAnalysis:
        """
        Perform complete heuristic analysis of a backtest configuration.
        
        Args:
            backtest_summary: BacktestSummary object to analyze
            
        Returns:
            ConfigurationAnalysis with all heuristic scores and overall assessment
        """
        # Apply all heuristics
        heuristic_scores = [
            self.analyze_equity_curve_stability(backtest_summary),
            self.analyze_performance_metrics(backtest_summary),
            self.analyze_trades_analysis(backtest_summary),
            self.analyze_risk_analysis(backtest_summary),
            self.analyze_trades_distribution(backtest_summary),
            self.analyze_realized_vs_open(backtest_summary)
        ]
        
        # Calculate weighted overall score
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for score in heuristic_scores:
            weight_key = score.name.lower().replace(' ', '_').replace('vs', 'vs')
            weight = self.weights.get(weight_key, 1.0)
            total_weighted_score += score.score * weight
            total_weight += weight
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Calculate diversity factors
        diversity_factors = {
            'trade_count': len(backtest_summary.trades),
            'roi_level': backtest_summary.roi,
            'profit_variability': np.std([t.profit_loss for t in backtest_summary.trades]) if backtest_summary.trades else 0.0,
            'parameter_signature': hash(str(sorted(backtest_summary.parameters.items())))
        }
        
        # Generate recommendation
        if overall_score >= 80:
            recommendation = "Excellent configuration - highly recommended for further optimization"
        elif overall_score >= 60:
            recommendation = "Good configuration - suitable for parameter refinement"
        elif overall_score >= 40:
            recommendation = "Moderate configuration - requires significant improvements"
        else:
            recommendation = "Poor configuration - not recommended for further development"
        
        return ConfigurationAnalysis(
            backtest_id=backtest_summary.backtest_id,
            backtest_summary=backtest_summary,
            heuristic_scores=heuristic_scores,
            overall_score=overall_score,
            rank=0,  # Will be set during ranking
            diversity_factors=diversity_factors,
            recommendation=recommendation
        )
    
    def identify_top_configurations(
        self, 
        backtest_summaries: List[BacktestSummary],
        top_count: int = 5,
        diversity_threshold: float = 0.3
    ) -> List[ConfigurationAnalysis]:
        """
        Identify top-performing and diverse configurations using all heuristics.
        
        Args:
            backtest_summaries: List of BacktestSummary objects to analyze
            top_count: Number of top configurations to return
            diversity_threshold: Minimum diversity required between configurations
            
        Returns:
            List of top ConfigurationAnalysis objects, ranked and diverse
        """
        if not backtest_summaries:
            return []
        
        # Analyze all configurations
        logger.info(f"Analyzing {len(backtest_summaries)} configurations with advanced heuristics...")
        
        analyses = []
        for summary in backtest_summaries:
            analysis = self.analyze_configuration(summary)
            analyses.append(analysis)
        
        # Sort by overall score
        analyses.sort(key=lambda a: a.overall_score, reverse=True)
        
        # Set ranks
        for i, analysis in enumerate(analyses):
            analysis.rank = i + 1
        
        # Select diverse top configurations
        selected_configurations = []
        
        for analysis in analyses:
            if len(selected_configurations) >= top_count:
                break
            
            # Check diversity against already selected configurations
            is_diverse = True
            for selected in selected_configurations:
                diversity_score = self._calculate_diversity_score(analysis, selected)
                if diversity_score < diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse or len(selected_configurations) == 0:  # Always include the top one
                selected_configurations.append(analysis)
                logger.info(f"Selected configuration {analysis.backtest_id}: score={analysis.overall_score:.1f}, rank={analysis.rank}")
        
        return selected_configurations
    
    def _calculate_diversity_score(self, analysis1: ConfigurationAnalysis, analysis2: ConfigurationAnalysis) -> float:
        """
        Calculate diversity score between two configurations.
        Higher score means more diverse.
        """
        factors1 = analysis1.diversity_factors
        factors2 = analysis2.diversity_factors
        
        # Normalize and compare factors
        trade_count_diff = abs(factors1['trade_count'] - factors2['trade_count']) / max(factors1['trade_count'], factors2['trade_count'], 1)
        roi_diff = abs(factors1['roi_level'] - factors2['roi_level']) / max(abs(factors1['roi_level']), abs(factors2['roi_level']), 1)
        profit_var_diff = abs(factors1['profit_variability'] - factors2['profit_variability']) / max(factors1['profit_variability'], factors2['profit_variability'], 1)
        
        # Parameter signature difference (0 if same, 1 if different)
        param_diff = 1.0 if factors1['parameter_signature'] != factors2['parameter_signature'] else 0.0
        
        # Weighted diversity score
        diversity_score = (trade_count_diff * 0.3 + roi_diff * 0.3 + profit_var_diff * 0.2 + param_diff * 0.2)
        
        return diversity_score

def main():
    """Test the heuristics analyzer"""
    from data_extractor import BacktestDataExtractor
    
    # Configuration
    LAB_ID = '55b45ee4-9cc5-42f7-8556-4c3aa2b13a44'
    RESULTS_DIR = f'/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/experiments/bt_analysis/raw_results/lab_{LAB_ID}'
    
    # Extract backtest data
    extractor = BacktestDataExtractor(RESULTS_DIR)
    backtest_summaries = extractor.process_all_backtests()
    
    if not backtest_summaries:
        print("No backtest data available for analysis")
        return
    
    # Initialize analyzer
    analyzer = HeuristicsAnalyzer()
    
    # Identify top configurations
    top_configurations = analyzer.identify_top_configurations(
        backtest_summaries, 
        top_count=5, 
        diversity_threshold=0.3
    )
    
    print(f"\n=== TOP {len(top_configurations)} CONFIGURATIONS ===")
    
    for i, config in enumerate(top_configurations):
        print(f"\n--- Configuration {i+1} ---")
        print(f"Backtest ID: {config.backtest_id}")
        print(f"Overall Score: {config.overall_score:.1f}/100")
        print(f"Rank: {config.rank}")
        print(f"ROI: {config.backtest_summary.roi:.1f}%")
        print(f"Total Trades: {len(config.backtest_summary.trades)}")
        print(f"Win Rate: {config.backtest_summary.winning_trades/len(config.backtest_summary.trades)*100:.1f}%")
        print(f"Recommendation: {config.recommendation}")
        
        print("\nHeuristic Scores:")
        for score in config.heuristic_scores:
            print(f"  {score.name}: {score.score:.1f}/100 - {score.explanation}")
        
        print(f"\nKey Parameters:")
        for key, value in list(config.backtest_summary.parameters.items())[:5]:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main()