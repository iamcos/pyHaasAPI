#!/usr/bin/env python3
"""
Simple example demonstrating bot settings editing functionality.

This example shows how to:
1. Get a bot's current settings
2. Edit various bot settings
3. Verify the changes

Usage:
    python examples/bot_settings_editing_example.py
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api
from pyHaasAPI.model import HaasScriptSettings
from pyHaasAPI.exceptions import HaasApiError

# Load environment variables
load_dotenv()

def main():
    """Main example function."""
    print("🤖 Bot Settings Editing Example")
    print("=" * 40)
    
    try:
        # Authenticate with the API
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
            print("❌ No bots found. Please create a bot first.")
            return
        
        # Select the first bot for editing
        bot = bots[0]
        print(f"✅ Selected bot: {bot.bot_name} (ID: {bot.bot_id})")
        
        # Display current settings
        print(f"\n📊 Current Bot Settings:")
        print(f"  Bot Name: {bot.bot_name}")
        print(f"  Trade Amount: {bot.settings.trade_amount}")
        print(f"  Leverage: {bot.settings.leverage}")
        print(f"  Interval: {bot.settings.interval}")
        print(f"  Chart Style: {bot.settings.chart_style}")
        print(f"  Position Mode: {bot.settings.position_mode}")
        print(f"  Margin Mode: {bot.settings.margin_mode}")
        
        # Get script parameters
        try:
            script_params = api.get_bot_script_parameters(authenticated_executor, bot.bot_id)
            print(f"  Script Parameters: {len(script_params)} parameters")
            for param_name, param_value in script_params.items():
                print(f"    {param_name}: {param_value}")
        except Exception as e:
            print(f"  Script Parameters: Unable to retrieve ({e})")
        
        # Example 1: Edit trade amount
        print(f"\n💰 Example 1: Editing Trade Amount")
        current_amount = bot.settings.trade_amount
        new_amount = current_amount * 1.5  # Increase by 50%
        
        print(f"  Current: {current_amount}")
        print(f"  New: {new_amount}")
        
        updated_settings = HaasScriptSettings(trade_amount=new_amount)
        updated_bot = api.edit_bot_settings(authenticated_executor, bot.bot_id, bot.script_id, updated_settings)
        print(f"✅ Trade amount updated successfully!")
        
        # Example 2: Edit leverage
        print(f"\n⚖️ Example 2: Editing Leverage")
        current_leverage = bot.settings.leverage
        new_leverage = current_leverage + 2.0
        
        print(f"  Current: {current_leverage}")
        print(f"  New: {new_leverage}")
        
        updated_settings = HaasScriptSettings(leverage=new_leverage)
        updated_bot = api.edit_bot_settings(authenticated_executor, bot.bot_id, bot.script_id, updated_settings)
        print(f"✅ Leverage updated successfully!")
        
        # Example 3: Edit chart settings
        print(f"\n📊 Example 3: Editing Chart Settings")
        current_interval = bot.settings.interval
        current_chart_style = bot.settings.chart_style
        new_interval = current_interval + 5
        new_chart_style = current_chart_style + 1
        
        print(f"  Current interval: {current_interval} -> New: {new_interval}")
        print(f"  Current chart style: {current_chart_style} -> New: {new_chart_style}")
        
        updated_settings = HaasScriptSettings(
            interval=new_interval,
            chart_style=new_chart_style
        )
        updated_bot = api.edit_bot_settings(authenticated_executor, bot.bot_id, bot.script_id, updated_settings)
        print(f"✅ Chart settings updated successfully!")
        
        # Example 4: Edit script parameters (if available)
        try:
            script_params = api.get_bot_script_parameters(authenticated_executor, bot.bot_id)
            if script_params:
                print(f"\n🔧 Example 4: Editing Script Parameters")
                param_name = list(script_params.keys())[0]
                current_value = script_params[param_name]
                
                # Determine new value based on type
                if isinstance(current_value, (int, float)):
                    new_value = current_value + 1
                elif isinstance(current_value, bool):
                    new_value = not current_value
                else:
                    new_value = f"edited_{int(time.time())}"
                
                print(f"  Parameter: {param_name}")
                print(f"  Current value: {current_value}")
                print(f"  New value: {new_value}")
                
                updated_settings = HaasScriptSettings(
                    script_parameters={param_name: new_value}
                )
                updated_bot = api.edit_bot_settings(authenticated_executor, bot.bot_id, bot.script_id, updated_settings)
                print(f"✅ Script parameter updated successfully!")
            else:
                print(f"\n🔧 Example 4: No script parameters available to edit")
        except Exception as e:
            print(f"\n🔧 Example 4: Unable to edit script parameters ({e})")
        
        # Example 5: Edit multiple settings at once
        print(f"\n🎯 Example 5: Editing Multiple Settings")
        
        # Get current bot again to have latest values
        current_bot = api.get_bot(authenticated_executor, bot.bot_id)
        
        new_trade_amount = current_bot.settings.trade_amount * 0.8  # Decrease by 20%
        new_leverage = current_bot.settings.leverage - 1.0
        new_interval = current_bot.settings.interval - 5 if current_bot.settings.interval > 10 else 15
        
        print(f"  Trade Amount: {current_bot.settings.trade_amount} -> {new_trade_amount}")
        print(f"  Leverage: {current_bot.settings.leverage} -> {new_leverage}")
        print(f"  Interval: {current_bot.settings.interval} -> {new_interval}")
        
        updated_settings = HaasScriptSettings(
            trade_amount=new_trade_amount,
            leverage=new_leverage,
            interval=new_interval
        )
        updated_bot = api.edit_bot_settings(authenticated_executor, bot.bot_id, bot.script_id, updated_settings)
        print(f"✅ Multiple settings updated successfully!")
        
        # Verify final state
        print(f"\n📋 Final Bot Settings:")
        final_bot = api.get_bot(authenticated_executor, bot.bot_id)
        print(f"  Bot Name: {final_bot.bot_name}")
        print(f"  Trade Amount: {final_bot.settings.trade_amount}")
        print(f"  Leverage: {final_bot.settings.leverage}")
        print(f"  Interval: {final_bot.settings.interval}")
        print(f"  Chart Style: {final_bot.settings.chart_style}")
        
        print(f"\n🎉 Bot settings editing example completed successfully!")
        
    except HaasApiError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 