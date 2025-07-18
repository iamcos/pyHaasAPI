#!/usr/bin/env python3
"""
Bulk Set History Depth

This script allows you to set the history depth for all markets in the system.
It will ask for user input on how many months to sync, then apply this setting
to all available markets.
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import time
from pyHaasAPI import api


def main():
    """Bulk set history depth for all markets"""
    print("🚀 Bulk Set History Depth")
    print("=" * 40)
    
    # Get user input for months
    while True:
        try:
            months = int(input("📅 How many months of history to sync? (1-60): "))
            if 1 <= months <= 60:
                break
            else:
                print("❌ Please enter a number between 1 and 60")
        except ValueError:
            print("❌ Please enter a valid number")
    
    print(f"\n📊 Setting history depth to {months} months for all markets...")
    
    # Initialize and authenticate
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    print("✅ Authenticated!")
    
    try:
        # Get all markets with their current history status
        print("\n📋 Getting current history status...")
        history_status = api.get_history_status(executor)
        
        if not history_status:
            print("❌ No markets found!")
            return
        
        print(f"📊 Found {len(history_status)} markets")
        
        # Show current status
        print("\n📋 Current History Status:")
        print("-" * 50)
        for market, info in list(history_status.items())[:10]:  # Show first 10
            current_months = info.get('MaxMonths', 0)
            status = info.get('Status', 0)
            print(f"  {market}: {current_months} months (Status: {status})")
        
        if len(history_status) > 10:
            print(f"  ... and {len(history_status) - 10} more markets")
        
        # Confirm with user
        print(f"\n⚠️  This will set {months} months of history for ALL {len(history_status)} markets.")
        confirm = input("🤔 Continue? (y/N): ").lower().strip()
        
        if confirm != 'y':
            print("❌ Operation cancelled")
            return
        
        # Process all markets
        print(f"\n🔄 Setting history depth for {len(history_status)} markets...")
        print("=" * 60)
        
        successful = 0
        failed = 0
        results = []
        
        for i, (market, info) in enumerate(history_status.items(), 1):
            print(f"[{i}/{len(history_status)}] Setting {months} months for {market}...", end=" ")
            
            try:
                success = api.set_history_depth(executor, market, months)
                
                if success:
                    print("✅ Success")
                    successful += 1
                    results.append({"market": market, "status": "success", "months": months})
                else:
                    print("❌ Failed")
                    failed += 1
                    results.append({"market": market, "status": "failed", "months": months})
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                failed += 1
                results.append({"market": market, "status": "error", "error": str(e)})
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {len(history_status)}")
        
        if successful > 0:
            print(f"\n🎉 Successfully set {months} months history depth for {successful} markets!")
        
        # Save results
        import json
        with open('bulk_history_depth_results.json', 'w') as f:
            json.dump({
                "months_requested": months,
                "total_markets": len(history_status),
                "successful": successful,
                "failed": failed,
                "results": results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: bulk_history_depth_results.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Place the main execution logic here
    pass 