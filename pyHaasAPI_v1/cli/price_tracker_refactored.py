#!/usr/bin/env python3
"""
Refactored Price Tracker CLI for pyHaasAPI

This tool demonstrates the real-time price data functionality by fetching
current prices for various markets. Refactored to use base classes.
"""

import argparse
import time
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseDirectAPICLI
from .common import add_common_arguments
from pyHaasAPI_v1.price import PriceAPI, PriceData


class PriceTrackerRefactored(BaseDirectAPICLI):
    """Refactored real-time price tracking tool using base classes"""
    
    def __init__(self):
        super().__init__()
        self.price_api = None
        
    def run(self, args) -> bool:
        """Main execution method"""
        try:
            # Connect to API
            if not self.connect():
                return False
            
            # Initialize price API
            self.price_api = PriceAPI(self.executor)
            
            if args.continuous:
                self.monitor_prices(args.markets, args.interval)
            else:
                self.track_prices(args.markets)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in price tracker: {e}")
            return False
    
    def track_prices(self, markets: List[str]):
        """Track current prices for specified markets"""
        self.logger.info("📊 Fetching current prices...")
        self.logger.info("=" * 80)
        
        for market in markets:
            try:
                price_data = self.get_price_data(market)
                if price_data:
                    self.display_price_data(market, price_data)
                else:
                    self.logger.warning(f"⚠️ Could not fetch price for {market}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error fetching price for {market}: {e}")
        
        self.logger.info("=" * 80)
    
    def monitor_prices(self, markets: List[str], interval: int):
        """Monitor prices continuously"""
        self.logger.info(f"🔄 Starting continuous price monitoring (interval: {interval}s)")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                self.logger.info(f"\n📊 Prices at {datetime.now().strftime('%H:%M:%S')}")
                self.track_prices(markets)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Price monitoring stopped")
    
    def get_price_data(self, market: str) -> PriceData:
        """Get price data for a specific market"""
        try:
            return self.price_api.get_price_data(market)
        except Exception as e:
            self.logger.error(f"❌ Error getting price data for {market}: {e}")
            return None
    
    def display_price_data(self, market: str, price_data: PriceData):
        """Display formatted price data"""
        print(f"📈 {market}")
        print(f"   💰 Price: ${price_data.close:.6f}")
        print(f"   📊 24h High: ${price_data.high:.6f}")
        print(f"   📉 24h Low: ${price_data.low:.6f}")
        print(f"   📈 Open: ${price_data.open:.6f}")
        print(f"   📊 Volume: {price_data.volume:,.2f}")
        print(f"   💱 Bid: ${price_data.bid:.6f}")
        print(f"   💱 Ask: ${price_data.ask:.6f}")
        print(f"   📏 Spread: ${price_data.spread:.6f} ({price_data.spread_percentage:.2f}%)")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Real-time price tracking tool")
    
    # Add common arguments
    add_common_arguments(parser)
    
    # Add specific arguments
    parser.add_argument('markets', nargs='*', default=['BTC_USDT_PERPETUAL'], 
                       help='Markets to track (default: BTC_USDT_PERPETUAL)')
    parser.add_argument('--continuous', action='store_true', 
                       help='Monitor prices continuously')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Interval for continuous monitoring in seconds (default: 5)')
    
    args = parser.parse_args()
    
    # Create and run tracker
    tracker = PriceTrackerRefactored()
    success = tracker.run(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
















