#!/usr/bin/env python3
"""
Manual authentication test script
Allows manual input of one-time code for HaasOnline API authentication
"""

import os
from dotenv import load_dotenv
load_dotenv()

from pyHaasAPI import api
from config import settings

def manual_authenticate():
    """Manual authentication with user input for one-time code"""
    print("🔐 Manual HaasOnline API Authentication")
    print("=" * 50)
    
    print(f"Host: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
    print(f"Email: {settings.API_EMAIL}")
    print(f"Password: {'*' * len(settings.API_PASSWORD)}")
    
    try:
        # Step 1: Create guest executor
        print("\n📋 Step 1: Creating guest executor...")
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        )
        print("✅ Guest executor created")
        
        # Step 2: First authentication step (credentials)
        print("\n📋 Step 2: Authenticating with credentials...")
        import requests
        import random
        
        interface_key = "".join(f"{random.randint(0, 100)}" for _ in range(10))
        url = f"http://{settings.API_HOST}:{settings.API_PORT}/UserAPI.php"
        
        params = {
            "channel": "LOGIN_WITH_CREDENTIALS",
            "email": settings.API_EMAIL,
            "password": settings.API_PASSWORD,
            "interfaceKey": interface_key,
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if not data.get("Success", False):
            print(f"❌ Credential authentication failed: {data.get('Error', 'Unknown error')}")
            return None
        
        print("✅ Credential authentication successful!")
        print(f"Interface Key: {interface_key}")
        
        # Step 3: Manual one-time code input
        print("\n📋 Step 3: One-time code authentication...")
        print("Please check your email or authenticator app for the one-time code.")
        pincode = input("Enter the one-time code: ").strip()
        
        if not pincode:
            print("❌ No pincode provided")
            return None
        
        # Step 4: Second authentication step (one-time code)
        params = {
            "channel": "LOGIN_WITH_ONE_TIME_CODE",
            "email": settings.API_EMAIL,
            "pincode": pincode,
            "interfaceKey": interface_key,
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if not data.get("Success", False):
            print(f"❌ One-time code authentication failed: {data.get('Error', 'Unknown error')}")
            return None
        
        print("✅ One-time code authentication successful!")
        
        # Extract user data
        user_data = data.get("Data", {})
        if isinstance(user_data, dict) and "data" in user_data:
            user_data = user_data["data"]
        
        user_id = user_data.get("user_id", "")
        print(f"User ID: {user_id}")
        
        # Create authenticated state
        from pyHaasAPI.api import Authenticated
        state = Authenticated(user_id=user_id, interface_key=interface_key)
        
        # Create authenticated executor
        auth_executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=state
        )
        
        print("✅ Fully authenticated!")
        return auth_executor
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def test_api_calls(executor):
    """Test various API calls with authenticated executor"""
    if not executor:
        print("❌ No authenticated executor available")
        return
    
    print("\n🧪 Testing API calls...")
    
    try:
        # Test 1: Get accounts
        print("\n📋 Test 1: Getting accounts...")
        accounts = api.get_accounts(executor)
        print(f"✅ Successfully retrieved {len(accounts)} accounts")
        for acc in accounts:
            print(f"  - {acc.name} ({acc.exchange_code}, Simulated: {acc.is_simulated})")
        
        # Test 2: Get scripts
        print("\n📋 Test 2: Getting scripts...")
        scripts = api.get_all_scripts(executor)
        print(f"✅ Successfully retrieved {len(scripts)} scripts")
        for script in scripts[:5]:  # Show first 5
            print(f"  - {script.script_name} (ID: {script.script_id})")
        
        # Test 3: Get markets
        print("\n📋 Test 3: Getting markets...")
        markets = api.get_all_markets(executor)
        print(f"✅ Successfully retrieved {len(markets)} markets")
        for market in markets[:5]:  # Show first 5
            print(f"  - {market.primary}/{market.secondary} ({market.price_source})")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def main():
    """Main function"""
    executor = manual_authenticate()
    if executor:
        test_api_calls(executor)
    else:
        print("\n❌ Authentication failed. Cannot proceed with API tests.")

if __name__ == "__main__":
    main() 