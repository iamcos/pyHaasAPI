# Market Data Guide for pyHaasAPI

## Overview

Market data functionality in pyHaasAPI provides access to real-time and historical market information, including prices, order books, trade history, and chart data. This is essential for both backtesting and live trading operations.

## Core Concepts

### Market Types

- **Spot Markets**: Traditional cryptocurrency trading pairs
- **Futures Markets**: Derivative contracts with leverage
- **Exchange-Specific Markets**: Markets available on specific exchanges

### Market Naming Conventions

#### Spot Markets
Format: `<EXCHANGE>_<BASE>_<QUOTE>_`

```python
# Examples
"BINANCE_BTC_USDT_"
"KRAKEN_ETH_BTC_"
"COINBASE_ADA_USD_"
```

#### Futures Markets
Format: `<EXCHANGE>_<BASE>_<QUOTE>_<CONTRACT_TYPE>`

```python
# Examples
"BINANCEQUARTERLY_BTC_USD_PERPETUAL"
"BINANCEQUARTERLY_BTC_USD_QUARTERLY"
"BINANCEQUARTERLY_ETH_USD_PERPETUAL"
```

## Market Discovery

### Getting All Markets

```python
from pyHaasAPI import api

# Get all available markets (slow, not recommended)
all_markets = api.get_all_markets(executor)
print(f"Found {len(all_markets)} markets")
```

### Exchange-Specific Market Fetching (Recommended)

```python
from pyHaasAPI.price import PriceAPI

price_api = PriceAPI(executor)

# Recommended exchanges (fast and reliable)
exchanges = ["BINANCE", "KRAKEN"]  # Skip COINBASE (has issues)

all_markets = []
for exchange in exchanges:
    try:
        markets = price_api.get_trade_markets(exchange)
        all_markets.extend(markets)
        print(f"Found {len(markets)} markets on {exchange}")
    except Exception as e:
        print(f"Failed to get {exchange} markets: {e}")
        continue

print(f"Total markets: {len(all_markets)}")
```

### Getting Futures Markets

```python
# Get futures markets
futures_markets = api.get_futures_markets(
    executor, 
    exchange_code="BINANCEQUARTERLY"
)

for market in futures_markets:
    print(f"Futures Market: {market.get('market', 'N/A')}")
    print(f"  Contract: {market.get('contract_type', 'N/A')}")
    print(f"  Leverage: {market.get('max_leverage', 'N/A')}")
```

## Market Information

### Getting Market Price

```python
# Get current market price
price_info = api.get_market_price(executor, "BINANCE_BTC_USDT_")
print(f"Current price: {price_info.get('price', 'N/A')}")
print(f"24h change: {price_info.get('change_24h', 'N/A')}%")
print(f"24h volume: {price_info.get('volume_24h', 'N/A')}")
```

### Getting Order Book

```python
# Get order book with custom depth
order_book = api.get_order_book(executor, "BINANCE_BTC_USDT_", depth=20)

print("Bids (Buy orders):")
for bid in order_book.get('bids', [])[:5]:
    print(f"  {bid[0]} @ {bid[1]}")

print("Asks (Sell orders):")
for ask in order_book.get('asks', [])[:5]:
    print(f"  {ask[0]} @ {ask[1]}")
```

### Getting Recent Trades

```python
# Get recent trades
trades = api.get_last_trades(executor, "BINANCE_BTC_USDT_", limit=100)

for trade in trades[:10]:  # Show last 10 trades
    print(f"Trade: {trade.get('amount', 'N/A')} @ {trade.get('price', 'N/A')}")
    print(f"  Side: {trade.get('side', 'N/A')}")
    print(f"  Time: {trade.get('timestamp', 'N/A')}")
```

### Getting Market Snapshot

```python
# Get comprehensive market snapshot
snapshot = api.get_market_snapshot(executor, "BINANCE_BTC_USDT_")

print(f"Market: {snapshot.get('market', 'N/A')}")
print(f"Price: {snapshot.get('price', 'N/A')}")
print(f"24h High: {snapshot.get('high_24h', 'N/A')}")
print(f"24h Low: {snapshot.get('low_24h', 'N/A')}")
print(f"24h Volume: {snapshot.get('volume_24h', 'N/A')}")
print(f"24h Change: {snapshot.get('change_24h', 'N/A')}%")
```

## Chart Data

### Getting Historical Chart Data

