#!/usr/bin/env python3
"""
Filtered Cache Analysis CLI for pyHaasAPI v2

This module provides realistic cache analysis by filtering out test runs
with unrealistic starting balances and position sizes.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path for v1 imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI import UnifiedCacheManager

logger = logging.getLogger("cache_analysis_filtered")


class FilteredCacheAnalyzer:
    """Cache analyzer with realistic filtering"""
    
    def __init__(self):
        self.cache = UnifiedCacheManager()
        
        # Filtering criteria for realistic analysis
        self.min_starting_balance = 100.0  # Minimum $100 starting balance
        self.max_position_pnl = 10000.0    # Maximum $10,000 position P&L
        self.min_positions = 5             # Minimum 5 positions for valid analysis
        
    async def analyze_cached_labs_filtered(self, 
                                          min_roe: float = 0.0,
                                          max_roe: float = 10000.0,
                                          min_winrate: float = 0.0,
                                          min_trades: int = 5,
                                          top_count: int = 10,
                                          per_lab_timeout_seconds: int = 180,
                                          max_concurrency: int = 4) -> Dict[str, Any]:
        """Analyze cached labs with realistic filtering"""
        try:
            logger.info("🔍 Starting filtered cache analysis...")
            
            # Get all cached labs
            cache_dir = self.cache.base_dir / "backtests"
            if not cache_dir.exists():
                logger.error("❌ Cache directory not found")
                return {}
            
            # Group files by lab ID
            lab_files = {}
            for cache_file in cache_dir.glob("*.json"):
                lab_id = cache_file.name.split('_')[0]
                if lab_id not in lab_files:
                    lab_files[lab_id] = []
                lab_files[lab_id].append(cache_file)
            
            logger.info(f"📁 Found {len(lab_files)} labs with cached data")
            
            # Analyze each lab concurrently with limits and timeouts
            lab_results = {}
            total_backtests_analyzed = 0
            total_backtests_filtered = 0

            semaphore = asyncio.Semaphore(max_concurrency)

            async def analyze_one(lab_id: str, cache_files):
                async with semaphore:
                    logger.info(f"🔍 Analyzing lab: {lab_id[:8]} ({len(cache_files)} backtests)")
                    try:
                        return lab_id, await asyncio.wait_for(
                            self._analyze_lab_filtered(lab_id, cache_files, min_winrate=min_winrate, min_trades=min_trades),
                            timeout=per_lab_timeout_seconds
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"⏱️ Timed out analyzing lab {lab_id[:8]} after {per_lab_timeout_seconds}s")
                        return lab_id, None

            tasks = [analyze_one(lab_id, files) for lab_id, files in lab_files.items()]
            for coro in asyncio.as_completed(tasks):
                lab_id, lab_analysis = await coro
                if lab_analysis and lab_analysis.get('valid_backtests'):
                    lab_results[lab_id] = lab_analysis
                    total_backtests_analyzed += lab_analysis['valid_backtests']
                    total_backtests_filtered += lab_analysis.get('filtered_out', 0)
            
            # Generate summary
            summary = {
                'total_labs': len(lab_results),
                'total_backtests_analyzed': total_backtests_analyzed,
                'total_backtests_filtered': total_backtests_filtered,
                'filtering_criteria': {
                    'min_starting_balance': self.min_starting_balance,
                    'max_position_pnl': self.max_position_pnl,
                    'min_positions': self.min_positions
                },
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Save results
            results_file = f"filtered_cache_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump({
                    'summary': summary,
                    'labs': lab_results
                }, f, indent=2)
            
            logger.info(f"💾 Filtered analysis saved to: {results_file}")
            
            # Print summary
            self._print_filtered_summary(summary, lab_results, top_count)
            
            return {
                'summary': summary,
                'labs': lab_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error in filtered analysis: {e}")
            return {}
    
    async def _analyze_lab_filtered(self, lab_id: str, cache_files: List[Path], *, min_winrate: float = 0.0, min_trades: int = 5) -> Optional[Dict[str, Any]]:
        """Analyze a single lab with filtering"""
        try:
            valid_backtests = []
            filtered_out = []
            
            for cache_file in cache_files:
                backtest_analysis = self._analyze_single_backtest_filtered(cache_file, lab_id)
                
                if backtest_analysis:
                    # Convert min_winrate to fraction (args are in percent)
                    meets_wr = backtest_analysis.get('win_rate', 0.0) * 100 >= min_winrate
                    meets_trades = (backtest_analysis.get('total_trades', 0) or 0) >= min_trades

                    if self._is_realistic_backtest(backtest_analysis) and meets_wr and meets_trades:
                        valid_backtests.append(backtest_analysis)
                    else:
                        filtered_out.append({
                            'backtest_id': backtest_analysis['backtest_id'],
                            'reason': self._get_filter_reason(backtest_analysis) if self._is_realistic_backtest(backtest_analysis) else self._get_filter_reason(backtest_analysis),
                            'roe': backtest_analysis.get('roe_percentage', 0)
                        })
            
            if not valid_backtests:
                logger.warning(f"⚠️ No valid backtests found for {lab_id[:8]}")
                return None
            
            # Sort by ROE
            valid_backtests.sort(key=lambda x: x.get('roe_percentage', 0), reverse=True)
            
            # Calculate lab statistics
            lab_stats = self._calculate_lab_statistics(valid_backtests)
            
            return {
                'lab_id': lab_id,
                'total_backtests': len(cache_files),
                'valid_backtests': len(valid_backtests),
                'filtered_out': len(filtered_out),
                'top_performances': valid_backtests[:10],  # Top 10
                'lab_statistics': lab_stats,
                'filtered_reasons': self._summarize_filter_reasons(filtered_out)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error analyzing lab {lab_id[:8]}: {e}")
            return None
    
    def _analyze_single_backtest_filtered(self, cache_file: Path, lab_id: str) -> Optional[Dict[str, Any]]:
        """Analyze a single backtest with detailed metrics"""
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            reports = data.get('Reports', {})
            if not reports:
                return None
            
            # Get the first report
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
            
            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown(position_history, starting_balance)
            
            return {
                'backtest_id': backtest_id,
                'lab_id': lab_id,
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
                'max_drawdown': max_drawdown,
                'position_history': position_history,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error analyzing backtest {cache_file.name}: {e}")
            return None
    
    def _is_realistic_backtest(self, backtest: Dict[str, Any]) -> bool:
        """Check if backtest meets realistic criteria"""
        starting_balance = backtest.get('starting_balance', 0)
        position_history = backtest.get('position_history', [])
        total_positions = backtest.get('total_positions', 0)
        
        # Check starting balance
        if starting_balance < self.min_starting_balance:
            return False
        
        # Check number of positions
        if total_positions < self.min_positions:
            return False
        
        # Check position P&L sizes
        if position_history:
            max_position_pnl = max(abs(pnl) for pnl in position_history)
            if max_position_pnl > self.max_position_pnl:
                return False
        
        return True
    
    def _get_filter_reason(self, backtest: Dict[str, Any]) -> str:
        """Get the reason why a backtest was filtered out"""
        starting_balance = backtest.get('starting_balance', 0)
        position_history = backtest.get('position_history', [])
        total_positions = backtest.get('total_positions', 0)
        
        if starting_balance < self.min_starting_balance:
            return f"Starting balance too low: ${starting_balance:.2f} < ${self.min_starting_balance}"
        
        if total_positions < self.min_positions:
            return f"Too few positions: {total_positions} < {self.min_positions}"
        
        if position_history:
            max_position_pnl = max(abs(pnl) for pnl in position_history)
            if max_position_pnl > self.max_position_pnl:
                return f"Position P&L too large: ${max_position_pnl:.2f} > ${self.max_position_pnl}"
        
        return "Unknown filter reason"
    
    def _summarize_filter_reasons(self, filtered_out: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize why backtests were filtered out"""
        reasons = {}
        for item in filtered_out:
            reason = item.get('reason', 'Unknown')
            reasons[reason] = reasons.get(reason, 0) + 1
        return reasons
    
    def _calculate_lab_statistics(self, valid_backtests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for a lab"""
        if not valid_backtests:
            return {}
        
        roe_values = [bt.get('roe_percentage', 0) for bt in valid_backtests]
        win_rates = [bt.get('win_rate', 0) for bt in valid_backtests]
        trades = [bt.get('total_trades', 0) for bt in valid_backtests]
        
        return {
            'avg_roe': sum(roe_values) / len(roe_values),
            'max_roe': max(roe_values),
            'min_roe': min(roe_values),
            'avg_winrate': sum(win_rates) / len(win_rates),
            'avg_trades': sum(trades) / len(trades),
            'total_backtests': len(valid_backtests)
        }
    
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
    
    def _print_filtered_summary(self, summary: Dict[str, Any], lab_results: Dict[str, Any], top_count: int):
        """Print filtered analysis summary"""
        print(f"\n{'='*80}")
        print(f"📊 FILTERED CACHE ANALYSIS SUMMARY")
        print(f"{'='*80}")
        print(f"Total Labs: {summary['total_labs']}")
        print(f"Backtests Analyzed: {summary['total_backtests_analyzed']}")
        print(f"Backtests Filtered Out: {summary['total_backtests_filtered']}")
        print(f"Filtering Rate: {(summary['total_backtests_filtered'] / (summary['total_backtests_analyzed'] + summary['total_backtests_filtered']) * 100):.1f}%")
        
        print(f"\n🔍 FILTERING CRITERIA:")
        criteria = summary['filtering_criteria']
        print(f"  Min Starting Balance: ${criteria['min_starting_balance']}")
        print(f"  Max Position P&L: ${criteria['max_position_pnl']}")
        print(f"  Min Positions: {criteria['min_positions']}")
        
        # Show top performing labs
        print(f"\n🏆 TOP PERFORMING LABS (Realistic ROE):")
        print(f"{'Lab ID':<12} {'Script':<25} {'Market':<20} {'Avg ROE':<10} {'Avg WR':<8} {'Backtests':<10}")
        print(f"{'-'*80}")
        
        lab_stats = []
        for lab_id, lab_data in lab_results.items():
            stats = lab_data.get('lab_statistics', {})
            top_perf = lab_data.get('top_performances', [])
            if top_perf:
                script_name = top_perf[0].get('script_name', 'Unknown')[:24]
                market_tag = top_perf[0].get('market_tag', 'Unknown')[:19]
                avg_roe = stats.get('avg_roe', 0)
                avg_wr = stats.get('avg_winrate', 0) * 100
                backtest_count = stats.get('total_backtests', 0)
                
                lab_stats.append({
                    'lab_id': lab_id,
                    'script_name': script_name,
                    'market_tag': market_tag,
                    'avg_roe': avg_roe,
                    'avg_wr': avg_wr,
                    'backtest_count': backtest_count
                })
        
        # Sort by average ROE
        lab_stats.sort(key=lambda x: x['avg_roe'], reverse=True)
        
        for lab in lab_stats[:top_count]:
            print(f"{lab['lab_id'][:8]:<12} {lab['script_name']:<25} {lab['market_tag']:<20} {lab['avg_roe']:<10.1f} {lab['avg_wr']:<8.1f} {lab['backtest_count']:<10}")
        
        # Show top individual backtests
        print(f"\n🏆 TOP INDIVIDUAL BACKTESTS (Realistic ROE):")
        print(f"{'Lab ID':<12} {'Script':<25} {'Market':<20} {'ROE':<10} {'WR':<8} {'Trades':<8} {'Balance':<12}")
        print(f"{'-'*90}")
        
        all_backtests = []
        for lab_id, lab_data in lab_results.items():
            for backtest in lab_data.get('top_performances', []):
                all_backtests.append(backtest)
        
        # Sort by ROE
        all_backtests.sort(key=lambda x: x.get('roe_percentage', 0), reverse=True)
        
        for backtest in all_backtests[:top_count]:
            lab_id = backtest.get('lab_id', 'Unknown')[:8]
            script_name = backtest.get('script_name', 'Unknown')[:24]
            market_tag = backtest.get('market_tag', 'Unknown')[:19]
            roe = backtest.get('roe_percentage', 0)
            wr = backtest.get('win_rate', 0) * 100
            trades = backtest.get('total_trades', 0)
            balance = backtest.get('starting_balance', 0)
            
            print(f"{lab_id:<12} {script_name:<25} {market_tag:<20} {roe:<10.1f} {wr:<8.1f} {trades:<8} ${balance:<11.2f}")


async def main():
    """Main entry point for filtered cache analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filtered Cache Analysis CLI for pyHaasAPI v2")
    parser.add_argument('--min-roe', type=float, default=0.0, help='Minimum ROE percentage')
    parser.add_argument('--max-roe', type=float, default=10000.0, help='Maximum ROE percentage')
    parser.add_argument('--min-winrate', type=float, default=0.0, help='Minimum win rate percentage')
    parser.add_argument('--min-trades', type=int, default=5, help='Minimum number of trades')
    parser.add_argument('--top-count', type=int, default=10, help='Number of top results to show')
    
    args = parser.parse_args()
    
    analyzer = FilteredCacheAnalyzer()
    
    try:
        # Perform filtered analysis
        results = await analyzer.analyze_cached_labs_filtered(
            min_roe=args.min_roe,
            max_roe=args.max_roe,
            min_winrate=args.min_winrate,
            min_trades=args.min_trades,
            top_count=args.top_count
        )
        
        if results:
            logger.info("✅ Filtered analysis completed successfully")
        else:
            logger.error("❌ No analysis results generated")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Filtered analysis failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
