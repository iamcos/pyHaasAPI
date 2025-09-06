"""
Cache management for pyHaasAPI analysis

This module provides unified caching functionality for backtest data,
analysis results, and reports.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .models import LabAnalysisResult


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
                'ROI %', 'Win Rate %', 'Total Trades', 'Max Drawdown %', 'Realized Profits USDT',
                'PC Value', 'Avg Profit/Trade', 'Profit Factor', 'Sharpe Ratio',
                'Analysis Timestamp'
            ])
            
            # Write data rows
            for backtest in result.top_backtests:
                writer.writerow([
                    result.lab_id, result.lab_name, result.total_backtests, result.analyzed_backtests,
                    backtest.backtest_id, backtest.generation_idx, backtest.population_idx,
                    backtest.market_tag, backtest.script_id, backtest.script_name,
                    backtest.roi_percentage, backtest.win_rate * 100, backtest.total_trades,
                    backtest.max_drawdown, backtest.realized_profits_usdt,
                    backtest.pc_value, backtest.avg_profit_per_trade, backtest.profit_factor,
                    backtest.sharpe_ratio, backtest.analysis_timestamp
                ])
        
        return report_path
