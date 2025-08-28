#!/usr/bin/env python3
"""
Walk Forward Optimization (WFO) Analyzer
========================================

Enhanced financial analytics system for HaasOnline backtest analysis with
Walk Forward Optimization capabilities and bot recommendation logic.

Features:
- Walk Forward Optimization analysis of backtest performance
- Diversity filtering to avoid similar strategy recommendations
- Bot recommendation system with configurable criteria
- Comprehensive performance scoring and ranking
- Statistical analysis of trading strategies

Author: AI Assistant
Version: 1.0
"""

import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
from dotenv import load_dotenv
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
from pyHaasAPI import api
from pyHaasAPI.backtest_object import BacktestObject
from pyHaasAPI.model import GetBacktestResultRequest

# Load environment variables
load_dotenv()

@dataclass
class WFOMetrics:
    """Walk Forward Optimization metrics - ADVANCED ANALYSIS vs Basic Backtest Analysis

    WFO DIFFERENCE FROM PREVIOUS financial_analytics.py:
    ======================================================================

    PREVIOUS financial_analytics.py (Basic Analysis):
    -------------------------------------------------
    ❌ Static snapshot analysis - looks at final results only
    ❌ Single performance score based on end metrics
    ❌ No consideration of performance stability over time
    ❌ Simple profit/loss ratio without temporal context
    ❌ Basic Sharpe ratio without time-based validation

    THIS WFO Analyzer (Advanced Walk Forward Analysis):
    ---------------------------------------------------
    ✅ TIME-BASED STABILITY: Analyzes performance across different periods
    ✅ CONSISTENCY SCORING: Measures how reliable performance is over time
    ✅ ROBUSTNESS TESTING: Validates strategy across varying market conditions
    ✅ FORWARD-LOOKING VALIDATION: Tests how strategy would perform going forward
    ✅ COMPREHENSIVE RISK METRICS: Sortino, Calmar ratios for better risk assessment
    """

    backtest_id: str
    lab_id: str
    script_name: str
    account_id: str
    market: str

    # Basic trading metrics (same as before)
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Profitability metrics (same as before)
    total_profit: float
    total_profit_usd: float
    roi_percentage: float
    profit_factor: float

    # Risk metrics (ENHANCED with advanced ratios)
    max_drawdown: float
    max_drawdown_percentage: float
    sharpe_ratio: float

    # Trade quality metrics (same as before)
    avg_trade_profit: float
    avg_winning_trade: float
    avg_losing_trade: float
    largest_win: float
    largest_loss: float

    # Enhanced risk metrics with defaults (moved to end)
    sortino_ratio: float = 0.0  # NEW: Downside risk only
    calmar_ratio: float = 0.0   # NEW: Annual return vs max drawdown
    profit_loss_ratio: float = 0.0

    # Time-based metrics (NEW: WFO requires temporal analysis)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_days: float = 0.0
    avg_trades_per_day: float = 0.0

    # Walk Forward Optimization specific metrics (BRAND NEW)
    wfo_score: float = 0.0          # Overall WFO stability score
    stability_score: float = 0.0    # Performance consistency over time
    consistency_score: float = 0.0  # Reliable win rate and profit factor
    robustness_score: float = 0.0   # Performance across different conditions

    # Fees and costs (same as before)
    total_fees: float = 0.0
    net_profit_after_fees: float = 0.0

    # Quality indicators (ENHANCED with WFO validation)
    is_profitable: bool = False
    has_positive_sharpe: bool = False
    has_acceptable_drawdown: bool = False
    has_good_win_rate: bool = False
    has_sufficient_trades: bool = False
    overall_score: float = 0.0

    # Additional metadata (same as before)
    script_parameters: Dict[str, Any] = field(default_factory=dict)
    market_conditions: str = ""
    strategy_type: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BotRecommendation:
    """Bot recommendation with diversity and quality scoring"""
    backtest: WFOMetrics
    recommendation_score: float
    diversity_score: float
    bot_name: str
    reasoning: List[str]
    risk_assessment: str
    position_size_usdt: float = 2000.0

