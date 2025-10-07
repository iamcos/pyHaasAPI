"""
Market API module for pyHaasAPI v2

Provides comprehensive market data functionality including market discovery,
price data retrieval, and market validation. Based on the best implementations
from v1: PriceAPI class and MarketManager.
"""

import asyncio
from typing import Optional, List, Dict, Any, Set
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import MarketError, MarketNotFoundError, PriceDataError
from ...core.logging import get_logger
from ...core.field_utils import safe_get_dict_field
from ...models.market import MarketData, PriceData, CloudMarket


class MarketAPI:
    """
    Market API for managing market data and price information
    
    Provides comprehensive market data functionality including market discovery,
    price data retrieval, and market validation. Based on the best implementations
    from v1: PriceAPI class and MarketManager.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("market_api")
        self._markets_cache: Dict[str, CloudMarket] = {}
        self._price_cache: Dict[str, PriceData] = {}
    
    async def get_all_markets(self) -> List[CloudMarket]:
        """
        Get all available markets
        
        Based on the most recent v1 implementation from pyHaasAPI/price.py (lines 82-88)
        
        Returns:
            List of CloudMarket objects with all available markets
            
        Raises:
            MarketError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving all markets")
            
            # Use canonical PHP JSON endpoint only
            raw = await self.client.get_json(
                endpoint="/PriceAPI.php",
                params={"channel": "MARKETLIST"}
            )
            
            # Some endpoints return raw lists, others wrap in {Success, Data}
            markets_payload = safe_get_dict_field(raw, "Data", raw) if isinstance(raw, dict) else raw
            markets: List[CloudMarket] = []
            if isinstance(markets_payload, list):
                for market_data in markets_payload:
                    try:
                        markets.append(CloudMarket.model_validate(market_data))
                    except Exception:
                        # Fallback minimal mapping
                        price_source = (safe_get_dict_field(market_data, "price_source") or safe_get_dict_field(market_data, "PriceSource") or "")
                        primary = safe_get_dict_field(market_data, "primary") or safe_get_dict_field(market_data, "Primary") or ""
                        secondary = safe_get_dict_field(market_data, "secondary") or safe_get_dict_field(market_data, "Secondary") or ""
                        contract = safe_get_dict_field(market_data, "contract") or safe_get_dict_field(market_data, "Contract") or ""
                        market_tag = safe_get_dict_field(market_data, "market_tag") or safe_get_dict_field(market_data, "MarketTag") or f"{price_source}_{primary}_{secondary}"
                        markets.append(CloudMarket(
                            price_source=price_source,
                            primary=primary,
                            secondary=secondary,
                            contract=contract,
                            market_tag=market_tag
                        ))
            
            self.logger.debug(f"Retrieved {len(markets)} markets")
            
            # Update cache
            self._markets_cache = {f"{m.price_source}_{m.primary}_{m.secondary}": m for m in markets}
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve all markets: {e}")
            raise MarketError(f"Failed to retrieve all markets: {e}") from e
    
    async def get_all_markets_by_pricesource(self, price_source: str) -> List[CloudMarket]:
        """
        Get markets from a specific price source
        
        Args:
            price_source: Price source identifier (e.g., "BINANCE", "BYBIT")
            
        Returns:
            List of CloudMarket objects from the specified price source
            
        Raises:
            MarketError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving markets for price source: {price_source}")
            
            response = await self.client.get_json(
                endpoint="PriceAPI.php",
                params={
                    "channel": "MARKETLIST",
                    "pricesource": price_source,
                }
            )
            
            payload = safe_get_dict_field(response, "Data", response) if isinstance(response, dict) else response
            markets = [CloudMarket.model_validate(market_data) for market_data in (payload or [])]
            self.logger.debug(f"Retrieved {len(markets)} markets for {price_source}")
            return markets
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve markets for price source {price_source}: {e}")
            raise MarketError(f"Failed to retrieve markets for price source: {e}") from e
    
    async def get_unique_pricesources(self) -> Set[str]:
        """
        Get all unique price sources
        
        Returns:
            Set of unique price source identifiers
            
        Raises:
            MarketError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving unique price sources")
            
            all_markets = await self.get_all_markets()
            price_sources = set(market.price_source for market in all_markets)
            
            self.logger.debug(f"Found {len(price_sources)} unique price sources")
            return price_sources
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve unique price sources: {e}")
            raise MarketError(f"Failed to retrieve unique price sources: {e}") from e
    
    async def get_trade_markets(self, exchange_code: Optional[str] = None) -> List[CloudMarket]:
        """
        Get list of supported trading markets for a given exchange
        
        Args:
            exchange_code: Exchange code (e.g., "BINANCE", "BYBIT")
            
        Returns:
            List of CloudMarket objects for the specified exchange
            
        Raises:
            MarketError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving trade markets for exchange: {exchange_code}")
            
            # If exchange_code provided, use TRADE_MARKETS, otherwise MARKETLIST
            if exchange_code:
                response = await self.client.get_json(
                    endpoint="/PriceAPI.php",
                    params={
                        "channel": "TRADE_MARKETS",
                        "pricesource": exchange_code,
                    }
                )
                payload = safe_get_dict_field(response, "Data", response) if isinstance(response, dict) else response
            else:
                response = await self.client.get_json(
                    endpoint="/PriceAPI.php",
                    params={
                        "channel": "MARKETLIST",
                    }
                )
                payload = safe_get_dict_field(response, "Data", response) if isinstance(response, dict) else response
            
            # Convert Market objects to CloudMarket objects
            markets = []
            for market_data in (payload or []):
                # Map flexible fields to our CloudMarket model
                market = CloudMarket(
                    market=safe_get_dict_field(market_data, "Market") or safe_get_dict_field(market_data, "market") or safe_get_dict_field(market_data, "market_tag") or "",
                    exchange=safe_get_dict_field(market_data, "PriceSource") or safe_get_dict_field(market_data, "price_source") or "",
                    base_currency=safe_get_dict_field(market_data, "Primary") or safe_get_dict_field(market_data, "primary") or "",
                    quote_currency=safe_get_dict_field(market_data, "Secondary") or safe_get_dict_field(market_data, "secondary") or "",
                    is_active=bool(safe_get_dict_field(market_data, "IsActive", True)),
                    min_trade_amount=float(safe_get_dict_field(market_data, "MinTradeAmount", 0) or 0),
                    max_trade_amount=float(safe_get_dict_field(market_data, "MaxTradeAmount", 0) or 0),
                    price_precision=int(safe_get_dict_field(market_data, "PricePrecision", 2) or 2),
                    amount_precision=int(safe_get_dict_field(market_data, "AmountPrecision", 2) or 2),
                )
                markets.append(market)
            
            self.logger.debug(f"Retrieved {len(markets)} trade markets for {exchange_code}")
            return markets
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve trade markets for exchange {exchange_code}: {e}")
            raise MarketError(f"Failed to retrieve trade markets: {e}") from e
    
    async def get_price_data(self, market: str) -> PriceData:
        """
        Get real-time price data for a specific market
        
        Args:
            market: Market identifier (e.g., "BINANCEFUTURES_BTC_USDT_PERPETUAL")
            
        Returns:
            PriceData object with current price information
            
        Raises:
            MarketNotFoundError: If market is not found
            PriceDataError: If price data retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving price data for market: {market}")
            
            response = await self.client.get_json(
                endpoint="PriceAPI.php",
                params={
                    "channel": "PRICE",
                    "market": market,
                }
            )
            
            # Convert response to PriceData dataclass
            price_data = PriceData(
                timestamp=response.get('timestamp', 0),
                open=response.get('open', 0.0),
                high=response.get('high', 0.0),
                low=response.get('low', 0.0),
                close=response.get('close', 0.0),
                volume=response.get('volume', 0.0),
                bid=response.get('bid', 0.0),
                ask=response.get('ask', 0.0),
                spread=response.get('spread', 0.0),
                spread_percentage=response.get('spread_percentage', 0.0)
            )
            
            # Update cache
            self._price_cache[market] = price_data
            
            self.logger.debug(f"Retrieved price data for market: {market}")
            return price_data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve price data for market {market}: {e}")
            raise PriceDataError(f"Failed to retrieve price data: {e}") from e
    
    async def get_historical_data(
        self,
        market: str,
        interval: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get historical price data for a specific market
        
        Args:
            market: Market identifier
            interval: Data interval in minutes (default: 1)
            limit: Number of data points to retrieve (default: 100)
            
        Returns:
            Dictionary containing historical price data
            
        Raises:
            MarketNotFoundError: If market is not found
            PriceDataError: If historical data retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving historical data for market: {market}")
            
            response = await self.client.get(
                endpoint="PriceAPI.php",
                params={
                    "channel": "HISTORICAL",
                    "market": market,
                    "interval": interval,
                    "limit": limit,
                }
            )
            
            self.logger.debug(f"Retrieved historical data for market: {market}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve historical data for market {market}: {e}")
            raise PriceDataError(f"Failed to retrieve historical data: {e}") from e
    
    async def get_multiple_prices(self, markets: List[str]) -> Dict[str, PriceData]:
        """
        Get real-time price data for multiple markets
        
        Args:
            markets: List of market identifiers
            
        Returns:
            Dictionary mapping market names to PriceData objects
            
        Raises:
            PriceDataError: If price data retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving price data for {len(markets)} markets")
            
            # Use asyncio.gather for parallel requests
            tasks = [self.get_price_data(market) for market in markets]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            price_data_dict = {}
            for market, result in zip(markets, results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Failed to get price for {market}: {result}")
                    continue
                price_data_dict[market] = result
            
            self.logger.debug(f"Retrieved price data for {len(price_data_dict)} markets")
            return price_data_dict
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve multiple prices: {e}")
            raise PriceDataError(f"Failed to retrieve multiple prices: {e}") from e
    
    async def validate_market(self, market: CloudMarket) -> bool:
        """
        Validate if a market is available and accessible
        
        Args:
            market: CloudMarket object to validate
            
        Returns:
            True if market is valid, False otherwise
            
        Raises:
            MarketError: If validation fails
        """
        try:
            self.logger.debug(f"Validating market: {market.market_tag}")
            
            # Try to get price data for the market
            try:
                await self.get_price_data(market.market_tag)
                self.logger.debug(f"Market validation successful: {market.market_tag}")
                return True
            except (MarketNotFoundError, PriceDataError):
                self.logger.debug(f"Market validation failed: {market.market_tag}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to validate market {market.market_tag}: {e}")
            raise MarketError(f"Failed to validate market: {e}") from e
    
    async def get_valid_market(self, market_tag: str) -> Optional[CloudMarket]:
        """
        Get a valid market by market tag, with fallback options
        
        Args:
            market_tag: Market tag to search for
            
        Returns:
            CloudMarket object if found and valid, None otherwise
            
        Raises:
            MarketError: If search fails
        """
        try:
            self.logger.debug(f"Searching for valid market: {market_tag}")
            
            # First, try to find the exact market
            all_markets = await self.get_all_markets()
            for market in all_markets:
                if market.market_tag == market_tag:
                    if await self.validate_market(market):
                        self.logger.debug(f"Found valid market: {market_tag}")
                        return market
                    else:
                        self.logger.warning(f"Market found but not valid: {market_tag}")
            
            # If not found, try to find similar markets
            self.logger.debug(f"Exact market not found, searching for similar: {market_tag}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get valid market {market_tag}: {e}")
            raise MarketError(f"Failed to get valid market: {e}") from e
    
    # Additional utility methods based on MarketManager
    
    async def get_markets_efficiently(self, exchanges: List[str]) -> List[CloudMarket]:
        """
        Get markets efficiently for specified exchanges
        
        Args:
            exchanges: List of exchange codes (e.g., ["BINANCE", "BYBIT"])
            
        Returns:
            List of CloudMarket objects from all specified exchanges
            
        Raises:
            MarketError: If retrieval fails
        """
        try:
            self.logger.info(f"Fetching markets efficiently from {exchanges}")
            all_markets = []
            
            # Use asyncio.gather for parallel requests
            tasks = [self.get_trade_markets(exchange) for exchange in exchanges]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for exchange, result in zip(exchanges, results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Failed to get {exchange} markets: {result}")
                    continue
                
                if result:
                    all_markets.extend(result)
                    self.logger.info(f"Found {len(result)} markets for {exchange}")
                else:
                    self.logger.warning(f"No markets found for {exchange}")
            
            # Update cache
            self._markets_cache = {f"{m.price_source}_{m.primary}_{m.secondary}": m for m in all_markets}
            
            self.logger.info(f"Found {len(all_markets)} total markets across exchanges")
            return all_markets
            
        except Exception as e:
            self.logger.error(f"Failed to get markets efficiently: {e}")
            raise MarketError(f"Failed to get markets efficiently: {e}") from e
    
    async def get_market_by_pair(
        self,
        exchange: str,
        primary: str,
        secondary: str
    ) -> Optional[CloudMarket]:
        """
        Get market by exchange and trading pair
        
        Args:
            exchange: Exchange code
            primary: Primary currency
            secondary: Secondary currency
            
        Returns:
            CloudMarket object if found, None otherwise
            
        Raises:
            MarketError: If search fails
        """
        try:
            self.logger.debug(f"Searching for market: {exchange}_{primary}_{secondary}")
            
            # Check cache first
            cache_key = f"{exchange}_{primary}_{secondary}"
            if cache_key in self._markets_cache:
                return self._markets_cache[cache_key]
            
            # Search in all markets
            all_markets = await self.get_all_markets()
            for market in all_markets:
                if (market.price_source == exchange and 
                    market.primary == primary and 
                    market.secondary == secondary):
                    
                    # Update cache
                    self._markets_cache[cache_key] = market
                    self.logger.debug(f"Found market: {market.market_tag}")
                    return market
            
            self.logger.debug(f"Market not found: {exchange}_{primary}_{secondary}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get market by pair {exchange}_{primary}_{secondary}: {e}")
            raise MarketError(f"Failed to get market by pair: {e}") from e
    
    async def find_trading_pairs(
        self,
        markets: List[CloudMarket],
        pairs: List[str] = None
    ) -> Dict[str, List[CloudMarket]]:
        """
        Find trading pairs in a list of markets
        
        Args:
            markets: List of markets to search in
            pairs: List of trading pairs to find (e.g., ["BTC_USDT", "ETH_USDT"])
            
        Returns:
            Dictionary mapping trading pairs to lists of matching markets
            
        Raises:
            MarketError: If search fails
        """
        try:
            self.logger.debug(f"Finding trading pairs in {len(markets)} markets")
            
            if pairs is None:
                # Extract all unique pairs from markets
                pairs = list(set(f"{m.primary}_{m.secondary}" for m in markets))
            
            pair_markets = {}
            for pair in pairs:
                pair_markets[pair] = [
                    market for market in markets
                    if f"{market.primary}_{market.secondary}" == pair
                ]
            
            self.logger.debug(f"Found {len(pair_markets)} trading pairs")
            return pair_markets
            
        except Exception as e:
            self.logger.error(f"Failed to find trading pairs: {e}")
            raise MarketError(f"Failed to find trading pairs: {e}") from e
    
    async def get_market_summary(self, market: str) -> Dict[str, Any]:
        """
        Get comprehensive market summary including price data and market info
        
        Args:
            market: Market identifier
            
        Returns:
            Dictionary containing comprehensive market information
            
        Raises:
            MarketNotFoundError: If market is not found
            MarketError: If retrieval fails
        """
        try:
            self.logger.debug(f"Getting market summary for: {market}")
            
            # Get price data and market info in parallel
            price_data, market_info = await asyncio.gather(
                self.get_price_data(market),
                self.get_valid_market(market),
                return_exceptions=True
            )
            
            summary = {
                "market": market,
                "price_data": price_data if not isinstance(price_data, Exception) else None,
                "market_info": market_info if not isinstance(market_info, Exception) else None,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.debug(f"Retrieved market summary for: {market}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get market summary for {market}: {e}")
            raise MarketError(f"Failed to get market summary: {e}") from e
    
    # Cache management methods
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._markets_cache.clear()
        self._price_cache.clear()
        self.logger.debug("Cleared all market and price caches")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "markets_cached": len(self._markets_cache),
            "prices_cached": len(self._price_cache)
        }
