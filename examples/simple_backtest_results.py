#!/usr/bin/env python3
"""
Simple Backtest Results Example

This example directly replicates the cURL request for GET_BACKTEST_RESULT_PAGE
with the exact parameters from the provided example.
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest


def main():
    """Replicate the cURL request for backtest results"""
    print("🚀 Replicating GET_BACKTEST_RESULT_PAGE request...")
    
    # Initialize and authenticate
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    
    # Parameters from your cURL request
    lab_id = "5a21c24f-5150-4dcd-b61c-595aef146d02"
    next_page_id = 0
    page_length = 1000
    
    print(f"📋 Requesting backtest results:")
    print(f"   Lab ID: {lab_id}")
    print(f"   Page ID: {next_page_id}")
    print(f"   Page Length: {page_length}")
    
    try:
        # This replicates your cURL request exactly
        results = api.get_backtest_result(
            executor,
            GetBacktestResultRequest(
                lab_id=lab_id,
                next_page_id=next_page_id,
                page_lenght=page_length
            )
        )
        
        print(f"\n✅ Success! Retrieved {len(results.items)} backtest configurations")
        print(f"📄 Next page ID: {results.next_page_id if results.next_page_id else 'No more pages'}")
        
        # Display first few results
        print(f"\n📊 First 3 configurations:")
        for i, result in enumerate(results.items[:3], 1):
            print(f"\n   Configuration {i}:")
            print(f"   - Backtest ID: {result.backtest_id}")
            print(f"   - Generation: {result.generation_idx}")
            print(f"   - Population: {result.population_idx}")
            print(f"   - Status: {result.status}")
            
            if result.summary:
                print(f"   - ROI: {result.summary.ReturnOnInvestment}%")
                print(f"   - Realized Profits: {result.summary.RealizedProfits}")
                print(f"   - Fee Costs: {result.summary.FeeCosts}")
        
        # Show total results summary
        if results.items:
            rois = [r.summary.ReturnOnInvestment for r in results.items if r.summary]
            if rois:
                print(f"\n📈 Performance Summary:")
                print(f"   - Best ROI: {max(rois):.4f}%")
                print(f"   - Worst ROI: {min(rois):.4f}%")
                print(f"   - Average ROI: {sum(rois)/len(rois):.4f}%")
                print(f"   - Total configurations: {len(results.items)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Place the main execution logic here
    pass 