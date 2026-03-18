# pyHaasAPI

A Python client for the HaasOnline API, including tools for backtest data management, analysis, and visualization.

## 📊 Nexus Quant Command Center
A premium dashboard for unified HaasOnline & Freqtrade operations. [Read the Guide](docs/DASHBOARD_GUIDE.md)

### Features
*   **The Universe of Bots**: Interactive scatter plot (ROI vs Drawdown).
*   **Script Forge**: Autonomous HaasScript dependency resolution & auto-repair.
*   **Unified Arena**: Run Haas Cloud and Freqtrade Vectorized tests in one UI.
*   **Lab Inspector**: Drill down into specific labs to find top performers.

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
