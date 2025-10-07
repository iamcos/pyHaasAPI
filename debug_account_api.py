#!/usr/bin/env python3
"""
Debug script to isolate AccountAPI error
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.account.account_api import AccountAPI

async def debug_account_api():
    """Debug AccountAPI get_account_data method."""
    print("🔍 Debugging AccountAPI get_account_data method...")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD'),
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    try:
        # Connect and authenticate
        await client.connect()
        session = await auth_manager.authenticate()
        print(f"✅ Authenticated: {session.user_id}")
        
        # Create AccountAPI
        account_api = AccountAPI(client, auth_manager)
        
        # Test get_accounts first
        print("💰 Testing get_accounts()...")
        accounts = await account_api.get_accounts()
        print(f"✅ Got {len(accounts)} accounts from server")
        
        if accounts:
            # Test get_account_data with first account
            first_account = accounts[0]
            print(f"🔍 Testing get_account_data() with account: {first_account.account_id}")
            print(f"🔍 Account object type: {type(first_account)}")
            print(f"🔍 Account object attributes: {dir(first_account)}")
            
            try:
                account_data = await account_api.get_account_data(first_account.account_id)
                print(f"✅ Account data retrieved successfully")
                print(f"🔍 Account data type: {type(account_data)}")
                print(f"🔍 Account data attributes: {dir(account_data)}")
                
                # Try to access exchange field
                try:
                    exchange = account_data.exchange
                    print(f"✅ Exchange: {exchange}")
                except Exception as e:
                    print(f"❌ Error accessing exchange field: {e}")
                    print(f"🔍 Account data content: {account_data}")
                
            except Exception as e:
                print(f"❌ Error in get_account_data: {e}")
                print(f"🔍 Exception type: {type(e)}")
                print(f"🔍 Exception args: {e.args}")
                import traceback
                traceback.print_exc()
            
            return True
        else:
            print("⚠️ No accounts found to test with")
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()

async def main():
    """Main debug function."""
    print("🚀 Starting AccountAPI debug...")
    
    success = await debug_account_api()
    
    if success:
        print("🎉 Debug completed!")
    else:
        print("💥 Debug failed!")

if __name__ == "__main__":
    asyncio.run(main())
