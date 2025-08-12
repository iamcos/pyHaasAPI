#!/usr/bin/env python3
"""
Test script for simulated account management
"""
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
from pyHaasAPI import api

def main():
    print("🧪 Simulated Account Management Test")
    print("=" * 40)
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    print("✅ Authentication successful!")
    accounts = api.get_accounts(executor)
    sim_accounts = [acc for acc in accounts if acc.is_simulated]
    if not sim_accounts:
        print("❌ No simulated accounts found!")
        return
    for acc in sim_accounts:
        print(f"Simulated Account: {acc.name} (ID: {acc.account_id})")
    print("\n✅ Simulated account management tests completed!")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 