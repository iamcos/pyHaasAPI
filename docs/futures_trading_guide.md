# Futures Trading Guide

This guide covers the new futures trading functionality in pyHaasAPI, including support for PERPETUAL and QUARTERLY contracts, position modes, margin modes, and leverage settings.

## Overview

The HaasOnline system supports advanced futures trading with different contract types and trading modes. This guide explains how to use these features through the pyHaasAPI library.

## Contract Types

### PERPETUAL Contracts
Perpetual contracts are futures contracts that don't have an expiration date. They are the most common type of futures contract in cryptocurrency trading.

**Market Format**: `BINANCEQUARTERLY_BTC_USD_PERPETUAL`

### QUARTERLY Contracts
Quarterly contracts have a specific expiration date, typically every three months.

**Market Format**: `BINANCEQUARTERLY_BTC_USD_QUARTERLY`

## Position Modes

### ONE-WAY Mode (Position Mode = 0)
- Only one position can be open at a time
- If you have a long position and place a sell order, it will close the long position
- Simpler for beginners

### HEDGE Mode (Position Mode = 1)
- Can have both long and short positions simultaneously
- More complex but allows for advanced trading strategies
- Requires more margin

## Margin Modes

### CROSS Margin (Margin Mode = 0)
- All available balance is used as margin
- More efficient use of capital
- Higher risk if positions move against you

### ISOLATED Margin (Margin Mode = 1)
- Each position has its own allocated margin
- Better risk management
- Less efficient use of capital

## Leverage Settings

Leverage allows you to control larger positions with less capital. Common leverage values:
- **1x-10x**: Conservative
- **10x-25x**: Moderate
- **25x-50x**: Aggressive
- **50x-125x**: Very aggressive (exchange dependent)

## API Usage Examples

### Creating Futures Markets

```python
from pyHaasAPI.model import CloudMarket

# Create perpetual contract
btc_perpetual = CloudMarket(
    category="FUTURES",
    price_source="BINANCEQUARTERLY",
    primary="BTC",
    secondary="USD",
    contract_type="PERPETUAL"
)

# Create quarterly contract
btc_quarterly = CloudMarket(
    category="FUTURES",
    price_source="BINANCEQUARTERLY",
    primary="BTC",
    secondary="USD",
    contract_type="QUARTERLY"
)

# Format market tags
perpetual_market = btc_perpetual.format_futures_market_tag("BINANCEQUARTERLY", "PERPETUAL")
quarterly_market = btc_quarterly.format_futures_market_tag("BINANCEQUARTERLY", "QUARTERLY")

print(f"Perpetual: {perpetual_market}")  # BINANCEQUARTERLY_BTC_USD_PERPETUAL
print(f"Quarterly: {quarterly_market}")  # BINANCEQUARTERLY_BTC_USD_QUARTERLY
```

### Creating Futures Labs

```python
from pyHaasAPI.model import CreateLabRequest, PositionMode, MarginMode, PriceDataStyle

# Create lab for perpetual contract
lab_request = CreateLabRequest.with_futures_market(
    script_id="your_script_id",
    account_id="your_account_id",
    market=btc_perpetual,
    exchange_code="BINANCEQUARTERLY",
    interval=1,
    default_price_data_style=PriceDataStyle.CandleStick,
    contract_type="PERPETUAL"
)

# Add futures-specific settings
lab_request.leverage = 50.0
lab_request.position_mode = PositionMode.ONE_WAY
lab_request.margin_mode = MarginMode.CROSS

# Create the lab
lab = api.create_lab(executor, lab_request)
```

### Setting Position and Margin Modes

```python
from pyHaasAPI import api
from pyHaasAPI.model import PositionMode, MarginMode

# Set position mode to ONE-WAY
api.set_position_mode(
    executor,
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL",
    position_mode=PositionMode.ONE_WAY
)

# Set margin mode to CROSS
api.set_margin_mode(
    executor,
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL",
    margin_mode=MarginMode.CROSS
)

# Set leverage to 50x
api.set_leverage(
    executor,
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL",
    leverage=50.0
)
```

### Getting Current Settings

```python
# Get current position mode
position_mode = api.get_position_mode(
    executor,
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL"
)

# Get current margin mode
margin_mode = api.get_margin_mode(
    executor,
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL"
)

# Get current leverage
leverage = api.get_leverage(
    executor,
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL"
)
```

### Creating Bots from Lab Results

