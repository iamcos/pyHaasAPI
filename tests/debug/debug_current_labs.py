#!/usr/bin/env python3
"""
Debug current labs to understand market tag format and delete incorrectly created labs
"""

import requests
import json
from typing import List, Dict, Optional

MCP_SERVER_URL = "http://127.0.0.1:8000"

class LabDebugger:
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.session = requests.Session()
        
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
            print(f"Error getting lab details for {lab_id}: {e}")
            return None
    
    def get_all_markets(self) -> List[Dict]:
        """Get all available markets to understand naming scheme"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_all_markets")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data", [])
            return []
        except Exception as e:
            print(f"Error getting markets: {e}")
            return []
    
    def delete_lab(self, lab_id: str) -> bool:
        """Delete a lab"""
        try:
            response = self.session.delete(f"{self.mcp_url}/delete_lab/{lab_id}")
            if response.status_code == 200:
                data = response.json()
                return data.get("Success", False)
            return False
        except Exception as e:
            print(f"Error deleting lab {lab_id}: {e}")
            return False
    
    def analyze_binance_market_naming(self):
        """Analyze Binance market naming scheme"""
        print("🔍 Analyzing Binance market naming scheme...")
        
        markets = self.get_all_markets()
        if not markets:
            print("❌ No markets found")
            return {}
        
        binance_markets = {}
        binance_futures_markets = {}
        
        for market in markets:
            market_name = market.get("market_name", "").upper()
            primary = market.get("primary_currency", "").upper()
            secondary = market.get("secondary_currency", "").upper()
            market_tag = market.get("market_tag", "")
            exchange = market.get("exchange", "").upper()
            
            if "BINANCE" in exchange:
                pair_key = f"{primary}_{secondary}"
                
                if "FUTURES" in exchange or "PERPETUAL" in market_tag:
                    binance_futures_markets[pair_key] = {
                        "market_tag": market_tag,
                        "market_name": market_name,
                        "exchange": exchange,
                        "primary": primary,
                        "secondary": secondary
                    }
                else:
                    binance_markets[pair_key] = {
                        "market_tag": market_tag,
                        "market_name": market_name,
                        "exchange": exchange,
                        "primary": primary,
                        "secondary": secondary
                    }
        
        print(f"📊 Found {len(binance_markets)} Binance spot markets")
        print(f"📊 Found {len(binance_futures_markets)} Binance futures markets")
        
        # Show examples for our target pairs
        target_pairs = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "UNI_USDT"]
        
        print("\n🎯 Target pairs analysis:")
        for pair in target_pairs:
            if pair in binance_futures_markets:
                market = binance_futures_markets[pair]
                print(f"  {pair}: {market['market_tag']}")
            elif pair in binance_markets:
                market = binance_markets[pair]
                print(f"  {pair}: {market['market_tag']} (spot)")
            else:
                print(f"  {pair}: NOT FOUND")
        
        return {
            "binance_spot": binance_markets,
            "binance_futures": binance_futures_markets
        }
    
    def debug_current_labs(self):
        """Debug currently created labs"""
        print("🔧 Debugging current labs...")
        
        labs = self.get_all_labs()
        task_labs = [lab for lab in labs if lab.get("N", "").startswith("Task_")]
        
        print(f"📋 Found {len(task_labs)} task labs:")
        
        for lab in task_labs:
            lab_id = lab.get("LID")
            lab_name = lab.get("N")
            print(f"\n  📝 {lab_name} ({lab_id})")
            
            # Get detailed configuration
            details = self.get_lab_details(lab_id)
            if details:
                settings = details.get("ST", {})
                market_tag = settings.get("marketTag", "N/A")
                account_id = settings.get("accountId", "N/A")
                print(f"    Market: {market_tag}")
                print(f"    Account: {account_id}")
            else:
                print("    ❌ Could not get lab details")
        
        return task_labs
    
    def delete_task_labs(self, task_labs: List[Dict]) -> int:
        """Delete all task labs"""
        print(f"\n🗑️  Deleting {len(task_labs)} task labs...")
        
        deleted_count = 0
        for lab in task_labs:
            lab_id = lab.get("LID")
            lab_name = lab.get("N")
            
            if self.delete_lab(lab_id):
                print(f"  ✅ Deleted: {lab_name}")
                deleted_count += 1
            else:
                print(f"  ❌ Failed to delete: {lab_name}")
        
        return deleted_count
    
    def save_market_naming_scheme(self, market_data: Dict):
        """Save the discovered market naming scheme"""
        try:
            with open("binance_market_naming.json", "w") as f:
                json.dump(market_data, f, indent=2)
            print("💾 Saved Binance market naming scheme to binance_market_naming.json")
        except Exception as e:
            print(f"Error saving market naming scheme: {e}")

def main():
    print("🚀 Debugging current labs and learning market naming scheme")
    
    debugger = LabDebugger(MCP_SERVER_URL)
    
    # 1. Analyze Binance market naming scheme
    market_data = debugger.analyze_binance_market_naming()
    
    # 2. Debug current labs
    task_labs = debugger.debug_current_labs()
    
    # 3. Ask user if they want to delete the incorrectly created labs
    if task_labs:
        print(f"\n⚠️  Found {len(task_labs)} incorrectly created task labs")
        delete_confirm = input("Delete all task labs? (y/N): ").strip().lower()
        
        if delete_confirm == 'y':
            deleted_count = debugger.delete_task_labs(task_labs)
            print(f"✅ Deleted {deleted_count} labs")
        else:
            print("🔄 Keeping existing labs")
    
    # 4. Save market naming scheme for future use
    debugger.save_market_naming_scheme(market_data)
    
    print("\n📋 Next steps:")
    print("1. Use the discovered market naming scheme for correct lab creation")
    print("2. Create labs one by one with proper market tags")
    print("3. Verify each lab has correct market configuration")

if __name__ == "__main__":
    main()