#!/usr/bin/env python3
"""
Meaningful Backtests Analysis for Bot Creation
Analyzes cached backtests to find the best candidates for bot creation
based on high win rates and realistic trade amounts.
"""

import json
import glob
from pyHaasAPI import UnifiedCacheManager

def analyze_meaningful_backtests():
    """Analyze meaningful backtests for bot creation recommendations."""
    
    # Find the latest filtered analysis file
    files = sorted(glob.glob('filtered_cache_analysis_*.json'))
    if not files:
        print('No filtered analysis files found')
        return
    
    latest = files[-1]
    print(f'Using analysis file: {latest}')
    
    with open(latest, 'r') as f:
        data = json.load(f)
    
    print('\n=== MEANINGFUL BACKTESTS ANALYSIS FOR BOT CREATION ===')
    
    # Get all valid backtests from the analysis
    all_valid_backtests = []
    for lab_id, lab_data in data.get('labs', {}).items():
        top_performances = lab_data.get('top_performances', [])
        for backtest in top_performances:
            all_valid_backtests.append({
                'lab_id': lab_id,
                'backtest_id': backtest.get('backtest_id'),
                'script_name': backtest.get('script_name'),
                'market_tag': backtest.get('market_tag'),
                'starting_balance': backtest.get('starting_balance', 0),
                'roe_percentage': backtest.get('roe_percentage', 0),
                'win_rate': backtest.get('win_rate', 0) * 100,  # Convert to percentage
                'total_trades': backtest.get('total_trades', 0),
                'total_positions': backtest.get('total_positions', 0),
                'max_drawdown': backtest.get('max_drawdown', 0)
            })
    
    print(f'Total valid backtests found: {len(all_valid_backtests)}')
    
    # Define criteria for meaningful backtests
    print('\n=== BOT CREATION CRITERIA ===')
    print('1. High Win Rate: >= 60% (excellent performance)')
    print('2. Realistic Trade Amount: Starting balance >= $1,000 (realistic capital)')
    print('3. Sufficient Trading Activity: >= 5 trades (statistical significance)')
    print('4. No Drawdown: Account balance never goes negative')
    print('5. ROE can be high (even 1000%+) as long as win rate is excellent')
    
    # Filter for meaningful backtests
    meaningful_backtests = []
    for backtest in all_valid_backtests:
        win_rate = backtest['win_rate']
        starting_balance = backtest['starting_balance']
        total_trades = backtest['total_trades']
        max_drawdown = backtest['max_drawdown']
        
        # Check criteria
        if (win_rate >= 60 and  # High win rate
            starting_balance >= 1000 and  # Realistic capital
            total_trades >= 5 and  # Sufficient trading
            max_drawdown <= 0):  # No drawdown (account never negative)
            
            meaningful_backtests.append(backtest)
    
    print(f'\nMeaningful backtests found: {len(meaningful_backtests)}')
    
    # Sort by win rate (primary) and ROE (secondary)
    meaningful_backtests.sort(key=lambda x: (x['win_rate'], x['roe_percentage']), reverse=True)
    
    print('\n=== TOP MEANINGFUL BACKTESTS FOR BOT CREATION ===')
    print('Rank | Script | Market | Win Rate | ROE | Balance | Trades | Drawdown')
    print('-' * 100)
    
    for i, backtest in enumerate(meaningful_backtests[:10]):  # Top 10
        print(f'{i+1:>4} | {backtest["script_name"][:15]:<15} | {backtest["market_tag"][:20]:<20} | {backtest["win_rate"]:>7.1f}% | {backtest["roe_percentage"]:>6.1f}% | ${backtest["starting_balance"]:>8.2f} | {backtest["total_trades"]:>6} | {backtest["max_drawdown"]:>8.1f}%')
    
    # Group by script and market for recommendations
    print('\n=== BOT CREATION RECOMMENDATIONS ===')
    script_market_groups = {}
    for backtest in meaningful_backtests:
        key = f'{backtest["script_name"]} - {backtest["market_tag"]}'
        if key not in script_market_groups:
            script_market_groups[key] = []
        script_market_groups[key].append(backtest)
    
    for script_market, backtests in script_market_groups.items():
        if len(backtests) >= 1:  # Recommend even single good backtests
            avg_win_rate = sum(bt['win_rate'] for bt in backtests) / len(backtests)
            avg_roe = sum(bt['roe_percentage'] for bt in backtests) / len(backtests)
            avg_balance = sum(bt['starting_balance'] for bt in backtests) / len(backtests)
            
            print(f'\n🎯 RECOMMENDED: {script_market}')
            print(f'   Backtests: {len(backtests)}')
            print(f'   Avg Win Rate: {avg_win_rate:.1f}%')
            print(f'   Avg ROE: {avg_roe:.1f}%')
            print(f'   Avg Balance: ${avg_balance:.2f}')
            print(f'   Top Backtest: {backtests[0]["backtest_id"]}')
            
            # Bot creation parameters
            print(f'   Bot Creation Parameters:')
            print(f'   - Trade Amount: $2,000 USDT (20% of $10,000 account)')
            print(f'   - Leverage: 20x')
            print(f'   - Position Mode: HEDGE')
            print(f'   - Margin Mode: CROSS')
            print(f'   - Expected Win Rate: {avg_win_rate:.1f}%')
            print(f'   - Expected ROE: {avg_roe:.1f}%')
    
    # Summary statistics
    if meaningful_backtests:
        avg_win_rate = sum(bt['win_rate'] for bt in meaningful_backtests) / len(meaningful_backtests)
        avg_roe = sum(bt['roe_percentage'] for bt in meaningful_backtests) / len(meaningful_backtests)
        avg_balance = sum(bt['starting_balance'] for bt in meaningful_backtests) / len(meaningful_backtests)
        
        print(f'\n=== SUMMARY STATISTICS ===')
        print(f'Total Meaningful Backtests: {len(meaningful_backtests)}')
        print(f'Average Win Rate: {avg_win_rate:.1f}%')
        print(f'Average ROE: {avg_roe:.1f}%')
        print(f'Average Starting Balance: ${avg_balance:.2f}')
        print(f'Recommended Bot Count: {len(script_market_groups)} different strategies')
        
        # Create bot creation recommendations file
        create_bot_recommendations_file(meaningful_backtests, script_market_groups)
    else:
        print('\n❌ No meaningful backtests found that meet the criteria')
        print('Consider relaxing the criteria or checking if there are more backtests available')

