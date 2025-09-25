#!/usr/bin/env python3
"""
Fixed Cache Analysis CLI for pyHaasAPI v2

This module provides cache analysis functionality that correctly extracts
performance metrics from the actual cache file structure:
- Reports[report_key]['PR'] - Performance Report (aggregated metrics)
- Reports[report_key]['P'] - Positions (including PH - Position History)
- Reports[report_key]['T'] - Trade statistics
- Reports[report_key]['O'] - Orders

We calculate all performance metrics ourselves from the raw trade data.
"""

import asyncio
import json
import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path for v1 imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI import UnifiedCacheManager
import logging

logger = logging.getLogger("cache_analysis_fixed")


class CacheAnalyzerV2Fixed:
    """Fixed cache analysis tool that correctly extracts performance metrics"""
    
    def __init__(self):
        self.cache = UnifiedCacheManager()
        
    async def connect(self) -> bool:
        """Connect to cache (no API connection needed)"""
        try:
            cached_labs = self.get_cached_labs()
            if cached_labs:
                logger.info(f"📁 Found {len(cached_labs)} labs with cached data - using cache-only mode")
                logger.info("✅ Cache-only mode activated (no API connection required)")
                return True
            else:
                logger.warning("⚠️ No cached labs found")
                return False
        except Exception as e:
            logger.error(f"❌ Cache connection failed: {e}")
            return False
    
    def get_cached_labs(self) -> Dict[str, int]:
        """Get dictionary of labs with cached data and their backtest counts"""
        cache_dir = self.cache.base_dir / "backtests"
        if not cache_dir.exists():
            return {}
        
        # Get unique lab IDs from cached files with counts
        lab_counts = {}
        for cache_file in cache_dir.glob("*.json"):
            lab_id = cache_file.name.split('_')[0]
            lab_counts[lab_id] = lab_counts.get(lab_id, 0) + 1
        
        return lab_counts
    
    async def analyze_cached_lab(self, lab_id: str, top_count: int = 10) -> Optional[Dict[str, Any]]:
        """Analyze a single lab from cached data using correct structure"""
        try:
            logger.info(f"🔍 Analyzing cached lab: {lab_id[:8]}...")
            
            # Get all cache files for this lab
            cache_dir = self.cache.base_dir / "backtests"
            cache_files = list(cache_dir.glob(f"{lab_id}_*.json"))
            
            if not cache_files:
                logger.warning(f"⚠️ No cache files found for {lab_id[:8]}")
                return None
            
            performances = []
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # Extract performance from Reports section
                    performance = self._extract_performance_from_reports(data, lab_id, cache_file.stem)
                    if performance:
                        performances.append(performance)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error reading cache file {cache_file.name}: {e}")
                    continue
            
            if performances:
                # Sort by ROE and return top results
                performances.sort(key=lambda x: x.get('roe_percentage', 0), reverse=True)
                logger.info(f"✅ Found {len(performances)} backtests for {lab_id[:8]}")
                return self._create_analysis_result(lab_id, performances[:top_count])
            else:
                logger.warning(f"⚠️ No backtests found for {lab_id[:8]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error analyzing lab {lab_id[:8]}: {e}")
            return None
    
    def _extract_performance_from_reports(self, data: Dict[str, Any], lab_id: str, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Extract performance metrics from Reports section"""
        try:
            reports = data.get('Reports', {})
            if not reports:
                return None
            
            # Get the first (and usually only) report
            report_key = list(reports.keys())[0]
            report = reports[report_key]
            
            # Extract basic info
            script_name = data.get('ScriptName', 'Unknown')
            market_tag = report.get('M', 'Unknown')
            
            # Extract performance report (PR)
            pr = report.get('PR', {})
            if not pr:
                return None
            
            # Extract position data (P)
            positions = report.get('P', {})
            
            # Extract trade statistics (T)
            trades = report.get('T', {})
            
            # Calculate performance metrics from raw data
            performance = self._calculate_performance_metrics(
                pr, positions, trades, lab_id, backtest_id, script_name, market_tag
            )
            
            return performance
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting performance from reports: {e}")
            return None
    
    def _calculate_performance_metrics(
        self, 
        pr: Dict[str, Any], 
        positions: Dict[str, Any], 
        trades: Dict[str, Any],
        lab_id: str, 
        backtest_id: str, 
        script_name: str, 
        market_tag: str
    ) -> Dict[str, Any]:
        """Calculate all performance metrics from raw data"""
        
        # Extract basic metrics from PR (Performance Report)
        starting_balance = pr.get('SB', 10000.0)  # Starting Balance
        current_balance = pr.get('PC', 10000.0)   # Portfolio Current
        realized_profits = pr.get('RP', 0.0)      # Realized Profits
        unrealized_profits = pr.get('UP', 0.0)    # Unrealized Profits
        gross_profit = pr.get('GP', 0.0)          # Gross Profit
        
        # Calculate ROI percentage from bot report
        roi_percentage = ((current_balance - starting_balance) / starting_balance) * 100 if starting_balance > 0 else 0
        
        # Extract position statistics
        total_positions = positions.get('C', 0)           # Count of positions
        winning_positions = positions.get('W', 0)        # Winning positions
        average_profit = positions.get('AP', 0.0)       # Average Profit
        total_profit = positions.get('APM', 0.0)        # Total Profit
        
        # Calculate win rate
        win_rate = (winning_positions / total_positions) if total_positions > 0 else 0
        
        # Extract trade statistics
        total_trades = trades.get('TR', 0)              # Total Trades
        winning_trades = trades.get('BW', 0)            # Winning Trades
        losing_trades = trades.get('BL', 0)             # Losing Trades
        
        # Calculate profit factor
        gross_profit_abs = abs(gross_profit)
        gross_loss_abs = abs(realized_profits - gross_profit) if realized_profits < gross_profit else 0
        profit_factor = gross_profit_abs / gross_loss_abs if gross_loss_abs > 0 else 0
        
        # Calculate average profit per trade
        avg_profit_per_trade = realized_profits / total_trades if total_trades > 0 else 0
        
        # Calculate ROE from actual trades/positions (not from bot report)
        roe_percentage = self._calculate_roe_from_trades(positions.get('PH', []), starting_balance)
        
        # Calculate max drawdown from position history
        max_drawdown = self._calculate_max_drawdown(positions.get('PH', []), starting_balance)
        
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(positions.get('PH', []))
        
        return {
            'backtest_id': backtest_id,
            'lab_id': lab_id,
            'script_name': script_name,
            'market_tag': market_tag,
            'roi_percentage': roi_percentage,
            'roe_percentage': roe_percentage,  # ROE calculated from actual trades
            'win_rate': win_rate,
            'total_trades': total_trades,
            'total_positions': total_positions,
            'winning_positions': winning_positions,
            'max_drawdown': max_drawdown,
            'realized_profits_usdt': realized_profits,
            'unrealized_profits_usdt': unrealized_profits,
            'gross_profit': gross_profit,
            'starting_balance': starting_balance,
            'current_balance': current_balance,
            'pc_value': current_balance,
            'avg_profit_per_trade': avg_profit_per_trade,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_roe_from_trades(self, position_history: List[float], starting_balance: float) -> float:
        """Calculate ROE (Return on Equity) from actual trade P&L"""
        if not position_history or starting_balance <= 0:
            return 0.0
        
        # Calculate total P&L from all positions
        total_pnl = sum(position_history)
        
        # ROE = (Total P&L / Starting Balance) * 100
        roe_percentage = (total_pnl / starting_balance) * 100
        
        return roe_percentage
    
    def _calculate_max_drawdown(self, position_history: List[float], starting_balance: float) -> float:
        """Calculate maximum drawdown from position history"""
        if not position_history:
            return 0.0
        
        # Convert position P&L to running balance
        running_balance = starting_balance
        peak = starting_balance
        max_dd = 0.0
        
        for pnl in position_history:
            running_balance += pnl
            if running_balance > peak:
                peak = running_balance
            
            drawdown = (peak - running_balance) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd * 100  # Return as percentage
    
    def _calculate_sharpe_ratio(self, position_history: List[float]) -> float:
        """Calculate simplified Sharpe ratio from position history"""
        if len(position_history) < 2:
            return 0.0
        
        # Calculate returns
        returns = [pnl for pnl in position_history if pnl != 0]
        if len(returns) < 2:
            return 0.0
        
        # Calculate mean and std deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe = mean_return / std_dev if std_dev > 0 else 0
        return sharpe
    
    def _create_analysis_result(self, lab_id: str, performances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create analysis result from performances"""
        return {
            'lab_id': lab_id,
            'total_backtests': len(performances),
            'top_performances': performances,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    async def analyze_all_cached_labs(self, top_count: int = 10) -> Dict[str, Any]:
        """Analyze all cached labs"""
        cached_labs = self.get_cached_labs()
        if not cached_labs:
            logger.warning("⚠️ No cached labs found")
            return {}
        
        logger.info(f"🔍 Analyzing {len(cached_labs)} cached labs...")
        
        results = {}
        for lab_id, backtest_count in cached_labs.items():
            logger.info(f"📊 Lab {lab_id[:8]}: {backtest_count} backtests")
            result = await self.analyze_cached_lab(lab_id, top_count)
            if result:
                results[lab_id] = result
        
        logger.info(f"✅ Analysis complete: {len(results)} labs analyzed")
        return results
    
    def print_analysis_summary(self, results: Dict[str, Any], sort_by: str = 'roe') -> None:
        """Print analysis summary"""
        if not results:
            logger.info("📊 No analysis results to display")
            return
        
        logger.info(f"\n📊 ANALYSIS SUMMARY ({len(results)} labs)")
        logger.info("=" * 80)
        
        # Collect all performances for sorting
        all_performances = []
        for lab_id, result in results.items():
            for perf in result.get('top_performances', []):
                perf['lab_id'] = lab_id
                all_performances.append(perf)
        
        # Sort by specified metric (always use ROE, never ROI)
        if sort_by == 'roi':
            all_performances.sort(key=lambda x: x.get('roe_percentage', 0), reverse=True)
        elif sort_by == 'roe':
            all_performances.sort(key=lambda x: x.get('roe_percentage', 0), reverse=True)
        elif sort_by == 'winrate':
            all_performances.sort(key=lambda x: x.get('win_rate', 0), reverse=True)
        elif sort_by == 'profit':
            all_performances.sort(key=lambda x: x.get('realized_profits_usdt', 0), reverse=True)
        elif sort_by == 'trades':
            all_performances.sort(key=lambda x: x.get('total_trades', 0), reverse=True)
        
        # Display top results
        logger.info(f"{'Lab ID':<10} {'Script':<25} {'Market':<20} {'ROE%':<8} {'WR%':<6} {'Trades':<7} {'Profit':<10}")
        logger.info("-" * 80)
        
        for perf in all_performances[:20]:  # Show top 20
            lab_id = perf.get('lab_id', '')[:8]
            script_name = perf.get('script_name', '')[:24]
            market_tag = perf.get('market_tag', '')[:19]
            roe = perf.get('roe_percentage', 0)
            win_rate = perf.get('win_rate', 0)
            trades = perf.get('total_trades', 0)
            profit = perf.get('realized_profits_usdt', 0)
            
            logger.info(f"{lab_id:<10} {script_name:<25} {market_tag:<20} {roe:<8.1f} {win_rate:<6.1f} {trades:<7} {profit:<10.2f}")
    
    def save_analysis_results(self, results: Dict[str, Any], output_file: str) -> None:
        """Save analysis results to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"💾 Analysis results saved to: {output_file}")
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")


async def main():
    """Main entry point for testing"""
    analyzer = CacheAnalyzerV2Fixed()
    
    if not await analyzer.connect():
        return 1
    
    try:
        # Analyze all labs
        results = await analyzer.analyze_all_cached_labs(top_count=2)
        
        # Display results
        analyzer.print_analysis_summary(results, 'roe')
        
        # Save results
        analyzer.save_analysis_results(results, 'cache_analysis_results_v2_fixed.json')
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
