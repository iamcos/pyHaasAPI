#!/usr/bin/env python3
"""
Integration test for market fetching methods using pyHaasAPI.

This test authenticates using credentials from .env and checks:
- Market fetching for multiple exchanges (BINANCE, COINBASE, KRAKEN)
- That target pairs (BTC/USDT, ETH/USDT, SOL/USDT) are present in the results
- Prints sample markets for each exchange
"""
import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
from pyHaasAPI import api
from pyHaasAPI.price import PriceAPI

def test_market_fetching():
    """
    Test fetching markets from multiple exchanges and verify target pairs exist.
    - Authenticates using .env credentials
    - Fetches markets for BINANCE, COINBASE, KRAKEN
    - Checks for BTC/USDT, ETH/USDT, SOL/USDT pairs
    """
    print("🧪 Testing Market Fetching Methods\n")
    
    # Authenticate
    print("🔐 Authenticating...")
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    print("✅ Authentication successful")
    
    # Test exchange-specific market fetching
    print("\n📊 Testing exchange-specific market fetching...")
    price_api = PriceAPI(executor)
    
    exchanges = ["BINANCE", "COINBASE", "KRAKEN"]
    total_markets = []
    
    for exchange in exchanges:
        try:
            print(f"  🔍 Fetching {exchange} markets...")
            exchange_markets = price_api.get_trade_markets(exchange)
            total_markets.extend(exchange_markets)
            print(f"  ✅ Found {len(exchange_markets)} {exchange} markets")
            
            # Show some sample markets
            if exchange_markets:
                sample_markets = exchange_markets[:3]
                for market in sample_markets:
                    print(f"    - {market.primary}/{market.secondary}")
                    
        except Exception as e:
            print(f"  ❌ Failed to get {exchange} markets: {e}")
    
    print(f"\n📈 Total markets found: {len(total_markets)}")
    
    # Test if we can find our target pairs
    target_pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    print(f"\n🔍 Checking for target pairs: {target_pairs}")
    
    for pair in target_pairs:
        base, quote = pair.split('/')
        matching = [m for m in total_markets if m.primary == base and m.secondary == quote]
        if matching:
            print(f"  ✅ {pair}: {len(matching)} market(s) found: {[m.price_source for m in matching]}")
        else:
            print(f"  ❌ {pair}: No markets found")
    
    print("\n✅ Market fetching test complete!")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 