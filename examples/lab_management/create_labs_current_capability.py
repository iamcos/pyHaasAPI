#!/usr/bin/env python3
"""
Create labs with current MCP server capabilities
Creates labs with correct naming scheme and documents required configuration
"""

import requests
import json
import time
from typing import List, Dict, Optional

# Trading pairs from task_at_hand.md
TRADING_PAIRS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "APT",
    "LTC", "BCH", "ADA", "UNI", "GALA", "TRX"
]

BASE_LAB_ID = "edd56c9f-97d9-4417-984b-06f3a6411763"
MCP_SERVER_URL = "http://127.0.0.1:8000"
TEST_ACCOUNT_ID = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe"

class CurrentCapabilityLabCreator:
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.session = requests.Session()
        
    def check_mcp_server_status(self) -> bool:
        """Check if MCP server is running and authenticated"""
        try:
            response = self.session.get(f"{self.mcp_url}/status")
            if response.status_code == 200:
                data = response.json()
                return data.get("haas_api_connected", False)
            return False
        except Exception as e:
            print(f"Error checking MCP server status: {e}")
            return False
    
    def get_all_labs(self) -> List[Dict]:
        """Get all existing labs"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_all_labs")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data", [])
            return []
        except Exception as e:
            print(f"Error getting labs: {e}")
            return []
    
    def delete_existing_adx_labs(self):
        """Delete all existing ADX BB STOCH Scalper labs"""
        print("🗑️  Deleting existing ADX BB STOCH Scalper labs...")
        
        labs = self.get_all_labs()
        adx_labs = [lab for lab in labs if "ADX BB STOCH Scalper" in lab.get("N", "")]
        
        if not adx_labs:
            print("✅ No existing ADX BB STOCH Scalper labs found")
            return
        
        print(f"Found {len(adx_labs)} ADX BB STOCH Scalper labs to delete")
        
        for lab in adx_labs:
            lab_id = lab.get("LID")
            lab_name = lab.get("N")
            print(f"  Deleting: {lab_name}")
            
            try:
                response = self.session.delete(f"{self.mcp_url}/delete_lab/{lab_id}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("Success"):
                        print(f"    ✅ Deleted")
                    else:
                        print(f"    ❌ Delete failed: {data.get('Error')}")
                else:
                    print(f"    ❌ HTTP error: {response.status_code}")
            except Exception as e:
                print(f"    ❌ Error: {e}")
            
            time.sleep(0.2)
    
    def clone_lab(self, base_lab_id: str, new_name: str) -> Optional[Dict]:
        """Clone a lab with a new name"""
        try:
            payload = {
                "lab_id": base_lab_id,
                "new_name": new_name
            }
            response = self.session.post(f"{self.mcp_url}/clone_lab", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data")
                else:
                    print(f"    ❌ Clone failed: {data.get('Error', 'Unknown error')}")
            else:
                print(f"    ❌ HTTP error cloning lab: {response.status_code}")
            return None
        except Exception as e:
            print(f"    ❌ Error cloning lab: {e}")
            return None
    
    def create_lab_with_correct_naming(self, coin: str, strategy: str) -> Optional[Dict]:
        """Create a lab with correct naming scheme"""
        print(f"\n🔧 Creating lab for {coin}...")
        
        # Generate lab name following the documented format
        lab_name = f"0 - {strategy} - 2 years {coin} - alpha test"
        print(f"  📝 Lab name: {lab_name}")
        
        # Clone the lab
        cloned_lab = self.clone_lab(BASE_LAB_ID, lab_name)
        if not cloned_lab:
            return None
        
        lab_id = cloned_lab.get("LID") or cloned_lab.get("lab_id")
        print(f"  ✅ Cloned successfully")
        print(f"  📋 Lab ID: {lab_id}")
        
        return {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "coin": coin,
            "strategy": strategy,
            "expected_market_tag": f"BINANCEFUTURES_{coin}_USDT_PERPETUAL",
            "expected_account_id": TEST_ACCOUNT_ID,
            "status": "created_needs_configuration"
        }
    
    def create_all_labs_current_capability(self) -> Dict[str, Dict]:
        """Create all labs with current MCP server capabilities"""
        print(f"🚀 Creating labs with current MCP server capabilities")
        print(f"Base lab ID: {BASE_LAB_ID}")
        print(f"⚠️  Configuration will need to be completed via MCP server enhancement")
        
        # Check MCP server status
        if not self.check_mcp_server_status():
            print("❌ MCP server is not running or not authenticated")
            return {}
        
        print("✅ MCP server is running and authenticated")
        
        # Check if base lab exists
        existing_labs = self.get_all_labs()
        base_lab_exists = any(lab.get("LID") == BASE_LAB_ID for lab in existing_labs)
        
        if not base_lab_exists:
            print(f"❌ Base lab {BASE_LAB_ID} not found")
            return {}
        
        print(f"✅ Base lab {BASE_LAB_ID} found")
        
        # Delete existing labs first
        self.delete_existing_adx_labs()
        
        print(f"\n🎯 Creating new labs with correct naming...")
        strategy = "ADX BB STOCH Scalper"
        
        created_labs = {}
        
        for i, coin in enumerate(TRADING_PAIRS, 1):
            print(f"\n[{i}/{len(TRADING_PAIRS)}] Processing {coin}...")
            
            lab_data = self.create_lab_with_correct_naming(coin, strategy)
            
            if lab_data:
                lab_key = f"{strategy}_{coin}"
                created_labs[lab_key] = lab_data
                print(f"  ✅ {coin} lab created with correct naming")
            else:
                print(f"  ❌ Failed to create lab for {coin}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        return created_labs
    
    def generate_configuration_script(self, created_labs: Dict[str, Dict]):
        """Generate a script for completing the configuration"""
        script_content = f"""#!/usr/bin/env python3
