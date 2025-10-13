## Server Content Revision Project (srv03)

Purpose
- End-to-end workflow to snapshot server labs/bots, fetch limited backtest data per lab, analyze, and create bots while avoiding duplicates. Target server: srv03 via mandated SSH tunnel.

Environment & Constraints
- v2-only runtime; use existing APIs/services in `pyHaasAPI/`.
- Connectivity via `ServerManager` (single-tunnel policy: 8090, 8092). Use `preflight_check()`.
- Run Python inside `.venv`; kill stray processes before long runs.
- No mocks; real servers/data. Primary testing on srv03.
- Field access safety: use `getattr`/`hasattr`, validate critical fields, honor timeouts/retries.
 - Default server is configurable via `API_DEFAULT_SERVER` (defaults to `srv03`).

High-Level Phases
1) Snapshot
   - List labs and bots; map bots to labs; collect coins; compute coverage (labs without bots; coins without labs/bots).
2) Download (Quick Mode)
   - For labs missing cache or needing refresh: download last N (e.g., 5) backtests per lab and store in unified cache format.
3) Analysis
   - Zero-drawdown filtering with min win rate; sort by ROE; produce reports (summary + per-lab top picks).
4) Bot Creation (Duplicate-Safe)
   - Create bots from analysis results using centralized naming scheme; skip if an equivalent bot already exists.
5) Project Mode (Auto)
   - One command to run snapshot → download-5-per-lab → analyze → duplicate-safe bot creation.

Initial Scope (MVP)
- CLI: `cli_ref/ProjectManagerCLI` built on `EnhancedBaseCLI` reusing `AnalysisManager`, `BotManager`, `ReportManager`.
- Commands:
  - `snapshot` (server state: labs, bots, coins, coverage)
  - `fetch --lab-id LAB --count 5` or `fetch-all --count 5` (download limited backtests)
  - `analyze --min-winrate 55 --sort-by roe`
  - `create-bots --bots-per-lab 1`
  - `run --quick` (auto pipeline)
- Duplicate detection: check existing bots (by naming or lab/backtest tuple) before creation.

Naming Scheme (Existing)
- Centralized in `cli_ref/bot_manager.py`:
- Format: "Lab Name - Script Name - ROI% pop/gen WinRate%".
- For now, keep as-is; consider optional server/coin scoping later.

Testing Discipline (srv03)
- Use `ServerManager.ensure_srv03_tunnel()` and `preflight_check()`.
- Kill stray processes before runs; enforce timeouts.
- Validate against real data; avoid unbounded loops.

Implementation Progress

✅ **Completed Tasks**
- [x] Analyze `cli_ref/` and identify reusable managers.
- [x] Create native `services/ServerContentManager` for snapshot, gaps/duplicates, resumable fetch (5 per lab).
- [x] Add `default_server` configuration via `API_DEFAULT_SERVER` env var (defaults to `srv03`).
- [x] Enhance `core/simple_trading_orchestrator.py` to use `Settings.default_server` when no servers specified.
- [x] Implement resumable fetch: download 5 backtests per lab with resume capability.

✅ **Recently Completed**
- [x] Integrate duplicate bot detection into bot creation flows in services.
- [x] Add thin CLI in `cli_ref/` that delegates to services for project mode with `--server` flags.
- [x] Enhance `SimpleTradingOrchestrator` to use `ServerContentManager` snapshot and skip duplicates.

📋 **Next Steps**
- [ ] Write cache in unified schema (reuse existing unified cache utilities where available).
- [ ] Quick mode: limit to 5 backtests per lab for initial tests.
- [ ] End-to-end test on srv03; generate a snapshot report and analysis summary.

**Current Architecture**
- `ServerContentManager`: Native service for server snapshot, gap analysis, duplicate detection, resumable fetch
- `SimpleTradingOrchestrator`: Enhanced to respect `Settings.default_server` fallback
- `Settings`: Added `default_server` field with env override `API_DEFAULT_SERVER`
- Services exported via `services/__init__.py` for CLI consumption

Quick Start (once implemented)
- Activate venv and run via tunnel:
  - `source .venv/bin/activate && pkill -f python || true`
  - `timeout 30 python -m pyHaasAPI.cli_ref.project_manager snapshot --server srv02`  # override default
  - `timeout 60 python -m pyHaasAPI.cli_ref.project_manager fetch-all --count 5`
  - `timeout 60 python -m pyHaasAPI.cli_ref.project_manager analyze --min-winrate 55 --sort-by roe`
  - `timeout 60 python -m pyHaasAPI.cli_ref.project_manager create-bots --bots-per-lab 1`
  - Or: `timeout 120 python -m pyHaasAPI.cli_ref.project_manager run --quick --server srv01 srv02`

Artifacts
- Snapshot report (JSON): labs, bots, coins, coverage map.
- Analysis report: per-lab top backtests (zero-drawdown, sorted by ROE).
- Bot creation report: created/skipped (duplicate) bots with reasons.

Notes
- Keep CLIs thin; main logic in APIs/services and centralized managers.
- Add safe cancellations and bounded timers for any long operations.
 - All authentication and connectivity via `ServerManager` and `AuthenticationManager`.

