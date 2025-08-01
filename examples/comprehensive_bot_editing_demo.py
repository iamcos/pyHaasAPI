#!/usr/bin/env python3
"""
Comprehensive Bot Editing Demo

This script demonstrates all the enhanced bot editing capabilities:
- Individual parameter editing by name
- Group-based parameter editing
- Parameter validation
- Comprehensive bot data retrieval
- Parameter metadata and constraints
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path to import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI.api import RequestsExecutor, Guest
from pyHaasAPI.bot_editing_api import (
    get_comprehensive_bot,
    edit_bot_parameter_by_name,
    edit_bot_parameters_by_group,
    validate_bot_parameters,
    get_bot_parameter_groups,
    get_bot_parameter_metadata,
    get_bot_closed_positions
)

# Load environment variables
load_dotenv()

def main():
    # Get credentials from environment
    email = os.getenv("API_EMAIL")
    password = os.getenv("API_PASSWORD")
    
    if not email or not password:
        print("❌ Error: API_EMAIL and API_PASSWORD must be set in .env file")
        return
    
    # Bot ID to work with
    bot_id = "6dcbbe90f464401e807dbae2bca5b279"
    
    print("🔐 Authenticating...")
    try:
        # Create executor and authenticate
        executor = RequestsExecutor(host="127.0.0.1", port=8090, state=Guest())
        authenticated_executor = executor.authenticate(email, password)
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    print(f"\n🤖 Working with bot: {bot_id}")
    
    try:
        # 1. Get comprehensive bot data (mimics web interface)
        print("\n📊 1. Getting comprehensive bot data...")
        comprehensive_bot = get_comprehensive_bot(authenticated_executor, bot_id)
        
        print(f"   Basic Info: {comprehensive_bot['basic_info']['BN']}")
        print(f"   Runtime Data Keys: {list(comprehensive_bot['runtime_data'].keys())}")
        print(f"   Recent Logs: {len(comprehensive_bot['recent_logs'])} entries")
        print(f"   Closed Positions: {len(comprehensive_bot['closed_positions'])} positions")
        print(f"   Script Parameters: {len(comprehensive_bot['script_parameters'])} parameters")
        
        # 2. Get parameter groups
        print("\n📋 2. Getting parameter groups...")
        groups = get_bot_parameter_groups(authenticated_executor, bot_id)
        
        for group_name, params in groups.items():
            print(f"   Group '{group_name}': {len(params)} parameters")
            for param in params[:3]:  # Show first 3 parameters
                print(f"     - {param}")
            if len(params) > 3:
                print(f"     ... and {len(params) - 3} more")
        
        # 3. Get detailed parameter metadata
        print("\n🔍 3. Getting parameter metadata...")
        metadata = get_bot_parameter_metadata(authenticated_executor, bot_id)
        
        # Show a few examples
        for i, (param_name, meta) in enumerate(metadata.items()):
            if i >= 3:  # Show first 3 parameters
                break
            print(f"   Parameter: {param_name}")
            print(f"     Type: {meta['type']}")
            print(f"     Min: {meta['min']}, Max: {meta['max']}, Step: {meta['step']}")
            print(f"     Group: {meta['group']}")
            print(f"     Current Value: {meta['current_value']}")
            if meta['options']:
                print(f"     Options: {list(meta['options'].keys())}")
            print()
        
        # 4. Validate some parameter changes
        print("\n✅ 4. Validating parameter changes...")
        test_changes = {
            "Stop Loss (%)": 10,
            "Take Profit (%)": 15,
            "BBands Length": 20,
            "RSI Buy Level": 25
        }
        
        validation_result = validate_bot_parameters(authenticated_executor, bot_id, test_changes)
        
        print(f"   Valid parameters: {validation_result['valid']}")
        print(f"   Invalid parameters: {validation_result['invalid']}")
        
        # 5. Edit a single parameter
        print("\n✏️ 5. Editing single parameter...")
        try:
            updated_bot = edit_bot_parameter_by_name(
                authenticated_executor, 
                bot_id, 
                "Stop Loss (%)", 
                8
            )
            print(f"   ✅ Successfully updated 'Stop Loss (%)' to 8")
            print(f"   Bot name: {updated_bot.bot_name}")
        except Exception as e:
            print(f"   ❌ Failed to update parameter: {e}")
        
        # 6. Edit multiple parameters in a group
        print("\n📝 6. Editing parameters by group...")
        try:
            bb_group_changes = {
                "BBands Length": 15,
                "BBands DevUp": 2.5,
                "BBands DevDown": 2.5
            }
            
            updated_bot = edit_bot_parameters_by_group(
                authenticated_executor,
                bot_id,
                "MadHatter BBands",
                bb_group_changes
            )
            print(f"   ✅ Successfully updated {len(bb_group_changes)} BBands parameters")
            print(f"   Bot name: {updated_bot.bot_name}")
        except Exception as e:
            print(f"   ❌ Failed to update group parameters: {e}")
        
        # 7. Get closed positions
        print("\n📈 7. Getting closed positions...")
        closed_positions = get_bot_closed_positions(authenticated_executor, bot_id)
        print(f"   Found {len(closed_positions)} closed positions")
        
        if closed_positions:
            # Show details of the most recent position
            latest_position = closed_positions[0]
            print(f"   Latest position:")
            print(f"     Market: {latest_position.get('Market', 'N/A')}")
            print(f"     Side: {latest_position.get('Side', 'N/A')}")
            print(f"     Amount: {latest_position.get('Amount', 'N/A')}")
            print(f"     PnL: {latest_position.get('PnL', 'N/A')}")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 