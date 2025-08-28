#!/usr/bin/env python3
"""
Financial Analytics Script for pyHaasAPI Backtests
Analyzes backtest results and identifies well-performing strategies
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from pyHaasAPI import api
from pyHaasAPI.backtest_object import BacktestObject
from pyHaasAPI.model import GetBacktestResultRequest


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics"""
    backtest_id: str
    lab_id: str
    script_name: str
    account_id: str
    market: str
    
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Profitability metrics
    total_profit: float
    total_profit_usd: float
    roi_percentage: float
    profit_factor: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_percentage: float
    sharpe_ratio: float
    
    # Trade metrics
    avg_trade_profit: float
    avg_winning_trade: float
    avg_losing_trade: float
    largest_win: float
    largest_loss: float
    
    # Time metrics
    start_time: datetime
    end_time: datetime
    duration_days: float
    
    # Additional metrics
    total_fees: float
    net_profit_after_fees: float
    
    # Quality indicators
    is_profitable: bool
    has_positive_sharpe: bool
    has_acceptable_drawdown: bool
    has_good_win_rate: bool
    overall_score: float


class BacktestAnalyzer:
    """Analyzes backtest results and provides insights"""
    
    def __init__(self, executor):
        self.executor = executor
        self.metrics_list: List[BacktestMetrics] = []
        
    def analyze_backtest(self, lab_id: str, backtest_id: str) -> Optional[BacktestMetrics]:
        """Analyze a single backtest and return metrics"""
        try:
            # Get backtest data
            bt_object = BacktestObject(self.executor, lab_id, backtest_id)
            
            if not bt_object.runtime or not bt_object.metadata:
                print(f"Warning: No runtime data for backtest {backtest_id}")
                return None
            
            # Extract basic data
            runtime = bt_object.runtime
            metadata = bt_object.metadata
            
            # Calculate additional metrics
            losing_trades = runtime.total_trades - runtime.winning_trades
            avg_trade_profit = runtime.total_profit / runtime.total_trades if runtime.total_trades > 0 else 0
            
            # Calculate time duration
            duration_days = 0
            if metadata.start_time and metadata.end_time:
                duration_days = (metadata.end_time - metadata.start_time).days
            
            # Calculate fees (estimate if not available)
            total_fees = runtime.raw_data.get('f', {}).get('TFC', 0) if runtime.raw_data else 0
            net_profit_after_fees = runtime.total_profit - total_fees
            
            # Calculate ROI percentage
            roi_percentage = (runtime.total_profit / 100) * 100 if runtime.total_profit != 0 else 0
            
            # Calculate max drawdown percentage
            max_drawdown_percentage = (runtime.max_drawdown / runtime.total_profit) * 100 if runtime.total_profit > 0 else 0
            
            # Quality indicators
            is_profitable = runtime.total_profit > 0
            has_positive_sharpe = runtime.sharpe_ratio > 0
            has_acceptable_drawdown = max_drawdown_percentage < 20  # Less than 20% drawdown
            has_good_win_rate = runtime.win_rate > 0.4  # More than 40% win rate
            
            # Overall score (0-100)
            overall_score = self._calculate_overall_score(
                is_profitable, has_positive_sharpe, has_acceptable_drawdown, 
                has_good_win_rate, runtime.win_rate, runtime.profit_factor, 
                max_drawdown_percentage, roi_percentage
            )
            
            metrics = BacktestMetrics(
                backtest_id=backtest_id,
                lab_id=lab_id,
                script_name=metadata.script_name,
                account_id=metadata.account_id,
                market=metadata.market_tag,
                total_trades=runtime.total_trades,
                winning_trades=runtime.winning_trades,
                losing_trades=losing_trades,
                win_rate=runtime.win_rate,
                total_profit=runtime.total_profit,
                total_profit_usd=runtime.total_profit,  # Assuming USD
                roi_percentage=roi_percentage,
                profit_factor=runtime.profit_factor,
                max_drawdown=runtime.max_drawdown,
                max_drawdown_percentage=max_drawdown_percentage,
                sharpe_ratio=runtime.sharpe_ratio,
                avg_trade_profit=avg_trade_profit,
                avg_winning_trade=0,  # Would need to calculate from positions
                avg_losing_trade=0,   # Would need to calculate from positions
                largest_win=0,        # Would need to calculate from positions
                largest_loss=0,       # Would need to calculate from positions
                start_time=metadata.start_time or datetime.now(),
                end_time=metadata.end_time or datetime.now(),
                duration_days=duration_days,
                total_fees=total_fees,
                net_profit_after_fees=net_profit_after_fees,
                is_profitable=is_profitable,
                has_positive_sharpe=has_positive_sharpe,
                has_acceptable_drawdown=has_acceptable_drawdown,
                has_good_win_rate=has_good_win_rate,
                overall_score=overall_score
            )
            
            return metrics
            
        except Exception as e:
            print(f"Error analyzing backtest {backtest_id}: {e}")
            return None
    
    def _calculate_overall_score(self, is_profitable: bool, has_positive_sharpe: bool, 
                                has_acceptable_drawdown: bool, has_good_win_rate: bool,
                                win_rate: float, profit_factor: float, 
                                max_drawdown_percentage: float, roi_percentage: float) -> float:
        """Calculate overall performance score (0-100)"""
        score = 0
        
        # Base profitability (40 points)
        if is_profitable:
            score += 40
            # Bonus for high ROI
            if roi_percentage > 50:
                score += 10
            elif roi_percentage > 20:
                score += 5
        
        # Risk management (30 points)
        if has_positive_sharpe:
            score += 15
        if has_acceptable_drawdown:
            score += 15
        
        # Win rate quality (20 points)
        if has_good_win_rate:
            score += 20
        elif win_rate > 0.3:
            score += 10
        
        # Profit factor bonus (10 points)
        if profit_factor > 2.0:
            score += 10
        elif profit_factor > 1.5:
            score += 5
        
        return min(score, 100)
    
    def analyze_lab_backtests(self, lab_id: str, max_backtests: int = 50) -> List[BacktestMetrics]:
        """Analyze all backtests in a lab"""
        print(f"Analyzing backtests for lab {lab_id}...")
        
        try:
            # Get lab backtest results
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
            
            print(f"Found {len(results)} backtests to analyze")
            
            # Analyze each backtest
            metrics_list = []
            for i, result in enumerate(results):
                print(f"Analyzing backtest {i+1}/{len(results)}: {result.backtest_id}")
                metrics = self.analyze_backtest(lab_id, result.backtest_id)
                if metrics:
                    metrics_list.append(metrics)
            
            self.metrics_list = metrics_list
            return metrics_list
            
        except Exception as e:
            print(f"Error analyzing lab backtests: {e}")
            return []
    
    def get_best_performers(self, min_score: float = 70, min_trades: int = 5) -> List[BacktestMetrics]:
        """Get backtests that meet quality criteria"""
        return [
            m for m in self.metrics_list 
            if m.overall_score >= min_score and m.total_trades >= min_trades
        ]
    
    def get_profitable_backtests(self) -> List[BacktestMetrics]:
        """Get all profitable backtests"""
        return [m for m in self.metrics_list if m.is_profitable]
    
    def get_high_risk_backtests(self, max_drawdown_threshold: float = 30) -> List[BacktestMetrics]:
        """Get backtests with high drawdown (risk analysis)"""
        return [
            m for m in self.metrics_list 
            if m.max_drawdown_percentage > max_drawdown_threshold
        ]
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report"""
        if not self.metrics_list:
            return "No backtests analyzed."
        
        total_backtests = len(self.metrics_list)
        profitable_count = len(self.get_profitable_backtests())
        best_performers = self.get_best_performers()
        high_risk = self.get_high_risk_backtests()
        
        report = f"""
