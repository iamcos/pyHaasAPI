# pyHaasAPI

A comprehensive Python library for HaasOnline API integration with advanced trading automation capabilities.

## 🚀 Features

- **Complete API Coverage**: Full HaasOnline API integration with type-safe models
- **Advanced Analysis**: Trade-level backtest data extraction with intelligent debugging
- **Market Intelligence**: Multi-exchange market discovery and classification
- **Lab Management**: Bulk lab cloning and automated configuration
- **Account Management**: Standardized account creation and naming schemas
- **Parameter Intelligence**: Advanced parameter optimization with strategic values

## 📦 Installation

```bash
pip install pyHaasAPI
```

## 🔧 Quick Start

```python
from pyHaasAPI import api
from pyHaasAPI.analysis import BacktestDataExtractor
from pyHaasAPI.markets import MarketDiscovery

# Get authenticated executor
executor = api.get_authenticated_executor()

# Extract trade data from backtest results
extractor = BacktestDataExtractor()
summary = extractor.extract_backtest_data("backtest_results.json")
print(f"Extracted {len(summary.trades)} trades with {summary.win_rate:.1f}% win rate")
```

## 📚 Documentation

- [Parameter Optimization Algorithm](docs/PARAMETER_OPTIMIZATION_ALGORITHM.md)
- [Quick Reference Guide](docs/PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md)
- [Complete Documentation](docs/README.md)

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for reliable, scalable trading automation**
