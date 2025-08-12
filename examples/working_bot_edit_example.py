#!/usr/bin/env python3
"""
Working example demonstrating bot settings editing functionality.

This example uses the edit_bot_parameter function which takes a full HaasBot object
and modifies its settings, which is more reliable than edit_bot_settings.

Usage:
    python examples/working_bot_edit_example.py
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api
from pyHaasAPI.exceptions import HaasApiError

# Load environment variables
load_dotenv()

def main():
    """Main example function."""
    print("🤖 Working Bot Settings Editing Example")
    print("=" * 50)
    
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
        
        # Get detailed bot info
        detailed_bot = api.get_bot(authenticated_executor, bot.bot_id)
        
        # Display current settings
        print(f"\n📊 Current Bot Settings:")
        print(f"  Bot Name: {detailed_bot.bot_name}")
        print(f"  Trade Amount: {detailed_bot.settings.trade_amount}")
        print(f"  Leverage: {detailed_bot.settings.leverage}")
        print(f"  Interval: {detailed_bot.settings.interval}")
        print(f"  Chart Style: {detailed_bot.settings.chart_style}")
        print(f"  Position Mode: {detailed_bot.settings.position_mode}")
        print(f"  Margin Mode: {detailed_bot.settings.margin_mode}")
        
        # Get script parameters
        try:
            script_params = api.get_bot_script_parameters(authenticated_executor, bot.bot_id)
            print(f"  Script Parameters: {len(script_params)} parameters")
            for param_name, param_value in script_params.items():
                print(f"    {param_name}: {param_value}")
        except Exception as e:
            print(f"  Script Parameters: Unable to retrieve ({e})")
        
        # Example 1: Edit trade amount using edit_bot_parameter
        print(f"\n💰 Example 1: Editing Trade Amount")
        current_amount = detailed_bot.settings.trade_amount
        new_amount = current_amount * 1.5  # Increase by 50%
        
        print(f"  Current: {current_amount}")
        print(f"  New: {new_amount}")
        
        # Modify the bot's settings directly
        detailed_bot.settings.trade_amount = new_amount
        
        # Use edit_bot_parameter with the modified bot
        updated_bot = api.edit_bot_parameter(authenticated_executor, detailed_bot)
        print(f"✅ Trade amount updated successfully!")
        print(f"  Updated bot name: {updated_bot.bot_name}")
        
        # Example 2: Edit leverage
        print(f"\n⚖️ Example 2: Editing Leverage")
        current_leverage = updated_bot.settings.leverage
        new_leverage = current_leverage + 2.0
        
        print(f"  Current: {current_leverage}")
        print(f"  New: {new_leverage}")
        
        # Modify the bot's settings
        updated_bot.settings.leverage = new_leverage
        
        # Use edit_bot_parameter
        updated_bot = api.edit_bot_parameter(authenticated_executor, updated_bot)
        print(f"✅ Leverage updated successfully!")
        print(f"  Updated bot name: {updated_bot.bot_name}")
        
        # Example 3: Edit chart settings
        print(f"\n📊 Example 3: Editing Chart Settings")
        current_interval = updated_bot.settings.interval
        current_chart_style = updated_bot.settings.chart_style
        new_interval = current_interval + 5
        new_chart_style = current_chart_style + 1
        
        print(f"  Current interval: {current_interval} -> New: {new_interval}")
        print(f"  Current chart style: {current_chart_style} -> New: {new_chart_style}")
        
        # Modify the bot's settings
        updated_bot.settings.interval = new_interval
        updated_bot.settings.chart_style = new_chart_style
        
        # Use edit_bot_parameter
        updated_bot = api.edit_bot_parameter(authenticated_executor, updated_bot)
        print(f"✅ Chart settings updated successfully!")
        print(f"  Updated bot name: {updated_bot.bot_name}")
        
        # Example 4: Edit script parameters (if available)
        try:
            script_params = api.get_bot_script_parameters(authenticated_executor, bot.bot_id)
            if script_params:
                print(f"\n🔧 Example 4: Editing Script Parameters")
                param_name = list(script_params.keys())[0]
                current_value = script_params[param_name]
                
                # Determine new value based on type
                if isinstance(current_value, dict) and 'V' in current_value:
                    current_param_value = current_value['V']
                    if isinstance(current_param_value, str) and current_param_value.isdigit():
                        new_param_value = str(int(current_param_value) + 1)
                    elif isinstance(current_param_value, str):
                        new_param_value = f"edited_{int(time.time())}"
                    else:
                        new_param_value = current_param_value
                else:
                    new_param_value = f"edited_{int(time.time())}"
                
                print(f"  Parameter: {param_name}")
                print(f"  Current value: {current_value}")
                print(f"  New value: {new_param_value}")
                
                # Modify the bot's script parameters
                if not updated_bot.settings.script_parameters:
                    updated_bot.settings.script_parameters = {}
                updated_bot.settings.script_parameters[param_name] = new_param_value
                
                # Use edit_bot_parameter
                updated_bot = api.edit_bot_parameter(authenticated_executor, updated_bot)
                print(f"✅ Script parameter updated successfully!")
                print(f"  Updated bot name: {updated_bot.bot_name}")
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
        
        # Modify multiple settings
        current_bot.settings.trade_amount = new_trade_amount
        current_bot.settings.leverage = new_leverage
        current_bot.settings.interval = new_interval
        
        # Use edit_bot_parameter
        updated_bot = api.edit_bot_parameter(authenticated_executor, current_bot)
        print(f"✅ Multiple settings updated successfully!")
        print(f"  Updated bot name: {updated_bot.bot_name}")
        
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