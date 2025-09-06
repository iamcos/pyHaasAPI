#!/usr/bin/env python3
"""
Debug Bot Objects

Simple script to examine what the actual bot objects look like
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api

def main():
    # Connect to API
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    print(f"Connecting to {api_host}:{api_port}...")
    
    haas_api = api.RequestsExecutor(
        host=api_host,
        port=api_port,
        state=api.Guest()
    )
    
    executor = haas_api.authenticate(api_email, api_password)
    print("✅ Connected to API")
    
    # Get bots
    bots = api.get_all_bots(executor)
    print(f"\nFound {len(bots)} bots")
    
    # Examine first few bots in detail
    for i, bot in enumerate(bots[:5]):
        print(f"\n--- Bot {i+1} ---")
        print(f"Type: {type(bot)}")
        print(f"Dir: {dir(bot)}")
        
        # Try common attributes
        for attr in ['bot_id', 'Name', 'name', 'AccountId', 'account_id', 'Status', 'status']:
            try:
                value = getattr(bot, attr, None)
                print(f"{attr}: {value}")
            except Exception as e:
                print(f"{attr}: Error - {e}")
        
        # Try to access as dict if it has model_dump
        if hasattr(bot, 'model_dump'):
            try:
                data = bot.model_dump()
                print(f"Model dump keys: {list(data.keys())}")
                for key, value in list(data.items())[:5]:  # Show first 5
                    print(f"  {key}: {value}")
            except Exception as e:
                print(f"Model dump error: {e}")

if __name__ == "__main__":
    main()

