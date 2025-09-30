# pyHaasAPI v2

A modern, async-first, type-safe Python library for interacting with the HaasOnline trading platform. This is a complete rewrite of the original pyHaasAPI with a focus on performance, reliability, and developer experience.

## 🚀 Features

- **Async-First Architecture**: Built from the ground up with async/await support
- **Type Safety**: Comprehensive type hints and runtime type validation
- **Modular Design**: Clean separation of concerns with dedicated API modules
- **Service Layer**: High-level business logic services for common operations
- **CLI Tools**: Modern command-line interface for all operations
- **Comprehensive Testing**: Full test coverage with unit, integration, and performance tests
- **Error Handling**: Robust error handling with custom exception hierarchy
- **Rate Limiting**: Built-in rate limiting and retry logic
- **Caching**: Intelligent caching for improved performance
- **Documentation**: Comprehensive API documentation and usage examples

## 📦 Installation

```bash
# Install from source
git clone https://github.com/yourusername/pyHaasAPI.git
cd pyHaasAPI
pip install -e .

# Install with optional dependencies
pip install -e ".[dev,test,docs]"
```

## 🔧 Quick Start

### Basic Usage

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager

async def main():
    # Create client and authenticate
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    
    # Authenticate
    await auth_manager.authenticate()
    
    # Use the client
    labs = await client.get_labs()
    print(f"Found {len(labs)} labs")

# Run the async function
asyncio.run(main())
```

### Using the Service Layer

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import LabService, BotService, AnalysisService

async def main():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create services
    lab_service = LabService(client, auth_manager)
    bot_service = BotService(client, auth_manager)
    analysis_service = AnalysisService(client, auth_manager)
    
    # Analyze a lab and create bots
    analysis_result = await analysis_service.analyze_lab_comprehensive("lab_123", top_count=5)
    
    if analysis_result.success:
        # Create bots from top performers
        bot_result = await bot_service.create_bots_from_lab(
            lab_id="lab_123",
            count=3,
            activate=True
        )
        
        print(f"Created {len(bot_result.data)} bots")

asyncio.run(main())
```

### Using the CLI

```bash
# List all labs
python -m pyHaasAPI_v2.cli lab list

# Create bots from lab analysis
python -m pyHaasAPI_v2.cli bot create --from-lab lab_123 --count 3 --activate

# Analyze labs and generate reports
python -m pyHaasAPI_v2.cli analysis labs --generate-reports --output-format csv

# Get help for any command
python -m pyHaasAPI_v2.cli --help
```

## 🏗️ Architecture

### Core Components

- **AsyncHaasClient**: Low-level async HTTP client
- **AuthenticationManager**: Handles authentication and token management
- **Type Validation**: Runtime type checking and validation
- **Async Utilities**: Rate limiting, retry logic, batch processing

### API Modules

- **LabAPI**: Lab management operations
- **BotAPI**: Bot management operations
- **AccountAPI**: Account management operations
- **ScriptAPI**: Script management operations
- **MarketAPI**: Market data operations
- **BacktestAPI**: Backtest operations
- **OrderAPI**: Order management operations

### Service Layer

- **LabService**: High-level lab management
- **BotService**: High-level bot management
- **AnalysisService**: Analysis and reporting
- **ReportingService**: Report generation

### Tools

- **DataDumper**: Export API data to various formats
- **TestingManager**: Test data management

## 📚 Documentation

- [API Reference](docs/api_reference.md)
- [CLI Reference](docs/cli_reference.md)
- [Examples](docs/examples.md)
- [Migration Guide](docs/migration_guide.md)
- [Contributing](docs/contributing.md)

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run specific test types
python -m pytest -m unit
python -m pytest -m integration
python -m pytest -m performance

# Run with coverage
python -m pytest --cov=pyHaasAPI_v2 --cov-report=html

# Use the test runner
python run_tests.py --coverage --parallel
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
export API_EMAIL="your_email@example.com"
export API_PASSWORD="your_password"

# Optional
export API_HOST="127.0.0.1"
export API_PORT="8090"
export API_TIMEOUT="30.0"
export API_STRICT_MODE="false"
```

### Configuration Files

```python
from pyHaasAPI_v2 import Settings

# Load from environment or config file
settings = Settings()
settings.load_from_file("config.yaml")
```

## 🚀 Performance

pyHaasAPI v2 is designed for high performance:

- **Async Operations**: Non-blocking I/O for better concurrency
- **Rate Limiting**: Intelligent rate limiting to avoid API limits
- **Caching**: Built-in caching for frequently accessed data
- **Batch Processing**: Efficient batch operations
- **Connection Pooling**: Reuse HTTP connections

## 🔒 Security

- **Type Safety**: Runtime type validation prevents many security issues
- **Input Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Secure error handling without information leakage
- **Authentication**: Secure token-based authentication

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/pyHaasAPI.git
cd pyHaasAPI

# Install development dependencies
pip install -e ".[dev,test,docs]"

# Run tests
python run_tests.py

# Run linting
flake8 pyHaasAPI_v2/
black pyHaasAPI_v2/
isort pyHaasAPI_v2/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- HaasOnline for providing the trading platform
- The Python community for excellent async libraries
- Contributors and users of the original pyHaasAPI

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/pyHaasAPI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/pyHaasAPI/discussions)

## 🔄 Migration from v1

If you're migrating from pyHaasAPI v1, see our [Migration Guide](docs/migration_guide.md) for detailed instructions.

## 📊 Status

- **Version**: 2.0.0
- **Python**: 3.8+
- **Status**: Production Ready
- **Coverage**: 95%+
- **Tests**: 500+ test cases

---

**pyHaasAPI v2** - Modern, async-first, type-safe Python library for HaasOnline trading platform.