#!/usr/bin/env python3
"""
Lab Lifecycle Example
---------------------
Demonstrates the full lifecycle of a lab:
- Create lab
- Clone lab
- Update lab details (market/account)
- Update parameters
- Start execution (backtest)
- Monitor status
- Retrieve results
- Delete lab

Run with: python -m examples.lab_lifecycle_example
"""
from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, CloudMarket, StartLabExecutionRequest, GetBacktestResultRequest
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

    # 1. Fetch a real CloudMarket from the API
    markets = api.get_all_markets(executor)
    # Pick the first market, or filter for a specific one if needed
    market = next((m for m in markets if m.price_source == "BINANCE" and m.primary == "BTC" and m.secondary == "USDT"), markets[0])

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

    req = CreateLabRequest.with_generated_name(
        script_id=script_id,
        account_id=account_id,
        market=market,
        exchange_code=market.price_source,
        interval=1,
        default_price_data_style="CandleStick"
    )
    lab = api.create_lab(executor, req)
    print(f"Lab created: {lab.lab_id}")
    time.sleep(2)  # Allow server to process new lab

    # 2. Clone the lab
    cloned_lab = api.clone_lab(executor, lab.lab_id, new_name="BTC_USDT_Clone")
    print(f"Cloned lab ID: {cloned_lab.lab_id}")
    time.sleep(2)  # Allow server to process cloned lab

    # 3. Update lab details (market/account)
    eth_market = next((m for m in markets if m.price_source == "BINANCE" and m.primary == "ETH" and m.secondary == "USDT"), markets[0])
    lab_details = api.get_lab_details(executor, cloned_lab.lab_id)
    lab_details.settings.market_tag = eth_market.format_market_tag(eth_market.price_source)
    lab_details.settings.account_id = account_id
    updated_lab = api.update_lab_details(executor, lab_details)
    print(f"Updated lab: {updated_lab.lab_id}")

    # 4. Update parameters (example: set StopLoss to 1.5)
    for param in updated_lab.parameters:
        if param.get("K") == "StopLoss":
            param["O"] = ["1.5"]
    updated_lab = api.update_lab_details(executor, updated_lab)
    print("Updated parameters.")

    # 5. Ensure lab config parameters before backtest
    updated_lab = api.ensure_lab_config_parameters(executor, updated_lab.lab_id)
    print("Ensured lab config parameters.")

    # Print lab details before starting execution
    print("Lab details before execution:")
    print(api.get_lab_details(executor, updated_lab.lab_id))

    # 6. Start execution (backtest)
    start_unix = int(time.time()) - 86400 * 30  # 30 days ago
    end_unix = int(time.time())
    request = StartLabExecutionRequest(
        lab_id=updated_lab.lab_id,
        start_unix=start_unix,
        end_unix=end_unix,
        send_email=False
    )
    try:
        result = api.start_lab_execution(executor, request)
        print(f"Lab status after start: {result.status}")
    except Exception as e:
        print(f"Failed to start lab execution: {e}")
        import traceback; traceback.print_exc()
        return

    # 7. Monitor status
    print("Monitoring lab execution status...")
    for _ in range(20):
        status = api.get_lab_execution_update(executor, updated_lab.lab_id)
        print(f"Current status: {status.execution_status}")
        if status.execution_status == "COMPLETED":
            break
        time.sleep(5)

    # 8. Retrieve results
    results = api.get_backtest_result(
        executor,
        GetBacktestResultRequest(
            lab_id=updated_lab.lab_id,
            next_page_id=0,
            page_lenght=100
        )
    )
    print(f"Backtest results: {results.items}")

    # 9. Delete lab
    api.delete_lab(executor, updated_lab.lab_id)
    print("Lab deleted.")

if __name__ == "__main__":
    main() 