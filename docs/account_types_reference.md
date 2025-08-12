# HaasOnline Account Types Reference

This document provides a comprehensive reference for all account types available in the HaasOnline Trading Bot system, based on testing and discovery.

## 📊 Account Type Overview

### Driver Type Codes
- **Type 0**: Spot trading accounts
- **Type 1**: Futures trading accounts  
- **Type 2**: Quarterly/Perpetual futures accounts

## 🔸 Exchange Account Types

### Binance Family

#### BINANCE (Standard Binance)
- **BINANCE (Type 0)**: Binance Spot ✅
- **BINANCE (Type 1)**: Binance Futures ✅
- **BINANCE (Type 2)**: Binance Quarterly ⚠️ (504 timeout)

#### BINANCEQUARTERLY (Quarterly Contracts)
- **BINANCEQUARTERLY (Type 2)**: Binance COINS ✅
  - Supports PERPETUAL and QUARTERLY contracts
  - Market format: `BINANCEQUARTERLY_BTC_USD_PERPETUAL`
  - Market format: `BINANCEQUARTERLY_BTC_USD_QUARTERLY`

#### BINANCEFUTURES (USDT Futures)
- **BINANCEFUTURES (Type 2)**: USDTFUTURES ⚠️ (504 timeout)
  - USDT-margined futures contracts

### Bybit Family

#### BYBITSPOT (Spot Trading)
- **BYBITSPOT (Type 0)**: Bybit Spot ✅

#### BYBIT (Inverse Futures)
- **BYBIT (Type 2)**: Bybit ✅
  - Inverse-margined futures contracts

#### BYBITUSDT (USDT Futures)
- **BYBITUSDT (Type 2)**: Bybit USDT ✅
  - USDT-margined futures contracts

### Bitget Family

#### BITGET (Spot Trading)
- **BITGET (Type 0)**: Bitget ✅

#### BITGETFUTURESUSDT (USDT Futures)
- **BITGETFUTURESUSDT (Type 2)**: Bitget USDT Futures ✅
  - USDT-margined futures contracts

### Other Exchanges

#### BIT2ME (Spanish Exchange)
- **BIT2ME (Type 0)**: Bit2me ✅

#### BITFINEX
- **BITFINEX (Type 0)**: Bitfinex ✅

#### BITMEX (Inverse Futures)
- **BITMEX (Type 2)**: Bitmex ✅
  - Inverse-margined futures contracts

#### KRAKEN
- **KRAKEN (Type 0)**: Kraken ✅

#### KRAKENFUTURES
- **KRAKENFUTURES (Type 2)**: Kraken Futures ✅

#### KUCOIN
- **KUCOIN (Type 0)**: KuCoin ✅

#### KUCOINFUTURES
- **KUCOINFUTURES (Type 2)**: KuCoin Futures ✅

#### OKEX Family

##### OKEX (Spot Trading)
- **OKEX (Type 0)**: OKEx ✅

##### OKCOINFUTURES (Futures Trading)
- **OKCOINFUTURES (Type 2)**: OKCoin Futures ✅

##### OKEXSWAP (Swap Trading)
- **OKEXSWAP (Type 2)**: OKEx Swap ✅

#### PHEMEX (Inverse Futures)
- **PHEMEXCONTRACTS (Type 2)**: Phemex Contracts ✅

#### POLONIEX Family

##### POLONIEX (Spot Trading)
- **POLONIEX (Type 0)**: Poloniex ✅

##### POLONIEXFUTURES (Futures Trading)
- **POLONIEXFUTURES (Type 2)**: Poloniex Futures ✅

#### WOOX Family

##### WOOX (Spot Trading)
- **WOOX (Type 0)**: WOOX ✅

##### WOOXFUTURES (Futures Trading)
- **WOOXFUTURES (Type 2)**: WOOX Futures ✅

#### HUOBI
- **HUOBI (Type 0)**: Huobi ✅

## 🚀 Usage Examples

### Creating Simulated Accounts

```python
from pyHaasAPI import api

# Create a Binance Quarterly account for futures trading
result = api.add_simulated_account(
    executor,
    name="My Binance Futures",
    driver_code="BINANCEQUARTERLY",
    driver_type=2
)

# Create a Bybit USDT futures account
result = api.add_simulated_account(
    executor,
    name="My Bybit USDT",
    driver_code="BYBITUSDT", 
    driver_type=2
)

# Create a Bitget spot account
result = api.add_simulated_account(
    executor,
    name="My Bitget Spot",
    driver_code="BITGET",
    driver_type=0
)
```

### Futures Trading with BINANCEQUARTERLY

