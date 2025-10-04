#!/usr/bin/env python3
"""
Start longest backtest on server 3 lab
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI_v1 import api, HaasAnalyzer, UnifiedCacheManager
from dotenv import load_dotenv

load_dotenv()

def establish_ssh_tunnel():
    """Establish SSH tunnel to server 3"""
    print("🔗 Establishing SSH tunnel to server 3...")
    
    # Kill any existing tunnel on port 8090
    try:
        subprocess.run(["pkill", "-f", "ssh.*8090"], check=False)
        time.sleep(1)
    except:
        pass
    
    # Start SSH tunnel to server 3
    # Note: You'll need to replace with actual server 3 SSH details
    ssh_command = [
        "ssh", "-L", "8090:localhost:8090", 
        "srv03",  # Replace with actual server 3 hostname/IP
        "-N"  # Don't execute remote commands
    ]
    
    print(f"🚀 Starting SSH tunnel: {' '.join(ssh_command)}")
    
    # Start tunnel in background
    tunnel_process = subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a moment for tunnel to establish
    time.sleep(3)
    
    # Check if tunnel is working
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 8090))
        sock.close()
        
        if result == 0:
            print("✅ SSH tunnel established successfully")
            return tunnel_process
        else:
            print("❌ SSH tunnel failed to establish")
            tunnel_process.terminate()
            return None
    except Exception as e:
        print(f"❌ Error checking tunnel: {e}")
        tunnel_process.terminate()
        return None

def main():
    """Connect to server 3 and start lab execution"""
    tunnel_process = None
    try:
        # Establish SSH tunnel
        tunnel_process = establish_ssh_tunnel()
        if not tunnel_process:
            print("❌ Failed to establish SSH tunnel to server 3")
            return
        
        print("🔗 Connecting to server 3 via tunnel...")
        
        # Create analyzer with cache manager
        cache_manager = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache_manager)
        
        # Connect to API (this will use environment variables for server 3)
        if not analyzer.connect():
            print("❌ Failed to connect to HaasOnline API")
            return
        
        print("✅ Connected to server 3")
        
        # Get executor from analyzer
        executor = analyzer.executor
        
        print("✅ Authenticated successfully")
        
        # Get labs
        print("📋 Fetching labs...")
        labs = api.get_labs(executor)
        
        if not labs:
            print("❌ No labs found on server 3")
            return
        
        print(f"✅ Found {len(labs)} labs on server 3")
        
        # Show first few labs
        print("\n📊 Available labs:")
        for i, lab in enumerate(labs[:5]):
            lab_name = getattr(lab, 'lab_name', 'Unknown')
            print(f"  {i+1}. {lab.lab_id}: {lab_name}")
        
        # Use the first lab for longest backtest
        target_lab = labs[0]
        lab_id = target_lab.lab_id
        lab_name = getattr(target_lab, 'lab_name', 'Unknown')
        
        print(f"\n🎯 Starting longest backtest for lab: {lab_id} ({lab_name})")
        
        # Get lab details
        lab_details = api.get_lab_details(executor, lab_id)
        print(f"📊 Lab details: {lab_details}")
        
        # Configure for longest backtest (discover cutoff date)
        print("🔍 Discovering cutoff date for longest backtest...")
        
        # For now, let's use a reasonable start date (2 years ago)
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        
        print(f"📅 Using cutoff date: {cutoff_date}")
        
        # Update lab settings for longest backtest
        lab_settings = {
            "start_date": cutoff_date,
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "max_iterations": 1500,
            "max_generations": 100
        }
        
        print("⚙️ Updating lab settings for longest backtest...")
        api.update_lab_details(executor, lab_id, lab_settings)
        
        print("✅ Lab settings updated")
        
        # Start lab execution
        print("🚀 Starting lab execution...")
        job_id = api.start_lab_execution(executor, lab_id)
        
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
    finally:
        # Clean up SSH tunnel
        if tunnel_process:
            print("🧹 Cleaning up SSH tunnel...")
            tunnel_process.terminate()
            tunnel_process.wait()

if __name__ == "__main__":
    main()
