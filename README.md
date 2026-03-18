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

## 🛠️ Technology Stack & Acknowledgments

### Dashboard Frontend
- **Glassmorphism UI**: Custom Vanilla CSS framework.
- **Charts**: [ApexCharts](https://apexcharts.com/) for equity curves and bot performance plots.
- **Icons**: [Lucide](https://lucide.dev/) for crisp, minimalist iconography.
- **Intelligence Terminal (Crucix)**: Integrated data visualizations using:
    - [D3.js](https://d3js.org/) for data-driven OSINT feeds.
    - [Three.js](https://threejs.org/) for the global operational globe.
    - [Globe.gl](https://globe.gl/) for the interactive 3D tactical map.
    - [GSAP](https://greensock.com/gsap/) for smooth micro-animations.

### Backend Orchestrator
- **aiohttp**: Fast, asynchronous Python web server.
- **pyHaasAPI Core**: Custom library for unified HaasOnline/Freqtrade communication.

## 📄 License & Terms

**Copyright (c) 2024–2026 Cosmos (iamcos)**

This Software is released under a **Research-Only License**.

1. **Research & Personal Use**: You are free to use, modify, and study this codebase for academic or personal experimentation.
2. **Commercial/Live Trading**: Use of this software for managing **real money** or in a **commercial setting** is strictly prohibited without prior written consent and a separate licensing agreement. 
3. **Contact**: If you intend to use this for financial gain or live trading, you **MUST** contact the author via [GitHub](https://github.com/iamcos) to discuss terms and procedure.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. USE AT YOUR OWN RISK.
