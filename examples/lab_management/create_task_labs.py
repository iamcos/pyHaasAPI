#!/usr/bin/env python3
"""
Create labs for the 12 trading pairs specified in task_at_hand.md
Base lab: 7e39fd98-ad7c-4753-8802-c19b2ab11c31
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

class TaskLabCreator:
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
                    print(f"Failed to clone lab: {data.get('Error', 'Unknown error')}")
            else:
                print(f"HTTP error cloning lab: {response.status_code}")
            return None
        except Exception as e:
            print(f"Error cloning lab: {e}")
            return None
    
    def get_accounts(self) -> List[Dict]:
        """Get all accounts to find test account"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_all_accounts")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data", [])
            return []
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []
    
    def find_test_account(self) -> Optional[str]:
        """Find the test account 'для тестов 10к'"""
        accounts = self.get_accounts()
        for account in accounts:
            if "для тестов 10к" in account.get("name", ""):
                return account.get("account_id")
        print("Warning: Test account 'для тестов 10к' not found")
        return None
    
    def create_labs_for_task_pairs(self) -> Dict[str, str]:
        """Create labs for the 12 trading pairs from task_at_hand.md"""
        print(f"🚀 Creating labs for {len(TRADING_PAIRS)} trading pairs from task_at_hand.md")
        print(f"Base lab ID: {BASE_LAB_ID}")
        print(f"Trading pairs: {', '.join(TRADING_PAIRS)}")
        
        # Check MCP server status
        if not self.check_mcp_server_status():
            print("❌ MCP server is not running or not authenticated")
            return {}
        
        print("✅ MCP server is running and authenticated")
        
        # Get existing labs to check if base lab exists
        existing_labs = self.get_all_labs()
        base_lab_exists = any(lab.get("LID") == BASE_LAB_ID for lab in existing_labs)
        
        if not base_lab_exists:
            print(f"❌ Base lab {BASE_LAB_ID} not found")
            return {}
        
        print(f"✅ Base lab {BASE_LAB_ID} found")
        
        # Find test account
        test_account_id = self.find_test_account()
        if test_account_id:
            print(f"✅ Found test account: {test_account_id}")
        else:
            print("⚠️  Test account not found, will need manual assignment")
        
        created_labs = {}
        
        for i, coin in enumerate(TRADING_PAIRS, 1):
            print(f"\n[{i}/{len(TRADING_PAIRS)}] Creating lab for {coin}...")
            
            # Generate lab name following the task naming convention
            lab_name = f"Task_{coin}_USDT_Backtest"
            
            # Clone the lab
            cloned_lab = self.clone_lab(BASE_LAB_ID, lab_name)
            
            if cloned_lab:
                lab_id = cloned_lab.get("LID") or cloned_lab.get("lab_id")  # Handle both formats
                print(f"  ✅ Cloned lab: {lab_name}")
                print(f"  📋 Lab ID: {lab_id}")
                
                created_labs[coin] = {
                    "lab_id": lab_id,
                    "lab_name": lab_name,
                    "market_tag": f"BINANCE_{coin}_USDT_",
                    "coin": coin
                }
                
                print(f"  📊 Market tag: BINANCE_{coin}_USDT_")
            else:
                print(f"  ❌ Failed to clone lab for {coin}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        return created_labs
    
    def save_results_to_file(self, created_labs: Dict[str, Dict], filename: str = "task_labs.json"):
        """Save created labs to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(created_labs, f, indent=2)
            print(f"💾 Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def print_summary(self, created_labs: Dict[str, Dict]):
        """Print summary of created labs"""
        print(f"\n{'='*80}")
        print("TASK LABS CREATION SUMMARY")
        print(f"{'='*80}")
        print(f"Successfully created {len(created_labs)} out of {len(TRADING_PAIRS)} labs:")
        
        for coin, lab_data in created_labs.items():
            print(f"  {coin}: {lab_data['lab_id']} ({lab_data['lab_name']})")
        
        if len(created_labs) < len(TRADING_PAIRS):
            failed_coins = set(TRADING_PAIRS) - set(created_labs.keys())
            print(f"\n❌ Failed to create labs for: {', '.join(failed_coins)}")
        
        print(f"\n📋 Next steps:")
        print(f"1. Configure each lab with correct market (BINANCE_{coin}_USDT_)")
        print(f"2. Assign test account 'для тестов 10к' to all labs")
        print(f"3. Set lab parameters (population: 50 for srv01)")
        print(f"4. Configure algorithm (Intelligent recommended)")
        print(f"5. Start backtesting")
        
        print(f"\n🔧 Manual configuration needed:")
        print(f"- Market assignment in HaasOnline interface")
        print(f"- Account assignment")
        print(f"- Lab parameter configuration")

def main():
    print("🎯 Creating labs for task_at_hand.md trading pairs")
    print(f"Base lab ID: {BASE_LAB_ID}")
    print(f"Target pairs: {', '.join(TRADING_PAIRS)}")
    
    creator = TaskLabCreator(MCP_SERVER_URL)
    created_labs = creator.create_labs_for_task_pairs()
    
    if created_labs:
        creator.save_results_to_file(created_labs)
        creator.print_summary(created_labs)
        
        print(f"\n✨ Success! Created {len(created_labs)} labs ready for backtesting.")
    else:
        print("❌ No labs were created. Check MCP server connection and base lab availability.")

if __name__ == "__main__":
    main()