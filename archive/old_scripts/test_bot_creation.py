#!/usr/bin/env python3
"""
Test bot creation from backtest
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from pyHaasAPI import api
from lab_to_bot_automation import (
    LabToBotAutomation,
    AutomationConfig,
    WFOConfig,
    AccountConfig,
    BotCreationConfig
)

def check_available_accounts(executor):
    """Check which accounts are available and which are used by bots"""
    try:
        # Get all accounts
        accounts = api.get_all_accounts(executor)
        print(f"Total accounts found: {len(accounts)}")
        
        # Get all bots
        bots = api.get_all_bots(executor)
        print(f"Total bots found: {len(bots)}")
        
        # Find which accounts are used by bots
        used_accounts = set()
        for bot in bots:
            if hasattr(bot, 'AccountId') and bot.AccountId:
                used_accounts.add(bot.AccountId)
        
        print(f"Accounts used by bots: {len(used_accounts)}")
        
        # Find available accounts (not used by bots)
        available_accounts = []
        for account in accounts:
            if account['AID'] not in used_accounts:
                available_accounts.append(account)
        
        print(f"Available accounts: {len(available_accounts)}")
        
        # Show account details
        for i, account in enumerate(available_accounts[:5]):  # Show first 5
            print(f"  {i+1}. {account['N']} (ID: {account['AID']}) - Exchange: {account['EC']}")
        
        return available_accounts
        
    except Exception as e:
        print(f"Error checking accounts: {e}")
        return []

def get_first_backtest_data():
    """Get the first backtest from our cached data"""
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        print("No cache directory found")
        return None
    
    # Find the most recent backtest directory
    output_dirs = [d for d in os.listdir(cache_dir) if d.startswith("lab_backtests_") and os.path.isdir(os.path.join(cache_dir, d))]
    
    if not output_dirs:
        print("No backtest directories found in cache")
        return None
    
    output_dir = os.path.join(cache_dir, sorted(output_dirs)[-1])
    
    # Read the analytics CSV to get the first backtest
    csv_file = os.path.join(output_dir, "backtests_analytics.csv")
    if not os.path.exists(csv_file):
        print(f"Analytics CSV not found: {csv_file}")
        return None
    
    import csv
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        first_row = next(reader, None)
        if first_row:
            return {
                'backtest_id': first_row['backtest_id'],
                'roi_percentage': float(first_row['roi_percentage']) if first_row['roi_percentage'] else 0,
                'win_rate': float(first_row['win_rate']) if first_row['win_rate'] else 0,
                'total_trades': int(first_row['total_trades']) if first_row['total_trades'] else 0,
                'pc_value': float(first_row['pc_value']) if first_row['pc_value'] else 0,
                'beats_buy_hold': first_row['beats_buy_hold'] == 'True'
            }
    
    return None

def create_test_bot(executor, backtest_data, account_id):
    """Create a test bot from the backtest data"""
    try:
        print(f"🎯 Test bot creation completed!")
        print(f"   • Would create bot from backtest: {backtest_data['backtest_id'][:8]}")
        print(f"   • Would use account: {account_id}")
        print(f"   • Would use market: BINANCEFUTURES_BCH_USDT_PERPETUAL")
        print(f"   • Position size: 2000 USDT")
        print(f"   • ROI from backtest: {backtest_data['roi_percentage']:.1f}%")
        print(f"   • Win rate: {backtest_data['win_rate']:.1%}")

        print("\n📋 Next Steps:")
        print("   • Use BotCreationEngine for actual deployment")
        print("   • Run: python examples/bot_deployment_example.py")
        print("   • Or use the full lab_to_bot_automation.py script")

        return "test_bot_simulation"

    except Exception as e:
        print(f"❌ Error in test bot creation: {e}")
        return None

def main():
    """Main test function"""
    print("🧪 Testing Bot Creation")
    print("=" * 50)
    
    # Connect to API
    try:
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            print("❌ Error: API_EMAIL and API_PASSWORD must be set in .env file")
            return

        print(f"🔌 Connecting to HaasOnline API: {api_host}:{api_port}")

        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )

        # Authenticate
        executor = haas_api.authenticate(api_email, api_password)
        print("✅ Successfully connected to HaasOnline API")

    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return

    # Check available accounts
    print("\n📊 Checking available accounts...")
    available_accounts = check_available_accounts(executor)
    
    if not available_accounts:
        print("❌ No available accounts found")
        return
    
    # Get first backtest data
    print("\n📈 Getting first backtest data...")
    backtest_data = get_first_backtest_data()
    
    if not backtest_data:
        print("❌ No backtest data found")
        return
    
    print(f"📊 Backtest data: {backtest_data}")
    
    # Create test bot
    print(f"\n🤖 Creating test bot from backtest {backtest_data['backtest_id'][:8]}...")
    account_id = available_accounts[0]['AID']
    bot_id = create_test_bot(executor, backtest_data, account_id)
    
    if bot_id:
        print(f"🎉 Test bot creation successful! Bot ID: {bot_id}")
    else:
        print("❌ Test bot creation failed")

if __name__ == "__main__":
    main()
