# Complete V1 Inventory and Migration Status

## Executive Summary

This document provides a **complete inventory** of every file in `pyHaasAPI_v1/` and its functionality, along with migration status to v2. This is a comprehensive audit to ensure nothing is missed.

## 📁 Core Modules

### `/pyHaasAPI_v1/api.py` (3249 lines)
**Functionality**: Main sync API client with all endpoint functions
- `RequestsExecutor` - Sync HTTP client
- `authenticate()` - Authentication with OTC
- `get_labs()`, `get_lab_details()`, `create_lab()`, `update_lab_details()`, `delete_lab()`
- `get_all_bots()`, `get_bot()`, `activate_bot()`, `deactivate_bot()`, `create_bot_from_lab()`
- `get_accounts()`, `get_account_details()`, `get_account_balance()`
- `get_backtest_result()`, `get_full_backtest_runtime_data()`, `start_lab_execution()`
- `get_scripts()`, `get_script_details()`, `create_script()`, `update_script()`
- **Migration Status**: ✅ **MIGRATED** - Replaced by async API modules in v2
- **V2 Equivalent**: `pyHaasAPI/api/*/*_api.py` (LabAPI, BotAPI, AccountAPI, BacktestAPI, ScriptAPI)

### `/pyHaasAPI_v1/model.py` (872 lines)
**Functionality**: Pydantic models for API responses
- `ApiResponse`, `LabDetails`, `LabRecord`, `LabBacktestResult`
- `HaasBot`, `UserAccount`, `AccountDetails`
- `CreateLabRequest`, `StartLabExecutionRequest`, `CreateBotRequest`
- `BacktestRuntimeData`, `ScriptRecord`
- **Migration Status**: ✅ **MIGRATED** - Models in `pyHaasAPI/models/`
- **V2 Equivalent**: `pyHaasAPI/models/*.py`

### `/pyHaasAPI_v1/parameters.py`
**Functionality**: Parameter handling and types
- `LabParameter`, `ParameterRange`, `ScriptParameter`
- `LabConfig`, `LabSettings`, `LabStatus`, `BacktestStatus`
- Parameter type enums and utilities
- **Migration Status**: ⚠️ **PARTIAL** - Some functionality in v2 models
- **Missing**: Parameter range generation logic

### `/pyHaasAPI_v1/parameter_handler.py`
**Functionality**: Parameter manipulation and optimization
- Parameter value extraction
- Range generation
- Parameter validation
- **Migration Status**: ❌ **NOT PORTED**
- **V2 Need**: Parameter optimization utilities

### `/pyHaasAPI_v1/optimization.py` (569 lines)
**Functionality**: Lab parameter optimization algorithms
- `OptimizationStrategy` enum (TRADITIONAL, MIXED, CONSERVATIVE, AGGRESSIVE)
- `ParameterRangeGenerator` class
- `optimize_lab_parameters_mixed()` - Mixed strategy optimization
- Strategic parameter values (RSI 14, timeframes, etc.)
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH - Advanced optimization logic

### `/pyHaasAPI_v1/lab.py` (545 lines)
**Functionality**: Lab management utilities
- `update_lab_parameter_ranges()` - Parameter optimization
- `backtest()` - Backtest execution helper
- `wait_for_execution()` - Execution monitoring
- `get_lab_default_params()` - Parameter extraction
- Lab cloning utilities
- **Migration Status**: ⚠️ **PARTIAL** - Core functionality in LabService
- **Missing**: Parameter range optimization helpers

### `/pyHaasAPI_v1/lab_manager.py` (456 lines)
**Functionality**: High-level lab management
- `LabManager` class - Consolidated lab operations
- `create_optimized_lab()` - Lab creation with optimization
- `cleanup_invalid_labs()` - Lab cleanup
- `run_backtest_analysis()` - Backtest execution and analysis
- **Migration Status**: ⚠️ **PARTIAL** - Functionality in LabService but different API
- **Missing**: Some helper methods

### `/pyHaasAPI_v1/lab_backup.py` (315 lines)
**Functionality**: Lab backup and restoration
- Lab configuration backup
- Restore functionality
- Backup management utilities
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW - Utility feature

