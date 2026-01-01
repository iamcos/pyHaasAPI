"""
Market Discovery System

This module provides comprehensive market discovery and classification
functionality for HaasOnline trading operations, supporting multiple
exchanges and market types with intelligent caching and filtering.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from ..model import CloudMarket

logger = logging.getLogger(__name__)

class MarketType(Enum):
    """Market type classification"""
    SPOT = "spot"
    PERPETUAL = "perpetual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    UNKNOWN = "unknown"

@dataclass
class MarketInfo:
    """Information about a trading market"""
    market_tag: str
    exchange: str
    base_asset: str
    quote_asset: str
    market_type: MarketType
    is_active: bool = True
    min_trade_amount: float = 0.0
    max_trade_amount: float = 0.0
    price_decimals: int = 8
    amount_decimals: int = 8
    maker_fee: float = 0.0
    taker_fee: float = 0.0
    
    @property
    def symbol(self) -> str:
        """Get trading symbol (BASE/QUOTE)"""
        return f"{self.base_asset}/{self.quote_asset}"
    
    @property
    def is_futures(self) -> bool:
        """Check if this is a futures market"""
        return self.market_type in [MarketType.PERPETUAL, MarketType.QUARTERLY, MarketType.MONTHLY]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'market_tag': self.market_tag,
            'exchange': self.exchange,
            'base_asset': self.base_asset,
            'quote_asset': self.quote_asset,
            'market_type': self.market_type.value,
            'symbol': self.symbol,
            'is_active': self.is_active,
            'is_futures': self.is_futures,
            'min_trade_amount': self.min_trade_amount,
            'max_trade_amount': self.max_trade_amount,
            'price_decimals': self.price_decimals,
            'amount_decimals': self.amount_decimals,
            'maker_fee': self.maker_fee,
            'taker_fee': self.taker_fee
        }

class MarketDiscovery:
    """Discovers and classifies trading markets across exchanges"""
    
    def __init__(self, executor=None, cache_duration: int = 3600):
        """
        Initialize market discovery.
        
        Args:
            executor: HaasOnline API executor (optional)
            cache_duration: Cache duration in seconds (default: 1 hour)
        """
        self.executor = executor
        self.cache_duration = cache_duration
        
        # Market cache
        self._market_cache: Dict[str, List[MarketInfo]] = {}
        self._cache_timestamp: Dict[str, float] = {}
        
        # Exchange configurations
        self._exchange_configs = self._initialize_exchange_configs()
    
    def _initialize_exchange_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize exchange-specific configurations"""
        return {
            'BINANCE': {
                'spot_suffix': '',
                'futures_suffix': '',
                'supports_perpetual': True,
                'supports_quarterly': False
            },
            'BINANCEFUTURES': {
                'spot_suffix': '',
                'futures_suffix': '_PERPETUAL',
                'supports_perpetual': True,
                'supports_quarterly': False
            },
            'BINANCEQUARTERLY': {
                'spot_suffix': '',
                'futures_suffix': '_PERPETUAL',
                'supports_perpetual': True,
                'supports_quarterly': True
            },
            'BYBIT': {
                'spot_suffix': '',
                'futures_suffix': '_PERPETUAL',
                'supports_perpetual': True,
                'supports_quarterly': False
            },
            'OKEX': {
                'spot_suffix': '',
                'futures_suffix': '_PERPETUAL',
                'supports_perpetual': True,
                'supports_quarterly': True
            }
        }
    
    def discover_markets(self, exchange: str, market_types: List[MarketType] = None) -> List[MarketInfo]:
        """
        Discover markets for a specific exchange.
        
        Args:
            exchange: Exchange name (e.g., "BINANCEFUTURES")
            market_types: List of market types to discover (None for all)
            
        Returns:
            List of discovered market information
        """
        # Check cache first
        cache_key = f"{exchange}_{market_types}"
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached markets for {exchange}")
            return self._market_cache[cache_key]
        
        logger.info(f"Discovering markets for {exchange}...")
        
        try:
            # Get all markets from the exchange
            markets = self._fetch_exchange_markets(exchange)
            discovered_markets = []
            
            for market in markets:
                market_info = self._classify_market(market, exchange)
                if market_info:
                    # Filter by market types if specified
                    if market_types is None or market_info.market_type in market_types:
                        discovered_markets.append(market_info)
            
            # Cache the results
            self._market_cache[cache_key] = discovered_markets
            self._cache_timestamp[cache_key] = time.time()
            
            logger.info(f"Discovered {len(discovered_markets)} markets for {exchange}")
            return discovered_markets
            
        except Exception as e:
            logger.error(f"Failed to discover markets for {exchange}: {e}")
            # Return cached data if available, otherwise empty list
            return self._market_cache.get(cache_key, [])
    
    def discover_perpetual_markets(self, exchange: str) -> List[MarketInfo]:
        """
        Discover perpetual trading markets for a specific exchange.
        
        Args:
            exchange: Exchange name
            
        Returns:
            List of perpetual market information
        """
        return self.discover_markets(exchange, [MarketType.PERPETUAL])
    
    def discover_spot_markets(self, exchange: str) -> List[MarketInfo]:
        """
        Discover spot trading markets for a specific exchange.
        
        Args:
            exchange: Exchange name
            
        Returns:
            List of spot market information
        """
        return self.discover_markets(exchange, [MarketType.SPOT])
    
    def discover_all_markets(self, exchanges: List[str] = None) -> Dict[str, List[MarketInfo]]:
        """
        Discover markets across multiple exchanges.
        
        Args:
            exchanges: List of exchange names (uses default if None)
            
        Returns:
            Dictionary mapping exchange names to market lists
        """
        if exchanges is None:
            exchanges = ["BINANCEFUTURES", "BINANCEQUARTERLY", "BYBIT"]
        
        all_markets = {}
        
        for exchange in exchanges:
            try:
                markets = self.discover_markets(exchange)
                all_markets[exchange] = markets
            except Exception as e:
                logger.error(f"Failed to discover markets for {exchange}: {e}")
                all_markets[exchange] = []
        
        return all_markets
    
    def find_markets_by_asset(self, base_asset: str, exchanges: List[str] = None) -> List[MarketInfo]:
        """
        Find all markets for a specific base asset across exchanges.
        
        Args:
            base_asset: Base asset symbol (e.g., "BTC")
            exchanges: List of exchanges to search (None for all)
            
        Returns:
            List of markets for the specified asset
        """
        all_markets = self.discover_all_markets(exchanges)
        asset_markets = []
        
        for exchange, markets in all_markets.items():
            for market in markets:
                if market.base_asset.upper() == base_asset.upper():
                    asset_markets.append(market)
        
        return asset_markets
    
    def find_markets_by_symbol(self, symbol: str, exchanges: List[str] = None) -> List[MarketInfo]:
        """
        Find all markets for a specific trading symbol across exchanges.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            exchanges: List of exchanges to search (None for all)
            
        Returns:
            List of markets for the specified symbol
        """
        if '/' not in symbol:
            raise ValueError("Symbol must be in format 'BASE/QUOTE' (e.g., 'BTC/USDT')")
        
        base_asset, quote_asset = symbol.split('/')
        all_markets = self.discover_all_markets(exchanges)
        symbol_markets = []
        
        for exchange, markets in all_markets.items():
            for market in markets:
                if (market.base_asset.upper() == base_asset.upper() and 
                    market.quote_asset.upper() == quote_asset.upper()):
                    symbol_markets.append(market)
        
        return symbol_markets
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of supported exchanges"""
        return list(self._exchange_configs.keys())
    
    def get_exchange_info(self, exchange: str) -> Dict[str, Any]:
        """Get information about a specific exchange"""
        config = self._exchange_configs.get(exchange, {})
        
        return {
            'exchange': exchange,
            'supports_spot': True,  # Assume all exchanges support spot
            'supports_perpetual': config.get('supports_perpetual', False),
            'supports_quarterly': config.get('supports_quarterly', False),
            'configuration': config
        }
    
    def filter_markets(self, markets: List[MarketInfo], **filters) -> List[MarketInfo]:
        """
        Filter markets based on various criteria.
        
        Args:
            markets: List of markets to filter
            **filters: Filter criteria (base_assets, quote_assets, market_types, etc.)
            
        Returns:
            Filtered list of markets
        """
        filtered = markets
        
        # Filter by base assets
        if 'base_assets' in filters:
            base_assets = [asset.upper() for asset in filters['base_assets']]
            filtered = [m for m in filtered if m.base_asset.upper() in base_assets]
        
        # Filter by quote assets
        if 'quote_assets' in filters:
            quote_assets = [asset.upper() for asset in filters['quote_assets']]
            filtered = [m for m in filtered if m.quote_asset.upper() in quote_assets]
        
        # Filter by market types
        if 'market_types' in filters:
            market_types = filters['market_types']
            if not isinstance(market_types, list):
                market_types = [market_types]
            filtered = [m for m in filtered if m.market_type in market_types]
        
        # Filter by active status
        if 'active_only' in filters and filters['active_only']:
            filtered = [m for m in filtered if m.is_active]
        
        # Filter by minimum trade amount
        if 'min_trade_amount' in filters:
            min_amount = filters['min_trade_amount']
            filtered = [m for m in filtered if m.min_trade_amount <= min_amount]
        
        return filtered
    
    def get_market_summary(self, markets: Dict[str, List[MarketInfo]]) -> Dict[str, Any]:
        """Get summary statistics of discovered markets"""
        total_markets = sum(len(market_list) for market_list in markets.values())
        
        # Count by market type
        type_counts = {}
        asset_counts = {}
        exchange_counts = {}
        
        for exchange, market_list in markets.items():
            exchange_counts[exchange] = len(market_list)
            
            for market in market_list:
                market_type = market.market_type.value
                type_counts[market_type] = type_counts.get(market_type, 0) + 1
                
                base_asset = market.base_asset
                asset_counts[base_asset] = asset_counts.get(base_asset, 0) + 1
        
        return {
            'total_markets': total_markets,
            'exchanges': list(markets.keys()),
            'markets_per_exchange': exchange_counts,
            'market_types': type_counts,
            'top_assets': sorted(asset_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'unique_base_assets': len(asset_counts),
            'discovery_timestamp': time.time()
        }
    
    def _fetch_exchange_markets(self, exchange: str) -> List[CloudMarket]:
        """
        Fetch markets from exchange API.
        
        Args:
            exchange: Exchange name
            
        Returns:
            List of CloudMarket objects
        """
        if not self.executor:
            # Return mock data for testing
            logger.warning("No executor provided, returning mock market data")
            return self._get_mock_markets(exchange)
        
        try:
            # Use HaasOnline API to get markets
            from ..price import PriceAPI
            price_api = PriceAPI(self.executor)
            return price_api.get_trade_markets(exchange)
            
        except Exception as e:
            logger.error(f"Failed to fetch markets from {exchange}: {e}")
            return []
    
    def _classify_market(self, market: CloudMarket, exchange: str) -> Optional[MarketInfo]:
        """
        Classify a market and extract information.
        
        Args:
            market: CloudMarket object
            exchange: Exchange name
            
        Returns:
            MarketInfo object or None if classification fails
        """
        try:
            # Get exchange configuration
            exchange_config = self._exchange_configs.get(exchange, {})
            
            # Determine market type based on exchange and market properties
            market_type = self._determine_market_type(market, exchange, exchange_config)
            
            # Format market tag
            market_tag = self._format_market_tag(market, exchange, market_type)
            
            # Extract market details
            return MarketInfo(
                market_tag=market_tag,
                exchange=exchange,
                base_asset=getattr(market, 'primary', getattr(market, 'primary_currency', 'UNKNOWN')),
                quote_asset=getattr(market, 'secondary', getattr(market, 'secondary_currency', 'UNKNOWN')),
                market_type=market_type,
                is_active=getattr(market, 'is_open', True),
                min_trade_amount=getattr(market, 'minimum_trade_amount', 0.0),
                max_trade_amount=getattr(market, 'maximum_trade_amount', 0.0),
                price_decimals=getattr(market, 'price_decimals', 8),
                amount_decimals=getattr(market, 'amount_decimals', 8),
                maker_fee=getattr(market, 'makers_fee', 0.0),
                taker_fee=getattr(market, 'takers_fee', 0.0)
            )
            
        except Exception as e:
            logger.warning(f"Failed to classify market {market}: {e}")
            return None
    
    def _determine_market_type(self, market: CloudMarket, exchange: str, config: Dict[str, Any]) -> MarketType:
        """Determine market type based on exchange and market properties"""
        exchange_upper = exchange.upper()
        
        # Check for futures exchanges
        if "FUTURES" in exchange_upper or "QUARTERLY" in exchange_upper:
            # Check for specific contract types
            contract_type = getattr(market, 'contract_type', None)
            if contract_type:
                if "PERPETUAL" in contract_type.upper():
                    return MarketType.PERPETUAL
                elif "QUARTERLY" in contract_type.upper():
                    return MarketType.QUARTERLY
                elif "MONTHLY" in contract_type.upper():
                    return MarketType.MONTHLY
            
            # Default to perpetual for futures exchanges
            return MarketType.PERPETUAL
        
        # Default to spot
        return MarketType.SPOT
    
    def _format_market_tag(self, market: CloudMarket, exchange: str, market_type: MarketType) -> str:
        """Format market tag based on exchange conventions"""
        base = getattr(market, 'primary', getattr(market, 'primary_currency', 'UNKNOWN'))
        quote = getattr(market, 'secondary', getattr(market, 'secondary_currency', 'UNKNOWN'))
        
        # Basic format
        market_tag = f"{exchange.upper()}_{base.upper()}_{quote.upper()}"
        
        # Add suffix based on market type
        if market_type == MarketType.PERPETUAL:
            market_tag += "_PERPETUAL"
        elif market_type == MarketType.QUARTERLY:
            market_tag += "_QUARTERLY"
        elif market_type == MarketType.MONTHLY:
            market_tag += "_MONTHLY"
        else:
            market_tag += "_"  # Spot markets typically end with underscore
        
        return market_tag
    
    def _get_mock_markets(self, exchange: str) -> List[CloudMarket]:
        """Generate mock market data for testing"""
        mock_markets = []
        
        # Common trading pairs
        pairs = [
            ("BTC", "USDT"), ("ETH", "USDT"), ("BNB", "USDT"),
            ("ADA", "USDT"), ("SOL", "USDT"), ("DOT", "USDT")
        ]
        
        for base, quote in pairs:
            # Create mock CloudMarket object
            mock_market = type('MockCloudMarket', (), {
                'primary': base,
                'secondary': quote,
                'primary_currency': base,
                'secondary_currency': quote,
                'is_open': True,
                'minimum_trade_amount': 0.001,
                'maximum_trade_amount': 1000000.0,
                'price_decimals': 8,
                'amount_decimals': 8,
                'makers_fee': 0.001,
                'takers_fee': 0.001,
                'contract_type': 'PERPETUAL' if 'FUTURES' in exchange.upper() else None
            })()
            
            mock_markets.append(mock_market)
        
        return mock_markets
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_timestamp:
            return False
        
        return (time.time() - self._cache_timestamp[cache_key]) < self.cache_duration
    
    def clear_cache(self, exchange: str = None):
        """
        Clear market cache.
        
        Args:
            exchange: Specific exchange to clear (None for all)
        """
        if exchange:
            # Clear cache for specific exchange
            keys_to_remove = [key for key in self._market_cache.keys() if key.startswith(exchange)]
            for key in keys_to_remove:
                self._market_cache.pop(key, None)
                self._cache_timestamp.pop(key, None)
        else:
            # Clear all cache
            self._market_cache.clear()
            self._cache_timestamp.clear()
        
        logger.info(f"Cleared market cache for {exchange or 'all exchanges'}")

# Convenience functions
def discover_perpetual_markets(exchange: str, executor=None) -> List[MarketInfo]:
    """
    Convenience function to discover perpetual markets.
    
    Args:
        exchange: Exchange name
        executor: HaasOnline API executor
        
    Returns:
        List of perpetual markets
    """
    discovery = MarketDiscovery(executor)
    return discovery.discover_perpetual_markets(exchange)

def find_asset_markets(base_asset: str, exchanges: List[str] = None, executor=None) -> List[MarketInfo]:
    """
    Convenience function to find markets for a specific asset.
    
    Args:
        base_asset: Base asset symbol
        exchanges: List of exchanges to search
        executor: HaasOnline API executor
        
    Returns:
        List of markets for the asset
    """
    discovery = MarketDiscovery(executor)
    return discovery.find_markets_by_asset(base_asset, exchanges)