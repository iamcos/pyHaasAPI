"""
Cache management for pyHaasAPI analysis

This module provides unified caching functionality for backtest data,
analysis results, and reports.
"""

import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import LabAnalysisResult

logger = logging.getLogger(__name__)


class UnifiedCacheManager:
    """Manages unified caching system for analysis data"""
    
    def __init__(self, base_dir: str = "unified_cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.base_dir / "backtests").mkdir(exist_ok=True)
        (self.base_dir / "reports").mkdir(exist_ok=True)
        (self.base_dir / "logs").mkdir(exist_ok=True)
    
    def get_backtest_cache_path(self, lab_id: str, backtest_id: str) -> Path:
        """Get cache path for backtest data"""
        return self.base_dir / "backtests" / f"{lab_id}_{backtest_id}.json"
    
    def get_report_path(self, lab_id: str, timestamp: str) -> Path:
        """Get report path for lab analysis"""
        return self.base_dir / "reports" / f"lab_analysis_{lab_id}_{timestamp}.csv"
    
    def cache_backtest_data(self, lab_id: str, backtest_id: str, data: Dict[str, Any]) -> None:
        """Cache backtest data"""
        cache_path = self.get_backtest_cache_path(lab_id, backtest_id)
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_backtest_cache(self, lab_id: str, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Load cached backtest data"""
        cache_path = self.get_backtest_cache_path(lab_id, backtest_id)
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_analysis_report(self, result: LabAnalysisResult) -> Path:
        """Save analysis report to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.get_report_path(result.lab_id, timestamp)
        
        with open(report_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Lab ID', 'Lab Name', 'Total Backtests', 'Analyzed Backtests',
                'Backtest ID', 'Generation', 'Population', 'Market', 'Script ID', 'Script Name',
                'Lab ROI %', 'Calculated ROI %', 'ROI Difference %', 'Win Rate %', 'Total Trades', 'Max Drawdown %', 'Realized Profits USDT',
                'PC Value', 'Avg Profit/Trade', 'Profit Factor', 'Sharpe Ratio',
                'Starting Balance USDT', 'Final Balance USDT', 'Peak Balance USDT',
                'Analysis Timestamp'
            ])
            
            # Write data rows
            for backtest in result.top_backtests:
                writer.writerow([
                    result.lab_id, result.lab_name, result.total_backtests, result.analyzed_backtests,
                    backtest.backtest_id, backtest.generation_idx, backtest.population_idx,
                    backtest.market_tag, backtest.script_id, backtest.script_name,
                    backtest.roi_percentage, backtest.calculated_roi_percentage, backtest.roi_difference,
                    backtest.win_rate * 100, backtest.total_trades, backtest.max_drawdown, 
                    backtest.realized_profits_usdt, backtest.pc_value, backtest.avg_profit_per_trade, 
                    backtest.profit_factor, backtest.sharpe_ratio,
                    backtest.starting_balance, backtest.final_balance, backtest.peak_balance,
                    backtest.analysis_timestamp
                ])
        
        return report_path
    
    def save_analysis_result(self, result: LabAnalysisResult) -> Path:
        """Save complete analysis result for later bot creation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_path = self.base_dir / "reports" / f"analysis_result_{result.lab_id}_{timestamp}.json"
        
        # Convert to dict for JSON serialization
        result_dict = {
            "lab_id": result.lab_id,
            "lab_name": result.lab_name,
            "total_backtests": result.total_backtests,
            "analyzed_backtests": result.analyzed_backtests,
            "processing_time": result.processing_time,
            "top_backtests": [
                {
                    "backtest_id": bt.backtest_id,
                    "generation_idx": bt.generation_idx,
                    "population_idx": bt.population_idx,
                    "market_tag": bt.market_tag,
                    "script_id": bt.script_id,
                    "script_name": bt.script_name,
                    "roi_percentage": bt.roi_percentage,
                    "calculated_roi_percentage": bt.calculated_roi_percentage,
                    "roi_difference": bt.roi_difference,
                    "win_rate": bt.win_rate,
                    "total_trades": bt.total_trades,
                    "max_drawdown": bt.max_drawdown,
                    "realized_profits_usdt": bt.realized_profits_usdt,
                    "pc_value": bt.pc_value,
                    "avg_profit_per_trade": bt.avg_profit_per_trade,
                    "profit_factor": bt.profit_factor,
                    "sharpe_ratio": bt.sharpe_ratio,
                    "starting_balance": bt.starting_balance,
                    "final_balance": bt.final_balance,
                    "peak_balance": bt.peak_balance,
                    "analysis_timestamp": bt.analysis_timestamp
                }
                for bt in result.top_backtests
            ],
            "saved_at": datetime.now().isoformat()
        }
        
        with open(result_path, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        return result_path
    
    def load_analysis_result(self, lab_id: str, timestamp: str = None) -> Optional[Dict[str, Any]]:
        """Load saved analysis result"""
        if timestamp:
            result_path = self.base_dir / "reports" / f"analysis_result_{lab_id}_{timestamp}.json"
        else:
            # Find the most recent analysis result for this lab
            pattern = f"analysis_result_{lab_id}_*.json"
            result_files = list(self.base_dir.glob(f"reports/{pattern}"))
            if not result_files:
                return None
            result_path = max(result_files, key=lambda p: p.stat().st_mtime)
        
        if result_path.exists():
            with open(result_path, 'r') as f:
                return json.load(f)
        return None
    
    def list_analysis_results(self, lab_id: str = None) -> List[Dict[str, Any]]:
        """List all saved analysis results"""
        if lab_id:
            pattern = f"analysis_result_{lab_id}_*.json"
        else:
            pattern = "analysis_result_*.json"
        
        result_files = list(self.base_dir.glob(f"reports/{pattern}"))
        results = []
        
        for result_file in result_files:
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    results.append({
                        "file_path": str(result_file),
                        "lab_id": data.get("lab_id"),
                        "lab_name": data.get("lab_name"),
                        "saved_at": data.get("saved_at"),
                        "top_backtests_count": len(data.get("top_backtests", [])),
                        "total_backtests": data.get("total_backtests", 0)
                    })
            except Exception as e:
                logger.warning(f"Failed to load analysis result {result_file}: {e}")
        
        return sorted(results, key=lambda x: x["saved_at"], reverse=True)
    
    def refresh_backtest_cache(self, lab_id: str, backtest_id: str = None) -> bool:
        """Refresh cached backtest data"""
        if backtest_id:
            # Refresh specific backtest
            cache_path = self.get_backtest_cache_path(lab_id, backtest_id)
            if cache_path.exists():
                cache_path.unlink()
                return True
        else:
            # Refresh all backtests for a lab
            pattern = f"{lab_id}_*.json"
            cache_files = list(self.base_dir.glob(f"backtests/{pattern}"))
            for cache_file in cache_files:
                cache_file.unlink()
            return len(cache_files) > 0
        return False