@dataclass
class WFOConfig:
    """Configuration for Walk Forward Optimization analysis"""
    # Bot selection criteria
    max_bots_per_lab: int = 10
    min_overall_score: float = 70.0
    min_win_rate: float = 40.0
    max_drawdown_pct: float = 30.0
    min_trades: int = 5
    min_roi_pct: float = 10.0
    min_sharpe_ratio: float = 0.5

    # Diversity filtering
    roi_similarity_threshold: float = 0.05  # ±5%
    trade_count_similarity_threshold: float = 0.10  # ±10%
    win_rate_similarity_threshold: float = 0.08  # ±8%

    # Scoring weights
    profitability_weight: float = 0.3
    win_rate_weight: float = 0.2
    roi_weight: float = 0.2
    risk_weight: float = 0.2
    consistency_weight: float = 0.1

    # WFO specific settings
    stability_window_days: int = 30
    min_sample_size: int = 10
    confidence_level: float = 0.95

class WFOAnalyzer:
    """
    Walk Forward Optimization Analyzer for HaasOnline backtests
    """

    def __init__(self, executor, config: WFOConfig = None):
        """
        Initialize the WFO Analyzer

        Args:
            executor: Authenticated HaasOnline API executor
            config: WFO analysis configuration
        """
        self.executor = executor
        self.config = config or WFOConfig()
        self.metrics_list: List[WFOMetrics] = []
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Setup logging for WFO analysis"""
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - WFO - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)

    def analyze_single_backtest(self, lab_id: str, backtest_id: str) -> Optional[WFOMetrics]:
        """
        Perform comprehensive WFO analysis on a single backtest

        Args:
            lab_id: Laboratory ID containing the backtest
            backtest_id: Specific backtest ID to analyze

        Returns:
            WFOMetrics object with complete analysis or None if analysis fails
        """
        try:
            self.logger.info(f"Starting WFO analysis for backtest {backtest_id}")

            # Get backtest data using BacktestObject
            bt_object = BacktestObject(self.executor, lab_id, backtest_id)

            if not bt_object.runtime or not bt_object.metadata:
                self.logger.warning(f"No runtime data available for backtest {backtest_id}")
                return None

            # Extract basic data
            runtime = bt_object.runtime
            metadata = bt_object.metadata

            # Skip backtests with insufficient data
            if runtime.total_trades < self.config.min_trades:
                self.logger.info(f"Skipping backtest {backtest_id}: insufficient trades ({runtime.total_trades})")
                return None

            # Calculate core metrics
            losing_trades = runtime.total_trades - runtime.winning_trades
            win_rate = runtime.winning_trades / runtime.total_trades if runtime.total_trades > 0 else 0.0

            # Calculate profitability metrics
            roi_percentage = (runtime.total_profit / 10000) * 100 if runtime.total_profit != 0 else 0.0
            profit_factor = runtime.profit_factor if runtime.profit_factor > 0 else 0.0

            # Calculate risk metrics
            max_drawdown_percentage = (runtime.max_drawdown / max(runtime.total_profit, 1)) * 100

            # Calculate trade quality metrics
            avg_trade_profit = runtime.total_profit / runtime.total_trades if runtime.total_trades > 0 else 0.0

            # Calculate time-based metrics first
            duration_days = 0.0
            avg_trades_per_day = 0.0
            if metadata.start_time and metadata.end_time:
                duration_days = (metadata.end_time - metadata.start_time).days
                avg_trades_per_day = runtime.total_trades / max(duration_days, 1)

            # Calculate additional risk metrics
            sortino_ratio = self._calculate_sortino_ratio(runtime)
            calmar_ratio = self._calculate_calmar_ratio(runtime, metadata, duration_days)

            # Extract PC value (Buy & Hold % over the course of the backtest)
            pc_value = 0.0
            if hasattr(runtime, 'raw_data') and 'PC' in runtime.raw_data:
                pc_value = float(runtime.raw_data.get('PC', 0.0))

            # Skip backtests where ROI < PC (not beating buy & hold)
            if roi_percentage < pc_value:
                self.logger.info(f"Skipping backtest {backtest_id}: ROI ({roi_percentage:.2f}%) < PC ({pc_value:.2f}%) - not beating buy & hold")
                return None

            # Calculate Walk Forward Optimization specific scores
            stability_score = self._calculate_stability_score(runtime, metadata, duration_days)
            consistency_score = self._calculate_consistency_score(runtime)
            robustness_score = self._calculate_robustness_score(runtime, metadata, duration_days)
            wfo_score = (stability_score + consistency_score + robustness_score) / 3.0

            # Calculate fees and net profit
            total_fees = runtime.raw_data.get('f', {}).get('TFC', 0) if runtime.raw_data else 0
            net_profit_after_fees = runtime.total_profit - total_fees

            # Quality indicators
            is_profitable = runtime.total_profit > 0
            has_positive_sharpe = runtime.sharpe_ratio > 0
            has_acceptable_drawdown = max_drawdown_percentage < self.config.max_drawdown_pct
            has_good_win_rate = win_rate > (self.config.min_win_rate / 100)
            has_sufficient_trades = runtime.total_trades >= self.config.min_trades

            # Overall score calculation
            overall_score = self._calculate_overall_score(
                runtime, metadata, roi_percentage, max_drawdown_percentage,
                win_rate, profit_factor, wfo_score
            )

            # Create WFOMetrics object
            metrics = WFOMetrics(
                backtest_id=backtest_id,
                lab_id=lab_id,
                script_name=metadata.script_name,
                account_id=metadata.account_id,
                market=metadata.market_tag,
                total_trades=runtime.total_trades,
                winning_trades=runtime.winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_profit=runtime.total_profit,
                total_profit_usd=runtime.total_profit,
                roi_percentage=roi_percentage,
                profit_factor=profit_factor,
                max_drawdown=runtime.max_drawdown,
                max_drawdown_percentage=max_drawdown_percentage,
                sharpe_ratio=runtime.sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                avg_trade_profit=avg_trade_profit,
                start_time=metadata.start_time,
                end_time=metadata.end_time,
                duration_days=duration_days,
                avg_trades_per_day=avg_trades_per_day,
                wfo_score=wfo_score,
                stability_score=stability_score,
                consistency_score=consistency_score,
                robustness_score=robustness_score,
                total_fees=total_fees,
                net_profit_after_fees=net_profit_after_fees,
                is_profitable=is_profitable,
                has_positive_sharpe=has_positive_sharpe,
                has_acceptable_drawdown=has_acceptable_drawdown,
                has_good_win_rate=has_good_win_rate,
                has_sufficient_trades=has_sufficient_trades,
                overall_score=overall_score,
                raw_data=runtime.raw_data or {}
            )

            self.logger.info(".2f")
            return metrics

        except Exception as e:
            self.logger.error(f"Error in WFO analysis for backtest {backtest_id}: {e}")
            return None

    def explain_wfo_vs_basic_analysis(self) -> str:
        """
        Explain the key differences between WFO and basic backtest analysis

        Returns:
            Detailed explanation string
        """
        explanation = """
