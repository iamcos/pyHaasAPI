#!/usr/bin/env python3
"""
Debug Labs

This script shows what labs exist and their names to understand the naming pattern.
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

    if not api_email or not api_password:
        print("❌ API_EMAIL and API_PASSWORD must be set in .env file")
        return 1

    print("🔌 Connecting to HaasOnline API...")

    try:
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )
        executor = haas_api.authenticate(api_email, api_password)
        print("✅ Connected to API successfully")
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return 1

    # Get all labs
    try:
        labs = api.get_all_labs(executor)
        print(f"\n🧪 Found {len(labs)} labs:")
        print("=" * 60)
        
        for i, lab in enumerate(labs, 1):
            print(f"{i:2d}. Lab object type: {type(lab)}")
            print(f"    Lab object dir: {dir(lab)}")
            print(f"    Lab object dict: {lab.__dict__ if hasattr(lab, '__dict__') else 'No __dict__'}")
            
            # Try different ways to access attributes
            lab_id = getattr(lab, 'LID', None)
            if lab_id is None:
                lab_id = getattr(lab, 'id', None)
            if lab_id is None:
                lab_id = getattr(lab, 'lab_id', None)
            if lab_id is None:
                lab_id = getattr(lab, 'ID', None)
                
            lab_name = getattr(lab, 'N', None)
            if lab_name is None:
                lab_name = getattr(lab, 'name', None)
            if lab_name is None:
                lab_name = getattr(lab, 'lab_name', None)
            if lab_name is None:
                lab_name = getattr(lab, 'Name', None)
                
            lab_desc = getattr(lab, 'D', None)
            if lab_desc is None:
                lab_desc = getattr(lab, 'description', None)
            if lab_desc is None:
                lab_desc = getattr(lab, 'desc', None)
            if lab_desc is None:
                lab_desc = getattr(lab, 'Description', None)
                
            lab_script = getattr(lab, 'SI', None)
            if lab_script is None:
                lab_script = getattr(lab, 'script_id', None)
            if lab_script is None:
                lab_script = getattr(lab, 'script', None)
            if lab_script is None:
                lab_script = getattr(lab, 'ScriptId', None)
            
            print(f"    Lab ID: {lab_id[:8] if lab_id else 'Unknown'}...")
            print(f"    Name: {lab_name or 'Unknown'}")
            print(f"    Description: {lab_desc or 'No description'}")
            print(f"    Script ID: {lab_script[:8] if lab_script else 'Unknown'}...")
            print()
            
            # Only show first 3 labs to avoid spam
            if i >= 3:
                print(f"... and {len(labs) - 3} more labs")
                break
                
    except Exception as e:
        print(f"❌ Failed to get labs: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
