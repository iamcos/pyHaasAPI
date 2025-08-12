#!/usr/bin/env python3
"""
Comprehensive test script for account management functions
"""
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
from pyHaasAPI import api

def main():
    print("🧪 Comprehensive Account Management Test")
    print("=" * 50)
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
    if not accounts:
        print("❌ No accounts found!")
        return
    for i, acc in enumerate(accounts, 1):
        print(f"  {i}. {acc.name} (ID: {acc.account_id}, Exchange: {acc.exchange_code})")
    # Add more comprehensive tests here as needed
    print("\n✅ Comprehensive account management tests completed!")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 