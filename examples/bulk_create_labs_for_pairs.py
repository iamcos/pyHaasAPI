#!/usr/bin/env python3
"""
Bulk Lab Creation for Trading Pairs

Given a list of trading pairs, this script:
- Finds the corresponding Binance spot market
- Clones a well-configured existing lab (template)
- Updates the clone to use the new market and the spot simulated Binance account
- Saves the new lab

Usage: Edit the TRADING_PAIRS list as needed.
"""
import os
import time
from typing import List
from pyHaasAPI import api
from pyHaasAPI.market_manager import MarketManager
from pyHaasAPI.model import CreateLabRequest
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# === CONFIGURATION ===
TRADING_PAIRS = [
    'BTC/USDT',
    'ETH/USDT',
    'AVAX/USDT',
    'SOL/USDT',
    'ADA/USDT',
    'XRP/USDT',
    'BNB/USDT',
    'DOT/USDT',
    'LINK/USDT',
    'MATIC/USDT',
    'DOGE/USDT',
    'TRX/USDT',
    'LTC/USDT',
    'ATOM/USDT',
    'NEAR/USDT',
    # Add more pairs as needed
]
EXCHANGE = "BINANCE"  # Only spot simulated Binance for now

# Load credentials from environment
HAAS_HOST = os.getenv("API_HOST", "127.0.0.1")
HAAS_PORT = int(os.getenv("API_PORT", "8090"))
HAAS_EMAIL = os.getenv("API_EMAIL", "")
HAAS_PASSWORD = os.getenv("API_PASSWORD", "")

def main():
    print("\n🚀 Bulk Lab Creation for Trading Pairs\n" + "=" * 40)
    # 1. Authenticate and create MarketManager
    executor = api.RequestsExecutor(
        host=HAAS_HOST,
        port=HAAS_PORT,
        state=api.Guest()
    ).authenticate(
        email=HAAS_EMAIL,
        password=HAAS_PASSWORD
    )
    market_manager = MarketManager(executor)

    # 2. Find the template lab (the only well-configured lab)
    labs = api.get_all_labs(executor)
    if not labs:
        print("❌ No labs found! Please create a template lab first.")
        return
    # For now, just use the first lab as the template
    template_lab = labs[0]
    print(f"✅ Using template lab: {template_lab.name} (ID: {template_lab.lab_id})")

    # 3. Get the spot simulated Binance account
    account = market_manager.get_test_account()
    if not account or EXCHANGE not in account.exchange_code.upper():
        print(f"❌ No spot simulated {EXCHANGE} account found!")
        return
    print(f"✅ Using account: {account.name} ({account.account_id})")

    # 4. For each trading pair, create a lab
    for pair in TRADING_PAIRS:
        base, quote = [x.strip().upper() for x in pair.replace('-', '/').split('/')]
        print(f"\n🔍 Processing pair: {base}/{quote}")
        market = market_manager.get_market_by_pair(EXCHANGE, base, quote)
        if not market:
            print(f"  ❌ Market not found for {base}/{quote} on {EXCHANGE}")
            continue
        market_tag = market_manager.format_market_string(market)
        print(f"  ✅ Found market: {market_tag}")

        # Clone the template lab
        new_lab_name = f"{template_lab.name}_CLONE_{base}_{quote}_{int(time.time())}"
        print(f"  📋 Cloning lab as: {new_lab_name}")
        cloned_lab = api.clone_lab(executor, template_lab.lab_id, new_lab_name)

        # Update the cloned lab's market/account if needed
        lab_details = api.get_lab_details(executor, cloned_lab.lab_id)
        lab_details.settings.account_id = account.account_id
        lab_details.settings.market_tag = market_tag
        lab_details.name = new_lab_name
        updated_lab = api.update_lab_details(executor, lab_details)
        print(f"  💾 Lab created and updated: {updated_lab.name} (ID: {updated_lab.lab_id})")

        # Start a backtest for 1 year
        from datetime import datetime, timedelta
        now = int(time.time())
        one_year_ago = now - 365 * 24 * 60 * 60
        from pyHaasAPI.model import StartLabExecutionRequest
        try:
            execution = api.start_lab_execution(
                executor,
                StartLabExecutionRequest(
                    lab_id=updated_lab.lab_id,
                    start_unix=one_year_ago,
                    end_unix=now,
                    send_email=False
                )
            )
            print(f"  🚀 Backtest started for 1 year: {execution.status.name if hasattr(execution, 'status') else execution}")
        except Exception as e:
            print(f"  ❌ Failed to start backtest: {e}")

    print("\n🎉 Bulk lab creation complete!")

if __name__ == "__main__":
    main() 