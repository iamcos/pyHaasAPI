#!/usr/bin/env python3
"""
Unified Strategy Robustness Analysis CLI Tool

This tool analyzes the robustness of trading strategies with both live API and cached data support:
- Max drawdown analysis for wallet protection
- Time-based performance consistency
- Risk assessment for bot creation
- Supports both live API analysis and cache-only mode
"""

import argparse
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI_v1.analysis.robustness import StrategyRobustnessAnalyzer
from pyHaasAPI_v1.analysis.analyzer import HaasAnalyzer
from pyHaasAPI_v1.analysis.cache import UnifiedCacheManager
from pyHaasAPI_v1.analysis.models import BacktestAnalysis
from pyHaasAPI_v1 import api

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedRobustnessAnalyzer:
    """Unified robustness analyzer supporting both live API and cache-only modes"""
    
    def __init__(self, cache_only: bool = False):
        self.cache_only = cache_only
        self.cache_manager = UnifiedCacheManager()
        self.robustness_analyzer = StrategyRobustnessAnalyzer(self.cache_manager)
        self.analyzer = None
        self.executor = None
        
        if not cache_only:
            self.analyzer = HaasAnalyzer(self.cache_manager)
    
    def connect(self) -> bool:
        """Connect to API (only if not in cache-only mode)"""
        if self.cache_only:
            logger.info("🔍 Running in cache-only mode - no API connection required")
            return True
        
        if not self.analyzer:
            logger.error("❌ Analyzer not initialized for live mode")
            return False
        
        logger.info("🔌 Connecting to HaasOnline API...")
        if not self.analyzer.connect():
            logger.error("❌ Failed to connect to HaasOnline API")
            return False
        
        self.executor = self.analyzer.executor
        logger.info("✅ Connected successfully")
        return True
    
    def analyze_lab_robustness(self, lab_id: str, top_count: int = 10, output_file: str = None) -> bool:
        """Analyze robustness for a specific lab"""
        
        logger.info(f"🔍 Starting robustness analysis for lab {lab_id}")
        
        try:
            if self.cache_only:
                return self._analyze_cached_lab_robustness(lab_id, top_count, output_file)
            else:
                return self._analyze_live_lab_robustness(lab_id, top_count, output_file)
                
        except Exception as e:
            logger.error(f"❌ Error in robustness analysis: {e}")
            return False
    
    def _analyze_live_lab_robustness(self, lab_id: str, top_count: int, output_file: str) -> bool:
        """Analyze robustness using live API data"""
        
        # Analyze the lab
        logger.info(f"📊 Analyzing lab {lab_id}...")
        result = self.analyzer.analyze_lab(lab_id, top_count)
        
        if not result or not result.top_backtests:
            logger.error(f"❌ No backtests found for lab {lab_id}")
            return False
        
        logger.info(f"✅ Found {len(result.top_backtests)} backtests for analysis")
        
        # Analyze robustness
        logger.info("🛡️ Analyzing strategy robustness...")
        robustness_results = self.robustness_analyzer.analyze_backtests(result.top_backtests)
        
        if not robustness_results:
            logger.error("❌ No robustness analysis results generated")
            return False
        
        # Display results
        self._display_robustness_results(robustness_results, lab_id)
        
        # Save results if requested
        if output_file:
            self._save_robustness_results(robustness_results, output_file, lab_id)
        
        return True
    
    def _analyze_cached_lab_robustness(self, lab_id: str, top_count: int, output_file: str) -> bool:
        """Analyze robustness using cached data only"""
        
        logger.info(f"📁 Analyzing cached data for lab {lab_id}")
        
        # Get cached lab data
        cache_dir = self.cache_manager.base_dir / "backtests"
        lab_files = list(cache_dir.glob(f"{lab_id}_*.json"))
        
        if not lab_files:
            logger.error(f"❌ No cached data found for lab {lab_id}")
            logger.info("💡 Run 'python -m pyHaasAPI.cli cache-labs' to cache lab data first")
            return False
        
        logger.info(f"📁 Found {len(lab_files)} cached backtest files")
        
        # Load and analyze cached data
        backtest_analyses = []
        
        for i, file_path in enumerate(lab_files[:top_count], 1):
            try:
                logger.info(f"📊 Processing cached file {i}/{min(len(lab_files), top_count)}: {file_path.name}")
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract balance data
                starting_balance, final_balance, peak_balance = self._extract_balance_data(data)
                
                # Create BacktestAnalysis object
                backtest_analysis = self._create_backtest_analysis_from_cached_data(data, starting_balance, final_balance, peak_balance)
                
                if backtest_analysis:
                    backtest_analyses.append(backtest_analysis)
                    
            except Exception as e:
                logger.error(f"❌ Error processing cached file {file_path.name}: {e}")
                continue
        
        if not backtest_analyses:
            logger.error("❌ No valid backtest data could be extracted from cache")
            return False
        
        logger.info(f"✅ Successfully processed {len(backtest_analyses)} cached backtests")
        
        # Analyze robustness
        logger.info("🛡️ Analyzing strategy robustness from cached data...")
        robustness_results = self.robustness_analyzer.analyze_backtests(backtest_analyses)
        
        if not robustness_results:
            logger.error("❌ No robustness analysis results generated")
            return False
        
        # Display results
        self._display_robustness_results(robustness_results, lab_id)
        
        # Save results if requested
        if output_file:
            self._save_robustness_results(robustness_results, output_file, lab_id)
        
        return True
    
    def _extract_balance_data(self, data: dict) -> tuple:
        """Extract and calculate balance information from cached backtest data"""
        
        # Default values
        starting_balance = 10000.0
        final_balance = 10000.0
        peak_balance = 10000.0
        
        try:
            # Try to extract from Reports section (at top level in cached data)
            reports = data.get('Reports', {})
            
            # Find the first report (there's usually only one)
            if reports:
                report_key = list(reports.keys())[0]
                report_data = reports[report_key]
                
                # Extract balance information
                starting_balance = report_data.get('StartingBalance', 10000.0)
                final_balance = report_data.get('FinalBalance', 10000.0)
                peak_balance = report_data.get('PeakBalance', max(starting_balance, final_balance))
                
                logger.debug(f"📊 Extracted balances - Start: {starting_balance}, Final: {final_balance}, Peak: {peak_balance}")
            
            # If no reports, try to extract from other sections
            else:
                # Try to get from runtime data
                runtime_data = data.get('runtime_data', {})
                if runtime_data:
                    starting_balance = runtime_data.get('StartingBalance', 10000.0)
                    final_balance = runtime_data.get('FinalBalance', 10000.0)
                    peak_balance = runtime_data.get('PeakBalance', max(starting_balance, final_balance))
                
                # Try to get from backtest data
                backtest_data = data.get('backtest_data', {})
                if backtest_data:
                    starting_balance = backtest_data.get('StartingBalance', starting_balance)
                    final_balance = backtest_data.get('FinalBalance', final_balance)
                    peak_balance = backtest_data.get('PeakBalance', peak_balance)
            
            # Ensure we have reasonable values
            if starting_balance <= 0:
                starting_balance = 10000.0
            if final_balance <= 0:
                final_balance = starting_balance
            if peak_balance <= 0:
                peak_balance = max(starting_balance, final_balance)
                
        except Exception as e:
            logger.warning(f"⚠️ Could not extract balance data: {e}, using defaults")
        
        return starting_balance, final_balance, peak_balance
    
    def _create_backtest_analysis_from_cached_data(self, data: dict, starting_balance: float, final_balance: float, peak_balance: float) -> Optional[BacktestAnalysis]:
        """Create BacktestAnalysis object from cached data"""
        
        try:
            # Extract basic information
            backtest_id = data.get('backtest_id', 'unknown')
            lab_id = data.get('lab_id', 'unknown')
            
            # Extract runtime data
            runtime_data = data.get('runtime_data', {})
            
            # Extract script information
            script_name = runtime_data.get('ScriptName', 'Unknown Script')
            script_id = runtime_data.get('ScriptId', 'unknown')
            
            # Extract market information
            market_tag = runtime_data.get('MarketTag', 'UNKNOWN')
            
            # Extract performance metrics
            total_trades = runtime_data.get('TotalTrades', 0)
            win_rate = runtime_data.get('WinRate', 0.0) * 100  # Convert to percentage
            
            # Calculate profits and ROI
            realized_profits_usdt = final_balance - starting_balance
            roi_percentage = (realized_profits_usdt / starting_balance) * 100 if starting_balance > 0 else 0
            
            # Calculate max drawdown
            max_drawdown = ((peak_balance - final_balance) / peak_balance) * 100 if peak_balance > 0 else 0
            
            # Create BacktestAnalysis object
            backtest_analysis = BacktestAnalysis(
                backtest_id=backtest_id,
                lab_id=lab_id,
                generation_idx=runtime_data.get('GenerationIdx'),
                population_idx=runtime_data.get('PopulationIdx'),
                market_tag=market_tag,
                script_id=script_id,
                script_name=script_name,
                roi_percentage=roi_percentage,
                win_rate=win_rate,
                total_trades=total_trades,
                max_drawdown=max_drawdown,
                realized_profits_usdt=realized_profits_usdt,
                pc_value=runtime_data.get('PCValue', 0.0),
                avg_profit_per_trade=runtime_data.get('AvgProfitPerTrade', 0.0),
                profit_factor=runtime_data.get('ProfitFactor', 0.0),
                sharpe_ratio=runtime_data.get('SharpeRatio', 0.0),
                analysis_timestamp=datetime.now().isoformat()
            )
            
            return backtest_analysis
            
        except Exception as e:
            logger.error(f"❌ Error creating BacktestAnalysis from cached data: {e}")
            return None
    
    def _display_robustness_results(self, robustness_results: Dict[str, Any], lab_id: str):
        """Display robustness analysis results"""
        
        logger.info("\n" + "=" * 80)
        logger.info("🛡️ STRATEGY ROBUSTNESS ANALYSIS RESULTS")
        logger.info("=" * 80)
        logger.info(f"📊 Lab ID: {lab_id}")
        logger.info(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # Display overall robustness score
        overall_score = robustness_results.get('overall_robustness_score', 0)
        logger.info(f"🎯 Overall Robustness Score: {overall_score:.2f}/100")
        
        # Display risk assessment
        risk_level = robustness_results.get('risk_level', 'Unknown')
        logger.info(f"⚠️ Risk Level: {risk_level}")
        
        # Display max drawdown analysis
        max_drawdown_analysis = robustness_results.get('max_drawdown_analysis', {})
        if max_drawdown_analysis:
            logger.info(f"\n📉 Max Drawdown Analysis:")
            logger.info(f"   Average Max Drawdown: {max_drawdown_analysis.get('avg_max_drawdown', 0):.2f}%")
            logger.info(f"   Worst Max Drawdown: {max_drawdown_analysis.get('worst_max_drawdown', 0):.2f}%")
            logger.info(f"   Drawdown Risk Level: {max_drawdown_analysis.get('risk_level', 'Unknown')}")
        
        # Display performance consistency
        consistency_analysis = robustness_results.get('performance_consistency', {})
        if consistency_analysis:
            logger.info(f"\n📈 Performance Consistency:")
            logger.info(f"   Win Rate Stability: {consistency_analysis.get('win_rate_stability', 0):.2f}")
            logger.info(f"   ROI Consistency: {consistency_analysis.get('roi_consistency', 0):.2f}")
            logger.info(f"   Trade Count Stability: {consistency_analysis.get('trade_count_stability', 0):.2f}")
        
        # Display recommendations
        recommendations = robustness_results.get('recommendations', [])
        if recommendations:
            logger.info(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"   {i}. {rec}")
        
        logger.info("=" * 80)
    
    def _save_robustness_results(self, robustness_results: Dict[str, Any], output_file: str, lab_id: str):
        """Save robustness results to file"""
        
        try:
            # Add metadata
            robustness_results['metadata'] = {
                'lab_id': lab_id,
                'analysis_date': datetime.now().isoformat(),
                'cache_only_mode': self.cache_only,
                'analyzer_version': '1.0.0'
            }
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(robustness_results, f, indent=2)
            
            logger.info(f"💾 Robustness results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving robustness results: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Unified Strategy Robustness Analysis Tool")
    
    # Lab selection
    parser.add_argument('--lab-id', type=str, help='Lab ID to analyze')
    parser.add_argument('--all-labs', action='store_true', help='Analyze all available labs')
    
    # Analysis options
    parser.add_argument('--top-count', type=int, default=10, help='Number of top backtests to analyze')
    parser.add_argument('--output', type=str, help='Output file for results (JSON format)')
    
    # Mode selection
    parser.add_argument('--cache-only', action='store_true', 
                       help='Use cached data only (no API connection required)')
    
    # Logging
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not args.lab_id and not args.all_labs:
        parser.error("Either --lab-id or --all-labs must be specified")
    
    if args.all_labs and args.cache_only:
        parser.error("--all-labs is not supported in cache-only mode")
    
    try:
        # Create unified analyzer
        analyzer = UnifiedRobustnessAnalyzer(cache_only=args.cache_only)
        
        # Connect (if not cache-only)
        if not analyzer.connect():
            return 1
        
        # Run analysis
        if args.lab_id:
            success = analyzer.analyze_lab_robustness(
                lab_id=args.lab_id,
                top_count=args.top_count,
                output_file=args.output
            )
        else:
            # Analyze all labs (live mode only)
            logger.info("🔍 Analyzing all available labs...")
            # This would need to be implemented to get all lab IDs
            logger.error("❌ --all-labs functionality not yet implemented")
            return 1
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())













