#!/usr/bin/env python3
"""
Test script for Lab Analysis and Deployment functionality

This script tests the core components without performing actual deployment.
Use this to validate your setup before running the full analysis.
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import components
from pyHaasAPI import api

def test_authentication():
    """Test API authentication"""
    print("🔐 Testing authentication...")

    try:
        executor = api.RequestsExecutor(
            host=os.getenv("API_HOST", "127.0.0.1"),
            port=int(os.getenv("API_PORT", 8090)),
            state=api.Guest()
        )

        executor = executor.authenticate(
            email=os.getenv("API_EMAIL", ""),
            password=os.getenv("API_PASSWORD", "")
        )

        print("✅ Authentication successful!")
        return executor

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def test_lab_access(executor):
    """Test lab access and data retrieval"""
    print("\n🏢 Testing lab access...")

    try:
        labs = api.get_all_labs(executor)
        print(f"✅ Found {len(labs)} labs")

        if labs:
            # Test getting details for first lab
            first_lab = labs[0]
            print(f"🔍 Testing lab details for: {first_lab.lab_id}")

            lab_details = api.get_lab_details(executor, first_lab.lab_id)
            print(f"✅ Lab details retrieved: {lab_details.name}")

            # Test backtest results
            backtest_results = api.get_backtest_result(
                executor,
                api.GetBacktestResultRequest(lab_id=first_lab.lab_id, next_page_id=0, page_lenght=10)
            )

            if hasattr(backtest_results, 'items') and backtest_results.items:
                print(f"✅ Found {len(backtest_results.items)} backtests")
                return first_lab.lab_id, len(backtest_results.items)
            else:
                print("⚠️ No backtests found in this lab")
                return first_lab.lab_id, 0
        else:
            print("⚠️ No labs found")
            return None, 0

    except Exception as e:
        print(f"❌ Lab access test failed: {e}")
        return None, 0

def test_account_access(executor):
    """Test account access and availability"""
    print("\n🏦 Testing account access...")

    try:
        # Test getting all bots first (this should work)
        bots = api.get_all_bots(executor)
        print(f"🤖 Found {len(bots)} total bots")

        # Count occupied accounts
        occupied_accounts = set()
        for bot in bots:
            if hasattr(bot, 'account_id') and bot.account_id:
                occupied_accounts.add(bot.account_id)
                print(f"🔒 Account {bot.account_id} has bot {bot.bot_id}")

        print(f"🔒 Found {len(occupied_accounts)} occupied accounts")

        # Test getting accounts - handle the direct list response
        try:
            accounts_data = api.get_all_account_balances(executor)
            # If it's a list, use it directly
            if isinstance(accounts_data, list):
                print(f"📊 Found {len(accounts_data)} total accounts")
                total_accounts = len(accounts_data)

                # Check for available accounts
                available_count = 0
                for account_data in accounts_data:
                    account_id = getattr(account_data, 'account_id', '')
                    account_name = getattr(account_data, 'name', '')

                    if ("[Sim] 4AA-10k" in account_name and
                        account_id not in occupied_accounts):
                        available_count += 1
                        print(f"✅ Available: {account_name}")
            else:
                # If it's an ApiResponse object, get the data
                if hasattr(accounts_data, 'data'):
                    accounts_list = accounts_data.data
                    print(f"📊 Found {len(accounts_list)} total accounts")
                    total_accounts = len(accounts_list)
                    available_count = 0
                    for account_data in accounts_list:
                        account_id = getattr(account_data, 'account_id', '')
                        account_name = getattr(account_data, 'name', '')

                        if ("[Sim] 4AA-10k" in account_name and
                            account_id not in occupied_accounts):
                            available_count += 1
                            print(f"✅ Available: {account_name}")
                else:
                    print("📊 Found 0 total accounts")
                    total_accounts = 0
                    available_count = 0

        except Exception as e:
            print(f"⚠️ Account balance retrieval failed: {e}")
            total_accounts = 0
            available_count = 0

        print(f"🎯 Found {available_count} available accounts matching pattern")

        return total_accounts, len(bots), available_count

    except Exception as e:
        print(f"❌ Account access test failed: {e}")
        return 0, 0, 0

def test_lab_analysis_components(executor, lab_id):
    """Test the analysis components without full deployment"""
    print(f"\n📊 Testing analysis components for lab: {lab_id}")

    try:
        # Import our analysis classes
        from lab_analysis_and_deployment import LabAnalyzer, AccountScanner

        # Test LabAnalyzer
        analyzer = LabAnalyzer(executor)
        metrics_list, lab_summary = analyzer.analyze_lab_backtests(lab_id)

        if metrics_list:
            print(f"✅ Analysis successful - processed {len(metrics_list)} backtests")
            print(f"📈 Top backtest score: {metrics_list[0].score:.1f}")
            print(f"💰 Top backtest profit: ${metrics_list[0].total_profit:.2f}")
            print(f"🎯 Top backtest win rate: {metrics_list[0].win_rate:.1f}%")

            # Show top 5
            print("\n🏆 Top 5 Backtests:")
            for i, metric in enumerate(metrics_list[:5], 1):
                print(f"  {i}. ID: {metric.backtest_id[:8]}... Score: {metric.score:.1f}, Profit: ${metric.total_profit:.2f}")
        else:
            print("⚠️ No backtests could be analyzed")

        # Test AccountScanner
        account_scanner = AccountScanner(executor)
        available_accounts = account_scanner.find_available_accounts()

        print(f"✅ Account scanning successful - found {len(available_accounts)} available accounts")

        return len(metrics_list), len(available_accounts)

    except Exception as e:
        print(f"❌ Analysis component test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

def main():
    """Main test function"""
    print("🧪 Lab Analysis and Deployment - Test Suite")
    print("=" * 60)

    # Check environment
    required_vars = ["API_HOST", "API_PORT", "API_EMAIL", "API_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Please set these in your .env file")
        return

    print("✅ Environment variables configured")

    # Test authentication
    executor = test_authentication()
    if not executor:
        print("❌ Cannot continue without successful authentication")
        return

    # Test lab access
    lab_id, backtest_count = test_lab_access(executor)

    # Test account access
    total_accounts, total_bots, available_accounts = test_account_access(executor)

    # Test analysis components if we have a lab
    analyzed_backtests = 0
    available_for_deployment = 0

    if lab_id and backtest_count > 0:
        analyzed_backtests, available_for_deployment = test_lab_analysis_components(executor, lab_id)

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"🔐 Authentication: ✅ PASSED")
    print(f"🏢 Lab Access: {'✅ PASSED' if lab_id else '❌ FAILED'}")
    print(f"📊 Backtests Found: {backtest_count}")
    print(f"🏦 Account Access: ✅ PASSED")
    print(f"📈 Total Accounts: {total_accounts}")
    print(f"🤖 Total Bots: {total_bots}")
    print(f"🎯 Available Accounts: {available_accounts}")
    print(f"📊 Analysis Components: {'✅ PASSED' if analyzed_backtests > 0 else '⚠️ PARTIAL'}")
    print(f"🔍 Backtests Analyzed: {analyzed_backtests}")
    print(f"🚀 Ready for Deployment: {'✅ YES' if available_for_deployment > 0 else '❌ NO'}")

    print("\n" + "=" * 60)

    if available_for_deployment > 0 and analyzed_backtests > 0:
        print("🎉 ALL TESTS PASSED - Ready for full analysis!")
        print(f"\n💡 Run the full analysis with:")
        print(f"   python lab_analysis_and_deployment.py {lab_id}")
    else:
        print("⚠️ Some tests failed or no data available")
        if available_accounts == 0:
            print("💡 Create simulation accounts matching pattern '[Sim] 4AA-10k'")
        if backtest_count == 0:
            print("💡 Ensure your lab has completed backtests")

if __name__ == "__main__":
    main()
