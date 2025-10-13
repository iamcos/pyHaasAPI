"""
Analysis Service for pyHaasAPI v2

This module provides business logic for analysis operations, using proven working patterns
from the existing analysis tools and cache management modules.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass

from ...api.lab import LabAPI
from ...api.backtest import BacktestAPI
from ...api.bot import BotAPI
from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import AnalysisError, LabNotFoundError
from ...core.logging import get_logger
from ...models.backtest import BacktestResult, BacktestRuntimeData
from ...analysis.metrics import RunMetrics, compute_metrics, calculate_risk_score, calculate_stability_score
from ...analysis.extraction import BacktestDataExtractor, BacktestSummary, TradeData
from ...config.analysis_config import get_analysis_config, get_drawdown_policy, validate_drawdown_requirement, get_drawdown_score

logger = get_logger("analysis_service")


@dataclass
class BacktestPerformance:
    """Data class for backtest performance metrics"""
    backtest_id: str
    lab_id: str
    generation_idx: int
    population_idx: int
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    starting_balance: float
    final_balance: float
    peak_balance: float
    script_name: str
    market_tag: str


@dataclass
class LabAnalysisResult:
    """Result of comprehensive lab analysis"""
    lab_id: str
    lab_name: str
    script_name: str
    market_tag: str
    total_backtests: int
    top_performers: List[BacktestPerformance]
    average_roi: float
    best_roi: float
    average_win_rate: float
    best_win_rate: float
    analysis_timestamp: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class AnalysisReport:
    """Comprehensive analysis report"""
    report_id: str
    report_type: str
    lab_ids: List[str]
    analysis_results: List[LabAnalysisResult]
    summary_statistics: Dict[str, Any]
    recommendations: List[str]
    generated_timestamp: str


class AnalysisService:
    """
    Analysis Service with business logic for analysis operations.

    Provides comprehensive analysis functionality including lab analysis,
    performance evaluation, and reporting using proven working patterns from v1.
    """

    def __init__(
        self,
        lab_api: LabAPI,
        backtest_api: BacktestAPI,
        bot_api: BotAPI,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ):
        self.lab_api = lab_api
        self.backtest_api = backtest_api
        self.bot_api = bot_api
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("analysis_service")
        self.data_extractor = BacktestDataExtractor()
        
        # Load configuration
        self.config = get_analysis_config()
        self.drawdown_policy = get_drawdown_policy()
        
        # Log configuration
        self.logger.info(f"Analysis service initialized with zero_drawdown_only={self.config.zero_drawdown_only}")

    # Lab Analysis Operations

    async def analyze_lab_comprehensive(
        self,
        lab_id: str,
        top_count: int = 10,
        min_win_rate: float = 0.3,
        min_trades: int = 5,
        sort_by: str = "roe"
    ) -> LabAnalysisResult:
        """
        Perform comprehensive lab analysis using proven working patterns.

        Args:
            lab_id: ID of the lab to analyze
            top_count: Number of top performers to return
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            sort_by: Field to sort by (roi, roe, winrate, profit, trades)

        Returns:
            LabAnalysisResult with analysis details

        Raises:
            AnalysisError: If analysis fails
        """
        try:
            self.logger.info(f"Performing comprehensive analysis for lab {lab_id}")

            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            if not lab_details:
                raise LabNotFoundError(f"Lab {lab_id} not found")

            # Get all backtests for the lab
            all_backtests = await self.backtest_api.get_all_backtests_for_lab(lab_id)
            
            if not all_backtests:
                return LabAnalysisResult(
                    lab_id=lab_id,
                    lab_name=lab_details.name,
                    script_name=lab_details.script_name,
                    market_tag=lab_details.settings.market_tag,
                    total_backtests=0,
                    top_performers=[],
                    average_roi=0.0,
                    best_roi=0.0,
                    average_win_rate=0.0,
                    best_win_rate=0.0,
                    analysis_timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message="No backtests found"
                )

            # Convert to performance objects and filter
            performances = []
            for backtest in all_backtests:
                # Apply filters
                if backtest.win_rate < min_win_rate:
                    continue
                if backtest.total_trades < min_trades:
                    continue
                
                # CRITICAL: Validate drawdown requirements using configuration
                if not validate_drawdown_requirement(backtest.max_drawdown, self.config):
                    self.logger.debug(f"Rejecting backtest {backtest.backtest_id} due to drawdown policy violation: {backtest.max_drawdown}")
                    continue

                # Convert to performance object
                performance = BacktestPerformance(
                    backtest_id=backtest.backtest_id,
                    lab_id=lab_id,
                    generation_idx=getattr(backtest, 'generation_idx', 0),
                    population_idx=getattr(backtest, 'population_idx', 0),
                    roi_percentage=backtest.roi_percentage,
                    win_rate=backtest.win_rate,
                    total_trades=backtest.total_trades,
                    max_drawdown=backtest.max_drawdown,
                    realized_profits_usdt=backtest.realized_profits_usdt,
                    starting_balance=getattr(backtest, 'starting_balance', 10000.0),
                    final_balance=getattr(backtest, 'final_balance', 10000.0),
                    peak_balance=getattr(backtest, 'peak_balance', 10000.0),
                    script_name=lab_details.script_name,
                    market_tag=lab_details.market_tag
                )
                performances.append(performance)

            # Sort by specified field
            if sort_by == "roi":
                performances.sort(key=lambda x: x.roi_percentage, reverse=True)
            elif sort_by == "roe":
                # ROE is typically ROI in this context
                performances.sort(key=lambda x: x.roi_percentage, reverse=True)
            elif sort_by == "winrate":
                performances.sort(key=lambda x: x.win_rate, reverse=True)
            elif sort_by == "profit":
                performances.sort(key=lambda x: x.realized_profits_usdt, reverse=True)
            elif sort_by == "trades":
                performances.sort(key=lambda x: x.total_trades, reverse=True)
            else:
                performances.sort(key=lambda x: x.roi_percentage, reverse=True)

            # Get top performers
            top_performers = performances[:top_count]

            # Calculate statistics
            total_backtests = len(performances)
            if total_backtests > 0:
                average_roi = sum(p.roi_percentage for p in performances) / total_backtests
                best_roi = max(p.roi_percentage for p in performances)
                average_win_rate = sum(p.win_rate for p in performances) / total_backtests
                best_win_rate = max(p.win_rate for p in performances)
            else:
                average_roi = 0.0
                best_roi = 0.0
                average_win_rate = 0.0
                best_win_rate = 0.0

            return LabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_details.name,
                script_name=lab_details.script_name,
                market_tag=lab_details.settings.market_tag,
                total_backtests=total_backtests,
                top_performers=top_performers,
                average_roi=average_roi,
                best_roi=best_roi,
                average_win_rate=average_win_rate,
                best_win_rate=best_win_rate,
                analysis_timestamp=datetime.now().isoformat(),
                success=True
            )

        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze lab: {e}")
            raise AnalysisError(f"Failed to analyze lab {lab_id}: {e}") from e

    async def analyze_multiple_labs(
        self,
        lab_ids: List[str],
        top_count: int = 10,
        min_win_rate: float = 0.3,
        min_trades: int = 5,
        sort_by: str = "roe"
    ) -> List[LabAnalysisResult]:
        """
        Analyze multiple labs in parallel.

        Args:
            lab_ids: List of lab IDs to analyze
            top_count: Number of top performers per lab
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            sort_by: Field to sort by

        Returns:
            List of LabAnalysisResult objects

        Raises:
            AnalysisError: If analysis fails
        """
        try:
            self.logger.info(f"Analyzing {len(lab_ids)} labs in parallel")

            # Create analysis tasks
            tasks = [
                self.analyze_lab_comprehensive(
                    lab_id=lab_id,
                    top_count=top_count,
                    min_win_rate=min_win_rate,
                    min_trades=min_trades,
                    sort_by=sort_by
                )
                for lab_id in lab_ids
            ]

            # Execute analyses in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and return successful results
            successful_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to analyze lab {lab_ids[i]}: {result}")
                else:
                    successful_results.append(result)

            self.logger.info(f"Successfully analyzed {len(successful_results)}/{len(lab_ids)} labs")
            return successful_results

        except Exception as e:
            self.logger.error(f"Failed to analyze multiple labs: {e}")
            raise AnalysisError(f"Failed to analyze multiple labs: {e}") from e

    # Performance Analysis and Metrics

    async def calculate_performance_metrics(
        self,
        backtest_id: str,
        lab_id: str
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for a backtest.

        Args:
            backtest_id: ID of the backtest
            lab_id: ID of the lab containing the backtest

        Returns:
            Dictionary with performance metrics

        Raises:
            AnalysisError: If metric calculation fails
        """
        try:
            self.logger.info(f"Calculating performance metrics for backtest {backtest_id}")

            # Get backtest runtime data
            runtime_data = await self.backtest_api.get_full_backtest_runtime_data(lab_id, backtest_id)

            # Extract performance metrics from runtime data
            metrics = {
                "backtest_id": backtest_id,
                "lab_id": lab_id,
                "script_name": getattr(runtime_data, 'ScriptName', 'Unknown'),
                "market_tag": getattr(runtime_data, 'PriceMarket', 'Unknown'),
                "account_id": getattr(runtime_data, 'AccountId', 'Unknown'),
                "calculation_timestamp": datetime.now().isoformat()
            }

            # Extract metrics from reports
            if hasattr(runtime_data, 'Reports') and runtime_data.Reports:
                for report_key, report in runtime_data.Reports.items():
                    if hasattr(report, 'P'):
                        p_data = report.P
                        metrics.update({
                            "total_trades": getattr(p_data, 'C', 0),
                            "winning_trades": getattr(p_data, 'W', 0),
                            "losing_trades": getattr(p_data, 'L', 0),
                            "win_rate": getattr(p_data, 'WR', 0.0),
                            "profit_factor": getattr(p_data, 'PF', 0.0),
                            "roi_percentage": getattr(p_data, 'ROE', 0.0),
                            "max_drawdown": getattr(p_data, 'MDD', 0.0),
                            "sharpe_ratio": getattr(p_data, 'SR', 0.0),
                            "total_profit": getattr(p_data, 'TP', 0.0),
                            "total_loss": getattr(p_data, 'TL', 0.0),
                            "average_win": getattr(p_data, 'AW', 0.0),
                            "average_loss": getattr(p_data, 'AL', 0.0),
                            "largest_win": getattr(p_data, 'LW', 0.0),
                            "largest_loss": getattr(p_data, 'LL', 0.0)
                        })
                        break  # Use first report

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {e}")
            raise AnalysisError(f"Failed to calculate metrics for backtest {backtest_id}: {e}") from e

    async def generate_analysis_report(
        self,
        lab_ids: List[str],
        report_type: str = "comprehensive",
        top_count: int = 10,
        min_win_rate: float = 0.3,
        min_trades: int = 5,
        sort_by: str = "roe"
    ) -> AnalysisReport:
        """
        Generate comprehensive analysis report for multiple labs.

        Args:
            lab_ids: List of lab IDs to include in report
            report_type: Type of report to generate
            top_count: Number of top performers per lab
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            sort_by: Field to sort by

        Returns:
            AnalysisReport with comprehensive analysis

        Raises:
            AnalysisError: If report generation fails
        """
        try:
            self.logger.info(f"Generating {report_type} analysis report for {len(lab_ids)} labs")

            # Analyze all labs
            analysis_results = await self.analyze_multiple_labs(
                lab_ids=lab_ids,
                top_count=top_count,
                min_win_rate=min_win_rate,
                min_trades=min_trades,
                sort_by=sort_by
            )

            # Calculate summary statistics
            summary_stats = self._calculate_summary_statistics(analysis_results)

            # Generate recommendations
            recommendations = self._generate_recommendations(analysis_results, summary_stats)

            # Create report
            report = AnalysisReport(
                report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_type=report_type,
                lab_ids=lab_ids,
                analysis_results=analysis_results,
                summary_statistics=summary_stats,
                recommendations=recommendations,
                generated_timestamp=datetime.now().isoformat()
            )

            self.logger.info(f"✅ Analysis report generated: {report.report_id}")
            return report

        except Exception as e:
            self.logger.error(f"Failed to generate analysis report: {e}")
            raise AnalysisError(f"Failed to generate analysis report: {e}") from e

    def _calculate_summary_statistics(
        self, 
        analysis_results: List[LabAnalysisResult]
    ) -> Dict[str, Any]:
        """Calculate summary statistics from analysis results"""
        if not analysis_results:
            return {}

        total_labs = len(analysis_results)
        total_backtests = sum(result.total_backtests for result in analysis_results)
        
        # Calculate averages
        avg_roi = sum(result.average_roi for result in analysis_results) / total_labs
        best_roi = max(result.best_roi for result in analysis_results)
        avg_win_rate = sum(result.average_win_rate for result in analysis_results) / total_labs
        best_win_rate = max(result.best_win_rate for result in analysis_results)

        # Count by market
        market_counts = {}
        script_counts = {}
        for result in analysis_results:
            market_counts[result.market_tag] = market_counts.get(result.market_tag, 0) + 1
            script_counts[result.script_name] = script_counts.get(result.script_name, 0) + 1

        return {
            "total_labs": total_labs,
            "total_backtests": total_backtests,
            "average_roi": avg_roi,
            "best_roi": best_roi,
            "average_win_rate": avg_win_rate,
            "best_win_rate": best_win_rate,
            "market_distribution": market_counts,
            "script_distribution": script_counts,
            "labs_with_data": len([r for r in analysis_results if r.total_backtests > 0]),
            "labs_without_data": len([r for r in analysis_results if r.total_backtests == 0])
        }

    def _generate_recommendations(
        self, 
        analysis_results: List[LabAnalysisResult],
        summary_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []

        # Check for labs without data
        if summary_stats.get("labs_without_data", 0) > 0:
            recommendations.append(f"{summary_stats['labs_without_data']} labs have no backtest data - consider executing them")

        # Check for low performance
        if summary_stats.get("average_roi", 0) < 10:
            recommendations.append("Overall ROI is low - consider reviewing strategy parameters")

        # Check for low win rates
        if summary_stats.get("average_win_rate", 0) < 0.4:
            recommendations.append("Average win rate is low - consider strategy optimization")

        # Check for market concentration
        market_dist = summary_stats.get("market_distribution", {})
        if len(market_dist) == 1:
            recommendations.append("All labs use the same market - consider diversifying across markets")

        # Check for script concentration
        script_dist = summary_stats.get("script_distribution", {})
        if len(script_dist) == 1:
            recommendations.append("All labs use the same script - consider testing different strategies")

        return recommendations

    # Bot Recommendation Generation

    async def generate_bot_recommendations(
        self,
        lab_ids: List[str],
        top_count: int = 5,
        min_win_rate: float = 0.6,
        min_trades: int = 10,
        min_roi: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Generate bot creation recommendations from lab analysis.

        Args:
            lab_ids: List of lab IDs to analyze
            top_count: Number of top backtests per lab
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            min_roi: Minimum ROI threshold

        Returns:
            List of bot recommendation dictionaries

        Raises:
            AnalysisError: If recommendation generation fails
        """
        try:
            self.logger.info(f"Generating bot recommendations from {len(lab_ids)} labs")

            # Analyze labs
            analysis_results = await self.analyze_multiple_labs(
                lab_ids=lab_ids,
                top_count=top_count,
                min_win_rate=min_win_rate,
                min_trades=min_trades,
                sort_by="roi"
            )

            # Generate recommendations
            recommendations = []
            for result in analysis_results:
                if not result.success or result.total_backtests == 0:
                    continue

                for performance in result.top_performers:
                    # Apply additional filters
                    if (performance.roi_percentage >= min_roi and 
                        performance.win_rate >= min_win_rate and 
                        performance.total_trades >= min_trades and
                        validate_drawdown_requirement(performance.max_drawdown, self.config)):  # CRITICAL: Use configuration validation
                        
                        recommendation = {
                            "lab_id": result.lab_id,
                            "lab_name": result.lab_name,
                            "backtest_id": performance.backtest_id,
                            "script_name": result.script_name,
                            "market_tag": result.market_tag,
                            "roi_percentage": performance.roi_percentage,
                            "win_rate": performance.win_rate,
                            "total_trades": performance.total_trades,
                            "max_drawdown": performance.max_drawdown,
                            "realized_profits_usdt": performance.realized_profits_usdt,
                            "recommendation_score": self._calculate_recommendation_score(performance),
                            "recommended_trade_amount": 2000.0,  # Standard amount
                            "recommended_leverage": 20.0,  # Standard leverage
                            "generated_timestamp": datetime.now().isoformat()
                        }
                        recommendations.append(recommendation)

            # Sort by recommendation score
            recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

            self.logger.info(f"Generated {len(recommendations)} bot recommendations")
            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to generate bot recommendations: {e}")
            raise AnalysisError(f"Failed to generate bot recommendations: {e}") from e

    def _calculate_recommendation_score(self, performance: BacktestPerformance) -> float:
        """Calculate recommendation score for a backtest performance"""
        try:
            # CRITICAL: Validate drawdown requirements using configuration
            if not validate_drawdown_requirement(performance.max_drawdown, self.config):
                self.logger.warning(f"Rejecting strategy due to drawdown policy violation: {performance.max_drawdown}")
                return 0.0
            
            # Weighted scoring system using configuration weights
            roi_score = min(performance.roi_percentage / 100.0, 1.0) * self.config.roi_weight
            win_rate_score = performance.win_rate * self.config.win_rate_weight
            trades_score = min(performance.total_trades / 100.0, 1.0) * self.config.trades_weight
            
            # Drawdown score using configuration
            drawdown_score = get_drawdown_score(performance.max_drawdown, self.drawdown_policy) * self.config.drawdown_weight

            total_score = roi_score + win_rate_score + trades_score + drawdown_score
            return min(total_score, 1.0)  # Cap at 1.0

        except Exception:
            return 0.0

    # Utility Methods

    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive analysis statistics.

        Returns:
            Dictionary with analysis statistics

        Raises:
            AnalysisError: If statistics retrieval fails
        """
        try:
            self.logger.info("Getting analysis statistics")

            # Get all labs
            all_labs = await self.lab_api.get_labs()
            
            stats = {
                "total_labs": len(all_labs),
                "completed_labs": 0,
                "running_labs": 0,
                "failed_labs": 0,
                "labs_with_backtests": 0,
                "total_backtests": 0,
                "statistics_timestamp": datetime.now().isoformat()
            }

            for lab in all_labs:
                # Count by status
                if hasattr(lab, 'status'):
                    if lab.status.value == 3:  # COMPLETED
                        stats["completed_labs"] += 1
                    elif lab.status.value == 2:  # RUNNING
                        stats["running_labs"] += 1
                    elif lab.status.value == 4:  # FAILED
                        stats["failed_labs"] += 1

                # Count backtests
                try:
                    backtests = await self.backtest_api.get_backtest_result(lab.lab_id, 0, 100)
                    backtest_count = len(backtests.items)
                    stats["total_backtests"] += backtest_count
                    if backtest_count > 0:
                        stats["labs_with_backtests"] += 1
                except Exception:
                    pass  # Skip labs with errors

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get analysis statistics: {e}")
            raise AnalysisError(f"Failed to get analysis statistics: {e}") from e

    # Advanced Analysis Methods (from v1 CLI)

    async def analyze_lab_manual(self, lab_id: str, top_count: int = 10) -> List[BacktestPerformance]:
        """
        Manual analysis that properly extracts data from cached files and CSV reports
        
        Based on the excellent v1 implementation from analyze_from_cache.py
        
        Args:
            lab_id: Lab ID to analyze
            top_count: Number of top performers to return
            
        Returns:
            List of BacktestPerformance objects
        """
        try:
            self.logger.info(f"🔍 Analyzing lab manually: {lab_id[:8]}...")
            
            # Get backtest results
            backtest_results = await self.backtest_api.get_backtest_result(lab_id, 0, 1000)
            
            if not backtest_results.items:
                self.logger.warning(f"⚠️ No backtests found for {lab_id[:8]}")
                return []
            
            performances = []
            
            for backtest in backtest_results.items:
                try:
                    # CRITICAL: Reject any strategy with negative drawdown
                    if backtest.max_drawdown != 0.0:
                        self.logger.debug(f"Rejecting backtest {backtest.backtest_id} due to non-zero drawdown: {backtest.max_drawdown}")
                        continue
                    
                    # Extract performance data
                    performance = BacktestPerformance(
                        backtest_id=backtest.backtest_id,
                        lab_id=lab_id,
                        generation_idx=backtest.generation_idx or 0,
                        population_idx=backtest.population_idx or 0,
                        roi_percentage=backtest.roi_percentage,
                        win_rate=backtest.win_rate,
                        total_trades=backtest.total_trades,
                        max_drawdown=backtest.max_drawdown,
                        realized_profits_usdt=backtest.realized_profits_usdt,
                        starting_balance=10000.0,  # Default starting balance
                        final_balance=10000.0 + backtest.realized_profits_usdt,
                        peak_balance=10000.0 + backtest.realized_profits_usdt,
                        script_name=backtest.script_name or "Unknown",
                        market_tag=backtest.market_tag or "Unknown"
                    )
                    performances.append(performance)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error processing backtest {backtest.backtest_id[:8]}: {e}")
                    continue
            
            # Sort by ROI and return top performers
            performances.sort(key=lambda x: x.roi_percentage, reverse=True)
            
            self.logger.info(f"✅ Found {len(performances)} backtests for {lab_id[:8]}")
            return performances[:top_count]
            
        except Exception as e:
            self.logger.error(f"❌ Error in manual analysis for {lab_id[:8]}: {e}")
            raise AnalysisError(f"Manual analysis failed for lab {lab_id}: {e}") from e

    async def calculate_advanced_metrics(self, backtest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate advanced metrics for a backtest
        
        Based on the excellent v1 implementation from interactive_analyzer.py
        
        Args:
            backtest_data: Raw backtest data
            
        Returns:
            Dictionary with advanced metrics
        """
        try:
            # Extract backtest summary
            summary = self.data_extractor.extract_backtest_summary(backtest_data)
            if not summary:
                return {}
            
            # Calculate metrics
            metrics = compute_metrics(summary)
            
            # Calculate additional metrics
            roe = (summary.net_profit / max(summary.starting_balance, 1)) * 100
            dd_usdt = summary.starting_balance - (summary.final_balance - summary.net_profit)
            dd_percentage = (dd_usdt / summary.starting_balance) * 100
            
            # Risk metrics
            risk_score = calculate_risk_score(metrics, backtest_data)
            stability_score = calculate_stability_score(metrics)
            
            return {
                "roe_percentage": roe,
                "dd_usdt": dd_usdt,
                "dd_percentage": dd_percentage,
                "risk_score": risk_score,
                "stability_score": stability_score,
                "advanced_metrics": {
                    "sharpe_ratio": metrics.sharpe,
                    "sortino_ratio": metrics.sortino,
                    "profit_factor": metrics.profit_factor,
                    "expectancy": metrics.expectancy,
                    "volatility": metrics.volatility,
                    "max_drawdown_pct": metrics.max_drawdown_pct,
                    "avg_trade_duration": metrics.avg_trade_duration_seconds,
                    "exposure_ratio": metrics.exposure_seconds / (365 * 24 * 3600) if metrics.exposure_seconds else 0
                }
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not calculate advanced metrics: {e}")
            return {}

    async def generate_lab_analysis_reports(
        self, 
        lab_results: List[LabAnalysisResult], 
        criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate lab analysis reports with filtering
        
        Based on the excellent v1 implementation from analyze_from_cache.py
        
        Args:
            lab_results: List of lab analysis results
            criteria: Filtering criteria
            
        Returns:
            Dictionary with filtered reports
        """
        if criteria is None:
            criteria = {
                'min_roe': 0,
                'max_roe': None,
                'min_winrate': 30,  # More realistic for actual data
                'max_winrate': None,
                'min_trades': 5,    # Much more realistic for actual data
                'max_trades': None
            }
        
        reports = {}
        
        for lab_result in lab_results:
            lab_id = lab_result.lab_id
            
            # Filter backtests by criteria
            qualifying_bots = []
            for backtest in lab_result.top_performers:
                # CRITICAL: Validate drawdown requirements using configuration
                if not validate_drawdown_requirement(backtest.max_drawdown, self.config):
                    self.logger.debug(f"Rejecting backtest {backtest.backtest_id} due to drawdown policy violation: {backtest.max_drawdown}")
                    continue
                
                # Calculate ROE (Return on Equity)
                roe = (backtest.realized_profits_usdt / max(backtest.starting_balance, 1)) * 100
                win_rate_pct = backtest.win_rate * 100
                
                # Apply filters
                if criteria['min_roe'] is not None and roe < criteria['min_roe']:
                    continue
                if criteria['max_roe'] is not None and roe > criteria['max_roe']:
                    continue
                if criteria['min_winrate'] is not None and win_rate_pct < criteria['min_winrate']:
                    continue
                if criteria['max_winrate'] is not None and win_rate_pct > criteria['max_winrate']:
                    continue
                if criteria['min_trades'] is not None and backtest.total_trades < criteria['min_trades']:
                    continue
                if criteria['max_trades'] is not None and backtest.total_trades > criteria['max_trades']:
                    continue
                
                qualifying_bots.append(backtest)
            
            if qualifying_bots:
                reports[lab_id] = {
                    'lab_name': lab_result.lab_name,
                    'script_name': lab_result.script_name,
                    'market_tag': lab_result.market_tag,
                    'total_backtests': lab_result.total_backtests,
                    'qualifying_bots': len(qualifying_bots),
                    'top_performers': qualifying_bots,
                    'average_roi': lab_result.average_roi,
                    'best_roi': lab_result.best_roi,
                    'average_win_rate': lab_result.average_win_rate,
                    'best_win_rate': lab_result.best_win_rate
                }
        
        return reports

    async def analyze_data_distribution(self, lab_results: List[LabAnalysisResult]) -> Dict[str, Any]:
        """
        Analyze data distribution across labs
        
        Based on the excellent v1 implementation from analyze_from_cache.py
        
        Args:
            lab_results: List of lab analysis results
            
        Returns:
            Dictionary with distribution analysis
        """
        try:
            all_rois = []
            all_win_rates = []
            all_trades = []
            all_drawdowns = []
            
            for lab_result in lab_results:
                for backtest in lab_result.top_performers:
                    all_rois.append(backtest.roi_percentage)
                    all_win_rates.append(backtest.win_rate * 100)
                    all_trades.append(backtest.total_trades)
                    all_drawdowns.append(backtest.max_drawdown)
            
            if not all_rois:
                return {"error": "No data available for distribution analysis"}
            
            # Calculate statistics
            distribution = {
                "total_backtests": len(all_rois),
                "roi_distribution": {
                    "min": min(all_rois),
                    "max": max(all_rois),
                    "avg": sum(all_rois) / len(all_rois),
                    "median": sorted(all_rois)[len(all_rois) // 2]
                },
                "win_rate_distribution": {
                    "min": min(all_win_rates),
                    "max": max(all_win_rates),
                    "avg": sum(all_win_rates) / len(all_win_rates),
                    "median": sorted(all_win_rates)[len(all_win_rates) // 2]
                },
                "trades_distribution": {
                    "min": min(all_trades),
                    "max": max(all_trades),
                    "avg": sum(all_trades) / len(all_trades),
                    "median": sorted(all_trades)[len(all_trades) // 2]
                },
                "drawdown_distribution": {
                    "min": min(all_drawdowns),
                    "max": max(all_drawdowns),
                    "avg": sum(all_drawdowns) / len(all_drawdowns),
                    "median": sorted(all_drawdowns)[len(all_drawdowns) // 2]
                }
            }
            
            return distribution
            
        except Exception as e:
            self.logger.error(f"Error analyzing data distribution: {e}")
            return {"error": f"Distribution analysis failed: {e}"}