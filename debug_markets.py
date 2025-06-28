#!/usr/bin/env python3

# Test the parse_market function and filtering logic
DEFAULT_MARKETS = [
    "BINANCE_BTC_USDT",
    "BINANCE_ETH_USDT",
    "BINANCE_SOL_BNB",
    "BINANCE_ETH_BTC",
    "BINANCE_BNB_USDT",
    "BINANCE_SOL_USDT",
    "BINANCE_ETH_SOL",
    "COINBASE_BTC_USDT",
    "COINBASE_ETH_USDT",
    "KRAKEN_BTC_USDT",
    "KRAKEN_ETH_USDT",
]

def parse_market(market_str):
    parts = market_str.split("_")
    if len(parts) == 3:
        return {"exchange": parts[0], "symbol": f"{parts[1]}/{parts[2]}", "market": market_str}
    return {"exchange": market_str, "symbol": "", "market": market_str}

print("Testing parse_market function:")
for market in DEFAULT_MARKETS:
    parsed = parse_market(market)
    print(f"  {market} -> {parsed}")

print("\nTesting filtering logic:")
all_market_dicts = [parse_market(m) for m in DEFAULT_MARKETS]
print(f"All market dicts: {len(all_market_dicts)}")
print(f"First few: {all_market_dicts[:3]}")

# Test exchange filtering
exch_filter = "BINANCE"
filtered_by_exchange = [d for d in all_market_dicts if d["exchange"] == exch_filter]
print(f"\nFiltered by {exch_filter}: {len(filtered_by_exchange)}")
print(f"First few: {filtered_by_exchange[:3]}")

# Test search filtering
search = "btc"
def join_row(d):
    if not isinstance(d, dict):
        return ""
    return f"{d.get('exchange', '')} {d.get('symbol', '')} {d.get('market', '')}".lower()

print(f"\nSearch string: '{search}'")
for d in all_market_dicts:
    joined = join_row(d)
    print(f"  {d['market']} -> '{joined}'") 