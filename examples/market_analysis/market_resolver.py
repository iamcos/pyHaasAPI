#!/usr/bin/env python3
"""
Market Resolver - Handle different exchange naming schemes and contract types
This module provides functionality to resolve trading pairs across different exchanges
and handle various contract types (Spot, Perpetual, Futures, etc.)
"""

import requests
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ContractType(Enum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    FUTURES = "FUTURES"
    MARGIN = "MARGIN"

@dataclass
class MarketInfo:
    exchange: str
    base_asset: str
    quote_asset: str
    contract_type: ContractType
    market_tag: str
    display_name: str
    is_active: bool

class MarketResolver:
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.session = requests.Session()
        self._market_cache = {}
        
    def get_all_markets(self) -> List[Dict]:
        """Get all available markets from HaasOnline"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_all_markets")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data", [])
            return []
        except Exception as e:
            print(f"Error getting markets: {e}")
            return []
    
    def parse_market_info(self, market_data: Dict) -> Optional[MarketInfo]:
        """Parse market data into MarketInfo object"""
        try:
            # Extract market tag (this is the key identifier)
            market_tag = market_data.get("market_tag") or market_data.get("tag") or market_data.get("id")
            if not market_tag:
                return None
            
            # Parse exchange from market tag (usually first part)
            parts = market_tag.split("_")
            if len(parts) < 3:
                return None
                
            exchange = parts[0]
            base_asset = parts[1]
            quote_asset = parts[2]
            
            # Determine contract type from market tag or additional info
            contract_type = self._determine_contract_type(market_tag, market_data)
            
            # Create display name
            display_name = f"{base_asset}/{quote_asset}"
            if contract_type != ContractType.SPOT:
                display_name += f" ({contract_type.value})"
            
            return MarketInfo(
                exchange=exchange,
                base_asset=base_asset,
                quote_asset=quote_asset,
                contract_type=contract_type,
                market_tag=market_tag,
                display_name=display_name,
                is_active=market_data.get("is_active", True)
            )
        except Exception as e:
            print(f"Error parsing market info: {e}")
            return None
    
    def _determine_contract_type(self, market_tag: str, market_data: Dict) -> ContractType:
        """Determine contract type from market tag and data"""
        market_tag_lower = market_tag.lower()
        
        # Check for perpetual indicators
        if any(indicator in market_tag_lower for indicator in ['perp', 'perpetual', 'perm']):
            return ContractType.PERPETUAL
        
        # Check for futures indicators
        if any(indicator in market_tag_lower for indicator in ['fut', 'future', 'futures']):
            return ContractType.FUTURES
        
        # Check for margin indicators
        if any(indicator in market_tag_lower for indicator in ['margin', 'cross', 'isolated']):
            return ContractType.MARGIN
        
        # Check market data for additional info
        market_type = market_data.get("type", "").lower()
        if "perpetual" in market_type:
            return ContractType.PERPETUAL
        elif "futures" in market_type:
            return ContractType.FUTURES
        elif "margin" in market_type:
            return ContractType.MARGIN
        
        # Default to SPOT if no indicators found
        return ContractType.SPOT
    
    def find_markets_for_assets(self, assets: List[str], quote_asset: str = "USDT", 
                               preferred_contract_type: ContractType = ContractType.PERPETUAL,
                               exchange_filter: Optional[str] = None) -> Dict[str, List[MarketInfo]]:
        """Find markets for given assets with specified quote asset"""
        print(f"🔍 Searching for markets: {assets} paired with {quote_asset}")
        
        all_markets = self.get_all_markets()
        if not all_markets:
            print("❌ No markets found")
            return {}
        
        print(f"📊 Found {len(all_markets)} total markets")
        
        results = {}
        
        for asset in assets:
            asset_upper = asset.upper()
            matching_markets = []
            
            for market_data in all_markets:
                market_info = self.parse_market_info(market_data)
                if not market_info:
                    continue
                
                # Check if this market matches our criteria
                if (market_info.base_asset.upper() == asset_upper and 
                    market_info.quote_asset.upper() == quote_asset.upper()):
                    
                    # Apply exchange filter if specified
                    if exchange_filter and market_info.exchange.upper() != exchange_filter.upper():
                        continue
                    
                    matching_markets.append(market_info)
            
            # Sort by preferred contract type
            matching_markets.sort(key=lambda m: (
                m.contract_type != preferred_contract_type,  # Preferred type first
                m.exchange,  # Then by exchange
                m.market_tag  # Then by market tag
            ))
            
            results[asset] = matching_markets
        
        return results
    
    def get_best_market_for_asset(self, asset: str, quote_asset: str = "USDT",
                                 preferred_contract_type: ContractType = ContractType.PERPETUAL,
                                 exchange_filter: Optional[str] = "BINANCE") -> Optional[MarketInfo]:
        """Get the best market for a single asset"""
        markets = self.find_markets_for_assets([asset], quote_asset, preferred_contract_type, exchange_filter)
        asset_markets = markets.get(asset, [])
        
        if not asset_markets:
            return None
        
        return asset_markets[0]  # Return the best match (first after sorting)
    
    def resolve_market_tag_safely(self, base_asset: str, quote_asset: str = "USDT",
                                 exchange: str = "BINANCE", 
                                 contract_type: ContractType = ContractType.PERPETUAL) -> Optional[str]:
        """Safely resolve market tag, handling various naming schemes"""
        
        # First, try to find exact match from available markets
        best_market = self.get_best_market_for_asset(base_asset, quote_asset, contract_type, exchange)
        if best_market:
            return best_market.market_tag
        
        # If no exact match, try common naming patterns
        common_patterns = [
            f"{exchange}_{base_asset}_{quote_asset}_",  # BINANCE_BTC_USDT_
            f"{exchange}_{base_asset}_{quote_asset}",   # BINANCE_BTC_USDT
            f"{exchange}_{base_asset}{quote_asset}_",   # BINANCE_BTCUSDT_
            f"{exchange}_{base_asset}{quote_asset}",    # BINANCE_BTCUSDT
        ]
        
        # Add contract type suffixes if not SPOT
        if contract_type != ContractType.SPOT:
            extended_patterns = []
            for pattern in common_patterns:
                extended_patterns.extend([
                    f"{pattern}PERP",
                    f"{pattern}PERPETUAL", 
                    f"{pattern}PERM",
                    f"{pattern}FUTURES",
                    f"{pattern}FUT",
                ])
            common_patterns.extend(extended_patterns)
        
        # Test each pattern against available markets
        all_markets = self.get_all_markets()
        available_tags = [m.get("market_tag", m.get("tag", m.get("id", ""))) for m in all_markets]
        
        for pattern in common_patterns:
            if pattern in available_tags:
                return pattern
        
        print(f"⚠️  Could not resolve market tag for {base_asset}/{quote_asset} on {exchange}")
        return None
    
    def print_market_analysis(self, assets: List[str], quote_asset: str = "USDT"):
        """Print detailed analysis of available markets for assets"""
        print(f"\n{'='*80}")
        print(f"MARKET ANALYSIS FOR {quote_asset} PAIRS")
        print(f"{'='*80}")
        
        results = self.find_markets_for_assets(assets, quote_asset)
        
        for asset in assets:
            markets = results.get(asset, [])
            print(f"\n🪙 {asset}/{quote_asset}:")
            
            if not markets:
                print(f"  ❌ No markets found")
                continue
            
            print(f"  ✅ Found {len(markets)} markets:")
            
            for i, market in enumerate(markets):
                status = "🟢" if market.is_active else "🔴"
                preferred = "⭐" if i == 0 else "  "
                print(f"    {preferred} {status} {market.exchange}: {market.market_tag} ({market.contract_type.value})")
    
    def validate_market_tags(self, market_tags: List[str]) -> Dict[str, bool]:
        """Validate that market tags exist and are accessible"""
        print(f"\n🔍 Validating {len(market_tags)} market tags...")
        
        all_markets = self.get_all_markets()
        available_tags = set()
        
        for market_data in all_markets:
            tag = market_data.get("market_tag") or market_data.get("tag") or market_data.get("id")
            if tag:
                available_tags.add(tag)
        
        results = {}
        for tag in market_tags:
            is_valid = tag in available_tags
            status = "✅" if is_valid else "❌"
            print(f"  {status} {tag}")
            results[tag] = is_valid
        
        return results

def main():
    """Test the market resolver"""
    MCP_SERVER_URL = "http://127.0.0.1:8000"
    
    # Trading pairs from task
    TRADING_PAIRS = [
        "BTC", "ETH", "SOL", "BNB", "XRP", "APT", 
        "LTC", "BCH", "ADA", "UNI", "GALA", "TRX"
    ]
    
    resolver = MarketResolver(MCP_SERVER_URL)
    
    # Check MCP server status
    try:
        response = requests.get(f"{MCP_SERVER_URL}/status")
        if response.status_code != 200 or not response.json().get("haas_api_connected"):
            print("❌ MCP server is not running or not authenticated")
            return
    except:
        print("❌ Cannot connect to MCP server")
        return
    
    print("✅ MCP server is running and authenticated")
    
    # Analyze available markets
    resolver.print_market_analysis(TRADING_PAIRS)
    
    # Get best market tags for each asset
    print(f"\n{'='*80}")
    print("RECOMMENDED MARKET TAGS")
    print(f"{'='*80}")
    
    recommended_tags = []
    for asset in TRADING_PAIRS:
        market_tag = resolver.resolve_market_tag_safely(
            asset, 
            quote_asset="USDT",
            exchange="BINANCE",
            contract_type=ContractType.PERPETUAL
        )
        
        if market_tag:
            print(f"✅ {asset}: {market_tag}")
            recommended_tags.append(market_tag)
        else:
            print(f"❌ {asset}: Could not resolve")
    
    # Validate the recommended tags
    if recommended_tags:
        print(f"\n{'='*80}")
        print("VALIDATION")
        print(f"{'='*80}")
        resolver.validate_market_tags(recommended_tags)

if __name__ == "__main__":
    main()