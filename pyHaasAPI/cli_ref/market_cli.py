"""
Market CLI module using v2 APIs and centralized managers.
Provides market data functionality.
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.core.logging import get_logger


class MarketCLI(EnhancedBaseCLI):
    """Market data CLI using v2 APIs and centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("market_cli")

    async def list_markets(self) -> Dict[str, Any]:
        """List all available markets"""
        try:
            self.logger.info("Listing all markets")
            
            if not self.market_api:
                return {"error": "Market API not available"}
            
            markets = await self.market_api.list_markets()
            
            return {
                "success": True,
                "markets": markets,
                "count": len(markets) if markets else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error listing markets: {e}")
            return {"error": str(e)}

    async def get_market_details(self, market_id: str) -> Dict[str, Any]:
        """Get market details"""
        try:
            self.logger.info(f"Getting market details for {market_id}")
            
            if not self.market_api:
                return {"error": "Market API not available"}
            
            market = await self.market_api.get_market_details(market_id)
            
            if market:
                return {
                    "success": True,
                    "market": market
                }
            else:
                return {
                    "success": False,
                    "error": f"Market {market_id} not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting market details: {e}")
            return {"error": str(e)}

    async def get_market_data(self, market_id: str, timeframe: str = "1h", limit: int = 100) -> Dict[str, Any]:
        """Get market data for a specific market"""
        try:
            self.logger.info(f"Getting market data for {market_id} (timeframe: {timeframe}, limit: {limit})")
            
            if not self.market_api:
                return {"error": "Market API not available"}
            
            data = await self.market_api.get_market_data(market_id, timeframe, limit)
            
            if data:
                return {
                    "success": True,
                    "market_id": market_id,
                    "timeframe": timeframe,
                    "data": data,
                    "count": len(data) if data else 0
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not retrieve data for market {market_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return {"error": str(e)}

    async def get_market_ticker(self, market_id: str) -> Dict[str, Any]:
        """Get market ticker data"""
        try:
            self.logger.info(f"Getting market ticker for {market_id}")
            
            if not self.market_api:
                return {"error": "Market API not available"}
            
            ticker = await self.market_api.get_market_ticker(market_id)
            
            if ticker:
                return {
                    "success": True,
                    "market_id": market_id,
                    "ticker": ticker
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not retrieve ticker for market {market_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting market ticker: {e}")
            return {"error": str(e)}

    def print_markets_report(self, markets_data: Dict[str, Any]):
        """Print markets report"""
        try:
            if "error" in markets_data:
                print(f"❌ Error: {markets_data['error']}")
                return
            
            markets = markets_data.get("markets", [])
            count = markets_data.get("count", 0)
            
            print("\n" + "="*80)
            print("📈 MARKETS REPORT")
            print("="*80)
            print(f"📊 Total Markets: {count}")
            print("-"*80)
            
            if markets:
                for market in markets:
                    market_id = getattr(market, 'id', 'Unknown')
                    market_name = getattr(market, 'name', 'Unknown')
                    market_type = getattr(market, 'type', 'Unknown')
                    status = getattr(market, 'status', 'Unknown')
                    
                    print(f"📈 {market_name}")
                    print(f"   ID: {market_id}")
                    print(f"   Type: {market_type}")
                    print(f"   Status: {status}")
                    print()
            else:
                print("No markets found")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing markets report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_market_details_report(self, market_data: Dict[str, Any]):
        """Print market details report"""
        try:
            if "error" in market_data:
                print(f"❌ Error: {market_data['error']}")
                return
            
            if not market_data.get("success", False):
                print(f"❌ {market_data.get('error', 'Unknown error')}")
                return
            
            market = market_data.get("market")
            if not market:
                print("❌ No market data available")
                return
            
            print("\n" + "="*80)
            print("📈 MARKET DETAILS")
            print("="*80)
            
            # Basic info
            market_id = getattr(market, 'id', 'Unknown')
            market_name = getattr(market, 'name', 'Unknown')
            market_type = getattr(market, 'type', 'Unknown')
            status = getattr(market, 'status', 'Unknown')
            
            print(f"📈 {market_name}")
            print(f"   ID: {market_id}")
            print(f"   Type: {market_type}")
            print(f"   Status: {status}")
            
            # Additional details
            if hasattr(market, 'base_currency'):
                print(f"   Base Currency: {market.base_currency}")
            if hasattr(market, 'quote_currency'):
                print(f"   Quote Currency: {market.quote_currency}")
            if hasattr(market, 'min_trade_size'):
                print(f"   Min Trade Size: {market.min_trade_size}")
            if hasattr(market, 'max_trade_size'):
                print(f"   Max Trade Size: {market.max_trade_size}")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing market details report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_market_data_report(self, data_result: Dict[str, Any]):
        """Print market data report"""
        try:
            if "error" in data_result:
                print(f"❌ Error: {data_result['error']}")
                return
            
            if not data_result.get("success", False):
                print(f"❌ {data_result.get('error', 'Unknown error')}")
                return
            
            market_id = data_result.get("market_id", "Unknown")
            timeframe = data_result.get("timeframe", "Unknown")
            data = data_result.get("data", [])
            count = data_result.get("count", 0)
            
            print("\n" + "="*80)
            print("📊 MARKET DATA REPORT")
            print("="*80)
            print(f"📈 Market: {market_id}")
            print(f"⏰ Timeframe: {timeframe}")
            print(f"📊 Data Points: {count}")
            print("-"*80)
            
            if data:
                # Show first few data points
                for i, point in enumerate(data[:5]):
                    timestamp = getattr(point, 'timestamp', 'Unknown')
                    open_price = getattr(point, 'open', 0)
                    high_price = getattr(point, 'high', 0)
                    low_price = getattr(point, 'low', 0)
                    close_price = getattr(point, 'close', 0)
                    volume = getattr(point, 'volume', 0)
                    
                    print(f"📊 Point {i+1}:")
                    print(f"   Time: {timestamp}")
                    print(f"   OHLC: {open_price:.4f} / {high_price:.4f} / {low_price:.4f} / {close_price:.4f}")
                    print(f"   Volume: {volume}")
                    print()
                
                if count > 5:
                    print(f"... and {count - 5} more data points")
            else:
                print("No data available")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing market data report: {e}")
            print(f"❌ Error generating report: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Market Data CLI")
    parser.add_argument("--list", action="store_true", help="List all markets")
    parser.add_argument("--details", type=str, help="Get market details by ID")
    parser.add_argument("--data", type=str, help="Get market data by ID")
    parser.add_argument("--ticker", type=str, help="Get market ticker by ID")
    parser.add_argument("--timeframe", type=str, default="1h", help="Timeframe for market data (default: 1h)")
    parser.add_argument("--limit", type=int, default=100, help="Limit for market data (default: 100)")
    
    args = parser.parse_args()
    
    cli = MarketCLI()
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        if args.list:
            # List markets
            markets_data = await cli.list_markets()
            cli.print_markets_report(markets_data)
            
        elif args.details:
            # Get market details
            market_data = await cli.get_market_details(args.details)
            cli.print_market_details_report(market_data)
            
        elif args.data:
            # Get market data
            data_result = await cli.get_market_data(args.data, args.timeframe, args.limit)
            cli.print_market_data_report(data_result)
            
        elif args.ticker:
            # Get market ticker
            ticker_result = await cli.get_market_ticker(args.ticker)
            if ticker_result.get("success"):
                print(f"📈 Market {args.ticker} Ticker: {ticker_result['ticker']}")
            else:
                print(f"❌ {ticker_result.get('error', 'Unknown error')}")
                
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())





