#!/usr/bin/env python3
"""
Setup script for Enhanced Authentication System
Helps configure and test the multi-credential authentication system for the MCP server
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_section(title):
    print(f"\n{'-' * 40}")
    print(f"  {title}")
    print(f"{'-' * 40}")

def check_current_credentials():
    """Check what credentials are currently available"""
    
    print_section("Current Environment Variables")
    
    # Load environment variables
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv()
        print("✅ Found .env file")
    else:
        print("⚠️ No .env file found")
    
    # Check for all possible credential sets
    credential_vars = [
        ("Primary", "API_EMAIL", "API_PASSWORD"),
        ("Local", "API_EMAIL_LOCAL", "API_PASSWORD_LOCAL"),
        ("Backup", "API_EMAIL_BACKUP", "API_PASSWORD_BACKUP"),
        ("Dev", "API_EMAIL_DEV", "API_PASSWORD_DEV")
    ]
    
    found_creds = []
    
    for name, email_var, pass_var in credential_vars:
        email = os.getenv(email_var)
        password = os.getenv(pass_var)
        
        if email and password:
            print(f"✅ {name}: {email_var}={email[:3]}***@***.*** (password set)")
            found_creds.append(name)
        elif email:
            print(f"⚠️ {name}: {email_var}={email} (password missing)")
        elif password:
            print(f"⚠️ {name}: Email missing (password set)")
        else:
            print(f"❌ {name}: Not configured")
    
    # Check server connection details
    print(f"\nServer Configuration:")
    api_host = os.getenv("API_HOST", "localhost")
    api_port = os.getenv("API_PORT", "8090")
    print(f"API_HOST: {api_host}")
    print(f"API_PORT: {api_port}")
    
    return found_creds

def setup_credentials_interactive():
    """Interactive credential setup"""
    
    print_section("Interactive Credential Setup")
    
    env_file = Path('.env')
    
    print("This will help you set up multiple credential sets for automatic authentication.")
    print("You can set up as many credential sets as you need for different servers/environments.")
    
    # Server configuration
    current_host = os.getenv("API_HOST", "localhost")
    current_port = os.getenv("API_PORT", "8090")
    
    print(f"\nCurrent server configuration:")
    print(f"Host: {current_host}")
    print(f"Port: {current_port}")
    
    update_server = input("\nUpdate server configuration? (y/N): ").strip().lower()
    
    if update_server in ['y', 'yes']:
        new_host = input(f"Enter API host [{current_host}]: ").strip() or current_host
        new_port = input(f"Enter API port [{current_port}]: ").strip() or current_port
        
        set_key(env_file, "API_HOST", new_host)
        set_key(env_file, "API_PORT", new_port)
        print(f"✅ Updated server configuration: {new_host}:{new_port}")
    
    # Credential sets setup
    credential_sets = [
        ("Primary", "API_EMAIL", "API_PASSWORD", "Main production credentials"),
        ("Local", "API_EMAIL_LOCAL", "API_PASSWORD_LOCAL", "Local development server credentials"),
        ("Backup", "API_EMAIL_BACKUP", "API_PASSWORD_BACKUP", "Backup/secondary credentials"),
        ("Dev", "API_EMAIL_DEV", "API_PASSWORD_DEV", "Development environment credentials")
    ]
    
    for name, email_var, pass_var, description in credential_sets:
        print(f"\n--- {name} Credentials ---")
        print(f"Description: {description}")
        
        current_email = os.getenv(email_var, "")
        current_pass = os.getenv(pass_var, "")
        
        if current_email:
            print(f"Current email: {current_email}")
            update = input("Update this credential set? (y/N): ").strip().lower()
            if update not in ['y', 'yes']:
                continue
        else:
            setup = input(f"Set up {name} credentials? (y/N): ").strip().lower()
            if setup not in ['y', 'yes']:
                continue
        
        email = input(f"Enter email for {name}: ").strip()
        if email:
            password = input(f"Enter password for {name}: ").strip()
            if password:
                set_key(env_file, email_var, email)
                set_key(env_file, pass_var, password)
                print(f"✅ Saved {name} credentials")
            else:
                print(f"❌ Skipped {name} (no password provided)")
        else:
            print(f"❌ Skipped {name} (no email provided)")

def test_authentication():
    """Test the authentication system"""
    
    print_section("Testing Authentication System")
    
    try:
        # Import the auth manager
        from mcp_server.auth_manager import get_auth_manager
        
        print("✅ Successfully imported auth manager")
        
        # Get the auth manager instance
        auth_manager = get_auth_manager()
        
        print(f"✅ Created auth manager with {len(auth_manager.credential_sets)} credential sets")
        
        # List available credential sets
        print("\nAvailable credential sets:")
        for i, cred_set in enumerate(auth_manager.credential_sets, 1):
            print(f"{i}. {cred_set.name}: {cred_set.email} ({cred_set.description})")
        
        if not auth_manager.credential_sets:
            print("❌ No credential sets available. Please set up credentials first.")
            return False
        
        # Test authentication
        print(f"\n🔄 Testing authentication...")
        auth_result = auth_manager.authenticate()
        
        if auth_result.success:
            print(f"✅ Authentication successful!")
            print(f"   Credential set: {auth_result.credential_set.name}")
            print(f"   Email: {auth_result.credential_set.email}")
            print(f"   Server: {auth_result.server_info.get('host')}:{auth_result.server_info.get('port')}")
            print(f"   Account: {auth_result.server_info.get('account_name', 'Unknown')}")
            return True
        else:
            print(f"❌ Authentication failed: {auth_result.error_message}")
            
            # Show detailed status
            status = auth_manager.get_authentication_status()
            print(f"\nDetailed status:")
            for cred_set in status['credential_sets']:
                print(f"  {cred_set['name']}: {cred_set['success_count']} successes, {cred_set['failure_count']} failures")
            
            return False
    
    except ImportError as e:
        print(f"❌ Failed to import auth manager: {e}")
        print("Make sure auth_manager.py is in the mcp_server directory")
        return False
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_mcp_server():
    """Test the MCP server with enhanced authentication"""
    
    print_section("Testing MCP Server Integration")
    
    try:
        # Import and test the MCP server
        sys.path.append('mcp_server')
        from server import HaasMCPServer
        
        print("✅ Successfully imported MCP server")
        
        # Create server instance (this will test authentication)
        print("🔄 Creating MCP server instance...")
        server = HaasMCPServer()
        
        if server.haas_executor:
            print("✅ MCP server initialized successfully with authentication")
            
            if hasattr(server, 'auth_manager'):
                status = server.auth_manager.get_authentication_status()
                current_session = status.get('current_session')
                if current_session:
                    print(f"   Active credential set: {current_session.get('credential_set')}")
                    print(f"   Server info: {current_session.get('server_info')}")
            
            return True
        else:
            print("❌ MCP server failed to authenticate")
            return False
    
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

def show_usage_examples():
    """Show usage examples"""
    
    print_section("Usage Examples")
    
    examples = """