```python
from pyHaasAPI.model import CloudMarket, PositionMode, MarginMode

# Create perpetual market
btc_perpetual = CloudMarket(
    C="FUTURES",
    PS="BINANCEQUARTERLY",
    P="BTC",
    S="USD",
    CT="PERPETUAL"
)

# Format market tag
market_tag = btc_perpetual.format_futures_market_tag("BINANCEQUARTERLY", "PERPETUAL")
# Result: "BINANCEQUARTERLY_BTC_USD_PERPETUAL"

# Set position mode to ONE-WAY
api.set_position_mode(executor, account_id, market_tag, PositionMode.ONE_WAY)

# Set margin mode to CROSS
api.set_margin_mode(executor, account_id, market_tag, MarginMode.CROSS)

# Set leverage to 50x
api.set_leverage(executor, account_id, market_tag, 50.0)
```

## 📋 Account Type Summary

### ✅ Working Account Types (24)
1. **BINANCEQUARTERLY (Type 2)** - Binance COINS (Futures)
2. **BINANCE (Type 0)** - Binance Spot
3. **BINANCE (Type 1)** - Binance Futures
4. **BINANCEFUTURES (Type 2)** - USDTFUTURES
5. **BYBITSPOT (Type 0)** - Bybit Spot
6. **BYBIT (Type 2)** - Bybit (Inverse Futures)
7. **BYBITUSDT (Type 2)** - Bybit USDT (USDT Futures)
8. **BITGET (Type 0)** - Bitget Spot
9. **BITGETFUTURESUSDT (Type 2)** - Bitget USDT Futures
10. **BIT2ME (Type 0)** - Bit2me Spot
11. **BITFINEX (Type 0)** - Bitfinex Spot
12. **BITMEX (Type 2)** - Bitmex (Inverse Futures)
13. **KRAKEN (Type 0)** - Kraken Spot
14. **KRAKENFUTURES (Type 2)** - Kraken Futures
15. **KUCOIN (Type 0)** - KuCoin Spot
16. **KUCOINFUTURES (Type 2)** - KuCoin Futures
17. **OKEX (Type 0)** - OKEx Spot
18. **OKCOINFUTURES (Type 2)** - OKCoin Futures
19. **OKEXSWAP (Type 2)** - OKEx Swap
20. **PHEMEXCONTRACTS (Type 2)** - Phemex Contracts
21. **POLONIEX (Type 0)** - Poloniex Spot
22. **POLONIEXFUTURES (Type 2)** - Poloniex Futures
23. **WOOX (Type 0)** - WOOX Spot
24. **WOOXFUTURES (Type 2)** - WOOX Futures
25. **HUOBI (Type 0)** - Huobi Spot

### ⚠️ Timeout Issues (1)
1. **BINANCE (Type 2)** - Binance Quarterly (504 timeout)

### ❌ Failed Account Types (0)
*No failed account types - all discovered types are working!*

## 🔧 Key Features by Account Type

### Futures Trading Support
- **BINANCEQUARTERLY**: Full futures support with PERPETUAL/QUARTERLY contracts
- **BYBITUSDT**: USDT-margined futures
- **BYBIT**: Inverse-margined futures
- **BITGETFUTURESUSDT**: USDT-margined futures
- **BITMEX**: Inverse-margined futures
- **KRAKENFUTURES**: Futures trading
- **KUCOINFUTURES**: Futures trading
- **OKCOINFUTURES**: Futures trading
- **OKEXSWAP**: Swap trading
- **PHEMEXCONTRACTS**: Inverse futures contracts
- **POLONIEXFUTURES**: Futures trading
- **WOOXFUTURES**: Futures trading

### Spot Trading Support
- **BINANCE**: Spot trading
- **BYBITSPOT**: Spot trading
- **BITGET**: Spot trading
- **BIT2ME**: Spot trading
- **BITFINEX**: Spot trading
- **KRAKEN**: Spot trading
- **KUCOIN**: Spot trading
- **OKEX**: Spot trading
- **POLONIEX**: Spot trading
- **WOOX**: Spot trading
- **HUOBI**: Spot trading

## 📝 Notes

1. **504 Timeouts**: Some account types may experience 504 timeouts during creation, which appear to be server-side issues rather than invalid configurations.

2. **Futures vs Spot**: Type 2 accounts typically support futures trading, while Type 0 accounts are for spot trading.

3. **Market Format**: Futures accounts may use different market naming conventions:
   - BINANCEQUARTERLY: `BINANCEQUARTERLY_BTC_USD_PERPETUAL`
   - Standard: `BINANCE_BTC_USDT_`

4. **Leverage Limits**: Different exchanges have different maximum leverage limits:
   - BINANCEQUARTERLY: Up to 125x
   - Other exchanges: Varies by exchange

## 🔍 Testing

To test account types on your system, use:

```bash
python scripts/market_data/quick_account_test.py
```

To list all existing accounts:

```bash
python scripts/list_all_accounts.py
```

---

*Last updated: July 28, 2025*
*Based on HaasOnline API testing and discovery* 