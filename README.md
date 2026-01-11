# pyHaasAPI

A Python client for the HaasOnline API, including tools for backtest data management, analysis, and visualization.

## 📊 Backtest Visualization Dashboard
A custom Streamlit dashboard ("Haas Data Viz") is available to analyze thousands of backtest results.

### Features
*   **The Universe of Bots**: Interactive scatter plot (ROI vs Drawdown) to spot outliers.
*   **Noise Reduction**: Filters out "junk" bots (low trades, negative ROI) by default.
*   **True Metrics**: Recalulates ROI, Win Rate, and Drawdown from raw trade data.
*   **Lab Inspector**: Drill down into specific labs to find their top performers.

### Quick Start
1. **Hydrate Data**: Aggregate the raw JSON backtests into a high-performance dataset.
    ```bash
    python3 aggregate_backtests.py
    ```
    *(Creates `backtest_data.parquet`)*

2. **Launch Dashboard**:
    ```bash
    ./run_viz.sh
    ```
    Open `http://localhost:8501` in your browser.

## 🛠️ Utility Scripts

### Data Management
*   `download_missing_reports.py`: Targeted downloader for fetching missing backtests from srv01/srv02/srv03.
*   `sync_cache_to_backtests.py`: Symlinks nested `runtime_reports` to a flat `backtest` directory for analysis.
*   `verify_backtest_counts.py`: Audit script to compare server vs. local backtest counts.

### Data Recovery
*   `restore_cache.py`: Reassembles and unzips the split `unified_cache.zip.part_*` files.
*   `upload_parts.py`: Uploads large archives to Telegram using the MCP tool.
