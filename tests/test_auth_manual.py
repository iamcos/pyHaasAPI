#!/usr/bin/env python3
"""
Manual authentication test script
"""
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
from pyHaasAPI import api

def main():
    print("🔐 Manual Authentication Test")
    print("=" * 40)
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    )
    email = settings.API_EMAIL
    password = settings.API_PASSWORD
    print(f"Using email: {email}")
    print("Attempting authentication...")
    try:
        auth_executor = executor.authenticate(email=email, password=password)
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 