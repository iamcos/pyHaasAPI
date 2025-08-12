### **Phase 1: Initial Backtest Analysis & Top Result Identification (Current Focus)**
**Goal:** Analyze the results of your initial 100 backtests (2-year duration, timeframe optimization) to identify top-performing and diverse configurations using advanced heuristics.

1.  **Retrieve Lab Details:** Completed. Lab `55b45ee4-9cc5-42f7-8556-4c3aa2b13a44` details (parameters, settings) have been fetched.
2.  **Fetch and Save Raw Backtest Results:** Completed. Detailed backtest results (summary, orders, positions, logs) for all backtests have been fetched using `get_full_backtest_data` and saved as individual JSON files in `experiments/bt_analysis/raw_results/lab_55b45ee4-9cc5-42f7-8556-4c3aa2b13a44/`.
3.  **Identify Top & Diverse Configurations:** (In Progress). Implement a robust analysis using various heuristics (e.g., Equity Curve Stability, Performance Metrics, Trades Analysis, Risk Analysis, Trades Distribution, Realized vs. Open Profit) to identify the best-performing and diverse backtest configurations. The settings from `InputFields` will also be saved and considered during this analysis.

### **Phase 2: Deeper Optimization with Indicator Parameters (3-Year Backtest) (Future)**
**Goal:** Take the selected configurations from Phase 1 and perform a more in-depth optimization by varying indicator parameters over a 3-year period.

1.  **Parameter Identification:** (To be defined based on web search and user input).
2.  **Generate New Backtest Configurations:** (To be implemented).
3.  **Execution (User Action Required):** (To be implemented).
4.  **Result Collection & Analysis:** (To be implemented).

### **Phase 3: Comprehensive Parameter Influence Mapping (Quick Backtest Series) (Future)**
**Goal:** Understand the granular influence of all parameters on bot behavior through a large series of short-duration backtests.

1.  **Exhaustive Parameter Combination Generation:** (To be implemented).
2.  **Execute Quick Backtests (User Action Required):** (To be implemented).
3.  **Data Collection & Influence Analysis:** (To be implemented).

### **New Workflow: Automated Indicator Parameter Research (In Progress - Manual Web Search Step)**
**Goal:** Automate the research phase for identifying optimal indicator parameters.

1.  **Identify Strategy/Indicators from Script:** Implemented in `utils/research_tools.py` using `script_record.settings.script_parameters`.
2.  **Formulate Search Queries:** Implemented in `utils/research_tools.py` to generate and print search queries.
3.  **Execute Web Search:** **Manual Step.** You will need to manually execute the printed search queries using `google_web_search` (or your preferred search engine) and provide the results back to me.
4.  **Process and Present Results:** (To be implemented once web search results are provided).

### **Script-Agnostic Design Principle:**
Throughout all phases, the implementation will strive to be script-agnostic by:
*   Dynamically inspecting the `parameters` and `settings.script_parameters` fields of the `LabDetails` object rather than hardcoding parameter names or types.
*   Using generic metrics from `LabBacktestSummary` for performance evaluation.

### **Analysis of Results & Parameter Ranges (Clarification)**
*   **Phase 1 (2-year, timeframe ranges):** Extracted KPIs (`RealizedProfits`, `ReturnOnInvestment`, `FeeCosts`, `Orders`, `Positions`) and specific parameter values. Analysis will now involve applying various heuristics (Equity Curve Stability, Performance Metrics, Trades Analysis, Risk Analysis, Trades Distribution, Realized vs. Open Profit) to identify the best-performing and diverse backtests. The settings from `InputFields` will be saved and used in this analysis.
*   **Phase 2 (3-year, indicator ranges):** Similar data extraction and filtering. Focus on correlating performance with varied indicator parameters to find optimal ranges/values and interactions.
*   **Phase 3 (Quick Backtest Series):** Collect granular data (input parameters, concise output metrics). Analyze sensitivity of bot behavior to parameter changes, including univariate analysis and preparing data for external multivariate analysis (e.g., regression, heatmaps, clustering).

### **Chart Data Handling (Decision)**
*   Chart data will **not** be included in the main backtest JSON files for Phase 1 and Phase 2 due to its size and primary use for visual analysis. The ability to process chart backtest data will be retained for future use, potentially for quick backtests or on-demand analysis.

---

### **Current Status of Backtest Analysis Debugging:**

The primary goal is to correctly extract and analyze detailed trade information from backtest results.

**Problem Identified:**
The analysis script (`run.py`) is encountering `RuntimeWarning`s (division by zero) because the `ProfitLoss` and `TradeAmount` fields within the `detailed_trades` data are consistently zero, even though the overall `Summary ROI` indicates non-zero profits/losses. This suggests that the correct data for individual trades is not being extracted.

**Debugging Steps Taken:**
1.  Initially, `utils/backtest_tools.py` was modified to extract `detailed_trades` from `FinishedPositions` and `UnmanagedPositions` using assumed keys (`PL`, `Time`, `Amount`, `Price`, `ID`).
2.  Upon observing zero values, the key mappings were adjusted based on a closer inspection of the raw JSON structure, changing `ProfitLoss` to `rp` (from the position object) and `TradeAmount` to `m` (from the entry order).
3.  Further debug prints were added to `utils/backtest_tools.py` and `run.py` to inspect the raw position data and the extracted `detailed_trades` list at various stages.

**Current Findings:**
The debug output confirms that even with the updated key mappings, the `ProfitLoss` and `TradeAmount` values being extracted into `detailed_trades` are `0.0`. This strongly suggests that the actual trade-level profit/loss and trade amount data are *not* located in the `rp` field of the position object or the `m` field of the entry order as previously assumed.

**Next Steps (for the new session):**
The next session should focus on a deeper investigation of the raw backtest JSON data. We need to meticulously examine the entire `runtime_data` and `Reports` sections, looking for any fields or nested structures that contain non-zero values for individual trade profit/loss and trade amounts. It's possible these values are aggregated or stored under different, less obvious keys.