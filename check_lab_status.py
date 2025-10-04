#!/usr/bin/env python3
"""
Check lab status and potentially cancel existing run
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI_v1 import api
from dotenv import load_dotenv

load_dotenv()

def main():
    """Check lab status and cancel if needed"""
    lab_id = "e5fa057f-bba9-481b-a4d2-05fc0a8521c6"
    
    print(f"🔍 Checking status for lab: {lab_id}")
    
    try:
        # Create API connection
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        
        # Authenticate
        print("🔐 Authenticating...")
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        
        print("✅ Authenticated successfully")
        
        # Get lab details
        print(f"📊 Getting lab details for {lab_id}...")
        lab_details = api.get_lab_details(executor, lab_id)
        
        print(f"📊 Lab Status: {lab_details.status}")
        print(f"📊 Lab Name: {lab_details.name}")
        print(f"📊 Market: {lab_details.settings.market_tag}")
        print(f"📊 Scheduled Backtests: {lab_details.scheduled_backtests}")
        print(f"📊 Completed Backtests: {lab_details.completed_backtests}")
        print(f"📊 Running Since: {lab_details.running_since}")
        print(f"📊 Start Unix: {lab_details.start_unix}")
        print(f"📊 End Unix: {lab_details.end_unix}")
        
        # Check if lab is running
        if lab_details.status.value == 1:  # QUEUED
            print("⚠️ Lab is in QUEUED status - it may be stuck")
            print("🔄 Attempting to cancel existing execution...")
            
            try:
                cancel_result = api.cancel_lab_execution(executor, lab_id)
                print(f"📊 Cancel result: {cancel_result}")
                
                # Wait a moment
                import time
                time.sleep(3)
                
                # Check status again
                updated_details = api.get_lab_details(executor, lab_id)
                print(f"📊 Updated status: {updated_details.status}")
                
            except Exception as e:
                print(f"❌ Error canceling lab: {e}")
        
        elif lab_details.status.value == 2:  # RUNNING
            print("✅ Lab is actively running")
            print(f"📊 Progress: {lab_details.completed_backtests}/{lab_details.scheduled_backtests}")
            
        else:
            print(f"📊 Lab status: {lab_details.status}")
        
        print(f"\n📈 Lab Configuration:")
        print(f"🔄 Max Generations: {lab_details.config.max_generations}")
        print(f"👥 Max Population: {lab_details.config.max_population}")
        print(f"📅 Start Date: {lab_details.start_unix}")
        print(f"📅 End Date: {lab_details.end_unix}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()






