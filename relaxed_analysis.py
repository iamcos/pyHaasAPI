#!/usr/bin/env python3
import json
import glob

# Find the latest filtered analysis file
files = sorted(glob.glob('filtered_cache_analysis_*.json'))
if files:
    latest = files[-1]
    with open(latest, 'r') as f:
        data = json.load(f)
    
    print('=== ANALYZING ALL VALID BACKTESTS ===')
    
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
                'win_rate': backtest.get('win_rate', 0) * 100,
                'total_trades': backtest.get('total_trades', 0),
                'total_positions': backtest.get('total_positions', 0),
                'max_drawdown': backtest.get('max_drawdown', 0)
            })
    
    print(f'Total valid backtests: {len(all_valid_backtests)}')
    
    # Show all backtests with their metrics
    print('\n=== ALL VALID BACKTESTS ===')
    print('Script | Market | Win Rate | ROE | Balance | Trades | Drawdown')
    print('-' * 80)
    
    for backtest in all_valid_backtests:
        print(f'{backtest["script_name"][:15]:<15} | {backtest["market_tag"][:20]:<20} | {backtest["win_rate"]:>7.1f}% | {backtest["roe_percentage"]:>6.1f}% | ${backtest["starting_balance"]:>8.2f} | {backtest["total_trades"]:>6} | {backtest["max_drawdown"]:>8.1f}%')
    
    # Analyze what criteria we can use
    print('\n=== CRITERIA ANALYSIS ===')
    win_rates = [bt['win_rate'] for bt in all_valid_backtests]
    balances = [bt['starting_balance'] for bt in all_valid_backtests]
    trades = [bt['total_trades'] for bt in all_valid_backtests]
    drawdowns = [bt['max_drawdown'] for bt in all_valid_backtests]
    
    print(f'Win Rates: Min={min(win_rates):.1f}%, Max={max(win_rates):.1f}%, Avg={sum(win_rates)/len(win_rates):.1f}%')
    print(f'Balances: Min=${min(balances):.2f}, Max=${max(balances):.2f}, Avg=${sum(balances)/len(balances):.2f}')
    print(f'Trades: Min={min(trades):.1f}, Max={max(trades):.1f}, Avg={sum(trades)/len(trades):.1f}')
    print(f'Drawdowns: Min={min(drawdowns):.1f}%, Max={max(drawdowns):.1f}%, Avg={sum(drawdowns)/len(drawdowns):.1f}%')
    
    # Relaxed criteria
    print('\n=== RELAXED CRITERIA FOR BOT CREATION ===')
    print('1. Win Rate: >= 50% (good performance)')
    print('2. Starting Balance: >= $500 (reasonable capital)')
    print('3. Trades: >= 3 (some trading activity)')
    print('4. Drawdown: <= 5% (low risk)')
    
    # Apply relaxed criteria
    meaningful_backtests = []
    for backtest in all_valid_backtests:
        if (backtest['win_rate'] >= 50 and
            backtest['starting_balance'] >= 500 and
            backtest['total_trades'] >= 3 and
            backtest['max_drawdown'] <= 5):
            meaningful_backtests.append(backtest)
    
    print(f'\nMeaningful backtests with relaxed criteria: {len(meaningful_backtests)}')
    
    if meaningful_backtests:
        print('\n=== RECOMMENDED BOTS FOR CREATION ===')
        for i, backtest in enumerate(meaningful_backtests):
            print(f'\n{i+1}. {backtest["script_name"]} - {backtest["market_tag"]}')
            print(f'   Win Rate: {backtest["win_rate"]:.1f}%')
            print(f'   ROE: {backtest["roe_percentage"]:.1f}%')
            print(f'   Balance: ${backtest["starting_balance"]:.2f}')
            print(f'   Trades: {backtest["total_trades"]}')
            print(f'   Drawdown: {backtest["max_drawdown"]:.1f}%')
            print(f'   Backtest ID: {backtest["backtest_id"]}')
            print(f'   Bot Parameters: $2,000 USDT, 20x leverage, HEDGE mode')
    else:
        print('\n❌ No backtests meet even the relaxed criteria')
        print('Let me try even more relaxed criteria...')
        
        # Even more relaxed criteria
        print('\n=== VERY RELAXED CRITERIA ===')
        print('1. Win Rate: >= 30% (decent performance)')
        print('2. Starting Balance: >= $100 (any capital)')
        print('3. Trades: >= 1 (any trading activity)')
        print('4. Drawdown: <= 10% (moderate risk)')
        
        very_relaxed_backtests = []
        for backtest in all_valid_backtests:
            if (backtest['win_rate'] >= 30 and
                backtest['starting_balance'] >= 100 and
                backtest['total_trades'] >= 1 and
                backtest['max_drawdown'] <= 10):
                very_relaxed_backtests.append(backtest)
        
        print(f'\nVery relaxed criteria matches: {len(very_relaxed_backtests)}')
        
        if very_relaxed_backtests:
            print('\n=== BOTS FOR CREATION (VERY RELAXED) ===')
            for i, backtest in enumerate(very_relaxed_backtests):
                print(f'\n{i+1}. {backtest["script_name"]} - {backtest["market_tag"]}')
                print(f'   Win Rate: {backtest["win_rate"]:.1f}%')
                print(f'   ROE: {backtest["roe_percentage"]:.1f}%')
                print(f'   Balance: ${backtest["starting_balance"]:.2f}')
                print(f'   Trades: {backtest["total_trades"]}')
                print(f'   Drawdown: {backtest["max_drawdown"]:.1f}%')
                print(f'   Backtest ID: {backtest["backtest_id"]}')
                print(f'   Bot Parameters: $2,000 USDT, 20x leverage, HEDGE mode')
else:
    print('No filtered analysis files found')


