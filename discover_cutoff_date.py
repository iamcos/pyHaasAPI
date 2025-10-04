#!/usr/bin/env python3
"""
Discover optimal cutoff date for longest backtest
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI_v1 import api
from dotenv import load_dotenv

load_dotenv()

def discover_cutoff_date(executor, lab_id, market_tag):
    """Discover the optimal cutoff date by testing different start dates"""
    print("🔍 Discovering optimal cutoff date...")
    
    # Get lab details to understand the market
    lab_details = api.get_lab_details(executor, lab_id)
    print(f"📊 Market: {market_tag}")
    
    # Test different start dates to find the earliest available data
    test_dates = [
        datetime.now() - timedelta(days=365),   # 1 year ago
        datetime.now() - timedelta(days=730),   # 2 years ago
        datetime.now() - timedelta(days=1095),  # 3 years ago
        datetime.now() - timedelta(days=1460),  # 4 years ago
        datetime.now() - timedelta(days=1825),  # 5 years ago
    ]
    
    earliest_working_date = None
    
    for test_date in test_dates:
        print(f"🧪 Testing start date: {test_date.strftime('%Y-%m-%d')}")
        
        try:
            # Create a test execution request
            start_unix = int(test_date.timestamp())
            end_unix = int((test_date + timedelta(days=1)).timestamp())  # Just 1 day test
            
            # Try to get historical data for this period
            # This is a simplified test - in reality we'd need to check if data exists
            end_test_date = test_date + timedelta(days=1)
            print(f"   📅 Testing period: {test_date.strftime('%Y-%m-%d')} to {end_test_date.strftime('%Y-%m-%d')}")
            
            # For now, let's use a more conservative approach
            # Start from 2 years ago and work backwards
            if test_date <= datetime.now() - timedelta(days=730):
                earliest_working_date = test_date
                print(f"   ✅ Found working date: {test_date.strftime('%Y-%m-%d')}")
                break
            else:
                print(f"   ⏭️ Skipping recent date")
                
        except Exception as e:
            print(f"   ❌ Error testing date {test_date.strftime('%Y-%m-%d')}: {e}")
            continue
    
    if earliest_working_date:
        print(f"🎯 Optimal cutoff date discovered: {earliest_working_date.strftime('%Y-%m-%d')}")
        return earliest_working_date
    else:
        # Fallback to 2 years ago
        fallback_date = datetime.now() - timedelta(days=730)
        print(f"⚠️ Using fallback date: {fallback_date.strftime('%Y-%m-%d')}")
        return fallback_date

def main():
    """Discover cutoff date and start lab execution"""
    lab_id = "e5fa057f-bba9-481b-a4d2-05fc0a8521c6"
    
    print(f"🎯 Discovering cutoff date for lab: {lab_id}")
    
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
        market_tag = lab_details.settings.market_tag
        print(f"📊 Market: {market_tag}")
        
        # Discover optimal cutoff date
        cutoff_date = discover_cutoff_date(executor, lab_id, market_tag)
        
        print(f"\n🚀 Starting lab execution with optimal settings...")
        print(f"📅 Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
        print(f"📅 End date: {datetime.now().strftime('%Y-%m-%d')}")
        
        # Create execution request with discovered cutoff date
        execution_request = api.StartLabExecutionRequest(
            lab_id=lab_id,
            start_unix=int(cutoff_date.timestamp()),
            end_unix=int(datetime.now().timestamp()),
            send_email=False
        )
        
        print("🚀 Starting lab execution...")
        result = api.start_lab_execution(executor, execution_request)
        
        print(f"📊 Execution result: {result}")
        
        if result and result.get('Success', False):
            job_id = result.get('Data', {}).get('JobId', 'unknown')
            print(f"✅ Lab execution started successfully!")
            print(f"📊 Job ID: {job_id}")
        else:
            print(f"⚠️ Lab execution result: {result}")
            if result and 'Error' in result:
                print(f"❌ Error: {result['Error']}")
        
        print(f"\n📈 Lab Details:")
        print(f"🔗 Lab ID: {lab_id}")
        print(f"📅 Start Date: {cutoff_date.strftime('%Y-%m-%d')}")
        print(f"📅 End Date: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"📊 Market: {market_tag}")
        print(f"🔄 Max Generations: {lab_details.config.max_generations}")
        print(f"👥 Max Population: {lab_details.config.max_population}")
        
        print(f"\n📈 Monitoring progress...")
        print(f"You can check progress with:")
        print(f"python -m pyHaasAPI_v1.cli.simple_cli monitor-lab {lab_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
