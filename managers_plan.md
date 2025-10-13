# Managers Plan (v2-only)

## Goal
Clone template lab to BTC/TRX/ADA on the specified account, configure naming and $2000-equivalent trade amounts, sync 36-month history, discover each lab's cutoff using the refined algorithm, finalize names with cutoff dates, and start all labs (one running, others queued).

## Integration Targets
- `pyHaasAPI/core/simple_trading_orchestrator.py`: integrate longest-backtest discovery via `LongestBacktestService`.
- `pyHaasAPI/services/longest_backtest_service.py`: orchestrates clone → config → sync → cutoff → rename → start.
- `pyHaasAPI/services/lab_clone_manager.py`: v2 clone + market/account set.
- `pyHaasAPI/services/lab_config_manager.py`: v2 rename + trade amount set.
- `pyHaasAPI/services/sync_history_manager.py`: v2 register (historical fetch), `BacktestAPI.get_history_status`, `set_history_depth`.

## Algorithm (refined)
1. Start at 36 months.
2. Decrease by 1 month until status RUNNING.
3. Add 2 weeks; if still RUNNING, add 1 more week.
4. Decrease by 2 days until RUNNING; target cutoff within 1–2 days.
5. Wait 5 seconds between start and status check; force-cancel before each test.

## Naming
Format: `1 | TRX | Simple RSING VWAP Strategy | - DD.MM.YYYY` (date added after cutoff discovery).

## Flow (single server srv03 via tunnel 8090)
1. Clone template lab to BTC/TRX/ADA with account assignment.
2. Pre-rename (without date) and set $2000 USDT-equivalent trade amounts using `MarketAPI.get_price_data`.
3. Register markets and sync 36 months with `BacktestAPI`.
4. Ensure no labs are running; discover cutoff per lab (sequential).
5. Finalize names with cutoff date; start all labs at discovered periods.

## v2 APIs Used
- Lab: `clone_lab`, `get_lab_details`, `update_lab_details`, `start_lab_execution`, `cancel_lab_execution`, `get_lab_execution_status`.
- Market: `get_price_data`, `get_historical_data` (registration trigger).
- Backtest: `get_history_status`, `set_history_depth`.

## Orchestrator Hook
In `SimpleTradingOrchestrator._discover_all_cutoffs(...)`, invoke `LongestBacktestService.orchestrate_clone_config_sync_and_find_cutoff` with the template lab, account, stage, and markets for this server.

## Success Criteria
- v2-only; no v1 dependencies.
- All labs stopped before discovery; history depth set to 36 months.
- Cutoff found for each lab; names finalized; all labs started (1 running, others queued).