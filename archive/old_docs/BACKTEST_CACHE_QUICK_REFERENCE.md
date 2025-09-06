# Backtest Cache Quick Reference

## Quick Answer: Yes, caching happens by default!

The system automatically saves backtest data in multiple formats for efficient access and processing.

## Cache Locations

### 1. **Lab-Specific Cache** (Human-readable)
```
cache/lab_backtests_{lab_id}_{timestamp}/
├── backtests_list.json         # Complete backtest list
├── backtests_analytics.csv     # Processed analytics
└── backtest_details/           # Individual backtest files
    ├── backtest_id_1.json
    ├── backtest_id_2.json
    └── ...
```

### 2. **System Cache** (Fast access)
```
backtest_cache/
├── cache.db                    # SQLite metadata
├── 2751638c6281007e3f355b4e92ab5929.pkl  # Pickled data
└── 9693c717f7ad3ba03529962d090fda98.pkl  # Pickled data
```

## Quick Usage Examples

### Load Latest Cache
```python
from backtest_cache_example import BacktestCacheManager

cache_manager = BacktestCacheManager()
latest_cache = cache_manager.get_latest_lab_cache()
analytics = cache_manager.load_analytics_csv(latest_cache)
```

### Access Specific Backtest
```python
# Load backtest details
details = cache_manager.load_backtest_details(latest_cache, "backtest_id")

# Access runtime data
runtime = details.get('runtime', {})
reports = runtime.get('Reports', {})
```

### Get Performance Summary
```python
from backtest_cache_example import BacktestAnalyzer

analyzer = BacktestAnalyzer(cache_manager)
summary = analyzer.generate_performance_summary(analytics)
top_performers = analyzer.find_top_performers(analytics, 'roi_percentage', 5)
```

## Data Structure

### Analytics CSV Columns
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

### JSON Structure
```json
{
  "backtest_id": "uuid",
  "script_name": "Strategy Name",
  "runtime": {
    "Reports": {
      "report_key": {
        "PR": {
          "PC": 15.5,    // Buy & hold performance
          "RP": 155.0,   // Realized profit
          "ROI": 15.5,   // Return on investment
          "RM": -5.2     // Max drawdown
        },
        "F": {
          "TFC": 2.5     // Total fees
        }
      }
    },
    "FinishedPositions": [...],
    "UnmanagedPositions": [...]
  }
}
```

## Common Operations

### 1. Find Best Performers
```python
# Top 10 by ROI
top_roi = analyzer.find_top_performers(analytics, 'roi_percentage', 10)

# Top 10 by win rate
top_winrate = analyzer.find_top_performers(analytics, 'win_rate', 10)
```

### 2. Filter Profitable Backtests
```python
profitable = [a for a in analytics if a.get('roi_percentage', 0) > 0]
beating_buyhold = [a for a in analytics if a.get('beats_buy_hold', False)]
```

### 3. Analyze by Script
```python
script_stats = analyzer.analyze_script_performance(analytics)
for script, stats in script_stats.items():
    print(f"{script}: {stats['avg_roi']:.2f}% ROI, {stats['profitable_percentage']:.1f}% profitable")
```

## Cache Management

### Clear Cache
```bash
# Clear all cache
rm -rf cache/
rm -rf backtest_cache/

# Clear specific lab cache
rm -rf cache/lab_backtests_*
```

### Check Cache Status
```python
# Get pickle cache info
pickle_info = cache_manager.get_pickle_cache_info()
print(f"Cache size: {pickle_info['total_size']} bytes")
print(f"Files: {len(pickle_info['files'])}")
```

## Performance Tips

1. **Use CSV for bulk analysis** - Faster than loading individual JSON files
2. **Use pickle cache for programmatic access** - Optimized for Python objects
3. **Filter data early** - Don't load unnecessary backtest details
4. **Cache frequently accessed data** - Store computed statistics

## Error Handling

### Common Issues
```python
# Check if cache exists
if not latest_cache:
    print("No cache found. Run fetch_lab_backtests.py first.")

# Check if analytics exist
if not analytics:
    print("No analytics data found in cache.")

# Handle missing backtest details
details = cache_manager.load_backtest_details(latest_cache, backtest_id)
if not details:
    print(f"Backtest {backtest_id} not found in cache.")
```

## Integration with Other Tools

### Pandas Analysis
```python
import pandas as pd

# Load CSV directly
df = pd.read_csv(latest_cache / "backtests_analytics.csv")

# Filter and analyze
profitable_df = df[df['roi_percentage'] > 0]
print(f"Profitable backtests: {len(profitable_df)}")
```

### Export to Excel
```python
import pandas as pd

df = pd.read_csv(latest_cache / "backtests_analytics.csv")
df.to_excel("backtest_analysis.xlsx", index=False)
```

## Automation

### Scheduled Cache Updates
```python
# Run daily cache update
import schedule
import time

def update_cache():
    # Run fetch_lab_backtests.py
    os.system("python fetch_lab_backtests.py")

schedule.every().day.at("09:00").do(update_cache)

while True:
    schedule.run_pending()
    time.sleep(60)
```

This quick reference covers the most common operations with the backtest caching system. For detailed documentation, see `BACKTEST_RESULTS_PROCESSING_GUIDE.md`.
