#!/usr/bin/env python3
"""
Debug lab response format
"""

import requests
import json

MCP_SERVER_URL = "http://127.0.0.1:8000"

def debug_labs():
    """Debug the lab response"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/get_all_labs")
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def check_server_status():
    """Check server status"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/status")
        print(f"Server status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Status data: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Status check error: {e}")

def main():
    print("🔧 Debugging MCP server responses...")
    print("\n1. Checking server status:")
    check_server_status()
    
    print("\n2. Checking labs response:")
    debug_labs()

if __name__ == "__main__":
    main()