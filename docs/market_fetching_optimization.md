# Market Fetching Optimization Guide

## Overview

This document outlines the optimal methods for fetching market data from the HaasOnline API, based on extensive testing and performance analysis.

## The Problem

The `api.get_all_markets()` function can be slow and unreliable, often resulting in:
- **504 Gateway Timeout** errors
- Long response times (30+ seconds)
- Server overload when fetching large market lists
- Inconsistent availability during peak usage

## The Solution: Exchange-Specific Market Fetching

### Recommended Approach

Use the `PriceAPI.get_trade_markets(exchange)` method to fetch markets by exchange instead of all markets at once.

```python
from pyHaasAPI.price import PriceAPI

def get_markets_efficiently(executor):
    """Get markets efficiently using exchange-specific endpoints"""
    price_api = PriceAPI(executor)
    all_markets = []
    
    # Use exchange-specific endpoints (much faster than get_all_markets)
    exchanges = ["BINANCE", "KRAKEN"]  # Skip COINBASE as it has issues
    
    for exchange in exchanges:
        try:
            print(f"Fetching {exchange} markets...")
            exchange_markets = price_api.get_trade_markets(exchange)
            all_markets.extend(exchange_markets)
            print(f"Found {len(exchange_markets)} {exchange} markets")
        except Exception as e:
            print(f"Failed to get {exchange} markets: {e}")
            continue
    
    return all_markets
```

### Performance Comparison

| Method | Speed | Reliability | Error Handling |
|--------|-------|-------------|----------------|
| `get_all_markets()` | ❌ Slow (30s+) | ❌ Unreliable | ❌ All-or-nothing |
| `get_trade_markets(exchange)` | ✅ Fast (2-5s) | ✅ Reliable | ✅ Per-exchange |

### Exchange Compatibility

| Exchange | Status | Notes |
|----------|--------|-------|
| **BINANCE** | ✅ Working | Fast, reliable |
| **KRAKEN** | ✅ Working | Fast, reliable |
| **COINBASE** | ❌ Issues | Invalid pricesource errors |

## Implementation Examples

### Basic Market Fetching
```python
from pyHaasAPI.price import PriceAPI

def get_markets_for_pairs(executor, pairs):
    """Get markets for specific trading pairs efficiently"""
    price_api = PriceAPI(executor)
    all_markets = []
    
    # Fetch from reliable exchanges
    for exchange in ["BINANCE", "KRAKEN"]:
        try:
            markets = price_api.get_trade_markets(exchange)
            all_markets.extend(markets)
        except Exception as e:
            print(f"Warning: {exchange} markets unavailable: {e}")
    
    # Filter for requested pairs
    pair_markets = {}
    for pair in pairs:
        base, quote = pair.split('/')
        matching = [m for m in all_markets 
                   if m.primary == base.upper() and m.secondary == quote.upper()]
        if matching:
            pair_markets[pair] = matching
    
    return pair_markets
```

### Advanced with Retry Logic
```python
import time
from pyHaasAPI.price import PriceAPI

def get_markets_with_retry(executor, max_attempts=3):
    """Get markets with retry logic and fallback"""
    for attempt in range(max_attempts):
        try:
            price_api = PriceAPI(executor)
            all_markets = []
            
            exchanges = ["BINANCE", "KRAKEN"]
            for exchange in exchanges:
                try:
                    markets = price_api.get_trade_markets(exchange)
                    all_markets.extend(markets)
                except Exception as e:
                    print(f"Failed to get {exchange} markets: {e}")
                    continue
            
            if all_markets:
                return all_markets
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(5)
    
    # Fallback to get_all_markets if all else fails
    print("Falling back to get_all_markets...")
    return api.get_all_markets(executor)
```

## Best Practices

### 1. **Always Use Exchange-Specific Fetching**
```python
# ✅ Good
markets = price_api.get_trade_markets("BINANCE")

# ❌ Avoid
markets = api.get_all_markets(executor)
```

### 2. **Handle Individual Exchange Failures**
```python
# ✅ Good
for exchange in exchanges:
    try:
        markets = price_api.get_trade_markets(exchange)
        all_markets.extend(markets)
    except Exception as e:
        print(f"Warning: {exchange} failed: {e}")
        continue

# ❌ Avoid
try:
    all_markets = api.get_all_markets(executor)  # All-or-nothing
except Exception as e:
    print("All markets failed!")
```

### 3. **Cache Market Data When Possible**
```python
# ✅ Good for repeated operations
cached_markets = get_markets_efficiently(executor)
# Use cached_markets for multiple operations

# ❌ Avoid repeated fetching
for operation in operations:
    markets = get_markets_efficiently(executor)  # Unnecessary API calls
```

### 4. **Filter Markets Early**
```python
# ✅ Good - filter during fetch
def get_markets_for_pairs(executor, pairs):
    price_api = PriceAPI(executor)
    pair_markets = {pair: [] for pair in pairs}
    
    for exchange in ["BINANCE", "KRAKEN"]:
        try:
            markets = price_api.get_trade_markets(exchange)
            for market in markets:
                for pair in pairs:
                    base, quote = pair.split('/')
                    if market.primary == base.upper() and market.secondary == quote.upper():
                        pair_markets[pair].append(market)
        except Exception as e:
            continue
    
    return pair_markets
```

## Real-World Example: Scalper Sweep

The `examples/mcp_scalper_sweep.py` file demonstrates efficient market fetching in a production scenario:

1. **Efficient Market Discovery**: Uses exchange-specific endpoints to find available markets
2. **Pair Matching**: Filters markets for specific trading pairs
3. **Lab Creation**: Creates labs for each matching market
4. **Parameter Optimization**: Sweeps parameters from 0.5 to 2.0 with 0.1 steps
5. **Bot Deployment**: Deploys optimized bots based on backtest results

## Troubleshooting

### Common Issues

1. **COINBASE Markets Fail**
   - **Cause**: Invalid pricesource parameter
   - **Solution**: Skip COINBASE or handle the error gracefully

2. **Timeout Errors**
   - **Cause**: Server overload or network issues
   - **Solution**: Use retry logic with exponential backoff

3. **Empty Market Lists**
   - **Cause**: All exchanges failed or no markets available
   - **Solution**: Implement fallback to `get_all_markets()` or check server status

### Debug Information

```python
def debug_market_fetching(executor):
    """Debug market fetching issues"""
    price_api = PriceAPI(executor)
    
    for exchange in ["BINANCE", "KRAKEN", "COINBASE"]:
        try:
            markets = price_api.get_trade_markets(exchange)
            print(f"{exchange}: {len(markets)} markets")
            if markets:
                print(f"  Sample: {markets[0].price_source}_{markets[0].primary}_{markets[0].secondary}")
        except Exception as e:
            print(f"{exchange}: ERROR - {e}")
```

## Conclusion

Exchange-specific market fetching provides significant performance and reliability improvements over the traditional `get_all_markets()` approach. This optimization is especially important for:

- **Automated trading systems** requiring fast market discovery
- **Lab creation workflows** that need reliable market data
- **Multi-exchange strategies** requiring market availability
- **Production environments** where reliability is critical

Always prefer `PriceAPI.get_trade_markets(exchange)` over `api.get_all_markets()` for better performance and reliability. 