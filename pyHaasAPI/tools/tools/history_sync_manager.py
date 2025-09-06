#!/usr/bin/env python3
"""
History Sync Manager
-------------------
Automate and monitor history sync for any list of markets.

Features:
- Accepts markets via CLI or file
- Triggers sync (GET_CHART) and sets desired history depth
- Monitors sync status and reports progress
- Prints summary table and can write results to JSON

Usage:
    python -m tools.history_sync_manager --markets "BINANCE_BTC_USDT_,BINANCE_ETH_USDT_" --months 36
    python -m tools.history_sync_manager --markets-file markets.txt --months 24 --interval 10 --timeout 300 --output results.json

See also:
- docs/lab_workflows.md
- examples/bulk_set_history_depth.py
"""
import argparse
import time
import json
from config import settings
from pyHaasAPI import api

def parse_markets_from_file(path):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def main():
    parser = argparse.ArgumentParser(description="History Sync Manager: Automate and monitor history sync for markets.")
    parser.add_argument('--markets', type=str, help='Comma-separated list of market tags (e.g., "BINANCE_BTC_USDT_,BINANCE_ETH_USDT_")')
    parser.add_argument('--markets-file', type=str, help='File with one market tag per line')
    parser.add_argument('--months', type=int, default=36, help='Desired history depth in months (default: 36)')
    parser.add_argument('--interval', type=int, default=5, help='Polling interval in seconds (default: 5)')
    parser.add_argument('--timeout', type=int, default=300, help='Max wait time per market in seconds (default: 300)')
    parser.add_argument('--output', type=str, help='Write summary results to JSON file')
    args = parser.parse_args()

    # Build market list
    markets = []
    if args.markets:
        markets = [m.strip() for m in args.markets.split(',') if m.strip()]
    elif args.markets_file:
        markets = parse_markets_from_file(args.markets_file)
    else:
        print("No markets specified! Use --markets or --markets-file.")
        return

    print(f"Markets to sync: {markets}")
    print(f"Desired history depth: {args.months} months")

    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    results = []
    for market in markets:
        print(f"\n---\nProcessing market: {market}")
        # Trigger GET_CHART to initiate sync
        try:
            api.get_chart(executor, market, interval=15, style=301)
        except Exception as e:
            print(f"GET_CHART error: {e}")

        # Poll until the market appears and is synched
        waited = 0
        info = None
        while True:
            history_status = api.get_history_status(executor)
            info = history_status.get(market)
            if info and info.get("Status") == 3:
                print(f"Market {market} is synched (Status 3). Proceeding to set history depth...")
                break
            print(f"Waiting for {market} to be synched... (current status: {info})")
            time.sleep(args.interval)
            waited += args.interval
            if waited >= args.timeout:
                print(f"Timed out waiting for {market} to be synched.")
                break

        # Set history depth if synched
        set_result = None
        if info and info.get("Status") == 3:
            set_result = api.set_history_depth(executor, market, args.months)
            if set_result:
                print(f"✅ Set history depth to {args.months} months for {market}")
            else:
                print(f"❌ Failed to set history depth for {market}")
        else:
            print(f"Skipping set_history_depth for {market} (not synched)")

        # Record result
        results.append({
            "market": market,
            "final_status": info,
            "set_history_depth": set_result
        })

    # Print summary
    print("\n=== History Sync Summary ===")
    for r in results:
        print(f"{r['market']}: Status={r['final_status']}, SetHistoryDepth={r['set_history_depth']}")

    # Optionally write to JSON
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results written to {args.output}")

if __name__ == "__main__":
    main() 