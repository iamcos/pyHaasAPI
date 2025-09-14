#!/usr/bin/env python3
"""
Interactive Analysis CLI Tool

This tool provides an interactive analysis and decision-making interface for cached lab data.
Features: detailed metrics, visualization, comparison, filtering, and selective bot creation.
"""

import os
import sys
import logging
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import argparse

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.analysis.models import BacktestAnalysis
from pyHaasAPI.analysis.metrics import RunMetrics, compute_metrics
from pyHaasAPI.analysis.extraction import BacktestDataExtractor, BacktestSummary
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InteractiveAnalyzer:
    """Interactive analysis and decision-making tool for cached lab data"""
    
    def __init__(self):
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.start_time = time.time()
        self.selected_backtests = []
        
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            logger.info("🔌 Connecting to HaasOnline API...")
            
            # Initialize analyzer
            self.analyzer = HaasAnalyzer(self.cache)
            
            # Connect
            if not self.analyzer.connect():
                logger.error("❌ Failed to connect to HaasOnline API")
                return False
                
            logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_cached_labs(self) -> List[str]:
        """Get list of labs with cached data"""
        cache_dir = self.cache.base_dir / "backtests"
        if not cache_dir.exists():
            return []
        
        # Get unique lab IDs from cached files
        lab_ids = set()
        for cache_file in cache_dir.glob("*.json"):
            lab_id = cache_file.name.split('_')[0]
            lab_ids.add(lab_id)
        
        return list(lab_ids)
    
    def load_analysis_results(self, lab_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Load analysis results from cache"""
        if lab_ids:
            # Load specific lab analysis results
            results = []
            for lab_id in lab_ids:
                result_data = self.cache.load_analysis_result(lab_id)
                if result_data:
                    results.append(result_data)
            return results
        else:
            # Load all analysis results
            return self.cache.list_analysis_results()
    
    def analyze_cached_lab_detailed(self, lab_id: str, top_count: int = 50) -> Optional[Any]:
        """Analyze a single lab with detailed metrics"""
        try:
            logger.info(f"🔍 Analyzing cached lab: {lab_id[:8]}...")
            
            # Use the analyzer to analyze from cache
            result = self.analyzer.analyze_lab(lab_id, top_count=top_count)
            
            if result and result.top_backtests:
                logger.info(f"✅ Found {len(result.top_backtests)} backtests for {lab_id[:8]}")
                return result
            else:
                logger.warning(f"⚠️ No backtests found for {lab_id[:8]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error analyzing lab {lab_id[:8]}: {e}")
            return None
    
    def calculate_advanced_metrics(self, backtest: BacktestAnalysis) -> Dict[str, Any]:
        """Calculate advanced metrics for a backtest"""
        try:
            # Load detailed backtest data
            backtest_data = self.cache.load_backtest_cache(backtest.lab_id, backtest.backtest_id)
            if not backtest_data:
                return {}
            
            # Extract trade data
            extractor = BacktestDataExtractor()
            summary = extractor.extract_backtest_summary(backtest_data)
            
            if not summary:
                return {}
            
            # Calculate advanced metrics
            metrics = compute_metrics(summary)
            
            # Calculate additional metrics
            roe = (backtest.realized_profits_usdt / max(backtest.starting_balance, 1)) * 100
            dd_usdt = backtest.starting_balance - (backtest.final_balance - backtest.realized_profits_usdt)
            dd_percentage = (dd_usdt / backtest.starting_balance) * 100
            
            # Risk metrics
            risk_score = self._calculate_risk_score(backtest, metrics)
            stability_score = self._calculate_stability_score(backtest, metrics)
            
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
            logger.warning(f"⚠️ Could not calculate advanced metrics for {backtest.backtest_id[:8]}: {e}")
            return {}
    
    def _calculate_risk_score(self, backtest: BacktestAnalysis, metrics: RunMetrics) -> float:
        """Calculate risk score (0-100, lower is better)"""
        risk_factors = []
        
        # Drawdown risk
        if backtest.max_drawdown > 0:
            risk_factors.append(min(backtest.max_drawdown * 10, 50))
        
        # Volatility risk
        if metrics.volatility > 0:
            risk_factors.append(min(metrics.volatility * 100, 30))
        
        # Low win rate risk
        if backtest.win_rate < 0.5:
            risk_factors.append((0.5 - backtest.win_rate) * 100)
        
        # High leverage risk (if we can detect it)
        if backtest.realized_profits_usdt > backtest.starting_balance * 2:
            risk_factors.append(20)
        
        return min(sum(risk_factors), 100)
    
    def _calculate_stability_score(self, backtest: BacktestAnalysis, metrics: RunMetrics) -> float:
        """Calculate stability score (0-100, higher is better)"""
        stability_factors = []
        
        # Win rate stability
        stability_factors.append(backtest.win_rate * 40)
        
        # Profit factor stability
        if metrics.profit_factor > 1:
            stability_factors.append(min(metrics.profit_factor * 10, 30))
        
        # Sharpe ratio stability
        if metrics.sharpe > 0:
            stability_factors.append(min(metrics.sharpe * 10, 20))
        
        # Trade count stability
        if backtest.total_trades > 50:
            stability_factors.append(10)
        
        return min(sum(stability_factors), 100)
    
    def display_detailed_analysis(self, backtests: List[BacktestAnalysis], 
                                 sort_by: str = 'roi', top_count: int = 20) -> List[BacktestAnalysis]:
        """Display detailed analysis with advanced metrics"""
        logger.info("=" * 140)
        logger.info(f"📊 DETAILED BACKTEST ANALYSIS (Top {min(top_count, len(backtests))} by {sort_by.upper()})")
        logger.info("=" * 140)
        
        # Sort backtests
        sorted_backtests = self._sort_backtests(backtests, sort_by)
        
        # Header
        header = f"{'#':<3} {'Gen/Pop':<8} {'ROI%':<8} {'ROE%':<8} {'Win%':<6} {'Trades':<6} {'DD%':<6} {'Risk':<5} {'Stab':<5} {'PF':<6} {'Sharpe':<7} {'Script':<25}"
        logger.info(header)
        logger.info("-" * 140)
        
        # Data rows
        for i, bt in enumerate(sorted_backtests[:top_count], 1):
            # Calculate advanced metrics
            advanced = self.calculate_advanced_metrics(bt)
            
            roe = advanced.get("roe_percentage", 0)
            dd_pct = advanced.get("dd_percentage", 0)
            risk_score = advanced.get("risk_score", 0)
            stability_score = advanced.get("stability_score", 0)
            profit_factor = advanced.get("advanced_metrics", {}).get("profit_factor", 0)
            sharpe = advanced.get("advanced_metrics", {}).get("sharpe_ratio", 0)
            
            # Use generation/population if available, otherwise use backtest ID
            gen_pop = f"{bt.generation_idx}/{bt.population_idx}" if bt.generation_idx is not None and bt.population_idx is not None else bt.backtest_id[:8]
            
            row = f"{i:<3} {gen_pop:<8} {bt.roi_percentage:<8.1f} {roe:<8.1f} {bt.win_rate*100:<6.1f} {bt.total_trades:<6} {dd_pct:<6.1f} {risk_score:<5.0f} {stability_score:<5.0f} {profit_factor:<6.2f} {sharpe:<7.2f} {bt.script_name[:25]:<25}"
            logger.info(row)
        
        return sorted_backtests[:top_count]
    
    def display_comparison_table(self, backtests: List[BacktestAnalysis]) -> None:
        """Display side-by-side comparison of selected backtests"""
        if not backtests:
            logger.warning("⚠️ No backtests selected for comparison")
            return
        
        logger.info("=" * 120)
        logger.info("🔍 BACKTEST COMPARISON")
        logger.info("=" * 120)
        
        for i, bt in enumerate(backtests, 1):
            advanced = self.calculate_advanced_metrics(bt)
            
            logger.info(f"\n📊 Backtest {i}: {bt.backtest_id[:12]}")
            logger.info(f"   Lab: {bt.lab_id[:8]} | Script: {bt.script_name}")
            logger.info(f"   ROI: {bt.roi_percentage:.1f}% | ROE: {advanced.get('roe_percentage', 0):.1f}% | Win Rate: {bt.win_rate*100:.1f}%")
            logger.info(f"   Trades: {bt.total_trades} | Profit: ${bt.realized_profits_usdt:.0f} | DD: {advanced.get('dd_percentage', 0):.1f}%")
            logger.info(f"   Risk Score: {advanced.get('risk_score', 0):.0f}/100 | Stability: {advanced.get('stability_score', 0):.0f}/100")
            logger.info(f"   Sharpe: {advanced.get('advanced_metrics', {}).get('sharpe_ratio', 0):.2f} | PF: {advanced.get('advanced_metrics', {}).get('profit_factor', 0):.2f}")
    
    def apply_filters(self, backtests: List[BacktestAnalysis], 
                     min_roi: float = None, max_risk: float = None,
                     min_win_rate: float = None, min_trades: int = None,
                     min_stability: float = None) -> List[BacktestAnalysis]:
        """Apply filters to backtests"""
        filtered = []
        
        for bt in backtests:
            # Calculate advanced metrics
            advanced = self.calculate_advanced_metrics(bt)
            
            # Apply filters
            if min_roi and bt.roi_percentage < min_roi:
                continue
            if max_risk and advanced.get("risk_score", 0) > max_risk:
                continue
            if min_win_rate and bt.win_rate < min_win_rate:
                continue
            if min_trades and bt.total_trades < min_trades:
                continue
            if min_stability and advanced.get("stability_score", 0) < min_stability:
                continue
            
            filtered.append(bt)
        
        logger.info(f"🔍 Applied filters: {len(filtered)}/{len(backtests)} backtests remain")
        return filtered
    
    def _sort_backtests(self, backtests: List[BacktestAnalysis], sort_by: str) -> List[BacktestAnalysis]:
        """Sort backtests by specified metric"""
        if sort_by.lower() == 'roe':
            # Calculate ROE for sorting
            def roe_key(bt):
                advanced = self.calculate_advanced_metrics(bt)
                return advanced.get("roe_percentage", 0)
            return sorted(backtests, key=roe_key, reverse=True)
        elif sort_by.lower() == 'roi':
            return sorted(backtests, key=lambda x: x.roi_percentage, reverse=True)
        elif sort_by.lower() == 'winrate':
            return sorted(backtests, key=lambda x: x.win_rate, reverse=True)
        elif sort_by.lower() == 'profit':
            return sorted(backtests, key=lambda x: x.realized_profits_usdt, reverse=True)
        elif sort_by.lower() == 'trades':
            return sorted(backtests, key=lambda x: x.total_trades, reverse=True)
        elif sort_by.lower() == 'risk':
            def risk_key(bt):
                advanced = self.calculate_advanced_metrics(bt)
                return advanced.get("risk_score", 0)
            return sorted(backtests, key=risk_key)  # Lower risk is better
        elif sort_by.lower() == 'stability':
            def stability_key(bt):
                advanced = self.calculate_advanced_metrics(bt)
                return advanced.get("stability_score", 0)
            return sorted(backtests, key=stability_key, reverse=True)
        else:
            # Default to ROE sorting
            def roe_key(bt):
                advanced = self.calculate_advanced_metrics(bt)
                return advanced.get("roe_percentage", 0)
            return sorted(backtests, key=roe_key, reverse=True)
    
    def interactive_selection(self, backtests: List[BacktestAnalysis]) -> List[BacktestAnalysis]:
        """Interactive backtest selection"""
        logger.info("\n🎯 INTERACTIVE BACKTEST SELECTION")
        logger.info("=" * 50)
        
        selected = []
        
        while True:
            logger.info(f"\nSelected: {len(selected)} backtests")
            logger.info("Commands:")
            logger.info("  [number] - Select backtest by number")
            logger.info("  [number]-[number] - Select range (e.g., 1-5)")
            logger.info("  all - Select all backtests")
            logger.info("  clear - Clear selection")
            logger.info("  done - Finish selection")
            logger.info("  list - Show current selection")
            
            try:
                choice = input("\nEnter command: ").strip().lower()
                
                if choice == 'done':
                    break
                elif choice == 'all':
                    selected = backtests.copy()
                    logger.info(f"✅ Selected all {len(selected)} backtests")
                elif choice == 'clear':
                    selected = []
                    logger.info("✅ Selection cleared")
                elif choice == 'list':
                    self._show_selection(selected)
                elif '-' in choice:
                    # Range selection
                    start, end = map(int, choice.split('-'))
                    range_selected = backtests[start-1:end]
                    selected.extend(range_selected)
                    logger.info(f"✅ Selected backtests {start}-{end}")
                else:
                    # Single selection
                    idx = int(choice) - 1
                    if 0 <= idx < len(backtests):
                        if backtests[idx] not in selected:
                            selected.append(backtests[idx])
                            logger.info(f"✅ Selected backtest {idx+1}")
                        else:
                            logger.info(f"⚠️ Backtest {idx+1} already selected")
                    else:
                        logger.warning(f"⚠️ Invalid number: {choice}")
                        
            except (ValueError, IndexError):
                logger.warning(f"⚠️ Invalid input: {choice}")
        
        return selected
    
    def _show_selection(self, selected: List[BacktestAnalysis]) -> None:
        """Show current selection"""
        if not selected:
            logger.info("No backtests selected")
            return
        
        logger.info(f"\n📋 Current Selection ({len(selected)} backtests):")
        for i, bt in enumerate(selected, 1):
            logger.info(f"  {i}. {bt.backtest_id[:12]} - {bt.script_name} (ROI: {bt.roi_percentage:.1f}%)")
    
    def save_selection(self, selected: List[BacktestAnalysis], filename: str = None) -> str:
        """Save selected backtests for later bot creation"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"selected_backtests_{timestamp}.json"
        
        # Convert to serializable format
        selection_data = []
        for bt in selected:
            advanced = self.calculate_advanced_metrics(bt)
            selection_data.append({
                "backtest_id": bt.backtest_id,
                "lab_id": bt.lab_id,
                "script_name": bt.script_name,
                "roi_percentage": bt.roi_percentage,
                "win_rate": bt.win_rate,
                "total_trades": bt.total_trades,
                "realized_profits_usdt": bt.realized_profits_usdt,
                "advanced_metrics": advanced,
                "selected_at": datetime.now().isoformat()
            })
        
        # Save to cache directory
        save_path = self.cache.base_dir / "reports" / filename
        with open(save_path, 'w') as f:
            json.dump(selection_data, f, indent=2, default=str)
        
        logger.info(f"💾 Selection saved to: {save_path}")
        return str(save_path)
    
    def run_interactive_analysis(self, lab_ids: List[str] = None, 
                                sort_by: str = 'roi', top_count: int = 50) -> List[BacktestAnalysis]:
        """Run complete interactive analysis workflow"""
        logger.info("🚀 Starting Interactive Analysis Workflow...")
        self.start_time = time.time()
        
        # Get cached labs
        if lab_ids:
            cached_labs = lab_ids
        else:
            cached_labs = self.get_cached_labs()
        
        if not cached_labs:
            logger.warning("⚠️ No cached lab data found")
            return []
        
        logger.info(f"📋 Found {len(cached_labs)} labs with cached data")
        
        all_backtests = []
        
        # Analyze each lab
        for i, lab_id in enumerate(cached_labs):
            logger.info(f"📊 Analyzing lab {i+1}/{len(cached_labs)}: {lab_id[:8]}")
            
            result = self.analyze_cached_lab_detailed(lab_id, top_count)
            if result:
                all_backtests.extend(result.top_backtests)
        
        if not all_backtests:
            logger.warning("⚠️ No backtests found in cached data")
            return []
        
        logger.info(f"📈 Total backtests found: {len(all_backtests)}")
        
        # Display detailed analysis
        top_backtests = self.display_detailed_analysis(all_backtests, sort_by, top_count)
        
        # Interactive selection
        selected = self.interactive_selection(top_backtests)
        
        if selected:
            # Show comparison
            self.display_comparison_table(selected)
            
            # Save selection
            save_path = self.save_selection(selected)
            
            # Calculate processing time
            processing_time = time.time() - self.start_time
            
            logger.info("=" * 60)
            logger.info("📊 INTERACTIVE ANALYSIS SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total Backtests Analyzed: {len(all_backtests)}")
            logger.info(f"Backtests Selected: {len(selected)}")
            logger.info(f"Processing Time: {processing_time:.2f} seconds")
            logger.info(f"Selection Saved: {save_path}")
            logger.info("✅ Interactive analysis completed!")
            logger.info("💡 Use create-bots-from-analysis to create bots from your selection")
        
        return selected


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Interactive Analysis - Interactive analysis and decision-making for cached lab data',
        epilog='''
Examples:
  # Interactive analysis of all cached labs
  python -m pyHaasAPI.cli.interactive_analyzer
  
  # Analyze specific labs, sorted by ROE
  python -m pyHaasAPI.cli.interactive_analyzer --lab-ids lab1,lab2 --sort-by roe
  
  # Show top 100 backtests for detailed analysis
  python -m pyHaasAPI.cli.interactive_analyzer --top-count 100
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--lab-ids', nargs='+', type=str,
                       help='Analyze only specific lab IDs')
    parser.add_argument('--top-count', type=int, default=50,
                       help='Number of top backtests to show (default: 50)')
    parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate', 'profit', 'trades', 'risk', 'stability'], default='roe',
                       help='Sort backtests by metric (default: roe)')
    
    args = parser.parse_args()
    
    try:
        analyzer = InteractiveAnalyzer()
        
        if not analyzer.connect():
            sys.exit(1)
        
        # Run interactive analysis
        selected = analyzer.run_interactive_analysis(
            lab_ids=args.lab_ids,
            sort_by=args.sort_by,
            top_count=args.top_count
        )
        
        # Exit with appropriate code
        if selected:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n❌ Interactive analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
