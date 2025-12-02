#!/usr/bin/env python3
"""
Test script for lab API functionality
Tests lab listing, details, and status with local server
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.exceptions import LabError, AuthenticationError

async def test_lab_listing():
    """Test lab listing functionality"""
    print("🧪 Testing Lab API with Local Server")
    print("=" * 60)
    
    # Get credentials from environment
    email = os.getenv('API_EMAIL_LOCAL') or os.getenv('API_EMAIL')
    password = os.getenv('API_PASSWORD_LOCAL') or os.getenv('API_PASSWORD')
    
    if not email or not password:
        print("❌ Error: API_EMAIL and API_PASSWORD must be set")
        return False
    
    print(f"📧 Using email: {email}")
    print(f"🌐 Connecting to: 127.0.0.1:8090")
    print()
    
    try:
        # Create config for local server
        config = APIConfig(
            email=email,
            password=password,
            host="127.0.0.1",
            port=8090,
            timeout=30.0
        )
        
        # Create client and auth manager
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        # Authenticate
        print("🔐 Authenticating...")
        session = await auth_manager.authenticate()
        print(f"✅ Authentication successful! User ID: {session.user_id}")
        print()
        
        # Create lab API
        lab_api = LabAPI(client, auth_manager)
        
        # Test 1: List all labs
        print("📋 Test 1: Listing all labs...")
        labs = await lab_api.get_labs()
        print(f"✅ Found {len(labs)} lab(s)")
        print()
        
        if not labs:
            print("⚠️  No labs found on server")
            print("   This is expected if the server has no labs created yet")
            return True
        
        # Display labs
        print("📊 Available Labs:")
        print("-" * 60)
        for i, lab in enumerate(labs, 1):
            print(f"{i}. {lab.name} (ID: {lab.lab_id[:8]}...)")
            print(f"   Script: {lab.script_id}")
            print(f"   Status: {lab.status}")
            print(f"   Created: {lab.created_at}")
            print()
        
        # Test 2: Get details for first lab
        if labs:
            first_lab = labs[0]
            print(f"🔍 Test 2: Getting details for lab '{first_lab.name}'...")
            try:
                lab_details = await lab_api.get_lab_details(first_lab.lab_id)
                print(f"✅ Lab details retrieved!")
                market_tag = getattr(lab_details.settings, 'market_tag', None) or getattr(lab_details.settings, 'marketTag', 'N/A') if hasattr(lab_details, 'settings') else 'N/A'
                account_id = getattr(lab_details.settings, 'account_id', None) or getattr(lab_details.settings, 'accountId', 'N/A') if hasattr(lab_details, 'settings') else 'N/A'
                print(f"   Market: {market_tag}")
                print(f"   Account: {account_id}")
                print(f"   Script: {lab_details.script_id}")
                print(f"   Status: {lab_details.status}")
                if hasattr(lab_details, 'config'):
                    print(f"   Max Generations: {lab_details.config.max_generations}")
                print()
            except Exception as e:
                print(f"⚠️  Could not get lab details: {e}")
                print()
        
        # Test 3: Get backtests for first lab
        if labs:
            first_lab = labs[0]
            print(f"📊 Test 3: Getting backtests for lab '{first_lab.name}'...")
            try:
                from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
                backtest_api = BacktestAPI(client, auth_manager)
                
                # Get first page of backtests
                backtest_response = await backtest_api.get_backtest_result(
                    first_lab.lab_id, 
                    next_page_id=0, 
                    page_length=10
                )
                print(f"✅ Backtest retrieval successful!")
                print(f"   Total items in page: {len(backtest_response.items)}")
                print(f"   Has next page: {backtest_response.has_next}")
                if backtest_response.items:
                    print(f"   First backtest ID: {backtest_response.items[0].backtest_id}")
                    print(f"   First backtest generation: {backtest_response.items[0].generation_idx}")
                print()
            except Exception as e:
                print(f"⚠️  Could not get backtests: {e}")
                print()
        
        # Test 4: Get lab status (if lab was executed)
        if labs:
            first_lab = labs[0]
            print(f"📊 Test 4: Getting execution status for lab '{first_lab.name}'...")
            try:
                status = await lab_api.get_lab_execution_status(first_lab.lab_id)
                print(f"✅ Lab status retrieved!")
                print(f"   Status: {status.status}")
                print(f"   Progress: {status.progress}%")
                print(f"   Iterations: {status.current_iteration}/{status.max_iterations}")
                print()
            except Exception as e:
                print(f"ℹ️  Lab execution status: {e}")
                print(f"   (This is normal if the lab hasn't been executed yet)")
                print()
        
        # Close client
        await client.close()
        
        print("✅ All tests completed!")
        return True
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except LabError as e:
        print(f"❌ Lab API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(test_lab_listing())
    sys.exit(0 if success else 1)

