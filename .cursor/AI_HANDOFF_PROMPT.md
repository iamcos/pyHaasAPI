# AI Handoff Prompt: pyHaasAPI Project

## Current State
We have successfully downloaded ~78,000 backtest reports from 3 servers (srv01, srv02, srv03) into `unified_cache`.

## Key Capabilities & Tools

### 1. Visualization Dashboard ("Haas Data Viz")
**Location**: `viz_app.py`, `run_viz.sh`
**Purpose**: Interactive Streamlit dashboard to analyze the backtest universe.
**Workflow**:
1. Run `python3 aggregate_backtests.py` to parse raw JSONs -> `backtest_data.parquet`.
   - *Note*: Calculates "True ROI" and "Drawdown" from raw `FinishedPositions`, ignoring JSON metrics.
2. Run `./run_viz.sh` to launch the dashboard.

### 2. Data Management
- **Download**: `download_missing_reports.py` (Targeted), `DownloadCLI` (Bulk).
- **Sync**: `sync_cache_to_backtests.py` flattens the nested cache structure.
- **Verification**: `verify_backtest_counts.py` audits local data against servers.

### 3. Data Recovery / Transfer
- **Restore**: `restore_cache.py` reassembles split zip parts (`unified_cache.zip.part_*`) into the full archive.
- **Upload**: `upload_parts.py` handles chunked uploads to Telegram.

## Important Context
- **Data Source**: `unified_cache/backtests/*.json`
- **Aggregation**: We use `backtest_data.parquet` for performance. If new data is downloaded, re-run `aggregate_backtests.py`.
- **Metrics**: Always use the **CUSTOM calculated metrics** in `aggregate_backtests.py` as the source of truth for ROI/ROE/Drawdown.
