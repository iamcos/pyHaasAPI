# Backtest Results Processing Guide

## Overview

This guide documents the comprehensive backtest results processing system in the pyHaasAPI project. The system provides multiple layers of data processing, analysis, and caching to ensure efficient handling of backtest data.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Flow](#data-flow)
3. [Caching System](#caching-system)
4. [Processing Pipeline](#processing-pipeline)
5. [Output Formats](#output-formats)
6. [Usage Examples](#usage-examples)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

## System Architecture

The backtest results processing system consists of several interconnected components:

### Core Components

1. **Data Fetching Layer** (`fetch_lab_backtests.py`)
   - Fetches backtest data from HaasOnline API
   - Handles pagination and rate limiting
   - Manages API authentication

2. **Caching Layer** (`backtest_cache/`)
   - Stores processed data for quick access
   - Uses both pickle and JSON formats
   - Implements intelligent cache invalidation

3. **Processing Layer** (`backtest_execution/`)
   - Analyzes raw backtest data
   - Calculates performance metrics
   - Generates analytics reports

4. **Storage Layer** (`cache/` directories)
   - Organized by lab ID and timestamp
   - JSON files for human-readable data
   - CSV reports for analysis

## Data Flow

```
HaasOnline API → Data Fetching → Raw Data Storage → Processing → Analytics → Caching → Output
```

### Step-by-Step Flow

1. **API Connection**: Authenticate with HaasOnline API
2. **Data Fetching**: Retrieve backtest results with pagination
3. **Raw Storage**: Save complete backtest data to JSON files
4. **Processing**: Analyze performance metrics and trade data
5. **Analytics**: Generate comprehensive reports
6. **Caching**: Store processed results for future access
7. **Output**: Create CSV reports and summary files

## Caching System

### Yes, caching happens by default! 

The system implements a multi-layered caching approach:

### 1. **Backtest Cache Directory** (`backtest_cache/`)

**Location**: `backtest_cache/`
**Format**: Pickle files with hash-based naming
**Purpose**: Fast access to processed backtest objects

```
backtest_cache/
├── cache.db                    # SQLite database for metadata
├── 2751638c6281007e3f355b4e92ab5929.pkl  # Pickled backtest data
├── 9693c717f7ad3ba03529962d090fda98.pkl  # Pickled backtest data
└── ...
```

**Features**:
- Hash-based file naming for deduplication
- SQLite database for metadata tracking
- Automatic cache invalidation
- Thread-safe access

### 2. **Lab-Specific Cache** (`cache/lab_backtests_*`)

**Location**: `cache/lab_backtests_{lab_id}_{timestamp}/`
**Format**: JSON files organized by structure
**Purpose**: Human-readable, organized backtest data

```
cache/lab_backtests_caed4df4-bcf9-4d4c-a8af-a51af6b7982e_20250108_143022/
├── backtests_list.json         # Complete list of backtests
├── backtests_analytics.csv     # Processed analytics
└── backtest_details/           # Individual backtest files
    ├── backtest_id_1.json
    ├── backtest_id_2.json
    └── ...
```

**Features**:
- Timestamped directories for versioning
- Complete raw data preservation
- Individual backtest files for detailed analysis
- CSV reports for spreadsheet analysis

### 3. **History Intelligence Cache** (`data/history_cutoffs.json`)

**Location**: `data/history_cutoffs.json`
**Format**: JSON with backup system
**Purpose**: Store cutoff dates and history intelligence data

**Features**:
- Automatic backup creation
- Thread-safe operations
- Corruption recovery
- Version control

## Processing Pipeline

### 1. **Data Fetching** (`fetch_lab_backtests.py`)

```python
def fetch_all_backtests(executor: RequestsExecutor, lab_id: str, max_backtests: int = 1000):
    """Fetch all backtests from the lab with pagination"""
    # Handles pagination automatically
    # Returns list of backtest objects
```

**Key Features**:
- Automatic pagination handling
- Rate limiting protection
- Error recovery
- Progress logging

### 2. **Raw Data Storage** (`dump_raw_data`)

```python
def dump_raw_data(executor: RequestsExecutor, backtests: List[Dict[str, Any]], output_dir: str, lab_id: str):
    """Dump raw backtest data to JSON files"""
    # Creates organized directory structure
    # Saves both list and individual files
    # Includes runtime data fetching
```

**Output Structure**:
- `backtests_list.json`: Complete backtest list
- `backtest_details/`: Individual backtest files
- Runtime data included automatically

### 3. **Analytics Processing** (`analyze_backtest`)

```python
def analyze_backtest(executor: RequestsExecutor, backtest: Any, lab_id: str) -> Optional[Dict[str, Any]]:
    """Analyze a single backtest and return analytics"""
    # Extracts performance metrics
    # Calculates trade statistics
    # Compares against buy & hold
```

**Metrics Calculated**:
- ROI percentage
- Win rate
- Total trades and positions
- Maximum drawdown
- Fees analysis
- Buy & hold comparison

### 4. **Report Generation** (`create_csv_report`)

```python
def create_csv_report(analytics: List[Dict[str, Any]], output_dir: str):
    """Create CSV report with all analytics"""
    # Generates comprehensive CSV
    # Includes all calculated metrics
    # Sorted by performance
```

## Output Formats

### 1. **JSON Files** (Raw Data)

**Structure**:
```json
{
  "backtest_id": "uuid",
  "script_name": "Strategy Name",
  "generation": "1",
  "population": "1",
  "runtime": {
    "Reports": {
      "report_key": {
        "PR": {
          "PC": 15.5,
          "RP": 155.0,
          "ROI": 15.5,
          "RM": -5.2
        },
        "F": {
          "TFC": 2.5
        }
      }
    },
    "FinishedPositions": [...],
    "UnmanagedPositions": [...]
  }
}
```

### 2. **CSV Reports** (Analytics)

**Columns**:
- `backtest_id`: Unique identifier
- `script_name`: Strategy name
- `roi_percentage`: Return on investment
- `win_rate`: Percentage of winning trades
- `total_trades`: Number of completed trades
- `realized_profits_usdt`: Total profit in USDT
- `max_drawdown`: Maximum drawdown percentage
- `fees_usdt`: Total fees paid
- `beats_buy_hold`: Boolean comparison
- `start_time`/`end_time`: Execution period
- `orders`/`positions`: Trade statistics

### 3. **Pickle Files** (Cached Objects)

**Purpose**: Fast object serialization for programmatic access
**Usage**: Loaded automatically by the system
**Format**: Python objects with metadata

## Usage Examples

### 1. **Basic Backtest Fetching**

```python
from fetch_lab_backtests import main

# Run the complete pipeline
main()
```

### 2. **Custom Lab Analysis**

```python
import os
from fetch_lab_backtests import fetch_all_backtests, analyze_backtest, create_csv_report

# Setup
lab_id = "your-lab-id"
executor = get_authenticated_executor()

# Fetch backtests
backtests = fetch_all_backtests(executor, lab_id, max_backtests=100)

# Analyze each backtest
analytics = []
for backtest in backtests:
    analysis = analyze_backtest(executor, backtest, lab_id)
    if analysis:
        analytics.append(analysis)

# Generate report
create_csv_report(analytics, "output_directory")
```

### 3. **Accessing Cached Data**

```python
import json
import os

# Find most recent cache
cache_dir = "cache"
lab_dirs = [d for d in os.listdir(cache_dir) 
           if d.startswith("lab_backtests_") and os.path.isdir(os.path.join(cache_dir, d))]
latest_dir = sorted(lab_dirs)[-1]

# Load analytics
csv_file = os.path.join(cache_dir, latest_dir, "backtests_analytics.csv")
# Use pandas or csv module to read

# Load raw data
list_file = os.path.join(cache_dir, latest_dir, "backtests_list.json")
with open(list_file, 'r') as f:
    backtests = json.load(f)
```

### 4. **Individual Backtest Analysis**

```python
# Load specific backtest
backtest_id = "your-backtest-id"
detail_file = os.path.join(cache_dir, latest_dir, "backtest_details", f"{backtest_id}.json")

with open(detail_file, 'r') as f:
    backtest_data = json.load(f)

# Access runtime data
runtime = backtest_data.get('runtime', {})
reports = runtime.get('Reports', {})
```

## Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your-email@example.com
API_PASSWORD=your-password

# Processing Configuration
MAX_BACKTESTS=1000
PAGE_SIZE=100
```

### Script Configuration

```python
# In fetch_lab_backtests.py
lab_id = "caed4df4-bcf9-4d4c-a8af-a51af6b7982e"  # Your lab ID
max_backtests = 1000  # Maximum backtests to fetch
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API credentials in `.env` file
   - Check API host and port settings
   - Ensure HaasOnline API is running

2. **Cache Issues**
   - Clear cache directory: `rm -rf cache/`
   - Check file permissions
   - Verify disk space

3. **Processing Errors**
   - Check log files for detailed error messages
   - Verify backtest data completeness
   - Ensure all dependencies are installed

4. **Memory Issues**
   - Reduce `max_backtests` parameter
   - Process backtests in smaller batches
   - Monitor system memory usage

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

1. **Batch Processing**: Process backtests in smaller batches
2. **Parallel Processing**: Use multiple threads for analysis
3. **Selective Loading**: Load only required data fields
4. **Cache Management**: Regular cache cleanup

## Advanced Features

### 1. **History Intelligence**

The system includes advanced history intelligence features:
- Cutoff date discovery
- History synchronization
- Data quality validation

### 2. **Real-time Processing**

For live backtest monitoring:
- WebSocket connections
- Real-time data streaming
- Live performance tracking

### 3. **Custom Analytics**

Extend the analytics system:
- Custom performance metrics
- Risk analysis
- Portfolio optimization

## Best Practices

1. **Regular Backups**: Keep copies of important cache directories
2. **Version Control**: Use timestamped directories for data versioning
3. **Data Validation**: Always verify data completeness
4. **Performance Monitoring**: Track processing times and resource usage
5. **Error Handling**: Implement robust error recovery
6. **Documentation**: Document custom analysis procedures

## Conclusion

The backtest results processing system provides a comprehensive solution for fetching, analyzing, and caching backtest data. The multi-layered caching system ensures efficient data access while maintaining data integrity and providing multiple output formats for different use cases.

The system is designed to be:
- **Scalable**: Handles large numbers of backtests
- **Reliable**: Includes error recovery and data validation
- **Flexible**: Supports custom analysis and reporting
- **Efficient**: Implements intelligent caching and optimization

For additional support or feature requests, refer to the project documentation or create an issue in the repository.
