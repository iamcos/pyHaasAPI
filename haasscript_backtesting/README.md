# HaasScript Backtesting System

A comprehensive platform for direct HaasScript backtesting, optimization, and analysis. This system provides an alternative to lab-based testing with enhanced debugging and parameter optimization capabilities.

## Features

- **Direct Script Execution**: Load, modify, and execute HaasScript files directly through the HaasOnline API
- **Advanced Debugging**: Comprehensive script debugging and validation with intelligent error suggestions
- **Backtest Management**: Execute, monitor, and manage backtest lifecycle with real-time progress tracking
- **Results Analysis**: Process and analyze backtest results with standard trading metrics
- **Parameter Optimization**: Run parameter sweeps and optimization routines
- **Multi-format Export**: Export results in JSON, CSV, and Excel formats
- **Lab Compatibility**: Format results to match existing lab-based workflows

## Architecture

The system is organized into several core modules:

- **Models**: Data structures for scripts, backtests, and results
- **Config**: Configuration management for system settings and API credentials
- **Script Manager**: HaasScript loading, debugging, and validation
- **Backtest Manager**: Backtest execution and monitoring
- **Results Manager**: Result processing and analysis

## Quick Start

### 1. Installation

```python
# Install the module (assuming it's in your Python path)
from haasscript_backtesting import (
    ConfigManager, ScriptManager, BacktestManager, ResultsManager
)
```

### 2. Configuration

Set up your environment variables:

```bash
export HAAS_SERVER_URL="https://your-haasonline-server.com"
export HAAS_API_KEY="your-api-key"
export HAAS_API_SECRET="your-api-secret"
```

Or create configuration files in the `config/` directory.

### 3. Basic Usage

```python
from haasscript_backtesting import ConfigManager
from haasscript_backtesting.script_manager import ScriptManager
from haasscript_backtesting.backtest_manager import BacktestManager
from haasscript_backtesting.results_manager import ResultsManager
from haasscript_backtesting.models import BacktestConfig, PositionMode
from datetime import datetime, timedelta

# Initialize system
config_manager = ConfigManager()
script_manager = ScriptManager(config_manager)
backtest_manager = BacktestManager(config_manager)
results_manager = ResultsManager(config_manager)

# Load and debug a script
script = script_manager.load_script("your_script_id")
debug_result = script_manager.debug_script(script)

if debug_result.success:
    # Configure backtest
    config = BacktestConfig(
        script_id="your_script_id",
        account_id="your_account",
        market_tag="BTC/USD",
        start_time=int((datetime.now() - timedelta(days=30)).timestamp()),
        end_time=int(datetime.now().timestamp()),
        interval=60,  # 1-hour candles
        trade_amount=1000.0,
        script_parameters={"param1": 100.0},
        position_mode=PositionMode.LONG_ONLY
    )
    
    # Execute backtest
    execution = backtest_manager.execute_backtest(config)
    
    # Monitor progress
    while execution.status.is_running:
        status = backtest_manager.monitor_execution(execution.backtest_id)
        print(f"Progress: {status.progress_percentage:.1f}%")
    
    # Process results
    results = results_manager.process_results(execution.backtest_id)
    
    # Display metrics
    print(f"Total Return: {results.trading_metrics.total_return:.2f}%")
    print(f"Sharpe Ratio: {results.trading_metrics.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {results.trading_metrics.max_drawdown:.2f}%")
```

## Configuration

### Environment Variables

- `HAAS_SERVER_URL`: HaasOnline server URL
- `HAAS_API_KEY`: API key for authentication
- `HAAS_API_SECRET`: API secret for authentication
- `HAAS_USERNAME`: Optional username
- `HAAS_PASSWORD`: Optional password
- `HAAS_MAX_CONCURRENT_BACKTESTS`: Maximum concurrent executions (default: 5)
- `HAAS_LOG_LEVEL`: Logging level (default: INFO)

### Configuration Files

Create configuration files in the `config/` directory:

- `system.json`: System-wide settings
- `haasonline.json`: HaasOnline API configuration
- `database.json`: Database connection settings

Use `config_manager.create_sample_configs()` to generate sample files.

## Data Models

### Core Models

- **HaasScript**: Represents a HaasScript with metadata and content
- **BacktestConfig**: Configuration for backtest execution
- **BacktestExecution**: Tracks backtest execution state
- **ProcessedResults**: Complete processed results with metrics
- **TradingMetrics**: Standard trading performance metrics

### Configuration Models

- **SystemConfig**: System-wide configuration settings
- **HaasOnlineConfig**: HaasOnline API configuration
- **DatabaseConfig**: Database connection configuration

## API Integration

The system integrates with the following HaasOnline API endpoints:

### Script Management
- `GET_SCRIPT_RECORD`: Retrieve script content
- `EXECUTE_DEBUGTEST`: Debug script compilation
- `EXECUTE_QUICKTEST`: Quick script testing

### Backtest Execution
- `EXECUTE_BACKTEST`: Start backtest execution
- `GET_EXECUTION_UPDATE`: Monitor progress
- `EXECUTION_BACKTESTS`: List running backtests

### Results Retrieval
- `GET_BACKTEST_RUNTIME`: Get runtime data
- `GET_BACKTEST_LOGS`: Retrieve execution logs
- `GET_BACKTEST_CHART_PARTITION`: Get chart data

### History Management
- `GET_BACKTEST_HISTORY`: Retrieve history
- `ARCHIVE_BACKTEST`: Archive results
- `DELETE_BACKTEST`: Delete backtests

## Testing

Run the test suite:

```python
python -m unittest haasscript_backtesting.tests.test_basic_functionality
```

Or run the basic usage example:

```python
python -m haasscript_backtesting.examples.basic_usage
```

## Error Handling

The system provides comprehensive error handling:

- **Script Errors**: Syntax errors, runtime errors, parameter validation
- **Execution Errors**: Resource constraints, network issues, timeouts
- **Data Errors**: Missing data, invalid ranges, corrupted results

All errors include detailed messages and suggestions for resolution.

## Performance Considerations

- **Concurrent Execution**: Configurable limits on concurrent backtests
- **Caching**: Script and result caching for improved performance
- **Resource Monitoring**: Real-time resource usage tracking
- **Cleanup**: Automatic cleanup of old executions

## Security

- **API Key Encryption**: Secure storage of API credentials
- **Input Validation**: Comprehensive input sanitization
- **Rate Limiting**: Configurable API rate limiting
- **Audit Logging**: Complete audit trail of operations

## Future Enhancements

This foundational implementation supports:

- RAG-enhanced script development assistance
- MCP server integration for external access
- Parameter optimization algorithms
- Multi-backend abstraction layer
- Real-time monitoring and alerting

## Contributing

This module is part of the larger HaasScript Backtesting System. Follow the established patterns for:

- Data model definitions in `models/`
- Configuration management in `config/`
- Core functionality in respective manager modules
- Comprehensive testing in `tests/`
- Usage examples in `examples/`

## License

This module is part of the HaasScript Backtesting System project.