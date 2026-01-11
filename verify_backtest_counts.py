import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab import LabAPI
from pyHaasAPI.api.backtest import BacktestAPI
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig

# Load environment variables from .env file
load_dotenv()

async def verify_server(server_name: str):
    print(f"🌐 Probing {server_name}...")
    
    settings = Settings()
    sm = ServerManager(settings)
    
    try:
        # Connect to server
        if not await sm.connect_server(server_name):
            print(f"❌ Failed to connect to {server_name}")
            return
            
        print(f"✅ Connected to {server_name}")
        
        # Setup client
        config = APIConfig(host='127.0.0.1', port=8090)
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        # Authenticate
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        if not email or not password:
            print("❌ API_EMAIL or API_PASSWORD not set")
            return
            
        print(f"🔐 Authenticating...")
        await auth_manager.authenticate(email, password)
        print(f"✅ Authenticated")
        
        # API instances
        lab_api = LabAPI(client, auth_manager)
        backtest_api = BacktestAPI(client, auth_manager)
        
        # Get labs
        print(f"📋 Fetching labs...")
        labs = await lab_api.get_labs()
        print(f"✅ Found {len(labs)} labs")
        
        report = []
        
        for lab in labs:
            lab_id = lab.lab_id
            lab_name = lab.name
            
            print(f"🔍 Checking lab {lab_name} ({lab_id[:8]})...")
            
            try:
                # Fetch all backtest summaries (just the IDs) to see total count
                # This uses get_all_backtests_for_lab which fetches pages of 100
                server_backtests = await backtest_api.get_all_backtests_for_lab(lab_id, max_pages=10) # 1000 max
                server_count = len(server_backtests)
                
                # Check cache
                cache_dir = Path(f"unified_cache/runtime_reports/{server_name}/{lab_id}")
                cached_files = list(cache_dir.glob("*_runtime.json")) if cache_dir.exists() else []
                cached_count = len(cached_files)
                
                # Check for missing reports
                cached_ids = {f.name.split('_')[0] for f in cached_files}
                server_ids = {bt.backtest_id for bt in server_backtests}
                missing_ids = list(server_ids - cached_ids)
                
                report.append({
                    "lab_id": lab_id,
                    "lab_name": lab_name,
                    "server_count": server_count,
                    "cached_count": cached_count,
                    "missing_count": len(missing_ids),
                    "missing_ids": missing_ids
                })
                
                if len(missing_ids) > 0:
                    print(f"   ⚠️ MISSING: {len(missing_ids)}/{server_count} (Cached: {cached_count})")
                else:
                    print(f"   ✅ Complete: {server_count}/{server_count} cached")
                
            except Exception as e:
                print(f"   ❌ Error checking lab: {e}")
        
        # Save report
        with open(f"verification_report_{server_name}.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report saved to verification_report_{server_name}.json")
            
    finally:
        await sm.disconnect_server(server_name)

if __name__ == "__main__":
    import sys
    server = sys.argv[1] if len(sys.argv) > 1 else "srv01"
    asyncio.run(verify_server(server))
