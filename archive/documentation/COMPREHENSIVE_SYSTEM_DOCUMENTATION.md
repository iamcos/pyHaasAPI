# 🚀 pyHaasAPI Comprehensive System Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Strategy Robustness Analysis](#strategy-robustness-analysis)
3. [Backtest Management System](#backtest-management-system)
4. [Cutoff-Based Pre-Bot Validation](#cutoff-based-pre-bot-validation)
5. [Walk Forward Optimization (WFO)](#walk-forward-optimization-wfo)
6. [CLI Tools](#cli-tools)
7. [API Integration](#api-integration)
8. [Cache Management](#cache-management)
9. [Usage Examples](#usage-examples)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The pyHaasAPI library now includes a comprehensive suite of advanced trading analysis and automation tools:

- **Strategy Robustness Analysis**: Identifies account blowup risk and provides safety recommendations
- **Backtest Management System**: Tracks and monitors backtest jobs with intelligent cutoff discovery
- **Pre-Bot Validation**: Individual backtests with maximum data periods before bot creation
- **Walk Forward Optimization**: Real WFO analysis with time period slicing
- **Enhanced CLI Tools**: Command-line interfaces for all major functionality

---

## 🛡️ Strategy Robustness Analysis

### Purpose
Analyzes trading strategies for robustness and risk factors, with special focus on **wallet protection** and **account blowup prevention**.

### Key Features

#### Max Drawdown Analysis
- **Tracks cumulative P&L** over time to detect when account goes negative
- **Calculates maximum drawdown** from peak balance
- **Flags dangerous strategies** that could blow up the account
- **Provides safety recommendations** based on risk level

#### Risk Assessment Levels
- **CRITICAL**: Max drawdown > 50% or consecutive losses > 10 → **DO NOT CREATE BOT**
- **HIGH**: Robustness score < 30 → High risk, consider reducing position size
- **MEDIUM**: Robustness score 30-50 → Medium risk, monitor closely
- **LOW**: Robustness score 50-70 → Low risk, suitable for bot creation
- **VERY LOW**: Robustness score > 70 → Very robust, excellent for bot creation

#### Safe Leverage Recommendations
- **Max drawdown > 30%**: 1.0x leverage (no leverage)
- **Max drawdown 20-30%**: 2.0x leverage
- **Max drawdown 10-20%**: 3.0x leverage
- **Max drawdown < 10%**: 5.0x leverage

### Usage

#### Programmatic Usage
```python
from pyHaasAPI.analysis import StrategyRobustnessAnalyzer, HaasAnalyzer, UnifiedCacheManager

# Initialize components
cache_manager = UnifiedCacheManager()
analyzer = HaasAnalyzer(cache_manager)
robustness_analyzer = StrategyRobustnessAnalyzer(cache_manager)

# Connect to API
analyzer.connect()

# Analyze lab
lab_result = analyzer.analyze_lab("lab-id", top_count=10)

# Analyze robustness
robustness_results = robustness_analyzer.analyze_lab_robustness(lab_result)

# Generate report
report = robustness_analyzer.generate_robustness_report(robustness_results)
print(report)
```

#### CLI Usage
```bash
# Analyze specific lab
poetry run python -m pyHaasAPI.cli.robustness_analyzer \
  --lab-id e4616b35-8065-4095-966b-546de68fd493 \
  --top-count 10

# Analyze all labs
poetry run python -m pyHaasAPI.cli.robustness_analyzer \
  --all-labs \
  --top-count 5

# Save report to file
poetry run python -m pyHaasAPI.cli.robustness_analyzer \
  --lab-id lab123 \
  --output robustness_report.txt
```

### Sample Output
```
================================================================================
STRATEGY ROBUSTNESS ANALYSIS REPORT
================================================================================
Analysis Date: 2025-09-07 15:05:44
Total Backtests Analyzed: 5

SUMMARY STATISTICS:
----------------------------------------
Average Robustness Score: 69.4/100
Highest Robustness Score: 70.4/100
Lowest Robustness Score: 67.6/100

RISK LEVEL DISTRIBUTION:
----------------------------------------
CRITICAL: 5 backtests (100.0%)

DETAILED ANALYSIS:
----------------------------------------
Backtest ID: eb844c2f-66c1-4769-8b88-3e02f349b40d
  Overall ROI: 1874.8%
  Robustness Score: 68.3/100
  Risk Level: CRITICAL
  Max Drawdown: 929.7%
  Account Blowup Risk: YES
  Safe Leverage: 1.0x
  Recommendation: DO NOT CREATE BOT - High risk of account blowup
```

---

## 🔧 Backtest Management System

### Purpose
Comprehensive system for managing backtest jobs, including creation, monitoring, and result retrieval.

### Key Components

#### BacktestJob
```python
@dataclass
class BacktestJob:
    job_id: str
    job_type: str  # 'lab' or 'individual'
    lab_id: str
    backtest_id: Optional[str] = None
    script_id: str = ""
    market_tag: str = ""
    account_id: str = ""
    start_unix: int = 0
    end_unix: int = 0
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
```

#### WFOJob
```python
@dataclass
class WFOJob:
    wfo_id: str
    base_script_id: str
    base_market_tag: str
    base_account_id: str
    time_periods: List[Dict[str, Any]]
    parameter_ranges: Dict[str, List[float]]
    status: str = "pending"
    created_at: str = ""
    completed_at: Optional[str] = None
    lab_jobs: List[BacktestJob] = None
    results: Optional[Dict[str, Any]] = None
```

### Features

#### Job Tracking
- **Persistent Storage**: Jobs saved to `unified_cache/backtest_jobs.json`
- **Status Monitoring**: Tracks pending, running, completed, and failed jobs
- **Result Caching**: Stores backtest results for later analysis
- **Error Handling**: Captures and stores error messages

#### Job Management
- **Create Individual Backtests**: For pre-bot validation
- **Create WFO Labs**: With multiple time periods
- **Monitor Execution**: Check job status and retrieve results
- **Cleanup Old Jobs**: Remove completed jobs older than specified days

### Usage

#### Programmatic Usage
```python
from pyHaasAPI.analysis import BacktestManager, UnifiedCacheManager
from datetime import datetime, timedelta

# Initialize
cache_manager = UnifiedCacheManager()
backtest_manager = BacktestManager(cache_manager)

# Connect to API
backtest_manager.connect(executor)

# Create individual backtest
job = backtest_manager.create_individual_backtest(
    script_id="script123",
    market_tag="BINANCE_BTC_USDT_",
    account_id="acc123",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    job_name="PreBotValidation"
)

# Monitor jobs
results = backtest_manager.monitor_jobs()
print(f"Completed: {results['completed_jobs']}")
print(f"Failed: {results['failed_jobs']}")

# Get job status
job_status = backtest_manager.get_job_status(job.job_id)
print(f"Status: {job_status.status}")

# Generate status report
report = backtest_manager.generate_status_report()
print(report)
```

---

## 🎯 Cutoff-Based Pre-Bot Validation

### Purpose
Creates individual backtests using **cutoff discovery** to maximize the backtest period for comprehensive pre-bot validation.

### How It Works

#### 1. Lab Creation
- Creates a lab for the specified script and market
- Uses proper market and account assignment

#### 2. Cutoff Discovery
- **Binary Search Algorithm**: Finds the earliest date with available data
- **Range**: Searches from 2 years ago to yesterday
- **Precision**: 1-day accuracy
- **Safety**: Adds 1-day buffer after cutoff

#### 3. Optimal Period Calculation
```python
cutoff_date = discovered_cutoff_date
end_date = datetime.now()
start_date = cutoff_date + timedelta(days=1)  # Safety margin
```

#### 4. Backtest Execution
- Starts backtest with maximum possible period
- Tracks execution status
- Retrieves results when complete

### Usage

#### CLI Usage
```bash
# Create cutoff-based individual backtest
poetry run python -m pyHaasAPI.cli.backtest_manager create-individual-cutoff \
  --script-id script123 \
  --market-tag BINANCE_BTC_USDT_ \
  --account-id acc123 \
  --job-name "PreBotValidation"

# Monitor the job
poetry run python -m pyHaasAPI.cli.backtest_manager monitor

# Check status
poetry run python -m pyHaasAPI.cli.backtest_manager status
```

#### Programmatic Usage
```python
# Create cutoff-based backtest
job = backtest_manager.create_individual_backtest_with_cutoff(
    script_id="script123",
    market_tag="BINANCE_BTC_USDT_",
    account_id="acc123",
    job_name="PreBotValidation"
)

print(f"Job ID: {job.job_id}")
print(f"Lab ID: {job.lab_id}")
print(f"Backtest period: {(datetime.fromtimestamp(job.end_unix) - datetime.fromtimestamp(job.start_unix)).days} days")
```

### Sample Output
```
2025-09-07 15:31:03,652 - INFO - Creating cutoff-based individual backtest for script script123
2025-09-07 15:31:03,653 - INFO - Creating lab for cutoff-based individual backtest
2025-09-07 15:31:03,654 - INFO - Created lab lab456 for cutoff-based individual backtest
2025-09-07 15:31:03,655 - INFO - Starting simplified cutoff discovery for BINANCE_BTC_USDT_
2025-09-07 15:31:03,656 - INFO - Attempt 1: Testing cutoff at 2023-09-07 15:31:03
2025-09-07 15:31:03,657 - INFO - Data available at 2023-09-07 15:31:03, moving cutoff earlier
...
2025-09-07 15:31:03,660 - INFO - Discovered cutoff date: 2022-11-13 21:58:10 (after 8 attempts)
2025-09-07 15:31:03,661 - INFO - Cutoff date: 2022-11-13 21:58:10
2025-09-07 15:31:03,662 - INFO - Optimal backtest period: 2022-11-14 21:58:10 to 2025-09-07 15:31:03
2025-09-07 15:31:03,663 - INFO - Backtest duration: 1027 days
2025-09-07 15:31:03,664 - INFO - Created cutoff-based individual backtest job: individual_cutoff_1694115063_script123
```

---

## 📊 Walk Forward Optimization (WFO)

### Purpose
Performs real Walk Forward Optimization by slicing existing long backtest data into training and testing periods.

### Key Features

#### Real WFO Implementation
- **Data Slicing**: Uses actual historical trade data from existing backtests
- **Time Period Management**: Creates multiple training/testing periods
- **Parameter Evolution**: Tracks how optimal parameters change over time
- **Performance Analysis**: Analyzes strategy robustness across different periods

#### WFO Modes
- **Rolling Window**: Fixed training period, sliding testing window
- **Fixed Window**: Fixed training and testing periods
- **Expanding Window**: Growing training period, fixed testing period

### Usage

#### CLI Usage
```bash
# Create WFO lab with 4 periods
poetry run python -m pyHaasAPI.cli.backtest_manager create-wfo \
  --script-id script123 \
  --market-tag BINANCE_BTC_USDT_ \
  --account-id acc123 \
  --training-days 90 \
  --testing-days 30 \
  --num-periods 4 \
  --wfo-name "WFO_Analysis"

# Monitor WFO progress
poetry run python -m pyHaasAPI.cli.backtest_manager monitor

# WFO analysis (existing tool)
poetry run python -m pyHaasAPI.cli.wfo_analyzer \
  --lab-id lab123 \
  --start-date 2022-01-01 \
  --end-date 2023-12-31 \
  --training-days 180 \
  --testing-days 60
```

#### Programmatic Usage
```python
from pyHaasAPI.analysis import WFOAnalyzer, WFOConfig, WFOMode
from datetime import datetime

# Initialize WFO analyzer
wfo_analyzer = WFOAnalyzer(cache_manager)
wfo_analyzer.connect()

# Configure WFO
config = WFOConfig(
    total_start_date=datetime(2022, 1, 1),
    total_end_date=datetime(2023, 12, 31),
    training_duration_days=365,
    testing_duration_days=90,
    mode=WFOMode.ROLLING_WINDOW
)

# Run WFO analysis
wfo_result = wfo_analyzer.analyze_lab_wfo("lab-id", config)

# Save report
report_path = wfo_analyzer.save_wfo_report(wfo_result)
print(f"WFO report saved to: {report_path}")
```

---

## 🖥️ CLI Tools

### Available CLI Tools

#### 1. Strategy Robustness Analyzer
```bash
poetry run python -m pyHaasAPI.cli.robustness_analyzer [OPTIONS]
```

**Options:**
- `--lab-id`: Analyze specific lab
- `--all-labs`: Analyze all available labs
- `--top-count`: Number of top backtests to analyze (default: 10)
- `--output`: Save report to file
- `--verbose`: Enable verbose logging

#### 2. Backtest Manager
```bash
poetry run python -m pyHaasAPI.cli.backtest_manager [COMMAND] [OPTIONS]
```

**Commands:**
- `create-individual`: Create individual backtest (fixed hours)
- `create-individual-cutoff`: Create individual backtest with cutoff discovery
- `create-wfo`: Create WFO lab with multiple periods
- `monitor`: Monitor all pending and running jobs
- `status`: Show comprehensive status report
- `cleanup`: Clean up old completed jobs

#### 3. WFO Analyzer
```bash
poetry run python -m pyHaasAPI.cli.wfo_analyzer [OPTIONS]
```

**Options:**
- `--lab-id`: Lab ID to analyze
- `--start-date`: WFO start date (YYYY-MM-DD)
- `--end-date`: WFO end date (YYYY-MM-DD)
- `--training-days`: Training period duration
- `--testing-days`: Testing period duration
- `--mode`: WFO mode (rolling, fixed, expanding)
- `--dry-run`: Show what would be done without executing

#### 4. Mass Bot Creator
```bash
poetry run python -m pyHaasAPI.cli.mass_bot_creator [OPTIONS]
```

**Options:**
- `--top-count`: Number of top bots to create per lab
- `--activate`: Activate bots immediately after creation
- `--lab-ids`: Specific lab IDs to process
- `--exclude-lab-ids`: Lab IDs to exclude
- `--min-backtests`: Minimum backtests required to process lab
- `--min-winrate`: Minimum win rate threshold
- `--dry-run`: Show what would be done without executing

#### 5. Bot Trade Amount Manager
```bash
poetry run python -m pyHaasAPI.cli.fix_bot_trade_amounts [OPTIONS]
```

**Options:**
- `--method`: Calculation method (usdt, wallet)
- `--target-amount`: Target trade amount in USDT
- `--wallet-percentage`: Percentage of wallet balance
- `--bot-ids`: Specific bot IDs to update
- `--all-bots`: Update all bots
- `--leverage-recommendations`: Show leverage recommendations

#### 6. Account Cleanup
```bash
poetry run python -m pyHaasAPI.cli.account_cleanup [OPTIONS]
```

**Options:**
- `--dry-run`: Show what would be done without executing
- `--verbose`: Enable verbose logging

#### 7. Price Tracker
```bash
poetry run python -m pyHaasAPI.cli.price_tracker MARKET_TAG
```

**Example:**
```bash
poetry run python -m pyHaasAPI.cli.price_tracker BTC_USDT_PERPETUAL
```

---

## 🔌 API Integration

### Core API Functions

#### Authentication & Session Management
```python
from pyHaasAPI import api

# Authenticate
executor = api.authenticate(email, password)
executor = api.login_with_one_time_code(email, pincode)
```

#### Lab Management
```python
# Create lab
lab = api.create_lab(executor, CreateLabRequest(...))

# Get lab details
lab_details = api.get_lab_details(executor, lab_id)

# Start lab execution
api.start_lab_execution(executor, StartLabExecutionRequest(...))

# Get backtest results
results = api.get_backtest_result_page(executor, lab_id, 0, 100)
```

#### Bot Management
```python
# Create bot
bot = api.add_bot(executor, AddBotRequest(...))

# Create bot from lab
bot = api.add_bot_from_lab(executor, AddBotFromLabRequest(...))

# Edit bot parameters
api.edit_bot_parameter(executor, bot_id, parameter_name, value)

# Activate bot
api.activate_bot(executor, bot_id)
```

#### Account Management
```python
# Get accounts
accounts = api.get_accounts(executor)

# Get account data
account_data = api.get_account_data(executor, account_id)

# Rename account
api.rename_account(executor, account_id, new_name)
```

### Enhanced Execution
```python
from pyHaasAPI.enhanced_execution import EnhancedBacktestExecutor

# Initialize enhanced executor
enhanced_executor = EnhancedBacktestExecutor(executor)

# Execute with intelligence
result = enhanced_executor.execute_backtest_with_intelligence(
    lab_id=lab_id,
    start_date=start_date,
    end_date=end_date,
    auto_adjust=True
)
```

---

## 💾 Cache Management

### Unified Cache Structure
```
unified_cache/
├── backtests/              # Cached backtest runtime data
│   └── {lab_id}_{backtest_id}.json
├── reports/                # CSV analysis reports
│   └── lab_analysis_{lab_id}_{timestamp}.csv
├── logs/                   # Analysis logs
├── backtest_jobs.json      # Backtest job tracking
└── wfo_jobs.json          # WFO job tracking
```

### Cache Benefits
- **Avoids redundant API calls** for backtest data
- **Speeds up subsequent analysis** runs
- **Provides offline access** to analysis results
- **Enables historical analysis** tracking
- **Persistent job tracking** across sessions

### Cache Management
```python
from pyHaasAPI.analysis import UnifiedCacheManager

# Initialize cache manager
cache_manager = UnifiedCacheManager()

# Cache backtest data
cache_manager.cache_backtest_data(lab_id, backtest_id, data)

# Load cached data
cached_data = cache_manager.load_backtest_cache(lab_id, backtest_id)

# Save analysis report
cache_manager.save_analysis_report(lab_id, timestamp, report_data)
```

---

## 📚 Usage Examples

### Complete Pre-Bot Validation Workflow

```python
from pyHaasAPI.analysis import (
    HaasAnalyzer, 
    StrategyRobustnessAnalyzer, 
    BacktestManager,
    UnifiedCacheManager
)
from datetime import datetime

# Initialize components
cache_manager = UnifiedCacheManager()
analyzer = HaasAnalyzer(cache_manager)
robustness_analyzer = StrategyRobustnessAnalyzer(cache_manager)
backtest_manager = BacktestManager(cache_manager)

# Connect to API
analyzer.connect()
backtest_manager.connect(analyzer.executor)

# Step 1: Analyze lab for top backtests
lab_result = analyzer.analyze_lab("lab-id", top_count=5)

# Step 2: Analyze robustness
robustness_results = robustness_analyzer.analyze_lab_robustness(lab_result)

# Step 3: Filter safe strategies
safe_strategies = []
for backtest_id, metrics in robustness_results.items():
    if metrics.risk_level != "CRITICAL" and metrics.robustness_score > 50:
        safe_strategies.append(backtest_id)

# Step 4: Create individual backtests for validation
validation_jobs = []
for backtest_id in safe_strategies:
    backtest = next(bt for bt in lab_result.top_backtests if bt.backtest_id == backtest_id)
    
    job = backtest_manager.create_individual_backtest_with_cutoff(
        script_id=backtest.script_id,
        market_tag=backtest.market_tag,
        account_id="acc123",
        job_name=f"Validation_{backtest_id[:8]}"
    )
    validation_jobs.append(job)

# Step 5: Monitor validation jobs
while True:
    results = backtest_manager.monitor_jobs()
    if results['completed_jobs'] > 0:
        print(f"Completed {results['completed_jobs']} validation jobs")
        break
    time.sleep(30)

# Step 6: Create bots for validated strategies
for job in validation_jobs:
    if job.status == "completed" and job.results:
        # Create bot from validated backtest
        bot = analyzer.create_bot_from_backtest(
            backtest=job.results,
            bot_name=f"Validated_{job.job_id[:8]}"
        )
        print(f"Created bot: {bot.bot_id}")
```

### Mass Bot Creation with Robustness Filtering

```bash
# Step 1: Analyze robustness for all labs
poetry run python -m pyHaasAPI.cli.robustness_analyzer \
  --all-labs \
  --top-count 10 \
  --output robustness_report.txt

# Step 2: Create cutoff-based validation backtests for top strategies
poetry run python -m pyHaasAPI.cli.backtest_manager create-individual-cutoff \
  --script-id script123 \
  --market-tag BINANCE_BTC_USDT_ \
  --account-id acc123

# Step 3: Monitor validation jobs
poetry run python -m pyHaasAPI.cli.backtest_manager monitor

# Step 4: Create bots for validated strategies
poetry run python -m pyHaasAPI.cli.mass_bot_creator \
  --top-count 5 \
  --min-winrate 0.6 \
  --activate
```

### WFO Analysis Workflow

```bash
# Step 1: Create WFO lab
poetry run python -m pyHaasAPI.cli.backtest_manager create-wfo \
  --script-id script123 \
  --market-tag BINANCE_BTC_USDT_ \
  --account-id acc123 \
  --training-days 180 \
  --testing-days 60 \
  --num-periods 6

# Step 2: Monitor WFO progress
poetry run python -m pyHaasAPI.cli.backtest_manager monitor

# Step 3: Run WFO analysis
poetry run python -m pyHaasAPI.cli.wfo_analyzer \
  --lab-id lab123 \
  --start-date 2022-01-01 \
  --end-date 2023-12-31 \
  --training-days 180 \
  --testing-days 60 \
  --mode rolling
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
```
ModuleNotFoundError: No module named 'pydantic'
```
**Solution:** Install dependencies
```bash
poetry install
# or
pip install -r requirements.txt
```

#### 2. Authentication Issues
```
Failed to connect to HaasOnline API
```
**Solution:** Check environment variables
```bash
export API_EMAIL="your_email@example.com"
export API_PASSWORD="your_password"
export API_HOST="127.0.0.1"
export API_PORT="8090"
```

#### 3. Cutoff Discovery Failures
```
Failed to discover cutoff date: Unknown error
```
**Solution:** 
- Check if lab was created successfully
- Verify market tag format
- Ensure sufficient API permissions

#### 4. Job Monitoring Issues
```
Not connected to API. Cannot monitor jobs.
```
**Solution:** Ensure BacktestManager is connected
```python
backtest_manager.connect(executor)
```

#### 5. Cache Issues
```
Failed to load jobs: [Errno 2] No such file or directory
```
**Solution:** Cache files are created automatically on first use. This is normal for new installations.

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
poetry run python -m pyHaasAPI.cli.backtest_manager --verbose status
```

### Log Files

Check log files for detailed error information:
- Application logs: Console output with timestamps
- Cache logs: `unified_cache/logs/`
- Job tracking: `unified_cache/backtest_jobs.json`

### Performance Optimization

#### For Large-Scale Analysis
1. **Use caching**: Enable cache for repeated analysis
2. **Batch processing**: Process multiple labs in batches
3. **Parallel execution**: Use multiple API connections for concurrent operations
4. **Cleanup old data**: Regularly clean up old jobs and cache files

#### Memory Management
```python
# Clean up old jobs
backtest_manager.cleanup_old_jobs(days_old=7)

# Clear cache if needed
cache_manager.clear_cache()
```

---

## 🎯 Best Practices

### 1. Pre-Bot Validation Workflow
1. **Analyze robustness** first to filter out dangerous strategies
2. **Use cutoff-based backtests** for maximum data validation
3. **Monitor validation jobs** before creating bots
4. **Apply safety recommendations** (leverage, position size)

### 2. Risk Management
- **Always check robustness scores** before bot creation
- **Use recommended leverage levels** based on drawdown analysis
- **Monitor account balance** to prevent negative balances
- **Set appropriate trade amounts** based on account size

### 3. Performance Optimization
- **Cache backtest data** to avoid redundant API calls
- **Use batch operations** for multiple labs/bots
- **Monitor job status** regularly
- **Clean up old data** periodically

### 4. Error Handling
- **Check API connectivity** before operations
- **Validate input parameters** (market tags, account IDs)
- **Handle timeouts gracefully** for long-running operations
- **Log errors** for debugging

---

## 📈 Future Enhancements

### Planned Features
1. **Multi-Lab Analysis**: Analyze multiple labs simultaneously
2. **Advanced Risk Metrics**: More sophisticated risk calculations
3. **Real-Time Monitoring**: Live bot performance monitoring
4. **Portfolio Optimization**: Multi-strategy portfolio management
5. **Machine Learning Integration**: AI-powered strategy selection

### Contributing
1. **Report Issues**: Use GitHub issues for bug reports
2. **Feature Requests**: Submit enhancement proposals
3. **Code Contributions**: Follow the development workflow
4. **Documentation**: Help improve documentation

---

## 📞 Support

### Getting Help
1. **Check Documentation**: Review this comprehensive guide
2. **CLI Help**: Use `--help` flag for any CLI tool
3. **Logs**: Check console output and log files
4. **GitHub Issues**: Report bugs and request features

### Contact Information
- **Repository**: [pyHaasAPI GitHub](https://github.com/your-repo/pyHaasAPI)
- **Documentation**: This file and inline code documentation
- **Issues**: GitHub Issues for bug reports and feature requests

---

*Last Updated: September 7, 2025*
*Version: 2.3 - Comprehensive System Implementation*