```python
# Get chart data with custom parameters
chart_data = api.get_chart(
    executor,
    market="BINANCE_BTC_USDT_",
    interval=15,    # 15-minute candles
    style=301       # Candle style
)

print(f"Chart data points: {len(chart_data.get('data', []))}")
print(f"Time range: {chart_data.get('start_time', 'N/A')} to {chart_data.get('end_time', 'N/A')}")

# Process candle data
for candle in chart_data.get('data', [])[:5]:  # Show first 5 candles
    print(f"Candle: {candle.get('time', 'N/A')}")
    print(f"  Open: {candle.get('open', 'N/A')}")
    print(f"  High: {candle.get('high', 'N/A')}")
    print(f"  Low: {candle.get('low', 'N/A')}")
    print(f"  Close: {candle.get('close', 'N/A')}")
    print(f"  Volume: {candle.get('volume', 'N/A')}")
```

### Chart Intervals

```python
# Common chart intervals (in minutes)
intervals = {
    1: "1 minute",
    5: "5 minutes", 
    15: "15 minutes",
    30: "30 minutes",
    60: "1 hour",
    240: "4 hours",
    1440: "1 day"
}

# Example: Get 1-hour chart
hourly_chart = api.get_chart(
    executor,
    market="BINANCE_BTC_USDT_",
    interval=60,
    style=301
)
```

### Chart Styles

```python
# Common chart styles
chart_styles = {
    300: "Candlestick",
    301: "Candlestick with volume",
    302: "Line chart",
    303: "Area chart"
}

# Example: Get line chart
line_chart = api.get_chart(
    executor,
    market="BINANCE_BTC_USDT_",
    interval=15,
    style=302
)
```

## Market History Management

### Checking History Status

```python
# Get history synchronization status
history_status = api.get_history_status(executor)

for market_status in history_status.get('markets', []):
    market = market_status.get('market', 'N/A')
    status = market_status.get('status', 'N/A')
    last_update = market_status.get('last_update', 'N/A')
    
    print(f"Market: {market}")
    print(f"  Status: {status}")
    print(f"  Last Update: {last_update}")
```

### Setting History Depth

```python
# Set history depth for a market
success = api.set_history_depth(
    executor,
    market="BINANCE_BTC_USDT_",
    months=36  # 3 years of history
)

if success:
    print("History depth set successfully")
else:
    print("Failed to set history depth")
```

### Ensuring History is Ready

```python
# Ensure market history is ready for backtesting
ready = api.ensure_market_history_ready(
    executor,
    market="BINANCE_BTC_USDT_",
    months=36,        # 3 years of history
    poll_interval=5,  # Check every 5 seconds
    timeout=300       # Wait up to 5 minutes
)

if ready:
    print("✅ Market history is ready for backtesting")
else:
    print("❌ Market history not ready within timeout")
```

### History Synchronization

```python
# Ensure history is synced for a market
synced = api.ensure_history_synced(
    executor,
    market="BINANCE_BTC_USDT_",
    months=12  # 1 year of history
)

if synced:
    print("✅ History synchronized successfully")
else:
    print("❌ History synchronization failed")
```

## Market Analysis

### Price Analysis

```python
def analyze_price_movement(market, hours=24):
    """Analyze price movement over specified hours"""
    import time
    
    # Get current price
    current_price = api.get_market_price(executor, market)
    current = float(current_price.get('price', 0))
    
    # Get historical data
    end_time = int(time.time())
    start_time = end_time - (hours * 3600)
    
    chart_data = api.get_chart(
        executor,
        market=market,
        interval=60,  # 1-hour candles
        style=300
    )
    
    # Analyze price movement
    if chart_data.get('data'):
        first_price = float(chart_data['data'][0].get('close', current))
        price_change = ((current - first_price) / first_price) * 100
        
        print(f"Price Analysis for {market}")
        print(f"  Start Price: {first_price}")
        print(f"  Current Price: {current}")
        print(f"  Change: {price_change:.2f}%")
        
        return price_change
    
    return 0
```

### Volume Analysis

```python
def analyze_volume(market, hours=24):
    """Analyze trading volume over specified hours"""
    import time
    
    # Get chart data
    chart_data = api.get_chart(
        executor,
        market=market,
        interval=60,  # 1-hour candles
        style=301     # With volume
    )
    
    if chart_data.get('data'):
        total_volume = sum(float(candle.get('volume', 0)) for candle in chart_data['data'])
        avg_volume = total_volume / len(chart_data['data'])
        
        print(f"Volume Analysis for {market}")
        print(f"  Total Volume: {total_volume:.2f}")
        print(f"  Average Volume: {avg_volume:.2f}")
        
        return total_volume, avg_volume
    
    return 0, 0
```

### Market Comparison

