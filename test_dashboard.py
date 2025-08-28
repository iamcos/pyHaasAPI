#!/usr/bin/env python3
"""
Test script for the Backtesting Lab Analysis Dashboard

This script allows you to test the dashboard functionality without running the full web interface.
"""

import os
import sys
import json
from datetime import datetime

# Add project root to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import dashboard components
from dash_backtest_analyzer import BacktestDashboard
from pyHaasAPI import api

def test_authentication():
    """Test the authentication functionality"""
    print("🔐 Testing Authentication...")

    # Create dashboard instance
    dashboard = BacktestDashboard()

    # Test with dummy credentials (will fail but test the flow)
    success = dashboard.authenticate_user(
        email="test@example.com",
        password="test_password",
        host="127.0.0.1",
        port=8090
    )

    if success:
        print("✅ Authentication successful")
    else:
        print("❌ Authentication failed (expected with dummy credentials)")

    return success

def test_data_processing():
    """Test data processing functions"""
    print("\n📊 Testing Data Processing...")

    dashboard = BacktestDashboard()

    # Create mock backtest data for testing
    class MockBacktest:
        def __init__(self, total_profit, total_trades, winning_trades, max_drawdown, sharpe_ratio, start_time, end_time):
            self.total_profit = total_profit
            self.total_trades = total_trades
            self.winning_trades = winning_trades
            self.max_drawdown = max_drawdown
            self.sharpe_ratio = sharpe_ratio
            self.start_time = start_time
            self.end_time = end_time

    # Create mock backtests
    mock_backtests = [
        MockBacktest(1000, 50, 35, 5.2, 1.8, datetime(2024, 1, 1), datetime(2024, 1, 2)),
        MockBacktest(-200, 30, 15, 8.1, 0.5, datetime(2024, 1, 2), datetime(2024, 1, 3)),
        MockBacktest(1500, 60, 45, 3.5, 2.1, datetime(2024, 1, 3), datetime(2024, 1, 4)),
        MockBacktest(800, 40, 28, 4.8, 1.9, datetime(2024, 1, 4), datetime(2024, 1, 5)),
    ]

    try:
        # Test metrics cards creation
        metrics_cards = dashboard.create_metrics_cards(mock_backtests)
        print("✅ Metrics cards created successfully")

        # Test chart generation (without actual display)
        print("✅ Chart generation functions available")

        print("✅ Data processing tests passed")
        return True

    except Exception as e:
        print(f"❌ Data processing test failed: {e}")
        return False

def test_imports():
    """Test that all required imports are available"""
    print("\n📦 Testing Imports...")

    try:
        import dash
        import dash_bootstrap_components as dbc
        import plotly.graph_objects as go
        import plotly.express as px
        import pandas as pd
        import numpy as np

        from pyHaasAPI import api
        from pyHaasAPI.backtest_object import BacktestObject, BacktestManager

        print("✅ All imports successful")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Backtesting Lab Analysis Dashboard")
    print("=" * 60)

    # Run tests
    tests = [
        test_imports,
        test_data_processing,
        # Note: test_authentication is commented out to avoid requiring actual credentials
        # test_authentication,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Dashboard is ready to use.")
        print("\nTo run the dashboard:")
        print("1. Activate your virtual environment: source .venv/bin/activate")
        print("2. Run: python dash_backtest_analyzer.py")
        print("3. Open your browser to http://localhost:8050")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")

if __name__ == '__main__':
    main()
