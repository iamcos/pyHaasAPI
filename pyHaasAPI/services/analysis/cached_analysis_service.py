"""
Cached Analysis Service for pyHaasAPI v2

This service uses the existing cached backtest files instead of trying to fetch from the API.
It reads the 23,980+ cached backtest files and performs analysis on them.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from ...core.logging import get_logger
from ...models.backtest import BacktestResult, BacktestRuntimeData
from ...analysis.metrics import RunMetrics, compute_metrics, calculate_risk_score, calculate_stability_score
from ...analysis.extraction import BacktestDataExtractor, BacktestSummary, TradeData

logger = get_logger("cached_analysis_service")


@dataclass
class CachedBacktestPerformance:
    """Data class for cached backtest performance metrics"""
    backtest_id: str
    lab_id: str
    generation_idx: int
    population_idx: int
    roi_percentage: float  # Actually ROE (Return on Equity) calculated from trades
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    starting_balance: float
    final_balance: float
    peak_balance: float
    script_name: str
    market_tag: str
    file_path: str
    # Additional financial metrics
    profit_factor: float = 0.0  # Gross profit / Gross loss
    sharpe_ratio: float = 0.0  # Risk-adjusted return
    average_profit_per_trade: float = 0.0  # Average profit per trade
    average_loss_per_trade: float = 0.0  # Average loss per trade
    largest_win: float = 0.0  # Largest winning trade
    largest_loss: float = 0.0  # Largest losing trade
    consecutive_wins: int = 0  # Maximum consecutive wins
    consecutive_losses: int = 0  # Maximum consecutive losses
    recovery_factor: float = 0.0  # Net profit / Max drawdown


@dataclass
class CachedLabAnalysisResult:
    """Result of comprehensive lab analysis using cached data"""
    lab_id: str
    lab_name: str
    script_name: str
    market_tag: str
    total_backtests: int
    top_performers: List[CachedBacktestPerformance]
    average_roi: float
    best_roi: float
    average_win_rate: float
    best_win_rate: float
    analysis_timestamp: str
    success: bool
    error_message: Optional[str] = None


class CachedAnalysisService:
    """
    Analysis Service that uses cached backtest files instead of API calls.
    
    This service reads the 23,980+ cached backtest files and performs analysis on them.
    It's much more efficient than trying to fetch from the API.
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.backtests_dir = cache_dir / "backtests"
        self.logger = get_logger("cached_analysis_service")
        self.data_extractor = BacktestDataExtractor()
        
        # Ensure backtests directory exists
        if not self.backtests_dir.exists():
            self.logger.warning(f"Backtests directory not found: {self.backtests_dir}")
            self.backtests_dir.mkdir(parents=True, exist_ok=True)

    def get_cached_backtest_files_for_lab(self, lab_id: str) -> List[Path]:
        """Get all cached backtest files for a specific lab"""
        try:
            # Find all files that start with the lab_id
            pattern = f"{lab_id}_*.json"
            files = list(self.backtests_dir.glob(pattern))
            self.logger.info(f"Found {len(files)} cached backtest files for lab {lab_id[:8]}")
            return files
        except Exception as e:
            self.logger.error(f"Failed to get cached files for lab {lab_id[:8]}: {e}")
            return []

    def load_backtest_from_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single backtest file and return its data"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            self.logger.warning(f"Failed to load backtest file {file_path.name}: {e}")
            return None

    def extract_performance_from_cached_data(self, data: Dict[str, Any], file_path: Path) -> Optional[CachedBacktestPerformance]:
        """Extract performance metrics from cached backtest data"""
        try:
            # Extract basic info from top-level fields
            backtest_id = data.get('LogId', '')
            lab_id = data.get('BotId', '')
            script_name = data.get('ScriptName', '')
            market_tag = data.get('PriceMarket', '')
            
            # Get the first (and usually only) report
            reports = data.get('Reports', {})
            if not reports:
                return None
            
            report_key = list(reports.keys())[0]
            report = reports[report_key]
            
            # Extract performance data from PR (Performance Report)
            pr = report.get('PR', {})
            starting_balance = pr.get('SB', 1000.0)
            realized_profits = pr.get('RP', 0.0)  # Realized Profits from trades
            final_balance = pr.get('FPC', {}).get('USDT', starting_balance) if pr.get('FPC') else starting_balance
            
            # Calculate ROE (Return on Equity) from actual trade data
            roe_percentage = (realized_profits / starting_balance * 100) if starting_balance > 0 else 0.0
            
            # Extract trade data from P (Positions) - this has the actual trade count
            positions = report.get('P', {})
            total_trades = int(positions.get('C', 0))  # Total trades from positions
            winning_trades = int(positions.get('W', 0))  # Winning trades from positions
            
            # Calculate win rate from actual trade counts
            if total_trades > 0:
                win_rate = (winning_trades / total_trades) * 100
            else:
                win_rate = 0.0
            
            # Calculate max drawdown from RPH (Realized P&L History)
            rph = pr.get('RPH', [])
            max_drawdown = 0.0
            peak_balance = starting_balance
            if rph:
                peak = starting_balance
                max_dd = 0.0
                for pnl in rph:
                    current_balance = starting_balance + pnl
                    if current_balance > peak:
                        peak = current_balance
                    drawdown = (peak - current_balance) / peak if peak > 0 else 0.0
                    max_dd = max(max_dd, drawdown)
                max_drawdown = max_dd * 100  # Convert to percentage
                peak_balance = peak
            
            # Calculate additional financial metrics from trade data
            additional_metrics = self._calculate_additional_metrics(rph, total_trades, winning_trades, realized_profits, max_drawdown)
            
            # Extract generation and population from file name or data
            generation_idx = 0
            population_idx = 0
            
            return CachedBacktestPerformance(
                backtest_id=backtest_id,
                lab_id=lab_id,
                generation_idx=generation_idx,
                population_idx=population_idx,
                roi_percentage=roe_percentage,  # Now using ROE calculated from trades
                win_rate=win_rate,
                total_trades=total_trades,
                max_drawdown=max_drawdown,
                realized_profits_usdt=realized_profits,  # Use actual realized profits from trades
                starting_balance=starting_balance,
                final_balance=final_balance,
                peak_balance=peak_balance,
                script_name=script_name,
                market_tag=market_tag,
                file_path=str(file_path),
                # Additional financial metrics
                profit_factor=additional_metrics['profit_factor'],
                sharpe_ratio=additional_metrics['sharpe_ratio'],
                average_profit_per_trade=additional_metrics['average_profit_per_trade'],
                average_loss_per_trade=additional_metrics['average_loss_per_trade'],
                largest_win=additional_metrics['largest_win'],
                largest_loss=additional_metrics['largest_loss'],
                consecutive_wins=additional_metrics['consecutive_wins'],
                consecutive_losses=additional_metrics['consecutive_losses'],
                recovery_factor=additional_metrics['recovery_factor']
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to extract performance from {file_path.name}: {e}")
            return None

    def _calculate_additional_metrics(self, rph: List[float], total_trades: int, winning_trades: int, 
                                    realized_profits: float, max_drawdown: float) -> Dict[str, float]:
        """Calculate additional financial metrics from trade data"""
        metrics = {
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'average_profit_per_trade': 0.0,
            'average_loss_per_trade': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'recovery_factor': 0.0
        }
        
        if not rph or total_trades == 0:
            return metrics
        
        # Calculate trade-by-trade P&L from RPH
        trade_pnls = []
        if len(rph) > 1:
            for i in range(1, len(rph)):
                trade_pnl = rph[i] - rph[i-1]
                trade_pnls.append(trade_pnl)
        elif len(rph) == 1:
            trade_pnls = [rph[0]]
        
        if not trade_pnls:
            return metrics
        
        # Separate winning and losing trades
        winning_trade_pnls = [pnl for pnl in trade_pnls if pnl > 0]
        losing_trade_pnls = [pnl for pnl in trade_pnls if pnl < 0]
        
        # Profit Factor: Gross Profit / Gross Loss
        gross_profit = sum(winning_trade_pnls) if winning_trade_pnls else 0.0
        gross_loss = abs(sum(losing_trade_pnls)) if losing_trade_pnls else 0.0
        if gross_loss > 0:
            metrics['profit_factor'] = gross_profit / gross_loss
        
        # Average profit/loss per trade
        if winning_trade_pnls:
            metrics['average_profit_per_trade'] = gross_profit / len(winning_trade_pnls)
        if losing_trade_pnls:
            metrics['average_loss_per_trade'] = gross_loss / len(losing_trade_pnls)
        
        # Largest win/loss
        if winning_trade_pnls:
            metrics['largest_win'] = max(winning_trade_pnls)
        if losing_trade_pnls:
            metrics['largest_loss'] = min(losing_trade_pnls)  # Most negative
        
        # Consecutive wins/losses
        current_streak = 0
        max_wins = 0
        max_losses = 0
        
        for pnl in trade_pnls:
            if pnl > 0:  # Winning trade
                if current_streak >= 0:  # Continuing win streak
                    current_streak += 1
                else:  # Starting new win streak
                    max_losses = max(max_losses, abs(current_streak))
                    current_streak = 1
            else:  # Losing trade
                if current_streak <= 0:  # Continuing loss streak
                    current_streak -= 1
                else:  # Starting new loss streak
                    max_wins = max(max_wins, current_streak)
                    current_streak = -1
        
        # Final streak
        if current_streak > 0:
            max_wins = max(max_wins, current_streak)
        else:
            max_losses = max(max_losses, abs(current_streak))
        
        metrics['consecutive_wins'] = max_wins
        metrics['consecutive_losses'] = max_losses
        
        # Sharpe Ratio (simplified - using standard deviation of returns)
        if len(trade_pnls) > 1:
            import statistics
            mean_return = statistics.mean(trade_pnls)
            std_return = statistics.stdev(trade_pnls)
            if std_return > 0:
                metrics['sharpe_ratio'] = mean_return / std_return
        
        # Recovery Factor: Net Profit / Max Drawdown
        if max_drawdown > 0:
            metrics['recovery_factor'] = realized_profits / (max_drawdown / 100 * 1000)  # Convert percentage to absolute
        
        return metrics

    async def analyze_lab_from_cache(
        self,
        lab_id: str,
        lab_name: str = "",
        script_name: str = "",
        market_tag: str = "",
        top_count: int = 10,
        min_win_rate: float = 0.55,  # Standardized: 55%+ win rate
        min_trades: int = 5,
        max_drawdown: float = 0.0,   # Standardized: Zero drawdown only
        sort_by: str = "roi"
    ) -> CachedLabAnalysisResult:
        """
        Analyze a lab using cached backtest files.
        
        Args:
            lab_id: Lab ID to analyze
            lab_name: Lab name (for display)
            script_name: Script name (for display)
            market_tag: Market tag (for display)
            top_count: Number of top performers to return
            min_win_rate: Minimum win rate filter
            min_trades: Minimum trades filter
            sort_by: Sort field (roi, win_rate, etc.)
            
        Returns:
            CachedLabAnalysisResult with analysis results
        """
        try:
            self.logger.info(f"🔍 Analyzing lab from cache: {lab_id[:8]}...")
            
            # Get cached files for this lab
            cached_files = self.get_cached_backtest_files_for_lab(lab_id)
            
            if not cached_files:
                return CachedLabAnalysisResult(
                    lab_id=lab_id,
                    lab_name=lab_name,
                    script_name=script_name,
                    market_tag=market_tag,
                    total_backtests=0,
                    top_performers=[],
                    average_roi=0.0,
                    best_roi=0.0,
                    average_win_rate=0.0,
                    best_win_rate=0.0,
                    analysis_timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message="No cached backtest files found"
                )
            
            # Load and analyze all backtests
            performances = []
            for file_path in cached_files:
                data = self.load_backtest_from_file(file_path)
                if data:
                    performance = self.extract_performance_from_cached_data(data, file_path)
                    if performance:
                        # Apply filters
                        if (performance.win_rate >= min_win_rate and 
                            performance.total_trades >= min_trades and
                            performance.max_drawdown <= max_drawdown and  # Configurable drawdown limit
                            performance.realized_profits_usdt >= 0):  # Never negative
                            performances.append(performance)
            
            if not performances:
                return CachedLabAnalysisResult(
                    lab_id=lab_id,
                    lab_name=lab_name,
                    script_name=script_name,
                    market_tag=market_tag,
                    total_backtests=len(cached_files),
                    top_performers=[],
                    average_roi=0.0,
                    best_roi=0.0,
                    average_win_rate=0.0,
                    best_win_rate=0.0,
                    analysis_timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message=f"No backtests passed filters (min_win_rate={min_win_rate}, min_trades={min_trades})"
                )
            
            # Sort by specified field with multi-criteria sorting
            if sort_by == "roi":
                performances.sort(key=lambda x: (x.roi_percentage, x.win_rate, x.profit_factor, -x.max_drawdown), reverse=True)
            elif sort_by == "win_rate":
                performances.sort(key=lambda x: (x.win_rate, x.roi_percentage, x.profit_factor, -x.max_drawdown), reverse=True)
            elif sort_by == "total_trades":
                performances.sort(key=lambda x: (x.total_trades, x.win_rate, x.roi_percentage, x.profit_factor), reverse=True)
            elif sort_by == "profit_factor":
                performances.sort(key=lambda x: (x.profit_factor, x.win_rate, x.roi_percentage, -x.max_drawdown), reverse=True)
            elif sort_by == "sharpe_ratio":
                performances.sort(key=lambda x: (x.sharpe_ratio, x.win_rate, x.roi_percentage, -x.max_drawdown), reverse=True)
            elif sort_by == "recovery_factor":
                performances.sort(key=lambda x: (x.recovery_factor, x.win_rate, x.roi_percentage, -x.max_drawdown), reverse=True)
            else:
                # Default: prioritize win rate, then ROE, then profit factor, then low drawdown
                performances.sort(key=lambda x: (x.win_rate, x.roi_percentage, x.profit_factor, -x.max_drawdown), reverse=True)
            
            # Get top performers
            top_performers = performances[:top_count]
            
            # Calculate summary statistics
            rois = [p.roi_percentage for p in performances]
            win_rates = [p.win_rate for p in performances]
            
            average_roi = sum(rois) / len(rois) if rois else 0.0
            best_roi = max(rois) if rois else 0.0
            average_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.0
            best_win_rate = max(win_rates) if win_rates else 0.0
            
            self.logger.info(f"✅ Lab analysis complete: {len(performances)} backtests analyzed, {len(top_performers)} top performers")
            
            return CachedLabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_name,
                script_name=script_name,
                market_tag=market_tag,
                total_backtests=len(performances),
                top_performers=top_performers,
                average_roi=average_roi,
                best_roi=best_roi,
                average_win_rate=average_win_rate,
                best_win_rate=best_win_rate,
                analysis_timestamp=datetime.now().isoformat(),
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze lab {lab_id[:8]}: {e}")
            return CachedLabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_name,
                script_name=script_name,
                market_tag=market_tag,
                total_backtests=0,
                top_performers=[],
                average_roi=0.0,
                best_roi=0.0,
                average_win_rate=0.0,
                best_win_rate=0.0,
                analysis_timestamp=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            )

    async def analyze_all_labs_from_cache(
        self,
        lab_ids: List[str],
        lab_info: Dict[str, Dict[str, str]] = None,
        top_count: int = 10,
        min_win_rate: float = 0.3,
        min_trades: int = 5,
        sort_by: str = "roi"
    ) -> Dict[str, CachedLabAnalysisResult]:
        """
        Analyze all labs using cached backtest files.
        
        Args:
            lab_ids: List of lab IDs to analyze
            lab_info: Optional dict mapping lab_id to {name, script_name, market_tag}
            top_count: Number of top performers to return per lab
            min_win_rate: Minimum win rate filter
            min_trades: Minimum trades filter
            sort_by: Sort field (roi, win_rate, etc.)
            
        Returns:
            Dict mapping lab_id to CachedLabAnalysisResult
        """
        results = {}
        
        for lab_id in lab_ids:
            # Get lab info if provided
            lab_name = ""
            script_name = ""
            market_tag = ""
            if lab_info and lab_id in lab_info:
                lab_name = lab_info[lab_id].get("name", "")
                script_name = lab_info[lab_id].get("script_name", "")
                market_tag = lab_info[lab_id].get("market_tag", "")
            
            # Analyze this lab
            result = await self.analyze_lab_from_cache(
                lab_id=lab_id,
                lab_name=lab_name,
                script_name=script_name,
                market_tag=market_tag,
                top_count=top_count,
                min_win_rate=min_win_rate,
                min_trades=min_trades,
                sort_by=sort_by
            )
            
            results[lab_id] = result
        
        return results

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get statistics about the cached backtest files"""
        try:
            all_files = list(self.backtests_dir.glob("*.json"))
            total_files = len(all_files)
            
            # Group by lab ID
            lab_counts = {}
            for file_path in all_files:
                lab_id = file_path.name.split('_')[0]
                lab_counts[lab_id] = lab_counts.get(lab_id, 0) + 1
            
            return {
                "total_backtest_files": total_files,
                "unique_labs": len(lab_counts),
                "lab_counts": lab_counts,
                "cache_directory": str(self.backtests_dir)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return {"error": str(e)}
