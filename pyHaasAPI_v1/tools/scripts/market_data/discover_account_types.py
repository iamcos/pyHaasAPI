#!/usr/bin/env python3
"""
Discover Account Types Script
-----------------------------
This script discovers and documents all available exchange account types in the HaasOnline system.

It attempts to:
1. Query existing accounts to see what types are already configured
2. Test common driver codes and types to see what's available
3. Document the findings for future reference

Run with: python scripts/market_data/discover_account_types.py
"""

import os
import sys
import time
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from dotenv import load_dotenv
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.exceptions import HaasApiError

@dataclass
class AccountType:
    """Represents an account type configuration"""
    driver_code: str
    driver_type: int
    name: str
    description: str = ""
    is_working: bool = False
    error_message: str = ""

class AccountTypeDiscoverer:
    """Discovers and documents available account types in HaasOnline"""
    
    def __init__(self):
        self.executor = None
        self.existing_accounts = []
        self.discovered_types = []
        
        # Common driver codes to test
        self.common_driver_codes = [
            # Binance variations
            "BINANCE", "BINANCEQUARTERLY", "BINANCESPOT", "BINANCEFUTURES", "BINANCEUS",
            # Bybit variations
            "BYBIT", "BYBITSPOT", "BYBITFUTURES", "BYBITUSDT", "BYBITINVERSE",
            # Other major exchanges
            "KRAKEN", "COINBASE", "COINBASEPRO", "KUCOIN", "OKX", "OKEX",
            "HUOBI", "GATEIO", "BITGET", "MEXC", "BITFINEX", "POLONIEX",
            # Derivatives and futures
            "DERIBIT", "FTX", "BITMEX", "DYDX", "PERPETUAL", "FUTURES",
            # Simulated and test
            "SIM", "SIMULATED", "TEST", "DEMO", "PAPER",
            # Generic types
            "SPOT", "FUTURES", "OPTIONS", "MARGIN", "LEVERAGE"
        ]
        
        # Common driver types to test
        self.common_driver_types = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
    def setup(self) -> bool:
        """Initialize authentication"""
        print("🔐 Setting up authentication...")
        
        try:
            load_dotenv()
            
            self.executor = api.RequestsExecutor(
                host=settings.API_HOST,
                port=settings.API_PORT,
                state=api.Guest()
            ).authenticate(
                email=settings.API_EMAIL,
                password=settings.API_PASSWORD
            )
            
            print("✅ Authentication successful")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_existing_accounts(self) -> List[Dict]:
        """Get all existing accounts and analyze their types"""
        print("\n📊 Analyzing existing accounts...")
        
        try:
            accounts = api.get_accounts(self.executor)
            self.existing_accounts = accounts
            
            print(f"Found {len(accounts)} existing accounts:")
            
            # Group by exchange code and type
            account_types = {}
            for account in accounts:
                key = (account.exchange_code, account.exchange_type)
                if key not in account_types:
                    account_types[key] = []
                account_types[key].append(account)
            
            # Print summary
            for (exchange_code, exchange_type), account_list in account_types.items():
                print(f"  {exchange_code} (Type {exchange_type}): {len(account_list)} accounts")
                for account in account_list:
                    print(f"    - {account.name} (ID: {account.account_id})")
                    print(f"      Simulated: {account.is_simulated}, Test Net: {account.is_test_net}")
            
            return accounts
            
        except Exception as e:
            print(f"❌ Error getting existing accounts: {e}")
            return []
    
    def test_account_type(self, driver_code: str, driver_type: int) -> AccountType:
        """Test if a specific account type is available"""
        test_name = f"Test_{driver_code}_{driver_type}"
        
        try:
            # Try to create a simulated account with this configuration
            result = api.add_simulated_account(
                self.executor,
                name=test_name,
                driver_code=driver_code,
                driver_type=driver_type
            )
            
            # If successful, delete it immediately
            if result and "AID" in result:
                account_id = result["AID"]
                try:
                    api.delete_account(self.executor, account_id)
                except:
                    pass  # Ignore deletion errors
                
                return AccountType(
                    driver_code=driver_code,
                    driver_type=driver_type,
                    name=f"{driver_code} (Type {driver_type})",
                    description=f"Successfully created and deleted test account",
                    is_working=True
                )
            else:
                return AccountType(
                    driver_code=driver_code,
                    driver_type=driver_type,
                    name=f"{driver_code} (Type {driver_type})",
                    description="API returned success but no account ID",
                    is_working=False,
                    error_message="No account ID in response"
                )
                
        except HaasApiError as e:
            return AccountType(
                driver_code=driver_code,
                driver_type=driver_type,
                name=f"{driver_code} (Type {driver_type})",
                description="API error occurred",
                is_working=False,
                error_message=str(e)
            )
        except Exception as e:
            return AccountType(
                driver_code=driver_code,
                driver_type=driver_type,
                name=f"{driver_code} (Type {driver_type})",
                description="Unexpected error",
                is_working=False,
                error_message=str(e)
            )
    
    def discover_working_types(self) -> List[AccountType]:
        """Discover working account types by testing combinations"""
        print("\n🔍 Discovering working account types...")
        
        working_types = []
        total_tests = len(self.common_driver_codes) * len(self.common_driver_types)
        current_test = 0
        
        for driver_code in self.common_driver_codes:
            for driver_type in self.common_driver_types:
                current_test += 1
                print(f"Testing {current_test}/{total_tests}: {driver_code} (Type {driver_type})")
                
                account_type = self.test_account_type(driver_code, driver_type)
                
                if account_type.is_working:
                    working_types.append(account_type)
                    print(f"  ✅ Working: {driver_code} (Type {driver_type})")
                else:
                    print(f"  ❌ Failed: {driver_code} (Type {driver_type}) - {account_type.error_message}")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
        
        return working_types
    
    def generate_documentation(self, working_types: List[AccountType]) -> str:
        """Generate documentation for discovered account types"""
        print("\n📝 Generating documentation...")
        
        doc = """# HaasOnline Account Types Discovery

This document was generated by the account type discovery script.

## Summary

- **Total existing accounts**: {existing_count}
- **Working account types discovered**: {working_count}
- **Test date**: {date}

## Existing Accounts

{existing_accounts_section}

## Working Account Types

These account types were successfully tested and can be used to create simulated accounts:

{working_types_section}

## Usage Examples

### Creating a Simulated Account

```python
from pyHaasAPI_v1 import api

# Example: Create a Binance Quarterly Futures simulated account
result = api.add_simulated_account(
    executor,
    name="My Binance Quarterly Account",
    driver_code="BINANCEQUARTERLY",
    driver_type=2
)

if result and "AID" in result:
    account_id = result["AID"]
    print(f"Created account with ID: {account_id}")
```

### Testing Account Credentials

```python
# Example: Test Binance Spot account credentials
result = api.test_account(
    executor,
    driver_code="BINANCESPOT",
    driver_type=0,
    version=5,
    public_key="your_public_key",
    private_key="your_private_key"
)
```

## Notes

- Driver types appear to correspond to different account configurations (spot, futures, etc.)
- Some driver codes may be exchange-specific
- Always test account creation in a safe environment first
- Delete test accounts after discovery to keep your account list clean

""".format(
            existing_count=len(self.existing_accounts),
            working_count=len(working_types),
            date=time.strftime("%Y-%m-%d %H:%M:%S"),
            existing_accounts_section=self._format_existing_accounts(),
            working_types_section=self._format_working_types(working_types)
        )
        
        return doc
    
    def _format_existing_accounts(self) -> str:
        """Format existing accounts for documentation"""
        if not self.existing_accounts:
            return "No existing accounts found."
        
        lines = []
        for account in self.existing_accounts:
            lines.append(f"- **{account.name}**")
            lines.append(f"  - Exchange: {account.exchange_code}")
            lines.append(f"  - Type: {account.exchange_type}")
            lines.append(f"  - Account ID: {account.account_id}")
            lines.append(f"  - Simulated: {account.is_simulated}")
            lines.append(f"  - Test Net: {account.is_test_net}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_working_types(self, working_types: List[AccountType]) -> str:
        """Format working types for documentation"""
        if not working_types:
            return "No working account types discovered."
        
        # Group by driver code
        grouped = {}
        for account_type in working_types:
            if account_type.driver_code not in grouped:
                grouped[account_type.driver_code] = []
            grouped[account_type.driver_code].append(account_type)
        
        lines = []
        for driver_code, types in sorted(grouped.items()):
            lines.append(f"### {driver_code}")
            for account_type in sorted(types, key=lambda x: x.driver_type):
                lines.append(f"- **Type {account_type.driver_type}**: {account_type.description}")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_documentation(self, documentation: str, filename: str = "discovered_account_types.md"):
        """Save documentation to file"""
        filepath = os.path.join("docs", filename)
        
        try:
            os.makedirs("docs", exist_ok=True)
            with open(filepath, "w") as f:
                f.write(documentation)
            print(f"✅ Documentation saved to: {filepath}")
        except Exception as e:
            print(f"❌ Error saving documentation: {e}")
    
    def run_discovery(self):
        """Run the complete discovery process"""
        print("🚀 Starting Account Type Discovery")
        print("=" * 50)
        
        # Setup
        if not self.setup():
            return
        
        # Get existing accounts
        self.get_existing_accounts()
        
        # Discover working types
        working_types = self.discover_working_types()
        
        # Generate and save documentation
        documentation = self.generate_documentation(working_types)
        self.save_documentation(documentation)
        
        # Print summary
        print("\n" + "=" * 50)
        print("🎉 Discovery Complete!")
        print(f"📊 Found {len(working_types)} working account types")
        print(f"📝 Documentation saved to: docs/discovered_account_types.md")
        
        # Print quick reference
        print("\n📋 Quick Reference - Working Account Types:")
        for account_type in working_types:
            print(f"  {account_type.driver_code} (Type {account_type.driver_type})")

def main():
    """Main function"""
    discoverer = AccountTypeDiscoverer()
    discoverer.run_discovery()

if __name__ == "__main__":
    main() 