#!/usr/bin/env python3
"""
Utility/Advanced Example
-----------------------
Demonstrates advanced utilities:
- Ensure market history ready
- Ensure lab config parameters
- Error handling
- Bulk lab creation (example)

Run with: python -m examples.utility_advanced_example
"""
from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, CloudMarket
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

    # 1. Ensure market history ready
    markets = api.get_all_markets(executor)
    market = next((m for m in markets if m.price_source == "BINANCE" and m.primary == "BTC" and m.secondary == "USDT"), markets[0])
    market_tag = market.format_market_tag(market.price_source)
    print(f"Ensuring history for {market_tag}...")
    ready = api.ensure_market_history_ready(executor, market_tag, months=36)
    print(f"History ready: {ready}")

    # 2. Ensure lab config parameters
    # (Assume you have a lab_id from a created lab)
    # lab_id = "your_lab_id"
    # api.ensure_lab_config_parameters(executor, lab_id)
    # print("Lab config parameters ensured.")

    # 3. Error handling example
    try:
        api.get_market_price(executor, "INVALID_MARKET")
    except api.HaasApiError as e:
        print(f"Handled API error: {e}")

    # 4. Bulk lab creation (example, using real CloudMarket objects)
    # Use two real markets for demonstration
    eth_market = next((m for m in markets if m.price_source == "BINANCE" and m.primary == "ETH" and m.secondary == "USDT"), markets[0])
    market_configs = [market, eth_market]
    # Auto-select the first available script and account if placeholders are present
    script_id = "your_script_id"
    account_id = "your_account_id"
    scripts = api.get_all_scripts(executor)
    accounts = api.get_accounts(executor)
    if script_id == "your_script_id":
        if not scripts:
            print("No scripts found. Please create a script in the UI first.")
            return
        script_id = scripts[0].script_id
        print(f"Auto-selected script_id: {script_id}")
    if account_id == "your_account_id":
        if not accounts:
            print("No accounts found. Please create an account in the HaasOnline UI first, then re-run this script.")
            print("To create an account: Log in to the HaasOnline web UI, go to 'Accounts', and add a new account (simulated or real).")
            return
        account_id = accounts[0].account_id
        print(f"Auto-selected account_id: {account_id}")
    for m in market_configs:
        market_tag = m.format_market_tag(m.price_source)
        if not api.ensure_market_history_ready(executor, market_tag, months=12):
            print(f"Skipping lab creation for {market_tag} (history not ready)")
            continue
        req = CreateLabRequest.with_generated_name(
            script_id=script_id,
            account_id=account_id,
            market=m,
            exchange_code=m.price_source,
            interval=1,
            default_price_data_style="CandleStick"
        )
        try:
            lab = api.create_lab(executor, req)
            print(f"Lab created for {market_tag}: {lab.lab_id}")
        except Exception as e:
            print(f"Failed to create lab for {market_tag}: {e}")

if __name__ == "__main__":
    main() 