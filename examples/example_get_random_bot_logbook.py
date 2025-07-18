#!/usr/bin/env python3
"""
Example: Get Runtime Logbook of a Random Bot

This script demonstrates how to use the pyHaasAPI to:
- Authenticate with the HaasOnline API
- Retrieve all bots
- Select a random bot
- Fetch and print its runtime logbook (step-by-step execution logs)

Environment variables are loaded from a .env file (see below).

Example .env file:
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your@email.com
API_PASSWORD=yourpassword

How it works:
1. Authenticate using your API credentials
2. Get all bots with api.get_all_bots(executor)
3. Pick a random bot
4. Get its logbook with api.get_bot_runtime_logbook(executor, bot_id)
5. Print the log entries
"""
import random
import os
from pyHaasAPI import api
from config import settings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_HOST = os.environ.get("API_HOST")
API_PORT = int(os.environ.get("API_PORT", 8090))
API_EMAIL = os.environ.get("API_EMAIL")
API_PASSWORD = os.environ.get("API_PASSWORD")

def main():
    print("=== Example: Get Random Bot Logbook ===")
    # Check for required environment variables
    if not all([API_HOST, API_PORT, API_EMAIL, API_PASSWORD]):
        print("Missing one or more required environment variables: API_HOST, API_PORT, API_EMAIL, API_PASSWORD")
        print("Please create a .env file with these values.")
        return
    # 1. Authenticate
    executor = api.RequestsExecutor(
        host=API_HOST,
        port=API_PORT,
        state=api.Guest()
    ).authenticate(email=API_EMAIL, password=API_PASSWORD)
    print("Authenticated!")

    # 2. Get all bots
    bots = api.get_all_bots(executor)
    if not bots:
        print("No bots found!")
        return
    print(f"Found {len(bots)} bots.")

    # 3. Pick a random bot
    bot = random.choice(bots)
    bot_id = getattr(bot, 'bot_id', None)
    bot_name = getattr(bot, 'bot_name', 'Unknown')
    print(f"Randomly selected bot: {bot_name} (ID: {bot_id})")
    if not bot_id:
        print("Selected bot has no ID!")
        return

    # 4. Get its runtime logbook
    logs = api.get_bot_runtime_logbook(executor, bot_id, next_page_id=-1, page_length=20)
    print(f"\n=== Runtime Logbook for '{bot_name}' ===")
    if not logs:
        print("No log entries found.")
    else:
        for entry in logs:
            print(entry)

    print("\nDone.")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 