=== BACKTEST FINANCIAL ANALYTICS REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS:
- Total Backtests Analyzed: {total_backtests}
- Profitable Backtests: {profitable_count} ({profitable_count/total_backtests*100:.1f}%)
- High-Quality Backtests (Score ≥70): {len(best_performers)} ({len(best_performers)/total_backtests*100:.1f}%)
- High-Risk Backtests (Drawdown >30%): {len(high_risk)} ({len(high_risk)/total_backtests*100:.1f}%)

OVERALL PERFORMANCE:
- Average ROI: {np.mean([m.roi_percentage for m in self.metrics_list]):.2f}%
- Average Win Rate: {np.mean([m.win_rate for m in self.metrics_list]):.2f}%
- Average Profit Factor: {np.mean([m.profit_factor for m in self.metrics_list]):.2f}
- Average Max Drawdown: {np.mean([m.max_drawdown_percentage for m in self.metrics_list]):.2f}%

TOP PERFORMERS (Score ≥70):
"""
        
        if best_performers:
            # Sort by overall score
            best_performers.sort(key=lambda x: x.overall_score, reverse=True)
            
            for i, metrics in enumerate(best_performers[:10], 1):
                report += f"""
{i}. {metrics.script_name}
   - Backtest ID: {metrics.backtest_id}
   - Market: {metrics.market}
   - Score: {metrics.overall_score:.1f}/100
   - ROI: {metrics.roi_percentage:.2f}%
   - Win Rate: {metrics.win_rate:.2f}%
   - Profit Factor: {metrics.profit_factor:.2f}
   - Max Drawdown: {metrics.max_drawdown_percentage:.2f}%
   - Total Trades: {metrics.total_trades}
   - Total Profit: ${metrics.total_profit:.2f}
