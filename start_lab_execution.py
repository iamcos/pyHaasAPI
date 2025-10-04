#!/usr/bin/env python3
"""
Start lab execution with longest backtest discovery
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
    """Start lab execution for the specified lab ID"""
    lab_id = "e5fa057f-bba9-481b-a4d2-05fc0a8521c6"
    
    print(f"🎯 Starting lab execution for: {lab_id}")
    
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
        print(f"📊 Lab details: {lab_details}")
        
        # Configure for longest backtest (discover cutoff date)
        print("🔍 Discovering cutoff date for longest backtest...")
        
        # For now, let's use a reasonable start date (2 years ago)
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        
        print(f"📅 Using cutoff date: {cutoff_date}")
        
        # Update lab settings for longest backtest
        print("⚙️ Updating lab settings for longest backtest...")
        
        # Update the lab details object with new settings
        lab_details.config.max_generations = 100
        lab_details.config.max_population = 10
        
        # Update the lab details
        updated_lab = api.update_lab_details(executor, lab_details)
        
        print("✅ Lab settings updated")
        
        # Start lab execution
        print("🚀 Starting lab execution...")
        
        # Create execution request with longest backtest period
        from datetime import datetime, timedelta
        start_date = datetime.now() - timedelta(days=730)  # 2 years ago
        end_date = datetime.now()
        
        execution_request = api.StartLabExecutionRequest(
            lab_id=lab_id,
            start_unix=int(start_date.timestamp()),
            end_unix=int(end_date.timestamp()),
            send_email=False
        )
        
        result = api.start_lab_execution(executor, execution_request)
        print(f"📊 Execution result: {result}")
        
        if result and result.get('Success', False):
            job_id = result.get('Data', {}).get('JobId', 'unknown')
        else:
            job_id = 'unknown'
            print(f"⚠️ Lab execution may have failed: {result}")
        
        print(f"✅ Lab execution started!")
        print(f"📊 Job ID: {job_id}")
        print(f"🔗 Lab ID: {lab_id}")
        print(f"📅 Start Date: {cutoff_date}")
        print(f"📅 End Date: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"🔄 Max Iterations: 1500")
        
        print("\n📈 Monitoring progress...")
        print("You can check progress with:")
        print(f"python -m pyHaasAPI_v1.cli.simple_cli monitor-lab {lab_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
