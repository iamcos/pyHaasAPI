#!/usr/bin/env python3
"""
Create labs for all perpetual trading pairs from base lab 7e39fd98-ad7c-4753-8802-c19b2ab11c31
This script discovers all perpetual markets and clones the base lab for each one.
"""

import requests
import json
import time
from typing import List, Dict, Optional

BASE_LAB_ID = "7e39fd98-ad7c-4753-8802-c19b2ab11c31"
MCP_SERVER_URL = "http://127.0.0.1:8000"

class PerpetualLabCreator:
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
    
    def get_all_markets(self) -> List[Dict]:
        """Get all available markets from HaasOnline"""
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
    
    def filter_perpetual_markets(self, markets: List[Dict]) -> List[Dict]:
        """Filter markets to only include perpetual contracts"""
        perpetual_markets = []
        
        for market in markets:
            market_name = market.get("market_name", "").upper()
            primary_currency = market.get("primary_currency", "").upper()
            secondary_currency = market.get("secondary_currency", "").upper()
            
            # Look for perpetual indicators in market name
            perpetual_indicators = [
                "PERP", "PERPETUAL", "SWAP", 
                "_USDT_", "_BUSD_", "_USD_",  # Common perpetual suffixes
                "FUTURES", "FUT"
            ]
            
            # Check if it's a perpetual market
            is_perpetual = any(indicator in market_name for indicator in perpetual_indicators)
            
            # Additional check for USDT pairs (common for perpetuals)
            is_usdt_pair = secondary_currency == "USDT"
            
            if is_perpetual or is_usdt_pair:
                perpetual_markets.append({
                    "market_name": market_name,
                    "primary_currency": primary_currency,
                    "secondary_currency": secondary_currency,
                    "market_tag": market.get("market_tag", ""),
                    "exchange": market.get("exchange", ""),
                    "full_market_data": market
                })
        
        return perpetual_markets
    
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
    
    def create_labs_for_perpetual_markets(self, limit: Optional[int] = None) -> Dict[str, str]:
        """Create labs for all perpetual markets"""
        print("🔍 Discovering all perpetual markets...")
        
        # Check MCP server status
        if not self.check_mcp_server_status():
            print("❌ MCP server is not running or not authenticated")
            return {}
        
        print("✅ MCP server is running and authenticated")
        
        # Get all markets
        all_markets = self.get_all_markets()
        if not all_markets:
            print("❌ No markets found")
            return {}
        
        print(f"📊 Found {len(all_markets)} total markets")
        
        # Filter for perpetual markets
        perpetual_markets = self.filter_perpetual_markets(all_markets)
        print(f"🎯 Found {len(perpetual_markets)} perpetual markets")
        
        # Apply limit if specified
        if limit:
            perpetual_markets = perpetual_markets[:limit]
            print(f"📝 Limited to first {limit} markets for testing")
        
        # Find test account
        test_account_id = self.find_test_account()
        if not test_account_id:
            print("❌ Could not find test account")
            return {}
        
        print(f"✅ Found test account: {test_account_id}")
        
        created_labs = {}
        
        print(f"\n🚀 Creating labs for {len(perpetual_markets)} perpetual markets...")
        
        for i, market in enumerate(perpetual_markets, 1):
            primary = market["primary_currency"]
            secondary = market["secondary_currency"]
            exchange = market["exchange"]
            
            print(f"\n[{i}/{len(perpetual_markets)}] Creating lab for {primary}/{secondary} on {exchange}...")
            
            # Generate lab name
            lab_name = f"Perpetual_{exchange}_{primary}_{secondary}"
            
            # Clone the lab
            cloned_lab = self.clone_lab(BASE_LAB_ID, lab_name)
            
            if cloned_lab:
                lab_id = cloned_lab.get("lab_id")
                print(f"  ✅ Cloned lab: {lab_name} (ID: {lab_id})")
                
                market_key = f"{exchange}_{primary}_{secondary}"
                created_labs[market_key] = {
                    "lab_id": lab_id,
                    "market_tag": market["market_tag"],
                    "market_name": market["market_name"],
                    "exchange": exchange,
                    "primary": primary,
                    "secondary": secondary
                }
                
                print(f"  📊 Market tag: {market['market_tag']}")
            else:
                print(f"  ❌ Failed to clone lab for {primary}/{secondary}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        return created_labs
    
    def save_results_to_file(self, created_labs: Dict[str, Dict], filename: str = "perpetual_labs.json"):
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
        print("PERPETUAL LABS CREATION SUMMARY")
        print(f"{'='*80}")
        print(f"Successfully created {len(created_labs)} labs:")
        
        # Group by exchange
        exchanges = {}
        for market_key, lab_data in created_labs.items():
            exchange = lab_data["exchange"]
            if exchange not in exchanges:
                exchanges[exchange] = []
            exchanges[exchange].append(lab_data)
        
        for exchange, labs in exchanges.items():
            print(f"\n{exchange} ({len(labs)} markets):")
            for lab in labs:
                print(f"  {lab['primary']}/{lab['secondary']}: {lab['lab_id']}")
        
        print(f"\nNext steps:")
        print(f"1. Configure each lab with appropriate market tags")
        print(f"2. Set up lab parameters (algorithm, population, etc.)")
        print(f"3. Assign test account to all labs")
        print(f"4. Start distributed backtesting")
        print(f"\nNote: Market configuration may need manual adjustment in HaasOnline interface")

def main():
    print("🚀 Creating labs for all perpetual markets")
    print(f"Base lab ID: {BASE_LAB_ID}")
    
    # Ask user for limit to avoid overwhelming
    try:
        limit_input = input("Enter max number of markets to process (or press Enter for all): ").strip()
        limit = int(limit_input) if limit_input else None
    except ValueError:
        limit = None
    
    creator = PerpetualLabCreator(MCP_SERVER_URL)
    created_labs = creator.create_labs_for_perpetual_markets(limit=limit)
    
    if created_labs:
        creator.save_results_to_file(created_labs)
        creator.print_summary(created_labs)
    else:
        print("❌ No labs were created")

if __name__ == "__main__":
    main()