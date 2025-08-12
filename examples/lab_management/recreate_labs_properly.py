#!/usr/bin/env python3
"""
Recreate labs with proper market tags and account assignment
Using the existing account ID: 6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe
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
TEST_ACCOUNT_ID = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe"  # From previous lab configurations

class ProperLabRecreator:
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
    
    def delete_existing_labs(self):
        """Delete existing incorrectly configured labs"""
        print("🗑️  Deleting existing labs...")
        
        labs = self.get_all_labs()
        adx_labs = [lab for lab in labs if "ADX BB STOCH Scalper" in lab.get("N", "")]
        
        if not adx_labs:
            print("✅ No existing ADX BB STOCH Scalper labs found")
            return
        
        print(f"Found {len(adx_labs)} ADX BB STOCH Scalper labs to delete:")
        
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
            
            time.sleep(0.2)  # Small delay
    
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
    
    def update_lab_details(self, lab_id: str, coin: str, account_id: str) -> bool:
        """Update lab with proper market tag and account - this needs MCP server implementation"""
        # For now, we'll document what needs to be done
        # This would require implementing the UPDATE_LAB_DETAILS endpoint in MCP server
        expected_market = f"BINANCEFUTURES_{coin}_USDT_PERPETUAL"
        print(f"    📊 Market should be: {expected_market}")
        print(f"    👤 Account should be: {account_id}")
        print(f"    ⚠️  Manual configuration needed in HaasOnline interface")
        return True
    
    def create_single_lab_properly(self, coin: str, strategy: str, account_id: str) -> Optional[Dict]:
        """Create a single lab with proper configuration"""
        print(f"\n🔧 Creating lab for {coin} with {strategy}...")
        
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
        
        # Update lab configuration
        self.update_lab_details(lab_id, coin, account_id)
        
        return {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "coin": coin,
            "strategy": strategy,
            "account_id": account_id,
            "expected_market_tag": f"BINANCEFUTURES_{coin}_USDT_PERPETUAL",
            "status": "created_needs_manual_config"
        }
    
    def recreate_all_labs(self) -> Dict[str, Dict]:
        """Recreate all labs with proper configuration"""
        print(f"🚀 Recreating labs with proper configuration")
        print(f"Base lab ID: {BASE_LAB_ID}")
        print(f"Test account ID: {TEST_ACCOUNT_ID}")
        
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
        self.delete_existing_labs()
        
        print(f"\n🎯 Creating new labs with proper configuration...")
        strategy = "ADX BB STOCH Scalper"
        
        created_labs = {}
        
        for i, coin in enumerate(TRADING_PAIRS, 1):
            print(f"\n[{i}/{len(TRADING_PAIRS)}] Processing {coin}...")
            
            lab_data = self.create_single_lab_properly(coin, strategy, TEST_ACCOUNT_ID)
            
            if lab_data:
                lab_key = f"{strategy}_{coin}"
                created_labs[lab_key] = lab_data
                print(f"  ✅ {coin} lab created successfully")
            else:
                print(f"  ❌ Failed to create lab for {coin}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        return created_labs
    
    def save_results(self, created_labs: Dict[str, Dict]):
        """Save results to file"""
        try:
            with open("properly_recreated_labs.json", "w") as f:
                json.dump(created_labs, f, indent=2)
            print(f"💾 Results saved to properly_recreated_labs.json")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def print_summary(self, created_labs: Dict[str, Dict]):
        """Print summary with manual configuration instructions"""
        print(f"\n{'='*80}")
        print("PROPERLY RECREATED LABS SUMMARY")
        print(f"{'='*80}")
        print(f"Successfully created {len(created_labs)} labs:")
        
        for lab_key, lab_data in created_labs.items():
            print(f"\n📊 {lab_data['coin']}:")
            print(f"  Lab ID: {lab_data['lab_id']}")
            print(f"  Name: {lab_data['lab_name']}")
            print(f"  Expected market: {lab_data['expected_market_tag']}")
            print(f"  Account ID: {lab_data['account_id']}")
        
        print(f"\n🔧 MANUAL CONFIGURATION REQUIRED:")
        print(f"For each lab, you need to:")
        print(f"1. Open HaasOnline interface")
        print(f"2. Navigate to Labs section")
        print(f"3. For each lab, update:")
        print(f"   - Market tag to: BINANCEFUTURES_{{COIN}}_USDT_PERPETUAL")
        print(f"   - Account to: {TEST_ACCOUNT_ID}")
        print(f"   - Lab parameters: Population=50, Generations=50, Elites=3")
        print(f"4. Save configuration")
        print(f"5. Start 2-year backtest")
        
        print(f"\n📋 Market tags needed:")
        for lab_key, lab_data in created_labs.items():
            coin = lab_data['coin']
            print(f"  {coin}: BINANCEFUTURES_{coin}_USDT_PERPETUAL")

def main():
    print("🎯 Recreating labs with proper market tags and account assignment")
    print("This will delete existing ADX BB STOCH Scalper labs and recreate them properly")
    
    recreator = ProperLabRecreator(MCP_SERVER_URL)
    created_labs = recreator.recreate_all_labs()
    
    if created_labs:
        recreator.save_results(created_labs)
        recreator.print_summary(created_labs)
        print(f"\n✨ Success! Recreated {len(created_labs)} labs.")
        print(f"⚠️  Manual configuration required in HaasOnline interface.")
    else:
        print("❌ No labs were recreated successfully")

if __name__ == "__main__":
    main()