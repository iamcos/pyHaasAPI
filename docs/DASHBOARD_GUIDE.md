# 📊 Nexus Quant Dashboard Guide

Welcome to the **Nexus Quant Command Center**, a premium, unified interface for managing your HaasOnline and Freqtrade trading operations. This dashboard bridges the gap between high-performance cloud strategy execution and local vectorized backtesting.

## 🚀 Quick Start

To launch the dashboard server:

```bash
# From the project root
PYTHONPATH=. poetry run python dashboard/server.py
```

Then open [http://localhost:8080](http://localhost:8080) in your browser.

---

## 🏗️ Core Modules

### 1. Command Center (Global Status)
The "Empire Status" overview. Provides a high-level summary of your active bots, consolidated PNL, and server health.
- **Engine Toggles**: Filter metrics for Haas, Freqtrade, or view a combined "Global" state.
- **Server Selector**: Switch between `srv01`, `srv02`, and `srv03`. The dashboard automatically manages SSH tunnels and session re-authentication.

### 2. Script Forge (NEW & Autonomous)
The **Script Forge** is the heart of the project's autonomous maintenance system.
- **Target Selection**: Pick any script from your library.
- **Auto-Repair**: Triggers the `ScriptLifecycleManager` to parse the script, hunt for missing `CC_` dependencies, and orchestrate recursive compilations.
- **Autonomous Console**: Watch real-time logs as the engine builds your script dependency graph and validates it against the Haas server.

### 3. Backtest Arena
Unified testing environment where you can run simulations on both engines side-by-side.
- **Freqtrade Mode**: Runs local vectorized backtests via CLI.
- **Haas Mode**: Routes requests to the cloud servers for production-grade verification.
- **Metrics View**: Clean visualization of ROI, Drawdown, and Sharpe ratios.

### 4. Deep Analytics
A vault of previously executed backtests.
- **Cached Records**: Search and filter thousands of historical results without querying the live servers.
- **Performance Grids**: Dissect strategy DNA to find top-performing parameter combinations.

### 5. Strategy Mixology
Experimental lab for combining successful strategy traits.
- **DNA Extraction**: Select multiple successful bots to extract their parameter logic.
- **Synthesis**: Breed new configurations using genetic crossover or aggressive-extreme algorithms.

---

## 🛠️ Configuration & Tunnels

The dashboard manages its own connectivity via the `ServerManager`:
- **SSH Tunnels**: When you switch servers in the UI, a background process kills old tunnels and establishes new ones to the target server's API port (default `8090`).
- **Session Persistence**: Authentication is handled via the `AuthenticationManager`, ensuring your session remains active even when switching networks.

## 📁 File Structure
- `dashboard/server.py`: Aiohttp-based backend orchestrator.
- `dashboard/app.js`: Interactive frontend logic (using Lucide icons & ApexCharts).
- `dashboard/style.css`: Premium Glassmorphism design system.
- `.gemini_tmp/`: Scratchpad for transient logs and autonomous task results.

---

## ❓ Troubleshooting

**Q: "Haas not connected" error?**
- Ensure your `.env` file has the correct `API_EMAIL` and `API_PASSWORD`.
- Check if your SSH key is authorized for the target server.

**Q: Backtests are hanging?**
- For Freqtrade, ensure you have downloaded the required market data using the `freqtrade download-data` command first.
- For Haas, check the server-side logs in HTS to see if there is a compiler error.

---
*Created by Antigravity for the pyHaasAPI Project.*
