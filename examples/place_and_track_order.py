#!/usr/bin/env python3
"""
Minimal example: Place an order and track it
"""
import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
from pyHaasAPI import api
import time

def main():
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="garrypotterr@gmail.com",
        password="IQYTCQJIQYTCQJ"
    )

    account_id = "8feff3b1-74ba-44ac-9a73-0f84ee3cf500"
    market = "BINANCE_BTC_TUSD_"

    # 1. Get price
    price_info = api.get_market_price(executor, market)
    price = price_info.get('C') if isinstance(price_info, dict) else None
    print(f"Market price for {market}: {price}")
    if not price:
        print("Warning: No 'C' (close/last price) in get_market_price response:", price_info)
        print("Could not fetch price!")
        return

    # 2. Place a small buy order
    amount = 0.0005
    order_id = api.place_order(
        executor,
        account_id=account_id,
        market=market,
        side="buy",
        price=price,
        amount=amount
    )
    print(f"Order placed! ID: {order_id}")

    # 3. Cancel the order
    cancel_success = api.cancel_order(executor, account_id, order_id)
    print("Order cancelled!" if cancel_success else "Cancel failed!")

    # 4. Wait a moment for the cancellation to process
    time.sleep(2)

    # 5. Fetch open orders
    orders_response = api.get_account_orders(executor, account_id)
    orders = orders_response.get("I", []) if isinstance(orders_response, dict) else []
    print(f"Open orders for account {account_id} after cancellation:")
    for order in orders:
        print(order)

    # 6. Fetch positions
    positions_response = api.get_account_positions(executor, account_id)
    positions = positions_response.get("I", []) if isinstance(positions_response, dict) else []
    print(f"Positions for account {account_id}:")
    for pos in positions:
        print(pos)

    # 7. Fetch balances
    balance = api.get_account_balance(executor, account_id)
    print(f"Balance for account {account_id}:")
    print(balance)

if __name__ == "__main__":
    # Place the main execution logic here
    pass 