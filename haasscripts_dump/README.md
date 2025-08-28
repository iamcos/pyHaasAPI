# HaasScript Context Repository

This repository contains a comprehensive collection of HaasScript files, documentation, and context for HaasOnline trading bot development.

## Contents

### Documentation Files
- `System_prompt_HaasScript.md` - Core system prompt and development methodology for HaasScript
- `HaasScript_main_context.txt` - Main context documentation
- `HaasScript_Development_Guide.txt` - Development guide and best practices
- `HaasScript_tips_and_tricks_gemini.txt` - Tips and tricks for HaasScript development
- `HaasScript_plotting.txt` - Plotting and visualization documentation
- `pinescript_to_haasscript.txt` - Guide for converting PineScript to HaasScript

### HaasScript Files (.hss)
This repository contains over 100 HaasScript files including:

#### Original Haasonline Bots
- Accumulation Bot
- Advanced Index Bot
- Crypto Index Bot
- Flash Crash Bot
- Intelli Alice Bot
- Inter Exchange Arbitrage Bot
- MadHatter Bot (multiple versions)
- Market Making Bot
- Order Bot
- Ping Pong Bot
- Scalper Bot
- Zone Recovery Bot

#### Community and Custom Bots
- Enhanced RSI bots (futures and spot)
- Simple trading bots (EMA, RSI, Grid, etc.)
- Technical indicator implementations
- Lazy Bear indicator ports
- Custom scalping and market making strategies

#### Indicators and Utilities
- Technical indicators (ADX, STOCH, MACD, RSI, etc.)
- Custom indicators (ACO, Hull MA, STC, etc.)
- Utility functions and helpers

## HaasScript Development Philosophy

This repository follows the core HaasScript development principles:

1. **Stateless, Tick-Based Execution** - Scripts re-execute on every market tick
2. **Manual State Management** - Use Save() and Load() for persistence
3. **Data Type Safety** - Always validate and convert external data
4. **Performance Optimization** - Single point checks and efficient algorithms

## Usage

These scripts are designed for use with HaasOnline trading platform. Each `.hss` file can be imported directly into HaasOnline for backtesting and live trading.

## Contributing

When adding new scripts or documentation:
- Follow the established naming conventions
- Include proper documentation and comments
- Test thoroughly in backtesting before live deployment
- Maintain the performance-first development approach

## License

See LICENSE file for details.

## Disclaimer

These trading scripts are for educational and research purposes. Always test thoroughly in a safe environment before using with real funds. Trading involves risk and past performance does not guarantee future results.