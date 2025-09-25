#!/usr/bin/env python3
"""
Fix cache analysis to use correct data structure
The cache files have performance data in Reports[report_key]['PR'] not runtime_data
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the project root to the path
import sys
sys.path.insert(0, '/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI')

from pyHaasAPI import UnifiedCacheManager

class FixedCacheAnalyzer:
    """Fixed cache analyzer that uses correct data structure"""
    
    def __init__(self):
        self.cache = UnifiedCacheManager()
        
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
    
    def analyze_cached_lab(self, lab_id: str, top_count: int = 10) -> Optional[Dict[str, Any]]:
        """Analyze a single lab from cached data using correct structure"""
        try:
            print(f"🔍 Analyzing cached lab: {lab_id[:8]}...")
            
            cache_dir = self.cache.base_dir / "backtests"
            performances = []
            
            # Find all cache files for this lab
            cache_files = list(cache_dir.glob(f"{lab_id}_*.json"))
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # Extract performance data from Reports section
                    reports = data.get('Reports', {})
                    if not reports:
                        continue
                    
                    # Get the first (and usually only) report
                    report_key = list(reports.keys())[0]
                    report_data = reports[report_key]
                    
                    # Extract performance metrics from PR section
                    pr = report_data.get('PR', {})
                    if not pr:
                        continue
                    
                    # Extract key metrics
                    performance = self._extract_performance_metrics(pr, lab_id, cache_file.stem, data)
                    if performance:
                        performances.append(performance)
                
                except Exception as e:
                    print(f"⚠️ Error reading cache file {cache_file.name}: {e}")
                    continue
            
            # Sort by ROI and return top results
            performances.sort(key=lambda x: x.get('roi_percentage', 0), reverse=True)
            top_performances = performances[:top_count]
            
            if top_performances:
                print(f"✅ Found {len(top_performances)} backtests for {lab_id[:8]}")
                return {
                    'lab_id': lab_id,
                    'total_backtests': len(performances),
                    'top_performances': top_performances,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            else:
                print(f"⚠️ No backtests found for {lab_id[:8]}")
                return None
                        
        except Exception as e:
            print(f"❌ Error analyzing lab {lab_id[:8]}: {e}")
            return None
    
    def _extract_performance_metrics(self, pr: Dict[str, Any], lab_id: str, backtest_id: str, full_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract performance metrics from PR section"""
        try:
            # Extract basic info from full data
            script_name = full_data.get('ScriptName', 'Unknown')
            market_tag = full_data.get('PriceMarket', 'Unknown')
            
            # Extract performance metrics from PR
            pc_value = pr.get('PC', 0)  # Portfolio Close value
            realized_profits = pr.get('RP', 0)  # Realized Profits
            unrealized_profits = pr.get('UP', 0)  # Unrealized Profits
            roi = pr.get('ROI', 0)  # ROI percentage
            
            # Calculate ROI percentage (PC is already a percentage)
            roi_percentage = pc_value if pc_value != 0 else 0
            
            # Extract trade statistics from T section
            t_section = full_data.get('Reports', {}).get(list(full_data.get('Reports', {}).keys())[0], {}).get('T', {})
            
            # Calculate win rate from trade data
            total_trades = t_section.get('TC', 0)  # Total Count
            winning_trades = t_section.get('WC', 0)  # Winning Count
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Extract risk metrics
            max_drawdown = abs(pr.get('RM', 0))  # Risk Metric (drawdown)
            
            # Calculate average profit per trade
            avg_profit_per_trade = realized_profits / total_trades if total_trades > 0 else 0
            
            # Calculate profit factor
            gross_profit = pr.get('GP', 0)  # Gross Profit
            profit_factor = abs(gross_profit / realized_profits) if realized_profits != 0 else 0
            
            return {
                'backtest_id': backtest_id,
                'lab_id': lab_id,
                'script_name': script_name,
                'market_tag': market_tag,
                'roi_percentage': roi_percentage,
                'roe_percentage': roi_percentage,  # ROE same as ROI for this calculation
                'win_rate': win_rate,
                'total_trades': total_trades,
                'max_drawdown': max_drawdown,
                'realized_profits_usdt': realized_profits,
                'pc_value': pc_value,
                'avg_profit_per_trade': avg_profit_per_trade,
                'profit_factor': profit_factor,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting metrics from backtest data: {e}")
            return None
    
    def create_bot_recommendations(self, lab_results: Dict[str, Any], min_winrate: float = 0.52) -> List[Dict[str, Any]]:
        """Create bot recommendations from analysis results"""
        recommendations = []
        
        for lab_id, result in lab_results.items():
            if not result or 'top_performances' not in result:
                continue
                
            for performance in result['top_performances']:
                # Filter by win rate
                if performance.get('win_rate', 0) >= min_winrate:
                    # Create bot recommendation
                    bot_name = f"{lab_id[:8]} - {performance.get('script_name', 'Unknown')} - {performance.get('roi_percentage', 0):.1f}% {performance.get('win_rate', 0):.0f}%"
                    
                    recommendation = {
                        'lab_id': lab_id,
                        'backtest_id': performance.get('backtest_id', 'unknown'),
                        'bot_name': bot_name,
                        'market_tag': performance.get('market_tag', 'UNKNOWN'),
                        'script_name': performance.get('script_name', 'Unknown Script'),
                        'performance': {
                            'roi_percentage': performance.get('roi_percentage', 0),
                            'win_rate': performance.get('win_rate', 0),
                            'total_trades': performance.get('total_trades', 0),
                            'profit_factor': performance.get('profit_factor', 0),
                            'max_drawdown': performance.get('max_drawdown', 0)
                        },
                        'bot_config': {
                            'trade_amount_usdt': 2000.0,
                            'leverage': 20,
                            'margin_mode': 'CROSS',
                            'position_mode': 'HEDGE',
                            'account_assignment': 'individual'
                        },
                        'status': 'recommended',
                        'created_at': datetime.now().isoformat()
                    }
                    recommendations.append(recommendation)
        
        return recommendations

async def main():
    """Main function to test fixed cache analysis"""
    print("🔧 Testing Fixed Cache Analysis")
    print("="*50)
    
    analyzer = FixedCacheAnalyzer()
    
    # Get cached labs
    cached_labs = analyzer.get_cached_labs()
    print(f"📁 Found {len(cached_labs)} labs with cached data")
    
    if not cached_labs:
        print("⚠️ No cached labs found")
        return 1
    
    # Analyze first few labs
    lab_results = {}
    analyzed_count = 0
    max_analyze = 5  # Limit to first 5 labs for testing
    
    for lab_id, backtest_count in list(cached_labs.items())[:max_analyze]:
        print(f"🔍 Analyzing lab {lab_id[:8]} ({backtest_count} backtests)...")
        result = analyzer.analyze_cached_lab(lab_id, top_count=2)
        if result:
            lab_results[lab_id] = result
        analyzed_count += 1
    
    print(f"\n📊 Analysis Results:")
    print(f"Analyzed: {analyzed_count} labs")
    print(f"Successful: {len(lab_results)} labs")
    
    # Create bot recommendations
    recommendations = analyzer.create_bot_recommendations(lab_results, min_winrate=52.0)
    print(f"Bot recommendations: {len(recommendations)}")
    
    # Display recommendations
    if recommendations:
        print("\n🤖 BOT RECOMMENDATIONS:")
        print("="*60)
        for i, rec in enumerate(recommendations, 1):
            perf = rec['performance']
            print(f"{i}. {rec['bot_name']}")
            print(f"   ROI: {perf['roi_percentage']:.1f}%, WR: {perf['win_rate']:.0f}%, Trades: {perf['total_trades']}")
            print(f"   Market: {rec['market_tag']}")
    else:
        print("⚠️ No qualifying bot recommendations found")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)


