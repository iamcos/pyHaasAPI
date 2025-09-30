#!/usr/bin/env python3
"""
Debug Bot Structure

This script examines the actual structure of bot objects returned by the API
to understand how to properly extract bot information.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager


async def debug_bot_structure():
    """Debug the structure of bot objects"""
    print("Debugging Bot Structure")
    print("=" * 60)
    
    try:
        # Establish SSH tunnel
        print("Connecting to srv03...")
        ssh_cmd = [
            "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
            "prod@srv03"
        ]
        
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        await asyncio.sleep(5)
        
        if process.poll() is not None:
            print("SSH tunnel failed")
            return 1
        
        print("SSH tunnel established")
        
        # Get credentials
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("API_EMAIL and API_PASSWORD environment variables are required")
            return 1
        
        # Initialize analyzer and connect
        cache = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache)
        success = analyzer.connect(
            host='127.0.0.1',
            port=8090,
            email=email,
            password=password
        )
        
        if not success:
            print("Failed to connect to API")
            return 1
        
        print("Successfully connected to API")
        
        # Get all bots
        print("\nFetching all bots...")
        bots = api.get_all_bots(analyzer.executor)
        print(f"Found {len(bots)} bots")
        
        if not bots:
            print("No bots found")
            return 1
        
        # Examine first bot in detail
        first_bot = bots[0]
        print(f"\nFirst bot type: {type(first_bot)}")
        print(f"First bot class: {first_bot.__class__}")
        print(f"First bot dir: {dir(first_bot)}")
        
        # Try different ways to access bot data
        print("\nTrying different access methods:")
        
        # Method 1: Direct attribute access
        print("Method 1 - Direct attributes:")
        try:
            print(f"  bot_id: {getattr(first_bot, 'bot_id', 'NOT_FOUND')}")
            print(f"  bot_name: {getattr(first_bot, 'bot_name', 'NOT_FOUND')}")
            print(f"  account_id: {getattr(first_bot, 'account_id', 'NOT_FOUND')}")
            print(f"  market: {getattr(first_bot, 'market', 'NOT_FOUND')}")
            print(f"  script_id: {getattr(first_bot, 'script_id', 'NOT_FOUND')}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 2: Dictionary access
        print("Method 2 - Dictionary access:")
        try:
            if isinstance(first_bot, dict):
                print(f"  BotId: {first_bot.get('BotId', 'NOT_FOUND')}")
                print(f"  BotName: {first_bot.get('BotName', 'NOT_FOUND')}")
                print(f"  AccountId: {first_bot.get('AccountId', 'NOT_FOUND')}")
                print(f"  MarketTag: {first_bot.get('MarketTag', 'NOT_FOUND')}")
                print(f"  ScriptId: {first_bot.get('ScriptId', 'NOT_FOUND')}")
            else:
                print("  Not a dictionary")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 3: Model dump
        print("Method 3 - Model dump:")
        try:
            if hasattr(first_bot, 'model_dump'):
                bot_dict = first_bot.model_dump()
                print(f"  model_dump result: {type(bot_dict)}")
                print(f"  Keys: {list(bot_dict.keys()) if isinstance(bot_dict, dict) else 'Not a dict'}")
                if isinstance(bot_dict, dict):
                    for key, value in bot_dict.items():
                        print(f"    {key}: {value}")
            else:
                print("  No model_dump method")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 4: Get all attributes
        print("Method 4 - All attributes:")
        try:
            for attr in dir(first_bot):
                if not attr.startswith('_'):
                    try:
                        value = getattr(first_bot, attr)
                        print(f"  {attr}: {value} ({type(value)})")
                    except Exception as e:
                        print(f"  {attr}: Error accessing - {e}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 5: Try to get individual bot details
        print("\nMethod 5 - Individual bot details:")
        try:
            # Try to get bot ID first
            bot_id = None
            if hasattr(first_bot, 'bot_id'):
                bot_id = first_bot.bot_id
            elif isinstance(first_bot, dict):
                bot_id = first_bot.get('BotId')
            elif hasattr(first_bot, 'model_dump'):
                bot_dict = first_bot.model_dump()
                bot_id = bot_dict.get('bot_id') or bot_dict.get('BotId')
            
            if bot_id:
                print(f"  Bot ID found: {bot_id}")
                # Try to get individual bot details
                bot_details = api.get_bot(analyzer.executor, bot_id)
                if bot_details:
                    print(f"  Bot details type: {type(bot_details)}")
                    print(f"  Bot details: {bot_details}")
                else:
                    print("  Could not get bot details")
            else:
                print("  Could not find bot ID")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Show first 3 bots with all their data
        print("\nFirst 3 bots complete data:")
        for i, bot in enumerate(bots[:3]):
            print(f"\nBot {i+1}:")
            print(f"  Type: {type(bot)}")
            print(f"  Class: {bot.__class__}")
            print(f"  Repr: {repr(bot)}")
            print(f"  Str: {str(bot)}")
        
        print("\nBot structure debugging completed!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        try:
            if 'process' in locals() and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        except:
            pass


async def main():
    """Main entry point"""
    return await debug_bot_structure()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
