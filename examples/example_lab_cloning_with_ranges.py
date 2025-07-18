#!/usr/bin/env python3
"""
Example Script: Lab Creation, Cloning, and Parameter Range Application

This script demonstrates:
1. Creating a lab for Binance BTC/USDT market with scalper bot script
2. Cloning the lab
3. Cloning again and applying parameter ranges from 1 to 10 with step 0.5
4. Saving the final lab configuration

Requirements:
- pyHaasAPI library
- HaasOnline API running on localhost:8090
- Valid credentials
"""

import time
import os
from typing import List, Optional
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, StartLabExecutionRequest
from pyHaasAPI.parameters import ScriptParameter, ParameterRange
from config import settings
from dotenv import load_dotenv
load_dotenv()

# Configuration
HAAS_HOST = os.getenv("HAAS_API_HOST", "127.0.0.1")
HAAS_PORT = int(os.getenv("HAAS_API_PORT", "8090"))
HAAS_EMAIL = os.getenv("HAAS_API_EMAIL", "your_email@example.com")
HAAS_PASSWORD = os.getenv("HAAS_API_PASSWORD", "your_password")

# Parameter range configuration
PARAM_RANGE_START = 1.0
PARAM_RANGE_END = 10.0
PARAM_RANGE_STEP = 0.5

def authenticate() -> api.RequestsExecutor[api.Authenticated]:
    """Authenticate with HaasOnline API"""
    print("🔐 Authenticating with HaasOnline API...")
    
    try:
        executor = api.RequestsExecutor(
            host=HAAS_HOST,
            port=HAAS_PORT,
            state=api.Guest()
        ).authenticate(
            email=HAAS_EMAIL,
            password=HAAS_PASSWORD
        )
        print("✅ Authentication successful")
        return executor
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        raise

def find_scalper_script(executor: api.RequestsExecutor[api.Authenticated]):
    """Find a scalper bot script"""
    print("\n🔍 Finding scalper bot script...")
    
    # Try different scalper script names
    scalper_names = [
        "Scalper Bot",
        "Haasonline Original - Scalper Bot",
        "Scalper",
        "Scalping Bot"
    ]
    
    for name in scalper_names:
        scripts = api.get_scripts_by_name(executor, name)
        if scripts:
            script = scripts[0]
            print(f"✅ Found scalper script: {script.script_name} (ID: {script.script_id})")
            return script
    
    print("❌ No scalper bot scripts found!")
    raise Exception("No scalper bot scripts available")

def find_binance_btc_usdt_market(executor: api.RequestsExecutor[api.Authenticated]):
    """Find Binance BTC/USDT market"""
    print("\n🔍 Finding Binance BTC/USDT market...")
    
    markets = api.get_all_markets(executor)
    btc_usdt_markets = [
        m for m in markets 
        if m.primary == "BTC" and m.secondary == "USDT" and "BINANCE" in m.price_source.upper()
    ]
    
    if not btc_usdt_markets:
        print("❌ No Binance BTC/USDT markets found!")
        raise Exception("No Binance BTC/USDT markets available")
    
    market = btc_usdt_markets[0]
    print(f"✅ Found market: {market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}")
    return market

def find_account(executor: api.RequestsExecutor[api.Authenticated]):
    """Find a suitable account"""
    print("\n🔍 Finding account...")
    
    accounts = api.get_accounts(executor)
    if not accounts:
        print("❌ No accounts available!")
        raise Exception("No accounts available")
    
    # Prefer Binance accounts if available
    binance_accounts = [acc for acc in accounts if "BINANCE" in acc.exchange_code.upper()]
    account = binance_accounts[0] if binance_accounts else accounts[0]
    
    print(f"✅ Using account: {account.name} ({account.exchange_code})")
    return account

def create_initial_lab(executor: api.RequestsExecutor[api.Authenticated], script, market, account):
    """Create the initial lab"""
    print("\n🚀 Creating initial lab...")
    
    lab_name = f"Example_Scalper_BTC_USDT_{int(time.time())}"
    market_tag = f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
    
    lab = api.create_lab(
        executor,
        CreateLabRequest(
            script_id=script.script_id,
            name=lab_name,
            account_id=account.account_id,
            market=market_tag,
            interval=1,  # 1-minute interval for scalping
            default_price_data_style="CandleStick"
        )
    )
    
    print(f"✅ Created lab: {lab.name} (ID: {lab.lab_id})")
    return lab

def clone_lab(executor: api.RequestsExecutor[api.Authenticated], lab_id: str, new_name: str):
    """Clone a lab"""
    print(f"\n📋 Cloning lab to: {new_name}")
    
    cloned_lab = api.clone_lab(executor, lab_id, new_name)
    print(f"✅ Cloned lab: {cloned_lab.name} (ID: {cloned_lab.lab_id})")
    return cloned_lab

