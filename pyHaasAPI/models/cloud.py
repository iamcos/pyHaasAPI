"""
Cloud models for pyHaasAPI v2

Provides data models for cloud market data, price sources, and trading information.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CloudMarket(BaseModel):
    """Cloud market information"""
    price_source: str = Field(alias="PriceSource", description="Price source name")
    primary: str = Field(alias="Primary", description="Primary currency")
    secondary: str = Field(alias="Secondary", description="Secondary currency")
    contract_name: Optional[str] = Field(alias="ContractName", default=None, description="Contract name")
    short_name: Optional[str] = Field(alias="ShortName", default=None, description="Short name")
    wallet_tag: Optional[str] = Field(alias="WalletTag", default=None, description="Wallet tag")
    
    class Config:
        populate_by_name = True


class CloudTick(BaseModel):
    """Cloud tick data"""
    timestamp: int = Field(alias="Timestamp", description="Unix timestamp")
    open: float = Field(alias="Open", description="Open price")
    high: float = Field(alias="High", description="High price")
    low: float = Field(alias="Low", description="Low price")
    close: float = Field(alias="Close", description="Close price")
    volume: float = Field(alias="Volume", description="Volume")
    buy_price: Optional[float] = Field(alias="BuyPrice", default=None, description="Buy price")
    sell_price: Optional[float] = Field(alias="SellPrice", default=None, description="Sell price")
    
    class Config:
        populate_by_name = True


class CloudMinuteTick(BaseModel):
    """Cloud minute tick data"""
    timestamp: int = Field(alias="Timestamp", description="Unix timestamp")
    open: float = Field(alias="Open", description="Open price")
    high: float = Field(alias="High", description="High price")
    low: float = Field(alias="Low", description="Low price")
    close: float = Field(alias="Close", description="Close price")
    volume: float = Field(alias="Volume", description="Volume")
    buy_price: Optional[float] = Field(alias="BuyPrice", default=None, description="Buy price")
    sell_price: Optional[float] = Field(alias="SellPrice", default=None, description="Sell price")
    
    class Config:
        populate_by_name = True


class CloudOrderBookSide(BaseModel):
    """Cloud order book side entry"""
    price: float = Field(alias="Price", description="Price level")
    amount: float = Field(alias="Amount", description="Amount at this price level")
    
    class Config:
        populate_by_name = True


class CloudOrderbook(BaseModel):
    """Cloud order book"""
    ask: List[CloudOrderBookSide] = Field(alias="Ask", description="Ask side of order book")
    bid: List[CloudOrderBookSide] = Field(alias="Bid", description="Bid side of order book")
    
    class Config:
        populate_by_name = True


class CloudLastTrade(BaseModel):
    """Cloud last trade information"""
    timestamp: int = Field(alias="Timestamp", description="Unix timestamp")
    is_buy_order: bool = Field(alias="IsBuyOrder", description="Whether this is a buy order")
    price: float = Field(alias="Price", description="Trade price")
    amount: float = Field(alias="Amount", description="Trade amount")
    
    class Config:
        populate_by_name = True


class CloudPriceSourceKeyRules(BaseModel):
    """Cloud price source key rules"""
    # Empty class as reference file has no fields
    pass


class CloudPriceSourceOAuthAuthentication(BaseModel):
    """Cloud price source OAuth authentication information"""
    is_available: bool = Field(alias="IsAvailable", default=False, description="Whether OAuth is available")
    button_background: Optional[str] = Field(alias="ButtonBackground", default=None, description="Button background color")
    is_dark_text: bool = Field(alias="IsDarkText", default=False, description="Whether text is dark")
    
    class Config:
        populate_by_name = True


class CloudPriceSource(BaseModel):
    """Cloud price source information"""
    exchange_family: Optional[str] = Field(alias="ExchangeFamily", default=None, description="Exchange family")
    exchange_name: Optional[str] = Field(alias="ExchangeName", default=None, description="Exchange name")
    exchange_code: Optional[str] = Field(alias="ExchangeCode", default=None, description="Exchange code")
    exchange_color: Optional[str] = Field(alias="ExchangeColor", default=None, description="Exchange color")
    spot_trading: bool = Field(alias="SpotTrading", default=False, description="Supports spot trading")
    margin_trading: bool = Field(alias="MarginTrading", default=False, description="Supports margin trading")
    leverage_trading: bool = Field(alias="LeverageTrading", default=False, description="Supports leverage trading")
    has_testnet_support: bool = Field(alias="HasTestNetSupport", default=False, description="Has testnet support")
    api_versions: Optional[List[str]] = Field(alias="ApiVersions", default=None, description="Supported API versions")
    authentication_methods: Optional[List[str]] = Field(alias="AuthenticationMethods", default=None, description="Authentication methods")
    public_key_label: Optional[str] = Field(alias="PublicKeyLabel", default=None, description="Public key label")
    secret_key_label: Optional[str] = Field(alias="SecretKeyLabel", default=None, description="Secret key label")
    additional_field_label: Optional[str] = Field(alias="AdditionalFieldLabel", default=None, description="Additional field label")
    oauth: Optional[CloudPriceSourceOAuthAuthentication] = Field(alias="OAuth", default=None, description="OAuth authentication")
    public_key_rules: Optional[CloudPriceSourceKeyRules] = Field(alias="PublicKeyRules", default=None, description="Public key rules")
    secret_key_rules: Optional[CloudPriceSourceKeyRules] = Field(alias="SecretKeyRules", default=None, description="Secret key rules")
    additional_key_rules: Optional[CloudPriceSourceKeyRules] = Field(alias="AdditionalKeyRules", default=None, description="Additional key rules")
    location: Optional[str] = Field(alias="Location", default=None, description="Location")
    founded_year: Optional[int] = Field(alias="FoundedYear", default=None, description="Founded year")
    affiliation_link: Optional[str] = Field(alias="AffiliationLink", default=None, description="Affiliation link")
    website: Optional[str] = Field(alias="Website", default=None, description="Website")
    email: Optional[str] = Field(alias="Email", default=None, description="Email")
    twitter: Optional[str] = Field(alias="Twitter", default=None, description="Twitter")
    telegram: Optional[str] = Field(alias="Telegram", default=None, description="Telegram")
    facebook: Optional[str] = Field(alias="Facebook", default=None, description="Facebook")
    discord: Optional[str] = Field(alias="Discord", default=None, description="Discord")
    gitbook_api: Optional[str] = Field(alias="GitBookApi", default=None, description="GitBook API")
    rating: Optional[float] = Field(alias="Rating", default=None, description="Rating")
    is_forex_driver: bool = Field(alias="IsForexDriver", default=False, description="Is Forex driver")
    is_login_required: bool = Field(alias="IsLoginRequired", default=False, description="Is login required")
    is_beta_driver: bool = Field(alias="IsBetaDriver", default=False, description="Is beta driver")
    
    class Config:
        populate_by_name = True


class CloudTradeContract(BaseModel):
    """Cloud trade contract information"""
    type: Optional[str] = Field(alias="Type", default=None, description="Contract type")
    margin_currency: Optional[str] = Field(alias="MarginCurrency", default=None, description="Margin currency")
    display_name: Optional[str] = Field(alias="DisplayName", default=None, description="Display name")
    amount_label: Optional[str] = Field(alias="AmountLabel", default=None, description="Amount label")
    profit_label: Optional[str] = Field(alias="ProfitLabel", default=None, description="Profit label")
    contract_value: Optional[float] = Field(alias="ContractValue", default=None, description="Contract value")
    contract_value_currency: Optional[str] = Field(alias="ContractValueCurrency", default=None, description="Contract value currency")
    settlement_date: Optional[int] = Field(alias="SettlementDate", default=None, description="Settlement date (Unix timestamp)")
    lowest_leverage: Optional[float] = Field(alias="LowestLeverage", default=None, description="Lowest leverage")
    highest_leverage: Optional[float] = Field(alias="HighestLeverage", default=None, description="Highest leverage")
    
    class Config:
        populate_by_name = True


class CloudTradeMarket(BaseModel):
    """Cloud trade market information"""
    normalized_primary: Optional[str] = Field(alias="NormalizedPrimary", default=None, description="Normalized primary currency")
    normalized_secondary: Optional[str] = Field(alias="NormalizedSecondary", default=None, description="Normalized secondary currency")
    normalized_margin_currency: Optional[str] = Field(alias="NormalizedMarginCurrency", default=None, description="Normalized margin currency")
    exchange_symbol: Optional[str] = Field(alias="ExchangeSymbol", default=None, description="Exchange symbol")
    websocket_symbol: Optional[str] = Field(alias="WebSocketSymbol", default=None, description="WebSocket symbol")
    exchange_value: Optional[float] = Field(alias="ExchangeValue", default=None, description="Exchange value")
    price_step: Optional[float] = Field(alias="PriceStep", default=None, description="Price step")
    price_decimals: Optional[int] = Field(alias="PriceDecimals", default=None, description="Price decimals")
    amount_step: Optional[float] = Field(alias="AmountStep", default=None, description="Amount step")
    amount_decimals: Optional[int] = Field(alias="AmountDecimals", default=None, description="Amount decimals")
    price_decimal_type: Optional[str] = Field(alias="PriceDecimalType", default=None, description="Price decimal type")
    amount_decimal_type: Optional[str] = Field(alias="AmountDecimalType", default=None, description="Amount decimal type")
    makers_fee: Optional[float] = Field(alias="MakersFee", default=None, description="Maker's fee")
    takers_fee: Optional[float] = Field(alias="TakersFee", default=None, description="Taker's fee")
    minimum_trade_amount: Optional[float] = Field(alias="MinimumTradeAmount", default=None, description="Minimum trade amount")
    minimum_trade_volume: Optional[float] = Field(alias="MinimumTradeVolume", default=None, description="Minimum trade volume")
    maximum_trade_amount: Optional[float] = Field(alias="MaximumTradeAmount", default=None, description="Maximum trade amount")
    maximum_trade_volume: Optional[float] = Field(alias="MaximumTradeVolume", default=None, description="Maximum trade volume")
    is_open: bool = Field(alias="IsOpen", default=False, description="Whether market is open")
    is_margin: bool = Field(alias="IsMargin", default=False, description="Whether margin trading is available")
    contract_details: Optional[CloudTradeContract] = Field(alias="ContractDetails", default=None, description="Contract details")
    margin_currency: Optional[str] = Field(alias="MarginCurrency", default=None, description="Margin currency")
    amount_label: Optional[str] = Field(alias="AmountLabel", default=None, description="Amount label")
    profit_label: Optional[str] = Field(alias="ProfitLabel", default=None, description="Profit label")
    price_source: Optional[str] = Field(alias="PriceSource", default=None, description="Price source")
    primary: Optional[str] = Field(alias="Primary", default=None, description="Primary currency")
    secondary: Optional[str] = Field(alias="Secondary", default=None, description="Secondary currency")
    contract_name: Optional[str] = Field(alias="ContractName", default=None, description="Contract name")
    short_name: Optional[str] = Field(alias="ShortName", default=None, description="Short name")
    wallet_tag: Optional[str] = Field(alias="WalletTag", default=None, description="Wallet tag")
    
    class Config:
        populate_by_name = True