def create_bot_recommendations_file(meaningful_backtests, script_market_groups):
    """Create a JSON file with bot creation recommendations."""
    
    recommendations = {
        'analysis_timestamp': data.get('summary', {}).get('analysis_timestamp'),
        'total_meaningful_backtests': len(meaningful_backtests),
        'criteria': {
            'min_win_rate': 60,
            'min_starting_balance': 1000,
            'min_trades': 5,
            'max_drawdown': 0
        },
        'recommendations': []
    }
    
    for script_market, backtests in script_market_groups.items():
        if len(backtests) >= 1:
            avg_win_rate = sum(bt['win_rate'] for bt in backtests) / len(backtests)
            avg_roe = sum(bt['roe_percentage'] for bt in backtests) / len(backtests)
            avg_balance = sum(bt['starting_balance'] for bt in backtests) / len(backtests)
            
            recommendation = {
                'strategy': script_market,
                'backtest_count': len(backtests),
                'avg_win_rate': avg_win_rate,
                'avg_roe': avg_roe,
                'avg_balance': avg_balance,
                'top_backtest_id': backtests[0]['backtest_id'],
                'bot_parameters': {
                    'trade_amount_usdt': 2000,
                    'leverage': 20,
                    'position_mode': 'HEDGE',
                    'margin_mode': 'CROSS',
                    'expected_win_rate': avg_win_rate,
                    'expected_roe': avg_roe
                },
                'backtests': backtests
            }
            recommendations['recommendations'].append(recommendation)
    
    # Save recommendations
    filename = 'bot_creation_recommendations.json'
    with open(filename, 'w') as f:
        json.dump(recommendations, f, indent=2)
    
    print(f'\n💾 Bot creation recommendations saved to: {filename}')

if __name__ == '__main__':
    analyze_meaningful_backtests()


