#!/usr/bin/env python3
"""
Working Lab Analyzer for pyHaasAPI CLI

This module contains the PROVEN working lab analysis logic extracted from
analyze_from_cache.py - the most comprehensive and working analysis tool.
"""

import json
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from .base import BaseAnalysisCLI
from .common import convert_win_rate, calculate_roe


@dataclass
class BacktestPerformance:
    """Data class for backtest performance metrics"""
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


class WorkingLabAnalyzer:
    """PROVEN working lab analysis logic from analyze_from_cache.py"""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
    
    def analyze_lab_manual(self, lab_id: str, top_count: int) -> List[BacktestPerformance]:
        """
        PROVEN working manual analysis that properly extracts data from cached files
        Extracted from analyze_from_cache.py lines 105-205
        """
        cache_dir = self.cache.base_dir / "backtests"
        if not cache_dir.exists():
            return []
        
        # Find all cached files for this lab
        pattern = f"{lab_id}_*.json"
        cached_files = list(cache_dir.glob(pattern))
        
        self.logger.info(f"Found {len(cached_files)} cached backtests for lab {lab_id}")
        
        performances = []
        
        for file_path in cached_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract backtest ID from filename
                backtest_id = file_path.stem.split('_', 1)[1]
                
                # Extract performance data directly from top level (cached files are already processed)
                if not data:
                    continue
                
                # Extract performance metrics directly from the cached data
                starting_balance = data.get('starting_balance', 10000.0)
                realized_profits = data.get('realized_profits_usdt', 0.0)
                final_balance = starting_balance + realized_profits
                peak_balance = max(starting_balance, final_balance)
                
                roi_percentage = data.get('roi_percentage', 0.0)
                max_drawdown = data.get('max_drawdown', 0.0)
                
                total_trades = data.get('total_trades', 0)
                win_rate = convert_win_rate(data.get('win_rate', 0.0))
                
                # Extract script and market info
                script_name = data.get('script_name', 'Unknown Script')
                if not script_name and 'runtime_data' in data:
                    script_name = data['runtime_data'].get('ScriptName', 'Unknown Script')
                market_tag = data.get('market_tag', 'UNKNOWN')
                
                # Extract generation and population from cached data
                generation_idx = data.get('generation_idx', 0)
                population_idx = data.get('population_idx', 0)
                
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
                self.logger.warning(f"Error extracting data from {file_path.name}: {e}")
                continue
        
        # Sort by ROE (Return on Equity) - calculated as realized_profits / starting_balance
        performances.sort(key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
        
        # Return top performers
        return performances[:top_count]
    
    def generate_lab_analysis_reports(self, lab_results: List[Any], criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        PROVEN working report generation from analyze_from_cache.py lines 440-533
        """
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
                roe = calculate_roe(backtest.realized_profits_usdt, backtest.starting_balance)
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
    
    def get_full_lab_name(self, lab_id: str) -> str:
        """Get full lab name from CSV reports or cached data or generate descriptive name"""
        # First try to get from CSV reports
        lab_names = self.get_lab_names_from_csv()
        if lab_id in lab_names:
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
                               data.get('LabName') or
                               data.get('Name') or
                               data.get('name'))
                    
                    if lab_name:
                        return lab_name
        except Exception as e:
            self.logger.debug(f"Could not extract lab name for {lab_id}: {e}")
        
        # Final fallback to descriptive name
        return f"Lab {lab_id[:8]}"
    
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
                self.logger.warning(f"Error reading CSV file {csv_file}: {e}")
                continue
                
        return lab_names
    
    def analyze_data_distribution(self, lab_results: List[Any]) -> Dict[str, Any]:
        """Analyze the distribution of data across all labs to help users understand their data"""
        all_roes = []
        all_winrates = []
        all_trades = []
        
        for lab_result in lab_results:
            for backtest in lab_result.top_backtests:
                roe = calculate_roe(backtest.realized_profits_usdt, backtest.starting_balance)
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
        
        self.logger.info(f"💾 Lab analysis reports saved to: {filename}")
        return filename























