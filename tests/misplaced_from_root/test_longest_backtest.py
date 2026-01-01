#!/usr/bin/env python3
"""
Direct test of longest backtest functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.services.backtest.backtest_service import BacktestService
from dotenv import load_dotenv

load_dotenv()

async def main():
    """Test longest backtest on specific lab"""
    
    # Preflight check
    print("🔍 Checking SSH tunnel...")
    sm = ServerManager(Settings())
    ok = await sm.preflight_check()
    if not ok:
        print("❌ Tunnel preflight failed. Start the mandated SSH tunnel:")
        print("ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv02")
        return 1
    
    print("✅ SSH tunnel is active")
    
    # Create config first
    from pyHaasAPI.config.api_config import APIConfig
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD')
    )
    
    # Create client
    print("🌐 Creating client...")
    client = AsyncHaasClient(config)
    
    # Create authentication manager
    print("🔐 Authenticating...")
    auth_manager = AuthenticationManager(client, config)
    await auth_manager.authenticate()
    print("✅ Authentication successful")
    
    # Create API instances
    print("📡 Creating API instances...")
    lab_api = LabAPI(client, auth_manager)
    backtest_api = BacktestAPI(client, auth_manager)
    
    # Create backtest service
    print("⚙️ Creating backtest service...")
    backtest_service = BacktestService(lab_api, backtest_api)
    
    # Test lab ID
    lab_id = "46fd2d6e-dd2e-4aba-bd78-870fc9a6527a"
    print(f"🧪 Testing longest backtest on lab: {lab_id}")
    
    try:
        # Run comprehensive longest backtest
        results = await backtest_service.run_comprehensive_longest_backtest(
            lab_ids=[lab_id],
            max_iterations=1500,
            dry_run=False
        )
        
        print("\n📋 Results:")
        for lab_id, result in results.items():
            print(f"Lab {lab_id}:")
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Running Found: {result.get('running_found', False)}")
            print(f"  Approx Start: {result.get('approx_start_date', 'N/A')}")
            print(f"  End Date: {result.get('end_date', 'N/A')}")
            print(f"  Attempts: {len(result.get('attempts', []))}")
            print(f"  Notes: {result.get('notes', 'None')}")
            
            if 'error' in result:
                print(f"  Error: {result['error']}")
        
        # Save results
        import json
        with open('longest_backtest_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to longest_backtest_results.json")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during longest backtest: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
