#!/usr/bin/env python3
"""
Standalone market data test with retries and longer delays
"""
import time
from pyHaasAPI import api

def test_market_data_with_retries():
    """Test market data endpoints with retries and delays"""
    print("🧪 Standalone Market Data Test with Retries\n")
    
    # Authenticate with retries
    print("🔐 Authenticating...")
    executor = None
    for auth_attempt in range(3):
        try:
            executor = api.RequestsExecutor(
                host="127.0.0.1",
                port=8090,
                state=api.Guest()
            ).authenticate(
                email="your_email@example.com",
                password="your_password"
            )
            print("✅ Authentication successful")
            break
        except Exception as e:
            print(f"  ❌ Authentication attempt {auth_attempt + 1} failed: {e}")
            if auth_attempt < 2:
                print("  ⏳ Waiting 120 seconds before retry...")
                time.sleep(120)
            else:
                print("  💥 Authentication failed after all attempts")
                return
    
    if not executor:
        print("❌ No authenticated executor available")
        return
    
    # Get markets with retries
    print("\n📊 Getting markets...")
    markets = None
    for market_attempt in range(3):
        try:
            markets = api.get_all_markets(executor)
            if markets:
                print(f"✅ Got {len(markets)} markets")
                break
            else:
                print("  ⚠️ No markets returned")
        except Exception as e:
            print(f"  ❌ Market fetch attempt {market_attempt + 1} failed: {e}")
            if market_attempt < 2:
                print("  ⏳ Waiting 120 seconds before retry...")
                time.sleep(120)
            else:
                print("  💥 Market fetch failed after all attempts")
                return
    
    if not markets:
        print("❌ No markets available")
        return
    
    market = markets[0]
    market_symbol = f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
    print(f"✅ Using market: {market_symbol}")
    
    # Test functions with retries
    test_functions = [
        ("get_market_price", lambda: api.get_market_price(executor, market_symbol)),
        ("get_order_book", lambda: api.get_order_book(executor, market_symbol, depth=10)),
        ("get_last_trades", lambda: api.get_last_trades(executor, market_symbol, limit=50)),
        ("get_market_snapshot", lambda: api.get_market_snapshot(executor, market_symbol))
    ]
    
    for func_name, func_call in test_functions:
        print(f"\n🔍 Testing {func_name}...")
        success = False
        
        for attempt in range(3):
            try:
                result = func_call()
                print(f"  ✅ {func_name} SUCCESS on attempt {attempt + 1}")
                print(f"  📊 Result type: {type(result).__name__}")
                if hasattr(result, '__len__'):
                    print(f"  📊 Result length: {len(result)}")
                success = True
                break
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ {func_name} FAILED on attempt {attempt + 1}: {error_msg}")
                
                # Skip retries for unsupported channels
                if "not supported" in error_msg.lower() or "channel" in error_msg.lower():
                    print(f"  ⚠️ {func_name} appears to be unsupported by the server")
                    break
                
                if attempt < 2:  # Not the last attempt
                    print(f"  ⏳ Waiting 5 seconds before retry...")
                    time.sleep(5)
                else:
                    print(f"  💥 {func_name} FAILED after all attempts")
        
        if success:
            print(f"  🎉 {func_name} completed successfully!")
        else:
            print(f"  💀 {func_name} failed after all retries")
    
    print("\n🏁 Market data test completed!")

if __name__ == "__main__":
    test_market_data_with_retries() 