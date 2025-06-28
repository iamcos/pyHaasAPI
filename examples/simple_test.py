#!/usr/bin/env python3
"""
Simple test script to verify basic pyHaasAPI functionality
"""
import time
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, StartLabExecutionRequest

def main():
    print("🧪 Simple pyHaasAPI Test\n")
    
    # Authenticate
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="garrypotterr@gmail.com",
        password="IQYTCQJIQYTCQJ"
    )
    print("✅ Authentication successful")

    # Get scripts
    scripts = api.get_scripts_by_name(executor, "Scalper Bot")
    if not scripts:
        print("❌ No scalper bot scripts found!")
        return
    scalper_script = scripts[0]
    print(f"✅ Found scalper script: {scalper_script.script_name}")

    # Get markets
    all_markets = api.get_all_markets(executor)
    print(f"✅ Found {len(all_markets)} markets")

    # Get accounts
    accounts = api.get_accounts(executor)
    if not accounts:
        print("❌ No accounts available!")
        return
    account = accounts[0]
    print(f"✅ Using account: {account.name}")

    # Find BTC/USDT market
    btc_markets = [m for m in all_markets if m.primary == "BTC" and m.secondary == "USDT"]
    if not btc_markets:
        print("❌ No BTC/USDT markets found!")
        return
    market = btc_markets[0]
    print(f"✅ Using market: {market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}")

    # Create a simple lab
    lab_name = f"TEST_LAB_{int(time.time())}"
    lab = api.create_lab(
        executor,
        CreateLabRequest(
            script_id=scalper_script.script_id,
            name=lab_name,
            account_id=account.account_id,
            market=f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_",
            interval=1,
            default_price_data_style="CandleStick"
        )
    )
    print(f"✅ Created lab: {lab.lab_id}")

    # Get lab details
    lab_details = api.get_lab_details(executor, lab.lab_id)
    print(f"✅ Lab details retrieved, {len(lab_details.parameters)} parameters")

    # Run a short backtest (1 hour)
    now = int(time.time())
    start_unix = now - 3600  # 1 hour ago
    end_unix = now
    
    api.start_lab_execution(
        executor,
        StartLabExecutionRequest(
            lab_id=lab.lab_id,
            start_unix=start_unix,
            end_unix=end_unix,
            send_email=False
        )
    )
    print("✅ Started backtest")

    # Wait for completion
    print("⏳ Waiting for backtest to complete...")
    while True:
        details = api.get_lab_details(executor, lab.lab_id)
        if hasattr(details, 'status') and str(details.status) == '3':  # COMPLETED
            print("✅ Backtest completed!")
            break
        elif hasattr(details, 'status') and str(details.status) == '4':  # CANCELLED
            print("❌ Backtest cancelled!")
            break
        time.sleep(5)

    print("\n🎉 Test completed successfully!")

if __name__ == "__main__":
    main() 