#!/usr/bin/env python3
"""
Price Tracker CLI for pyHaasAPI

This tool demonstrates the real-time price data functionality by fetching
current prices for various markets.
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI_v1 import api
from pyHaasAPI_v1.price import PriceAPI, PriceData

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceTracker:
    """Real-time price tracking tool"""
    
    def __init__(self):
        self.executor = None
        self.price_api = None
        
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            logger.info("🔌 Connecting to HaasOnline API...")
            
            # Initialize executor
            from pyHaasAPI_v1.api import RequestsExecutor, Guest
            haas_api = RequestsExecutor(
                host=os.getenv('API_HOST', '127.0.0.1'),
                port=int(os.getenv('API_PORT', 8090)),
                state=Guest()
            )
            
            # Authenticate
            self.executor = haas_api.authenticate(
                os.getenv('API_EMAIL'), 
                os.getenv('API_PASSWORD')
            )
            
            # Initialize price API
            self.price_api = PriceAPI(self.executor)
            
            logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_price(self, market: str) -> Dict[str, Any]:
        """Get price data for a specific market"""
        try:
            # Use the structured PriceData model
            price_data = self.price_api.get_price_data(market)
            
            return {
                'market': market,
                'timestamp': price_data.timestamp,
                'datetime': datetime.fromtimestamp(price_data.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'open': price_data.open,
                'high': price_data.high,
                'low': price_data.low,
                'close': price_data.close,
                'volume': price_data.volume,
                'bid': price_data.bid,
                'ask': price_data.ask,
                'spread': price_data.spread,
                'spread_percentage': price_data.spread_percentage
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting price for {market}: {e}")
            return None
    
    def get_multiple_prices(self, markets: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get price data for multiple markets"""
        results = {}
        for market in markets:
            price_data = self.get_price(market)
            if price_data:
                results[market] = price_data
        return results
    
    def display_price(self, price_data: Dict[str, Any]):
        """Display formatted price data"""
        if not price_data:
            return
            
        print(f"\n📊 {price_data['market']}")
        print(f"🕐 {price_data['datetime']}")
        print(f"💰 Current Price: ${price_data['close']:,.2f}")
        print(f"📈 24h High: ${price_data['high']:,.2f}")
        print(f"📉 24h Low: ${price_data['low']:,.2f}")
        print(f"📊 Volume: {price_data['volume']:,.2f}")
        print(f"💱 Bid: ${price_data['bid']:,.2f} | Ask: ${price_data['ask']:,.2f}")
        print(f"📏 Spread: ${price_data['spread']:.4f} ({price_data['spread_percentage']:.4f}%)")
    
    def track_prices(self, markets: List[str], interval: int = 30):
        """Continuously track prices for specified markets"""
        logger.info(f"🔄 Starting price tracking for {len(markets)} markets (interval: {interval}s)")
        
        try:
            while True:
                print(f"\n{'='*60}")
                print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                for market in markets:
                    price_data = self.get_price(market)
                    if price_data:
                        self.display_price(price_data)
                
                print(f"\n⏰ Next update in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n❌ Price tracking stopped by user")
    
    def run_single_price_check(self, markets: List[str]):
        """Run a single price check for specified markets"""
        logger.info(f"📊 Getting current prices for {len(markets)} markets...")
        
        for market in markets:
            price_data = self.get_price(market)
            if price_data:
                self.display_price(price_data)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time price tracker for HaasOnline markets')
    parser.add_argument('--markets', nargs='+', 
                       default=['BINANCEFUTURES_BTC_USDT_PERPETUAL', 'BINANCEFUTURES_ETH_USDT_PERPETUAL'],
                       help='Markets to track (default: BTC and ETH)')
    parser.add_argument('--track', action='store_true', 
                       help='Continuously track prices (default: single check)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Update interval in seconds for tracking mode (default: 30)')
    
    args = parser.parse_args()
    
    try:
        tracker = PriceTracker()
        
        if not tracker.connect():
            sys.exit(1)
        
        if args.track:
            tracker.track_prices(args.markets, args.interval)
        else:
            tracker.run_single_price_check(args.markets)
            
    except KeyboardInterrupt:
        logger.info("\n❌ Price tracker interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
