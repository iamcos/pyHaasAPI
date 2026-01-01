#!/usr/bin/env python3
"""
Analyze all labs on srv03 and identify labs not in cache for bot creation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def analyze_labs():
    """Analyze all labs and identify uncached labs"""
    try:
        from pyHaasAPI.core.client import AsyncHaasClient
        from pyHaasAPI.core.auth import AuthenticationManager
        from pyHaasAPI.api.lab import LabAPI
        from pyHaasAPI.config.api_config import APIConfig
        from pyHaasAPI.config.logging_config import LoggingConfig
        from pyHaasAPI.core.server_manager import ServerManager
        from pyHaasAPI.config.settings import Settings
        
        # Set credentials from environment
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("❌ Error: API_EMAIL and API_PASSWORD environment variables are required")
            return
        
        # Ensure tunnel
        sm = ServerManager(Settings())
        if not await sm.ensure_srv03_tunnel():
            print("❌ Failed to establish tunnel to srv03")
            return
            
        # Create config
        logging_config = LoggingConfig()
        config = APIConfig(host='127.0.0.1', port=8090, logging=logging_config)
        
        # Create client and auth
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        print("🔐 Authenticating with srv03...")
        
        # Authenticate
        await auth_manager.authenticate(email, password)
        print("✅ Authentication successful")
        
        # Get labs
        lab_api = LabAPI(client, auth_manager)
        print("📋 Fetching all labs...")
        
        labs = await lab_api.get_labs()
        print(f"✅ Found {len(labs)} labs")
        
        print("\n" + "="*80)
        print("📊 LAB ANALYSIS REPORT - SRV03")
        print("="*80)
        
        # Analyze each lab
        uncached_labs = []
        cached_labs = []
        
        for i, lab in enumerate(labs, 1):
            lab_id = lab.lab_id
            lab_name = lab.name
            market_tag = lab.settings.market_tag if hasattr(lab, 'settings') else "Unknown"
            status = getattr(lab, 'status', 'Unknown')
            
            print(f"\n{i:2d}. Lab ID: {lab_id}")
            print(f"    Name: {lab_name}")
            print(f"    Market: {market_tag}")
            print(f"    Status: {status}")
            
            # Check if lab has backtests (indicating it's cached)
            try:
                # Try to get lab details to check for backtests
                lab_details = await lab_api.get_lab_details(lab_id)
                if lab_details:
                    # Check if lab has backtest data
                    # In v2 models, LabDetails might have backtest_count or similar
                    has_backtests = getattr(lab_details, 'backtest_count', 0) > 0
                    if has_backtests:
                        cached_labs.append({
                            'id': lab_id,
                            'name': lab_name,
                            'market': market_tag,
                            'status': status
                        })
                        print(f"    📊 Status: CACHED ({lab_details.backtest_count} backtests)")
                    else:
                        uncached_labs.append({
                            'id': lab_id,
                            'name': lab_name,
                            'market': market_tag,
                            'status': status
                        })
                        print(f"    📊 Status: NOT CACHED (no backtests)")
                else:
                    uncached_labs.append({
                        'id': lab_id,
                        'name': lab_name,
                        'market': market_tag,
                        'status': status
                    })
                    print(f"    📊 Status: NOT CACHED (no details)")
                    
            except Exception as e:
                uncached_labs.append({
                    'id': lab_id,
                    'name': lab_name,
                    'market': market_tag,
                    'status': status
                })
                print(f"    📊 Status: NOT CACHED (error: {e})")
        
        # Summary
        print("\n" + "="*80)
        print("📈 ANALYSIS SUMMARY")
        print("="*80)
        print(f"📊 Total Labs: {len(labs)}")
        print(f"✅ Cached Labs: {len(cached_labs)}")
        print(f"❌ Uncached Labs: {len(uncached_labs)}")
        
        if uncached_labs:
            print(f"\n🎯 LABS NOT IN CACHE (Ready for Bot Creation):")
            print("-" * 50)
            for lab in uncached_labs:
                print(f"  • {lab['id']} - {lab['name']} ({lab['market']})")
        
        if cached_labs:
            print(f"\n📊 CACHED LABS (Already Analyzed):")
            print("-" * 50)
            for lab in cached_labs:
                print(f"  • {lab['id']} - {lab['name']} ({lab['market']})")
        
        print(f"\n🎯 RECOMMENDATION:")
        if uncached_labs:
            print(f"Focus on {len(uncached_labs)} uncached labs for bot creation:")
            for lab in uncached_labs[:5]:  # Show top 5
                print(f"  - {lab['id']} ({lab['name']})")
            if len(uncached_labs) > 5:
                print(f"  ... and {len(uncached_labs) - 5} more")
        else:
            print("All labs are already cached. Consider running backtests on existing labs.")
        
        await client.close()
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'client' in locals():
            await client.close()

if __name__ == "__main__":
    asyncio.run(analyze_labs())




