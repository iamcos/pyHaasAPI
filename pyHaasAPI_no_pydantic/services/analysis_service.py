"""
Analysis Service for pyHaasAPI_no_pydantic

Provides comprehensive analysis functionality for lab operations,
including performance evaluation, reporting, and recommendations.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..api.lab_api import LabAPI
from ..models.lab import LabDetails, LabRecord, LabConfig
from ..api.exceptions import LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analysis operations"""
    min_win_rate: float = 0.3
    min_trades: int = 5
    top_count: int = 10
    sort_by: str = "roe"  # roi, roe, winrate, profit, trades
    include_recommendations: bool = True
    generate_reports: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis"""
    roi: float
    roe: float
    win_rate: float
    total_trades: int
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    avg_trade_duration: float
    best_trade: float
    worst_trade: float


@dataclass
class AnalysisReport:
    """Analysis report with results and recommendations"""
    lab_id: str
    lab_name: str
    analysis_timestamp: datetime
    performance_metrics: PerformanceMetrics
    recommendations: List[str]
    risk_assessment: str
    confidence_score: float


class AnalysisService:
    """
    Analysis Service for lab operations
    
    Provides comprehensive analysis functionality including performance
    evaluation, reporting, and recommendations for lab operations.
    """
    
    def __init__(self, lab_api: LabAPI):
        self.lab_api = lab_api
        self.logger = logger
    
    async def analyze_lab_performance(
        self,
        lab_id: str,
        config: Optional[AnalysisConfig] = None
    ) -> AnalysisReport:
        """
        Analyze lab performance with comprehensive metrics
        
        Args:
            lab_id: ID of the lab to analyze
            config: Optional analysis configuration
            
        Returns:
            AnalysisReport with performance metrics and recommendations
            
        Raises:
            LabAPIError: If analysis fails
        """
        try:
            self.logger.info(f"Analyzing lab performance for lab: {lab_id}")
            
            # Use default config if not provided
            if config is None:
                config = AnalysisConfig()
            
            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Perform analysis (this would need to be implemented based on actual API)
            # For now, return a placeholder structure
            performance_metrics = PerformanceMetrics(
                roi=0.0,
                roe=0.0,
                win_rate=0.0,
                total_trades=0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                avg_trade_duration=0.0,
                best_trade=0.0,
                worst_trade=0.0
            )
            
            recommendations = []
            if config.include_recommendations:
                recommendations = await self._generate_recommendations(performance_metrics)
            
            risk_assessment = await self._assess_risk(performance_metrics)
            confidence_score = await self._calculate_confidence(performance_metrics)
            
            report = AnalysisReport(
                lab_id=lab_id,
                lab_name=lab_details.name,
                analysis_timestamp=datetime.now(),
                performance_metrics=performance_metrics,
                recommendations=recommendations,
                risk_assessment=risk_assessment,
                confidence_score=confidence_score
            )
            
            self.logger.info(f"Lab performance analysis completed for lab {lab_id}")
            return report
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze lab performance: {e}")
            raise LabAPIError(f"Failed to analyze lab performance: {e}")
    
    async def compare_labs(
        self,
        lab_ids: List[str],
        config: Optional[AnalysisConfig] = None
    ) -> Dict[str, AnalysisReport]:
        """
        Compare multiple labs
        
        Args:
            lab_ids: List of lab IDs to compare
            config: Optional analysis configuration
            
        Returns:
            Dictionary mapping lab IDs to analysis reports
            
        Raises:
            LabAPIError: If comparison fails
        """
        try:
            self.logger.info(f"Comparing labs: {lab_ids}")
            
            # Use default config if not provided
            if config is None:
                config = AnalysisConfig()
            
            # Analyze each lab
            reports = {}
            for lab_id in lab_ids:
                try:
                    report = await self.analyze_lab_performance(lab_id, config)
                    reports[lab_id] = report
                except Exception as e:
                    self.logger.warning(f"Failed to analyze lab {lab_id}: {e}")
                    continue
            
            self.logger.info(f"Lab comparison completed for {len(reports)} labs")
            return reports
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to compare labs: {e}")
            raise LabAPIError(f"Failed to compare labs: {e}")
    
    async def find_best_labs(
        self,
        min_win_rate: float = 0.6,
        min_trades: int = 10,
        max_labs: int = 10
    ) -> List[AnalysisReport]:
        """
        Find the best performing labs
        
        Args:
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            max_labs: Maximum number of labs to return
            
        Returns:
            List of analysis reports for the best labs
            
        Raises:
            LabAPIError: If search fails
        """
        try:
            self.logger.info(f"Finding best labs with min_win_rate={min_win_rate}, min_trades={min_trades}")
            
            # Get all labs
            all_labs = await self.lab_api.get_labs()
            
            # Filter and analyze labs
            best_reports = []
            for lab in all_labs:
                try:
                    # Quick filter based on basic criteria
                    if lab.backtest_count < min_trades:
                        continue
                    
                    # Analyze lab
                    config = AnalysisConfig(
                        min_win_rate=min_win_rate,
                        min_trades=min_trades,
                        top_count=1
                    )
                    
                    report = await self.analyze_lab_performance(lab.lab_id, config)
                    
                    # Check if lab meets criteria
                    if (report.performance_metrics.win_rate >= min_win_rate and
                        report.performance_metrics.total_trades >= min_trades):
                        best_reports.append(report)
                    
                    # Stop if we have enough labs
                    if len(best_reports) >= max_labs:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Failed to analyze lab {lab.lab_id}: {e}")
                    continue
            
            # Sort by performance
            best_reports.sort(key=lambda x: x.performance_metrics.roe, reverse=True)
            
            self.logger.info(f"Found {len(best_reports)} best labs")
            return best_reports
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to find best labs: {e}")
            raise LabAPIError(f"Failed to find best labs: {e}")
    
    async def generate_analysis_report(
        self,
        lab_ids: Optional[List[str]] = None,
        output_format: str = "json",
        include_charts: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report
        
        Args:
            lab_ids: Optional list of lab IDs to include (if None, includes all labs)
            output_format: Output format (json, csv, html)
            include_charts: Whether to include chart data
            
        Returns:
            Dictionary with analysis report data
            
        Raises:
            LabAPIError: If report generation fails
        """
        try:
            self.logger.info(f"Generating analysis report for labs: {lab_ids or 'all'}")
            
            # Get labs to analyze
            if lab_ids is None:
                all_labs = await self.lab_api.get_labs()
                lab_ids = [lab.lab_id for lab in all_labs]
            
            # Analyze all labs
            reports = {}
            for lab_id in lab_ids:
                try:
                    report = await self.analyze_lab_performance(lab_id)
                    reports[lab_id] = report
                except Exception as e:
                    self.logger.warning(f"Failed to analyze lab {lab_id}: {e}")
                    continue
            
            # Generate report data
            report_data = {
                "generated_at": datetime.now().isoformat(),
                "total_labs": len(reports),
                "labs": reports,
                "summary": await self._generate_summary(reports),
                "recommendations": await self._generate_global_recommendations(reports)
            }
            
            if include_charts:
                report_data["charts"] = await self._generate_chart_data(reports)
            
            self.logger.info(f"Analysis report generated for {len(reports)} labs")
            return report_data
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to generate analysis report: {e}")
            raise LabAPIError(f"Failed to generate analysis report: {e}")
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    async def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate recommendations based on performance metrics"""
        recommendations = []
        
        if metrics.win_rate < 0.5:
            recommendations.append("Consider improving strategy to increase win rate")
        
        if metrics.max_drawdown > 0.2:
            recommendations.append("High drawdown detected - consider risk management improvements")
        
        if metrics.sharpe_ratio < 1.0:
            recommendations.append("Low Sharpe ratio - consider strategy optimization")
        
        if metrics.total_trades < 10:
            recommendations.append("Insufficient trade data - consider longer backtest period")
        
        return recommendations
    
    async def _assess_risk(self, metrics: PerformanceMetrics) -> str:
        """Assess risk level based on performance metrics"""
        risk_score = 0
        
        if metrics.max_drawdown > 0.3:
            risk_score += 3
        elif metrics.max_drawdown > 0.2:
            risk_score += 2
        elif metrics.max_drawdown > 0.1:
            risk_score += 1
        
        if metrics.sharpe_ratio < 0.5:
            risk_score += 2
        elif metrics.sharpe_ratio < 1.0:
            risk_score += 1
        
        if metrics.win_rate < 0.4:
            risk_score += 2
        elif metrics.win_rate < 0.5:
            risk_score += 1
        
        if risk_score >= 5:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _calculate_confidence(self, metrics: PerformanceMetrics) -> float:
        """Calculate confidence score based on performance metrics"""
        confidence = 0.5  # Base confidence
        
        # Adjust based on win rate
        if metrics.win_rate > 0.7:
            confidence += 0.2
        elif metrics.win_rate > 0.6:
            confidence += 0.1
        
        # Adjust based on number of trades
        if metrics.total_trades > 100:
            confidence += 0.2
        elif metrics.total_trades > 50:
            confidence += 0.1
        
        # Adjust based on Sharpe ratio
        if metrics.sharpe_ratio > 2.0:
            confidence += 0.1
        elif metrics.sharpe_ratio > 1.5:
            confidence += 0.05
        
        return min(1.0, max(0.0, confidence))
    
    async def _generate_summary(self, reports: Dict[str, AnalysisReport]) -> Dict[str, Any]:
        """Generate summary statistics for all reports"""
        if not reports:
            return {}
        
        total_labs = len(reports)
        avg_roi = sum(r.performance_metrics.roi for r in reports.values()) / total_labs
        avg_win_rate = sum(r.performance_metrics.win_rate for r in reports.values()) / total_labs
        avg_trades = sum(r.performance_metrics.total_trades for r in reports.values()) / total_labs
        
        best_lab = max(reports.values(), key=lambda x: x.performance_metrics.roe)
        worst_lab = min(reports.values(), key=lambda x: x.performance_metrics.roe)
        
        return {
            "total_labs": total_labs,
            "average_roi": avg_roi,
            "average_win_rate": avg_win_rate,
            "average_trades": avg_trades,
            "best_lab": {
                "lab_id": best_lab.lab_id,
                "lab_name": best_lab.lab_name,
                "roe": best_lab.performance_metrics.roe
            },
            "worst_lab": {
                "lab_id": worst_lab.lab_id,
                "lab_name": worst_lab.lab_name,
                "roe": worst_lab.performance_metrics.roe
            }
        }
    
    async def _generate_global_recommendations(self, reports: Dict[str, AnalysisReport]) -> List[str]:
        """Generate global recommendations based on all reports"""
        recommendations = []
        
        if not reports:
            return recommendations
        
        # Analyze overall performance
        avg_win_rate = sum(r.performance_metrics.win_rate for r in reports.values()) / len(reports)
        avg_roi = sum(r.performance_metrics.roi for r in reports.values()) / len(reports)
        
        if avg_win_rate < 0.5:
            recommendations.append("Overall win rate is low - consider strategy improvements")
        
        if avg_roi < 0.1:
            recommendations.append("Overall ROI is low - consider parameter optimization")
        
        # Check for high-risk labs
        high_risk_labs = [r for r in reports.values() if r.risk_assessment == "HIGH"]
        if len(high_risk_labs) > len(reports) * 0.3:
            recommendations.append("High number of high-risk labs detected - review risk management")
        
        return recommendations
    
    async def _generate_chart_data(self, reports: Dict[str, AnalysisReport]) -> Dict[str, Any]:
        """Generate chart data for visualization"""
        if not reports:
            return {}
        
        # Prepare data for charts
        lab_names = [r.lab_name for r in reports.values()]
        roi_values = [r.performance_metrics.roi for r in reports.values()]
        win_rates = [r.performance_metrics.win_rate for r in reports.values()]
        trade_counts = [r.performance_metrics.total_trades for r in reports.values()]
        
        return {
            "roi_chart": {
                "labels": lab_names,
                "data": roi_values
            },
            "win_rate_chart": {
                "labels": lab_names,
                "data": win_rates
            },
            "trades_chart": {
                "labels": lab_names,
                "data": trade_counts
            }
        }



