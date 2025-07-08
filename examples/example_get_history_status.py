#!/usr/bin/env python3
"""
Example: Get Historical Data Status for All Markets

This script demonstrates how to use the pyHaasAPI to:
- Authenticate with the HaasOnline API
- Retrieve historical data status for all markets
- Print the number of months of history and status for each market

Environment variables are loaded from a .env file (see below).

Example .env file:
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your@email.com
API_PASSWORD=yourpassword
"""
import os
from dotenv import load_dotenv
from pyHaasAPI import api
import sys

def main():
    load_dotenv()
    host = os.environ.get("API_HOST")
    port = os.environ.get("API_PORT")
    email = os.environ.get("API_EMAIL")
    password = os.environ.get("API_PASSWORD")
    if not all([host, port, email, password]):
        print("Missing one or more required environment variables: API_HOST, API_PORT, API_EMAIL, API_PASSWORD")
        sys.exit(1)
    print("=== Example: Get Historical Data Status for All Markets ===")
    executor = api.create_executor(host, port, email, password)
    api.authenticate(executor)
    print("Authenticated!")
    status = api.get_history_status(executor)
    if not status:
        print("No history status data returned.")
        return
    print(f"{'Market':<25} {'Months':<8} {'Status':<6}")
    print("-" * 45)
    for market, info in status.items():
        print(f"{market:<25} {info.get('MaxMonths', '-'):<8} {info.get('Status', '-'):<6}")
    print("\nDone.")

if __name__ == "__main__":
    main() 