def find_parameter_keys(lab_details, target_names: List[str]) -> List[str]:
    """Find parameter keys that match target names"""
    found_keys = []
    
    for param in lab_details.parameters:
        key = param.get('K', '')
        name = key.split('.')[-1].lower() if '.' in key else key.lower()
        
        for target in target_names:
            if target.lower() in name:
                found_keys.append(key)
                print(f"  🔑 Found parameter: {key} (matches '{target}')")
                break
    
    return found_keys

def apply_parameter_ranges(executor: api.RequestsExecutor[api.Authenticated], lab_id: str, param_keys: List[str]):
    """Apply parameter ranges to the lab"""
    print(f"\n🔧 Applying parameter ranges to lab {lab_id}...")
    
    # Get current lab details
    lab_details = api.get_lab_details(executor, lab_id)
    
    # Generate range values
    range_values = []
    current = PARAM_RANGE_START
    while current <= PARAM_RANGE_END:
        range_values.append(str(current))
        current += PARAM_RANGE_STEP
    
    print(f"  📊 Parameter range: {PARAM_RANGE_START} to {PARAM_RANGE_END} (step {PARAM_RANGE_STEP})")
    print(f"  📊 Generated {len(range_values)} values: {range_values[:5]}...{range_values[-5:] if len(range_values) > 10 else ''}")
    
    # Update parameters with ranges
    updated_parameters = []
    for param in lab_details.parameters:
        key = param.get('K', '')
        if key in param_keys:
            # Apply range to this parameter
            param['O'] = range_values
            print(f"  ✅ Applied range to parameter: {key}")
        updated_parameters.append(param)
    
    # Update lab details
    lab_details.parameters = updated_parameters
    updated_lab = api.update_lab_details(executor, lab_details)
    
    print(f"✅ Lab parameters updated successfully")
    return updated_lab

def save_lab_configuration(lab_details, filename: str):
    """Save lab configuration to file"""
    print(f"\n💾 Saving lab configuration to {filename}...")
    
    try:
        import json
        from datetime import datetime
        
        config_data = {
            "lab_id": lab_details.lab_id,
            "name": lab_details.name,
            "script_id": lab_details.script_id,
            "created_at": datetime.now().isoformat(),
            "parameters": lab_details.parameters,
            "settings": lab_details.settings.model_dump() if hasattr(lab_details.settings, 'model_dump') else str(lab_details.settings),
            "config": lab_details.config.model_dump() if hasattr(lab_details.config, 'model_dump') else str(lab_details.config)
        }
        
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        print(f"✅ Configuration saved to {filename}")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not save configuration: {e}")

def main():
    """Main execution function"""
    print("🚀 Example: Lab Creation, Cloning, and Parameter Range Application")
    print("=" * 70)
    
    try:
        # Step 1: Authenticate
        executor = authenticate()
        
        # Step 2: Find required resources
        script = find_scalper_script(executor)
        market = find_binance_btc_usdt_market(executor)
        account = find_account(executor)
        
        # Step 3: Create initial lab
        original_lab = create_initial_lab(executor, script, market, account)
        
        # Step 4: Clone the lab
        cloned_lab_1 = clone_lab(executor, original_lab.lab_id, f"Clone_1_{original_lab.name}")
        
        # Step 5: Clone again
        cloned_lab_2 = clone_lab(executor, original_lab.lab_id, f"Clone_2_{original_lab.name}")
        
        # Step 6: Find parameters to apply ranges to
        print(f"\n🔍 Finding parameters in lab {cloned_lab_2.lab_id}...")
        lab_details = api.get_lab_details(executor, cloned_lab_2.lab_id)
        
        # Look for common scalper parameters
        target_param_names = [
            "stop loss", "take profit", "profit target", "loss limit",
            "entry delay", "exit delay", "timeout", "threshold",
            "multiplier", "factor", "ratio", "percentage"
        ]
        
        param_keys = find_parameter_keys(lab_details, target_param_names)
        
        if not param_keys:
            print("⚠️ No suitable parameters found for range application")
            print("  Available parameters:")
            for param in lab_details.parameters[:10]:  # Show first 10
                key = param.get('K', '')
                name = key.split('.')[-1] if '.' in key else key
                print(f"    - {name}")
        else:
            # Step 7: Apply parameter ranges
            updated_lab = apply_parameter_ranges(executor, cloned_lab_2.lab_id, param_keys)
            
            # Step 8: Save configuration
            save_lab_configuration(updated_lab, f"lab_config_{updated_lab.lab_id}.json")
        
        # Summary
        print("\n📋 SUMMARY")
        print("=" * 30)
        print(f"✅ Original lab created: {original_lab.name} (ID: {original_lab.lab_id})")
        print(f"✅ First clone created: {cloned_lab_1.name} (ID: {cloned_lab_1.lab_id})")
        print(f"✅ Second clone created: {cloned_lab_2.name} (ID: {cloned_lab_2.lab_id})")
        
        if param_keys:
            print(f"✅ Parameter ranges applied to {len(param_keys)} parameters")
            print(f"✅ Range: {PARAM_RANGE_START} to {PARAM_RANGE_END} (step {PARAM_RANGE_STEP})")
        
        print(f"\n🎉 Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Place the main execution logic here
    pass 