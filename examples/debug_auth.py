#!/usr/bin/env python3
"""
Debug authentication script
Tests connection and authentication step by step
"""

import os
from dotenv import load_dotenv
load_dotenv()

from pyHaasAPI import api
from config import settings

def debug_connection():
    """Debug connection step by step"""
    print("🔍 Debugging HaasOnline API Connection")
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
        
        # Step 2: Test basic connection
        print("\n📋 Step 2: Testing basic connection...")
        import requests
        url = f"http://{settings.API_HOST}:{settings.API_PORT}/UserAPI.php"
        response = requests.get(url, timeout=5)
        print(f"✅ Server response: {response.status_code}")
        
        # Step 3: Try authentication
        print("\n📋 Step 3: Attempting authentication...")
        try:
            auth_executor = executor.authenticate(
                email=settings.API_EMAIL,
                password=settings.API_PASSWORD
            )
            print("✅ Authentication successful!")
            return auth_executor
        except Exception as auth_error:
            print(f"❌ Authentication failed: {auth_error}")
            print(f"Error type: {type(auth_error)}")
            
            # Try to get more details about the error
            if hasattr(auth_error, '__dict__'):
                print(f"Error details: {auth_error.__dict__}")
            
            return None
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def test_simple_api_call(executor):
    """Test a simple API call if authentication works"""
    if not executor:
        print("❌ No authenticated executor available")
        return
    
    print("\n📋 Testing simple API call...")
    try:
        # Try to get accounts
        accounts = api.get_accounts(executor)
        print(f"✅ Successfully retrieved {len(accounts)} accounts")
        for acc in accounts:
            print(f"  - {acc.name} ({acc.exchange_code})")
    except Exception as e:
        print(f"❌ API call failed: {e}")

def main():
    """Main debug function"""
    executor = debug_connection()
    test_simple_api_call(executor)

if __name__ == "__main__":
    main() 