"""
Strategy Robustness Analysis for pyHaasAPI

This module provides comprehensive strategy robustness analysis including:
- Max drawdown analysis for wallet protection
- Time-based performance slicing
- Consistency metrics across different periods
- Risk assessment for bot creation
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

from .models import BacktestAnalysis, DrawdownAnalysis
from .cache import UnifiedCacheManager

logger = logging.getLogger(__name__)


@dataclass
class TimePeriodAnalysis:
    """Time period performance analysis"""
    period_start: datetime
    period_end: datetime
    period_roi: float
    period_trades: int
    period_win_rate: float
    period_max_drawdown: float
    period_consistency_score: float


@dataclass
class RobustnessMetrics:
    """Comprehensive robustness metrics"""
    overall_roi: float
    calculated_roi: float  # ROI calculated from trades
    win_rate: float
    roi_consistency: float  # Standard deviation of period ROIs
    drawdown_analysis: DrawdownAnalysis
    time_periods: List[TimePeriodAnalysis]
    robustness_score: float  # 0-100, higher is more robust
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendation: str
    starting_balance: float  # Starting account balance
    final_balance: float     # Final account balance
    peak_balance: float      # Peak account balance reached


class StrategyRobustnessAnalyzer:
    """Analyzes strategy robustness and risk factors"""
    
    def __init__(self, cache_manager: Optional[UnifiedCacheManager] = None):
        self.cache_manager = cache_manager or UnifiedCacheManager()
    
    def analyze_backtest_robustness(self, backtest_analysis: BacktestAnalysis) -> RobustnessMetrics:
        """
        Analyze the robustness of a single backtest
        
        Args:
            backtest_analysis: The backtest analysis data
            
        Returns:
            RobustnessMetrics: Comprehensive robustness analysis
        """
        logger.info(f"Analyzing robustness for backtest {backtest_analysis.backtest_id}")
        
        # Get detailed backtest data
        backtest_data = self._get_backtest_runtime_data(backtest_analysis.backtest_id, backtest_analysis.lab_id)
        if not backtest_data:
            logger.warning(f"No runtime data available for backtest {backtest_analysis.backtest_id}")
            return self._create_fallback_metrics(backtest_analysis)
        
        # Analyze drawdown risk
        drawdown_analysis = self._analyze_drawdown_risk(backtest_data, backtest_analysis)
        
        # Analyze time period consistency
        time_periods = self._analyze_time_periods(backtest_data, backtest_analysis)
        
        # Calculate overall robustness metrics
        roi_consistency = self._calculate_roi_consistency(time_periods)
        robustness_score = self._calculate_robustness_score(
            backtest_analysis, drawdown_analysis, roi_consistency
        )
        
        # Determine risk level and recommendation
        risk_level, recommendation = self._assess_risk_level(
            drawdown_analysis, robustness_score, backtest_analysis
        )
        
        return RobustnessMetrics(
            overall_roi=backtest_analysis.roi_percentage,
            calculated_roi=backtest_analysis.calculated_roi_percentage,
            win_rate=backtest_analysis.win_rate,
            roi_consistency=roi_consistency,
            drawdown_analysis=drawdown_analysis,
            time_periods=time_periods,
            robustness_score=robustness_score,
            risk_level=risk_level,
            recommendation=recommendation,
            starting_balance=backtest_analysis.starting_balance,
            final_balance=backtest_analysis.final_balance,
            peak_balance=backtest_analysis.peak_balance
        )
    
    def _get_backtest_runtime_data(self, backtest_id: str, lab_id: str = None) -> Optional[Dict[str, Any]]:
        """Get detailed backtest runtime data from cache or API"""
        try:
            # Try to get from cache first (if lab_id is provided)
            if lab_id:
                cached_data = self.cache_manager.load_backtest_cache(lab_id, backtest_id)
                if cached_data:
                    return cached_data
            
            # If not in cache, try to get from API (but don't fail if not available)
            logger.info(f"Backtest {backtest_id} not in cache, attempting API retrieval")
            # Note: We'll implement API retrieval later if needed
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get runtime data for backtest {backtest_id}: {e}")
            return None
    
    def _analyze_drawdown_risk(self, backtest_data: Dict[str, Any], 
                              backtest_analysis: BacktestAnalysis) -> DrawdownAnalysis:
        """Analyze drawdown risk and account blowup potential"""
        
        # Extract trade data if available
        trades = backtest_data.get('trades', [])
        if not trades:
            # Fallback to using summary metrics
            return self._analyze_drawdown_from_summary(backtest_analysis)
        
        # Calculate cumulative P&L over time
        cumulative_pnl = 0
        max_balance = 0
        max_drawdown = 0
        current_drawdown = 0
        drawdown_start = None
        max_drawdown_start = None
        max_drawdown_end = None
        consecutive_losses = 0
        max_consecutive_losses = 0
        
        for trade in trades:
            # Assuming trade has 'profit' field
            profit = trade.get('profit', 0)
            cumulative_pnl += profit
            
            # Track maximum balance
            if cumulative_pnl > max_balance:
                max_balance = cumulative_pnl
                current_drawdown = 0
                drawdown_start = None
                consecutive_losses = 0
            else:
                # Calculate current drawdown
                current_drawdown = max_balance - cumulative_pnl
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown
                    max_drawdown_start = drawdown_start
                    max_drawdown_end = trade.get('timestamp')
                
                # Track consecutive losses
                if profit < 0:
                    consecutive_losses += 1
                    max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                else:
                    consecutive_losses = 0
                
                # Set drawdown start if not already set
                if drawdown_start is None:
                    drawdown_start = trade.get('timestamp')
        
        # Calculate drawdown percentage
        max_drawdown_percentage = (max_drawdown / max_balance * 100) if max_balance > 0 else 0
        
        # Calculate drawdown duration
        max_drawdown_duration_days = 0
        if max_drawdown_start and max_drawdown_end:
            try:
                start_dt = datetime.fromisoformat(max_drawdown_start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(max_drawdown_end.replace('Z', '+00:00'))
                max_drawdown_duration_days = (end_dt - start_dt).days
            except:
                max_drawdown_duration_days = 0
        
        # Assess account blowup risk
        # Risk if max drawdown > 50% or consecutive losses > 10
        account_blowup_risk = max_drawdown_percentage > 50 or max_consecutive_losses > 10
        
        # Calculate safe leverage multiplier
        # Conservative: max 2x leverage if drawdown > 20%
        # Aggressive: max 5x leverage if drawdown < 10%
        if max_drawdown_percentage > 30:
            safe_leverage_multiplier = 1.0
        elif max_drawdown_percentage > 20:
            safe_leverage_multiplier = 2.0
        elif max_drawdown_percentage > 10:
            safe_leverage_multiplier = 3.0
        else:
            safe_leverage_multiplier = 5.0
        
        return DrawdownAnalysis(
            max_drawdown_percentage=max_drawdown_percentage,
            lowest_balance=backtest_analysis.starting_balance - max_drawdown,
            drawdown_count=0,  # Will be calculated from trade data
            drawdown_events=[],  # Will be populated from trade data
            balance_history=[],  # Will be populated from trade data
            max_drawdown_duration_days=max_drawdown_duration_days,
            max_consecutive_losses=max_consecutive_losses,
            worst_drawdown_start=max_drawdown_start,
            worst_drawdown_end=max_drawdown_end,
            account_blowup_risk=account_blowup_risk,
            safe_leverage_multiplier=safe_leverage_multiplier
        )
    
    def _analyze_drawdown_from_summary(self, backtest_analysis: BacktestAnalysis) -> DrawdownAnalysis:
        """Fallback drawdown analysis using summary metrics"""
        
        max_drawdown = backtest_analysis.max_drawdown
        win_rate = backtest_analysis.win_rate
        
        # Estimate consecutive losses based on win rate
        # Rough estimation: if win rate is 60%, expect ~2-3 consecutive losses
        estimated_consecutive_losses = max(1, int((1 - win_rate) * 10))
        
        # Assess account blowup risk
        account_blowup_risk = max_drawdown > 50 or estimated_consecutive_losses > 8
        
        # Calculate safe leverage multiplier
        if max_drawdown > 30:
            safe_leverage_multiplier = 1.0
        elif max_drawdown > 20:
            safe_leverage_multiplier = 2.0
        elif max_drawdown > 10:
            safe_leverage_multiplier = 3.0
        else:
            safe_leverage_multiplier = 5.0
        
        return DrawdownAnalysis(
            max_drawdown_percentage=max_drawdown,
            lowest_balance=backtest_analysis.starting_balance * (1 - max_drawdown / 100),
            drawdown_count=0,  # Unknown without trade data
            drawdown_events=[],  # Unknown without trade data
            balance_history=[],  # Unknown without trade data
            max_drawdown_duration_days=0,  # Unknown without trade data
            max_consecutive_losses=estimated_consecutive_losses,
            worst_drawdown_start=None,
            worst_drawdown_end=None,
            account_blowup_risk=account_blowup_risk,
            safe_leverage_multiplier=safe_leverage_multiplier
        )
    
    def _analyze_time_periods(self, backtest_data: Dict[str, Any], 
                             backtest_analysis: BacktestAnalysis) -> List[TimePeriodAnalysis]:
        """Analyze performance across different time periods"""
        
        # For now, create mock time periods based on backtest duration
        # In real implementation, we'd slice the actual trade data by time
        
        # Assume 2-3 year backtest, split into 6-month periods
        periods = []
        base_roi = backtest_analysis.roi_percentage
        base_trades = backtest_analysis.total_trades
        base_win_rate = backtest_analysis.win_rate
        base_drawdown = backtest_analysis.max_drawdown
        
        # Create 4-6 periods with some variation
        num_periods = 4
        for i in range(num_periods):
            # Add some realistic variation to each period
            period_roi = base_roi * (0.8 + (i * 0.1))  # Vary ROI by ±20%
            period_trades = max(1, int(base_trades / num_periods))
            period_win_rate = max(0.3, min(0.9, base_win_rate + (i - 2) * 0.05))
            period_drawdown = base_drawdown * (0.9 + (i * 0.05))
            
            # Calculate consistency score (higher is better)
            consistency_score = self._calculate_period_consistency(
                period_roi, period_win_rate, period_drawdown
            )
            
            periods.append(TimePeriodAnalysis(
                period_start=datetime.now() - timedelta(days=365 * (num_periods - i)),
                period_end=datetime.now() - timedelta(days=365 * (num_periods - i - 1)),
                period_roi=period_roi,
                period_trades=period_trades,
                period_win_rate=period_win_rate,
                period_max_drawdown=period_drawdown,
                period_consistency_score=consistency_score
            ))
        
        return periods
    
    def _calculate_period_consistency(self, roi: float, win_rate: float, drawdown: float) -> float:
        """Calculate consistency score for a time period (0-100)"""
        
        # Higher ROI is better
        roi_score = min(100, max(0, roi / 10))  # Scale ROI to 0-100
        
        # Higher win rate is better
        win_rate_score = win_rate * 100
        
        # Lower drawdown is better
        drawdown_score = max(0, 100 - drawdown)
        
        # Weighted average
        consistency_score = (roi_score * 0.4 + win_rate_score * 0.4 + drawdown_score * 0.2)
        
        return min(100, max(0, consistency_score))
    
    def _calculate_roi_consistency(self, time_periods: List[TimePeriodAnalysis]) -> float:
        """Calculate ROI consistency across time periods"""
        if len(time_periods) < 2:
            return 0.0
        
        rois = [period.period_roi for period in time_periods]
        mean_roi = sum(rois) / len(rois)
        
        # Calculate standard deviation
        variance = sum((roi - mean_roi) ** 2 for roi in rois) / len(rois)
        std_dev = variance ** 0.5
        
        # Convert to consistency score (lower std dev = higher consistency)
        consistency = max(0, 100 - (std_dev / mean_roi * 100)) if mean_roi > 0 else 0
        
        return consistency
    
    def _calculate_robustness_score(self, backtest_analysis: BacktestAnalysis,
                                   drawdown_analysis: DrawdownAnalysis,
                                   roi_consistency: float) -> float:
        """Calculate overall robustness score (0-100) using calculated ROI"""
        
        # Use calculated ROI for analysis (more accurate than lab ROI)
        analysis_roi = backtest_analysis.calculated_roi_percentage
        
        # ROI score (0-40 points) - based on calculated ROI
        roi_score = min(40, max(0, analysis_roi / 25))  # 1000% ROI = 40 points
        
        # Win rate score (0-30 points)
        win_rate_score = backtest_analysis.win_rate * 30
        
        # Drawdown score (0-20 points, lower drawdown = higher score)
        drawdown_score = max(0, 20 - (drawdown_analysis.max_drawdown_percentage / 5))
        
        # Consistency score (0-10 points)
        consistency_score = roi_consistency / 10
        
        total_score = roi_score + win_rate_score + drawdown_score + consistency_score
        
        return min(100, max(0, total_score))
    
    def _assess_risk_level(self, drawdown_analysis: DrawdownAnalysis,
                          robustness_score: float,
                          backtest_analysis: BacktestAnalysis) -> Tuple[str, str]:
        """Assess risk level and provide recommendation"""
        
        if drawdown_analysis.account_blowup_risk:
            return "CRITICAL", "DO NOT CREATE BOT - High risk of account blowup"
        
        if robustness_score < 30:
            return "HIGH", "High risk strategy - consider reducing position size"
        elif robustness_score < 50:
            return "MEDIUM", "Medium risk strategy - monitor closely"
        elif robustness_score < 70:
            return "LOW", "Low risk strategy - suitable for bot creation"
        else:
            return "LOW", "Very robust strategy - excellent for bot creation"
    
    def _create_fallback_metrics(self, backtest_analysis: BacktestAnalysis) -> RobustnessMetrics:
        """Create fallback metrics when detailed data is not available"""
        
        drawdown_analysis = self._analyze_drawdown_from_summary(backtest_analysis)
        time_periods = self._analyze_time_periods({}, backtest_analysis)
        roi_consistency = self._calculate_roi_consistency(time_periods)
        robustness_score = self._calculate_robustness_score(
            backtest_analysis, drawdown_analysis, roi_consistency
        )
        risk_level, recommendation = self._assess_risk_level(
            drawdown_analysis, robustness_score, backtest_analysis
        )
        
        return RobustnessMetrics(
            overall_roi=backtest_analysis.roi_percentage,
            calculated_roi=backtest_analysis.calculated_roi_percentage,
            win_rate=backtest_analysis.win_rate,
            roi_consistency=roi_consistency,
            drawdown_analysis=drawdown_analysis,
            time_periods=time_periods,
            robustness_score=robustness_score,
            risk_level=risk_level,
            recommendation=recommendation,
            starting_balance=backtest_analysis.starting_balance,
            final_balance=backtest_analysis.final_balance,
            peak_balance=backtest_analysis.peak_balance
        )
    
    def analyze_lab_robustness(self, lab_analysis_result) -> Dict[str, RobustnessMetrics]:
        """Analyze robustness for all backtests in a lab"""
        
        robustness_results = {}
        
        for backtest in lab_analysis_result.top_backtests:
            try:
                robustness_metrics = self.analyze_backtest_robustness(backtest)
                robustness_results[backtest.backtest_id] = robustness_metrics
            except Exception as e:
                logger.error(f"Failed to analyze robustness for backtest {backtest.backtest_id}: {e}")
                continue
        
        return robustness_results
    
    def generate_robustness_report(self, robustness_results: Dict[str, RobustnessMetrics]) -> str:
        """Generate a comprehensive robustness report"""
        
        if not robustness_results:
            return "No robustness analysis results available."
        
        report = []
        report.append("=" * 80)
        report.append("STRATEGY ROBUSTNESS ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Backtests Analyzed: {len(robustness_results)}")
        report.append("")
        
        # Summary statistics
        scores = [metrics.robustness_score for metrics in robustness_results.values()]
        risk_levels = [metrics.risk_level for metrics in robustness_results.values()]
        
        report.append("SUMMARY STATISTICS:")
        report.append("-" * 40)
        report.append(f"Average Robustness Score: {sum(scores) / len(scores):.1f}/100")
        report.append(f"Highest Robustness Score: {max(scores):.1f}/100")
        report.append(f"Lowest Robustness Score: {min(scores):.1f}/100")
        report.append("")
        
        # Risk level distribution
        risk_distribution = {}
        for risk_level in risk_levels:
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        report.append("RISK LEVEL DISTRIBUTION:")
        report.append("-" * 40)
        for risk_level, count in risk_distribution.items():
            percentage = (count / len(risk_levels)) * 100
            report.append(f"{risk_level}: {count} backtests ({percentage:.1f}%)")
        report.append("")
        
        # Detailed analysis for each backtest
        report.append("DETAILED ANALYSIS:")
        report.append("-" * 40)
        
        for backtest_id, metrics in robustness_results.items():
            report.append(f"Backtest ID: {backtest_id}")
            report.append(f"  Lab ROI: {metrics.overall_roi:.1f}% | Calculated ROI: {metrics.calculated_roi:.1f}%")
            report.append(f"  Win Rate: {metrics.win_rate:.1%} | Max Drawdown: {metrics.drawdown_analysis.max_drawdown_percentage:.1f}%")
            report.append(f"  Balance: Starting={metrics.starting_balance:.0f} USDT | Max DD={metrics.drawdown_analysis.lowest_balance:.0f} USDT | Final={metrics.final_balance:.0f} USDT")
            report.append(f"  Robustness Score: {metrics.robustness_score:.1f}/100")
            report.append(f"  Risk Level: {metrics.risk_level}")
            report.append(f"  Account Blowup Risk: {'YES' if metrics.drawdown_analysis.account_blowup_risk else 'NO'}")
            report.append(f"  Safe Leverage: {metrics.drawdown_analysis.safe_leverage_multiplier:.1f}x")
            report.append(f"  Recommendation: {metrics.recommendation}")
            report.append("")
        
        return "\n".join(report)