### `/pyHaasAPI_v1/labs/cloning.py` (486 lines)
**Functionality**: Advanced lab cloning system
- `LabCloner` class
- Market discovery integration
- Bulk cloning operations
- Clone statistics tracking
- **Migration Status**: ✅ **MIGRATED** - Basic cloning in LabAPI
- **Missing**: Advanced cloning features, market discovery integration

### `/pyHaasAPI_v1/market_manager.py` (279 lines)
**Functionality**: Market management utilities
- `MarketManager` class
- `get_markets_efficiently()` - Efficient market fetching
- `get_market_by_pair()` - Market lookup
- `format_market_string()` - Market formatting
- `get_accounts()` - Account caching
- `get_test_account()` - Test account finder
- `get_scripts_by_name()` - Script lookup
- **Migration Status**: ⚠️ **PARTIAL** - Market API exists but missing utilities
- **Missing**: Market formatting utilities, account caching helpers

### `/pyHaasAPI_v1/price.py` (210 lines)
**Functionality**: Price API wrapper
- `PriceAPI` class
- `get_all_markets()`, `get_trade_markets()`
- `get_price_data()`, `get_multiple_prices()`
- `get_orderbook()` - Order book data
- `PriceData`, `Market`, `OrderBook` models
- **Migration Status**: ⚠️ **PARTIAL** - Market API exists but missing price-specific features
- **Missing**: Order book functionality, multiple price fetching

### `/pyHaasAPI_v1/markets/discovery.py`
**Functionality**: Market discovery system
- `MarketDiscovery` class
- Market type detection
- Market information extraction
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: MEDIUM

### `/pyHaasAPI_v1/bot_editing_api.py`
**Functionality**: Bot editing utilities
- Bot parameter editing
- Bot configuration updates
- **Migration Status**: ✅ **MIGRATED** - In BotAPI
- **V2 Equivalent**: `pyHaasAPI/api/bot/bot_api.py`

### `/pyHaasAPI_v1/backtest_manager.py`
**Functionality**: Backtest execution management
- Backtest job tracking
- Execution monitoring
- Queue management
- **Migration Status**: ⚠️ **PARTIAL** - Basic functionality in BacktestAPI
- **Missing**: Advanced queue management

### `/pyHaasAPI_v1/backtest_object.py`
**Functionality**: Backtest result object wrapper
- Backtest data models
- Result parsing utilities
- **Migration Status**: ✅ **MIGRATED** - In models/backtest.py

### `/pyHaasAPI_v1/enhanced_execution.py` (491 lines)
**Functionality**: Enhanced backtest execution with history intelligence
- `EnhancedBacktestExecutor` class
- History cutoff date integration
- Automatic period adjustment
- `execute_backtest_with_intelligence()` - Smart execution
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH - Smart execution features

### `/pyHaasAPI_v1/history_intelligence.py` (575 lines)
**Functionality**: History cutoff date discovery and management
- `HistoryIntelligenceService` class
- Automatic cutoff date discovery
- Binary search for precision
- Cutoff database management
- Integration with backtest execution
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH - Prevents backtest failures

### `/pyHaasAPI_v1/error_prevention.py`
**Functionality**: Error prevention utilities
- Validation helpers
- Error checking utilities
- **Migration Status**: ⚠️ **PARTIAL** - Some validation in services
- **Missing**: Comprehensive error prevention helpers

### `/pyHaasAPI_v1/domain.py`
**Functionality**: Domain models and types
- `BacktestPeriod` dataclass
- Domain exception types
- **Migration Status**: ✅ **MIGRATED** - In models/common.py

### `/pyHaasAPI_v1/types.py`
**Functionality**: Type definitions
- `UserState`, `Guest`, `Authenticated`
- `SyncExecutor` protocol
- Parameter option types
- **Migration Status**: ✅ **MIGRATED** - In core/type_definitions.py

### `/pyHaasAPI_v1/iterable_extensions.py`
**Functionality**: Iterable utility functions
- `find_idx()` - Find index helper
- Iterable extensions
- **Migration Status**: ⚠️ **PARTIAL** - Some utilities exist
- **Missing**: Specific iterable helpers

### `/pyHaasAPI_v1/exceptions.py`
**Functionality**: Exception hierarchy
- `HaasApiError` base exception
- Specific exception types
- **Migration Status**: ✅ **MIGRATED** - In exceptions/

