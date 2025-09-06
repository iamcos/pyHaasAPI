from typing import Optional, List, Set
from pydantic import BaseModel, Field
from pyHaasAPI.types import SyncExecutor, Authenticated, HaasApiError
from pyHaasAPI.model import CloudMarket
from pyHaasAPI.logger import log
import random

__all__ = ['PriceAPI', 'OrderBook', 'OrderBookEntry', 'PriceData']

class OrderBookEntry(BaseModel):
    price: float
    amount: float

class OrderBook(BaseModel):
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]


class PriceData(BaseModel):
    """Real-time price data for a market"""
    timestamp: int = Field(alias="T")  # Unix timestamp
    open: float = Field(alias="O")     # Opening price
    high: float = Field(alias="H")     # High price
    low: float = Field(alias="L")      # Low price
    close: float = Field(alias="C")    # Closing price
    volume: float = Field(alias="V")   # Volume
    bid: float = Field(alias="B")      # Best bid price
    ask: float = Field(alias="S")      # Best ask price
    
    @property
    def spread(self) -> float:
        """Calculate the bid-ask spread"""
        return self.ask - self.bid
    
    @property
    def spread_percentage(self) -> float:
        """Calculate the bid-ask spread as a percentage"""
        if self.bid > 0:
            return (self.spread / self.bid) * 100
        return 0.0

class Market(BaseModel):
    """Market data from trade markets endpoint"""
    exchange_symbol: str = Field(alias="ES")
    websocket_symbol: str = Field(alias="WS", default="")
    exchange_version: int = Field(alias="EV")
    exchange_version_string: dict = Field(alias="EVS", default_factory=dict)
    price_step_precision: float = Field(alias="PSP")
    price_decimals: int = Field(alias="PD")
    amount_step_precision: float = Field(alias="ASP")
    amount_decimals: int = Field(alias="AD")
    price_display_type: int = Field(alias="PDT")
    amount_display_type: int = Field(alias="ADT")
    maker_fee: float = Field(alias="MF")
    taker_fee: float = Field(alias="TF")
    min_trade_amount: float = Field(alias="MTA")
    min_trade_value: float = Field(alias="MTV")
    max_trade_amount: float = Field(alias="MXTA")
    max_trade_value: float = Field(alias="MXTV")
    is_open: bool = Field(alias="IO")
    is_margin: bool = Field(alias="IM")
    price_source: str = Field(alias="PS")
    primary: str = Field(alias="P")
    secondary: str = Field(alias="S")
    contract: str = Field(alias="C")

    def to_cloud_market(self) -> CloudMarket:
        """Convert to CloudMarket format"""
        return CloudMarket(
            PS=self.price_source,
            P=self.primary,
            S=self.secondary,
            C=self.contract
        )

class PriceAPI:
    """Handles all price-related API interactions"""
    
    def __init__(self, executor: SyncExecutor[Authenticated]):
        self.executor = executor

    def get_all_markets(self) -> list[CloudMarket]:
        """Retrieves information about all available markets."""
        return self.executor.execute(
            endpoint="Price",
            response_type=list[CloudMarket],
            query_params={"channel": "MARKETLIST"},
        )

    def get_all_markets_by_pricesource(self, price_source: str) -> list[CloudMarket]:
        """Retrieves information about markets from a specific price source."""
        return self.executor.execute(
            endpoint="Price",
            response_type=list[CloudMarket],
            query_params={"channel": "MARKETLIST", "pricesource": price_source},
        )

    def get_unique_pricesources(self) -> set[str]:
        """Returns all unique price sources"""
        all_markets = self.get_all_markets()
        return set(m.price_source for m in all_markets)

    def get_trade_markets(self, exchange_code: str) -> List[CloudMarket]:
        """Get list of supported trading markets for a given exchange"""
        markets = self.executor.execute(
            endpoint="Price",
            response_type=List[Market],
            query_params={
                "channel": "TRADE_MARKETS",
                "pricesource": exchange_code
            }
        )
        
        # Convert Market objects to CloudMarket objects to maintain compatibility
        return [market.to_cloud_market() for market in markets]

    def get_price_data(self, market: str) -> PriceData:
        """
        Get real-time price data for a specific market.
        
        Args:
            market: Market identifier (e.g., "BINANCEFUTURES_BTC_USDT_PERPETUAL")
            
        Returns:
            PriceData object with current price information
            
        Raises:
            HaasApiError: If the API request fails
            
        Example:
            >>> price_data = price_api.get_price_data("BINANCEFUTURES_BTC_USDT_PERPETUAL")
            >>> print(f"BTC Price: ${price_data.close}")
            >>> print(f"24h Volume: {price_data.volume}")
        """
        return self.executor.execute(
            endpoint="Price",
            response_type=PriceData,
            query_params={
                "channel": "PRICE",
                "market": market
            }
        )
    
    def get_multiple_prices(self, markets: List[str]) -> dict[str, PriceData]:
        """
        Get real-time price data for multiple markets.
        
        Args:
            markets: List of market identifiers
            
        Returns:
            Dictionary mapping market names to PriceData objects
        """
        results = {}
        for market in markets:
            try:
                results[market] = self.get_price_data(market)
            except Exception as e:
                log.warning(f"Failed to get price for {market}: {e}")
                continue
        return results
    
    def validate_market(self, market: CloudMarket) -> bool:
        """Validate if a market has active price data"""
        try:
            # Try to get price data to validate market
            market_id = f"{market.price_source}_{market.primary}_{market.secondary}"
            if market.contract:
                market_id += f"_{market.contract}"
            self.get_price_data(market_id)
            return True
        except Exception as e:
            log.warning(f"Market validation failed for {market}: {e}")
            return False

    def get_valid_market(self, exchange_code: str) -> CloudMarket:
        """Get a valid market for the given exchange using multiple methods"""
        try:
            # Method 1: Try trade markets first
            trade_markets = self.get_trade_markets(exchange_code)
            if trade_markets:
                market = random.choice(trade_markets)
                print(f"Selected from trade markets: {market.primary}/{market.secondary}")
                print(f"Trade market price source: {market.price_source}")  # Debug print
                if self.validate_market(market):
                    return market

            # Method 2: Try getting the price source from YAY account
            from pyHaasAPI.api import get_accounts
            accounts = get_accounts(self.executor)
            yay_account = next((acc for acc in accounts if "YAY" in acc.name), None)
            
            if yay_account:
                print(f"Found YAY account with exchange code: {yay_account.exchange_code}")
                print(f"YAY account price source: {yay_account.price_source}")  # Debug print
                
                price_source_markets = self.get_all_markets_by_pricesource(yay_account.price_source)
                if price_source_markets:
                    market = random.choice(price_source_markets)
                    print(f"Selected from YAY price source markets: {market.primary}/{market.secondary}")
                    if self.validate_market(market):
                        return market

            raise ValueError(f"No valid markets found for exchange {exchange_code}")

        except Exception as e:
            log.error(f"Error selecting market: {str(e)}")
            raise

