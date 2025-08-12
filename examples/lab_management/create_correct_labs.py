#!/usr/bin/env python3
"""
Create labs with correct naming scheme according to task documentation:
Format: {version} - {script_name} - {period} {coin} ({timeframe_details}) - {additional_info}
Example: "0 - ADX BB STOCH Scalper - 2 years BTC - alpha test"
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

# Strategies from task_at_hand.md
STRATEGIES = [
    "Simple RSING VWAP Strategy",
    "RSI-VWAP Trading Bot for Deribit (port)", 
    "ADX BB STOCH Scalper",
    "[pshaiBot] YATS Bot"
    # MadHatter Bot + mods - to be done later
]

BASE_LAB_ID = "edd56c9f-97d9-4417-984b-06f3a6411763"
MCP_SERVER_URL = "http://127.0.0.1:8000"

class CorrectLabCreator:
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
                    print(f"    ❌ Clone failed: {data.get('Error', 'Unknown error')}")
            else:
                print(f"    ❌ HTTP error cloning lab: {response.status_code}")
            return None
        except Exception as e:
            print(f"    ❌ Error cloning lab: {e}")
            return None
    
    def get_lab_details(self, lab_id: str) -> Optional[Dict]:
        """Get detailed lab configuration"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_lab_config/{lab_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data")
            return None
        except Exception as e:
            print(f"    ⚠️  Error getting lab details: {e}")
            return None
    
    def find_test_account(self) -> Optional[str]:
        """Find the test account"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_all_accounts")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    accounts = data.get("Data", [])
                    for account in accounts:
                        account_name = account.get("name", "")
                        if "для тестов 10к" in account_name or "test" in account_name.lower():
                            return account.get("account_id")
        except Exception as e:
            print(f"Error finding test account: {e}")
        return None
    
    def create_single_lab(self, coin: str, strategy: str) -> Optional[Dict]:
        """Create a single lab with proper naming scheme"""
        print(f"\n🔧 Creating lab for {coin} with {strategy}...")
        
        # Generate lab name following the documented format:
        # {version} - {script_name} - {period} {coin} ({timeframe_details}) - {additional_info}
        lab_name = f"0 - {strategy} - 2 years {coin} - alpha test"
        
        print(f"  📝 Lab name: {lab_name}")
        
        # Clone the lab
        cloned_lab = self.clone_lab(BASE_LAB_ID, lab_name)
        
        if not cloned_lab:
            return None
        
        lab_id = cloned_lab.get("LID") or cloned_lab.get("lab_id")
        print(f"  ✅ Cloned successfully")
        print(f"  📋 Lab ID: {lab_id}")
        
        # Get lab details to verify current configuration
        details = self.get_lab_details(lab_id)
        if details:
            settings = details.get("ST", {})
            current_market = settings.get("marketTag", "N/A")
            current_account = settings.get("accountId", "N/A")
            
            print(f"  📊 Current market: {current_market}")
            print(f"  👤 Current account: {current_account}")
            
            # Check if market tag is correct
            expected_market = f"BINANCEFUTURES_{coin}_USDT_PERPETUAL"
            if current_market == expected_market:
                print(f"  ✅ Market tag is correct!")
            else:
                print(f"  ⚠️  Market tag should be: {expected_market}")
                print(f"      (Manual configuration needed in HaasOnline interface)")
        
        return {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "coin": coin,
            "strategy": strategy,
            "expected_market_tag": f"BINANCEFUTURES_{coin}_USDT_PERPETUAL",
            "status": "created"
        }
    
    def create_labs_for_strategy(self, strategy: str, coins: List[str] = None) -> Dict[str, Dict]:
        """Create labs for a specific strategy"""
        if coins is None:
            coins = TRADING_PAIRS
            
        print(f"\n{'='*80}")
        print(f"CREATING LABS FOR STRATEGY: {strategy}")
        print(f"{'='*80}")
        print(f"Coins: {', '.join(coins)}")
        
        created_labs = {}
        
        for i, coin in enumerate(coins, 1):
            print(f"\n[{i}/{len(coins)}] Processing {coin}...")
            
            lab_data = self.create_single_lab(coin, strategy)
            
            if lab_data:
                lab_key = f"{strategy}_{coin}"
                created_labs[lab_key] = lab_data
                print(f"  ✅ {coin} lab created successfully")
            else:
                print(f"  ❌ Failed to create lab for {coin}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        return created_labs
    
    def create_all_labs(self) -> Dict[str, Dict]:
        """Create labs for all strategies and coins"""
        print(f"🚀 Creating labs with correct naming scheme")
        print(f"Base lab ID: {BASE_LAB_ID}")
        
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
        
        # Find test account
        test_account_id = self.find_test_account()
        if test_account_id:
            print(f"✅ Found test account: {test_account_id}")
        else:
            print("⚠️  Test account not found, will need manual assignment")
        
        all_created_labs = {}
        
        # For now, let's start with ADX BB STOCH Scalper as mentioned in the task
        strategy = "ADX BB STOCH Scalper"
        print(f"\n🎯 Starting with strategy: {strategy}")
        
        created_labs = self.create_labs_for_strategy(strategy)
        all_created_labs.update(created_labs)
        
        return all_created_labs
    
    def save_results(self, created_labs: Dict[str, Dict]):
        """Save results to file"""
        try:
            with open("correct_labs.json", "w") as f:
                json.dump(created_labs, f, indent=2)
            print(f"💾 Results saved to correct_labs.json")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def print_summary(self, created_labs: Dict[str, Dict]):
        """Print summary"""
        print(f"\n{'='*80}")
        print("CORRECT LABS CREATION SUMMARY")
        print(f"{'='*80}")
        print(f"Successfully created {len(created_labs)} labs:")
        
        # Group by strategy
        strategies = {}
        for lab_key, lab_data in created_labs.items():
            strategy = lab_data["strategy"]
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(lab_data)
        
        for strategy, labs in strategies.items():
            print(f"\n📊 {strategy} ({len(labs)} labs):")
            for lab in labs:
                print(f"  {lab['coin']}: {lab['lab_id']}")
                print(f"    Name: {lab['lab_name']}")
                print(f"    Expected market: {lab['expected_market_tag']}")
        
        print(f"\n📋 Next steps:")
        print(f"1. Verify each lab has correct market configuration in HaasOnline interface")
        print(f"2. Ensure proper account assignment ('для тестов 10к')")
        print(f"3. Configure lab parameters (population: 50, generations: 50, etc.)")
        print(f"4. Start 2-year backtesting")
        print(f"5. Monitor results and analyze performance")

def main():
    print("🎯 Creating labs with correct naming scheme")
    print("Format: {version} - {script_name} - {period} {coin} - {additional_info}")
    print("Example: '0 - ADX BB STOCH Scalper - 2 years BTC - alpha test'")
    
    creator = CorrectLabCreator(MCP_SERVER_URL)
    created_labs = creator.create_all_labs()
    
    if created_labs:
        creator.save_results(created_labs)
        creator.print_summary(created_labs)
        print(f"\n✨ Success! Created {len(created_labs)} labs with correct naming scheme.")
    else:
        print("❌ No labs were created successfully")

if __name__ == "__main__":
    main()