# Auto-generated configuration script for labs
# This script would complete the lab configuration once MCP server is enhanced

import requests

MCP_SERVER_URL = "{MCP_SERVER_URL}"
TEST_ACCOUNT_ID = "{TEST_ACCOUNT_ID}"

def configure_lab(lab_id: str, coin: str):
    market_tag = f"BINANCEFUTURES_{{coin}}_USDT_PERPETUAL"
    
    config = {{
        "MP": 50,  # Max Population
        "MG": 50,  # Max Generations
        "ME": 3,   # Max Elites
        "MR": 40.0, # Mix Rate
        "AR": 25.0  # Adjust Rate
    }}
    
    settings = {{
        "accountId": TEST_ACCOUNT_ID,
        "marketTag": market_tag,
        "leverage": 20,
        "positionMode": 1,  # HEDGE mode
        "marginMode": 0,
        "interval": 1,
        "chartStyle": 300,
        "tradeAmount": 100,
        "orderTemplate": 500,
        "scriptParameters": {{}}
    }}
    
    # This would call the UPDATE_LAB_DETAILS endpoint once implemented
    # payload = {{"lab_id": lab_id, "config": config, "settings": settings}}
    # response = requests.post(f"{{MCP_SERVER_URL}}/update_lab_details", json=payload)
    
    print(f"Would configure {{coin}} lab {{lab_id}} with market {{market_tag}}")

def main():
    print("🔧 Lab Configuration Script")
    print("⚠️  Requires UPDATE_LAB_DETAILS endpoint in MCP server")
    
"""
        
        for lab_key, lab_data in created_labs.items():
            coin = lab_data['coin']
            lab_id = lab_data['lab_id']
            script_content += f'    configure_lab("{lab_id}", "{coin}")\n'
        
        script_content += """
if __name__ == "__main__":
    main()
"""
        
        with open("configure_labs.py", "w") as f:
            f.write(script_content)
        
        print("📝 Generated configure_labs.py script")
    
    def save_results(self, created_labs: Dict[str, Dict]):
        """Save results to file"""
        try:
            with open("current_capability_labs.json", "w") as f:
                json.dump(created_labs, f, indent=2)
            print(f"💾 Results saved to current_capability_labs.json")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def print_summary(self, created_labs: Dict[str, Dict]):
        """Print summary and next steps"""
        print(f"\n{'='*80}")
        print("CURRENT CAPABILITY LABS CREATION SUMMARY")
        print(f"{'='*80}")
        print(f"Successfully created {len(created_labs)} labs with correct naming:")
        
        for lab_key, lab_data in created_labs.items():
            print(f"\n📊 {lab_data['coin']}:")
            print(f"  Lab ID: {lab_data['lab_id']}")
            print(f"  Name: {lab_data['lab_name']}")
            print(f"  Expected Market: {lab_data['expected_market_tag']}")
            print(f"  Expected Account: {lab_data['expected_account_id']}")
        
        print(f"\n✅ COMPLETED:")
        print(f"✅ Correct naming scheme applied")
        print(f"✅ Labs created and ready for configuration")
        
        print(f"\n⚠️  NEXT STEPS REQUIRED:")
        print(f"1. Implement UPDATE_LAB_DETAILS endpoint in MCP server")
        print(f"2. Or manually configure each lab in HaasOnline interface:")
        
        print(f"\n🔧 Manual Configuration Required for each lab:")
        for lab_key, lab_data in created_labs.items():
            coin = lab_data['coin']
            lab_id = lab_data['lab_id']
            market_tag = lab_data['expected_market_tag']
            print(f"\n{coin} Lab ({lab_id}):")
            print(f"  - Market: {market_tag}")
            print(f"  - Account: {TEST_ACCOUNT_ID}")
            print(f"  - Population: 50, Generations: 50, Elites: 3")
            print(f"  - Mix Rate: 40.0, Adjust Rate: 25.0")
        
        print(f"\n📋 For full automation, the MCP server needs enhancement.")

def main():
    print("🎯 CURRENT CAPABILITY LAB CREATION")
    print("Creating labs with correct naming scheme")
    print("⚠️  Full automation requires MCP server enhancement")
    
    creator = CurrentCapabilityLabCreator(MCP_SERVER_URL)
    created_labs = creator.create_all_labs_current_capability()
    
    if created_labs:
        creator.save_results(created_labs)
        creator.generate_configuration_script(created_labs)
        creator.print_summary(created_labs)
        print(f"\n✨ Created {len(created_labs)} labs with correct naming.")
        print(f"🔧 Configuration step requires MCP server enhancement or manual setup.")
    else:
        print("❌ No labs were created successfully")

if __name__ == "__main__":
    main()