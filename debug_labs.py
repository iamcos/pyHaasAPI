#!/usr/bin/env python3
"""
Debug script to test trade processing functionality
"""

import os
import sys
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the API
from pyHaasAPI import api

def test_trade_processing():
    """Test trade processing functionality"""
    print("🔍 Testing Trade Processing Functionality")
    print("=" * 60)

    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()

        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        print(f"📋 API Configuration:")
        print(f"   Host: {api_host}:{api_port}")
        print(f"   Email: {'Yes' if api_email else 'No'}")
        print(f"   Password: {'Yes' if api_password else 'No'}")

        if not api_email or not api_password:
            print("❌ Missing credentials")
            return False

        # Authenticate
        print("\n🔐 Authenticating...")
        executor = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        ).authenticate(
            email=api_email,
            password=api_password
        )
        print("✅ Authentication successful!")

        # Test getting all accounts to see available accounts
        print("\n🏦 Getting all accounts...")
        try:
            all_accounts = api.get_all_accounts(executor)
            print(f"✅ Found {len(all_accounts)} accounts")

            if all_accounts:
                # Test with the first account
                account = all_accounts[0]
                print(f"🔍 Testing with account: {account.account_id}")

                # Test 1: Get account trades
                print("\n📊 Testing get_account_trades...")
                try:
                    trades = api.get_account_trades(executor, account.account_id)
                    print(f"✅ Found {len(trades)} trades")
                    if trades:
                        print(f"📋 Sample trade: {trades[0]}")
                except Exception as e:
                    print(f"❌ get_account_trades failed: {e}")

                # Test 2: Get account orders
                print("\n📋 Testing get_account_orders...")
                try:
                    orders = api.get_account_orders(executor, account.account_id)
                    print(f"✅ Found orders: {type(orders)}")
                    if hasattr(orders, 'get') and 'I' in orders:
                        print(f"📋 Found {len(orders['I'])} orders")
                except Exception as e:
                    print(f"❌ get_account_orders failed: {e}")

                # Test 3: Get account positions
                print("\n📊 Testing get_account_positions...")
                try:
                    positions = api.get_account_positions(executor, account.account_id)
                    print(f"✅ Found positions: {type(positions)}")
                    if hasattr(positions, 'get') and 'I' in positions:
                        print(f"📋 Found {len(positions['I'])} positions")
                except Exception as e:
                    print(f"❌ get_account_positions failed: {e}")

                # Test 4: Get account balance
                print("\n💰 Testing get_account_balance...")
                try:
                    balance = api.get_account_balance(executor, account.account_id)
                    print(f"✅ Balance data: {type(balance)}")
                    print(f"📋 Balance info: {balance}")
                except Exception as e:
                    print(f"❌ get_account_balance failed: {e}")

            else:
                print("⚠️ No accounts found")

        except Exception as e:
            print(f"❌ get_all_accounts failed: {e}")

        # Test with labs if available
        print("\n🏢 Testing with labs...")
        try:
            labs = api.get_all_labs(executor)
            print(f"✅ Found {len(labs)} labs")

            if labs:
                # Test with first lab
                lab = labs[0]
                print(f"🔍 Testing with lab: {lab.lab_id}")

                # Get lab details
                print("\n📋 Getting lab details...")
                lab_details = api.get_lab_details(executor, lab.lab_id)
                print(f"✅ Lab details retrieved")
                print(f"   Name: {lab_details.name}")
                print(f"   Status: {getattr(lab_details, 'status', 'Unknown')}")
                print(f"   Script: {getattr(lab_details, 'script_name', 'Unknown')}")

                # Get backtest results
                print("\n📊 Getting backtest results...")
                backtest_results = api.get_backtest_result(
                    executor,
                    api.GetBacktestResultRequest(lab_id=lab.lab_id, next_page_id=0, page_lenght=5)
                )

                if hasattr(backtest_results, 'items') and backtest_results.items:
                    print(f"✅ Found {len(backtest_results.items)} backtests")

                    # Test with first backtest
                    backtest = backtest_results.items[0]
                    print(f"🔍 Testing with backtest: {backtest.backtest_id}")

                    # Test backtest runtime
                    print("\n⚡ Testing get_backtest_runtime...")
                    try:
                        runtime = api.get_backtest_runtime(executor, backtest.backtest_id)
                        print(f"✅ Runtime data retrieved: {type(runtime)}")
                        print(f"📋 Runtime keys: {list(runtime.keys()) if isinstance(runtime, dict) else 'Not a dict'}")
                    except Exception as e:
                        print(f"❌ get_backtest_runtime failed: {e}")

                    # Test backtest logs
                    print("\n📝 Testing get_backtest_log...")
                    try:
                        logs = api.get_backtest_log(executor, lab.lab_id, backtest.backtest_id)
                        print(f"✅ Found {len(logs)} log entries")
                        if logs:
                            print(f"📋 Sample log: {logs[0][:100]}...")
                    except Exception as e:
                        print(f"❌ get_backtest_log failed: {e}")

                else:
                    print("⚠️ No backtest results found")

        except Exception as e:
            print(f"❌ Lab testing failed: {e}")

        print("\n" + "=" * 60)
        print("🎉 Trade processing functionality test complete!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ Debug session failed: {e}")
        return False

def test_specific_backtest(backtest_id: str):
    """Test with a specific backtest ID"""
    print(f"🔍 Testing specific backtest: {backtest_id}")
    print("=" * 60)

    try:
        # Authenticate
        from dotenv import load_dotenv
        load_dotenv()

        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        executor = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        ).authenticate(
            email=api_email,
            password=api_password
        )

        # Test get_backtest_runtime with the specific ID
        print("⚡ Testing get_backtest_runtime...")
        try:
            runtime = api.get_backtest_runtime(executor, backtest_id)
            print(f"✅ Runtime data retrieved: {type(runtime)}")
            print(f"📋 Runtime data: {runtime}")
        except Exception as e:
            print(f"❌ get_backtest_runtime failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Specific backtest test failed: {e}")
        return False

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--specific':
        if len(sys.argv) > 2:
            backtest_id = sys.argv[2]
            test_specific_backtest(backtest_id)
        else:
            print("Usage: python debug_labs.py --specific <backtest_id>")
    else:
        test_trade_processing()
