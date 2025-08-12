#!/usr/bin/env python3
"""
Get History Status Data

This script demonstrates how to retrieve historical data status for all markets
from the Haas API. This shows which markets have historical data available
and their current status.
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import json
from pyHaasAPI import api


def main():
    """Get and display history status data for all markets"""
    print("📊 Getting History Status Data...")
    
    # Initialize and authenticate
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    
    try:
        # Get history status for all markets
        history_status = api.get_history_status(executor)
        
        print(f"✅ Successfully retrieved history status for {len(history_status)} markets")
        print("\n📋 History Status Summary:")
        print("=" * 50)
        
        # Display summary information
        total_markets = len(history_status)
        markets_with_data = sum(1 for status in history_status.values() if status)
        markets_without_data = total_markets - markets_with_data
        
        print(f"Total markets: {total_markets}")
        print(f"Markets with historical data: {markets_with_data}")
        print(f"Markets without historical data: {markets_without_data}")
        
        # Show some examples
        print("\n🔍 Sample Markets with Historical Data:")
        print("-" * 40)
        for market, status in list(history_status.items())[:10]:
            if status:
                print(f"✅ {market}: Available")
        
        print("\n❌ Sample Markets without Historical Data:")
        print("-" * 40)
        for market, status in list(history_status.items())[:10]:
            if not status:
                print(f"❌ {market}: Not available")
        
        # Save detailed results to file
        output_file = "history_status_results.json"
        with open(output_file, 'w') as f:
            json.dump(history_status, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Show exchange breakdown
        print("\n📈 Exchange Breakdown:")
        print("-" * 30)
        exchange_stats = {}
        for market in history_status.keys():
            if '_' in market:
                exchange = market.split('_')[0]
                if exchange not in exchange_stats:
                    exchange_stats[exchange] = {'total': 0, 'available': 0}
                exchange_stats[exchange]['total'] += 1
                if history_status[market]:
                    exchange_stats[exchange]['available'] += 1
        
        for exchange, stats in sorted(exchange_stats.items()):
            percentage = (stats['available'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{exchange}: {stats['available']}/{stats['total']} ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error getting history status: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Place the main execution logic here
    pass 