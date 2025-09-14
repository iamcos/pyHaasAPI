#!/usr/bin/env python3
"""
Quick check of parameter iteration results
"""

import time
from pyHaasAPI import api
from pyHaasAPI.tools.utils import fetch_all_lab_backtests

def check_results():
    print("🔍 Checking parameter iteration results...")
    
    # Authenticate
    try:
        executor = api.RequestsExecutor(
            host="127.0.0.1", port=8090, state=api.Guest()
        ).authenticate(
            email="your_email@example.com", password="your_password"
        )
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Get all labs
    try:
        labs = api.get_all_labs(executor)
        print(f"📋 Found {len(labs)} labs")
        
        # Filter for our test labs
        test_labs = [lab for lab in labs if lab.name.startswith("ParamTest_")]
        print(f"🧪 Found {len(test_labs)} test labs")
        
        for lab in test_labs:
            print(f"\n📊 Lab: {lab.name}")
            print(f"   ID: {lab.lab_id}")
            print(f"   Status: {lab.status}")
            
            # Get lab details
            try:
                details = api.get_lab_details(executor, lab.lab_id)
                print(f"   Parameters: {len(details.parameters)}")
                
                # Check for optimized parameters
                optimized_params = []
                for param in details.parameters:
                    if param.get('bruteforce', False):
                        optimized_params.append(param.get('K', ''))
                
                print(f"   Optimized parameters: {optimized_params}")
                
                # Get backtest results using centralized fetcher
                try:
                    backtests = fetch_all_lab_backtests(executor, lab.lab_id)
                    
                    if backtests:
                        print(f"   Backtest configurations: {len(backtests)}")
                        
                        # Show best result
                        best_result = max(backtests, key=lambda x: x.summary.ReturnOnInvestment if x.summary else 0)
                        print(f"   Best ROI: {best_result.summary.ReturnOnInvestment if best_result.summary else 0:.2f}%")
                        
                        # Show parameter variations if any
                        if len(backtests) > 1:
                            print(f"   ✅ Multiple configurations tested!")
                            for i, result in enumerate(backtests[:3]):  # Show first 3
                                roi = result.summary.ReturnOnInvestment if result.summary else 0
                                params = getattr(result, 'parameters', {})
                                print(f"     Config {i+1}: ROI {roi:.2f}%, Params: {params}")
                        else:
                            print(f"   ⚠️ Only one configuration tested")
                    else:
                        print(f"   ❌ No backtest results found")
                        
                except Exception as e:
                    print(f"   ❌ Error getting backtest results: {e}")
                    
            except Exception as e:
                print(f"   ❌ Error getting lab details: {e}")
                
    except Exception as e:
        print(f"❌ Error getting labs: {e}")

if __name__ == "__main__":
    check_results()
