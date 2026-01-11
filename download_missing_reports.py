import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.backtest import BacktestAPI
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig

# Load environment variables
load_dotenv()

async def download_missing_for_server(server_name: str, missing_data: list):
    if not missing_data:
        print(f"✅ No missing data for {server_name}")
        return

    print(f"🌐 Connecting to {server_name} to download {len(missing_data)} labs...")
    
    settings = Settings()
    sm = ServerManager(settings)
    
    try:
        if not await sm.connect_server(server_name):
            print(f"❌ Failed to connect to {server_name}")
            return
            
        config = APIConfig(host='127.0.0.1', port=8090)
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        await auth_manager.authenticate(email, password)
        
        backtest_api = BacktestAPI(client, auth_manager)
        
        for lab in missing_data:
            lab_id = lab['lab_id']
            missing_ids = lab['missing_ids']
            print(f"📥 Lab {lab['lab_name']} ({lab_id[:8]}): Downloading {len(missing_ids)} reports...")
            
            # Ensure directory exists
            dest_dir = Path(f"unified_cache/runtime_reports/{server_name}/{lab_id}")
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            for i, bt_id in enumerate(missing_ids, 1):
                dest_file = dest_dir / f"{bt_id}_runtime.json"
                if dest_file.exists():
                    continue
                    
                try:
                    # Use our fixed API method if we want structured data, 
                    # but the requirement says "ALWAYS save runtime data" (the raw JSON)
                    # So let's use get_backtest_runtime directly to get the raw dict
                    runtime_data = await backtest_api.get_backtest_runtime(lab_id, bt_id)
                    
                    with open(dest_file, "w") as f:
                        json.dump(runtime_data, f, indent=2)
                        
                    if i % 10 == 0:
                        print(f"   ✅ Progress: {i}/{len(missing_ids)}")
                        
                except Exception as e:
                    print(f"   ❌ Error downloading {bt_id[:8]}: {e}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.2)
                
    finally:
        await sm.disconnect_server(server_name)

async def main(target_server: str = None):
    servers = [target_server] if target_server else ["srv01", "srv02", "srv03"]
    for server in servers:
        report_file = f"verification_report_{server}.json"
        if not os.path.exists(report_file):
            continue
            
        with open(report_file, "r") as f:
            data = json.load(f)
            
        missing_data = [lab for lab in data if lab.get("missing_count", 0) > 0]
        await download_missing_for_server(server, missing_data)

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(target))
