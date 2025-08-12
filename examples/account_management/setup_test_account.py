#!/usr/bin/env python3
"""
Setup the test account "для тестов 10к" with correct balance
"""

import requests
import json
from typing import Optional, Dict

MCP_SERVER_URL = "http://127.0.0.1:8000"

class TestAccountSetup:
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
    
    def get_all_accounts(self) -> list:
        """Get all existing accounts"""
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
    
    def find_test_account(self) -> Optional[Dict]:
        """Find existing test account"""
        accounts = self.get_all_accounts()
        for account in accounts:
            account_name = account.get("name", "")
            if "для тестов 10к" in account_name:
                return account
        return None
    
    def create_simulated_account(self, name: str, driver_type: int = 1) -> Optional[Dict]:
        """Create a new simulated account"""
        try:
            payload = {
                "name": name,
                "driver_type": driver_type  # 1 for Binance Futures typically
            }
            response = self.session.post(f"{self.mcp_url}/create_simulated_account", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data")
                else:
                    print(f"❌ Account creation failed: {data.get('Error', 'Unknown error')}")
            else:
                print(f"❌ HTTP error creating account: {response.status_code}")
            return None
        except Exception as e:
            print(f"❌ Error creating account: {e}")
            return None
    
    def deposit_funds(self, account_id: str, amount: float = 10000.0) -> bool:
        """Deposit funds to account"""
        try:
            payload = {
                "account_id": account_id,
                "amount": amount
            }
            response = self.session.post(f"{self.mcp_url}/deposit_funds", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return True
                else:
                    print(f"❌ Deposit failed: {data.get('Error', 'Unknown error')}")
            else:
                print(f"❌ HTTP error depositing funds: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Error depositing funds: {e}")
            return False
    
    def get_account_balance(self, account_id: str) -> Optional[Dict]:
        """Get account balance"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_account_balance/{account_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data")
            return None
        except Exception as e:
            print(f"Error getting account balance: {e}")
            return None
    
    def setup_test_account(self) -> Optional[str]:
        """Setup the test account with correct balance"""
        print("🔧 Setting up test account 'для тестов 10к'...")
        
        # Check MCP server status
        if not self.check_mcp_server_status():
            print("❌ MCP server is not running or not authenticated")
            return None
        
        print("✅ MCP server is running and authenticated")
        
        # Check if test account already exists
        existing_account = self.find_test_account()
        
        if existing_account:
            account_id = existing_account.get("account_id")
            account_name = existing_account.get("name")
            print(f"✅ Found existing test account: {account_name} ({account_id})")
            
            # Check balance
            balance = self.get_account_balance(account_id)
            if balance:
                current_balance = balance.get("balance", 0)
                print(f"💰 Current balance: {current_balance} USDT")
                
                if current_balance < 10000:
                    print(f"💸 Adding funds to reach 10,000 USDT...")
                    needed_amount = 10000 - current_balance
                    if self.deposit_funds(account_id, needed_amount):
                        print(f"✅ Added {needed_amount} USDT")
                    else:
                        print(f"❌ Failed to add funds")
                        return None
                else:
                    print(f"✅ Balance is sufficient")
            
            return account_id
        
        else:
            print("📝 Creating new test account...")
            
            # Create new account
            account_data = self.create_simulated_account("для тестов 10к")
            
            if not account_data:
                return None
            
            account_id = account_data.get("account_id")
            print(f"✅ Created account: {account_id}")
            
            # Deposit initial funds
            print(f"💰 Depositing 10,000 USDT...")
            if self.deposit_funds(account_id, 10000.0):
                print(f"✅ Deposited 10,000 USDT")
            else:
                print(f"❌ Failed to deposit funds")
                return None
            
            return account_id
    
    def verify_account_setup(self, account_id: str):
        """Verify the account is properly set up"""
        print(f"\n🔍 Verifying account setup...")
        
        # Get account details
        accounts = self.get_all_accounts()
        account = next((acc for acc in accounts if acc.get("account_id") == account_id), None)
        
        if account:
            print(f"✅ Account found: {account.get('name')}")
            print(f"📋 Account ID: {account_id}")
            
            # Check balance
            balance = self.get_account_balance(account_id)
            if balance:
                current_balance = balance.get("balance", 0)
                print(f"💰 Balance: {current_balance} USDT")
                
                if current_balance >= 10000:
                    print(f"✅ Account is properly funded")
                    return True
                else:
                    print(f"❌ Insufficient balance")
            else:
                print(f"❌ Could not get balance")
        else:
            print(f"❌ Account not found")
        
        return False

def main():
    print("🚀 Setting up test account 'для тестов 10к'")
    
    setup = TestAccountSetup(MCP_SERVER_URL)
    account_id = setup.setup_test_account()
    
    if account_id:
        if setup.verify_account_setup(account_id):
            print(f"\n✨ Success! Test account is ready:")
            print(f"   Name: для тестов 10к")
            print(f"   ID: {account_id}")
            print(f"   Balance: 10,000+ USDT")
            print(f"\n📋 Next step: Recreate labs with this account")
        else:
            print(f"\n❌ Account setup verification failed")
    else:
        print(f"\n❌ Failed to setup test account")

if __name__ == "__main__":
    main()