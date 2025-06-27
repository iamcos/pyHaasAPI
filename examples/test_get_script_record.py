#!/usr/bin/env python3
"""
Test script for GET_SCRIPT_RECORD endpoint
"""

import json
from pyHaasAPI import api

def main():
    print("🚀 Testing GET_SCRIPT_RECORD endpoint...")
    
    # Setup
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    
    print("✅ Authentication successful")
    
    # Get all scripts first to find a script ID
    print("\n📜 Getting all scripts...")
    try:
        scripts = api.get_all_scripts(executor)
        print(f"✅ Found {len(scripts)} scripts")
        
        if scripts:
            # Use the first script for testing
            script = scripts[0]
            script_id = script.script_id
            print(f"🎯 Testing with script: {script.script_name} (ID: {script_id})")
            
            # Test GET_SCRIPT_RECORD
            print(f"\n📋 Getting script record for {script_id}...")
            try:
                script_record = api.get_script_record(executor, script_id)
                print(f"✅ Successfully retrieved script record")
                print(f"   Script Name: {script_record.script_name}")
                print(f"   Script Description: {script_record.script_description}")
                print(f"   Script Type: {script_record.script_type}")
                print(f"   Script Status: {script_record.script_status}")
                print(f"   Is Valid: {script_record.is_valid}")
                print(f"   Is Compiled: {script_record.is_compiled}")
                print(f"   Folder ID: {script_record.folder_id}")
                
                # Show compile result info
                compile_result = script_record.compile_result
                print(f"\n🔧 Compile Result:")
                print(f"   Is Valid: {compile_result.is_valid}")
                print(f"   Optimization Level: {compile_result.optimization}")
                print(f"   Compile Log Entries: {len(compile_result.compile_log)}")
                
                if compile_result.compile_log:
                    print(f"   First few log entries:")
                    for i, log_entry in enumerate(compile_result.compile_log[:3]):
                        print(f"     {i+1}. {log_entry}")
                
                # Show script components info
                print(f"\n🧩 Script Components:")
                print(f"   Components JSON length: {len(script_record.script_components)} characters")
                
                # Parse the components JSON to show structure
                try:
                    components = json.loads(script_record.script_components)
                    print(f"   Number of components: {len(components)}")
                    
                    if components:
                        # Show first component info
                        first_comp = components[0]
                        print(f"   First component:")
                        print(f"     Type: {first_comp.get('Type')}")
                        print(f"     Command: {first_comp.get('CommandName')}")
                        print(f"     Position: ({first_comp.get('X')}, {first_comp.get('Y')})")
                        
                except json.JSONDecodeError as e:
                    print(f"   ⚠️ Could not parse components JSON: {e}")
                
            except Exception as e:
                print(f"❌ Failed to get script record: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ No scripts found to test with")
            
    except Exception as e:
        print(f"❌ Failed to get scripts: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main() 