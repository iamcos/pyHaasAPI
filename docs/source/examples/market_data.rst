Trade Markets Data Examples
==========================

This page demonstrates how to fetch and use **trade markets data** (exchange trade markets) with pyHaasAPI, including getting available markets, prices, order books, and recent trades. 

.. note::
   This page focuses on *trade market discovery* and live market info (prices, order books, trades). For fetching historical market data (OHLCV, chart data, etc.), see the backtesting or chart data examples.

.. contents::
   :local:
   :depth: 2

Listing All Trade Markets
------------------------

.. code-block:: python

    from pyHaasAPI import api
    from config import settings

    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    markets = api.get_all_markets(executor)
    for market in markets[:5]:
        print(f"Market: {market.price_source} {market.primary}/{market.secondary}")

Getting Latest Price (Ticker)
-----------------------------

.. code-block:: python

    # Get the price for a specific trade market
    market = markets[0]
    price = api.get_market_price(executor, market.format_market_tag(market.price_source))
    print(f"Price for {market.primary}/{market.secondary}: {price}")

Getting Order Book
------------------

.. code-block:: python

    order_book = api.get_order_book(executor, market.format_market_tag(market.price_source))
    print(f"Order Book: {order_book}")

Getting Recent Trades
---------------------

.. code-block:: python

    trades = api.get_last_trades(executor, market.format_market_tag(market.price_source))
    print(f"Recent Trades: {trades[:3]}")

This workflow covers the basics of trade market discovery and live data. For historical data, see the backtesting or chart data documentation. 