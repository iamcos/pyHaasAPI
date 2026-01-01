#!/usr/bin/env python3
"""
List All Account Types
---------------------
Lists all account types currently in the HaasOnline system.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config import settings
from pyHaasAPI_v1 import api

def main():
    """Main function"""
    print("📊 All Account Types in Your System")
    print("=" * 50)
    
    # Authenticate
    print("🔐 Authenticating...")
    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Get all accounts
    try:
        accounts = api.get_accounts(executor)
        print(f"\nFound {len(accounts)} accounts:")
        print("-" * 50)
        
        # Group by exchange
        exchanges = {}
        for account in accounts:
            exchange = account.exchange_code
            if exchange not in exchanges:
                exchanges[exchange] = []
            exchanges[exchange].append(account)
        
        # Print grouped by exchange
        for exchange, accs in sorted(exchanges.items()):
            print(f"\n🔸 {exchange}:")
            for acc in accs:
                account_type = "Spot" if acc.exchange_type == 0 else "Futures" if acc.exchange_type == 1 else "Quarterly" if acc.exchange_type == 2 else f"Type {acc.exchange_type}"
                simulated = " (Simulated)" if acc.is_simulated else ""
                print(f"  - {acc.name} ({account_type}){simulated}")
        
        print(f"\n📋 Summary:")
        print(f"  Total accounts: {len(accounts)}")
        print(f"  Unique exchanges: {len(exchanges)}")
        print(f"  Simulated accounts: {sum(1 for acc in accounts if acc.is_simulated)}")
        print(f"  Real accounts: {sum(1 for acc in accounts if not acc.is_simulated)}")
        
    except Exception as e:
        print(f"❌ Error getting accounts: {e}")

if __name__ == "__main__":
    main() 