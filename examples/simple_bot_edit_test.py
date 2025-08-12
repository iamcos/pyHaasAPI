#!/usr/bin/env python3
"""
Simple test to debug bot settings editing
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api
from pyHaasAPI.model import HaasScriptSettings
from pyHaasAPI.exceptions import HaasApiError

# Load environment variables
load_dotenv()

def main():
    """Main test function."""
    print("🔍 Debugging Bot Settings Editing")
    print("=" * 40)
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        ip = os.getenv("API_HOST", "127.0.0.1")
        port = int(os.getenv("API_PORT", "8090"))
        email = os.getenv("API_EMAIL")
        password = os.getenv("API_PASSWORD")
        
        if not email or not password:
            print("❌ Missing API credentials. Please set API_EMAIL and API_PASSWORD in your .env file.")
            return
        
        executor = api.RequestsExecutor(host=ip, port=port, state=api.Guest())
        authenticated_executor = executor.authenticate(email=email, password=password)
        print("✅ Authentication successful!")
        
        # Get all bots
        print("\n📋 Getting all bots...")
        bots = api.get_all_bots(authenticated_executor)
        
        if not bots:
            print("❌ No bots found.")
            return
        
        # Select the first bot
        bot = bots[0]
        print(f"✅ Selected bot: {bot.bot_name} (ID: {bot.bot_id})")
        
        # Get detailed bot info
        print(f"\n📊 Bot Details:")
        detailed_bot = api.get_bot(authenticated_executor, bot.bot_id)
        print(f"  Bot Name: {detailed_bot.bot_name}")
        print(f"  Script ID: {detailed_bot.script_id}")
        print(f"  Account ID: {detailed_bot.account_id}")
        print(f"  Market: {detailed_bot.market}")
        print(f"  Is Activated: {detailed_bot.is_activated}")
        print(f"  Is Paused: {detailed_bot.is_paused}")
        
        # Get current settings
        print(f"\n⚙️ Current Settings:")
        print(f"  Trade Amount: {detailed_bot.settings.trade_amount}")
        print(f"  Leverage: {detailed_bot.settings.leverage}")
        print(f"  Interval: {detailed_bot.settings.interval}")
        print(f"  Chart Style: {detailed_bot.settings.chart_style}")
        print(f"  Position Mode: {detailed_bot.settings.position_mode}")
        print(f"  Margin Mode: {detailed_bot.settings.margin_mode}")
        
        # Get script parameters
        print(f"\n🔧 Script Parameters:")
        try:
            script_params = api.get_bot_script_parameters(authenticated_executor, bot.bot_id)
            print(f"  Found {len(script_params)} parameters")
            
            # Show first few parameters
            for i, (param_name, param_value) in enumerate(script_params.items()):
                if i < 3:  # Show first 3 parameters
                    print(f"    {param_name}: {param_value}")
                else:
                    break
        except Exception as e:
            print(f"  Error getting script parameters: {e}")
        
        # Try a minimal edit - just change trade amount
        print(f"\n💰 Testing minimal trade amount edit...")
        current_amount = detailed_bot.settings.trade_amount
        new_amount = current_amount + 10.0
        
        print(f"  Current: {current_amount}")
        print(f"  New: {new_amount}")
        
        # Create minimal settings update
        updated_settings = HaasScriptSettings(
            trade_amount=new_amount
        )
        
        print(f"  Settings object: {updated_settings.model_dump_json(by_alias=True)}")
        
        # Try the edit
        try:
            updated_bot = api.edit_bot_settings(
                authenticated_executor, 
                bot.bot_id, 
                detailed_bot.script_id, 
                updated_settings
            )
            print(f"✅ Edit successful! Updated bot: {updated_bot.bot_name}")
            
            # Verify the change
            verify_bot = api.get_bot(authenticated_executor, bot.bot_id)
            print(f"  Verified trade amount: {verify_bot.settings.trade_amount}")
            
        except HaasApiError as e:
            print(f"❌ Edit failed with HaasApiError: {e}")
        except Exception as e:
            print(f"❌ Edit failed with Exception: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 