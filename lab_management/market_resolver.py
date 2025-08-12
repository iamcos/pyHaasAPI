#!/usr/bin/env python3
"""
Market Resolver Utility

This module provides utilities for resolving and managing trading market
information, including market tag formatting, exchange mapping, and
market validation for the lab cloning system.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ExchangeType(Enum):
    """Exchange type classification"""
    SPOT = "spot"
    FUTURES = "futures"
    QUARTERLY = "quarterly"
    OPTIONS = "options"

@dataclass
class ExchangeInfo:
    """Information about a trading exchange"""
    exchange_id: str
    exchange_name: str
    exchange_type: ExchangeType
    supported_markets: List[str]
    api_prefix: str
    is_active: bool = True

@dataclass
class MarketPattern:
    """Pattern for matching market tags"""
    pattern: str
    exchange_type: ExchangeType
    market_type: str
    example: str

class MarketResolver:
    """Resolves and validates trading market information"""
    
    def __init__(self):
        self.exchange_registry = self._initialize_exchange_registry()
        self.market_patterns = self._initialize_market_patterns()
        self.asset_aliases = self._initialize_asset_aliases()
    
    def _initialize_exchange_registry(self) -> Dict[str, ExchangeInfo]:
        """Initialize the exchange registry with known exchanges"""
        exchanges = {
            "BINANCE": ExchangeInfo(
                exchange_id="BINANCE",
                exchange_name="Binance Spot",
                exchange_type=ExchangeType.SPOT,
                supported_markets=["BTC", "ETH", "ADA", "SOL", "BNB"],
                api_prefix="BINANCE"
            ),
            "BINANCEFUTURES": ExchangeInfo(
                exchange_id="BINANCEFUTURES",
                exchange_name="Binance Futures",
                exchange_type=ExchangeType.FUTURES,
                supported_markets=["BTC", "ETH", "ADA", "SOL", "BNB", "XRP", "LTC", "BCH", "UNI", "GALA", "TRX"],
                api_prefix="BINANCEFUTURES"
            ),
            "BINANCEQUARTERLY": ExchangeInfo(
                exchange_id="BINANCEQUARTERLY",
                exchange_name="Binance Quarterly",
                exchange_type=ExchangeType.QUARTERLY,
                supported_markets=["BTC", "ETH", "ADA", "SOL", "BNB"],
                api_prefix="BINANCEQUARTERLY"
            ),
            "KRAKEN": ExchangeInfo(
                exchange_id="KRAKEN",
                exchange_name="Kraken",
                exchange_type=ExchangeType.SPOT,
                supported_markets=["BTC", "ETH", "ADA", "SOL"],
                api_prefix="KRAKEN"
            ),
            "COINBASE": ExchangeInfo(
                exchange_id="COINBASE",
                exchange_name="Coinbase Pro",
                exchange_type=ExchangeType.SPOT,
                supported_markets=["BTC", "ETH", "ADA"],
                api_prefix="COINBASE",
                is_active=False  # Disabled due to issues mentioned in docs
            )
        }
        
        return exchanges
    
    def _initialize_market_patterns(self) -> List[MarketPattern]:
        """Initialize market tag patterns for recognition"""
        patterns = [
            MarketPattern(
                pattern=r"^([A-Z]+)_([A-Z]+)_([A-Z]+)_$",
                exchange_type=ExchangeType.SPOT,
                market_type="spot",
                example="BINANCE_BTC_USDT_"
            ),
            MarketPattern(
                pattern=r"^([A-Z]+FUTURES)_([A-Z]+)_([A-Z]+)_PERPETUAL$",
                exchange_type=ExchangeType.FUTURES,
                market_type="perpetual",
                example="BINANCEFUTURES_BTC_USDT_PERPETUAL"
            ),
            MarketPattern(
                pattern=r"^([A-Z]+QUARTERLY)_([A-Z]+)_([A-Z]+)_PERPETUAL$",
                exchange_type=ExchangeType.QUARTERLY,
                market_type="perpetual",
                example="BINANCEQUARTERLY_BTC_USD_PERPETUAL"
            ),
            MarketPattern(
                pattern=r"^([A-Z]+QUARTERLY)_([A-Z]+)_([A-Z]+)_QUARTERLY$",
                exchange_type=ExchangeType.QUARTERLY,
                market_type="quarterly",
                example="BINANCEQUARTERLY_BTC_USD_QUARTERLY"
            )
        ]
        
        return patterns
    
    def _initialize_asset_aliases(self) -> Dict[str, str]:
        """Initialize asset aliases for normalization"""
        return {
            # Common aliases
            "BITCOIN": "BTC",
            "ETHEREUM": "ETH",
            "CARDANO": "ADA",
            "SOLANA": "SOL",
            "BINANCECOIN": "BNB",
            "RIPPLE": "XRP",
            "LITECOIN": "LTC",
            "BITCOINCASH": "BCH",
            "UNISWAP": "UNI",
            "GALA": "GALA",
            "TRON": "TRX",
            
            # Stablecoin aliases
            "TETHER": "USDT",
            "USDCOIN": "USDC",
            "BUSD": "BUSD",
            "DAI": "DAI"
        }
    
    def parse_market_tag(self, market_tag: str) -> Optional[Dict[str, str]]:
        """
        Parse a market tag and extract components.
        
        Args:
            market_tag: Market tag to parse (e.g., "BINANCEFUTURES_BTC_USDT_PERPETUAL")
            
        Returns:
            Dictionary with parsed components or None if parsing fails
        """
        for pattern_info in self.market_patterns:
            match = re.match(pattern_info.pattern, market_tag)
            if match:
                groups = match.groups()
                
                if len(groups) >= 3:
                    return {
                        'exchange': groups[0],
                        'base_asset': groups[1],
                        'quote_asset': groups[2],
                        'market_type': pattern_info.market_type,
                        'exchange_type': pattern_info.exchange_type.value,
                        'contract_type': groups[3] if len(groups) > 3 else None
                    }
        
        logger.warning(f"Failed to parse market tag: {market_tag}")
        return None
    
    def format_market_tag(
        self, 
        exchange: str, 
        base_asset: str, 
        quote_asset: str, 
        market_type: str = "spot"
    ) -> str:
        """
        Format a market tag from components.
        
        Args:
            exchange: Exchange identifier
            base_asset: Base asset (e.g., "BTC")
            quote_asset: Quote asset (e.g., "USDT")
            market_type: Market type ("spot", "perpetual", "quarterly")
            
        Returns:
            Formatted market tag
        """
        # Normalize assets
        base_asset = self.normalize_asset(base_asset)
        quote_asset = self.normalize_asset(quote_asset)
        
        if market_type == "spot":
            return f"{exchange}_{base_asset}_{quote_asset}_"
        elif market_type == "perpetual":
            if "FUTURES" in exchange:
                return f"{exchange}_{base_asset}_{quote_asset}_PERPETUAL"
            elif "QUARTERLY" in exchange:
                return f"{exchange}_{base_asset}_{quote_asset}_PERPETUAL"
        elif market_type == "quarterly":
            return f"{exchange}_{base_asset}_{quote_asset}_QUARTERLY"
        
        # Default to spot format
        return f"{exchange}_{base_asset}_{quote_asset}_"
    
    def normalize_asset(self, asset: str) -> str:
        """
        Normalize an asset symbol using aliases.
        
        Args:
            asset: Asset symbol to normalize
            
        Returns:
            Normalized asset symbol
        """
        asset_upper = asset.upper()
        return self.asset_aliases.get(asset_upper, asset_upper)
    
    def validate_market_tag(self, market_tag: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a market tag format.
        
        Args:
            market_tag: Market tag to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not market_tag:
            return False, "Market tag is empty"
        
        # Parse the market tag
        parsed = self.parse_market_tag(market_tag)
        if not parsed:
            return False, f"Invalid market tag format: {market_tag}"
        
        # Check if exchange is known
        exchange = parsed['exchange']
        if exchange not in self.exchange_registry:
            return False, f"Unknown exchange: {exchange}"
        
        # Check if exchange is active
        exchange_info = self.exchange_registry[exchange]
        if not exchange_info.is_active:
            return False, f"Exchange is inactive: {exchange}"
        
        # Check if assets are supported
        base_asset = parsed['base_asset']
        if base_asset not in exchange_info.supported_markets:
            return False, f"Asset {base_asset} not supported on {exchange}"
        
        return True, None
    
    def get_supported_exchanges(self, market_type: str = None) -> List[str]:
        """
        Get list of supported exchanges, optionally filtered by market type.
        
        Args:
            market_type: Optional market type filter ("spot", "futures", "quarterly")
            
        Returns:
            List of supported exchange IDs
        """
        exchanges = []
        
        for exchange_id, exchange_info in self.exchange_registry.items():
            if not exchange_info.is_active:
                continue
            
            if market_type:
                if market_type == "spot" and exchange_info.exchange_type == ExchangeType.SPOT:
                    exchanges.append(exchange_id)
                elif market_type == "futures" and exchange_info.exchange_type == ExchangeType.FUTURES:
                    exchanges.append(exchange_id)
                elif market_type == "quarterly" and exchange_info.exchange_type == ExchangeType.QUARTERLY:
                    exchanges.append(exchange_id)
            else:
                exchanges.append(exchange_id)
        
        return exchanges
    
    def get_supported_assets(self, exchange: str = None) -> Set[str]:
        """
        Get set of supported assets, optionally filtered by exchange.
        
        Args:
            exchange: Optional exchange filter
            
        Returns:
            Set of supported asset symbols
        """
        if exchange:
            if exchange in self.exchange_registry:
                return set(self.exchange_registry[exchange].supported_markets)
            else:
                return set()
        
        # Return all supported assets across all exchanges
        all_assets = set()
        for exchange_info in self.exchange_registry.values():
            if exchange_info.is_active:
                all_assets.update(exchange_info.supported_markets)
        
        return all_assets
    
    def suggest_market_tags(
        self, 
        base_assets: List[str], 
        quote_assets: List[str] = None,
        exchanges: List[str] = None,
        market_type: str = "perpetual"
    ) -> List[str]:
        """
        Suggest market tags based on criteria.
        
        Args:
            base_assets: List of base assets
            quote_assets: List of quote assets (defaults to ["USDT", "USD"])
            exchanges: List of exchanges (defaults to active exchanges)
            market_type: Market type ("spot", "perpetual", "quarterly")
            
        Returns:
            List of suggested market tags
        """
        if quote_assets is None:
            quote_assets = ["USDT", "USD"]
        
        if exchanges is None:
            exchanges = self.get_supported_exchanges(
                "futures" if market_type == "perpetual" else market_type
            )
        
        suggestions = []
        
        for exchange in exchanges:
            exchange_info = self.exchange_registry.get(exchange)
            if not exchange_info or not exchange_info.is_active:
                continue
            
            for base_asset in base_assets:
                # Check if asset is supported on this exchange
                if base_asset not in exchange_info.supported_markets:
                    continue
                
                for quote_asset in quote_assets:
                    market_tag = self.format_market_tag(
                        exchange, base_asset, quote_asset, market_type
                    )
                    
                    # Validate the generated tag
                    is_valid, _ = self.validate_market_tag(market_tag)
                    if is_valid:
                        suggestions.append(market_tag)
        
        return suggestions
    
    def filter_perpetual_markets(self, market_tags: List[str]) -> List[str]:
        """
        Filter market tags to include only perpetual markets.
        
        Args:
            market_tags: List of market tags to filter
            
        Returns:
            List of perpetual market tags
        """
        perpetual_markets = []
        
        for market_tag in market_tags:
            parsed = self.parse_market_tag(market_tag)
            if parsed and parsed['market_type'] == 'perpetual':
                perpetual_markets.append(market_tag)
        
        return perpetual_markets
    
    def group_markets_by_exchange(self, market_tags: List[str]) -> Dict[str, List[str]]:
        """
        Group market tags by exchange.
        
        Args:
            market_tags: List of market tags to group
            
        Returns:
            Dictionary mapping exchange IDs to market tag lists
        """
        grouped = {}
        
        for market_tag in market_tags:
            parsed = self.parse_market_tag(market_tag)
            if parsed:
                exchange = parsed['exchange']
                if exchange not in grouped:
                    grouped[exchange] = []
                grouped[exchange].append(market_tag)
        
        return grouped
    
    def get_market_info_summary(self) -> Dict[str, Any]:
        """Get summary of market resolver capabilities"""
        active_exchanges = [
            ex_id for ex_id, ex_info in self.exchange_registry.items() 
            if ex_info.is_active
        ]
        
        total_assets = len(self.get_supported_assets())
        
        pattern_count = len(self.market_patterns)
        alias_count = len(self.asset_aliases)
        
        return {
            'active_exchanges': active_exchanges,
            'total_exchanges': len(self.exchange_registry),
            'total_supported_assets': total_assets,
            'market_patterns': pattern_count,
            'asset_aliases': alias_count,
            'exchange_types': list(set(ex.exchange_type.value for ex in self.exchange_registry.values()))
        }

def main():
    """Test the market resolver"""
    print("Testing Market Resolver...")
    print("=" * 40)
    
    resolver = MarketResolver()
    
    # Test market tag parsing
    print("1. Testing market tag parsing:")
    test_tags = [
        "BINANCEFUTURES_BTC_USDT_PERPETUAL",
        "BINANCE_ETH_USDT_",
        "BINANCEQUARTERLY_BTC_USD_PERPETUAL",
        "INVALID_TAG_FORMAT"
    ]
    
    for tag in test_tags:
        parsed = resolver.parse_market_tag(tag)
        if parsed:
            print(f"  ✓ {tag}: {parsed['exchange']} | {parsed['base_asset']}/{parsed['quote_asset']} | {parsed['market_type']}")
        else:
            print(f"  ✗ {tag}: Failed to parse")
    
    # Test market tag formatting
    print("\n2. Testing market tag formatting:")
    format_tests = [
        ("BINANCEFUTURES", "BTC", "USDT", "perpetual"),
        ("BINANCE", "ETH", "USDT", "spot"),
        ("BINANCEQUARTERLY", "BTC", "USD", "quarterly")
    ]
    
    for exchange, base, quote, market_type in format_tests:
        formatted = resolver.format_market_tag(exchange, base, quote, market_type)
        print(f"  ✓ {exchange} {base}/{quote} ({market_type}): {formatted}")
    
    # Test market tag validation
    print("\n3. Testing market tag validation:")
    validation_tests = [
        "BINANCEFUTURES_BTC_USDT_PERPETUAL",
        "BINANCE_ETH_USDT_",
        "INVALID_EXCHANGE_BTC_USDT_",
        "BINANCEFUTURES_INVALID_USDT_PERPETUAL"
    ]
    
    for tag in validation_tests:
        is_valid, error = resolver.validate_market_tag(tag)
        status = "✓" if is_valid else "✗"
        message = "Valid" if is_valid else error
        print(f"  {status} {tag}: {message}")
    
    # Test market suggestions
    print("\n4. Testing market suggestions:")
    suggestions = resolver.suggest_market_tags(
        base_assets=["BTC", "ETH", "SOL"],
        quote_assets=["USDT"],
        market_type="perpetual"
    )
    
    print(f"  Generated {len(suggestions)} perpetual market suggestions:")
    for suggestion in suggestions[:5]:  # Show first 5
        print(f"    - {suggestion}")
    
    # Test supported exchanges and assets
    print("\n5. Testing supported exchanges and assets:")
    futures_exchanges = resolver.get_supported_exchanges("futures")
    print(f"  Futures exchanges: {futures_exchanges}")
    
    all_assets = resolver.get_supported_assets()
    print(f"  Supported assets ({len(all_assets)}): {sorted(list(all_assets))}")
    
    # Test market filtering
    print("\n6. Testing market filtering:")
    test_markets = [
        "BINANCEFUTURES_BTC_USDT_PERPETUAL",
        "BINANCE_ETH_USDT_",
        "BINANCEQUARTERLY_SOL_USD_PERPETUAL",
        "KRAKEN_BTC_USD_"
    ]
    
    perpetual_only = resolver.filter_perpetual_markets(test_markets)
    print(f"  Perpetual markets: {perpetual_only}")
    
    grouped = resolver.group_markets_by_exchange(test_markets)
    print(f"  Grouped by exchange: {grouped}")
    
    # Test summary
    print("\n7. Market resolver summary:")
    summary = resolver.get_market_info_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 40)
    print("Market resolver test completed successfully!")

if __name__ == "__main__":
    main()