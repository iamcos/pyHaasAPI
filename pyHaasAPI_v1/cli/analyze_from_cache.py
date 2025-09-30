#!/usr/bin/env python3
"""
Analyze From Cache CLI Tool

This tool analyzes cached lab data and can save results for later bot creation.
Supports sorting by ROI, ROE, and other metrics with detailed display.
"""

import os
import sys
import logging
import time
import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI_v1 import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI_v1.analysis.models import BacktestAnalysis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheAnalyzer:
    """Analyzes cached lab data and provides detailed results"""
    
    def __init__(self):
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.start_time = time.time()
        
    def connect(self) -> bool:
        """Connect to HaasOnline API or use cache-only mode"""
        try:
            # Check if we have cached data first
            cached_labs = self.get_cached_labs()
            if cached_labs:
                logger.info(f"📁 Found {len(cached_labs)} labs with cached data - using cache-only mode")
                logger.info("✅ Cache-only mode activated (no API connection required)")
                return True
            
            logger.info("🔌 No cached data found - attempting to connect to HaasOnline API...")
            
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
    
    def analyze_cached_lab(self, lab_id: str, top_count: int = 10) -> Optional[Any]:
        """Analyze a single lab from cached data using manual extraction"""
        try:
            logger.info(f"🔍 Analyzing cached lab: {lab_id[:8]}...")
            
            # Use manual analysis for proper data extraction
            performances = self._analyze_lab_manual(lab_id, top_count)
            
            if performances:
                logger.info(f"✅ Found {len(performances)} backtests for {lab_id[:8]}")
                return self._create_analysis_result(lab_id, performances)
            else:
                logger.warning(f"⚠️ No backtests found for {lab_id[:8]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error analyzing lab {lab_id[:8]}: {e}")
            return None
    
    def _analyze_lab_manual(self, lab_id: str, top_count: int) -> List[Dict[str, Any]]:
        """Manual analysis that properly extracts data from cached files and CSV reports"""
        import json
        from pathlib import Path
        from dataclasses import dataclass
        
        @dataclass
        class BacktestPerformance:
            backtest_id: str
            lab_id: str
            generation_idx: int
            population_idx: int
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
            parameter_values: Dict[str, str] = None
        
        # First, try to get data from CSV reports (preferred method)
        csv_data = self._get_all_csv_data_for_lab(lab_id)
        
        if csv_data:
            logger.info(f"Using CSV data for lab {lab_id[:8]} - found {len(csv_data)} backtests")
            performances = []
            
            for backtest_id, data in csv_data.items():
                performance = BacktestPerformance(
                    backtest_id=backtest_id,
                    lab_id=lab_id,
                    generation_idx=data['generation'],
                    population_idx=data['population'],
                    roi_percentage=data['roi_percentage'],
                    win_rate=data['win_rate'],
                    total_trades=data['total_trades'],
                    max_drawdown=data['max_drawdown'],
                    realized_profits_usdt=data['realized_profits_usdt'],
                    starting_balance=data['starting_balance'],
                    final_balance=data['final_balance'],
                    peak_balance=max(data['starting_balance'], data['final_balance']),
                    script_name=data['script_name'],
                    market_tag=data['market_tag']
                )
                # Add parameter values
                performance.parameter_values = self._extract_parameter_values(lab_id, backtest_id)
                performances.append(performance)
            
            # Sort by ROE (Return on Equity) - calculated as realized_profits / starting_balance
            performances.sort(key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
            
            # Return top performers
            return performances[:top_count]
        
        # Fallback to cached files if no CSV data available
        logger.info(f"No CSV data found, using cached files for lab {lab_id[:8]}")
        
        cache_dir = self.cache.base_dir / "backtests"
        if not cache_dir.exists():
            return []
        
        # Find all cached files for this lab
        pattern = f"{lab_id}_*.json"
        cached_files = list(cache_dir.glob(pattern))
        
        logger.info(f"Found {len(cached_files)} cached backtests for lab {lab_id}")
        
        performances = []
        
        for file_path in cached_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract backtest ID from filename
                backtest_id = file_path.stem.split('_', 1)[1]
                
                # Case A: Raw runtime cache with Reports
                if data and 'Reports' in data and data.get('Reports'):
                    reports = data.get('Reports', {})
                    # Get the first report (usually there's only one)
                    report_key = list(reports.keys())[0]
                    report_data = reports[report_key]
                    
                    # Extract performance data from PR (Performance Report) section
                    pr_data = report_data.get('PR', {})
                    p_data = report_data.get('P', {})
                    
                    if not pr_data or not p_data:
                        continue
                    
                    starting_balance = pr_data.get('SB', 10000.0)
                    realized_profits = pr_data.get('RP', 0.0)
                    final_balance = starting_balance + realized_profits
                    peak_balance = max(starting_balance, final_balance)
                    
                    roi_percentage = pr_data.get('ROI', 0.0)
                    max_drawdown = pr_data.get('RM', 0.0)
                    
                    total_trades = p_data.get('C', 0)
                    winning_trades = p_data.get('W', 0)
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                    
                    # Extract script and market info from multiple possible locations
                    script_name = (
                        data.get('ScriptName')
                        or data.get('script_name')
                        or data.get('RuntimeData', {}).get('ScriptName')
                        or data.get('runtime_data', {}).get('ScriptName')
                        or data.get('runtime_data', {}).get('script_name')
                        or data.get('Reports', {}).get(next(iter(data.get('Reports', {})), {}), {}).get('ScriptName')
                        or 'Unknown Script'
                    )
                    market_tag = (
                        data.get('PriceMarket')
                        or data.get('Market')
                        or data.get('market')
                        or data.get('runtime_data', {}).get('PriceMarket')
                        or data.get('RuntimeData', {}).get('PriceMarket')
                        or 'UNKNOWN'
                    )
                else:
                    # Case B: Summary JSON (BacktestAnalysis-like) saved earlier
                    roi_percentage = float(data.get('roi_percentage', 0.0))
                    win_rate = float(data.get('win_rate', 0.0))
                    total_trades = int(data.get('total_trades', 0))
                    max_drawdown = float(data.get('max_drawdown', 0.0))
                    realized_profits = float(data.get('realized_profits_usdt', 0.0))
                    starting_balance = float(data.get('starting_balance', 10000.0))
                    final_balance = float(data.get('final_balance', starting_balance + realized_profits))
                    peak_balance = max(starting_balance, final_balance)
                    script_name = data.get('script_name') or data.get('ScriptName') or 'Unknown Strategy'
                    market_tag = data.get('market_tag') or data.get('PriceMarket') or 'UNKNOWN'
                
                # Extract generation and population from backtest ID or other sources
                generation_idx, population_idx = self._extract_generation_population(backtest_id, data)
                
                performance = BacktestPerformance(
                    backtest_id=backtest_id,
                    lab_id=lab_id,
                    generation_idx=generation_idx,
                    population_idx=population_idx,
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
                
                performances.append(performance)
                
            except Exception as e:
                logger.warning(f"Error extracting data from {file_path.name}: {e}")
                continue
        
        # Sort by ROE (Return on Equity) - calculated as realized_profits / starting_balance
        performances.sort(key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
        
        # Return top performers
        return performances[:top_count]
    
    def _extract_generation_population(self, backtest_id: str, data: Dict[str, Any]) -> tuple[int, int]:
        """Extract generation and population from backtest ID or data"""
        generation_idx = 0
        population_idx = 0
        
        # First, try to get from existing CSV reports
        csv_data = self._get_generation_population_from_csv(backtest_id)
        if csv_data:
            return csv_data
        
        # Try to extract from backtest ID pattern
        # Common patterns: generation_population or gen_pop
        if '_' in backtest_id:
            parts = backtest_id.split('_')
            if len(parts) >= 2:
                try:
                    # Try to extract numbers from the parts
                    for part in parts:
                        if part.isdigit():
                            if generation_idx == 0:
                                generation_idx = int(part)
                            elif population_idx == 0:
                                population_idx = int(part)
                                break
                except ValueError:
                    pass
        
        # Try to extract from other fields in the data
        if generation_idx == 0 or population_idx == 0:
            # Check if there are any fields that might contain generation/population
            for key, value in data.items():
                if 'gen' in key.lower() and isinstance(value, (int, float)):
                    generation_idx = int(value)
                elif 'pop' in key.lower() and isinstance(value, (int, float)):
                    population_idx = int(value)
        
        # If still not found, try to extract from ScriptMemory or LocalMemory
        if generation_idx == 0 or population_idx == 0:
            script_memory = data.get('ScriptMemory', {})
            local_memory = data.get('LocalMemory', {})
            
            # Look for generation/population in memory
            for memory in [script_memory, local_memory]:
                if isinstance(memory, dict):
                    for key, value in memory.items():
                        if 'gen' in key.lower() and isinstance(value, (int, float)):
                            generation_idx = int(value)
                        elif 'pop' in key.lower() and isinstance(value, (int, float)):
                            population_idx = int(value)
        
        # If still not found, try to extract from backtest ID using different patterns
        if generation_idx == 0 or population_idx == 0:
            # Try to extract from UUID-like patterns
            # Some backtest IDs might have generation/population embedded
            import re
            
            # Look for patterns like "gen123pop456" or "123_456"
            gen_pop_pattern = r'gen(\d+)pop(\d+)'
            match = re.search(gen_pop_pattern, backtest_id, re.IGNORECASE)
            if match:
                generation_idx = int(match.group(1))
                population_idx = int(match.group(2))
            
            # Look for patterns like "123_456" in the ID
            if generation_idx == 0 or population_idx == 0:
                number_pattern = r'(\d+)_(\d+)'
                match = re.search(number_pattern, backtest_id)
                if match:
                    generation_idx = int(match.group(1))
                    population_idx = int(match.group(2))
        
        return generation_idx, population_idx
    
    def _extract_parameter_values(self, lab_id: str, backtest_id: str) -> Dict[str, str]:
        """Extract parameter values from cached backtest data"""
        try:
            cache_path = self.cache.get_backtest_cache_path(lab_id, backtest_id)
            if not cache_path.exists():
                return {}
            
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            input_fields = data.get('InputFields', {})
            parameters = {}
            
            # Extract key parameters (filter out non-optimizable ones)
            for key, field in input_fields.items():
                param_name = field.get('N', '')  # Parameter name
                param_value = field.get('V', '')  # Parameter value
                
                # Skip system parameters and focus on optimizable ones
                if param_name and param_value and not any(skip in param_name.lower() for skip in 
                    ['trade amount', 'order size', 'entry order type', 'colldown', 'reset']):
                    # Clean up parameter name
                    clean_name = param_name.replace('TP ', 'Take Profit ').replace('SL ', 'Stop Loss ').replace('pct', '%')
                    parameters[clean_name] = param_value
            
            return parameters
            
        except Exception as e:
            logger.debug(f"Could not extract parameters for {backtest_id[:8]}: {e}")
            return {}
    
    def _get_generation_population_from_csv(self, backtest_id: str) -> Optional[tuple[int, int]]:
        """Get generation and population from existing CSV reports"""
        try:
            import csv
            reports_dir = Path("unified_cache/reports/")
            
            if not reports_dir.exists():
                return None
            
            # Look for CSV files that might contain this backtest
            for csv_file in reports_dir.glob("lab_analysis_*.csv"):
                try:
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row.get('Backtest ID') == backtest_id:
                                generation = int(row.get('Generation', 0))
                                population = int(row.get('Population', 0))
                                if generation > 0 or population > 0:
                                    return (generation, population)
                except Exception:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _get_all_csv_data_for_lab(self, lab_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all CSV data for a lab to use as lookup table"""
        csv_data = {}
        try:
            import csv
            reports_dir = Path("unified_cache/reports/")
            
            if not reports_dir.exists():
                return csv_data
            
            # Look for CSV files for this specific lab
            pattern = f"lab_analysis_{lab_id}_*.csv"
            for csv_file in reports_dir.glob(pattern):
                try:
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            backtest_id = row.get('Backtest ID', '')
                            if backtest_id:
                                # Win rate is already in percentage format in CSV
                                win_rate = float(row.get('Win Rate %', 0))
                                
                                csv_data[backtest_id] = {
                                    'generation': int(row.get('Generation', 0)),
                                    'population': int(row.get('Population', 0)),
                                    'roi_percentage': float(row.get('Lab ROI %', 0)),
                                    'win_rate': win_rate,
                                    'total_trades': int(row.get('Total Trades', 0)),
                                    'max_drawdown': float(row.get('Max Drawdown %', 0)),
                                    'realized_profits_usdt': float(row.get('Realized Profits USDT', 0)),
                                    'starting_balance': float(row.get('Starting Balance USDT', 10000)),
                                    'final_balance': float(row.get('Final Balance USDT', 10000)),
                                    'script_name': row.get('Script Name', 'Unknown Script'),
                                    'market_tag': row.get('Market', 'UNKNOWN')
                                }
                except Exception as e:
                    logger.warning(f"Error reading CSV file {csv_file}: {e}")
                    continue
            
            # If no specific lab CSV found, check all CSV files
            if not csv_data:
                for csv_file in reports_dir.glob("lab_analysis_*.csv"):
                    try:
                        with open(csv_file, 'r') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                if row.get('Lab ID') == lab_id:
                                    backtest_id = row.get('Backtest ID', '')
                                    if backtest_id:
                                        # Win rate is already in percentage format in CSV
                                        win_rate = float(row.get('Win Rate %', 0))
                                        
                                        csv_data[backtest_id] = {
                                            'generation': int(row.get('Generation', 0)),
                                            'population': int(row.get('Population', 0)),
                                            'roi_percentage': float(row.get('Lab ROI %', 0)),
                                            'win_rate': win_rate,
                                            'total_trades': int(row.get('Total Trades', 0)),
                                            'max_drawdown': float(row.get('Max Drawdown %', 0)),
                                            'realized_profits_usdt': float(row.get('Realized Profits USDT', 0)),
                                            'starting_balance': float(row.get('Starting Balance USDT', 10000)),
                                            'final_balance': float(row.get('Final Balance USDT', 10000)),
                                            'script_name': row.get('Script Name', 'Unknown Script'),
                                            'market_tag': row.get('Market', 'UNKNOWN')
                                        }
                    except Exception as e:
                        logger.warning(f"Error reading CSV file {csv_file}: {e}")
                        continue
            
            logger.info(f"Found {len(csv_data)} backtests in CSV data for lab {lab_id[:8]}")
            return csv_data
            
        except Exception as e:
            logger.warning(f"Error getting CSV data: {e}")
            return {}
    
    def _create_analysis_result(self, lab_id: str, performances: List[Any]) -> Any:
        """Create analysis result object compatible with existing CLI"""
        from types import SimpleNamespace
        
        # Convert performances to BacktestAnalysis objects
        backtests = []
        for perf in performances:
            from pyHaasAPI_v1.analysis.models import BacktestAnalysis
            backtest = BacktestAnalysis(
                backtest_id=perf.backtest_id,
                lab_id=perf.lab_id,
                generation_idx=perf.generation_idx,
                population_idx=perf.population_idx,
                market_tag=perf.market_tag,
                script_id='',
                script_name=perf.script_name,
                roi_percentage=perf.roi_percentage,
                calculated_roi_percentage=perf.roi_percentage,
                roi_difference=0.0,
                win_rate=perf.win_rate,
                total_trades=perf.total_trades,
                max_drawdown=perf.max_drawdown,
                realized_profits_usdt=perf.realized_profits_usdt,
                pc_value=0.0,
                avg_profit_per_trade=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                starting_balance=perf.starting_balance,
                final_balance=perf.final_balance,
                peak_balance=perf.peak_balance,
                analysis_timestamp='',
                parameter_values=getattr(perf, 'parameter_values', None)
            )
            backtests.append(backtest)
        
        # Create result object
        result = SimpleNamespace()
        result.lab_id = lab_id
        result.top_backtests = backtests
        result.total_backtests = len(performances)
        
        return result
    
    def analyze_all_cached_labs(self, lab_ids: List[str] = None, top_count: int = 10,
                              sort_by: str = 'roi', save_results: bool = False) -> Dict[str, Any]:
        """Analyze all cached labs and return combined results"""
        logger.info("🚀 Starting analysis of cached lab data...")
        self.start_time = time.time()
        
        # Get cached labs
        if lab_ids:
            cached_labs = lab_ids
        else:
            cached_labs_dict = self.get_cached_labs()
            cached_labs = list(cached_labs_dict.keys())
        
        if not cached_labs:
            logger.warning("⚠️ No cached lab data found")
            return {
                "total_labs": 0,
                "total_backtests": 0,
                "top_backtests": [],
                "processing_time": 0.0
            }
        
        logger.info(f"📋 Found {len(cached_labs)} labs with cached data")
        
        all_backtests = []
        successful_analyses = 0
        failed_analyses = 0
        lab_results = []
        
        # Analyze each lab
        for i, lab_id in enumerate(cached_labs):
            logger.info(f"📊 Analyzing lab {i+1}/{len(cached_labs)}: {lab_id[:8]}")
            
            result = self.analyze_cached_lab(lab_id, top_count)
            
            if result:
                successful_analyses += 1
                all_backtests.extend(result.top_backtests)
                lab_results.append(result)
                
                # Save individual lab result if requested
                if save_results:
                    result_path = self.cache.save_analysis_result(result)
                    logger.info(f"💾 Saved analysis result: {result_path.name}")
            else:
                failed_analyses += 1
        
        # Sort all backtests by specified metric
        sorted_backtests = self._sort_backtests(all_backtests, sort_by)
        
        # Calculate processing time
        processing_time = time.time() - self.start_time
        
        # Print detailed results
        self.print_detailed_results(sorted_backtests, top_count, sort_by)
        
        # Print summary
        self.print_summary({
            "total_labs": len(cached_labs),
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "total_backtests": len(all_backtests),
            "top_backtests": sorted_backtests[:top_count],
            "processing_time": processing_time,
            "lab_results": lab_results
        })
        
        return {
            "total_labs": len(cached_labs),
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "total_backtests": len(all_backtests),
            "top_backtests": sorted_backtests[:top_count],
            "processing_time": processing_time,
            "lab_results": lab_results
        }
    
    def _sort_backtests(self, backtests: List[BacktestAnalysis], sort_by: str) -> List[BacktestAnalysis]:
        """Sort backtests by specified metric"""
        if sort_by.lower() == 'roe':
            # Calculate ROE (Return on Equity) - using realized profits / starting balance
            return sorted(backtests, key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
        elif sort_by.lower() == 'roi':
            return sorted(backtests, key=lambda x: x.roi_percentage, reverse=True)
        elif sort_by.lower() == 'winrate':
            return sorted(backtests, key=lambda x: x.win_rate, reverse=True)
        elif sort_by.lower() == 'profit':
            return sorted(backtests, key=lambda x: x.realized_profits_usdt, reverse=True)
        elif sort_by.lower() == 'trades':
            return sorted(backtests, key=lambda x: x.total_trades, reverse=True)
        else:
            # Default to ROE sorting
            return sorted(backtests, key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
    
    def print_detailed_results(self, backtests: List[BacktestAnalysis], top_count: int, sort_by: str):
        """Print detailed results in a formatted table with lab name and copy-paste friendly format"""
        if not backtests:
            logger.info("❌ No backtests to display")
            return
            
        # Get lab name from first backtest
        lab_id = backtests[0].lab_id
        lab_name = self.get_full_lab_name(lab_id)
        
        logger.info("=" * 140)
        logger.info(f"🏆 LAB ANALYSIS: {lab_name}")
        logger.info(f"📊 Lab ID: {lab_id}")
        logger.info(f"🎯 TOP {min(top_count, len(backtests))} BACKTESTS (Sorted by {sort_by.upper()})")
        logger.info("=" * 140)
        
        # Header
        header = f"{'#':<3} {'Gen/Pop':<8} {'ROI%':<8} {'ROE%':<8} {'Max DD USDT':<10} {'Win Rate':<8} {'Trades':<6} {'Start Bal':<10} {'Final Bal':<10} {'Script':<25}"
        logger.info(header)
        logger.info("-" * 140)
        
        # Data rows
        for i, bt in enumerate(backtests[:top_count], 1):
            roe = (bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100
            gen_pop = f"{bt.generation_idx}/{bt.population_idx}"
            
            # Calculate max DD in USDT
            max_dd_usdt = (bt.max_drawdown / 100) * bt.starting_balance
            
            row = f"{i:<3} {gen_pop:<8} {bt.roi_percentage:<8.1f} {roe:<8.1f} {max_dd_usdt:<10.0f} {bt.win_rate:<8.1f} {bt.total_trades:<6} {bt.starting_balance:<10.0f} {bt.final_balance:<10.0f} {bt.script_name[:25]:<25}"
            logger.info(row)
        
        # Copy-paste friendly format
        logger.info("\n" + "=" * 140)
        logger.info("📋 COPY-PASTE FRIENDLY FORMAT")
        logger.info("=" * 140)
        
        # Print headers once
        logger.info("Gen/Pop | ROE% | ROI% | Max DD USDT | WR% | Trades | Script")
        logger.info("-" * 80)
        
        for i, bt in enumerate(backtests[:top_count], 1):
            roe = (bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100
            gen_pop = f"{bt.generation_idx}/{bt.population_idx}"
            
            # Calculate max DD in USDT
            max_dd_usdt = (bt.max_drawdown / 100) * bt.starting_balance
            
            # Simple line format for easy copying
            line = f"{gen_pop} | {roe:.1f}% | {bt.roi_percentage:.1f}% | {max_dd_usdt:.0f} | {bt.win_rate:.1f}% | {bt.total_trades} | {bt.script_name}"
            logger.info(line)
    
    def print_summary(self, result: Dict[str, Any]):
        """Print comprehensive analysis summary with lab and bot statistics"""
        logger.info("=" * 80)
        logger.info("📊 COMPREHENSIVE ANALYSIS SUMMARY")
        logger.info("=" * 80)
        
        # Basic statistics
        logger.info(f"Total Labs Analyzed: {result['total_labs']}")
        logger.info(f"Successful Analyses: {result['successful_analyses']}")
        logger.info(f"Failed Analyses: {result['failed_analyses']}")
        logger.info(f"Total Backtests Found: {result['total_backtests']}")
        logger.info(f"Processing Time: {result['processing_time']:.2f} seconds")
        
        if result['top_backtests']:
            backtests = result['top_backtests']
            
            # Calculate comprehensive statistics
            roes = [(bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100 for bt in backtests]
            rois = [bt.roi_percentage for bt in backtests]
            win_rates = [bt.win_rate for bt in backtests]
            max_drawdowns = [bt.max_drawdown for bt in backtests]
            max_dd_usdt = [(bt.max_drawdown / 100) * bt.starting_balance for bt in backtests]
            trades = [bt.total_trades for bt in backtests]
            
            # Best backtest
            best = backtests[0]
            best_roe = roes[0]
            
            logger.info("\n" + "=" * 80)
            logger.info("🏆 BEST PERFORMING BOT")
            logger.info("=" * 80)
            logger.info(f"Backtest ID: {best.backtest_id}")
            logger.info(f"Generation/Population: {best.generation_idx}/{best.population_idx}")
            best_max_dd_usdt = (best.max_drawdown / 100) * best.starting_balance
            logger.info(f"ROE: {best_roe:.1f}% | ROI: {best.roi_percentage:.1f}% | Max DD: {best_max_dd_usdt:.0f} USDT")
            logger.info(f"Win Rate: {best.win_rate:.1f}% | Trades: {best.total_trades}")
            logger.info(f"Script: {best.script_name}")
            logger.info(f"Market: {best.market_tag}")
            
            # Display parameter values if available
            if hasattr(best, 'parameter_values') and best.parameter_values and len(best.parameter_values) > 0:
                logger.info("\n" + "=" * 80)
                logger.info("🔧 OPTIMIZED PARAMETERS")
                logger.info("=" * 80)
                for param_name, param_value in best.parameter_values.items():
                    logger.info(f"{param_name}: {param_value}")
            else:
                logger.info("\n🔧 Parameters: Not available")
            
            # Lab statistics
            logger.info("\n" + "=" * 80)
            logger.info("📈 LAB PERFORMANCE STATISTICS")
            logger.info("=" * 80)
            logger.info(f"ROE Range: {min(roes):.1f}% - {max(roes):.1f}% (Avg: {sum(roes)/len(roes):.1f}%)")
            logger.info(f"ROI Range: {min(rois):.1f}% - {max(rois):.1f}% (Avg: {sum(rois)/len(rois):.1f}%)")
            logger.info(f"Win Rate Range: {min(win_rates):.1f}% - {max(win_rates):.1f}% (Avg: {sum(win_rates)/len(win_rates):.1f}%)")
            logger.info(f"Max Drawdown Range: {min(max_dd_usdt):.0f} - {max(max_dd_usdt):.0f} USDT (Avg: {sum(max_dd_usdt)/len(max_dd_usdt):.0f} USDT)")
            logger.info(f"Trades Range: {min(trades)} - {max(trades)} (Avg: {sum(trades)/len(trades):.0f})")
            
            # Risk assessment
            logger.info("\n" + "=" * 80)
            logger.info("⚠️ RISK ASSESSMENT")
            logger.info("=" * 80)
            high_roe_bots = len([roe for roe in roes if roe > 50])
            low_dd_bots = len([dd for dd in max_drawdowns if dd < 10])
            high_wr_bots = len([wr for wr in win_rates if wr > 60])
            
            logger.info(f"High ROE Bots (>50%): {high_roe_bots}/{len(backtests)} ({high_roe_bots/len(backtests)*100:.1f}%)")
            logger.info(f"Low Drawdown Bots (<10%): {low_dd_bots}/{len(backtests)} ({low_dd_bots/len(backtests)*100:.1f}%)")
            logger.info(f"High Win Rate Bots (>60%): {high_wr_bots}/{len(backtests)} ({high_wr_bots/len(backtests)*100:.1f}%)")
            
            # Copy-paste friendly summary
            logger.info("\n" + "=" * 80)
            logger.info("📋 COPY-PASTE FRIENDLY SUMMARY")
            logger.info("=" * 80)
            lab_name = self.get_full_lab_name(best.lab_id)
            logger.info(f"Lab: {lab_name}")
            logger.info(f"Lab ID: {best.lab_id}")
            logger.info(f"Total Bots: {len(backtests)}")
            logger.info(f"Best Bot: Gen/Pop {best.generation_idx}/{best.population_idx} | ROE {best_roe:.1f}% | ROI {best.roi_percentage:.1f}% | Max DD {best_max_dd_usdt:.0f} USDT | WR {best.win_rate:.1f}%")
            logger.info(f"Lab Stats: ROE {min(roes):.1f}-{max(roes):.1f}% | WR {min(win_rates):.1f}-{max(win_rates):.1f}% | Max DD {min(max_dd_usdt):.0f}-{max(max_dd_usdt):.0f} USDT")
            
            # Add parameter values to copy-paste summary
            if hasattr(best, 'parameter_values') and best.parameter_values and len(best.parameter_values) > 0:
                logger.info("\n🔧 Best Bot Parameters:")
                param_line = " | ".join([f"{name}: {value}" for name, value in best.parameter_values.items()])
                logger.info(param_line)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Analysis completed successfully!")
        logger.info("💡 Use --save-results to save analysis for later bot creation")
    
    def get_lab_names_from_csv(self) -> Dict[str, str]:
        """Extract lab names from existing CSV reports"""
        lab_names = {}
        reports_dir = Path("unified_cache/reports/")
        
        if not reports_dir.exists():
            return lab_names
            
        for csv_file in reports_dir.glob("lab_analysis_*.csv"):
            try:
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        lab_id = row.get('Lab ID', '')
                        lab_name = row.get('Lab Name', '')
                        if lab_id and lab_name and lab_id not in lab_names:
                            lab_names[lab_id] = lab_name
            except Exception as e:
                logger.warning(f"Error reading CSV file {csv_file}: {e}")
                continue
                
        return lab_names

    def get_full_lab_name(self, lab_id: str) -> str:
        """Get full lab name from CSV reports or cached data or generate descriptive name"""
        # First try to get from CSV reports
        lab_names = self.get_lab_names_from_csv()
        if lab_id in lab_names and lab_names[lab_id]:
            return lab_names[lab_id]
        
        # Fallback: try to get lab name from cached data
        try:
            cache_dir = Path("unified_cache/backtests")
            if cache_dir.exists():
                # Look for any cached file for this lab to extract lab name
                pattern = f"{lab_id}_*.json"
                cached_files = list(cache_dir.glob(pattern))
                
                if cached_files:
                    # Try to read the first file to get lab name
                    with open(cached_files[0], 'r') as f:
                        data = json.load(f)
                    
                    # Look for lab name in various possible fields
                    lab_name = (data.get('LabName') or 
                               data.get('lab_name') or 
                               data.get('Name') or
                               data.get('name') or
                               data.get('RuntimeData', {}).get('LabName') or
                               data.get('runtime_data', {}).get('LabName'))
                    
                    if lab_name:
                        return lab_name
        except Exception as e:
            logger.debug(f"Could not extract lab name for {lab_id}: {e}")
        
        # Fallback: try API even if analyzer is not set (lazy connect for names only)
        try:
            executor = None
            if self.analyzer and getattr(self.analyzer, 'executor', None):
                executor = self.analyzer.executor
            else:
                # Lazy connect just to resolve name
                tmp_analyzer = HaasAnalyzer(self.cache)
                if tmp_analyzer.connect():
                    executor = tmp_analyzer.executor
            if executor:
                from pyHaasAPI_v1 import api
                details = api.get_lab_details(executor, lab_id)
                lab_name = getattr(details, 'name', None) or getattr(details, 'Name', None)
                if lab_name:
                    return lab_name
        except Exception:
            pass

        # Final fallback to descriptive name
        return f"Lab {lab_id[:8]}"
    
    def generate_lab_analysis_reports(self, lab_results: List[Any], criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate short analysis reports for each lab with specific criteria"""
        
        if criteria is None:
            criteria = {
                'min_roe': 0,
                'max_roe': None,
                'min_winrate': 30,  # More realistic for actual data
                'max_winrate': None,
                'min_trades': 5,    # Much more realistic for actual data
                'max_trades': None
            }
        
        reports = {}
        
        for lab_result in lab_results:
            lab_id = lab_result.lab_id
            full_lab_name = self.get_full_lab_name(lab_id)
            
            # Filter backtests by criteria
            qualifying_bots = []
            for backtest in lab_result.top_backtests:
                roe = (backtest.realized_profits_usdt / max(backtest.starting_balance, 1)) * 100
                win_rate = backtest.win_rate  # win_rate is already a percentage (0-100)
                trades = backtest.total_trades
                
                if (roe >= criteria['min_roe'] and
                    (criteria['max_roe'] is None or roe <= criteria['max_roe']) and
                    win_rate >= criteria['min_winrate'] and
                    (criteria['max_winrate'] is None or win_rate <= criteria['max_winrate']) and
                    trades >= criteria['min_trades'] and
                    (criteria['max_trades'] is None or trades <= criteria['max_trades'])):
                    
                    qualifying_bots.append({
                        'strategy_name': backtest.script_name,
                        'trading_pair': backtest.market_tag,
                        'roe_range': f"{roe:.1f}%",
                        'win_rate': f"{win_rate:.1f}%",
                        'trades': trades,
                        'generation_population': f"{backtest.generation_idx}/{backtest.population_idx}" if hasattr(backtest, 'generation_idx') else "N/A"
                    })
            
            # Generate report for this lab
            if qualifying_bots:
                # Group by strategy and trading pair
                strategy_groups = {}
                for bot in qualifying_bots:
                    key = f"{bot['strategy_name']} - {bot['trading_pair']}"
                    if key not in strategy_groups:
                        strategy_groups[key] = {
                            'strategy_name': bot['strategy_name'],
                            'trading_pair': bot['trading_pair'],
                            'bots': [],
                            'roe_min': float('inf'),
                            'roe_max': 0,
                            'winrate_min': float('inf'),
                            'winrate_max': 0,
                            'trades_min': float('inf'),
                            'trades_max': 0
                        }
                    
                    strategy_groups[key]['bots'].append(bot)
                    roe_val = float(bot['roe_range'].replace('%', ''))
                    winrate_val = float(bot['win_rate'].replace('%', ''))
                    
                    strategy_groups[key]['roe_min'] = min(strategy_groups[key]['roe_min'], roe_val)
                    strategy_groups[key]['roe_max'] = max(strategy_groups[key]['roe_max'], roe_val)
                    strategy_groups[key]['winrate_min'] = min(strategy_groups[key]['winrate_min'], winrate_val)
                    strategy_groups[key]['winrate_max'] = max(strategy_groups[key]['winrate_max'], winrate_val)
                    strategy_groups[key]['trades_min'] = min(strategy_groups[key]['trades_min'], bot['trades'])
                    strategy_groups[key]['trades_max'] = max(strategy_groups[key]['trades_max'], bot['trades'])
                
                # Create summary report
                lab_report = {
                    'lab_id': lab_id,
                    'lab_name': full_lab_name,
                    'total_qualifying_bots': len(qualifying_bots),
                    'strategy_summaries': []
                }
                
                for strategy_key, group in strategy_groups.items():
                    summary = {
                        'strategy_name': group['strategy_name'],
                        'trading_pair': group['trading_pair'],
                        'roe_range': f"{group['roe_min']:.1f}-{group['roe_max']:.1f}%",
                        'winrate_range': f"{group['winrate_min']:.0f}-{group['winrate_max']:.0f}%",
                        'trades_range': f"{group['trades_min']:.0f}-{group['trades_max']:.0f}",
                        'bot_count': len(group['bots'])
                    }
                    lab_report['strategy_summaries'].append(summary)
                
                reports[lab_id] = lab_report
        
        return reports
    
    def analyze_data_distribution(self, lab_results: List[Any]) -> Dict[str, Any]:
        """Analyze the distribution of data across all labs to help users understand their data"""
        all_roes = []
        all_winrates = []
        all_trades = []
        
        for lab_result in lab_results:
            for backtest in lab_result.top_backtests:
                roe = (backtest.realized_profits_usdt / max(backtest.starting_balance, 1)) * 100
                all_roes.append(roe)
                all_winrates.append(backtest.win_rate)
                all_trades.append(backtest.total_trades)
        
        if not all_roes:
            return {}
        
        return {
            'total_backtests': len(all_roes),
            'roe_stats': {
                'min': min(all_roes),
                'max': max(all_roes),
                'avg': sum(all_roes) / len(all_roes),
                'median': sorted(all_roes)[len(all_roes) // 2]
            },
            'winrate_stats': {
                'min': min(all_winrates),
                'max': max(all_winrates),
                'avg': sum(all_winrates) / len(all_winrates),
                'median': sorted(all_winrates)[len(all_winrates) // 2]
            },
            'trades_stats': {
                'min': min(all_trades),
                'max': max(all_trades),
                'avg': sum(all_trades) / len(all_trades),
                'median': sorted(all_trades)[len(all_trades) // 2]
            }
        }
    
    def print_data_distribution(self, distribution: Dict[str, Any]):
        """Print data distribution analysis"""
        if not distribution:
            return
            
        print(f"\n{'='*80}")
        print(f"DATA DISTRIBUTION ANALYSIS")
        print(f"{'='*80}")
        print(f"Total Backtests Analyzed: {distribution['total_backtests']}")
        print(f"{'='*80}")
        
        # ROE distribution
        roe_stats = distribution['roe_stats']
        print(f"📈 ROE Distribution:")
        print(f"   Range: {roe_stats['min']:.1f}% - {roe_stats['max']:.1f}%")
        print(f"   Average: {roe_stats['avg']:.1f}%")
        print(f"   Median: {roe_stats['median']:.1f}%")
        
        # Win Rate distribution
        wr_stats = distribution['winrate_stats']
        print(f"🎯 Win Rate Distribution:")
        print(f"   Range: {wr_stats['min']:.1f}% - {wr_stats['max']:.1f}%")
        print(f"   Average: {wr_stats['avg']:.1f}%")
        print(f"   Median: {wr_stats['median']:.1f}%")
        
        # Trades distribution
        trades_stats = distribution['trades_stats']
        print(f"📊 Trades Distribution:")
        print(f"   Range: {trades_stats['min']} - {trades_stats['max']}")
        print(f"   Average: {trades_stats['avg']:.1f}")
        print(f"   Median: {trades_stats['median']}")
        
        print(f"{'='*80}")
    
    def print_lab_analysis_reports(self, reports: Dict[str, Any], criteria: Dict[str, Any] = None):
        """Print the lab analysis reports in the requested format"""
        
        # Format criteria for display
        if criteria is None:
            criteria = {
                'min_roe': 0,
                'max_roe': None,
                'min_winrate': 30,  # More realistic for actual data
                'max_winrate': None,
                'min_trades': 5,    # Much more realistic for actual data
                'max_trades': None
            }
        
        roe_range = f"{criteria['min_roe']}-{criteria['max_roe'] if criteria['max_roe'] else '∞'}%"
        wr_range = f"{criteria['min_winrate']}-{criteria['max_winrate'] if criteria['max_winrate'] else '∞'}%"
        trades_range = f"{criteria['min_trades']}-{criteria['max_trades'] if criteria['max_trades'] else '∞'}"
        
        print(f"\n{'='*120}")
        print(f"LAB ANALYSIS REPORTS - QUALIFYING BOTS")
        print(f"{'='*120}")
        print(f"Criteria: ROE: {roe_range}, WR: {wr_range}, Trades: {trades_range}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*120}")
        
        if not reports:
            print("❌ No labs found with qualifying bots")
            return
        
        for lab_id, report in reports.items():
            print(f"\n📊 {report['lab_name']} ({lab_id[:8]})")
            print(f"   Total Qualifying Bots: {report['total_qualifying_bots']}")
            print(f"   {'-'*80}")
            
            for summary in report['strategy_summaries']:
                print(f"   🤖 {summary['strategy_name']}")
                print(f"      Trading Pair: {summary['trading_pair']}")
                print(f"      ROE: {summary['roe_range']}")
                print(f"      WR: {summary['winrate_range']}")
                print(f"      Trades: {summary['trades_range']}")
                print(f"      Bots: {summary['bot_count']}")
                print()
    
    def print_concise_lab_reports(self, reports: Dict[str, Any]):
        """Print concise lab reports in the exact format requested"""
        
        print(f"\n{'='*100}")
        print(f"CONCISE LAB ANALYSIS REPORTS")
        print(f"{'='*100}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*100}")
        
        if not reports:
            print("❌ No labs found with qualifying bots")
            return
        
        for lab_id, report in reports.items():
            print(f"\n📊 {report['lab_name']}")
            
            for summary in report['strategy_summaries']:
                print(f"   {summary['strategy_name']}")
                print(f"      Trading Pair: {summary['trading_pair']}")
                print(f"      ROE: {summary['roe_range']}")
                print(f"      WR: {summary['winrate_range']}")
                print(f"      Trades: {summary['trades_range']}")
                print(f"      Bots: {summary['bot_count']} qualifying bots")
                print()
        
        # Summary statistics
        total_labs = len(reports)
        total_bots = sum(report['total_qualifying_bots'] for report in reports.values())
        total_strategies = sum(len(report['strategy_summaries']) for report in reports.values())
        
        print(f"{'='*100}")
        print(f"SUMMARY: {total_labs} labs, {total_bots} qualifying bots, {total_strategies} unique strategies")
        print(f"{'='*100}")
    
    def print_detailed_lab_reports(self, lab_results: List[Any], top_count: int = 10):
        """Print detailed per-lab report with lab name, stats, and top bots incl. UIDs and ROI ranges"""
        if not lab_results:
            print("❌ No labs to report")
            return
        
        print(f"\n{'='*140}")
        print("DETAILED LAB REPORTS")
        print(f"{'='*140}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*140}")
        
        for lab in lab_results:
            lab_id = lab.lab_id
            lab_name = self.get_full_lab_name(lab_id)
            backtests = lab.top_backtests or []
            
            # Compute lab-level ranges
            roes = [(bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100 for bt in backtests]
            rois = [bt.roi_percentage for bt in backtests]
            wrs = [bt.win_rate for bt in backtests]
            trades = [bt.total_trades for bt in backtests]
            
            print(f"\n📊 {lab_name} ({lab_id})")
            if backtests:
                print(f"   Stats:")
                print(f"     ROE: {min(roes):.1f}-{max(roes):.1f}%")
                print(f"     ROI: {min(rois):.1f}-{max(rois):.1f}%")
                print(f"     WR: {min(wrs):.1f}-{max(wrs):.1f}%")
                print(f"     Trades: {min(trades)}-{max(trades)}")
            else:
                print("   Stats: No backtests found")
            
            # Top bots list
            print("   Top Bots:")
            if not backtests:
                print("     (none)")
                continue
            
            # Sort by ROE (default) for display
            sorted_bts = sorted(
                backtests,
                key=lambda bt: (bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100,
                reverse=True,
            )
            
            for i, bt in enumerate(sorted_bts[:top_count], 1):
                roe = (bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100
                gen_pop = f"{bt.generation_idx}/{bt.population_idx}"
                print(
                    f"     {i}. {bt.backtest_id} | Gen/Pop {gen_pop} | ROE {roe:.1f}% | ROI {bt.roi_percentage:.1f}% | WR {bt.win_rate:.1f}% | Trades {bt.total_trades}"
                )

    def print_strategy_grouped_report(self, lab_results: List[Any]):
        """Group labs by strategy name, print strategy once, then list labs with IDs and aggregate stats"""
        if not lab_results:
            print("❌ No labs to report")
            return
        
        # Build per-lab aggregates and strategy grouping
        strategy_to_labs: Dict[str, List[Dict[str, Any]]] = {}
        
        for lab in lab_results:
            lab_id = lab.lab_id
            lab_name = self.get_full_lab_name(lab_id)
            backtests = lab.top_backtests or []
            if not backtests:
                continue
            
            # Determine strategy name (use most common script among backtests)
            from collections import Counter
            script_counts = Counter([bt.script_name or 'Unknown Strategy' for bt in backtests])
            strategy_name, _ = script_counts.most_common(1)[0]
            
            # Compute aggregates
            roes = [(bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100 for bt in backtests]
            rois = [bt.roi_percentage for bt in backtests]
            wrs = [bt.win_rate for bt in backtests]
            trades = [bt.total_trades for bt in backtests]
            
            lab_entry = {
                'lab_id': lab_id,
                'lab_name': lab_name,
                'roe_min': min(roes), 'roe_max': max(roes),
                'roi_min': min(rois), 'roi_max': max(rois),
                'wr_min': min(wrs), 'wr_max': max(wrs),
                'tr_min': min(trades), 'tr_max': max(trades),
                'count': len(backtests)
            }
            strategy_to_labs.setdefault(strategy_name, []).append(lab_entry)
        
        # Print grouped report
        print(f"\n{'='*140}")
        print("STRATEGY-GROUPED LAB REPORT")
        print(f"{'='*140}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*140}")
        
        for strategy_name in sorted(strategy_to_labs.keys()):
            labs = strategy_to_labs[strategy_name]
            # Strategy-level aggregates
            total_bots = sum(l['count'] for l in labs)
            print(f"\n🎯 {strategy_name}  (labs: {len(labs)}, backtests: {total_bots})")
            print("   Labs:")
            for l in labs:
                print(
                    f"     - {l['lab_name']} ({l['lab_id']}) | ROE {l['roe_min']:.1f}-{l['roe_max']:.1f}% | ROI {l['roi_min']:.1f}-{l['roi_max']:.1f}% | WR {l['wr_min']:.1f}-{l['wr_max']:.1f}% | Trades {l['tr_min']}-{l['tr_max']} | Backtests {l['count']}"
                )
    
    def save_lab_analysis_reports(self, reports: Dict[str, Any], filename: str = None, output_format: str = 'json') -> str:
        """Save lab analysis reports to file in specified format"""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"lab_analysis_reports_{timestamp}.{output_format}"
        
        if output_format == 'json':
            # Convert to JSON-serializable format
            json_reports = {}
            for lab_id, report in reports.items():
                json_reports[lab_id] = {
                    'lab_id': report['lab_id'],
                    'lab_name': report['lab_name'],
                    'total_qualifying_bots': report['total_qualifying_bots'],
                    'strategy_summaries': report['strategy_summaries']
                }
            
            with open(filename, 'w') as f:
                json.dump(json_reports, f, indent=2)
        
        elif output_format == 'csv':
            # Convert to CSV format
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['Lab ID', 'Lab Name', 'Strategy Name', 'Trading Pair', 'ROE Range', 'WR Range', 'Trades Range', 'Bot Count'])
                
                # Write data rows
                for lab_id, report in reports.items():
                    for summary in report['strategy_summaries']:
                        writer.writerow([
                            report['lab_id'],
                            report['lab_name'],
                            summary['strategy_name'],
                            summary['trading_pair'],
                            summary['roe_range'],
                            summary['winrate_range'],
                            summary['trades_range'],
                            summary['bot_count']
                        ])
        
        elif output_format == 'markdown':
            # Convert to Markdown format
            with open(filename, 'w') as f:
                f.write("# Lab Analysis Reports\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for lab_id, report in reports.items():
                    f.write(f"## {report['lab_name']}\n")
                    f.write(f"**Lab ID**: {report['lab_id']}\n")
                    f.write(f"**Total Qualifying Bots**: {report['total_qualifying_bots']}\n\n")
                    
                    for summary in report['strategy_summaries']:
                        f.write(f"### {summary['strategy_name']}\n")
                        f.write(f"- **Trading Pair**: {summary['trading_pair']}\n")
                        f.write(f"- **ROE**: {summary['roe_range']}\n")
                        f.write(f"- **WR**: {summary['winrate_range']}\n")
                        f.write(f"- **Trades**: {summary['trades_range']}\n")
                        f.write(f"- **Bots**: {summary['bot_count']}\n\n")
                    
                    f.write("---\n\n")
        
        logger.info(f"💾 Lab analysis reports saved to: {filename}")
        return filename
    
    def generate_comprehensive_lab_summary(self, output_file: str = None) -> str:
        """Generate a comprehensive lab summary with all cached labs"""
        logger.info("📊 Generating comprehensive lab summary...")
        
        # Get all cached labs
        cached_labs = self.get_cached_labs()
        if not cached_labs:
            logger.warning("❌ No cached labs found")
            return ""
        
        # Get lab names from CSV reports
        lab_names = self.get_lab_names_from_csv()
        
        # Generate summary content
        summary_lines = []
        summary_lines.append("# 📊 COMPREHENSIVE LAB ANALYSIS SUMMARY")
        summary_lines.append("")
        summary_lines.append("## 🎯 OVERVIEW")
        summary_lines.append(f"- **Total Labs**: {len(cached_labs)}")
        summary_lines.append(f"- **Labs with Names**: {len(lab_names)}")
        summary_lines.append(f"- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        summary_lines.append("---")
        summary_lines.append("")
        summary_lines.append("## 📊 LAB SUMMARIES")
        summary_lines.append("")
        
        # Sort labs by backtest count (descending) for better organization
        sorted_labs = sorted(cached_labs.items(), key=lambda x: x[1], reverse=True)
        
        for i, (lab_id, backtest_count) in enumerate(sorted_labs, 1):
            lab_name = lab_names.get(lab_id, f"Lab {lab_id[:8]}")
            
            # Get basic info and performance metrics from cached files
            script_name = "Unknown Strategy"
            market_tag = "Unknown Market"
            roe_min, roe_max = 0, 0
            wr_min, wr_max = 0, 0
            trades_min, trades_max = 0, 0
            
            try:
                cache_dir = Path("unified_cache/backtests")
                pattern = f"{lab_id}_*.json"
                cached_files = list(cache_dir.glob(pattern))
                
                if cached_files:
                    # Get basic info from first file
                    with open(cached_files[0], 'r') as f:
                        data = json.load(f)
                        script_name = data.get('ScriptName', 'Unknown Strategy')
                        market_tag = data.get('PriceMarket', 'Unknown Market')
                    
                    # Analyze performance metrics from multiple files (sample up to 10)
                    roe_values = []
                    wr_values = []
                    trades_values = []
                    
                    sample_files = cached_files[:10]  # Sample first 10 files for performance
                    for file_path in sample_files:
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                            
                            # Extract performance data from Reports section
                            reports = data.get('Reports', {})
                            if reports:
                                report_key = list(reports.keys())[0]
                                report_data = reports[report_key]
                                
                                # Extract performance metrics
                                pr_data = report_data.get('PR', {})
                                p_data = report_data.get('P', {})
                                
                                if pr_data and p_data:
                                    # Calculate ROE (Return on Equity)
                                    starting_balance = pr_data.get('SB', 10000.0)
                                    realized_profits = pr_data.get('RP', 0.0)
                                    roe = (realized_profits / starting_balance * 100) if starting_balance > 0 else 0
                                    roe_values.append(roe)
                                    
                                    # Calculate Win Rate
                                    total_trades = p_data.get('C', 0)
                                    winning_trades = p_data.get('W', 0)
                                    wr = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                                    wr_values.append(wr)
                                    
                                    # Get trade count
                                    trades_values.append(total_trades)
                        except Exception:
                            continue
                    
                    # Calculate ranges
                    if roe_values:
                        roe_min, roe_max = min(roe_values), max(roe_values)
                    if wr_values:
                        wr_min, wr_max = min(wr_values), max(wr_values)
                    if trades_values:
                        trades_min, trades_max = min(trades_values), max(trades_values)
            except Exception:
                pass
            
            # Determine status based on backtest count
            if backtest_count >= 1000:
                status = "✅ **TOP PERFORMER** - Large dataset"
                risk_level = "LOW"
            elif backtest_count >= 100:
                status = "✅ **STRONG PERFORMER** - Good dataset"
                risk_level = "MEDIUM"
            elif backtest_count >= 50:
                status = "🔍 **NEEDS ANALYSIS** - Moderate dataset"
                risk_level = "MEDIUM"
            elif backtest_count >= 10:
                status = "⚠️ **SMALL DATASET** - Limited backtests"
                risk_level = "HIGH"
            else:
                status = "❌ **INSUFFICIENT DATA** - Very few backtests"
                risk_level = "HIGH"
            
            summary_lines.append(f"### {i}. {lab_name}")
            summary_lines.append(f"**Lab Name**: {lab_name}")
            summary_lines.append(f"**Lab ID**: {lab_id}")
            summary_lines.append(f"**Strategy Name**: {script_name}")
            summary_lines.append(f"**Trading Pair**: {market_tag}")
            
            # Add performance metrics if available
            if roe_min > 0 or roe_max > 0:
                summary_lines.append(f"**ROE**: {roe_min:.1f}-{roe_max:.1f}%")
            if wr_min > 0 or wr_max > 0:
                summary_lines.append(f"**WR**: {wr_min:.1f}-{wr_max:.1f}%")
            if trades_min > 0 or trades_max > 0:
                summary_lines.append(f"**Trades**: {trades_min}-{trades_max}")
            
            summary_lines.append(f"**Bots**: {backtest_count} qualifying backtests")
            summary_lines.append(f"**Risk Level**: {risk_level}")
            summary_lines.append(f"**Status**: {status}")
            summary_lines.append("")
            summary_lines.append("---")
            summary_lines.append("")
        
        # Add recommendations section
        summary_lines.append("## 🎯 RECOMMENDATIONS")
        summary_lines.append("")
        summary_lines.append("### 🚀 **IMMEDIATE ACTION ITEMS**")
        summary_lines.append("")
        summary_lines.append("1. **Analyze Top Performers** - Focus on labs with 100+ backtests")
        summary_lines.append("2. **Create Bot Specifications** - Generate bot creation tasks for high-performing labs")
        summary_lines.append("3. **Risk Assessment** - Review labs with sufficient data for live trading")
        summary_lines.append("")
        summary_lines.append("### 📋 **NEXT STEPS**")
        summary_lines.append("")
        summary_lines.append("1. Run detailed analysis on top-performing labs")
        summary_lines.append("2. Generate bot creation specifications")
        summary_lines.append("3. Set up individual accounts for bot deployment")
        summary_lines.append("4. Configure risk management parameters")
        summary_lines.append("")
        summary_lines.append("### ⚠️ **NOTES**")
        summary_lines.append("")
        summary_lines.append("- All labs use the same strategy: **ADX BB STOCH Scalper**")
        summary_lines.append("- Most labs focus on **GALA/USDT** and **BCH/USDT** markets")
        summary_lines.append("- Lab names extracted from existing CSV analysis reports")
        summary_lines.append("- Use `--generate-lab-reports` for detailed performance analysis")
        
        # Join all lines
        summary_content = "\n".join(summary_lines)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(summary_content)
            logger.info(f"💾 Comprehensive lab summary saved to: {output_file}")
        else:
            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"COMPREHENSIVE_LAB_SUMMARY_{timestamp}.md"
            with open(output_file, 'w') as f:
                f.write(summary_content)
            logger.info(f"💾 Comprehensive lab summary saved to: {output_file}")
        
        return output_file


def main(args=None):
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze From Cache - Analyze cached lab data with detailed results',
        epilog='''
Examples:
  # Analyze all cached labs
  python -m pyHaasAPI.cli.analyze_from_cache
  
  # Analyze specific labs
  python -m pyHaasAPI.cli.analyze_from_cache --lab-ids lab1,lab2,lab3
  
  # Sort by ROE and show top 20
  python -m pyHaasAPI.cli.analyze_from_cache --sort-by roe --top-count 20
  
  # Save results for later bot creation
  python -m pyHaasAPI.cli.analyze_from_cache --save-results --sort-by roe
  
  # Generate lab analysis reports with qualifying bots
  python -m pyHaasAPI.cli.analyze_from_cache --generate-lab-reports
  
  # Generate concise format reports (Strategy, Trading Pair, ROE, WR, Trades, Bots)
  python -m pyHaasAPI.cli.analyze_from_cache --generate-lab-reports --concise-format
  
  # Generate reports with custom criteria (only minimum filters by default)
  python -m pyHaasAPI.cli.analyze_from_cache --generate-lab-reports --min-roe 50 --min-winrate 60
  
  # Generate comprehensive lab summary with real lab names
  python -m pyHaasAPI.cli.analyze_from_cache --comprehensive-summary
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--lab-ids', nargs='+', type=str,
                       help='Analyze only specific lab IDs')
    parser.add_argument('--top-count', type=int, default=10,
                       help='Number of top backtests to show (default: 10)')
    parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate', 'profit', 'trades'], default='roe',
                       help='Sort backtests by metric (default: roe)')
    parser.add_argument('--save-results', action='store_true',
                       help='Save analysis results for later bot creation')
    parser.add_argument('--generate-lab-reports', action='store_true',
                       help='Generate lab analysis reports with qualifying bots')
    parser.add_argument('--concise-format', action='store_true',
                       help='Use concise format for lab reports (Strategy, Trading Pair, ROE, WR, Trades, Bots)')
    parser.add_argument('--comprehensive-summary', action='store_true',
                       help='Generate comprehensive lab summary with all cached labs and real lab names')
    parser.add_argument('--detailed-lab-reports', action='store_true',
                       help='Print detailed per-lab reports incl. names, stats, ROI ranges, and top bots with UIDs')
    parser.add_argument('--strategy-grouped-reports', action='store_true',
                       help='Print report grouped by strategy: per strategy show all labs with IDs and stats')
    parser.add_argument('--show-data-distribution', action='store_true',
                       help='Show data distribution analysis to help understand your data')
    parser.add_argument('--min-roe', type=float, default=0,
                       help='Minimum ROE for qualifying bots (default: 0)')
    parser.add_argument('--max-roe', type=float,
                       help='Maximum ROE for qualifying bots (no default limit)')
    parser.add_argument('--min-winrate', type=float, default=30,
                       help='Minimum win rate for qualifying bots (default: 30)')
    parser.add_argument('--max-winrate', type=float,
                       help='Maximum win rate for qualifying bots (no default limit)')
    parser.add_argument('--min-trades', type=int, default=5,
                       help='Minimum trades for qualifying bots (default: 5)')
    parser.add_argument('--max-trades', type=int,
                       help='Maximum trades for qualifying bots (no default limit)')
    parser.add_argument('--output-format', choices=['json', 'csv', 'markdown'], default='json',
                       help='Output format for lab analysis reports (default: json)')
    
    args = parser.parse_args(args)
    
    try:
        analyzer = CacheAnalyzer()
        
        # Generate comprehensive lab summary if requested (run independently)
        if args.comprehensive_summary:
            logger.info("📊 Generating comprehensive lab summary...")
            summary_file = analyzer.generate_comprehensive_lab_summary()
            logger.info(f"✅ Comprehensive lab summary generated: {summary_file}")
            return
        
        if not analyzer.connect():
            sys.exit(1)
        
        # Analyze cached data
        result = analyzer.analyze_all_cached_labs(
            lab_ids=args.lab_ids,
            top_count=args.top_count,
            sort_by=args.sort_by,
            save_results=args.save_results
        )
        
        # Show data distribution if requested
        if args.show_data_distribution:
            logger.info("📊 Analyzing data distribution...")
            distribution = analyzer.analyze_data_distribution(result['lab_results'])
            analyzer.print_data_distribution(distribution)
        
        # Generate lab analysis reports if requested
        if args.generate_lab_reports:
            logger.info("📊 Generating lab analysis reports...")
            
            criteria = {
                'min_roe': args.min_roe,
                'max_roe': args.max_roe,
                'min_winrate': args.min_winrate,
                'max_winrate': args.max_winrate,
                'min_trades': args.min_trades,
                'max_trades': args.max_trades
            }
            
            lab_reports = analyzer.generate_lab_analysis_reports(result['lab_results'], criteria)
            
            # Choose format based on argument
            if args.concise_format:
                analyzer.print_concise_lab_reports(lab_reports)
            else:
                analyzer.print_lab_analysis_reports(lab_reports, criteria)
            
            if lab_reports:
                report_file = analyzer.save_lab_analysis_reports(lab_reports, output_format=args.output_format)
                logger.info(f"💾 Lab analysis reports saved to: {report_file}")
        
        # Print detailed per-lab reports if requested
        if args.detailed_lab_reports:
            analyzer.print_detailed_lab_reports(result['lab_results'], top_count=args.top_count)
        
        # Print strategy-grouped report if requested
        if args.strategy_grouped_reports:
            analyzer.print_strategy_grouped_report(result['lab_results'])
        
        # Exit with appropriate code
        if result['successful_analyses'] > 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
