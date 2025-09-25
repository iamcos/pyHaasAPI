"""
Market-related exceptions
"""

from .base import NonRetryableError


class MarketError(NonRetryableError):
    """Base class for market-related errors"""
    
    def __init__(self, message: str = "Market operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="MARKET_ERROR",
            recovery_suggestion="Check market configuration and try again",
            **kwargs
        )


class MarketNotFoundError(MarketError):
    """Raised when market is not found"""
    
    def __init__(self, market: str, **kwargs):
        super().__init__(
            message=f"Market not found: {market}",
            error_code="MARKET_NOT_FOUND",
            context={"market": market},
            recovery_suggestion="Check market symbol and try again",
            **kwargs
        )
        self.market = market


class PriceDataError(MarketError):
    """Raised when price data operation fails"""
    
    def __init__(self, market: str, **kwargs):
        super().__init__(
            message=f"Price data operation failed for market: {market}",
            error_code="PRICE_DATA_ERROR",
            context={"market": market},
            recovery_suggestion="Check market availability and try again",
            **kwargs
        )
        self.market = market


class MarketDataError(MarketError):
    """Raised when market data operation fails"""
    
    def __init__(self, market: str, **kwargs):
        super().__init__(
            message=f"Market data operation failed for market: {market}",
            error_code="MARKET_DATA_ERROR",
            context={"market": market},
            recovery_suggestion="Check market data source and try again",
            **kwargs
        )
        self.market = market


class ExchangeError(MarketError):
    """Raised when exchange operation fails"""
    
    def __init__(self, exchange: str, **kwargs):
        super().__init__(
            message=f"Exchange operation failed: {exchange}",
            error_code="EXCHANGE_ERROR",
            context={"exchange": exchange},
            recovery_suggestion="Check exchange connection and try again",
            **kwargs
        )
        self.exchange = exchange



