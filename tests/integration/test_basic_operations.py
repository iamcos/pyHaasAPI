#!/usr/bin/env python3
"""
Basic operations integration test
"""
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
from pyHaasAPI import api

def main():
    print("🧪 Basic Operations Integration Test")
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
    # Add your test logic here
    print("\n✅ Basic operations integration test completed!")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 