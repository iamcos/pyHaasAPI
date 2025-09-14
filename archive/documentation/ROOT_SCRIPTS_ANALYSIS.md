# Root Scripts Analysis & Cleanup Plan

## Overview
Analysis of root-level Python scripts to identify duplicates of API/CLI functionality and create cleanup plan.

## Script Categories

### 1. Analysis Scripts (DUPLICATE - API Available)
**Functionality:** Lab analysis, backtest analysis, bot filtering
**API Equivalent:** `pyHaasAPI.analysis.analyzer.HaasAnalyzer`
**CLI Equivalent:** `pyHaasAPI.cli.main` (analyze command)

- ✅ `analyze_10_backtests.py` → **DUPLICATE** - Use `HaasAnalyzer.analyze_lab()`
- ✅ `analyze_all_backtests.py` → **DUPLICATE** - Use `HaasAnalyzer.analyze_lab()` + mass bot creator
- ✅ `analyze_all_cached_backtests.py` → **DUPLICATE** - Use `HaasAnalyzer` with cache
- ✅ `analyze_top_bot.py` → **DUPLICATE** - Use `HaasAnalyzer.analyze_lab()`
- ✅ `filter_viable_bots.py` → **DUPLICATE** - Use `mass_bot_creator.py` with filtering
- ✅ `reanalyze_cached_backtests.py` → **DUPLICATE** - Use `HaasAnalyzer` with cache

### 2. WFO Analysis Scripts (DUPLICATE - API Available)
**Functionality:** Walk Forward Optimization analysis
**API Equivalent:** `pyHaasAPI.analysis.wfo.WFOAnalyzer`
**CLI Equivalent:** `pyHaasAPI.cli.wfo_analyzer`

- ✅ `generate_comprehensive_wfo_report.py` → **DUPLICATE** - Use `WFOAnalyzer`
- ✅ `debug_wfo.py` → **DUPLICATE** - Use `WFOAnalyzer` with debug mode

### 3. Debug Scripts (ARCHIVE - Development Tools)
**Functionality:** Debugging and investigation tools
**Status:** Development tools, should be archived

- ✅ `debug_backtest_data.py` → **ARCHIVE** - Development tool
- ✅ `debug_balance_analysis.py` → **ARCHIVE** - Development tool
- ✅ `debug_bot_config.py` → **ARCHIVE** - Development tool
- ✅ `debug_cached_data.py` → **ARCHIVE** - Development tool
- ✅ `debug_nested_reports.py` → **ARCHIVE** - Development tool
- ✅ `debug_reports_data.py` → **ARCHIVE** - Development tool
- ✅ `debug_runtime_data.py` → **ARCHIVE** - Development tool
- ✅ `debug_trades.py` → **ARCHIVE** - Development tool
- ✅ `investigate_balance_anomaly.py` → **ARCHIVE** - Development tool
- ✅ `find_balance_fields.py` → **ARCHIVE** - Development tool
- ✅ `find_real_balance.py` → **ARCHIVE** - Development tool

### 4. Status Check Scripts (DUPLICATE - API Available)
**Functionality:** Backtest status checking
**API Equivalent:** `pyHaasAPI.api.get_lab_execution_update()`

- ✅ `check_backtest_status.py` → **DUPLICATE** - Use `api.get_lab_execution_update()`
- ✅ `check_backtest_status_proper.py` → **DUPLICATE** - Use `api.get_lab_execution_update()`
- ✅ `simple_status_check.py` → **DUPLICATE** - Use `api.get_lab_execution_update()`

### 5. Test Scripts (ARCHIVE - Development Tools)
**Functionality:** Testing and validation
**Status:** Development tools, should be archived

- ✅ `test_balance_fix.py` → **ARCHIVE** - Development test
- ✅ `test_direct_backtest_correct.py` → **ARCHIVE** - Development test
- ✅ `test_direct_backtest.py` → **ARCHIVE** - Development test
- ✅ `test_enhanced_analysis.py` → **ARCHIVE** - Development test
- ✅ `test_robustness_analysis.py` → **ARCHIVE** - Development test
- ✅ `test_trade_extraction.py` → **ARCHIVE** - Development test
- ✅ `test_week_backtest.py` → **ARCHIVE** - Development test
- ✅ `test_wfo_with_cache.py` → **ARCHIVE** - Development test

### 6. Data Retrieval Scripts (DUPLICATE - API Available)
**Functionality:** Data retrieval and processing
**API Equivalent:** `pyHaasAPI.tools.utils.BacktestFetcher`

- ✅ `get_detailed_backtest_results.py` → **DUPLICATE** - Use `BacktestFetcher`

### 7. Generated Files (CLEANUP - Temporary Output)
**Functionality:** Generated reports and data files
**Status:** Temporary output files, should be cleaned up

- ✅ `all_backtests_analysis_*.json` → **CLEANUP** - Generated reports
- ✅ `analysis_report_*.json` → **CLEANUP** - Generated reports
- ✅ `detailed_drawdown_analysis_*.json` → **CLEANUP** - Generated reports
- ✅ `filtered_viable_bots_*.json` → **CLEANUP** - Generated reports
- ✅ `viable_bots_*.json` → **CLEANUP** - Generated reports
- ✅ `comprehensive_robustness_report.txt` → **CLEANUP** - Generated report
- ✅ `balance_anomaly_investigation.png` → **CLEANUP** - Generated image
- ✅ `bot_c44453ee_profit_curve.png` → **CLEANUP** - Generated image

## Cleanup Plan

### Phase 1: Archive Duplicate Scripts
Move scripts that duplicate API/CLI functionality to `archive/obsolete_scripts/`

### Phase 2: Archive Development Tools
Move debug and test scripts to `archive/development_tools/`

### Phase 3: Clean Generated Files
Remove temporary output files and generated reports

### Phase 4: Update Documentation
Update cursor rules and documentation to reflect the cleanup

## Benefits
- ✅ Clean root directory
- ✅ Eliminate confusion about which tools to use
- ✅ Encourage use of proper API/CLI interfaces
- ✅ Reduce maintenance burden
- ✅ Professional repository structure






