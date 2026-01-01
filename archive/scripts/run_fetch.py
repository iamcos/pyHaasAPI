#!/usr/bin/env python3
"""
Simple script to run backtest fetching
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI.cli_ref.project_manager_cli import ProjectManagerCLI

async def main():
    """Run fetch for all servers"""
    print("🚀 Starting backtest fetch for all servers...")
    
    cli = ProjectManagerCLI()
    
    try:
        # Fetch backtests for all servers
        servers = ["srv01", "srv02", "srv03"]
        result = await cli.fetch(servers, count=50, resume=True)
        
        print("✅ Fetch completed!")
        print(f"📊 Results: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cli.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

