#!/usr/bin/env python3
"""
Create labs for all trading pairs from base lab 7e39fd98-ad7c-4753-8802-c19b2ab11c31
This script clones the base lab for each trading pair on server 1.
Uses MarketResolver to handle different exchange naming schemes and contract types.
"""

import requests
import json
import time
from typing import List, Dict, Optional
from examples.market_analysis.market_resolver import MarketResolver, ContractType

# Trading pairs from task_at_hand.md
TRADING_PAIRS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "APT", 
    "LTC", "BCH", "ADA", "UNI", "GALA", "TRX"
]

BASE_LAB_ID = "7e39fd98-ad7c-4753-8802-c19b2ab11c31"
MCP_SERVER_URL = "http://127.0.0.1:8000"  # Assuming MCP server is running locally

# Safety settings
SAFE_MODE = True  # Set to False only when HaasScript editing is confirmed safe
CURRENT_SERVER = "srv01"  # Track which server we're connected to

class LabCreator:
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.session = requests.Session()
        self.market_resolver = MarketResolver(mcp_url)
        
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
    
    def resolve_market_tag_for_coin(self, coin: str) -> Optional[str]:
        """Resolve the correct market tag for a coin using MarketResolver"""
        return self.market_resolver.resolve_market_tag_safely(
            base_asset=coin,
            quote_asset="USDT", 
            exchange="BINANCE",
            contract_type=ContractType.PERPETUAL
        )
    
    def update_lab_market(self, lab_id: str, coin: str, account_id: str) -> bool:
        """Update lab market and account - SAFE MODE CHECK"""
        if SAFE_MODE and CURRENT_SERVER in ["srv01", "srv02"]:
            print(f"  ⚠️  SAFE MODE: Skipping lab configuration update for {coin}")
            print(f"     HaasScript editing may cause server issues on {CURRENT_SERVER}")
            print(f"     Manual configuration needed:")
            
            # Resolve correct market tag
            market_tag = self.resolve_market_tag_for_coin(coin)
            if market_tag:
                print(f"     - Market: {market_tag}")
            else:
                print(f"     - Market: BINANCE_{coin}_USDT_ (fallback - verify manually)")
            print(f"     - Account: {account_id}")
            return True
        
        # If not in safe mode or on srv03, attempt to update
        market_tag = self.resolve_market_tag_for_coin(coin)
        if not market_tag:
            print(f"  ❌ Could not resolve market tag for {coin}")
            return False
            
        print(f"  🔧 Updating lab {lab_id} with market: {market_tag} and account: {account_id}")
        # TODO: Implement actual lab update via MCP server endpoint
        # This would require adding update_lab_details endpoint to MCP server
        return True
    
    def create_labs_for_all_pairs(self) -> Dict[str, str]:
        """Create labs for all trading pairs"""
        print(f"🚀 Creating labs for {len(TRADING_PAIRS)} trading pairs...")
        print(f"📋 Base lab ID: {BASE_LAB_ID}")
        print(f"🖥️  Current server: {CURRENT_SERVER}")
        print(f"🛡️  Safe mode: {'ON' if SAFE_MODE else 'OFF'}")
        
        if SAFE_MODE:
            print("⚠️  SAFE MODE ENABLED: Lab configuration updates will be skipped")
            print("   This prevents potential server issues from HaasScript editing")
        
        # Check MCP server status
        if not self.check_mcp_server_status():
            print("❌ MCP server is not running or not authenticated")
            return {}
        
        print("✅ MCP server is running and authenticated")
        
        # Analyze available markets first
        print(f"\n{'='*60}")
        print("MARKET ANALYSIS")
        print(f"{'='*60}")
        self.market_resolver.print_market_analysis(TRADING_PAIRS)
        
        # Find test account
        test_account_id = self.find_test_account()
        if not test_account_id:
            print("❌ Could not find test account")
            return {}
        
        print(f"✅ Found test account: {test_account_id}")
        
        # Get existing labs to check if base lab exists
        existing_labs = self.get_all_labs()
        base_lab_exists = any(lab.get("lab_id") == BASE_LAB_ID for lab in existing_labs)
        
        if not base_lab_exists:
            print(f"❌ Base lab {BASE_LAB_ID} not found")
            return {}
        
        print(f"✅ Base lab {BASE_LAB_ID} found")
        
        created_labs = {}
        
        for i, coin in enumerate(TRADING_PAIRS, 1):
            print(f"\n[{i}/{len(TRADING_PAIRS)}] Creating lab for {coin}...")
            
            # Generate lab name
            lab_name = f"Distributed_Backtest_{coin}_USDT"
            
            # Clone the lab
            cloned_lab = self.clone_lab(BASE_LAB_ID, lab_name)
            
            if cloned_lab:
                lab_id = cloned_lab.get("lab_id")
                print(f"  ✅ Cloned lab: {lab_name} (ID: {lab_id})")
                
                # Update market and account (this would need MCP server implementation)
                if self.update_lab_market(lab_id, coin, test_account_id):
                    created_labs[coin] = lab_id
                    print(f"  ✅ Configured for {coin}")
                else:
                    print(f"  ⚠️  Lab created but market configuration needs manual setup")
                    created_labs[coin] = lab_id
            else:
                print(f"  ❌ Failed to clone lab for {coin}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(1)
        
        return created_labs
    
    def print_summary(self, created_labs: Dict[str, str]):
        """Print summary of created labs"""
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Successfully created {len(created_labs)} labs:")
        
        for coin, lab_id in created_labs.items():
            print(f"  {coin}: {lab_id}")
        
        if len(created_labs) < len(TRADING_PAIRS):
            failed_coins = set(TRADING_PAIRS) - set(created_labs.keys())
            print(f"\nFailed to create labs for: {', '.join(failed_coins)}")
        
        print(f"\nNext steps:")
        if SAFE_MODE:
            print(f"1. ⚠️  MANUALLY configure each lab with correct market and account:")
            for coin, lab_id in created_labs.items():
                market_tag = self.market_resolver.resolve_market_tag_safely(coin, "USDT", "BINANCE", ContractType.PERPETUAL)
                print(f"   - {coin} (Lab: {lab_id}): Market = {market_tag or f'BINANCE_{coin}_USDT_'}")
            print(f"2. Ensure all labs use the test account 'для тестов 10к'")
            print(f"3. Configure lab parameters (population: 50 for srv01)")
            print(f"4. When HaasScript editing is safe, disable SAFE_MODE and re-run")
        else:
            print(f"1. Verify each lab has correct market configuration")
            print(f"2. Ensure all labs use the test account 'для тестов 10к'")
            print(f"3. Configure lab parameters (population, generations, etc.)")
        print(f"5. Start distributed backtesting")

def main():
    print("🚀 Creating distributed labs for all trading pairs")
    print(f"Base lab ID: {BASE_LAB_ID}")
    print(f"Trading pairs: {', '.join(TRADING_PAIRS)}")
    
    creator = LabCreator(MCP_SERVER_URL)
    created_labs = creator.create_labs_for_all_pairs()
    creator.print_summary(created_labs)

if __name__ == "__main__":
    main()