from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Minimal versions of models for verification
# We can just path-inject or directly import if we are careful

import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from pyHaasAPI.models.trade import Trade
from pyHaasAPI.models.market import MarketData
from pyHaasAPI.services.bot_naming_service import BotNamingContext
from pyHaasAPI.services.analysis.cached_analysis_service import CachedBacktestPerformance
from pyHaasAPI.models.backtest import BacktestRuntimeData, BacktestAnalysis
from pyHaasAPI.models.bot import BotRuntimeData

def get_test_trades():
    return [
        Trade(profit_loss=100.0, fees=10.0),  # Win: net 90
        Trade(profit_loss=-50.0, fees=5.0),   # Loss: net -55
        Trade(profit_loss=200.0, fees=20.0),  # Win: net 180
    ]

def verify_model(name, model):
    print(f"Verifying {name}...")
    try:
        print(f"  Total Trades: {model.total_trades}")
        print(f"  Win Rate: {model.win_rate:.2f}%")
        
        # Check for specific property names (some use roi, some roi_percentage)
        roi = getattr(model, 'roi', getattr(model, 'roi_percentage', None))
        print(f"  ROI: {roi:.2f}%")
        
        # Check net profit
        net_profit = getattr(model, 'net_profit', getattr(model, 'realized_profits_usdt', None))
        print(f"  Net Profit: {net_profit:.2f}")
        
        # Check profit factor
        print(f"  Profit Factor: {model.profit_factor:.2f}")
        
        # Check max drawdown if available
        if hasattr(model, 'max_drawdown'):
            print(f"  Max Drawdown: {model.max_drawdown:.2f}%")
            
    except Exception as e:
        print(f"  FAILED: {e}")
    print("-" * 20)

def main():
    trades = get_test_trades()
    balance = 1000.0
    
    # 1. MarketData
    md = MarketData(trades=trades, starting_balance=balance)
    verify_model("MarketData", md)
    
    # 2. BotNamingContext
    bnc = BotNamingContext(
        server="srv03", lab_id="l1", lab_name="Lab1", 
        script_name="Scr1", market_tag="BTC/USDT", 
        trades=trades, starting_balance=balance
    )
    verify_model("BotNamingContext", bnc)
    
    # 3. CachedBacktestPerformance
    cbp = CachedBacktestPerformance(
        backtest_id="b1", lab_id="l1", generation_idx=1, population_idx=1,
        script_name="Scr1", market_tag="BTC/USDT", file_path="path/to/file",
        trades=trades, starting_balance=balance
    )
    verify_model("CachedBacktestPerformance", cbp)
    
    # 4. BacktestRuntimeData
    brd = BacktestRuntimeData(trades=trades, starting_balance=balance)
    verify_model("BacktestRuntimeData", brd)

    # 5. BacktestAnalysis
    ba = BacktestAnalysis(trades=trades, starting_balance=balance)
    verify_model("BacktestAnalysis", ba)
    
    # 6. BotRuntimeData
    bord = BotRuntimeData(trades=trades, starting_balance=balance)
    verify_model("BotRuntimeData", bord)

if __name__ == "__main__":
    main()
