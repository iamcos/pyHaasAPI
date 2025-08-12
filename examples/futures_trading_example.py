#!/usr/bin/env python3
"""
Futures Trading Example
-----------------------
Demonstrates the new futures trading functionality:
- PERPETUAL and QUARTERLY contracts
- Position modes (ONE-WAY vs HEDGE)
- Margin modes (CROSS vs ISOLATED)
- Leverage settings
- Creating bots from lab results with futures support

This example shows how to work with the new market format:
- BINANCEQUARTERLY_BTC_USD_PERPETUAL
- BINANCEQUARTERLY_BTC_USD_QUARTERLY

Run with: python -m examples.futures_trading_example
"""

import os
import sys
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import (
    CloudMarket, PositionMode, MarginMode, ContractType,
    CreateLabRequest, PriceDataStyle
)
from pyHaasAPI.exceptions import HaasApiError

def main():
    """Main function demonstrating futures trading functionality"""
    print("🚀 Futures Trading Example")
    print("=" * 50)
    
    # Environment variables already loaded at module level
    
    # Authenticate
    print("🔐 Authenticating...")
    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Get existing accounts and scripts
    print("\n📊 Getting accounts and scripts...")
    try:
        accounts = api.get_accounts(executor)
        scripts = api.get_all_scripts(executor)
        
        if not accounts:
            print("❌ No accounts found. Please create an account first.")
            return
        
        if not scripts:
            print("❌ No scripts found. Please create a script first.")
            return
        
        # Find BINANCEQUARTERLY account
        binance_quarterly_account = None
        for account in accounts:
            if account.exchange_code == "BINANCEQUARTERLY":
                binance_quarterly_account = account
                break
        
        if not binance_quarterly_account:
            print("❌ No BINANCEQUARTERLY account found.")
            print("Please create a BINANCEQUARTERLY account first.")
            return
        
        print(f"✅ Using account: {binance_quarterly_account.name}")
        print(f"✅ Using script: {scripts[0].script_name}")
        
    except Exception as e:
        print(f"❌ Error getting accounts/scripts: {e}")
        return
    
    # Demonstrate futures market creation
    print("\n📈 Creating Futures Markets")
    print("-" * 30)
    
    # Create CloudMarket objects for futures
    btc_perpetual = CloudMarket(
        C="FUTURES",
        PS="BINANCEQUARTERLY",
        P="BTC",
        S="USD",
        CT="PERPETUAL"
    )
    
    btc_quarterly = CloudMarket(
        C="FUTURES",
        PS="BINANCEQUARTERLY",
        P="BTC",
        S="USD",
        CT="QUARTERLY"
    )
    
    # Format market tags
    perpetual_market_tag = btc_perpetual.format_futures_market_tag("BINANCEQUARTERLY", "PERPETUAL")
    quarterly_market_tag = btc_quarterly.format_futures_market_tag("BINANCEQUARTERLY", "QUARTERLY")
    
    print(f"Perpetual Market: {perpetual_market_tag}")
    print(f"Quarterly Market: {quarterly_market_tag}")
    
    # Demonstrate lab creation with futures
    print("\n🧪 Creating Futures Labs")
    print("-" * 30)
    
    try:
        # Create lab for perpetual contract
        perpetual_lab_request = CreateLabRequest.with_futures_market(
            script_id=scripts[0].script_id,
            account_id=binance_quarterly_account.account_id,
            market=btc_perpetual,
            exchange_code="BINANCEQUARTERLY",
            interval=1,
            default_price_data_style="CandleStick",
            contract_type="PERPETUAL"
        )
        
        # Add futures-specific settings
        perpetual_lab_request.leverage = 50.0
        perpetual_lab_request.position_mode = PositionMode.ONE_WAY
        perpetual_lab_request.margin_mode = MarginMode.CROSS
        
        print(f"Creating perpetual lab: {perpetual_lab_request.name}")
        print(f"Market: {perpetual_lab_request.market}")
        print(f"Leverage: {perpetual_lab_request.leverage}x")
        print(f"Position Mode: {'ONE-WAY' if perpetual_lab_request.position_mode == 0 else 'HEDGE'}")
        print(f"Margin Mode: {'CROSS' if perpetual_lab_request.margin_mode == 0 else 'ISOLATED'}")
        
        perpetual_lab = api.create_lab(executor, perpetual_lab_request)
        print(f"✅ Created perpetual lab: {perpetual_lab.lab_id}")
        
        # Create lab for quarterly contract
        quarterly_lab_request = CreateLabRequest.with_futures_market(
            script_id=scripts[0].script_id,
            account_id=binance_quarterly_account.account_id,
            market=btc_quarterly,
            exchange_code="BINANCEQUARTERLY",
            interval=1,
            default_price_data_style="CandleStick",
            contract_type="QUARTERLY"
        )
        
        # Add futures-specific settings
        quarterly_lab_request.leverage = 25.0
        quarterly_lab_request.position_mode = PositionMode.HEDGE
        quarterly_lab_request.margin_mode = MarginMode.ISOLATED
        
        print(f"\nCreating quarterly lab: {quarterly_lab_request.name}")
        print(f"Market: {quarterly_lab_request.market}")
        print(f"Leverage: {quarterly_lab_request.leverage}x")
        print(f"Position Mode: {'ONE-WAY' if quarterly_lab_request.position_mode == 0 else 'HEDGE'}")
        print(f"Margin Mode: {'CROSS' if quarterly_lab_request.margin_mode == 0 else 'ISOLATED'}")
        
        quarterly_lab = api.create_lab(executor, quarterly_lab_request)
        print(f"✅ Created quarterly lab: {quarterly_lab.lab_id}")
        
    except Exception as e:
        print(f"❌ Error creating labs: {e}")
        return
    
    # Demonstrate position and margin mode settings
    print("\n⚙️ Setting Position and Margin Modes")
    print("-" * 40)
    
    try:
        # Set position mode to ONE-WAY
        print("Setting position mode to ONE-WAY...")
        position_result = api.set_position_mode(
            executor,
            account_id=binance_quarterly_account.account_id,
            market=perpetual_market_tag,
            position_mode=PositionMode.ONE_WAY
        )
        print(f"✅ Position mode set: {position_result}")
        
        # Set margin mode to CROSS
        print("Setting margin mode to CROSS...")
        margin_result = api.set_margin_mode(
            executor,
            account_id=binance_quarterly_account.account_id,
            market=perpetual_market_tag,
            margin_mode=MarginMode.CROSS
        )
        print(f"✅ Margin mode set: {margin_result}")
        
        # Set leverage to 50x
        print("Setting leverage to 50x...")
        leverage_result = api.set_leverage(
            executor,
            account_id=binance_quarterly_account.account_id,
            market=perpetual_market_tag,
            leverage=50.0
        )
        print(f"✅ Leverage set: {leverage_result}")
        
    except Exception as e:
        print(f"❌ Error setting modes: {e}")
    
    # Demonstrate getting current settings
    print("\n📊 Getting Current Settings")
    print("-" * 30)
    
    try:
        # Get current position mode
        current_position = api.get_position_mode(
            executor,
            account_id=binance_quarterly_account.account_id,
            market=perpetual_market_tag
        )
        print(f"Current Position Mode: {current_position}")
        
        # Get current margin mode
        current_margin = api.get_margin_mode(
            executor,
            account_id=binance_quarterly_account.account_id,
            market=perpetual_market_tag
        )
        print(f"Current Margin Mode: {current_margin}")
        
        # Get current leverage
        current_leverage = api.get_leverage(
            executor,
            account_id=binance_quarterly_account.account_id,
            market=perpetual_market_tag
        )
        print(f"Current Leverage: {current_leverage}")
        
    except Exception as e:
        print(f"❌ Error getting settings: {e}")
    
    # Demonstrate bot creation from lab results (simulated)
    print("\n🤖 Bot Creation from Lab Results")
    print("-" * 35)
    
    try:
        # Simulate bot creation (you would need actual lab and backtest IDs)
        print("Example bot creation with futures support:")
        print(f"Lab ID: {perpetual_lab.lab_id}")
        print(f"Market: {perpetual_market_tag}")
        print(f"Account: {binance_quarterly_account.account_id}")
        print(f"Leverage: 50x")
        print(f"Position Mode: ONE-WAY")
        print(f"Margin Mode: CROSS")
        
        # This would be the actual API call when you have backtest results
        # bot_result = api.add_bot_from_lab_with_futures(
        #     executor=executor,
        #     lab_id=perpetual_lab.lab_id,
        #     backtest_id="your_backtest_id",
        #     bot_name="COINS FUTURES BOT",
        #     account_id=binance_quarterly_account.account_id,
        #     market=perpetual_market_tag,
        #     leverage=50.0,
        #     position_mode=PositionMode.ONE_WAY,
        #     margin_mode=MarginMode.CROSS
        # )
        
        print("✅ Bot creation example prepared")
        
    except Exception as e:
        print(f"❌ Error with bot creation: {e}")
    
    # Cleanup - delete the test labs
    print("\n🧹 Cleaning Up")
    print("-" * 15)
    
    try:
        # Delete perpetual lab
        api.delete_lab(executor, perpetual_lab.lab_id)
        print(f"✅ Deleted perpetual lab: {perpetual_lab.lab_id}")
        
        # Delete quarterly lab
        api.delete_lab(executor, quarterly_lab.lab_id)
        print(f"✅ Deleted quarterly lab: {quarterly_lab.lab_id}")
        
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Futures Trading Example Complete!")
    print("\n📋 Summary of Features Demonstrated:")
    print("✅ PERPETUAL and QUARTERLY contract support")
    print("✅ Position mode settings (ONE-WAY vs HEDGE)")
    print("✅ Margin mode settings (CROSS vs ISOLATED)")
    print("✅ Leverage configuration (up to 50x)")
    print("✅ Futures market tag formatting")
    print("✅ Lab creation with futures settings")
    print("✅ Bot creation from lab results")
    
    print("\n💡 Key Market Formats:")
    print(f"   Perpetual: {perpetual_market_tag}")
    print(f"   Quarterly: {quarterly_market_tag}")
    
    print("\n🔧 Key Settings:")
    print("   Position Mode: 0=ONE-WAY, 1=HEDGE")
    print("   Margin Mode: 0=CROSS, 1=ISOLATED")
    print("   Leverage: 0.0-125.0 (exchange dependent)")

if __name__ == "__main__":
    main() 