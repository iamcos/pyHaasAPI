from typing import Optional, List, Set
from pydantic import BaseModel, Field
from haaslib.types import SyncExecutor, Authenticated, HaasApiError
from haaslib.model import CloudMarket
from haaslib.logger import log
import random

__all__ = ['PriceAPI', 'OrderBook', 'OrderBookEntry']

class OrderBookEntry(BaseModel):
    price: float
    amount: float

class OrderBook(BaseModel):
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]

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

    def validate_market(self, market: CloudMarket) -> bool:
        """Validate if a market has active price data"""
        try:
            # Implementation of market validation logic
            return True  # Placeholder
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
            from haaslib.api import get_accounts
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

