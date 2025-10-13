"""
Account CLI module using v2 APIs and centralized managers.
Provides account management functionality.
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.core.logging import get_logger


class AccountCLI(EnhancedBaseCLI):
    """Account management CLI using v2 APIs and centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("account_cli")

    async def list_accounts(self) -> Dict[str, Any]:
        """List all accounts"""
        try:
            self.logger.info("Listing all accounts")
            
            if not self.account_api:
                return {"error": "Account API not available"}
            
            accounts = await self.account_api.list_accounts()
            
            return {
                "success": True,
                "accounts": accounts,
                "count": len(accounts) if accounts else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error listing accounts: {e}")
            return {"error": str(e)}

    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get account details"""
        try:
            self.logger.info(f"Getting account details for {account_id}")
            
            if not self.account_api:
                return {"error": "Account API not available"}
            
            account = await self.account_api.get_account_details(account_id)
            
            if account:
                return {
                    "success": True,
                    "account": account
                }
            else:
                return {
                    "success": False,
                    "error": f"Account {account_id} not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting account details: {e}")
            return {"error": str(e)}

    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get account balance"""
        try:
            self.logger.info(f"Getting account balance for {account_id}")
            
            if not self.account_api:
                return {"error": "Account API not available"}
            
            balance = await self.account_api.get_account_balance(account_id)
            
            if balance is not None:
                return {
                    "success": True,
                    "account_id": account_id,
                    "balance": balance
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not retrieve balance for account {account_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            return {"error": str(e)}

    def print_accounts_report(self, accounts_data: Dict[str, Any]):
        """Print accounts report"""
        try:
            if "error" in accounts_data:
                print(f"❌ Error: {accounts_data['error']}")
                return
            
            accounts = accounts_data.get("accounts", [])
            count = accounts_data.get("count", 0)
            
            print("\n" + "="*80)
            print("💼 ACCOUNTS REPORT")
            print("="*80)
            print(f"📊 Total Accounts: {count}")
            print("-"*80)
            
            if accounts:
                for account in accounts:
                    account_id = getattr(account, 'id', 'Unknown')
                    account_name = getattr(account, 'name', 'Unknown')
                    account_type = getattr(account, 'type', 'Unknown')
                    status = getattr(account, 'status', 'Unknown')
                    
                    print(f"🏦 {account_name}")
                    print(f"   ID: {account_id}")
                    print(f"   Type: {account_type}")
                    print(f"   Status: {status}")
                    print()
            else:
                print("No accounts found")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing accounts report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_account_details_report(self, account_data: Dict[str, Any]):
        """Print account details report"""
        try:
            if "error" in account_data:
                print(f"❌ Error: {account_data['error']}")
                return
            
            if not account_data.get("success", False):
                print(f"❌ {account_data.get('error', 'Unknown error')}")
                return
            
            account = account_data.get("account")
            if not account:
                print("❌ No account data available")
                return
            
            print("\n" + "="*80)
            print("💼 ACCOUNT DETAILS")
            print("="*80)
            
            # Basic info
            account_id = getattr(account, 'id', 'Unknown')
            account_name = getattr(account, 'name', 'Unknown')
            account_type = getattr(account, 'type', 'Unknown')
            status = getattr(account, 'status', 'Unknown')
            
            print(f"🏦 {account_name}")
            print(f"   ID: {account_id}")
            print(f"   Type: {account_type}")
            print(f"   Status: {status}")
            
            # Additional details
            if hasattr(account, 'balance'):
                print(f"   Balance: {account.balance}")
            if hasattr(account, 'currency'):
                print(f"   Currency: {account.currency}")
            if hasattr(account, 'created_at'):
                print(f"   Created: {account.created_at}")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing account details report: {e}")
            print(f"❌ Error generating report: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Account Management CLI")
    parser.add_argument("--list", action="store_true", help="List all accounts")
    parser.add_argument("--details", type=str, help="Get account details by ID")
    parser.add_argument("--balance", type=str, help="Get account balance by ID")
    
    args = parser.parse_args()
    
    cli = AccountCLI()
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        if args.list:
            # List accounts
            accounts_data = await cli.list_accounts()
            cli.print_accounts_report(accounts_data)
            
        elif args.details:
            # Get account details
            account_data = await cli.get_account_details(args.details)
            cli.print_account_details_report(account_data)
            
        elif args.balance:
            # Get account balance
            balance_data = await cli.get_account_balance(args.balance)
            if balance_data.get("success"):
                print(f"💰 Account {args.balance} Balance: {balance_data['balance']}")
            else:
                print(f"❌ {balance_data.get('error', 'Unknown error')}")
                
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())





