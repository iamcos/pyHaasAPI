#!/usr/bin/env python3
"""Simple script to get lab details without freezing"""

import sys
import json
import requests
import time

def get_lab_via_mcp(lab_id):
    """Try to get lab details via MCP server"""
    try:
        url = f"http://localhost:8000/get_lab_details"
        params = {"lab_id": lab_id}
        
        print(f"Requesting lab details for {lab_id}...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"MCP request failed: {e}")
        return None

def get_lab_direct_api(lab_id):
    """Try direct API approach with timeout"""
    try:
        # This is a simplified version that should not freeze
        import sys
        sys.path.append('.')
        
        # Set a timeout alarm
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("API call timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        from pyHaasAPI import api
        from pyHaasAPI.api import SyncExecutor
        
        # Quick connection test
        executor = SyncExecutor()
        
        # Try to authenticate quickly
        auth_result = api.authenticate(executor, 'your_email@example.com', 'your_password')
        if not auth_result:
            return None
            
        # Get lab details
        lab_details = api.get_lab_details(executor, lab_id)
        
        signal.alarm(0)  # Cancel timeout
        
        return {
            "lab_id": lab_details.lab_id,
            "parameters": lab_details.parameters,
            "settings": lab_details.settings.model_dump() if hasattr(lab_details.settings, 'model_dump') else str(lab_details.settings)
        }
        
    except TimeoutError:
        print("API call timed out after 30 seconds")
        return None
    except Exception as e:
        print(f"Direct API failed: {e}")
        return None
    finally:
        signal.alarm(0)  # Make sure to cancel timeout

if __name__ == "__main__":
    lab_id = "e445821b-09b7-4559-8644-add67dd11242"
    
    print("Attempting to get lab details...")
    
    # Try MCP server first
    result = get_lab_via_mcp(lab_id)
    
    if not result:
        print("MCP failed, trying direct API...")
        result = get_lab_direct_api(lab_id)
    
    if result:
        # Save to file
        with open('lab_details.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print("✅ Lab details saved to lab_details.json")
        
        # Print parameter summary
        if 'parameters' in result:
            print(f"\n📊 Found {len(result['parameters'])} parameters:")
            for i, param in enumerate(result['parameters']):
                name = param.get('K', f'Param_{i}')
                value = param.get('V', param.get('O', ['N/A'])[0] if param.get('O') else 'N/A')
                param_type = param.get('T', 'Unknown')
                print(f"  {i+1}. {name} = {value} (type: {param_type})")
    else:
        print("❌ Failed to get lab details")
        sys.exit(1)