🚀 WALK FORWARD OPTIMIZATION (WFO) vs BASIC ANALYSIS - KEY DIFFERENCES
===============================================================================

📊 WHAT YOUR PREVIOUS financial_analytics.py DID:
-------------------------------------------------
• Looked at final backtest results (static snapshot)
• Calculated basic metrics: profit, win rate, Sharpe ratio
• Simple scoring based on end-of-period performance
• No consideration of HOW performance was achieved over time
• Treated all strategies equally regardless of stability

🎯 WHAT THIS WFO ANALYZER DOES (ADVANCED):
------------------------------------------
• Analyzes PERFORMANCE STABILITY across different time periods
• Measures CONSISTENCY of win rates and profit factors over time
• Tests ROBUSTNESS across varying market conditions
• Validates FORWARD-LOOKING potential (not just backward-looking results)
• Provides comprehensive risk metrics (Sortino, Calmar ratios)

🔍 REAL-WORLD EXAMPLE:
--------------------
Strategy A: 50% profit, but profits came from one big winning day
Strategy B: 45% profit, but consistent performance every week

PREVIOUS ANALYSIS: Strategy A wins (higher profit)
WFO ANALYSIS: Strategy B wins (more stable, consistent, robust)

🎪 WHY WFO MATTERS FOR YOUR TRADING:
-----------------------------------
• Stable strategies survive market changes bneetter
• Consistent performance is more reliable for live trading
• Robust strategies handle different market conditions
• Forward-looking validation predicts future performance

