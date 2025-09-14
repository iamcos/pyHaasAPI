#!/usr/bin/env python3
"""
Manual robustness analysis script that properly extracts data from cached backtests.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BacktestPerformance:
    """Performance data extracted from cached backtest"""
    backtest_id: str
    lab_id: str
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

def extract_performance_from_cached_file(file_path: Path, lab_id: str) -> BacktestPerformance:
    """Extract performance data from a single cached backtest file"""
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract backtest ID from filename
        backtest_id = file_path.stem.split('_', 1)[1]
        
        # Extract performance data from Reports section
        reports = data.get('Reports', {})
        if not reports:
            logger.warning(f"No Reports section in {file_path.name}")
            return None
        
        # Get the first (and usually only) report
        report_key = list(reports.keys())[0]
        report_data = reports[report_key]
        
        # Extract performance metrics from PR section
        pr_data = report_data.get('PR', {})
        if not pr_data:
            logger.warning(f"No PR section in {file_path.name}")
            return None
        
        # Extract trade statistics from P section
        p_data = report_data.get('P', {})
        
        # Calculate performance metrics
        starting_balance = pr_data.get('SB', 10000.0)
        realized_profits = pr_data.get('RP', 0.0)
        final_balance = starting_balance + realized_profits
        peak_balance = max(starting_balance, final_balance)
        
        roi_percentage = pr_data.get('ROI', 0.0)
        max_drawdown = pr_data.get('RM', 0.0)
        
        total_trades = p_data.get('C', 0)  # C = Count of trades
        winning_trades = p_data.get('W', 0)  # W = Winning trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        # Extract script and market info
        script_name = data.get('ScriptName', 'Unknown Script')
        market_tag = report_data.get('M', 'UNKNOWN')
        
        return BacktestPerformance(
            backtest_id=backtest_id,
            lab_id=lab_id,
            roi_percentage=roi_percentage,
            win_rate=win_rate,
            total_trades=total_trades,
            max_drawdown=max_drawdown,
            realized_profits_usdt=realized_profits,
            starting_balance=starting_balance,
            final_balance=final_balance,
            peak_balance=peak_balance,
            script_name=script_name,
            market_tag=market_tag
        )
        
    except Exception as e:
        logger.error(f"Error extracting data from {file_path.name}: {e}")
        return None

def analyze_lab_robustness(lab_id: str, top_count: int = 10) -> List[BacktestPerformance]:
    """Analyze robustness for a specific lab using cached data"""
    
    cache_dir = Path("unified_cache/backtests")
    if not cache_dir.exists():
        logger.error("Cache directory not found")
        return []
    
    # Find all cached files for this lab
    pattern = f"{lab_id}_*.json"
    cached_files = list(cache_dir.glob(pattern))
    
    logger.info(f"Found {len(cached_files)} cached backtests for lab {lab_id}")
    
    performances = []
    
    for file_path in cached_files:
        performance = extract_performance_from_cached_file(file_path, lab_id)
        if performance:
            performances.append(performance)
    
    # Sort by ROI (descending)
    performances.sort(key=lambda x: x.roi_percentage, reverse=True)
    
    # Return top performers
    return performances[:top_count]

def main():
    """Main function"""
    lab_id = "d26e6ff3-a706-4ae1-89c9-d82d49274a5f"
    top_count = 20
    
    logger.info(f"🔍 Analyzing robustness for lab: {lab_id}")
    
    performances = analyze_lab_robustness(lab_id, top_count)
    
    if not performances:
        logger.warning("No performance data found")
        return
    
    logger.info(f"📊 Found {len(performances)} backtests with performance data")
    
    # Display results
    print(f"\n{'='*120}")
    print(f"STRATEGY ROBUSTNESS ANALYSIS REPORT")
    print(f"{'='*120}")
    print(f"Lab ID: {lab_id}")
    print(f"Total Backtests Analyzed: {len(performances)}")
    print(f"Analysis Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*120}")
    
    print(f"\n{'Backtest ID':<40} {'ROI%':<8} {'Win Rate%':<10} {'Trades':<8} {'Max DD':<10} {'Start Bal':<12} {'Final Bal':<12} {'Script':<20}")
    print(f"{'-'*120}")
    
    for i, perf in enumerate(performances, 1):
        print(f"{perf.backtest_id:<40} {perf.roi_percentage:<8.1f} {perf.win_rate:<10.1f} {perf.total_trades:<8} {perf.max_drawdown:<10.1f} {perf.starting_balance:<12.1f} {perf.final_balance:<12.1f} {perf.script_name[:20]:<20}")
    
    # Summary statistics
    if performances:
        avg_roi = sum(p.roi_percentage for p in performances) / len(performances)
        avg_win_rate = sum(p.win_rate for p in performances) / len(performances)
        avg_trades = sum(p.total_trades for p in performances) / len(performances)
        avg_drawdown = sum(p.max_drawdown for p in performances) / len(performances)
        
        print(f"\n{'='*120}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*120}")
        print(f"Average ROI: {avg_roi:.1f}%")
        print(f"Average Win Rate: {avg_win_rate:.1f}%")
        print(f"Average Trades: {avg_trades:.0f}")
        print(f"Average Max Drawdown: {avg_drawdown:.1f}")
        print(f"Best ROI: {performances[0].roi_percentage:.1f}%")
        print(f"Worst ROI: {performances[-1].roi_percentage:.1f}%")

if __name__ == "__main__":
    main()






