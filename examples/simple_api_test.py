#!/usr/bin/env python3
"""
Simple test script for new API functions
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

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
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
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
    print("\n\ud83d\udcc1 Testing script folder listing...")
    try:
        folders = api.get_all_script_folders(executor)
        print(f"\u2705 Found {len(folders)} script folders")
        for folder in folders:
            print(f"   - Folder ID: {folder.folder_id}, Name: {folder.name}, Parent: {folder.parent_id}")
    except Exception as e:
        print(f"\u274c Script folder listing failed: {e}")

    # Test get_all_orders
    print("\n\ud83d\udcb0 Testing get_all_orders (all open orders for all accounts)...")
    try:
        all_orders = api.get_all_orders(executor)
        print(f"\u2705 Got open orders for {len(all_orders)} accounts")
        for account_orders in all_orders:
            aid = account_orders.get('AID', '(unknown)')
            orders = account_orders.get('I', [])
            print(f"   - Account: {aid}, {len(orders)} open orders")
            for order in orders:
                print(f"      OID: {order.get('OID')}, Market: {order.get('M')}, Price: {order.get('OP')}, Amount: {order.get('OA')}, Status: {order.get('S')}")
    except Exception as e:
        print(f"\u274c get_all_orders failed: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 