"""
        else:
            report += "No backtests meet the high-quality criteria (Score ≥70).\n"
        
        return report
    
    def save_detailed_report(self, filename: str = "backtest_analysis_report.json"):
        """Save detailed analysis to JSON file"""
        if not self.metrics_list:
            print("No data to save.")
            return
        
        # Convert to dictionary format
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "total_backtests": len(self.metrics_list),
            "backtests": []
        }
        
        for metrics in self.metrics_list:
            backtest_data = {
                "backtest_id": metrics.backtest_id,
                "lab_id": metrics.lab_id,
                "script_name": metrics.script_name,
                "account_id": metrics.account_id,
                "market": metrics.market,
                "metrics": {
                    "total_trades": metrics.total_trades,
                    "winning_trades": metrics.winning_trades,
                    "losing_trades": metrics.losing_trades,
                    "win_rate": metrics.win_rate,
                    "total_profit": metrics.total_profit,
                    "roi_percentage": metrics.roi_percentage,
                    "profit_factor": metrics.profit_factor,
                    "max_drawdown": metrics.max_drawdown,
                    "max_drawdown_percentage": metrics.max_drawdown_percentage,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "duration_days": metrics.duration_days,
                    "total_fees": metrics.total_fees,
                    "net_profit_after_fees": metrics.net_profit_after_fees
                },
                "quality_indicators": {
                    "is_profitable": metrics.is_profitable,
                    "has_positive_sharpe": metrics.has_positive_sharpe,
                    "has_acceptable_drawdown": metrics.has_acceptable_drawdown,
                    "has_good_win_rate": metrics.has_good_win_rate,
                    "overall_score": metrics.overall_score
                }
            }
            report_data["backtests"].append(backtest_data)
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"Detailed report saved to {filename}")


def main():
    """Main function to run the financial analytics"""
    load_dotenv()
    
    # Setup API connection
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")
    
    if not api_email or not api_password:
        print("Error: API_EMAIL and API_PASSWORD must be set in .env file")
        sys.exit(1)
    
    # Authenticate
    executor = api.RequestsExecutor(
        host=api_host,
        port=api_port,
        state=api.Guest()
    ).authenticate(
        email=api_email,
        password=api_password
    )
    
    # Create analyzer
    analyzer = BacktestAnalyzer(executor)
    
    # Example lab ID - you can change this or make it configurable
    lab_id = "6e04e13c-1a12-4759-b037-b6997f830edf"
    
    print("=== PYHAASAPI FINANCIAL ANALYTICS ===")
    print(f"Analyzing lab: {lab_id}")
    
    # Analyze backtests
    metrics_list = analyzer.analyze_lab_backtests(lab_id, max_backtests=50)
    
    if not metrics_list:
        print("No backtests found or analyzed.")
        return
    
    # Generate and display summary report
    summary = analyzer.generate_summary_report()
    print(summary)
    
    # Save detailed report
    analyzer.save_detailed_report()
    
    # Show top performers
    best_performers = analyzer.get_best_performers(min_score=70, min_trades=5)
    if best_performers:
        print(f"\n🎯 TOP PERFORMERS (Score ≥70, Min 5 trades):")
        print("=" * 80)
        for i, metrics in enumerate(best_performers[:5], 1):
            print(f"{i}. {metrics.script_name}")
            print(f"   Market: {metrics.market}")
            print(f"   Score: {metrics.overall_score:.1f}/100 | ROI: {metrics.roi_percentage:.2f}% | Win Rate: {metrics.win_rate:.2f}%")
            print(f"   Profit Factor: {metrics.profit_factor:.2f} | Max DD: {metrics.max_drawdown_percentage:.2f}%")
            print(f"   Trades: {metrics.total_trades} | Profit: ${metrics.total_profit:.2f}")
            print()
    
    # Show profitable backtests
    profitable = analyzer.get_profitable_backtests()
    if profitable:
        print(f"\n💰 PROFITABLE BACKTESTS ({len(profitable)} total):")
        print("=" * 80)
        for i, metrics in enumerate(profitable[:10], 1):
            print(f"{i}. {metrics.script_name} - ROI: {metrics.roi_percentage:.2f}% | Score: {metrics.overall_score:.1f}")
    
    # Show high-risk backtests
    high_risk = analyzer.get_high_risk_backtests()
    if high_risk:
        print(f"\n⚠️  HIGH-RISK BACKTESTS (Drawdown >30%):")
        print("=" * 80)
        for i, metrics in enumerate(high_risk[:5], 1):
            print(f"{i}. {metrics.script_name} - DD: {metrics.max_drawdown_percentage:.2f}% | ROI: {metrics.roi_percentage:.2f}%")


if __name__ == "__main__":
    main()
