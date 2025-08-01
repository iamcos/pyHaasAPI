#!/usr/bin/env python3
"""
Price/Market Example
--------------------
Demonstrates price/market endpoints:
- List markets
- Get price
- Get order book
- Get trades
- Get chart
- Set/get history depth

Run with: python -m examples.price_market_example
"""
from config import settings
from pyHaasAPI import api
import time

def main():
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # 1. List all markets
    markets = api.get_all_markets(executor)
    print(f"Total markets: {len(markets)}")
    first_market = markets[0].format_market_tag("BINANCE")
    print(f"First market: {first_market}")

    # 2. Get price
    price = api.get_market_price(executor, first_market)
    print(f"Price: {price}")

    # 3. Get order book
    order_book = api.get_order_book(executor, first_market)
    print(f"Order book: {order_book}")

    # 4. Get trades
    trades = api.get_last_trades(executor, first_market)
    print(f"Last trades: {trades}")

    # 5. Get chart data
    chart = api.get_chart(executor, first_market.format_market_tag(first_market.price_source), interval=15)
    if isinstance(chart, dict) and 'Plots' in chart:
        candles = chart['Plots'][0]['PricePlot']['Candles'] if chart['Plots'] and 'PricePlot' in chart['Plots'][0] else {}
        print(f"Chart data: {len(candles)} candles. First: {min(candles) if candles else 'N/A'}, Last: {max(candles) if candles else 'N/A'}")
    else:
        print(f"Chart data: {type(chart)} {str(chart)[:200]}")

    # 6. Set/get history depth
    set_result = api.set_history_depth(executor, first_market.format_market_tag(first_market.price_source), 12)
    print(f"Set history depth to 12 months: {set_result}")
    hist_status = api.get_history_status(executor, first_market.format_market_tag(first_market.price_source))
    if isinstance(hist_status, dict):
        print(f"History status for {first_market.format_market_tag(first_market.price_source)}: MaxMonths={hist_status.get('MaxMonths')}, Status={hist_status.get('Status')}")
    else:
        print(f"History status: {hist_status}")

if __name__ == "__main__":
    main() 