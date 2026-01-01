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
    """Lab listing utility for HaasOnline servers."""
    
    def __init__(self):
        # Default to srv03 as it is the most reliable in this environment
        self.default_server = "srv03"
        self.host = "127.0.0.1"
        self.port = 8090
        
    async def list_labs(self) -> Dict[str, Any]:
        """List all labs and their details."""
        print(f"🚀 pyHaasAPI v2 - List All Labs")
        print("=" * 60)
        
        # Load environment variables
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("❌ Error: API_EMAIL and API_PASSWORD environment variables must be set")
            return {"error": "Missing credentials"}
        
        try:
            # Create configuration
            config = APIConfig(
                email=email,
                password=password,
                host=self.host,
                port=self.port,
                timeout=30.0
            )
            
            # Create client and auth manager
            client = AsyncHaasClient(config)
            auth_manager = AuthenticationManager(client, config)
            
            # Authenticate
            print(f"🔗 Connecting to Haas API at {self.host}:{self.port}...")
            await auth_manager.authenticate()
            print(f"✅ Authentication successful")
            
            # Create lab API
            lab_api = LabAPI(client, auth_manager)
            
            # Get all labs
            print(f"📋 Fetching labs...")
            labs = await lab_api.get_labs()
            print(f"✅ Found {len(labs)} labs")
            
            detailed_labs = []
            for lab in labs:
                try:
                    # lab here is a LabRecord, it has .name, .lab_id, etc. (mapped from N, LID)
                    print(f"   🔍 Getting details for: {lab.name} ({lab.lab_id[:8]})")
                    details = await lab_api.get_lab_details(lab.lab_id)
                    detailed_labs.append(details)
                except Exception as e:
                    print(f"   ⚠️  Could not get details for {lab.lab_id}: {e}")
                    detailed_labs.append(lab)
            
            # Display summary
            print("\n" + "=" * 60)
            print(f"🧪 LAB DETAILS ({len(detailed_labs)} labs)")
            print("=" * 60)
            
            for i, lab in enumerate(detailed_labs, 1):
                status_emoji = "🟢" if getattr(lab, 'status', '') == "ACTIVE" else "🟡"
                print(f"{i:2d}. {status_emoji} {lab.name}")
                print(f"      ID: {lab.lab_id}")
                print(f"      Script: {getattr(lab, 'script_name', 'Unknown')}")
                
                if hasattr(lab, 'settings'):
                    print(f"      Market: {lab.settings.market_tag}")
                    print(f"      Trade Amount: {lab.settings.trade_amount}")
                elif hasattr(lab, 'market_tag'): # Fallback for LabRecord
                    print(f"      Market: {lab.market_tag}")
                
                if hasattr(lab, 'backtest_count'):
                    print(f"      Backtests: {lab.backtest_count}")
                elif hasattr(lab, 'completed_backtests'):
                    print(f"      Backtests: {lab.completed_backtests}")
                print()
            
            await client.close()
            return {"success": True, "count": len(detailed_labs)}
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if 'client' in locals():
                await client.close()
            return {"success": False, "error": str(e)}

async def main():
    """Main function to run the lab listing example."""
    lister = LabLister()
    result = await lister.list_labs()
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    # Run the example
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
