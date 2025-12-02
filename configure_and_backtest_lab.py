#!/usr/bin/env python3
"""
Configure lab with parameter ranges and run bruteforce backtest for 1 week
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Union, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.account.account_api import AccountAPI
from pyHaasAPI.models.lab import LabConfig, LabDetails
from pyHaasAPI.exceptions import LabError, AuthenticationError

async def configure_and_backtest_lab():
    """Configure lab with ranges and run bruteforce backtest"""
    print("🚀 Configuring Lab for Bruteforce Backtest (1 Week)")
    print("=" * 70)
    
    # Get credentials
    email = os.getenv('API_EMAIL_LOCAL') or os.getenv('API_EMAIL')
    password = os.getenv('API_PASSWORD_LOCAL') or os.getenv('API_PASSWORD')
    
    if not email or not password:
        print("❌ Error: API_EMAIL and API_PASSWORD must be set")
        return False
    
    print(f"📧 Using email: {email}")
    print(f"🌐 Connecting to: 127.0.0.1:8090")
    print()
    
    try:
        # Create config
        config = APIConfig(
            email=email,
            password=password,
            host="127.0.0.1",
            port=8090,
            timeout=30.0
        )
        
        # Create client and auth manager
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        # Authenticate
        print("🔐 Authenticating...")
        session = await auth_manager.authenticate()
        print(f"✅ Authentication successful! User ID: {session.user_id[:8]}...")
        print()
        
        # Create APIs
        lab_api = LabAPI(client, auth_manager)
        account_api = AccountAPI(client, auth_manager)
        
        # Step 1: List existing labs
        print("📋 Step 1: Listing existing labs...")
        labs = await lab_api.get_labs()
        print(f"✅ Found {len(labs)} lab(s)")
        
        if not labs:
            print("❌ No labs found. Please create a lab first.")
            await client.close()
            return False
        
        # Use the first lab
        selected_lab = labs[0]
        lab_id = selected_lab.lab_id
        print(f"📌 Using lab: {selected_lab.name} (ID: {lab_id[:8]}...)")
        print()
        
        # Step 2: Get lab details
        print("🔍 Step 2: Getting lab details...")
        lab_details = await lab_api.get_lab_details(lab_id)
        print(f"✅ Lab details retrieved!")
        print(f"   Script ID: {lab_details.script_id}")
        print(f"   Market: {getattr(lab_details.settings, 'market_tag', 'N/A') if hasattr(lab_details, 'settings') else 'N/A'}")
        print()
        
        # Step 3: Configure lab for bruteforce mode
        print("⚙️  Step 3: Configuring lab for bruteforce mode...")
        
        # Bruteforce mode: max_elites=1, mix_rate=0, adjust_rate=0
        bruteforce_config = LabConfig(
            max_parallel=20,  # Test many combinations in parallel
            max_generations=100,  # Many generations
            max_epochs=1,  # Single epoch per generation
            max_runtime=0,  # Unlimited runtime
            auto_restart=0,
            max_elites=1,  # BRUTEFORCE: Minimum elites (test all, don't evolve)
            mix_rate=0.0,  # No mixing in bruteforce
            adjust_rate=0.0  # No adjustment in bruteforce
        )
        
        await lab_api.ensure_lab_config_parameters(lab_id, bruteforce_config)
        print("✅ Lab configured for bruteforce mode")
        print(f"   Max Parallel: {bruteforce_config.max_parallel}")
        print(f"   Max Generations: {bruteforce_config.max_generations}")
        print(f"   Max Elites: {bruteforce_config.max_elites} (bruteforce - tests all combinations)")
        print(f"   Mix Rate: {bruteforce_config.mix_rate}%")
        print(f"   Adjust Rate: {bruteforce_config.adjust_rate}%")
        print()
        
        # Step 4: Set parameter ranges
        print("📊 Step 4: Setting parameter ranges...")
        
        # Get current parameters
        current_params = lab_details.parameters if hasattr(lab_details, 'parameters') and lab_details.parameters else []
        
        if not current_params:
            print("⚠️  No parameters found in lab. Using default ranges.")
            print("   (Parameters will need to be set manually if lab has none)")
        else:
            print(f"✅ Found {len(current_params)} parameter(s) in lab")
            
            # Create parameter ranges for bruteforce testing
            # Common ranges for trading parameters
            parameter_updates = []
            for param in current_params:
                # Handle both Pydantic models and dicts
                if isinstance(param, dict):
                    param_name = param.get('K', 'Unknown')
                    param_key = param.get('K', '')
                    current_value = param.get('O', [])
                else:
                    param_name = getattr(param, 'key', 'Unknown')  # Use key as name
                    param_key = getattr(param, 'key', '')
                    current_value = getattr(param, 'options', []) or getattr(param, 'value', [])
                
                # Define ranges based on parameter type/name
                if 'rsi' in param_name.lower() or 'length' in param_name.lower():
                    # RSI/Length parameters: 5-30, step 1
                    range_values = list(range(5, 31, 1))
                    print(f"   📈 {param_name}: Range 5-30 (step 1) - {len(range_values)} values")
                elif 'overbought' in param_name.lower():
                    # Overbought: 70-85, step 5
                    range_values = list(range(70, 86, 5))
                    print(f"   📈 {param_name}: Range 70-85 (step 5) - {len(range_values)} values")
                elif 'oversold' in param_name.lower():
                    # Oversold: 15-35, step 5
                    range_values = list(range(15, 36, 5))
                    print(f"   📈 {param_name}: Range 15-35 (step 5) - {len(range_values)} values")
                elif 'stoploss' in param_name.lower() or 'stop' in param_name.lower():
                    # Stop loss: 1-10, step 1
                    range_values = list(range(1, 11, 1))
                    print(f"   📈 {param_name}: Range 1-10 (step 1) - {len(range_values)} values")
                elif 'multiplier' in param_name.lower() or 'factor' in param_name.lower():
                    # Multiplier: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0
                    range_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
                    print(f"   📈 {param_name}: Range 0.5-3.0 - {len(range_values)} values")
                else:
                    # Default: ±50% around current value, reasonable steps
                    if isinstance(current_value, list) and len(current_value) > 0:
                        base_val = current_value[0]
                        if isinstance(base_val, (int, float)) and base_val > 0:
                            min_val = max(1, int(base_val * 0.5))
                            max_val = int(base_val * 1.5)
                            step = max(1, int((max_val - min_val) / 10))
                            range_values = list(range(min_val, max_val + 1, step))
                            print(f"   📈 {param_name}: Range {min_val}-{max_val} (step {step}) - {len(range_values)} values")
                        else:
                            # Keep current value if we can't determine range
                            range_values = current_value if isinstance(current_value, list) else [current_value]
                            print(f"   📈 {param_name}: Using current value(s)")
                    else:
                        # Keep current value
                        range_values = current_value if isinstance(current_value, list) else [current_value]
                        print(f"   📈 {param_name}: Using current value(s)")
                
                # Format parameter update
                parameter_updates.append({
                    "K": param_key,
                    "O": range_values,
                    "I": True,  # Include in optimization
                    "IS": True  # Include in optimization (second flag)
                })
            
            # Update lab parameters via update_lab_details
            if parameter_updates:
                print(f"\n   🔄 Updating {len(parameter_updates)} parameter(s) with ranges...")
                # Update lab details with parameters in P field (not scriptParameters)
                await lab_api.update_lab_details(
                    lab_id,
                    update_data={
                        "parameters": parameter_updates  # Send as "P" field
                    }
                )
                print("   ✅ Parameters updated with ranges!")
            else:
                print("   ⚠️  No parameter updates needed")
        print()
        
        # Step 5: Calculate 1-week backtest period
        print("📅 Step 5: Setting 1-week backtest period...")
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)  # 1 week
        
        start_unix = int(start_time.timestamp())
        end_unix = int(end_time.timestamp())
        
        print(f"   Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ({start_unix})")
        print(f"   End:   {end_time.strftime('%Y-%m-%d %H:%M:%S')} ({end_unix})")
        print(f"   Duration: 7 days")
        print()
        
        # Step 6: Start lab execution
        print("🚀 Step 6: Starting lab execution...")
        try:
            from pyHaasAPI.models.lab import StartLabExecutionRequest
            execution_request = StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=start_unix,
                end_unix=end_unix,
                send_email=False
            )
            response = await lab_api.start_lab_execution(execution_request, ensure_config=False)
            job_id = response.get("JobId") or response.get("job_id") or response.get("LID") or lab_id
            print(f"✅ Lab execution started!")
            print(f"   Job ID: {job_id}")
            print(f"   Lab ID: {lab_id}")
            print()
            
            # Step 7: Monitor execution status
            print("📊 Step 7: Monitoring execution status...")
            print("   (This may take a while for bruteforce mode)")
            print()
            
            # Check status a few times
            for i in range(5):
                await asyncio.sleep(3)  # Wait 3 seconds between checks
                try:
                    status = await lab_api.get_lab_execution_status(lab_id)
                    print(f"   Status check {i+1}: {status.status}")
                    print(f"   Progress: {status.progress:.1f}%")
                    print(f"   Iterations: {status.current_iteration}/{status.max_iterations}")
                    if hasattr(status, 'completed_backtests'):
                        print(f"   Completed backtests: {status.completed_backtests}")
                    print()
                except Exception as e:
                    print(f"   Status: Starting up... (error getting status: {e})")
                    print()
            
            print("✅ Lab execution is running!")
            print(f"   Monitor progress: python -m pyHaasAPI.cli.main lab status --lab-id {lab_id}")
            print()
            
        except Exception as e:
            print(f"⚠️  Could not start execution: {e}")
            print("   Lab may already be running or configured incorrectly")
            print()
        
        # Close client
        await client.close()
        
        print("✅ Configuration and execution setup completed!")
        return True
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except LabError as e:
        print(f"❌ Lab API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(configure_and_backtest_lab())
    sys.exit(0 if success else 1)
