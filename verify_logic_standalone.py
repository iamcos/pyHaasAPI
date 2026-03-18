from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

# STANDALONE LOGIC TEST - NO IMPORTS
# This verifies the EXACT logic implemented in the models

@dataclass
class Trade:
    profit_loss: float = 0.0
    fees: float = 0.0
    
    @property
    def net_profit(self) -> float:
        return self.profit_loss - self.fees
    
    @property
    def is_win(self) -> bool:
        return self.net_profit > 0

@dataclass
class BaseModel:
    pass

@dataclass
class MarketData(BaseModel):
    trades: List[Trade] = field(default_factory=list)
    starting_balance: float = 10000.0

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def net_profit(self) -> float:
        return sum(t.net_profit for t in self.trades)

    @property
    def roi(self) -> float:
        if self.starting_balance <= 0 or not self.trades:
            return 0.0
        return (self.net_profit / self.starting_balance) * 100.0

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.is_win)
        return (wins / len(self.trades)) * 100.0

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        return gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

def test_logic():
    print("Testing Dynamic Analytics Logic (Standalone)...")
    
    # Test Data:
    # Trade 1: 100 profit, 10 fee -> 90 net (Win)
    # Trade 2: -50 profit, 5 fee -> -55 net (Loss)
    # Trade 3: 200 profit, 20 fee -> 180 net (Win)
    trades = [
        Trade(100.0, 10.0),
        Trade(-50.0, 5.0),
        Trade(200.0, 20.0)
    ]
    
    balance = 1000.0
    md = MarketData(trades=trades, starting_balance=balance)
    
    # Expected results:
    # Total Trades: 3
    # Net Profit: 90 + (-55) + 180 = 215
    # ROI: (215 / 1000) * 100 = 21.5%
    # Win Rate: (2/3) * 100 = 66.67%
    # Gross Profit: 100 + 200 = 300
    # Gross Loss: 50
    # Profit Factor: 300 / 50 = 6.0
    
    print(f"Total Trades: {md.total_trades} (Expected: 3)")
    print(f"Net Profit: {md.net_profit} (Expected: 215.0)")
    print(f"ROI: {md.roi:.2f}% (Expected: 21.50%)")
    print(f"Win Rate: {md.win_rate:.2f}% (Expected: 66.67%)")
    print(f"Profit Factor: {md.profit_factor:.2f} (Expected: 6.00)")
    
    assert md.total_trades == 3
    assert md.net_profit == 215.0
    assert abs(md.roi - 21.5) < 0.01
    assert abs(md.win_rate - 66.67) < 0.01
    assert md.profit_factor == 6.0
    
    print("\n✅ Logic validation PASSED!")

if __name__ == "__main__":
    test_logic()
