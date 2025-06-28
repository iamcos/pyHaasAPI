#!/usr/bin/env python3
"""
Quick debug script to test search functionality
"""

# Test with the data structure we can see from the output
test_markets = [
    {"primary": "1000CAT", "secondary": "BNB", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "FDUSD", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "TRY", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "USDC", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "USDT", "price_source": "BINANCE"},
    {"primary": "BTC", "secondary": "USDT", "price_source": "BINANCE"},
    {"primary": "ETH", "secondary": "USDT", "price_source": "BINANCE"},
    {"primary": "BTC", "secondary": "USDT", "price_source": "COINBASE"},
]

test_scripts = [
    {"script_name": "Scalper Bot", "script_id": "123"},
    {"script_name": "RSI Strategy", "script_id": "456"},
    {"script_name": "MACD Bot", "script_id": "789"},
    {"script_name": "EMA Scalper", "script_id": "101"},
]

def search_markets(markets, query):
    """Search markets locally using the query (supports pairs and fuzzy)"""
    query = query.strip().upper()
    results = []
    
    # Support pair search like BTC/USDT
    if "/" in query:
        base, quote = query.split("/")
        for market in markets:
            if market["primary"].upper() == base and market["secondary"].upper() == quote:
                results.append(market)
    else:
        for market in markets:
            if (query in market["primary"].upper() or 
                query in market["secondary"].upper() or 
                query in market["price_source"].upper()):
                results.append(market)
    return results

def search_scripts(scripts, query):
    """Search scripts locally using the query"""
    query = query.lower()
    results = []
    
    for script in scripts:
        if query in script["script_name"].lower():
            results.append(script)
    
    return results

# Test searches
print("🔍 Testing market searches:")
queries = ["BTC", "BTC/USDT", "USDT", "BINANCE", "COINBASE"]
for query in queries:
    results = search_markets(test_markets, query)
    print(f"  '{query}': {len(results)} results")
    for market in results:
        print(f"    • {market['primary']}/{market['secondary']} on {market['price_source']}")

print("\n🤖 Testing script searches:")
script_queries = ["scalper", "rsi", "macd", "ema"]
for query in script_queries:
    results = search_scripts(test_scripts, query)
    print(f"  '{query}': {len(results)} results")
    for script in results:
        print(f"    • {script['script_name']}")

print("\n✅ Debug test completed!") 