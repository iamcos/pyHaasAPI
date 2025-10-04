#!/usr/bin/env python3
"""
Example: List All Labs Across Available Servers

This example demonstrates how to use pyHaasAPI v2 to:
1. Connect to multiple HaasOnline servers
2. List all labs from each server
3. Display lab information with backtest counts and performance metrics
4. Handle authentication and connection errors gracefully

Usage:
    python examples/list_all_labs.py
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.exceptions import LabError, AuthenticationError, NetworkError


class LabLister:
    """Lab listing utility for multiple servers."""
    
    def __init__(self):
        self.servers = {
            "srv01": {"host": "127.0.0.1", "port": 8090},
            "srv02": {"host": "127.0.0.1", "port": 8091}, 
            "srv03": {"host": "127.0.0.1", "port": 8092}
        }
        self.results = {}
    
    async def list_labs_for_server(self, server_name: str, config: APIConfig) -> Dict[str, Any]:
        """List all labs for a specific server."""
        print(f"\n🔍 Connecting to {server_name}...")
        
        try:
            # Create client and auth manager
            client = AsyncHaasClient(config)
            auth_manager = AuthenticationManager(client, config)
            
            # Authenticate
            print(f"   Authenticating with {server_name}...")
            session = await auth_manager.authenticate()
            print(f"   ✅ Authentication successful: {session.user_id}")
            
            # Create lab API
            lab_api = LabAPI(client, auth_manager)
            
            # Get all labs
            print(f"   📋 Fetching labs from {server_name}...")
            labs = await lab_api.get_labs()
            
            print(f"   ✅ Found {len(labs)} labs on {server_name}")
            
            # Get detailed information for each lab
            lab_details = []
            for lab in labs:
                try:
                    details = await lab_api.get_lab_details(lab.lab_id)
                    lab_details.append(details)
                except Exception as e:
                    print(f"   ⚠️  Could not get details for lab {lab.lab_id}: {e}")
                    lab_details.append(lab)  # Use basic lab record
            
            return {
                "server": server_name,
                "success": True,
                "lab_count": len(labs),
                "labs": lab_details,
                "user_id": session.user_id
            }
            
        except AuthenticationError as e:
            print(f"   ❌ Authentication failed for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Authentication failed: {e}",
                "lab_count": 0,
                "labs": []
            }
        except NetworkError as e:
            print(f"   ❌ Network error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Network error: {e}",
                "lab_count": 0,
                "labs": []
            }
        except LabError as e:
            print(f"   ❌ Lab API error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Lab API error: {e}",
                "lab_count": 0,
                "labs": []
            }
        except Exception as e:
            print(f"   ❌ Unexpected error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Unexpected error: {e}",
                "lab_count": 0,
                "labs": []
            }
    
    def format_lab_info(self, lab) -> str:
        """Format lab information for display."""
        info_lines = []
        
        # Basic info
        info_lines.append(f"      Name: {lab.name}")
        info_lines.append(f"      ID: {lab.lab_id}")
        info_lines.append(f"      Script: {lab.script_name}")
        info_lines.append(f"      Market: {lab.market_tag}")
        
        # Status info
        if hasattr(lab, 'status'):
            status_emoji = "🟢" if lab.status == "ACTIVE" else "🔴" if lab.status == "INACTIVE" else "🟡"
            info_lines.append(f"      Status: {status_emoji} {lab.status}")
        
        # Configuration info
        if hasattr(lab, 'config') and lab.config:
            info_lines.append(f"      Max Generations: {lab.config.max_generations}")
            info_lines.append(f"      Max Parallel: {lab.config.max_parallel}")
        
        # Creation date
        if hasattr(lab, 'created_at') and lab.created_at:
            info_lines.append(f"      Created: {lab.created_at}")
        
        return "\n".join(info_lines)
    
    async def list_all_labs(self) -> Dict[str, Any]:
        """List all labs across all available servers."""
        print("🚀 pyHaasAPI v2 - List All Labs Example")
        print("=" * 50)
        
        # Load environment variables
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("❌ Error: API_EMAIL and API_PASSWORD environment variables must be set")
            print("   Please create a .env file with your credentials:")
            print("   API_EMAIL=your_email@example.com")
            print("   API_PASSWORD=your_password")
            return {"error": "Missing credentials"}
        
        results = {}
        total_labs = 0
        
        # Try each server
        for server_name, server_config in self.servers.items():
            config = APIConfig(
                email=email,
                password=password,
                host=server_config["host"],
                port=server_config["port"],
                timeout=30.0
            )
            
            result = await self.list_labs_for_server(server_name, config)
            results[server_name] = result
            
            if result["success"]:
                total_labs += result["lab_count"]
        
        # Display summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        
        successful_servers = 0
        for server_name, result in results.items():
            if result["success"]:
                successful_servers += 1
                print(f"✅ {server_name}: {result['lab_count']} labs (User: {result.get('user_id', 'Unknown')})")
            else:
                print(f"❌ {server_name}: Failed - {result['error']}")
        
        print(f"\n🎯 Total: {successful_servers}/{len(self.servers)} servers connected")
        print(f"🧪 Total labs found: {total_labs}")
        
        # Display detailed lab information
        if total_labs > 0:
            print("\n" + "=" * 50)
            print("🧪 LAB DETAILS")
            print("=" * 50)
            
            for server_name, result in results.items():
                if result["success"] and result["labs"]:
                    print(f"\n📡 {server_name.upper()} ({result['lab_count']} labs):")
                    print("-" * 30)
                    
                    for i, lab in enumerate(result["labs"], 1):
                        print(f"  {i:2d}. 🧪 {lab.name}")
                        print(self.format_lab_info(lab))
                        print()
        
        return {
            "total_servers": len(self.servers),
            "successful_servers": successful_servers,
            "total_labs": total_labs,
            "results": results
        }


async def main():
    """Main function to run the lab listing example."""
    lister = LabLister()
    
    try:
        results = await lister.list_all_labs()
        
        if "error" in results:
            print(f"\n❌ Example failed: {results['error']}")
            return 1
        
        print(f"\n✅ Example completed successfully!")
        print(f"   Connected to {results['successful_servers']}/{results['total_servers']} servers")
        print(f"   Found {results['total_labs']} total labs")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Example interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Example failed with unexpected error: {e}")
        return 1


if __name__ == "__main__":
    # Run the example
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
