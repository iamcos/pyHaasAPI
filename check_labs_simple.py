#!/usr/bin/env python3
"""
Simple script to check labs on local servers without requiring full dependencies
"""

import json
import requests
import urllib.parse
from typing import Dict, List, Optional

# Server configurations
SERVERS = {
    "srv01": {"host": "127.0.0.1", "port": 8090},
    "srv02": {"host": "127.0.0.1", "port": 8092},
}

def check_labs_on_server(server_name: str, host: str, port: int) -> Dict:
    """Check labs on a specific server"""
    base_url = f"http://{host}:{port}"
    
    print(f"\n🔍 Checking {server_name} ({host}:{port})...")
    
    # Try to get labs - we need to check what endpoints are available
    # Based on the codebase, labs are accessed via POST to Labs endpoint
    # But we need credentials for that, so let's try a simple health check first
    
    try:
        # Check if server is responding
        health_url = f"{base_url}/api/health"
        try:
            response = requests.get(health_url, timeout=5)
            print(f"   Health check: {response.status_code}")
        except:
            pass
        
        # Try to access Labs endpoint (might need auth)
        labs_url = f"{base_url}/Labs"
        try:
            # Without auth, this will likely fail, but let's see what error we get
            response = requests.get(labs_url, timeout=5)
            print(f"   Labs endpoint GET: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
        except requests.exceptions.RequestException as e:
            print(f"   Labs endpoint error: {type(e).__name__}")
        
        return {"server": server_name, "accessible": True, "port": port}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"server": server_name, "accessible": False, "error": str(e)}

def main():
    """Main function"""
    print("🚀 Checking Labs on Local Servers")
    print("=" * 50)
    
    results = {}
    for server_name, config in SERVERS.items():
        result = check_labs_on_server(
            server_name, 
            config["host"], 
            config["port"]
        )
        results[server_name] = result
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    for server_name, result in results.items():
        status = "✅" if result.get("accessible") else "❌"
        print(f"{status} {server_name}: {result.get('port', 'N/A')}")
    
    print("\n💡 Note: Full lab listing requires authentication.")
    print("   To see actual labs, use: python -m pyHaasAPI.cli lab list")

if __name__ == "__main__":
    main()