1. Environment Variables Setup:
   Add these to your .env file:
   
   # Primary credentials
   API_EMAIL=your-email@domain.com
   API_PASSWORD=your-password
   
   # Local development credentials  
   API_EMAIL_LOCAL=local-email@domain.com
   API_PASSWORD_LOCAL=local-password
   
   # Server configuration
   API_HOST=localhost
   API_PORT=8090

2. Using the Auth Manager in Code:
   
   from mcp_server.auth_manager import get_auth_manager
   
   # Get authenticated executor
   auth_manager = get_auth_manager()
   result = auth_manager.authenticate()
   
   if result.success:
       executor = result.executor
       # Use executor for API calls
   
3. MCP Server Tools:
   
   The enhanced MCP server now includes:
   - get_auth_status: Get detailed authentication status
   - refresh_authentication: Force re-authentication
   - get_haas_status: Basic connection status
   
4. Authentication Flow:
   
   The system will automatically try credentials in this order:
   1. Most recently successful credentials
   2. Credentials with highest success rate
   3. Local credentials (if available)
   4. Primary credentials
   5. Any remaining credential sets
   
5. Caching:
   
   - Successful authentications are cached for 24 hours
   - Statistics are saved to .auth_cache.json
   - Failed attempts are tracked to optimize retry order
"""
    
    print(examples)

def main():
    """Main setup script"""
    
    print_header("Enhanced Authentication System Setup")
    print("This script helps you configure multi-credential authentication for the HaasOnline MCP server.")
    print("The system will automatically cycle through available credentials to find working ones.")
    
    while True:
        print(f"\n📋 Main Menu:")
        print("1. Check current credentials")
        print("2. Set up credentials interactively")
        print("3. Test basic authentication")
        print("4. Test enhanced authentication system")
        print("5. Test MCP server integration")
        print("6. Show usage examples")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == "1":
            creds = check_current_credentials()
            if creds:
                print(f"\n✅ Found {len(creds)} credential sets: {', '.join(creds)}")
            else:
                print(f"\n❌ No complete credential sets found")
        
        elif choice == "2":
            setup_credentials_interactive()
            print("\n✅ Credential setup completed")
        
        elif choice == "3":
            print("\n🔧 Running basic authentication test...")
            os.system("python test_enhanced_auth.py")
        
        elif choice == "4":
            success = test_authentication()
            if success:
                print("\n✅ Enhanced authentication system is working correctly")
            else:
                print("\n❌ Enhanced authentication system needs attention")
        
        elif choice == "5":
            success = test_mcp_server()
            if success:
                print("\n✅ MCP server integration is working correctly")
            else:
                print("\n❌ MCP server integration needs attention")
        
        elif choice == "6":
            show_usage_examples()
        
        elif choice == "7":
            print("\n👋 Setup complete. Your enhanced authentication system is ready!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-7.")

if __name__ == "__main__":
    main()