```python
def compare_markets(markets):
    """Compare multiple markets"""
    results = {}
    
    for market in markets:
        try:
            price_info = api.get_market_price(executor, market)
            snapshot = api.get_market_snapshot(executor, market)
            
            results[market] = {
                'price': float(price_info.get('price', 0)),
                'change_24h': float(price_info.get('change_24h', 0)),
                'volume_24h': float(snapshot.get('volume_24h', 0)),
                'high_24h': float(snapshot.get('high_24h', 0)),
                'low_24h': float(snapshot.get('low_24h', 0))
            }
            
        except Exception as e:
            print(f"Error getting data for {market}: {e}")
            continue
    
    # Sort by 24h change
    sorted_markets = sorted(results.items(), key=lambda x: x[1]['change_24h'], reverse=True)
    
    print("Market Comparison (24h Change):")
    for market, data in sorted_markets:
        print(f"{market}: {data['change_24h']:.2f}% (${data['price']:.2f})")
    
    return results
```

## Best Practices

### 1. Efficient Market Fetching

```python
def get_markets_efficiently(exchanges=None):
    """Get markets efficiently using exchange-specific fetching"""
    if exchanges is None:
        exchanges = ["BINANCE", "KRAKEN"]  # Skip COINBASE
    
    from pyHaasAPI.price import PriceAPI
    price_api = PriceAPI(executor)
    
    all_markets = []
    failed_exchanges = []
    
    for exchange in exchanges:
        try:
            markets = price_api.get_trade_markets(exchange)
            all_markets.extend(markets)
            print(f"✅ {exchange}: {len(markets)} markets")
        except Exception as e:
            failed_exchanges.append(exchange)
            print(f"❌ {exchange}: {e}")
    
    if failed_exchanges:
        print(f"⚠️  Failed exchanges: {failed_exchanges}")
    
    return all_markets
```

### 2. Market Validation

```python
def validate_market(market_tag):
    """Validate market tag format and availability"""
    # Check format
    if not market_tag.endswith('_'):
        print(f"❌ Invalid market format: {market_tag}")
        return False
    
    # Check if market exists
    try:
        price_info = api.get_market_price(executor, market_tag)
        if price_info.get('price'):
            print(f"✅ Market valid: {market_tag}")
            return True
        else:
            print(f"❌ Market not found: {market_tag}")
            return False
    except Exception as e:
        print(f"❌ Market validation failed: {market_tag} - {e}")
        return False
```

### 3. Rate Limiting

```python
import time

def rate_limited_market_requests(markets, delay=0.1):
    """Make market requests with rate limiting"""
    results = {}
    
    for market in markets:
        try:
            price_info = api.get_market_price(executor, market)
            results[market] = price_info
            time.sleep(delay)  # Rate limiting
        except Exception as e:
            print(f"Error getting {market}: {e}")
            results[market] = None
    
    return results
```

### 4. Error Handling

```python
def safe_market_operation(operation, market, *args, **kwargs):
    """Safely perform market operations with error handling"""
    try:
        result = operation(executor, market, *args, **kwargs)
        return result
    except api.HaasApiError as e:
        print(f"❌ API error for {market}: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for {market}: {e}")
        return None

# Usage examples
price = safe_market_operation(api.get_market_price, "BINANCE_BTC_USDT_")
orderbook = safe_market_operation(api.get_order_book, "BINANCE_BTC_USDT_", 20)
```

## Troubleshooting

### Common Issues

1. **Market Not Found**
   - Verify market tag format
   - Check if market is available on the exchange
   - Ensure exchange is supported

2. **History Not Available**
   - Set appropriate history depth
   - Wait for synchronization to complete
   - Check server status

3. **Rate Limiting**
   - Implement delays between requests
   - Use batch operations when possible
   - Monitor API usage

4. **Data Inconsistencies**
   - Verify market is actively trading
   - Check for exchange maintenance
   - Validate data timestamps

### Debug Information

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed market information
def debug_market(market):
    print(f"Debugging market: {market}")
    
    try:
        price = api.get_market_price(executor, market)
        print(f"Price: {price}")
    except Exception as e:
        print(f"Price error: {e}")
    
    try:
        snapshot = api.get_market_snapshot(executor, market)
        print(f"Snapshot: {snapshot}")
    except Exception as e:
        print(f"Snapshot error: {e}")
    
    try:
        orderbook = api.get_order_book(executor, market, 5)
        print(f"Orderbook: {orderbook}")
    except Exception as e:
        print(f"Orderbook error: {e}")
```

### Performance Optimization

```python
# Cache market data for repeated access
market_cache = {}

def get_cached_market_price(market, cache_duration=60):
    """Get market price with caching"""
    import time
    
    current_time = time.time()
    
    if market in market_cache:
        cached_data, timestamp = market_cache[market]
        if current_time - timestamp < cache_duration:
            return cached_data
    
    # Fetch fresh data
    try:
        price_data = api.get_market_price(executor, market)
        market_cache[market] = (price_data, current_time)
        return price_data
    except Exception as e:
        print(f"Error fetching price for {market}: {e}")
        return None
``` 