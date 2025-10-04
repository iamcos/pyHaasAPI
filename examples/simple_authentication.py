#!/usr/bin/env python3
"""
Example: Simple Authentication Test

This example demonstrates the basic authentication flow of pyHaasAPI v2:
1. Connect to a HaasOnline server
2. Authenticate with email/password
3. Display authentication success information
4. Handle authentication errors gracefully

Usage:
    python examples/simple_authentication.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.exceptions import AuthenticationError, NetworkError


async def test_authentication():
    """Test authentication with a single server."""
    print("🚀 pyHaasAPI v2 - Simple Authentication Test")
    print("=" * 50)
    
    # Load environment variables
    email = os.getenv('API_EMAIL')
    password = os.getenv('API_PASSWORD')
    
    if not email or not password:
        print("❌ Error: API_EMAIL and API_PASSWORD environment variables must be set")
        print("   Please create a .env file with your credentials:")
        print("   API_EMAIL=your_email@example.com")
        print("   API_PASSWORD=your_password")
        return False
    
    # Server configuration (using srv03 as default)
    server_config = {
        "host": "127.0.0.1",
        "port": 8092,  # srv03 port
        "timeout": 30.0
    }
    
    print(f"🔗 Connecting to server: {server_config['host']}:{server_config['port']}")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {'*' * len(password)}")
    
    try:
        # Create configuration
        config = APIConfig(
            email=email,
            password=password,
            host=server_config["host"],
            port=server_config["port"],
            timeout=server_config["timeout"]
        )
        
        # Create client and auth manager
        print("\n🏗️  Creating client and authentication manager...")
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        # Authenticate
        print("🔐 Starting authentication process...")
        print("   Step 1: Sending email/password...")
        
        session = await auth_manager.authenticate()
        
        print("   ✅ Authentication successful!")
        print(f"   👤 User ID: {session.user_id}")
        print(f"   🔑 Session Key: {session.session_key[:20]}...")
        print(f"   🕒 Authenticated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test session validity
        print("\n🧪 Testing session validity...")
        is_authenticated = await auth_manager.is_authenticated()
        print(f"   Session valid: {'✅ Yes' if is_authenticated else '❌ No'}")
        
        return True
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Possible causes:")
        print("   • Invalid email or password")
        print("   • Account not found")
        print("   • Server authentication service unavailable")
        return False
        
    except NetworkError as e:
        print(f"❌ Network error: {e}")
        print("   Possible causes:")
        print("   • Server not running")
        print("   • SSH tunnel not established")
        print("   • Firewall blocking connection")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   This might be a server-side issue or API change")
        return False


async def main():
    """Main function to run the authentication test."""
    try:
        success = await test_authentication()
        
        if success:
            print("\n✅ Authentication test completed successfully!")
            print("   pyHaasAPI v2 authentication is working correctly.")
            return 0
        else:
            print("\n❌ Authentication test failed!")
            print("   Please check your credentials and server connection.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with unexpected error: {e}")
        return 1


if __name__ == "__main__":
    # Run the example
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