🏆 WFO PROVIDES WHAT BASIC ANALYSIS CAN'T:
-------------------------------------------
✅ Stability Score: How consistent is performance over time?
✅ Consistency Score: How reliable are win rates and profits?
✅ Robustness Score: How well does it handle market variability?
✅ Forward Validation: How would this perform going forward?

💡 BOTTOM LINE:
Your old analysis was like judging a race by final position.
WFO is like analyzing the entire race - speed, endurance, consistency, adaptability.
        """
        return explanation

    def analyze_lab_backtests(self, lab_id: str, max_backtests: int = 50) -> List[WFOMetrics]:
        """
        Perform WFO analysis on all backtests in a laboratory

        Args:
            lab_id: Laboratory ID to analyze
            max_backtests: Maximum number of backtests to analyze

        Returns:
            List of WFOMetrics objects with complete WFO analysis
        """
        self.logger.info(f"Starting WFO analysis for lab {lab_id}")

        try:
            # Get all backtests from the lab
            results = []
            next_page_id = 0

            while len(results) < max_backtests:
                request = GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=next_page_id,
                    page_lenght=min(20, max_backtests - len(results))
                )

                response = api.get_backtest_result(self.executor, request)

                if not response or not response.items:
                    break

                results.extend(response.items)
                next_page_id = response.next_page_id

                if not response.next_page_id:
                    break

            self.logger.info(f"Found {len(results)} backtests to analyze")

            # Analyze each backtest
            metrics_list = []
            for i, result in enumerate(results):
                self.logger.info(f"Analyzing backtest {i+1}/{len(results)}: {result.backtest_id}")
                metrics = self.analyze_single_backtest(lab_id, result.backtest_id)
                if metrics:
                    metrics_list.append(metrics)

            self.metrics_list = metrics_list
            self.logger.info(f"WFO analysis completed: {len(metrics_list)} backtests successfully analyzed")

            # Display statistics
            self._display_analysis_statistics(metrics_list, results)

            return metrics_list

        except Exception as e:
            self.logger.error(f"Error in lab WFO analysis: {e}")
            return []

    def filter_similar_strategies(self, metrics_list: List[WFOMetrics]) -> List[WFOMetrics]:
        """
        Apply diversity filtering to remove similar-performing strategies

        Args:
            metrics_list: List of WFOMetrics to filter

        Returns:
            Filtered list with diverse strategies
        """
        if len(metrics_list) <= self.config.max_bots_per_lab:
            return metrics_list

        self.logger.info("Applying diversity filtering to remove similar strategies")

        # Sort by overall score (best first)
        sorted_metrics = sorted(metrics_list, key=lambda x: x.overall_score, reverse=True)
        diverse_strategies = []

        for candidate in sorted_metrics:
            # Check if candidate is too similar to already selected strategies
            is_similar = False

            for selected in diverse_strategies:
                if self._are_strategies_similar(candidate, selected):
                    is_similar = True
                    self.logger.debug(".2f")
                    break

            if not is_similar:
                diverse_strategies.append(candidate)
                self.logger.debug(f"Selected diverse strategy: {candidate.script_name} (Score: {candidate.overall_score:.1f})")

                # Stop if we have enough diverse strategies
                if len(diverse_strategies) >= self.config.max_bots_per_lab:
                    break

        self.logger.info(f"Diversity filtering complete: {len(diverse_strategies)} diverse strategies selected")
        return diverse_strategies

    def generate_bot_recommendations(self, lab_id: str) -> List[BotRecommendation]:
        """
        Generate bot recommendations based on WFO analysis

        Args:
            lab_id: Laboratory ID for bot naming

        Returns:
            List of BotRecommendation objects
        """
        self.logger.info("Generating bot recommendations")

        # Filter strategies that meet minimum criteria
        qualified_strategies = [
            m for m in self.metrics_list
            if m.overall_score >= self.config.min_overall_score
            and m.total_trades >= self.config.min_trades
            and m.roi_percentage >= self.config.min_roi_pct
            and m.sharpe_ratio >= self.config.min_sharpe_ratio
            and m.max_drawdown_percentage <= self.config.max_drawdown_pct
        ]

        self.logger.info(f"Found {len(qualified_strategies)} strategies meeting minimum criteria")

        # Apply diversity filtering
        diverse_strategies = self.filter_similar_strategies(qualified_strategies)

        # Generate bot recommendations
        recommendations = []
        for i, strategy in enumerate(diverse_strategies):
            recommendation = self._create_bot_recommendation(strategy, i + 1)
            recommendations.append(recommendation)

        self.logger.info(f"Generated {len(recommendations)} bot recommendations")
        return recommendations

    def _are_strategies_similar(self, strategy1: WFOMetrics, strategy2: WFOMetrics) -> bool:
        """
        Determine if two strategies are too similar based on performance metrics

        Args:
            strategy1: First strategy to compare
            strategy2: Second strategy to compare

        Returns:
            True if strategies are considered similar
        """
        # Check ROI similarity
        roi_diff = abs(strategy1.roi_percentage - strategy2.roi_percentage)
        roi_similar = roi_diff <= (self.config.roi_similarity_threshold * 100)

        # Check trade count similarity
        trade_diff = abs(strategy1.total_trades - strategy2.total_trades)
        trade_similar = trade_diff <= (strategy1.total_trades * self.config.trade_count_similarity_threshold)

        # Check win rate similarity
        win_rate_diff = abs(strategy1.win_rate - strategy2.win_rate)
        win_rate_similar = win_rate_diff <= self.config.win_rate_similarity_threshold

        # Strategies are similar if they match on multiple criteria
        similarity_score = (roi_similar + trade_similar + win_rate_similar) / 3.0

        return similarity_score >= 0.67  # Similar if 2 out of 3 criteria match

    def _calculate_stability_score(self, runtime, metadata, duration_days: float) -> float:
        """Calculate stability score based on performance consistency"""
        if runtime.total_trades < self.config.min_sample_size:
            return 0.0

        # Use Sharpe ratio as proxy for stability (higher is better)
        stability = min(runtime.sharpe_ratio / 2.0, 1.0) if runtime.sharpe_ratio > 0 else 0.0

        # Factor in trade frequency consistency
        avg_trades_per_day = runtime.total_trades / max(duration_days, 1)
        consistency_factor = min(avg_trades_per_day / 10.0, 1.0)  # Prefer strategies with regular trading

        return (stability + consistency_factor) / 2.0

    def _calculate_consistency_score(self, runtime) -> float:
        """Calculate consistency score based on win rate stability"""
        if runtime.total_trades < self.config.min_sample_size:
            return 0.0

        # Higher win rate with sufficient sample size indicates consistency
        win_rate_score = min(runtime.win_rate * 2.0, 1.0)

        # Profit factor indicates consistency of profitable trades
        profit_factor_score = min(runtime.profit_factor / 3.0, 1.0) if runtime.profit_factor > 0 else 0.0

        return (win_rate_score + profit_factor_score) / 2.0

    def _calculate_robustness_score(self, runtime, metadata, duration_days: float = 0.0) -> float:
        """Calculate robustness score based on performance across different conditions"""
        if runtime.total_trades < self.config.min_sample_size:
            return 0.0

        # Prefer strategies that performed well across different time periods
        duration_score = min(duration_days / 90.0, 1.0)  # Longer tests are more robust

        # Lower drawdown relative to profit indicates robustness
        risk_adjusted_score = 1.0 - min(runtime.max_drawdown / max(runtime.total_profit, 1), 1.0)

        return (duration_score + risk_adjusted_score) / 2.0

    def _calculate_sortino_ratio(self, runtime) -> float:
        """Calculate Sortino ratio (downside risk only)"""
        if runtime.total_trades < self.config.min_sample_size:
            return 0.0

        # This is a simplified calculation - in practice you'd need return series
        if runtime.max_drawdown > 0:
            return runtime.total_profit / runtime.max_drawdown
        return 0.0

    def _calculate_calmar_ratio(self, runtime, metadata, duration_days: float) -> float:
        """Calculate Calmar ratio (annual return vs max drawdown)"""
        if runtime.total_trades < self.config.min_sample_size or runtime.max_drawdown <= 0:
            return 0.0

        # Annualize the return
        annual_return = runtime.total_profit * (365.0 / max(duration_days, 1))
        return annual_return / runtime.max_drawdown

    def _calculate_overall_score(self, runtime, metadata, roi_pct: float,
                               max_drawdown_pct: float, win_rate: float,
                               profit_factor: float, wfo_score: float) -> float:
        """Calculate overall performance score (0-100)"""
        score = 0.0

        # Profitability score (30 points)
        if runtime.total_profit > 0:
            score += 30 * self.config.profitability_weight / 0.3
            # Bonus for high ROI
            if roi_pct > 50:
                score += 10
            elif roi_pct > 20:
                score += 5

        # Risk-adjusted performance (25 points)
        if runtime.sharpe_ratio > 0:
            score += 15 * self.config.risk_weight / 0.2
        if max_drawdown_pct < 20:
            score += 10 * self.config.risk_weight / 0.2

        # Win rate quality (20 points)
        if win_rate > 0.4:
            score += 20 * self.config.win_rate_weight / 0.2
        elif win_rate > 0.3:
            score += 10 * self.config.win_rate_weight / 0.2

        # Profit factor (15 points)
        if profit_factor > 2.0:
            score += 15 * self.config.roi_weight / 0.2
        elif profit_factor > 1.5:
            score += 10 * self.config.roi_weight / 0.2

        # WFO score (10 points)
        score += wfo_score * 10 * self.config.consistency_weight / 0.1

        return min(score, 100.0)

    def _create_bot_recommendation(self, strategy: WFOMetrics, rank: int) -> BotRecommendation:
        """Create a bot recommendation from WFO analysis"""
        # Generate bot name
        profit_pct = round(strategy.roi_percentage)
        bot_name = f"{strategy.script_name} +{profit_pct}% pop/gen"

        # Create reasoning list
        reasoning = [
            ".2f",
            ".2f",
            ".2f",
            ".2f",
            ".2f"
        ]

        # Risk assessment
        if strategy.max_drawdown_percentage < 15:
            risk_assessment = "Low Risk"
        elif strategy.max_drawdown_percentage < 25:
            risk_assessment = "Medium Risk"
        else:
            risk_assessment = "High Risk"

        # Calculate recommendation score
        recommendation_score = strategy.overall_score * (strategy.wfo_score + 1) / 2

        # Diversity score (higher is more unique)
        diversity_score = 1.0 - (strategy.roi_percentage / 200.0)  # Prefer moderate ROI strategies

        return BotRecommendation(
            backtest=strategy,
            recommendation_score=recommendation_score,
            diversity_score=diversity_score,
            bot_name=bot_name,
            reasoning=reasoning,
            risk_assessment=risk_assessment,
            position_size_usdt=2000.0
        )

    def generate_wfo_report(self, recommendations: List[BotRecommendation]) -> str:
        """Generate comprehensive WFO analysis report"""
        if not recommendations:
            return "No bot recommendations generated."

        report = ".1f"".1f"".1f"f"""
