#!/usr/bin/env python3
"""
Check what labs are available on the server
"""

import requests
import json
import urllib.parse

MCP_SERVER_URL = "http://127.0.0.1:8000"

def get_all_labs():
    """Get all existing labs"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/get_all_labs")
        if response.status_code == 200:
            data = response.json()
            if data.get("Success"):
                return data.get("Data", [])
        return []
    except Exception as e:
        print(f"Error getting labs: {e}")
        return []

def main():
    print("🔍 Checking available labs...")
    
    labs = get_all_labs()
    
    if not labs:
        print("❌ No labs found or server not accessible")
        return
    
    print(f"✅ Found {len(labs)} labs:")
    print()
    
    for i, lab in enumerate(labs, 1):
        lab_id = lab.get("LID", "N/A")
        lab_name_raw = lab.get("N", "N/A")
        # Decode URL-encoded names
        lab_name = urllib.parse.unquote(lab_name_raw) if lab_name_raw != "N/A" else "N/A"
        print(f"{i:2d}. {lab_name}")
        print(f"    ID: {lab_id}")
        print()
    
    # Look for the specific lab ID
    target_id = "edd56c9f-97d9-4417-984b-06f3a6411763"
    found_lab = next((lab for lab in labs if lab.get("LID") == target_id), None)
    
    if found_lab:
        lab_name = urllib.parse.unquote(found_lab.get("N", "N/A"))
        print(f"✅ Found target lab: {lab_name} ({target_id})")
    else:
        print(f"❌ Target lab {target_id} not found")
        print("Available lab IDs:")
        for lab in labs:
            print(f"  - {lab.get('LID')}")

if __name__ == "__main__":
    main()