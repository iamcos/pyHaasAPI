#!/usr/bin/env python3
"""
Simple Example: Lab Creation, Cloning, and Parameter Ranges

This script demonstrates the core functionality:
1. Create a lab for Binance BTC/USDT with scalper bot
2. Clone the lab twice
3. Apply parameter ranges (1 to 10, step 0.5) to the second clone
4. Clone the lab with ranges (third clone)
5. Save the configuration
"""

import time
import os
from dotenv import load_dotenv
load_dotenv()
# Credentials must be set in your .env file as HAAS_API_HOST, HAAS_API_PORT, HAAS_API_EMAIL, HAAS_API_PASSWORD
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest

# Configuration
HAAS_HOST = os.getenv("HAAS_API_HOST")
HAAS_PORT = int(os.getenv("HAAS_API_PORT"))
HAAS_EMAIL = os.getenv("HAAS_API_EMAIL")
HAAS_PASSWORD = os.getenv("HAAS_API_PASSWORD")

def main():
    print("🚀 Simple Lab Cloning Example")
    print("=" * 40)
    
    try:
        # 1. Authenticate
        print("🔐 Authenticating...")
        executor = api.RequestsExecutor(
            host=HAAS_HOST,
            port=HAAS_PORT,
            state=api.Guest()
        ).authenticate(
            email=HAAS_EMAIL,
            password=HAAS_PASSWORD
        )
        print("✅ Authenticated")
        
        # 2. Find scalper script
        print("\n🔍 Finding scalper script...")
        scripts = api.get_scripts_by_name(executor, "Scalper Bot")
        if not scripts:
            print("❌ No scalper bot found!")
            return
        script = scripts[0]
        print(f"✅ Found: {script.script_name}")
        
        # 3. Find Binance BTC/USDT market
        print("\n🔍 Finding Binance BTC/USDT market...")
        markets = api.get_all_markets(executor)
        btc_market = None
        for market in markets:
            if (market.primary == "BTC" and market.secondary == "USDT" and 
                "BINANCE" in market.price_source.upper()):
                btc_market = market
                break
        
        if not btc_market:
            print("❌ No Binance BTC/USDT market found!")
            return
        print(f"✅ Found: {btc_market.price_source}_{btc_market.primary}_{btc_market.secondary}")
        
        # 4. Find account
        print("\n🔍 Finding account...")
        accounts = api.get_accounts(executor)
        if not accounts:
            print("❌ No accounts found!")
            return
        account = accounts[0]
        print(f"✅ Using: {account.name}")
        
        # 5. Create initial lab
        print("\n🚀 Creating initial lab...")
        lab_name = f"Example_Lab_{int(time.time())}"
        market_tag = f"{btc_market.price_source.upper()}_{btc_market.primary.upper()}_{btc_market.secondary.upper()}_"
        
        original_lab = api.create_lab(
            executor,
            CreateLabRequest(
                script_id=script.script_id,
                name=lab_name,
                account_id=account.account_id,
                market=market_tag,
                interval=1,
                default_price_data_style="CandleStick"
            )
        )
        print(f"✅ Created: {original_lab.name} (ID: {original_lab.lab_id})")
        
        # 6. Clone the lab
        print("\n📋 Cloning lab...")
        cloned_lab_1 = api.clone_lab(executor, original_lab.lab_id, f"Clone_1_{lab_name}")
        print(f"✅ Cloned: {cloned_lab_1.name} (ID: {cloned_lab_1.lab_id})")
        
        # 7. Clone again
        print("\n📋 Cloning again...")
        cloned_lab_2 = api.clone_lab(executor, original_lab.lab_id, f"Clone_2_{lab_name}")
        print(f"✅ Cloned: {cloned_lab_2.name} (ID: {cloned_lab_2.lab_id})")
        
        # 8. Apply parameter ranges to the second clone
        print("\n🔧 Applying parameter ranges...")
        lab_details = api.get_lab_details(executor, cloned_lab_2.lab_id)
        
        # Generate range values (1 to 10, step 0.5)
        range_values = []
        current = 1.0
        while current <= 10.0:
            range_values.append(str(current))
            current += 0.5
        
        print(f"📊 Generated {len(range_values)} values: {range_values[:5]}...{range_values[-5:]}")
        
        # Find parameters to update (look for common scalper parameters)
        updated_parameters = []
        param_count = 0
        
        for param in lab_details.parameters:
            key = param.get('K', '')
            name = key.split('.')[-1].lower() if '.' in key else key.lower()
            
            # Apply range to parameters that might be suitable
            if any(keyword in name for keyword in ['stop', 'profit', 'target', 'threshold', 'delay']):
                param['O'] = range_values
                param_count += 1
                print(f"  ✅ Applied range to: {key}")
            
            updated_parameters.append(param)
        
        if param_count == 0:
            print("⚠️ No suitable parameters found, applying to first few parameters")
            # Apply to first few parameters as fallback
            for i, param in enumerate(updated_parameters[:3]):
                param['O'] = range_values
                print(f"  ✅ Applied range to parameter {i+1}: {param.get('K', '')}")
        
        # Update lab
        lab_details.parameters = updated_parameters
        updated_lab = api.update_lab_details(executor, lab_details)
        print(f"✅ Lab updated successfully")
        
        # 9. Clone the lab with ranges (third clone)
        print("\n📋 Cloning lab with ranges...")
        cloned_lab_3 = api.clone_lab(executor, updated_lab.lab_id, f"Clone_3_With_Ranges_{lab_name}")
        print(f"✅ Cloned: {cloned_lab_3.name} (ID: {cloned_lab_3.lab_id})")
        
        # 10. Save configuration
        print("\n💾 Saving configuration...")
        import json
        from datetime import datetime
        
        config = {
            "lab_id": cloned_lab_3.lab_id,
            "name": cloned_lab_3.name,
            "script_id": cloned_lab_3.script_id,
            "created_at": datetime.now().isoformat(),
            "parameter_range": {
                "start": 1.0,
                "end": 10.0,
                "step": 0.5,
                "values_count": len(range_values)
            },
            "parameters_updated": param_count,
            "all_labs": {
                "original": original_lab.lab_id,
                "clone_1": cloned_lab_1.lab_id,
                "clone_2_with_ranges": updated_lab.lab_id,
                "clone_3_of_ranged": cloned_lab_3.lab_id
            }
        }
        
        filename = f"lab_config_{cloned_lab_3.lab_id}.json"
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration saved to {filename}")
        
        # Summary
        print("\n📋 SUMMARY")
        print("=" * 20)
        print(f"Original lab: {original_lab.lab_id}")
        print(f"Clone 1: {cloned_lab_1.lab_id}")
        print(f"Clone 2 (with ranges): {updated_lab.lab_id}")
        print(f"Clone 3 (of ranged lab): {cloned_lab_3.lab_id}")
        print(f"Parameters updated: {param_count}")
        print(f"Range values: {len(range_values)}")
        print("\n🎉 Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 