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
    settings = Settings()
    sm = ServerManager(settings)
    
    # Ensure srv03 tunnel
    ok = await sm.ensure_srv03_tunnel()
    if not ok:
        print("❌ Tunnel to srv03 failed. Start the mandated SSH tunnel:")
        print("ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv03")
        return 1
    
    print("✅ SSH tunnel to srv03 is active")
    
    # Create config first
    from pyHaasAPI.config.api_config import APIConfig
    email = os.getenv('API_EMAIL')
    password = os.getenv('API_PASSWORD')
    
    if not email or not password:
        print("❌ Error: API_EMAIL and API_PASSWORD environment variables must be set")
        return 1
        
    config = APIConfig(
        email=email,
        password=password,
        host='127.0.0.1',
        port=8090
    )
    
    # Create client
    print("🌐 Creating client...")
    client = AsyncHaasClient(config)
    
    # Create authentication manager
    print("🔐 Authenticating...")
    auth_manager = AuthenticationManager(client, config)
    try:
        await auth_manager.authenticate()
        print("✅ Authentication successful")
        
        # Create API instances
        print("📡 Creating API instances...")
        lab_api = LabAPI(client, auth_manager)
        backtest_api = BacktestAPI(client, auth_manager)
        
        # Create backtest service
        print("⚙️ Creating backtest service...")
        backtest_service = BacktestService(lab_api, backtest_api)
        
        # Test lab ID - using a more realistic discovery or placeholder
        labs = await lab_api.get_labs()
        if not labs:
            print("⚠ No labs found to test with")
            await client.close()
            return 0
            
        lab_id = labs[0].lab_id
        print(f"🧪 Testing longest backtest on lab: {lab_id}")
        
        # Run comprehensive longest backtest
        results = await backtest_service.run_comprehensive_longest_backtest(
            lab_ids=[lab_id],
            max_iterations=1500,
            dry_run=True  # Use dry_run=True by default for safety in tests
        )
        
        print("\n📋 Results:")
        for lid, result in results.items():
            print(f"Lab {lid}:")
            print(f"  Status: {result.get('status', 'unknown')}")
            
        # Save results
        import json
        with open('longest_backtest_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to longest_backtest_results.json")
        
        await client.close()
        return 0
        
    except Exception as e:
        print(f"❌ Error during longest backtest: {e}")
        import traceback
        traceback.print_exc()
        if 'client' in locals():
            await client.close()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
