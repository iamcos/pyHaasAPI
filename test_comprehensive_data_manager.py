#!/usr/bin/env python3
"""
Test Comprehensive Data Manager

This script demonstrates the comprehensive data manager capabilities:
- Connect to srv01
- Fetch all data (labs, bots, accounts, backtests)
- Analyze for qualifying backtests
- Create bots with 55+ win rate and no drawdown
"""

import asyncio
import sys
from pathlib import Path

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI_v2.core.data_manager import ComprehensiveDataManager, DataManagerConfig
from pyHaasAPI_v2.config.settings import Settings


async def test_comprehensive_data_manager():
    """Test the comprehensive data manager"""
    print("🚀 Testing Comprehensive Data Manager")
    print("=" * 60)
    
    data_manager = None
    
    try:
        # Initialize data manager
        settings = Settings()
        config = DataManagerConfig(
            cache_duration_minutes=30,
            max_concurrent_requests=2,  # Reduced for stability
            request_delay_seconds=2.0,  # Increased delay
            auto_refresh=False,  # Disable for testing
            refresh_interval_minutes=15
        )
        
        data_manager = ComprehensiveDataManager(settings, config)
        
        print("🔧 Initializing data manager...")
        if not await data_manager.initialize():
            print("❌ Failed to initialize data manager")
            return 1
        
        print("✅ Data manager initialized")
        
        # Connect to srv01
        print("\n🔗 Connecting to srv01...")
        if not await data_manager.connect_to_server("srv01"):
            print("❌ Failed to connect to srv01")
            return 1
        
        print("✅ Connected to srv01")
        
        # Fetch all server data
        print("\n📊 Fetching all server data...")
        if not await data_manager.fetch_all_server_data("srv01"):
            print("❌ Failed to fetch server data")
            return 1
        
        print("✅ Fetched all server data")
        
        # Get server summary
        print("\n📋 Server Summary:")
        summary = await data_manager.get_server_summary()
        for server_name, data in summary.items():
            print(f"  {server_name}: {data['labs_count']} labs, {data['bots_count']} bots, {data['backtests_count']} backtests")
        
        # Get qualifying backtests
        print("\n🔍 Analyzing for qualifying backtests (55+ WR, no drawdown)...")
        qualifying_backtests = await data_manager.get_qualifying_backtests(
            "srv01",
            min_winrate=55.0,
            max_drawdown=0.0,
            min_trades=5
        )
        
        if not qualifying_backtests:
            print("⚠️ No qualifying backtests found")
            return 0
        
        print(f"✅ Found {len(qualifying_backtests)} qualifying backtests")
        
        # Display top results
        print("\n🏆 Top qualifying backtests:")
        for i, bt in enumerate(qualifying_backtests[:10]):
            print(f"  {i+1}. {bt['roe']:.1f}% ROE, {bt['winrate']:.1f}% WR, {bt['trades']} trades, {bt['max_drawdown']:.1f}% DD")
        
        # Create bots from top qualifying backtests
        print(f"\n🤖 Creating bots from top {min(5, len(qualifying_backtests))} backtests...")
        created_bots = await data_manager.create_bots_from_qualifying_backtests(
            "srv01",
            qualifying_backtests,
            max_bots=5
        )
        
        if created_bots:
            print(f"✅ Created {len(created_bots)} bots:")
            for bot in created_bots:
                print(f"  - {bot['bot_name']} (ID: {bot['bot_id']})")
        else:
            print("⚠️ No bots were created")
        
        print("\n🎉 Comprehensive data manager test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        if data_manager:
            print("\n🧹 Shutting down data manager...")
            await data_manager.shutdown()


async def main():
    """Main entry point"""
    return await test_comprehensive_data_manager()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
