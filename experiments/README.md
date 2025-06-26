# Experiments

This folder contains experimental features, prototypes, and UI explorations for the pyHaasAPI project. These are not part of the stable API client, but serve as sandboxes for new ideas and workflows.

## Current Experiment: Textual TUI Backtester

### Description
A Textual-based terminal UI for backtesting the "Haasonline Original - Scalper Bot" on multiple markets. Features include:
- Fuzzy-searchable, multi-select market list with exchange filter
- Parameter presets (Default, Aggressive, Conservative)
- Backtest period presets (YTD, Last 3 Months, Last Month)
- Save/load for market lists and parameter/period presets
- Single-screen interface with keyboard navigation
- Results log and tips section

### What is Done
- UI scaffolded with Textual (Header, Footer, Parameters, Markets, Period, Results)
- Market selector with fuzzy search, exchange filter, and multi-select
- Parameter and period preset dropdowns
- Keyboard navigation and tips
- Results log area

### What is To Do
- Fix fuzzy search matching and market list layout issues
- Improve DataTable navigation (disable left/right, fix highlight)
- Integrate real backtesting logic (currently UI only)
- Add save/load for presets and market lists
- Add error handling and user feedback
- Polish UI/UX and documentation

## How to Run
From the project root:
```bash
pip install -r requirements.txt
python experiments/textual_backtester.py
```

---

For more information, see the main project README. 