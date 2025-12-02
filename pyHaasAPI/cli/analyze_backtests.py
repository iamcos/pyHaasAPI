#!/usr/bin/env python3
"""
Comprehensive Backtest Analysis CLI

Analyzes downloaded backtest data and generates detailed spreadsheet analysis.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics


class BacktestAnalyzer:
    """Analyze downloaded backtest data and generate detailed spreadsheet"""
    
    def __init__(self, json_file: str):
        self.json_file = Path(json_file)
        self.data = self._load_data()
        self.analysis_results = []
    
    def _load_data(self) -> Dict[str, Any]:
        """Load JSON data file"""
        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_file}")
        
        with open(self.json_file, 'r') as f:
            return json.load(f)
    
    def analyze(self) -> List[Dict[str, Any]]:
        """Perform comprehensive analysis of all backtests"""
        print("📊 Analyzing backtest data...")
        
        server_results = self.data.get('server_results', {})
        
        for server_name, server_data in server_results.items():
            if 'error' in server_data:
                continue
            
            labs = server_data.get('labs', [])
            print(f"\n🔍 Analyzing {server_name}: {len(labs)} labs")
            
            for lab in labs:
                if 'error' in lab:
                    continue
                
                backtests = lab.get('backtests', [])
                if not backtests:
                    continue
                
                lab_analysis = self._analyze_lab(server_name, lab, backtests)
                self.analysis_results.append(lab_analysis)
        
        print(f"\n✅ Analyzed {len(self.analysis_results)} labs")
        return self.analysis_results
    
    def _analyze_lab(self, server: str, lab: Dict[str, Any], backtests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a single lab's backtests"""
        if not backtests:
            return {
                'server': server,
                'lab_id': lab.get('lab_id', ''),
                'lab_name': lab.get('lab_name', ''),
                'total_backtests': 0,
                'error': 'No backtests'
            }
        
        # Extract metrics
        rois = [bt.get('roi', 0) for bt in backtests if bt.get('roi') is not None]
        roes = [bt.get('roe', 0) for bt in backtests if bt.get('roe') is not None]
        win_rates = [bt.get('win_rate', 0) for bt in backtests if bt.get('win_rate') is not None]
        total_trades = [bt.get('total_trades', 0) for bt in backtests if bt.get('total_trades') is not None]
        profits = [bt.get('realized_profits_usdt', 0) for bt in backtests if bt.get('realized_profits_usdt') is not None]
        drawdowns = [abs(bt.get('max_drawdown', 0)) for bt in backtests if bt.get('max_drawdown') is not None]
        
        # Calculate statistics
        analysis = {
            'server': server,
            'lab_id': lab.get('lab_id', ''),
            'lab_name': lab.get('lab_name', ''),
            'script_id': lab.get('script_id', ''),
            'status': lab.get('status', ''),
            'completed_backtests': lab.get('completed_backtests', 0),
            'downloaded_backtests': len(backtests),
            
            # ROI Statistics
            'avg_roi': statistics.mean(rois) if rois else 0,
            'median_roi': statistics.median(rois) if rois else 0,
            'max_roi': max(rois) if rois else 0,
            'min_roi': min(rois) if rois else 0,
            'std_roi': statistics.stdev(rois) if len(rois) > 1 else 0,
            
            # ROE Statistics
            'avg_roe': statistics.mean(roes) if roes else 0,
            'median_roe': statistics.median(roes) if roes else 0,
            'max_roe': max(roes) if roes else 0,
            'min_roe': min(roes) if roes else 0,
            
            # Win Rate Statistics
            'avg_win_rate': statistics.mean(win_rates) if win_rates else 0,
            'median_win_rate': statistics.median(win_rates) if win_rates else 0,
            'max_win_rate': max(win_rates) if win_rates else 0,
            'min_win_rate': min(win_rates) if win_rates else 0,
            
            # Trade Statistics
            'avg_trades': statistics.mean(total_trades) if total_trades else 0,
            'median_trades': statistics.median(total_trades) if total_trades else 0,
            'max_trades': max(total_trades) if total_trades else 0,
            'min_trades': min(total_trades) if total_trades else 0,
            'total_trades_all': sum(total_trades) if total_trades else 0,
            
            # Profit Statistics
            'avg_profit_usdt': statistics.mean(profits) if profits else 0,
            'median_profit_usdt': statistics.median(profits) if profits else 0,
            'max_profit_usdt': max(profits) if profits else 0,
            'min_profit_usdt': min(profits) if profits else 0,
            'total_profit_usdt': sum(profits) if profits else 0,
            
            # Drawdown Statistics
            'avg_drawdown': statistics.mean(drawdowns) if drawdowns else 0,
            'max_drawdown': max(drawdowns) if drawdowns else 0,
            'min_drawdown': min(drawdowns) if drawdowns else 0,
            
            # Performance Ratios
            'profit_factor': self._calculate_profit_factor(backtests),
            'sharpe_ratio': self._calculate_avg_sharpe(backtests),
            'sortino_ratio': self._calculate_avg_sortino(backtests),
            'calmar_ratio': self._calculate_avg_calmar(backtests),
            
            # Counts
            'profitable_backtests': len([bt for bt in backtests if bt.get('roi', 0) > 0]),
            'losing_backtests': len([bt for bt in backtests if bt.get('roi', 0) < 0]),
            'break_even_backtests': len([bt for bt in backtests if bt.get('roi', 0) == 0]),
            
            # Top Performers
            'top_roi': self._get_top_backtest(backtests, 'roi'),
            'top_roe': self._get_top_backtest(backtests, 'roe'),
            'top_win_rate': self._get_top_backtest(backtests, 'win_rate'),
        }
        
        return analysis
    
    def _calculate_profit_factor(self, backtests: List[Dict[str, Any]]) -> float:
        """Calculate average profit factor"""
        profit_factors = [bt.get('profit_factor', 0) for bt in backtests if bt.get('profit_factor')]
        return statistics.mean(profit_factors) if profit_factors else 0
    
    def _calculate_avg_sharpe(self, backtests: List[Dict[str, Any]]) -> float:
        """Calculate average Sharpe ratio"""
        sharpes = [bt.get('sharpe_ratio', 0) for bt in backtests if bt.get('sharpe_ratio')]
        return statistics.mean(sharpes) if sharpes else 0
    
    def _calculate_avg_sortino(self, backtests: List[Dict[str, Any]]) -> float:
        """Calculate average Sortino ratio"""
        sortinos = [bt.get('sortino_ratio', 0) for bt in backtests if bt.get('sortino_ratio')]
        return statistics.mean(sortinos) if sortinos else 0
    
    def _calculate_avg_calmar(self, backtests: List[Dict[str, Any]]) -> float:
        """Calculate average Calmar ratio"""
        calmars = [bt.get('calmar_ratio', 0) for bt in backtests if bt.get('calmar_ratio')]
        return statistics.mean(calmars) if calmars else 0
    
    def _get_top_backtest(self, backtests: List[Dict[str, Any]], metric: str) -> Optional[float]:
        """Get top backtest value for a metric"""
        values = [bt.get(metric, 0) for bt in backtests if bt.get(metric) is not None]
        return max(values) if values else None
    
    def generate_spreadsheet(self, output_file: Optional[str] = None) -> str:
        """Generate detailed CSV spreadsheet"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'BACKTEST_ANALYSIS_{timestamp}.csv'
        
        output_path = Path(output_file)
        
        # Define comprehensive columns
        fieldnames = [
            'Server', 'Lab ID', 'Lab Name', 'Script ID', 'Status',
            'Completed Backtests', 'Downloaded Backtests',
            'Avg ROI %', 'Median ROI %', 'Max ROI %', 'Min ROI %', 'Std ROI',
            'Avg ROE %', 'Median ROE %', 'Max ROE %', 'Min ROE %',
            'Avg Win Rate %', 'Median Win Rate %', 'Max Win Rate %', 'Min Win Rate %',
            'Avg Trades', 'Median Trades', 'Max Trades', 'Min Trades', 'Total Trades',
            'Avg Profit USDT', 'Median Profit USDT', 'Max Profit USDT', 'Min Profit USDT', 'Total Profit USDT',
            'Avg Drawdown %', 'Max Drawdown %', 'Min Drawdown %',
            'Avg Profit Factor', 'Avg Sharpe Ratio', 'Avg Sortino Ratio', 'Avg Calmar Ratio',
            'Profitable Backtests', 'Losing Backtests', 'Break Even Backtests',
            'Top ROI %', 'Top ROE %', 'Top Win Rate %'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.analysis_results:
                row = {
                    'Server': result.get('server', ''),
                    'Lab ID': result.get('lab_id', ''),
                    'Lab Name': result.get('lab_name', ''),
                    'Script ID': result.get('script_id', ''),
                    'Status': result.get('status', ''),
                    'Completed Backtests': result.get('completed_backtests', 0),
                    'Downloaded Backtests': result.get('downloaded_backtests', 0),
                    'Avg ROI %': round(result.get('avg_roi', 0), 2),
                    'Median ROI %': round(result.get('median_roi', 0), 2),
                    'Max ROI %': round(result.get('max_roi', 0), 2),
                    'Min ROI %': round(result.get('min_roi', 0), 2),
                    'Std ROI': round(result.get('std_roi', 0), 2),
                    'Avg ROE %': round(result.get('avg_roe', 0), 2),
                    'Median ROE %': round(result.get('median_roe', 0), 2),
                    'Max ROE %': round(result.get('max_roe', 0), 2),
                    'Min ROE %': round(result.get('min_roe', 0), 2),
                    'Avg Win Rate %': round(result.get('avg_win_rate', 0), 2),
                    'Median Win Rate %': round(result.get('median_win_rate', 0), 2),
                    'Max Win Rate %': round(result.get('max_win_rate', 0), 2),
                    'Min Win Rate %': round(result.get('min_win_rate', 0), 2),
                    'Avg Trades': round(result.get('avg_trades', 0), 1),
                    'Median Trades': round(result.get('median_trades', 0), 1),
                    'Max Trades': result.get('max_trades', 0),
                    'Min Trades': result.get('min_trades', 0),
                    'Total Trades': result.get('total_trades_all', 0),
                    'Avg Profit USDT': round(result.get('avg_profit_usdt', 0), 2),
                    'Median Profit USDT': round(result.get('median_profit_usdt', 0), 2),
                    'Max Profit USDT': round(result.get('max_profit_usdt', 0), 2),
                    'Min Profit USDT': round(result.get('min_profit_usdt', 0), 2),
                    'Total Profit USDT': round(result.get('total_profit_usdt', 0), 2),
                    'Avg Drawdown %': round(result.get('avg_drawdown', 0), 2),
                    'Max Drawdown %': round(result.get('max_drawdown', 0), 2),
                    'Min Drawdown %': round(result.get('min_drawdown', 0), 2),
                    'Avg Profit Factor': round(result.get('profit_factor', 0), 2),
                    'Avg Sharpe Ratio': round(result.get('sharpe_ratio', 0), 2),
                    'Avg Sortino Ratio': round(result.get('sortino_ratio', 0), 2),
                    'Avg Calmar Ratio': round(result.get('calmar_ratio', 0), 2),
                    'Profitable Backtests': result.get('profitable_backtests', 0),
                    'Losing Backtests': result.get('losing_backtests', 0),
                    'Break Even Backtests': result.get('break_even_backtests', 0),
                    'Top ROI %': round(result.get('top_roi', 0), 2) if result.get('top_roi') is not None else '',
                    'Top ROE %': round(result.get('top_roe', 0), 2) if result.get('top_roe') is not None else '',
                    'Top Win Rate %': round(result.get('top_win_rate', 0), 2) if result.get('top_win_rate') is not None else '',
                }
                writer.writerow(row)
        
        print(f"\n💾 Detailed analysis saved to: {output_path}")
        return str(output_path)


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        # Find latest JSON file
        json_files = sorted(Path('.').glob('COMPLETE_BACKTEST_DATABASE_*.json'), reverse=True)
        if not json_files:
            print("❌ No backtest database JSON file found!")
            print("Usage: python -m pyHaasAPI.cli.analyze_backtests <json_file>")
            sys.exit(1)
        json_file = json_files[0]
        print(f"📁 Using latest file: {json_file}")
    else:
        json_file = sys.argv[1]
    
    analyzer = BacktestAnalyzer(json_file)
    analyzer.analyze()
    output_file = analyzer.generate_spreadsheet()
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Analyzed {len(analyzer.analysis_results)} labs")
    print(f"📈 Spreadsheet: {output_file}")


if __name__ == '__main__':
    main()

