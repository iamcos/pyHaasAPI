"""
Results comparison engine for multiple backtest analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from scipy import stats

from ..models import ProcessedResults, ExecutionMetrics, Trade


logger = logging.getLogger(__name__)


class ResultsComparisonEngine:
    """
    Engine for comparing multiple backtest results.
    
    Provides comprehensive comparison analysis including:
    - Statistical significance testing
    - Performance ranking and scoring
    - Risk-adjusted comparisons
    - Correlation analysis
    - Consistency metrics
    """
    
    def __init__(self):
        """Initialize comparison engine."""
        self.logger = logging.getLogger(__name__)
    
    def compare_multiple_results(self, results_list: List[ProcessedResults]) -> Dict[str, Any]:
        """
        Compare multiple backtest results comprehensively.
        
        Args:
            results_list: List of ProcessedResults to compare
            
        Returns:
            Comprehensive comparison report
        """
        if len(results_list) < 2:
            raise ValueError("At least 2 results are required for comparison")
        
        self.logger.info(f"Comparing {len(results_list)} backtest results")
        
        # Basic comparison metrics
        basic_comparison = self._create_basic_comparison(results_list)
        
        # Statistical analysis
        statistical_analysis = self._perform_statistical_analysis(results_list)
        
        # Risk-adjusted rankings
        risk_rankings = self._calculate_risk_adjusted_rankings(results_list)
        
        # Consistency analysis
        consistency_analysis = self._analyze_consistency(results_list)
        
        # Correlation analysis
        correlation_analysis = self._calculate_correlations(results_list)
        
        # Performance attribution comparison
        attribution_comparison = self._compare_performance_attribution(results_list)
        
        return {
            'summary': {
                'total_results': len(results_list),
                'comparison_date': datetime.now().isoformat(),
                'analysis_type': 'comprehensive_comparison'
            },
            'basic_comparison': basic_comparison,
            'statistical_analysis': statistical_analysis,
            'risk_adjusted_rankings': risk_rankings,
            'consistency_analysis': consistency_analysis,
            'correlation_analysis': correlation_analysis,
            'attribution_comparison': attribution_comparison,
            'recommendations': self._generate_recommendations(results_list, risk_rankings)
        }
    
    def compare_two_results(self, result1: ProcessedResults, result2: ProcessedResults) -> Dict[str, Any]:
        """
        Detailed comparison between two specific results.
        
        Args:
            result1: First result to compare
            result2: Second result to compare
            
        Returns:
            Detailed pairwise comparison
        """
        self.logger.info(f"Comparing results {result1.backtest_id} vs {result2.backtest_id}")
        
        # Performance comparison
        performance_diff = self._calculate_performance_differences(result1, result2)
        
        # Statistical significance test
        significance_test = self._test_statistical_significance(result1, result2)
        
        # Risk comparison
        risk_comparison = self._compare_risk_profiles(result1, result2)
        
        # Trade analysis comparison
        trade_comparison = self._compare_trade_patterns(result1, result2)
        
        return {
            'comparison_pair': {
                'result1_id': result1.backtest_id,
                'result2_id': result2.backtest_id,
                'comparison_date': datetime.now().isoformat()
            },
            'performance_differences': performance_diff,
            'statistical_significance': significance_test,
            'risk_comparison': risk_comparison,
            'trade_pattern_comparison': trade_comparison,
            'winner': self._determine_winner(result1, result2)
        }
    
    def rank_results_by_criteria(
        self, 
        results_list: List[ProcessedResults], 
        criteria: List[str],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Rank results by multiple criteria with optional weighting.
        
        Args:
            results_list: List of results to rank
            criteria: List of criteria to rank by
            weights: Optional weights for each criterion
            
        Returns:
            Ranking analysis with scores
        """
        if not results_list:
            return {}
        
        # Default weights if not provided
        if weights is None:
            weights = {criterion: 1.0 for criterion in criteria}
        
        # Calculate scores for each criterion
        criterion_scores = {}
        for criterion in criteria:
            criterion_scores[criterion] = self._calculate_criterion_scores(results_list, criterion)
        
        # Calculate composite scores
        composite_scores = self._calculate_composite_scores(results_list, criterion_scores, weights)
        
        # Create rankings
        rankings = self._create_rankings(results_list, composite_scores)
        
        return {
            'criteria': criteria,
            'weights': weights,
            'criterion_scores': criterion_scores,
            'composite_scores': composite_scores,
            'rankings': rankings,
            'analysis_date': datetime.now().isoformat()
        }
    
    def _create_basic_comparison(self, results_list: List[ProcessedResults]) -> Dict[str, Any]:
        """Create basic comparison metrics."""
        metrics_comparison = {}
        
        # Key metrics to compare
        key_metrics = [
            'total_return', 'sharpe_ratio', 'max_drawdown', 'profit_factor',
            'volatility', 'calmar_ratio', 'sortino_ratio'
        ]
        
        for metric in key_metrics:
            values = [getattr(result.execution_metrics, metric) for result in results_list]
            
            metrics_comparison[metric] = {
                'values': values,
                'best': max(values) if metric != 'max_drawdown' else min(values),
                'worst': min(values) if metric != 'max_drawdown' else max(values),
                'mean': np.mean(values),
                'median': np.median(values),
                'std_dev': np.std(values, ddof=1) if len(values) > 1 else 0.0,
                'range': max(values) - min(values),
                'coefficient_of_variation': np.std(values, ddof=1) / np.mean(values) if np.mean(values) != 0 else 0.0
            }
        
        # Best performers by metric
        best_performers = {}
        for metric in key_metrics:
            values_with_ids = [(getattr(result.execution_metrics, metric), result.backtest_id) 
                              for result in results_list]
            
            if metric == 'max_drawdown':
                best_value, best_id = min(values_with_ids, key=lambda x: x[0])
            else:
                best_value, best_id = max(values_with_ids, key=lambda x: x[0])
            
            best_performers[metric] = {
                'backtest_id': best_id,
                'value': best_value
            }
        
        return {
            'metrics_comparison': metrics_comparison,
            'best_performers': best_performers,
            'total_results': len(results_list)
        }
    
    def _perform_statistical_analysis(self, results_list: List[ProcessedResults]) -> Dict[str, Any]:
        """Perform statistical analysis on results."""
        # Extract returns for each result
        all_returns = []
        for result in results_list:
            returns = self._extract_returns_from_trades(result.trade_history, result.performance_data.initial_balance)
            all_returns.append(returns)
        
        # Statistical tests
        statistical_tests = {}
        
        # Normality tests
        normality_tests = {}
        for i, returns in enumerate(all_returns):
            if len(returns) >= 8:  # Minimum sample size for Shapiro-Wilk
                try:
                    stat, p_value = stats.shapiro(returns)
                    normality_tests[results_list[i].backtest_id] = {
                        'test': 'shapiro_wilk',
                        'statistic': stat,
                        'p_value': p_value,
                        'is_normal': p_value > 0.05
                    }
                except Exception as e:
                    self.logger.warning(f"Normality test failed for {results_list[i].backtest_id}: {e}")
        
        # Pairwise t-tests for returns comparison
        pairwise_tests = {}
        for i in range(len(results_list)):
            for j in range(i + 1, len(results_list)):
                if len(all_returns[i]) > 1 and len(all_returns[j]) > 1:
                    try:
                        stat, p_value = stats.ttest_ind(all_returns[i], all_returns[j])
                        pair_key = f"{results_list[i].backtest_id}_vs_{results_list[j].backtest_id}"
                        pairwise_tests[pair_key] = {
                            'test': 'independent_t_test',
                            'statistic': stat,
                            'p_value': p_value,
                            'significant_difference': p_value < 0.05
                        }
                    except Exception as e:
                        self.logger.warning(f"T-test failed for pair {i}-{j}: {e}")
        
        # ANOVA test if more than 2 results
        anova_test = {}
        if len(all_returns) > 2 and all(len(returns) > 1 for returns in all_returns):
            try:
                stat, p_value = stats.f_oneway(*all_returns)
                anova_test = {
                    'test': 'one_way_anova',
                    'statistic': stat,
                    'p_value': p_value,
                    'significant_difference': p_value < 0.05
                }
            except Exception as e:
                self.logger.warning(f"ANOVA test failed: {e}")
        
        return {
            'normality_tests': normality_tests,
            'pairwise_tests': pairwise_tests,
            'anova_test': anova_test,
            'sample_sizes': [len(returns) for returns in all_returns]
        }
    
    def _calculate_risk_adjusted_rankings(self, results_list: List[ProcessedResults]) -> Dict[str, Any]:
        """Calculate risk-adjusted performance rankings."""
        # Multiple risk-adjusted metrics
        risk_metrics = ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']
        
        rankings = {}
        for metric in risk_metrics:
            values_with_ids = [(getattr(result.execution_metrics, metric), result.backtest_id) 
                              for result in results_list]
            
            # Sort by metric (descending)
            sorted_results = sorted(values_with_ids, key=lambda x: x[0], reverse=True)
            
            rankings[metric] = [
                {
                    'rank': i + 1,
                    'backtest_id': backtest_id,
                    'value': value,
                    'percentile': ((len(sorted_results) - i) / len(sorted_results)) * 100
                }
                for i, (value, backtest_id) in enumerate(sorted_results)
            ]
        
        # Composite risk score
        composite_scores = self._calculate_composite_risk_scores(results_list)
        
        return {
            'individual_rankings': rankings,
            'composite_risk_scores': composite_scores,
            'methodology': 'Higher scores indicate better risk-adjusted performance'
        }
    
    def _analyze_consistency(self, results_list: List[ProcessedResults]) -> Dict[str, Any]:
        """Analyze consistency of trading performance."""
        consistency_metrics = {}
        
        for result in results_list:
            if not result.trade_history:
                continue
            
            # Extract trade returns
            trade_returns = [trade.profit_loss / result.performance_data.initial_balance 
                           for trade in result.trade_history if trade.profit_loss is not None]
            
            if not trade_returns:
                continue
            
            # Consistency metrics
            consistency_metrics[result.backtest_id] = {
                'return_consistency': {
                    'std_deviation': np.std(trade_returns, ddof=1) if len(trade_returns) > 1 else 0.0,
                    'coefficient_of_variation': np.std(trade_returns, ddof=1) / np.mean(trade_returns) if np.mean(trade_returns) != 0 else float('inf'),
                    'positive_trade_ratio': len([r for r in trade_returns if r > 0]) / len(trade_returns)
                },
                'streak_analysis': {
                    'max_winning_streak': self._calculate_max_streak(trade_returns, True),
                    'max_losing_streak': self._calculate_max_streak(trade_returns, False),
                    'avg_streak_length': self._calculate_avg_streak_length(trade_returns)
                },
                'drawdown_consistency': {
                    'max_drawdown': result.execution_metrics.max_drawdown,
                    'drawdown_frequency': self._calculate_drawdown_frequency(result.trade_history, result.performance_data.initial_balance)
                }
            }
        
        # Rank by consistency
        consistency_ranking = self._rank_by_consistency(consistency_metrics)
        
        return {
            'individual_consistency': consistency_metrics,
            'consistency_ranking': consistency_ranking,
            'methodology': 'Lower variability and more consistent returns indicate better consistency'
        }
    
    def _calculate_correlations(self, results_list: List[ProcessedResults]) -> Dict[str, Any]:
        """Calculate correlations between different results."""
        if len(results_list) < 2:
            return {}
        
        # Extract returns series for each result
        returns_series = {}
        for result in results_list:
            returns = self._extract_returns_from_trades(result.trade_history, result.performance_data.initial_balance)
            if returns:
                returns_series[result.backtest_id] = returns
        
        # Calculate pairwise correlations
        correlations = {}
        result_ids = list(returns_series.keys())
        
        for i in range(len(result_ids)):
            for j in range(i + 1, len(result_ids)):
                id1, id2 = result_ids[i], result_ids[j]
                returns1, returns2 = returns_series[id1], returns_series[id2]
                
                # Align series lengths (take minimum)
                min_length = min(len(returns1), len(returns2))
                if min_length > 1:
                    try:
                        correlation = np.corrcoef(returns1[:min_length], returns2[:min_length])[0, 1]
                        correlations[f"{id1}_vs_{id2}"] = {
                            'correlation': correlation,
                            'sample_size': min_length,
                            'strength': self._interpret_correlation_strength(correlation)
                        }
                    except Exception as e:
                        self.logger.warning(f"Correlation calculation failed for {id1} vs {id2}: {e}")
        
        # Average correlation
        avg_correlation = np.mean([corr['correlation'] for corr in correlations.values()]) if correlations else 0.0
        
        return {
            'pairwise_correlations': correlations,
            'average_correlation': avg_correlation,
            'interpretation': self._interpret_correlation_strength(avg_correlation)
        }
    
    def _compare_performance_attribution(self, results_list: List[ProcessedResults]) -> Dict[str, Any]:
        """Compare performance attribution across results."""
        from .metrics_calculator import TradingMetricsCalculator
        
        calculator = TradingMetricsCalculator()
        attributions = {}
        
        # Calculate attribution for each result
        for result in results_list:
            if result.trade_history:
                attribution = calculator.calculate_performance_attribution(result.trade_history)
                attributions[result.backtest_id] = attribution
        
        # Compare time-based performance
        time_comparison = self._compare_time_attributions(attributions)
        
        # Compare size-based performance
        size_comparison = self._compare_size_attributions(attributions)
        
        return {
            'individual_attributions': attributions,
            'time_comparison': time_comparison,
            'size_comparison': size_comparison,
            'summary': f"Attribution analysis for {len(attributions)} results"
        }
    
    def _generate_recommendations(self, results_list: List[ProcessedResults], risk_rankings: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison analysis."""
        recommendations = []
        
        # Find best overall performer
        if 'composite_risk_scores' in risk_rankings:
            best_performer = max(risk_rankings['composite_risk_scores'], 
                               key=lambda x: x['composite_score'])
            recommendations.append(f"Best overall risk-adjusted performer: {best_performer['backtest_id']} "
                                 f"(composite score: {best_performer['composite_score']:.3f})")
        
        # Check for high correlation
        correlations = self._calculate_correlations(results_list)
        if correlations.get('average_correlation', 0) > 0.7:
            recommendations.append("High correlation detected between strategies - consider diversification")
        
        # Check for consistency
        consistency = self._analyze_consistency(results_list)
        if consistency.get('consistency_ranking'):
            most_consistent = consistency['consistency_ranking'][0]
            recommendations.append(f"Most consistent performer: {most_consistent['backtest_id']}")
        
        # Risk warnings
        high_risk_results = [result for result in results_list 
                           if result.execution_metrics.max_drawdown > 20]
        if high_risk_results:
            recommendations.append(f"Warning: {len(high_risk_results)} strategies have drawdown > 20%")
        
        return recommendations
    
    def _extract_returns_from_trades(self, trades: List[Trade], initial_balance: float) -> List[float]:
        """Extract returns series from trade history."""
        returns = []
        current_balance = initial_balance
        
        for trade in trades:
            if trade.profit_loss is not None:
                trade_return = trade.profit_loss / current_balance
                returns.append(trade_return)
                current_balance += trade.profit_loss
        
        return returns
    
    def _calculate_performance_differences(self, result1: ProcessedResults, result2: ProcessedResults) -> Dict[str, float]:
        """Calculate performance differences between two results."""
        metrics1 = result1.execution_metrics
        metrics2 = result2.execution_metrics
        
        return {
            'total_return_diff': metrics1.total_return - metrics2.total_return,
            'sharpe_ratio_diff': metrics1.sharpe_ratio - metrics2.sharpe_ratio,
            'max_drawdown_diff': metrics1.max_drawdown - metrics2.max_drawdown,
            'volatility_diff': metrics1.volatility - metrics2.volatility,
            'profit_factor_diff': metrics1.profit_factor - metrics2.profit_factor
        }
    
    def _test_statistical_significance(self, result1: ProcessedResults, result2: ProcessedResults) -> Dict[str, Any]:
        """Test statistical significance between two results."""
        returns1 = self._extract_returns_from_trades(result1.trade_history, result1.performance_data.initial_balance)
        returns2 = self._extract_returns_from_trades(result2.trade_history, result2.performance_data.initial_balance)
        
        if len(returns1) < 2 or len(returns2) < 2:
            return {'error': 'Insufficient data for statistical testing'}
        
        try:
            # T-test
            t_stat, t_p_value = stats.ttest_ind(returns1, returns2)
            
            # Mann-Whitney U test (non-parametric)
            u_stat, u_p_value = stats.mannwhitneyu(returns1, returns2, alternative='two-sided')
            
            return {
                't_test': {
                    'statistic': t_stat,
                    'p_value': t_p_value,
                    'significant': t_p_value < 0.05
                },
                'mann_whitney_test': {
                    'statistic': u_stat,
                    'p_value': u_p_value,
                    'significant': u_p_value < 0.05
                },
                'sample_sizes': [len(returns1), len(returns2)]
            }
        except Exception as e:
            return {'error': f'Statistical testing failed: {e}'}
    
    def _compare_risk_profiles(self, result1: ProcessedResults, result2: ProcessedResults) -> Dict[str, Any]:
        """Compare risk profiles of two results."""
        metrics1 = result1.execution_metrics
        metrics2 = result2.execution_metrics
        
        return {
            'volatility_comparison': {
                'result1': metrics1.volatility,
                'result2': metrics2.volatility,
                'lower_risk': result1.backtest_id if metrics1.volatility < metrics2.volatility else result2.backtest_id
            },
            'drawdown_comparison': {
                'result1': metrics1.max_drawdown,
                'result2': metrics2.max_drawdown,
                'lower_drawdown': result1.backtest_id if metrics1.max_drawdown < metrics2.max_drawdown else result2.backtest_id
            },
            'var_comparison': {
                'result1': metrics1.value_at_risk_95,
                'result2': metrics2.value_at_risk_95,
                'lower_var': result1.backtest_id if metrics1.value_at_risk_95 > metrics2.value_at_risk_95 else result2.backtest_id
            }
        }
    
    def _compare_trade_patterns(self, result1: ProcessedResults, result2: ProcessedResults) -> Dict[str, Any]:
        """Compare trading patterns between two results."""
        return {
            'trade_count_comparison': {
                'result1': len(result1.trade_history),
                'result2': len(result2.trade_history),
                'difference': len(result1.trade_history) - len(result2.trade_history)
            },
            'win_rate_comparison': {
                'result1': result1.performance_data.win_rate,
                'result2': result2.performance_data.win_rate,
                'difference': result1.performance_data.win_rate - result2.performance_data.win_rate
            },
            'average_trade_size': {
                'result1': np.mean([t.amount for t in result1.trade_history]) if result1.trade_history else 0,
                'result2': np.mean([t.amount for t in result2.trade_history]) if result2.trade_history else 0
            }
        }
    
    def _determine_winner(self, result1: ProcessedResults, result2: ProcessedResults) -> Dict[str, Any]:
        """Determine overall winner between two results."""
        score1 = 0
        score2 = 0
        
        # Compare key metrics
        if result1.execution_metrics.total_return > result2.execution_metrics.total_return:
            score1 += 1
        else:
            score2 += 1
        
        if result1.execution_metrics.sharpe_ratio > result2.execution_metrics.sharpe_ratio:
            score1 += 1
        else:
            score2 += 1
        
        if result1.execution_metrics.max_drawdown < result2.execution_metrics.max_drawdown:
            score1 += 1
        else:
            score2 += 1
        
        winner_id = result1.backtest_id if score1 > score2 else result2.backtest_id
        
        return {
            'winner': winner_id,
            'score1': score1,
            'score2': score2,
            'margin': abs(score1 - score2),
            'criteria_used': ['total_return', 'sharpe_ratio', 'max_drawdown']
        }
    
    def _calculate_criterion_scores(self, results_list: List[ProcessedResults], criterion: str) -> Dict[str, float]:
        """Calculate normalized scores for a specific criterion."""
        values = []
        for result in results_list:
            if hasattr(result.execution_metrics, criterion):
                values.append(getattr(result.execution_metrics, criterion))
            else:
                values.append(0.0)
        
        # Normalize scores (0-1 scale)
        if criterion == 'max_drawdown':
            # For drawdown, lower is better
            max_val = max(values) if values else 1.0
            normalized = [(max_val - val) / max_val if max_val != 0 else 0.0 for val in values]
        else:
            # For other metrics, higher is better
            min_val = min(values) if values else 0.0
            max_val = max(values) if values else 1.0
            range_val = max_val - min_val
            normalized = [(val - min_val) / range_val if range_val != 0 else 0.0 for val in values]
        
        return {result.backtest_id: score for result, score in zip(results_list, normalized)}
    
    def _calculate_composite_scores(
        self, 
        results_list: List[ProcessedResults], 
        criterion_scores: Dict[str, Dict[str, float]], 
        weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Calculate composite scores using weighted criteria."""
        composite_scores = []
        
        for result in results_list:
            total_score = 0.0
            total_weight = 0.0
            
            for criterion, weight in weights.items():
                if criterion in criterion_scores and result.backtest_id in criterion_scores[criterion]:
                    total_score += criterion_scores[criterion][result.backtest_id] * weight
                    total_weight += weight
            
            final_score = total_score / total_weight if total_weight > 0 else 0.0
            
            composite_scores.append({
                'backtest_id': result.backtest_id,
                'composite_score': final_score,
                'weighted_components': {
                    criterion: criterion_scores[criterion].get(result.backtest_id, 0.0) * weight
                    for criterion, weight in weights.items()
                    if criterion in criterion_scores
                }
            })
        
        return sorted(composite_scores, key=lambda x: x['composite_score'], reverse=True)
    
    def _create_rankings(self, results_list: List[ProcessedResults], composite_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create final rankings with additional metadata."""
        rankings = []
        
        for i, score_data in enumerate(composite_scores):
            # Find the corresponding result
            result = next(r for r in results_list if r.backtest_id == score_data['backtest_id'])
            
            rankings.append({
                'rank': i + 1,
                'backtest_id': score_data['backtest_id'],
                'composite_score': score_data['composite_score'],
                'percentile': ((len(composite_scores) - i) / len(composite_scores)) * 100,
                'key_metrics': {
                    'total_return': result.execution_metrics.total_return,
                    'sharpe_ratio': result.execution_metrics.sharpe_ratio,
                    'max_drawdown': result.execution_metrics.max_drawdown
                }
            })
        
        return rankings
    
    def _calculate_composite_risk_scores(self, results_list: List[ProcessedResults]) -> List[Dict[str, Any]]:
        """Calculate composite risk-adjusted scores."""
        scores = []
        
        for result in results_list:
            # Weighted combination of risk-adjusted metrics
            sharpe_weight = 0.4
            sortino_weight = 0.3
            calmar_weight = 0.3
            
            composite_score = (
                result.execution_metrics.sharpe_ratio * sharpe_weight +
                result.execution_metrics.sortino_ratio * sortino_weight +
                result.execution_metrics.calmar_ratio * calmar_weight
            )
            
            scores.append({
                'backtest_id': result.backtest_id,
                'composite_score': composite_score,
                'components': {
                    'sharpe_ratio': result.execution_metrics.sharpe_ratio,
                    'sortino_ratio': result.execution_metrics.sortino_ratio,
                    'calmar_ratio': result.execution_metrics.calmar_ratio
                }
            })
        
        return sorted(scores, key=lambda x: x['composite_score'], reverse=True)
    
    def _calculate_max_streak(self, returns: List[float], winning: bool) -> int:
        """Calculate maximum winning or losing streak."""
        max_streak = 0
        current_streak = 0
        
        for return_val in returns:
            is_winning = return_val > 0
            if is_winning == winning:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_avg_streak_length(self, returns: List[float]) -> float:
        """Calculate average streak length."""
        if not returns:
            return 0.0
        
        streaks = []
        current_streak = 1
        
        for i in range(1, len(returns)):
            if (returns[i] > 0) == (returns[i-1] > 0):
                current_streak += 1
            else:
                streaks.append(current_streak)
                current_streak = 1
        
        streaks.append(current_streak)
        
        return np.mean(streaks) if streaks else 0.0
    
    def _calculate_drawdown_frequency(self, trades: List[Trade], initial_balance: float) -> float:
        """Calculate frequency of drawdown periods."""
        if not trades:
            return 0.0
        
        # Build equity curve
        equity_curve = [initial_balance]
        current_balance = initial_balance
        
        for trade in trades:
            if trade.profit_loss is not None:
                current_balance += trade.profit_loss
                equity_curve.append(current_balance)
        
        # Count drawdown periods
        peak = equity_curve[0]
        drawdown_periods = 0
        in_drawdown = False
        
        for balance in equity_curve[1:]:
            if balance > peak:
                peak = balance
                in_drawdown = False
            elif not in_drawdown:
                drawdown_periods += 1
                in_drawdown = True
        
        return drawdown_periods / len(trades) if trades else 0.0
    
    def _rank_by_consistency(self, consistency_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank results by consistency metrics."""
        rankings = []
        
        for backtest_id, metrics in consistency_metrics.items():
            # Calculate consistency score (lower is better for most metrics)
            cv = metrics['return_consistency']['coefficient_of_variation']
            positive_ratio = metrics['return_consistency']['positive_trade_ratio']
            max_losing_streak = metrics['streak_analysis']['max_losing_streak']
            
            # Composite consistency score (higher is better)
            consistency_score = positive_ratio / (1 + cv + max_losing_streak * 0.1)
            
            rankings.append({
                'backtest_id': backtest_id,
                'consistency_score': consistency_score,
                'components': metrics
            })
        
        return sorted(rankings, key=lambda x: x['consistency_score'], reverse=True)
    
    def _interpret_correlation_strength(self, correlation: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.8:
            return "Very Strong"
        elif abs_corr >= 0.6:
            return "Strong"
        elif abs_corr >= 0.4:
            return "Moderate"
        elif abs_corr >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    def _compare_time_attributions(self, attributions: Dict[str, Any]) -> Dict[str, Any]:
        """Compare time-based performance attributions."""
        # Extract best/worst hours for each result
        best_hours = {}
        worst_hours = {}
        
        for backtest_id, attribution in attributions.items():
            time_attr = attribution.get('time_attribution', {})
            best_hours[backtest_id] = time_attr.get('best_hour')
            worst_hours[backtest_id] = time_attr.get('worst_hour')
        
        return {
            'best_hours': best_hours,
            'worst_hours': worst_hours,
            'common_patterns': self._find_common_time_patterns(attributions)
        }
    
    def _compare_size_attributions(self, attributions: Dict[str, Any]) -> Dict[str, Any]:
        """Compare size-based performance attributions."""
        size_preferences = {}
        
        for backtest_id, attribution in attributions.items():
            size_attr = attribution.get('size_attribution', {})
            size_buckets = size_attr.get('size_buckets', {})
            
            # Find best performing size bucket
            best_bucket = None
            best_pnl = float('-inf')
            
            for bucket, stats in size_buckets.items():
                if stats['total_pnl'] > best_pnl:
                    best_pnl = stats['total_pnl']
                    best_bucket = bucket
            
            size_preferences[backtest_id] = best_bucket
        
        return {
            'size_preferences': size_preferences,
            'common_preferences': self._find_common_size_preferences(size_preferences)
        }
    
    def _find_common_time_patterns(self, attributions: Dict[str, Any]) -> Dict[str, Any]:
        """Find common time-based patterns across results."""
        # This is a simplified implementation
        return {'analysis': 'Time pattern analysis would be implemented here'}
    
    def _find_common_size_preferences(self, size_preferences: Dict[str, str]) -> Dict[str, Any]:
        """Find common size preferences across results."""
        from collections import Counter
        
        preference_counts = Counter(size_preferences.values())
        most_common = preference_counts.most_common(1)
        
        return {
            'most_common_preference': most_common[0] if most_common else None,
            'preference_distribution': dict(preference_counts)
        }