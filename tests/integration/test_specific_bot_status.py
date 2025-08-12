#!/usr/bin/env python3
"""
Check settings for a specific bot
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api
from pyHaasAPI.exceptions import HaasApiError

# Load environment variables
load_dotenv()

def check_bot_settings(bot_id: str):
    """Check settings for a specific bot."""
    try:
        # Get credentials from environment
        ip = os.getenv("API_HOST", "127.0.0.1")
        port = int(os.getenv("API_PORT", "8090"))
        email = os.getenv("API_EMAIL")
        password = os.getenv("API_PASSWORD")
        
        if not email or not password:
            print("❌ Missing API credentials. Please set API_EMAIL and API_PASSWORD in your .env file.")
            return
        
        print(f"🔐 Authenticating...")
        executor = api.RequestsExecutor(host=ip, port=port, state=api.Guest())
        authenticated_executor = executor.authenticate(email=email, password=password)
        print("✅ Authentication successful!")
        
        # Get the specific bot
        print(f"\n📋 Getting bot {bot_id}...")
        bot = api.get_bot(authenticated_executor, bot_id)
        
        print(f"\n🤖 Bot Details:")
        print(f"  Bot Name: {bot.bot_name}")
        print(f"  Bot ID: {bot.bot_id}")
        print(f"  Script ID: {bot.script_id}")
        print(f"  Account ID: {bot.account_id}")
        print(f"  Market: {bot.market}")
        print(f"  Is Activated: {bot.is_activated}")
        print(f"  Is Paused: {bot.is_paused}")
        
        print(f"\n⚙️ Bot Settings:")
        print(f"  Trade Amount: {bot.settings.trade_amount}")
        print(f"  Leverage: {bot.settings.leverage}")
        print(f"  Interval: {bot.settings.interval}")
        print(f"  Chart Style: {bot.settings.chart_style}")
        print(f"  Position Mode: {bot.settings.position_mode}")
        print(f"  Margin Mode: {bot.settings.margin_mode}")
        print(f"  Order Template: {bot.settings.order_template}")
        
        # Get script parameters
        print(f"\n🔧 Script Parameters:")
        try:
            script_params = api.get_bot_script_parameters(authenticated_executor, bot_id)
            print(f"  Found {len(script_params)} parameters:")
            
            for param_name, param_value in script_params.items():
                if isinstance(param_value, dict) and 'V' in param_value:
                    actual_value = param_value['V']
                    param_type = param_value.get('T', 'Unknown')
                    min_val = param_value.get('MIN', 'N/A')
                    max_val = param_value.get('MAX', 'N/A')
                    step_val = param_value.get('ST', 'N/A')
                    group = param_value.get('G', 'N/A')
                    key = param_value.get('K', 'N/A')
                    extended_key = param_value.get('EK', 'N/A')
                    name = param_value.get('N', 'N/A')
                    tooltip = param_value.get('TT', 'N/A')
                    description = param_value.get('D', 'N/A')
                    options = param_value.get('O', None)
                    
                    print(f"    {param_name}:")
                    print(f"      Value: {actual_value}")
                    print(f"      Type: {param_type}")
                    print(f"      Min: {min_val}")
                    print(f"      Max: {max_val}")
                    print(f"      Step: {step_val}")
                    print(f"      Group: {group}")
                    print(f"      Key: {key}")
                    print(f"      Extended Key: {extended_key}")
                    print(f"      Name: {name}")
                    print(f"      Tooltip: {tooltip}")
                    print(f"      Description: {description}")
                    
                    if options:
                        print(f"      Options: {options}")
                    
                    print()
                else:
                    print(f"    {param_name}: {param_value}")
                    
        except Exception as e:
            print(f"  Error getting script parameters: {e}")
        
    except HaasApiError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_specific_bot.py <bot_id>")
        sys.exit(1)
    
    bot_id = sys.argv[1]
    check_bot_settings(bot_id) 