### `/pyHaasAPI_v1/logger.py`
**Functionality**: Logging utilities
- Structured logging
- Log configuration
- **Migration Status**: ✅ **MIGRATED** - In core/logging.py

### `/pyHaasAPI_v1/api_validation.py`
**Functionality**: API response validation
- Response validation utilities
- Error checking
- **Migration Status**: ⚠️ **PARTIAL** - Some validation exists
- **Missing**: Comprehensive validation helpers

### `/pyHaasAPI_v1/tools.py`
**Functionality**: General utility tools
- Helper functions
- Utility classes
- **Migration Status**: ⚠️ **PARTIAL**
- **Missing**: Specific utilities

### `/pyHaasAPI_v1/accounts/management.py`
**Functionality**: Account management utilities
- Account operations
- Account helpers
- **Migration Status**: ⚠️ **PARTIAL** - In AccountAPI but missing utilities
- **Missing**: Account management helpers

## 📊 Analysis Modules

### `/pyHaasAPI_v1/analysis/analyzer.py`
**Functionality**: Main analysis engine
- `HaasAnalyzer` class
- Lab analysis
- Backtest processing
- Bot creation recommendations
- **Migration Status**: ⚠️ **PARTIAL** - AnalysisService exists but different API
- **Missing**: Some analysis methods

### `/pyHaasAPI_v1/analysis/metrics.py`
**Functionality**: Performance metrics calculation
- `RunMetrics` class
- `compute_metrics()` - Comprehensive metrics
- Sharpe ratio, Sortino ratio, profit factor
- **Migration Status**: ✅ **MIGRATED** - In analysis/metrics.py

### `/pyHaasAPI_v1/analysis/extraction.py`
**Functionality**: Backtest data extraction
- `BacktestDataExtractor` class
- Trade data extraction
- Parameter extraction
- **Migration Status**: ✅ **MIGRATED** - In analysis/extraction.py

### `/pyHaasAPI_v1/analysis/models.py`
**Functionality**: Analysis data models
- `BacktestAnalysis` dataclass
- `DrawdownAnalysis` dataclass
- `BotCreationResult` dataclass
- **Migration Status**: ✅ **MIGRATED** - In models/

### `/pyHaasAPI_v1/analysis/cache.py`
**Functionality**: Cache management
- `UnifiedCacheManager` class
- Backtest data caching
- Cache invalidation
- **Migration Status**: ⚠️ **PARTIAL** - Basic caching exists
- **Missing**: Unified cache manager

### `/pyHaasAPI_v1/analysis/scoring.py`
**Functionality**: Scoring algorithms
- Risk scoring
- Stability scoring
- Composite scoring
- **Migration Status**: ⚠️ **PARTIAL** - Some scoring in metrics.py
- **Missing**: Comprehensive scoring module

### `/pyHaasAPI_v1/analysis/wfo.py` (662 lines)
**Functionality**: Walk Forward Optimization
- `WFOAnalyzer` class
- `WFOMode` enum (ROLLING, FIXED, EXPANDING)
- `WFOConfig` dataclass
- Multiple WFO modes
- Performance stability analysis
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH

### `/pyHaasAPI_v1/analysis/robustness.py` (469 lines)
**Functionality**: Strategy robustness analysis
- `StrategyRobustnessAnalyzer` class
- `RobustnessMetrics` dataclass
- Time period analysis
- Drawdown risk assessment
- Risk level classification
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH

### `/pyHaasAPI_v1/analysis/backtest_manager.py`
**Functionality**: Backtest management for analysis
- Backtest job tracking
- Result analysis
- **Migration Status**: ⚠️ **PARTIAL**
- **Missing**: Analysis-specific backtest management

### `/pyHaasAPI_v1/analysis/live_bot_validator.py`
**Functionality**: Live bot validation
- Bot validation logic
- Performance monitoring
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: MEDIUM

### `/pyHaasAPI_v1/analysis/logs.py`
**Functionality**: Analysis logging utilities
- Log extraction
- Log parsing
- **Migration Status**: ⚠️ **PARTIAL**
- **Missing**: Specific log utilities

## 🖥️ CLI Modules

