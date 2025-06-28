#!/usr/bin/env python3
print("Testing search logic...")

# Test data based on what we saw
test_markets = [
    {"primary": "1000CAT", "secondary": "BNB", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "FDUSD", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "TRY", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "USDC", "price_source": "BINANCE"},
    {"primary": "1000CAT", "secondary": "USDT", "price_source": "BINANCE"},
    {"primary": "BTC", "secondary": "USDT", "price_source": "BINANCE"},
    {"primary": "ETH", "secondary": "USDT", "price_source": "BINANCE"},
]

def search_markets(markets, query):
    query = query.strip().upper()
    results = []
    
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

# Test
print("Searching for BTC:")
btc_results = search_markets(test_markets, "BTC")
print(f"Found {len(btc_results)} BTC markets")
for market in btc_results:
    print(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")

print("\nSearching for BTC/USDT:")
btc_usdt_results = search_markets(test_markets, "BTC/USDT")
print(f"Found {len(btc_usdt_results)} BTC/USDT markets")
for market in btc_usdt_results:
    print(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")

print("\nSearching for USDT:")
usdt_results = search_markets(test_markets, "USDT")
print(f"Found {len(usdt_results)} USDT markets")
for market in usdt_results:
    print(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")

print("\n✅ Test completed!") 