#!/usr/bin/env python3
"""
Detailed Analysis CLI for pyHaasAPI v2

This module provides detailed analysis of specific labs and their top performing bots,
with breakdown of trades, ROE accumulation graphs, and account balance graphs.
"""

import asyncio
import json
import csv
import logging
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path for v1 imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI import UnifiedCacheManager

logger = logging.getLogger("detailed_analysis")


class DetailedAnalyzer:
    """Detailed analysis tool for specific labs and backtests"""
    
    def __init__(self):
        self.cache = UnifiedCacheManager()
        
    async def analyze_lab_detailed(self, lab_id: str, top_count: int = 5) -> Dict[str, Any]:
        """Perform detailed analysis of a specific lab"""
        try:
            logger.info(f"🔍 Performing detailed analysis for lab: {lab_id[:8]}")
            
            # Get all cache files for this lab
            cache_dir = self.cache.base_dir / "backtests"
            cache_files = list(cache_dir.glob(f"{lab_id}_*.json"))
            
            if not cache_files:
                logger.warning(f"⚠️ No cache files found for {lab_id[:8]}")
                return {}
            
            logger.info(f"📁 Found {len(cache_files)} backtests for {lab_id[:8]}")
            
            # Analyze each backtest
            backtest_analyses = []
            for cache_file in cache_files:
                analysis = self._analyze_single_backtest(cache_file, lab_id)
                if analysis:
                    backtest_analyses.append(analysis)
            
            # Sort by ROE and get top performers
            backtest_analyses.sort(key=lambda x: x.get('roe_percentage', 0), reverse=True)
            top_performers = backtest_analyses[:top_count]
            
            # Generate detailed reports
            detailed_report = {
                'lab_id': lab_id,
                'total_backtests': len(backtest_analyses),
                'top_performers': top_performers,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Save detailed report
            report_file = f"detailed_analysis_{lab_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(detailed_report, f, indent=2)
            
            logger.info(f"💾 Detailed analysis saved to: {report_file}")
            
            # Generate visualizations
            await self._generate_visualizations(lab_id, top_performers)
            
            return detailed_report
            
        except Exception as e:
            logger.error(f"❌ Error in detailed analysis: {e}")
            return {}
    
    def _analyze_single_backtest(self, cache_file: Path, lab_id: str) -> Optional[Dict[str, Any]]:
        """Analyze a single backtest file in detail"""
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            reports = data.get('Reports', {})
            if not reports:
                return None
            
            # Get the first (and usually only) report
            report_key = list(reports.keys())[0]
            report = reports[report_key]
            
            # Extract data
            pr = report.get('PR', {})
            positions = report.get('P', {})
            trades = report.get('T', {})
            
            # Basic info
            script_name = data.get('ScriptName', 'Unknown')
            market_tag = report.get('M', 'Unknown')
            backtest_id = cache_file.stem
            
            # Performance metrics
            starting_balance = pr.get('SB', 0)
            current_balance = pr.get('PC', 0)
            realized_profits = pr.get('RP', 0)
            
            # Position analysis
            position_history = positions.get('PH', [])
            total_positions = positions.get('C', 0)
            winning_positions = positions.get('W', 0)
            
            # Calculate ROE from trades
            total_pnl = sum(position_history)
            roe_percentage = (total_pnl / starting_balance) * 100 if starting_balance > 0 else 0
            
            # Calculate win rate
            win_rate = (winning_positions / total_positions) if total_positions > 0 else 0
            
            # Trade statistics
            total_trades = trades.get('TR', 0)
            winning_trades = trades.get('BW', 0)
            losing_trades = trades.get('BL', 0)
            
            # Calculate running balance and ROE accumulation
            running_balance, roe_accumulation = self._calculate_running_metrics(position_history, starting_balance)
            
            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown(position_history, starting_balance)
            
            return {
                'backtest_id': backtest_id,
                'script_name': script_name,
                'market_tag': market_tag,
                'starting_balance': starting_balance,
                'current_balance': current_balance,
                'realized_profits': realized_profits,
                'total_pnl': total_pnl,
                'roe_percentage': roe_percentage,
                'win_rate': win_rate,
                'total_positions': total_positions,
                'winning_positions': winning_positions,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'max_drawdown': max_drawdown,
                'position_history': position_history,
                'running_balance': running_balance,
                'roe_accumulation': roe_accumulation,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error analyzing backtest {cache_file.name}: {e}")
            return None
    
    def _calculate_running_metrics(self, position_history: List[float], starting_balance: float) -> tuple:
        """Calculate running balance and ROE accumulation"""
        if not position_history or starting_balance <= 0:
            return [], []
        
        running_balance = [starting_balance]
        roe_accumulation = [0.0]
        
        for pnl in position_history:
            new_balance = running_balance[-1] + pnl
            running_balance.append(new_balance)
            
            roe = ((new_balance - starting_balance) / starting_balance) * 100
            roe_accumulation.append(roe)
        
        return running_balance, roe_accumulation
    
    def _calculate_max_drawdown(self, position_history: List[float], starting_balance: float) -> float:
        """Calculate maximum drawdown from position history"""
        if not position_history:
            return 0.0
        
        running_balance = [starting_balance]
        for pnl in position_history:
            running_balance.append(running_balance[-1] + pnl)
        
        peak = starting_balance
        max_dd = 0.0
        
        for balance in running_balance:
            if balance > peak:
                peak = balance
            
            drawdown = (peak - balance) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd * 100  # Return as percentage
    
    async def _generate_visualizations(self, lab_id: str, top_performers: List[Dict[str, Any]]):
        """Generate graphs for the top performing backtests"""
        try:
            logger.info("📊 Generating visualizations...")
            
            # Create output directory
            output_dir = Path(f"detailed_analysis_{lab_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            output_dir.mkdir(exist_ok=True)
            
            for i, backtest in enumerate(top_performers[:3]):  # Top 3 only
                await self._create_backtest_graphs(backtest, output_dir, i + 1)
            
            logger.info(f"📊 Visualizations saved to: {output_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error generating visualizations: {e}")
    
    async def _create_backtest_graphs(self, backtest: Dict[str, Any], output_dir: Path, rank: int):
        """Create graphs for a single backtest"""
        try:
            backtest_id = backtest['backtest_id']
            position_history = backtest['position_history']
            running_balance = backtest['running_balance']
            roe_accumulation = backtest['roe_accumulation']
            
            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'Backtest Analysis - Rank #{rank}\n{backtest_id[:20]}...', fontsize=14)
            
            # 1. Position P&L over time
            ax1.plot(position_history, 'b-', alpha=0.7)
            ax1.axhline(y=0, color='r', linestyle='--', alpha=0.5)
            ax1.set_title('Position P&L Over Time')
            ax1.set_xlabel('Position Number')
            ax1.set_ylabel('P&L ($)')
            ax1.grid(True, alpha=0.3)
            
            # 2. Running Balance
            ax2.plot(running_balance, 'g-', linewidth=2)
            ax2.axhline(y=backtest['starting_balance'], color='r', linestyle='--', alpha=0.5, label='Starting Balance')
            ax2.set_title('Account Balance Over Time')
            ax2.set_xlabel('Position Number')
            ax2.set_ylabel('Balance ($)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. ROE Accumulation
            ax3.plot(roe_accumulation, 'purple', linewidth=2)
            ax3.axhline(y=0, color='r', linestyle='--', alpha=0.5)
            ax3.set_title('ROE Accumulation Over Time')
            ax3.set_xlabel('Position Number')
            ax3.set_ylabel('ROE (%)')
            ax3.grid(True, alpha=0.3)
            
            # 4. Position P&L Distribution
            ax4.hist(position_history, bins=20, alpha=0.7, color='orange')
            ax4.axvline(x=0, color='r', linestyle='--', alpha=0.5)
            ax4.set_title('Position P&L Distribution')
            ax4.set_xlabel('P&L ($)')
            ax4.set_ylabel('Frequency')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save the plot
            plot_file = output_dir / f"backtest_analysis_rank_{rank}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Created visualization for rank #{rank}")
            
        except Exception as e:
            logger.error(f"❌ Error creating graphs for backtest: {e}")
    
    def print_detailed_summary(self, detailed_report: Dict[str, Any]):
        """Print a detailed summary of the analysis"""
        if not detailed_report:
            logger.info("📊 No detailed analysis results to display")
            return
        
        lab_id = detailed_report['lab_id']
        top_performers = detailed_report['top_performers']
        
        print(f"\n{'='*80}")
        print(f"📊 DETAILED ANALYSIS SUMMARY - Lab {lab_id[:8]}")
        print(f"{'='*80}")
        print(f"Total Backtests Analyzed: {detailed_report['total_backtests']}")
        print(f"Top Performers Shown: {len(top_performers)}")
        
        for i, backtest in enumerate(top_performers, 1):
            print(f"\n{'='*60}")
            print(f"🏆 RANK #{i} - {backtest['script_name']}")
            print(f"{'='*60}")
            print(f"Backtest ID: {backtest['backtest_id'][:30]}...")
            print(f"Market: {backtest['market_tag']}")
            print(f"")
            print(f"💰 FINANCIAL METRICS:")
            print(f"  Starting Balance: ${backtest['starting_balance']:,.2f}")
            print(f"  Current Balance: ${backtest['current_balance']:,.2f}")
            print(f"  Realized Profits: ${backtest['realized_profits']:,.2f}")
            print(f"  Total P&L: ${backtest['total_pnl']:,.2f}")
            print(f"  ROE: {backtest['roe_percentage']:,.2f}%")
            print(f"  Max Drawdown: {backtest['max_drawdown']:,.2f}%")
            print(f"")
            print(f"📈 TRADING METRICS:")
            print(f"  Total Positions: {backtest['total_positions']}")
            print(f"  Winning Positions: {backtest['winning_positions']}")
            print(f"  Win Rate: {backtest['win_rate']*100:.1f}%")
            print(f"  Total Trades: {backtest['total_trades']}")
            print(f"  Winning Trades: {backtest['winning_trades']}")
            print(f"  Losing Trades: {backtest['losing_trades']}")
            print(f"")
            print(f"📊 POSITION ANALYSIS:")
            if backtest['position_history']:
                print(f"  Position P&L Range: ${min(backtest['position_history']):,.2f} to ${max(backtest['position_history']):,.2f}")
                print(f"  Average Position P&L: ${sum(backtest['position_history'])/len(backtest['position_history']):,.2f}")
                positive_positions = [p for p in backtest['position_history'] if p > 0]
                negative_positions = [p for p in backtest['position_history'] if p < 0]
                print(f"  Positive Positions: {len(positive_positions)}")
                print(f"  Negative Positions: {len(negative_positions)}")
                
                if backtest['roe_percentage'] > 1000:
                    print(f"  ⚠️  HIGH ROE WARNING:")
                    print(f"      This high ROE ({backtest['roe_percentage']:,.2f}%) is likely due to:")
                    print(f"      - Very small starting balance (${backtest['starting_balance']:,.2f})")
                    print(f"      - This may be a test run with minimal capital")
                    print(f"      - Consider filtering out backtests with starting balance < $100")


async def main():
    """Main entry point for detailed analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Detailed Analysis CLI for pyHaasAPI v2")
    parser.add_argument('--lab-id', required=True, help='Lab ID to analyze in detail')
    parser.add_argument('--top-count', type=int, default=5, help='Number of top performers to analyze')
    
    args = parser.parse_args()
    
    analyzer = DetailedAnalyzer()
    
    try:
        # Perform detailed analysis
        detailed_report = await analyzer.analyze_lab_detailed(args.lab_id, args.top_count)
        
        if detailed_report:
            # Print summary
            analyzer.print_detailed_summary(detailed_report)
            logger.info("✅ Detailed analysis completed successfully")
        else:
            logger.error("❌ No analysis results generated")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Detailed analysis failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))