### `/pyHaasAPI_v1/cli/main.py` (372 lines)
**Functionality**: Main CLI entry point
- Unified command interface
- Command routing
- Help system
- **Migration Status**: ✅ **MIGRATED** - In cli/main.py (different structure)

### `/pyHaasAPI_v1/cli/base.py`
**Functionality**: Base CLI class
- Common CLI functionality
- Authentication handling
- Error handling
- **Migration Status**: ✅ **MIGRATED** - In cli/base.py

### `/pyHaasAPI_v1/cli/common.py`
**Functionality**: Common CLI utilities
- Shared argument parsers
- Common functions
- **Migration Status**: ⚠️ **PARTIAL**
- **Missing**: Some utility functions

### `/pyHaasAPI_v1/cli/analysis_cli.py`
**Functionality**: Unified analysis CLI
- Cache analysis
- Interactive analysis
- WFO analysis
- Lab caching
- **Migration Status**: ⚠️ **PARTIAL** - Basic analysis CLI exists
- **Missing**: Unified interface, WFO integration

### `/pyHaasAPI_v1/cli/analyze_from_cache.py` (1591 lines)
**Functionality**: Advanced cache analysis
- Manual data extraction
- CSV data integration
- Advanced filtering
- Report generation
- **Migration Status**: ⚠️ **PARTIAL** - Basic cache analysis exists
- **Missing**: Advanced features, CSV integration

### `/pyHaasAPI_v1/cli/analyze_from_cache_refactored.py`
**Functionality**: Refactored cache analysis
- Improved cache analysis
- Better structure
- **Migration Status**: ⚠️ **PARTIAL**
- **Missing**: Refactored improvements

### `/pyHaasAPI_v1/cli/interactive_analyzer.py` (524 lines)
**Functionality**: Interactive analysis tool
- Interactive backtest selection
- Advanced metrics display
- Risk/stability scoring
- Comparison tools
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH

### `/pyHaasAPI_v1/cli/wfo_analyzer.py` (265 lines)
**Functionality**: WFO analysis CLI
- Walk Forward Optimization interface
- Multiple WFO modes
- CSV export
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH

### `/pyHaasAPI_v1/cli/robustness_analyzer.py`
**Functionality**: Robustness analysis CLI
- Strategy robustness interface
- Risk assessment display
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH

### `/pyHaasAPI_v1/cli/robustness_analyzer_unified.py`
**Functionality**: Unified robustness analyzer
- Combined robustness features
- Enhanced reporting
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: HIGH

### `/pyHaasAPI_v1/cli/cached_robustness_analyzer.py`
**Functionality**: Cached robustness analysis
- Robustness with caching
- Performance optimization
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: MEDIUM

### `/pyHaasAPI_v1/cli/visualization_tool.py`
**Functionality**: Visualization and charting
- Backtest charts
- Performance graphs
- Distribution charts
- **Migration Status**: ⚠️ **PARTIAL** - Some visualization exists
- **Missing**: Comprehensive visualization tool

### `/pyHaasAPI_v1/cli/bot_management_cli.py`
**Functionality**: Unified bot management CLI
- Mass bot creation
- Bot amount fixing
- Account cleanup
- Bot activation/deactivation
- **Migration Status**: ⚠️ **PARTIAL** - Individual CLIs exist
- **Missing**: Unified interface

### `/pyHaasAPI_v1/cli/mass_bot_creator.py`
**Functionality**: Mass bot creation tool
- Bulk bot creation from labs
- Batch operations
- **Migration Status**: ⚠️ **PARTIAL** - Functionality in services
- **Missing**: Dedicated CLI