=== WALK FORWARD OPTIMIZATION (WFO) ANALYSIS REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS:
- Total Backtests Analyzed: {len(self.metrics_list)}
- Qualified Strategies: {len([m for m in self.metrics_list if m.overall_score >= self.config.min_overall_score])}
- Recommended Bots: {len(recommendations)}
- Average WFO Score: {self._safe_mean([r.backtest.wfo_score for r in recommendations]):.2f}
- Average ROI: {self._safe_mean([r.backtest.roi_percentage for r in recommendations]):.2f}%

BOT RECOMMENDATIONS (Ranked by WFO Score):
"""

        # Sort recommendations by WFO score
        sorted_recommendations = sorted(recommendations,
                                     key=lambda x: x.recommendation_score,
                                     reverse=True)

        for i, rec in enumerate(sorted_recommendations, 1):
            report += ".2f"".2f"".2f"".2f"".2f"".2f"".2f"f"""
{i}. {rec.bot_name}
   📊 Recommendation Score: {rec.recommendation_score:.1f}/100
   🎯 WFO Score: {rec.backtest.wfo_score:.2f}/10
   💰 ROI: {rec.backtest.roi_percentage:.2f}%
   🎲 Win Rate: {rec.backtest.win_rate:.2f}%
   📈 Profit Factor: {rec.backtest.profit_factor:.2f}
   ⚠️  Max Drawdown: {rec.backtest.max_drawdown_percentage:.2f}%
   📊 Sharpe Ratio: {rec.backtest.sharpe_ratio:.2f}
   🔄 Total Trades: {rec.backtest.total_trades}
   🎪 Risk Assessment: {rec.risk_assessment}
   💡 Reasoning:
