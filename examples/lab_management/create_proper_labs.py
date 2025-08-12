#!/usr/bin/env python3
"""
Create labs with proper Binance Futures market tags
Based on the curl example: BINANCEFUTURES_UNI_USDT_PERPETUAL
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

class ProperLabCreator:
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
    
    def update_lab_config(self, lab_id: str, coin: str, account_id: str) -> bool:
        """Update lab configuration with proper market tag"""
        # This would need to be implemented in the MCP server
        # For now, we'll document what needs to be done
        market_tag = f"BINANCEFUTURES_{coin}_USDT_PERPETUAL"
        print(f"    📊 Need to set market: {market_tag}")
        print(f"    👤 Need to set account: {account_id}")
        return True
    
    def start_lab_backtest(self, lab_id: str) -> bool:
        """Start lab backtest execution"""
        try:
            # Calculate 2-year period (current time - 2 years to current time)
            import time
            current_time = int(time.time())
            two_years_ago = current_time - (2 * 365 * 24 * 60 * 60)  # 2 years in seconds
            
            payload = {
                "lab_id": lab_id,
                "start_unix": two_years_ago,
                "end_unix": current_time,
                "send_email": False
            }
            
            response = self.session.post(f"{self.mcp_url}/backtest_lab", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    print(f"    ✅ Backtest started successfully")
                    return True
                else:
                    print(f"    ❌ Backtest start failed: {data.get('Error', 'Unknown error')}")
            else:
                print(f"    ❌ HTTP error starting backtest: {response.status_code}")
            return False
        except Exception as e:
            print(f"    ❌ Error starting backtest: {e}")
            return False
    
    def get_lab_execution_status(self, lab_id: str) -> Optional[Dict]:
        """Get lab execution status"""
        try:
            response = self.session.post(f"{self.mcp_url}/get_lab_execution_update", 
                                       json={"lab_id": lab_id})
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data")
            return None
        except Exception as e:
            print(f"    ⚠️  Error getting execution status: {e}")
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
    
    def create_single_lab(self, coin: str, strategy: str, test_account_id: Optional[str]) -> Optional[Dict]:
        """Create a single lab for a coin with proper verification"""
        print(f"\n🔧 Creating lab for {coin} with {strategy}...")
        
        # Generate lab name following the documented format:
        # {version} - {script_name} - {period} {coin} ({timeframe_details}) - {additional_info}
        lab_name = f"0 - {strategy} - 2 years {coin} - alpha test"
        
        # Clone the lab
        cloned_lab = self.clone_lab(BASE_LAB_ID, lab_name)
        
        if not cloned_lab:
            return None
        
        lab_id = cloned_lab.get("LID") or cloned_lab.get("lab_id")
        print(f"  ✅ Cloned: {lab_name}")
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
                print(f"  ⚠️  Market tag needs update to: {expected_market}")
        
        # Update configuration if needed
        if test_account_id:
            self.update_lab_config(lab_id, coin, test_account_id)
        
        return {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "coin": coin,
            "strategy": strategy,
            "expected_market_tag": f"BINANCEFUTURES_{coin}_USDT_PERPETUAL"
        }
    
    def create_labs_step_by_step(self, strategy: str = "ADX BB STOCH Scalper") -> Dict[str, Dict]:
        """Create labs one by one with verification"""
        print(f"🚀 Creating labs step by step for proper verification")
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
        
        created_labs = {}
        
        # Create labs one by one
        for i, coin in enumerate(TRADING_PAIRS, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(TRADING_PAIRS)}] Processing {coin}")
            print(f"{'='*60}")
            
            lab_data = self.create_single_lab(coin, strategy, test_account_id)
            
            if lab_data:
                created_labs[coin] = lab_data
                print(f"  ✅ {coin} lab created successfully")
                
                # Ask user if they want to continue
                if i < len(TRADING_PAIRS):
                    continue_input = input(f"\nContinue with next coin? (Y/n): ").strip().lower()
                    if continue_input == 'n':
                        print("🛑 Stopping at user request")
                        break
            else:
                print(f"  ❌ Failed to create lab for {coin}")
                continue_input = input(f"Continue with next coin? (Y/n): ").strip().lower()
                if continue_input == 'n':
                    print("🛑 Stopping at user request")
                    break
            
            # Small delay
            time.sleep(1)
        
        return created_labs
    
    def save_results(self, created_labs: Dict[str, Dict]):
        """Save results to file"""
        try:
            with open("proper_labs.json", "w") as f:
                json.dump(created_labs, f, indent=2)
            print(f"💾 Results saved to proper_labs.json")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def print_summary(self, created_labs: Dict[str, Dict]):
        """Print summary"""
        print(f"\n{'='*80}")
        print("PROPER LABS CREATION SUMMARY")
        print(f"{'='*80}")
        print(f"Successfully created {len(created_labs)} labs:")
        
        for coin, lab_data in created_labs.items():
            print(f"  {coin}: {lab_data['lab_id']}")
            print(f"    Expected market: {lab_data['expected_market_tag']}")
        
        print(f"\n📋 Next steps:")
        print(f"1. Verify each lab has correct market configuration in HaasOnline interface")
        print(f"2. Ensure proper account assignment")
        print(f"3. Configure lab parameters (population: 50, generations: 50, etc.)")
        print(f"4. Start backtesting")

def main():
    print("🎯 Creating labs with proper naming scheme and market tags")
    print("Naming format: {version} - {script_name} - {period} {coin} - {additional_info}")
    print("Market format: BINANCEFUTURES_{COIN}_USDT_PERPETUAL")
    
    # For now, we'll start with ADX BB STOCH Scalper as mentioned in the task
    strategy = "ADX BB STOCH Scalper"
    print(f"Strategy: {strategy}")
    
    creator = ProperLabCreator(MCP_SERVER_URL)
    created_labs = creator.create_labs_step_by_step(strategy)
    
    if created_labs:
        creator.save_results(created_labs)
        creator.print_summary(created_labs)
    else:
        print("❌ No labs were created successfully")

if __name__ == "__main__":
    main()