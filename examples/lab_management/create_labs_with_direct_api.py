#!/usr/bin/env python3
"""
Create labs with direct API calls using the format from the curl examples
This bypasses the MCP server and calls the HaasOnline API directly
"""

import requests
import json
import time
import urllib.parse
from typing import List, Dict, Optional

# Trading pairs from task_at_hand.md
TRADING_PAIRS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "APT",
    "LTC", "BCH", "ADA", "UNI", "GALA", "TRX"
]

BASE_LAB_ID = "edd56c9f-97d9-4417-984b-06f3a6411763"
MCP_SERVER_URL = "http://127.0.0.1:8000"
HAAS_API_URL = "http://127.0.0.1:8090"
TEST_ACCOUNT_ID = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe"

# These would need to be extracted from your session
INTERFACE_KEY = "340fb628-ce29-5cac-9335-04b0da28fdc4"
USER_ID = "84e214be09e1916190df8216190df82c"

class DirectAPILabCreator:
    def __init__(self, mcp_url: str, haas_url: str):
        self.mcp_url = mcp_url
        self.haas_url = haas_url
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
    
    def get_all_labs_via_mcp(self) -> List[Dict]:
        """Get all existing labs via MCP server"""
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
        """Delete all existing ADX BB STOCH Scalper labs via MCP"""
        print("🗑️  Deleting existing ADX BB STOCH Scalper labs...")
        
        labs = self.get_all_labs_via_mcp()
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
    
    def clone_lab_via_mcp(self, base_lab_id: str, new_name: str) -> Optional[Dict]:
        """Clone a lab via MCP server"""
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
    
    def update_lab_via_direct_api(self, lab_id: str, coin: str, account_id: str) -> bool:
        """Update lab configuration using direct HaasOnline API call"""
        try:
            market_tag = f"BINANCEFUTURES_{coin}_USDT_PERPETUAL"
            lab_name = f"0 - ADX BB STOCH Scalper - 2 years {coin} - alpha test"
            
            # Configuration based on your curl example
            config = {
                "MP": 50,  # Max Population
                "MG": 50,  # Max Generations
                "ME": 3,   # Max Elites
                "MR": 40.0, # Mix Rate
                "AR": 25.0  # Adjust Rate
            }
            
            settings = {
                "botId": "",
                "botName": "",
                "accountId": account_id,
                "marketTag": market_tag,
                "leverage": 20,
                "positionMode": 1,  # HEDGE mode
                "marginMode": 0,
                "interval": 1,
                "chartStyle": 300,
                "tradeAmount": 100,
                "orderTemplate": 500,
                "scriptParameters": {}
            }
            
            # Parameters array (empty for now, can be populated later)
            parameters = []
            
            # Prepare form data as in your curl example
            form_data = {
                'labid': lab_id,
                'name': lab_name,
                'type': '1',  # Lab type
                'config': json.dumps(config),
                'settings': json.dumps(settings),
                'parameters': json.dumps(parameters),
                'interfacekey': INTERFACE_KEY,
                'userid': USER_ID
            }
            
            # Make the direct API call
            url = f"{self.haas_url}/LabsAPI.php?channel=UPDATE_LAB_DETAILS"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/plain, */*'
            }
            
            response = self.session.post(url, data=form_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    print(f"    ✅ Configuration updated via direct API")
                    print(f"      Market: {market_tag}")
                    print(f"      Account: {account_id}")
                    print(f"      Population: {config['MP']}, Generations: {config['MG']}")
                    return True
                else:
                    print(f"    ❌ Direct API update failed: {data.get('Error', 'Unknown error')}")
            else:
                print(f"    ❌ HTTP error in direct API call: {response.status_code}")
                print(f"    Response: {response.text[:200]}...")
            return False
            
        except Exception as e:
            print(f"    ❌ Error in direct API call: {e}")
            return False
    
    def create_fully_automated_lab_direct(self, coin: str, strategy: str, account_id: str) -> Optional[Dict]:
        """Create a fully configured lab using direct API calls"""
        print(f"\n🔧 Creating fully automated lab for {coin} (Direct API)...")
        
        # Generate lab name following the documented format
        lab_name = f"0 - {strategy} - 2 years {coin} - alpha test"
        print(f"  📝 Lab name: {lab_name}")
        
        # Step 1: Clone the lab via MCP
        cloned_lab = self.clone_lab_via_mcp(BASE_LAB_ID, lab_name)
        if not cloned_lab:
            return None
        
        lab_id = cloned_lab.get("LID") or cloned_lab.get("lab_id")
        print(f"  ✅ Cloned successfully")
        print(f"  📋 Lab ID: {lab_id}")
        
        # Step 2: Update configuration via direct API
        if not self.update_lab_via_direct_api(lab_id, coin, account_id):
            print(f"  ❌ Failed to update configuration via direct API")
            return None
        
        return {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "coin": coin,
            "strategy": strategy,
            "account_id": account_id,
            "market_tag": f"BINANCEFUTURES_{coin}_USDT_PERPETUAL",
            "status": "fully_configured_direct_api"
        }
    
    def create_all_labs_with_direct_api(self) -> Dict[str, Dict]:
        """Create all labs using direct API calls"""
        print(f"🚀 Creating fully automated labs with Direct API")
        print(f"Base lab ID: {BASE_LAB_ID}")
        print(f"Test account ID: {TEST_ACCOUNT_ID}")
        print(f"🔗 Using Direct HaasOnline API calls for configuration")
        
        # Check MCP server status (still needed for cloning)
        if not self.check_mcp_server_status():
            print("❌ MCP server is not running or not authenticated")
            return {}
        
        print("✅ MCP server is running and authenticated")
        
        # Check if base lab exists
        existing_labs = self.get_all_labs_via_mcp()
        base_lab_exists = any(lab.get("LID") == BASE_LAB_ID for lab in existing_labs)
        
        if not base_lab_exists:
            print(f"❌ Base lab {BASE_LAB_ID} not found")
            return {}
        
        print(f"✅ Base lab {BASE_LAB_ID} found")
        
        # Delete existing labs first
        self.delete_existing_adx_labs()
        
        print(f"\n🎯 Creating new labs with Direct API configuration...")
        strategy = "ADX BB STOCH Scalper"
        
        created_labs = {}
        
        for i, coin in enumerate(TRADING_PAIRS, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(TRADING_PAIRS)}] Processing {coin}")
            print(f"{'='*60}")
            
            lab_data = self.create_fully_automated_lab_direct(coin, strategy, TEST_ACCOUNT_ID)
            
            if lab_data:
                lab_key = f"{strategy}_{coin}"
                created_labs[lab_key] = lab_data
                print(f"  ✅ {coin} lab fully configured via Direct API")
            else:
                print(f"  ❌ Failed to create lab for {coin}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(1)
        
        return created_labs
    
    def save_results(self, created_labs: Dict[str, Dict]):
        """Save results to file"""
        try:
            with open("direct_api_labs.json", "w") as f:
                json.dump(created_labs, f, indent=2)
            print(f"💾 Results saved to direct_api_labs.json")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def print_summary(self, created_labs: Dict[str, Dict]):
        """Print summary"""
        print(f"\n{'='*80}")
        print("DIRECT API LABS CREATION SUMMARY")
        print(f"{'='*80}")
        print(f"Successfully created {len(created_labs)} fully configured labs:")
        
        for lab_key, lab_data in created_labs.items():
            print(f"\n📊 {lab_data['coin']}:")
            print(f"  Lab ID: {lab_data['lab_id']}")
            print(f"  Name: {lab_data['lab_name']}")
            print(f"  Market: {lab_data['market_tag']}")
            print(f"  Account: {lab_data['account_id']}")
            print(f"  Status: {lab_data['status']}")
        
        print(f"\n🔗 DIRECT API CONFIGURATION COMPLETE:")
        print(f"✅ Labs created via MCP server")
        print(f"✅ Configuration updated via Direct HaasOnline API")
        print(f"✅ Correct naming scheme applied")
        print(f"✅ Market tags configured automatically")
        print(f"✅ Account assignment completed")
        print(f"✅ Lab parameters set (Population: 50, Generations: 50, Elites: 3)")
        
        print(f"\n📋 Ready for 2-year backtesting!")

def main():
    print("🎯 DIRECT API LAB CREATION")
    print("Creating labs with MCP + Direct HaasOnline API calls")
    print("🔗 Bypassing MCP server limitations for configuration")
    
    creator = DirectAPILabCreator(MCP_SERVER_URL, HAAS_API_URL)
    created_labs = creator.create_all_labs_with_direct_api()
    
    if created_labs:
        creator.save_results(created_labs)
        creator.print_summary(created_labs)
        print(f"\n✨ SUCCESS! Created {len(created_labs)} fully configured labs.")
        print(f"🚀 All labs are ready for backtesting!")
    else:
        print("❌ No labs were created successfully")
        print("💡 You may need to update INTERFACE_KEY and USER_ID from your browser session")

if __name__ == "__main__":
    main()