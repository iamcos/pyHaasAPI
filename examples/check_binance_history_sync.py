#!/usr/bin/env python3
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

    # Get all markets for BINANCE
    all_markets = api.get_all_markets(executor)
    binance_markets = [m for m in all_markets if m.price_source == "BINANCE"]
    if not binance_markets:
        print("No Binance markets found!")
        return

    if len(binance_markets) < 4:
        print("Less than four Binance markets found!")
        return

    for idx in [2, 3]:
        market_tag = binance_markets[idx].format_market_tag("BINANCE")
        print(f"\n---\nProcessing market: {market_tag}")

        # Trigger GET_CHART to initiate sync
        print(f"Triggering GET_CHART API call for {market_tag}...")
        try:
            chart = api.get_chart(executor, market_tag, interval=15, style=301)
            print(f"GET_CHART API response: {chart}")
        except Exception as e:
            print(f"GET_CHART API error: {e}")

        # Poll until the market appears and is synched
        max_wait = 180  # seconds
        wait_interval = 5
        waited = 0
        while True:
            history_status = api.get_history_status(executor)
            info = history_status.get(market_tag)
            if info and info.get("Status") == 3:
                print(f"Market {market_tag} is synched (Status 3). Proceeding to set history depth...")
                break
            print(f"Waiting for {market_tag} to be synched... (current status: {info})")
            time.sleep(wait_interval)
            waited += wait_interval
            if waited >= max_wait:
                print(f"Timed out waiting for {market_tag} to be synched.")
                break

        # Set history depth to 36 months if synched
        if info and info.get("Status") == 3:
            success = api.set_history_depth(executor, market_tag, 36)
            if success:
                print(f"✅ Set history depth to 36 months for {market_tag}")
            else:
                print(f"❌ Failed to set history depth for {market_tag}")

    # Print updated history status
    print("\nUpdated history_status:")
    history_status = api.get_history_status(executor)
    for market, info in history_status.items():
        print(f"  {market}: {info}")

if __name__ == "__main__":
    main() 