```python
# Create bot from lab results with futures support
bot_result = api.add_bot_from_lab_with_futures(
    executor=executor,
    lab_id="your_lab_id",
    backtest_id="your_backtest_id",
    bot_name="COINS FUTURES BOT",
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL",
    leverage=50.0,
    position_mode=PositionMode.ONE_WAY,
    margin_mode=MarginMode.CROSS
)
```

## Account Types

### BINANCEQUARTERLY Account
This is the account type that supports futures trading with both PERPETUAL and QUARTERLY contracts.

**Driver Code**: `BINANCEQUARTERLY`
**Driver Type**: `2`

### Creating a BINANCEQUARTERLY Account

```python
# Create a simulated BINANCEQUARTERLY account
result = api.add_simulated_account(
    executor,
    name="Binance COINS",
    driver_code="BINANCEQUARTERLY",
    driver_type=2
)

if result and "AID" in result:
    account_id = result["AID"]
    print(f"Created account: {account_id}")
```

## Market Format Reference

### Standard Spot Markets
- Format: `{EXCHANGE}_{PRIMARY}_{SECONDARY}_`
- Example: `BINANCE_BTC_USDT_`

### Futures Markets
- Format: `{EXCHANGE}_{PRIMARY}_{SECONDARY}_{CONTRACT_TYPE}`
- Examples:
  - `BINANCEQUARTERLY_BTC_USD_PERPETUAL`
  - `BINANCEQUARTERLY_BTC_USD_QUARTERLY`
  - `BINANCEQUARTERLY_ETH_USD_PERPETUAL`

## Best Practices

### Risk Management
1. **Start with lower leverage** (10x-25x) until you're comfortable
2. **Use ISOLATED margin** for better risk control
3. **Monitor your positions** regularly
4. **Set stop losses** to limit potential losses

### Account Setup
1. **Create a BINANCEQUARTERLY account** for futures trading
2. **Set position mode** based on your strategy (ONE-WAY for beginners)
3. **Choose margin mode** based on risk tolerance
4. **Set appropriate leverage** for your strategy

### Trading Strategy
1. **Test with simulated accounts** first
2. **Use backtesting** to validate strategies
3. **Start with PERPETUAL contracts** (more liquid)
4. **Consider QUARTERLY contracts** for longer-term strategies

## Common Issues and Solutions

### "Invalid drivercode" Error
- Ensure you're using `BINANCEQUARTERLY` as the driver code
- Use driver type `2` for futures accounts

### Market Not Found
- Verify the market format is correct
- Check that the exchange supports the contract type
- Ensure the account type matches the market

### Position Mode Change Failed
- Close all open positions before changing position mode
- Some exchanges don't allow position mode changes with open positions

### Leverage Too High
- Check the maximum leverage allowed by the exchange
- Reduce leverage to a supported value

## API Reference

### New Functions Added

#### `add_bot_from_lab_with_futures()`
Creates a bot from lab results with futures market support.

#### `set_position_mode()`
Sets the position mode for an account/market.

#### `set_margin_mode()`
Sets the margin mode for an account/market.

#### `set_leverage()`
Sets the leverage for an account/market.

#### `get_position_mode()`
Gets the current position mode for an account/market.

#### `get_margin_mode()`
Gets the current margin mode for an account/market.

#### `get_leverage()`
Gets the current leverage for an account/market.

#### `create_futures_lab()`
Creates a lab specifically for futures trading.

### New Models Added

#### `PositionMode` Enum
- `ONE_WAY = 0`
- `HEDGE = 1`

#### `MarginMode` Enum
- `CROSS = 0`
- `ISOLATED = 1`

#### `ContractType` Enum
- `SPOT = 0`
- `PERPETUAL = 1`
- `QUARTERLY = 2`
- `MONTHLY = 3`

### Updated Models

#### `CloudMarket`
- Added `contract_type` field
- Added `format_futures_market_tag()` method
- Updated `format_market_tag()` to support contract types

#### `CreateLabRequest`
- Added `with_futures_market()` class method
- Updated `with_generated_name()` to support contract types

## Example Scripts

See `examples/futures_trading_example.py` for a complete working example that demonstrates all the features described in this guide.

## Support

If you encounter issues with futures trading:

1. Check that your HaasOnline server supports futures trading
2. Verify your account type is `BINANCEQUARTERLY`
3. Ensure you have the correct permissions
4. Check the HaasOnline documentation for exchange-specific limitations

For API-specific issues, check the error messages and refer to the `pyHaasAPI.exceptions.HaasApiError` documentation. 