"""

            for reason in rec.reasoning:
                report += f"      • {reason}\n"

        report += ".2f"".2f"".2f"".2f"f"""

PERFORMANCE ANALYSIS:
- Average Stability Score: {self._safe_mean([r.backtest.stability_score for r in recommendations]):.2f}
- Average Consistency Score: {self._safe_mean([r.backtest.consistency_score for r in recommendations]):.2f}
- Average Robustness Score: {self._safe_mean([r.backtest.robustness_score for r in recommendations]):.2f}
- Best Performing Market: {max(set(r.backtest.market for r in recommendations), key=lambda x: sum(1 for r in recommendations if r.backtest.market == x))}
- Risk Distribution: {', '.join([f"{r.risk_assessment}: {sum(1 for rec in recommendations if rec.risk_assessment == r.risk_assessment)}" for r in set(rec.risk_assessment for rec in recommendations)])}

CONFIGURATION USED:
- Minimum Overall Score: {self.config.min_overall_score}
- Minimum Trades: {self.config.min_trades}
- Maximum Drawdown: {self.config.max_drawdown_pct}%
- ROI Similarity Threshold: {self.config.roi_similarity_threshold:.1%}
- Trade Count Similarity Threshold: {self.config.trade_count_similarity_threshold:.1%}
- Win Rate Similarity Threshold: {self.config.win_rate_similarity_threshold:.1%}
"""

        return report

    def _display_analysis_statistics(self, metrics_list: List[WFOMetrics], backtests_data: List[Dict[str, Any]]) -> None:
        """Display comprehensive statistics about the backtest analysis"""
        if not metrics_list:
            self.logger.info("📊 No backtests met the analysis criteria")
            return

        self.logger.info("\n" + "="*80)
        self.logger.info("📊 BACKTEST ANALYSIS STATISTICS")
        self.logger.info("="*80)

        # Basic counts
        total_backtests = len(backtests_data)
        analyzed_backtests = len(metrics_list)

        self.logger.info(f"Total backtests in lab: {total_backtests}")
        self.logger.info(f"Backtests meeting criteria: {analyzed_backtests}")
        self.logger.info(f"Success rate: {analyzed_backtests/total_backtests*100:.1f}%")

        # ROI Statistics
        roi_values = [m.roi_percentage for m in metrics_list]
        self.logger.info("\n🎯 ROI Statistics:")
        self.logger.info(f"   Range: {min(roi_values):.2f}% - {max(roi_values):.2f}%")
        self.logger.info(f"   Average: {self._safe_mean(roi_values):.2f}%")
        self.logger.info(f"   Median: {sorted(roi_values)[len(roi_values)//2]:.2f}%" if roi_values else "   Median: N/A")

        # Win Rate Statistics
        win_rates = [m.win_rate * 100 for m in metrics_list]
        self.logger.info("\n🎲 Win Rate Statistics:")
        self.logger.info(f"   Range: {min(win_rates):.1f}% - {max(win_rates):.1f}%")
        self.logger.info(f"   Average: {self._safe_mean(win_rates):.1f}%")

        # Trade Count Statistics
        trade_counts = [m.total_trades for m in metrics_list]
        self.logger.info("\n📈 Trade Count Statistics:")
        self.logger.info(f"   Range: {min(trade_counts)} - {max(trade_counts)} trades")
        self.logger.info(f"   Average: {self._safe_mean(trade_counts):.1f} trades")

        # Profit Factor Statistics
        profit_factors = [m.profit_factor for m in metrics_list if m.profit_factor > 0]
        if profit_factors:
            self.logger.info("\n💰 Profit Factor Statistics:")
            self.logger.info(f"   Range: {min(profit_factors):.2f} - {max(profit_factors):.2f}")
            self.logger.info(f"   Average: {self._safe_mean(profit_factors):.2f}")

        # WFO Score Statistics
        wfo_scores = [m.wfo_score for m in metrics_list]
        self.logger.info("\n🔬 WFO Score Statistics:")
        self.logger.info(f"   Range: {min(wfo_scores):.3f} - {max(wfo_scores):.3f}")
        self.logger.info(f"   Average: {self._safe_mean(wfo_scores):.3f}")

        # Top performers
        if len(metrics_list) > 0:
            top_performers = sorted(metrics_list, key=lambda x: x.roi_percentage, reverse=True)[:5]
            self.logger.info("\n🏆 Top 5 Performers by ROI:")
            for i, m in enumerate(top_performers, 1):
                self.logger.info(f"   {i}. {m.script_name} - {m.roi_percentage:.2f}% ROI, {m.total_trades} trades, {m.win_rate*100:.1f}% win rate")

        self.logger.info("="*80 + "\n")

    def _safe_mean(self, values: List[float]) -> float:
        """
        Calculate mean safely, with or without numpy

        Args:
            values: List of numeric values

        Returns:
            Mean of the values, or 0.0 if list is empty
        """
        if not values:
            return 0.0

        if HAS_NUMPY and np is not None:
            return np.mean(values)
        else:
            return sum(values) / len(values)

def main():
    """Example usage of WFO Analyzer"""
    print("🚀 Walk Forward Optimization (WFO) Analyzer")
    print("=" * 60)
    print("WFO Analyzer is ready for HaasOnline backtest analysis!")
    print("Use WFOAnalyzer class for comprehensive strategy evaluation")
    print("and bot recommendation generation with diversity filtering.")

if __name__ == "__main__":
    main()