### `/pyHaasAPI_v1/cli/mass_bot_creator_refactored.py`
**Functionality**: Refactored mass bot creator
- Improved bot creation
- Better error handling
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/cli/working_bot_creator.py`
**Functionality**: Proven working bot creator
- Tested bot creation logic
- Reliable implementation
- **Migration Status**: ⚠️ **PARTIAL**
- **Missing**: Specific proven logic

### `/pyHaasAPI_v1/cli/fix_bot_trade_amounts.py`
**Functionality**: Bot trade amount fixing
- Fix bot trade amounts
- Amount adjustment
- **Migration Status**: ⚠️ **PARTIAL** - Functionality exists
- **Missing**: Dedicated CLI

### `/pyHaasAPI_v1/cli/fix_bot_trade_amounts_refactored.py`
**Functionality**: Refactored amount fixer
- Improved fixing logic
- Better handling
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/cli/account_cleanup.py`
**Functionality**: Account cleanup tool
- Account management
- Cleanup operations
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/cli/account_cleanup_refactored.py`
**Functionality**: Refactored account cleanup
- Improved cleanup logic
- Better organization
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/cli/cache_labs.py`
**Functionality**: Lab caching tool
- Cache lab data
- Cache management
- **Migration Status**: ⚠️ **PARTIAL** - Basic caching exists

### `/pyHaasAPI_v1/cli/lab_monitor.py`
**Functionality**: Lab monitoring tool
- Real-time lab monitoring
- Status tracking
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: MEDIUM

### `/pyHaasAPI_v1/cli/price_tracker.py`
**Functionality**: Price tracking tool
- Real-time price monitoring
- Price history
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/cli/price_tracker_refactored.py`
**Functionality**: Refactored price tracker
- Improved price tracking
- Better features
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/cli/backtest_manager.py`
**Functionality**: Backtest management CLI
- Backtest job management
- Queue operations
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/cli/simple_cli.py`
**Functionality**: Simple CLI interface
- Basic commands
- Simple interface
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/cli/working_analyzer.py` (149 lines)
**Functionality**: Proven working analyzer
- Tested analysis logic
- Reliable implementation
- **Migration Status**: ⚠️ **PARTIAL** - Logic incorporated
- **Missing**: Specific proven methods

## 🛠️ Tools and Utilities

### `/pyHaasAPI_v1/tools/utils/backtest_fetcher.py`
**Functionality**: Backtest fetching utilities
- `BacktestFetcher` class
- `fetch_all_lab_backtests()` - Comprehensive fetching
- Pagination handling
- **Migration Status**: ⚠️ **PARTIAL** - Basic fetching exists
- **Missing**: Comprehensive fetcher utility

### `/pyHaasAPI_v1/tools/utils/backtest_tools.py`
**Functionality**: Backtest utilities
- Helper functions
- Backtest operations
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/tools/utils/analysis_tools.py`
**Functionality**: Analysis utilities
- Helper functions
- Analysis operations
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/tools/utils/research_tools.py`
**Functionality**: Research utilities
- Research helpers
- Data collection
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/tools/utils/market_data/market_fetcher.py`
**Functionality**: Market data fetching
- Market data collection
- Market utilities
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/tools/utils/lab_management/lab_sync_and_backtest.py`
**Functionality**: Lab sync and backtest utilities
- Lab synchronization
- Backtest coordination
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: MEDIUM

### `/pyHaasAPI_v1/tools/utils/lab_management/parameter_optimizer.py`
**Functionality**: Parameter optimization utilities
- Parameter optimization helpers
- Range generation
- **Migration Status**: ❌ **NOT PORTED** - Related to optimization.py
- **Priority**: HIGH

### `/pyHaasAPI_v1/tools/utils/auth/authenticator.py`
**Functionality**: Authentication utilities
- Auth helpers
- Session management
- **Migration Status**: ✅ **MIGRATED** - In core/auth.py

### `/pyHaasAPI_v1/tools/tools/history_sync_manager.py`
**Functionality**: History synchronization
- History sync utilities
- Data synchronization
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: MEDIUM

### `/pyHaasAPI_v1/tools/tools/analysis/ai_trading_tools.py`
**Functionality**: AI trading tools
- AI integration
- Trading assistance
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/tools/tools/analysis/textual_backtester.py`
**Functionality**: Textual backtester interface
- Text-based backtesting
- Terminal interface
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/tools/tools/analysis/run_verification.py`
**Functionality**: Run verification utilities
- Verification helpers
- Validation tools
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/tools/tools/haasscript_rag/`
**Functionality**: HaasScript RAG system
- RAG integration
- Script documentation
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/tools/tools/pyhaasapi_bridge_integration.py`
**Functionality**: Bridge integration
- External integration
- Bridge utilities
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW

### `/pyHaasAPI_v1/tools/scripts/`
**Functionality**: Various utility scripts
- Market data scripts
- Account testing scripts
- Parameter optimization scripts
- **Migration Status**: ❌ **NOT PORTED** (utility scripts)
- **Priority**: LOW

## 🎨 Miro Integration

### `/pyHaasAPI_v1/miro_integration/`
**Complete Miro board integration system**
- `dashboard_manager.py` - Dashboard management
- `lab_monitor.py` - Lab monitoring on Miro
- `bot_deployment.py` - Bot deployment interface
- `report_generator.py` - Automated reporting
- `client.py` - Miro API client
- `cli.py` - Miro integration CLI
- **Migration Status**: ❌ **NOT PORTED**
- **Priority**: LOW - External integration

## 📚 Examples

### `/pyHaasAPI_v1/examples/example_usage.py`
**Functionality**: Basic usage examples
- Simple examples
- Tutorial code
- **Migration Status**: ⚠️ **PARTIAL** - Examples exist in v2

### `/pyHaasAPI_v1/examples/complete_bot_management_example.py`
**Functionality**: Complete bot management example
- Full workflow example
- Best practices
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/examples/wfo_example.py`
**Functionality**: WFO analysis example
- WFO usage example
- **Migration Status**: ❌ **NOT PORTED** (depends on WFO)

## 🔧 Configuration

### `/pyHaasAPI_v1/config/lab_configuration.py`
**Functionality**: Lab configuration management
- Configuration utilities
- **Migration Status**: ⚠️ **PARTIAL**

### `/pyHaasAPI_v1/config/settings.py`
**Functionality**: Settings management
- Settings utilities
- **Migration Status**: ✅ **MIGRATED** - In config/

## 📦 Models

### `/pyHaasAPI_v1/models/`
**Functionality**: Additional models
- Auth models
- Common models
- Script models
- **Migration Status**: ✅ **MIGRATED** - In models/

## 📋 Summary by Priority

### HIGH PRIORITY - Core Functionality Missing
1. **WFO Analyzer** (`analysis/wfo.py`, `cli/wfo_analyzer.py`) - 927 lines
2. **Robustness Analyzer** (`analysis/robustness.py`, `cli/robustness_*.py`) - ~800 lines
3. **Interactive Analyzer** (`cli/interactive_analyzer.py`) - 524 lines
4. **Parameter Optimization** (`optimization.py`, `tools/utils/lab_management/parameter_optimizer.py`) - ~1000 lines
5. **Enhanced Execution** (`enhanced_execution.py`) - 491 lines
6. **History Intelligence** (`history_intelligence.py`) - 575 lines

### MEDIUM PRIORITY - Important Utilities
1. **Market Discovery** (`markets/discovery.py`)
2. **Lab Cloning Advanced** (`labs/cloning.py` advanced features)
3. **Lab Monitor CLI** (`cli/lab_monitor.py`)
4. **Market Manager Utilities** (`market_manager.py` utilities)
5. **History Sync Manager** (`tools/tools/history_sync_manager.py`)
6. **Lab Sync and Backtest** (`tools/utils/lab_management/lab_sync_and_backtest.py`)

### LOW PRIORITY - Nice to Have
1. **Miro Integration** (entire module)
2. **Price Tracker** (`cli/price_tracker*.py`)
3. **Lab Backup** (`lab_backup.py`)
4. **Research Tools** (`tools/utils/research_tools.py`)
5. **Various Utility Scripts** (`tools/scripts/`)

## 📊 Migration Statistics

- **Total Files**: ~123 Python files in v1
- **Fully Migrated**: ~35 files (28%)
- **Partially Migrated**: ~45 files (37%)
- **Not Migrated**: ~43 files (35%)
- **Total Lines of Code**: ~25,000+ lines in v1
- **Missing High Priority**: ~4,300 lines
- **Missing Medium Priority**: ~1,500 lines
- **Missing Low Priority**: ~3,000 lines

## 🎯 Recommendation

Focus on migrating HIGH PRIORITY items first:
1. WFO Analyzer
2. Robustness Analyzer  
3. Interactive Analyzer
4. Parameter Optimization
5. Enhanced Execution with History Intelligence

These represent ~4,300 lines of critical functionality that users likely depend on.

