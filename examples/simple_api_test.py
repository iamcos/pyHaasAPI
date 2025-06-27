#!/usr/bin/env python3
"""
Simple test script for new API functions
"""

import random
from pyHaasAPI import api

def main():
    print("🚀 Testing new API functions...")
    
    # Setup
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    
    print("✅ Authentication successful")
    
    # Test market data
    print("\n📊 Testing market data...")
    markets = api.get_all_markets(executor)
    print(f"✅ Found {len(markets)} markets")
    
    if markets:
        market = random.choice(markets)
        print(f"🎯 Testing with market: {market.primary}/{market.secondary}")
        
        try:
            price = api.get_market_price(executor, market.market)
            print(f"✅ Market price: {price}")
        except Exception as e:
            print(f"❌ Market price failed: {e}")
    
    # Test account management
    print("\n💰 Testing account management...")
    accounts = api.get_accounts(executor)
    print(f"✅ Found {len(accounts)} accounts")
    
    if accounts:
        account = random.choice(accounts)
        print(f"🎯 Testing with account: {account.name}")
        
        try:
            balance = api.get_account_balance(executor, account.account_id)
            print(f"✅ Account balance: {balance}")
        except Exception as e:
            print(f"❌ Account balance failed: {e}")
    
    # Test bot management
    print("\n🤖 Testing bot management...")
    bots = api.get_all_bots(executor)
    print(f"✅ Found {len(bots)} bots")
    
    if bots:
        bot = random.choice(bots)
        print(f"🎯 Testing with bot: {bot.bot_name}")
        
        try:
            bot_details = api.get_bot(executor, bot.bot_id)
            print(f"✅ Bot details: {bot_details.bot_name}")
        except Exception as e:
            print(f"❌ Bot details failed: {e}")
    
    # Test script folder listing
    print("\n📁 Testing script folder listing...")
    try:
        folders = api.get_all_script_folders(executor)
        print(f"✅ Found {len(folders)} script folders")
        for folder in folders:
            print(f"   - Folder ID: {folder.folder_id}, Name: {folder.name}, Parent: {folder.parent_id}")
    except Exception as e:
        print(f"❌ Script folder listing failed: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main() 