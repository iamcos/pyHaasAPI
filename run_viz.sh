#!/bin/bash
# Helper script to run the Haas Data Viz Dashboard

# Ensure we are in the repo root
cd "$(dirname "$0")"

# Activate the environment used for aggregation
source /home/cosmos/Documents/github/telegram-mcp/venv/bin/activate

# Check if data exists
if [ ! -f "backtest_data.parquet" ]; then
    echo "⚠️  backtest_data.parquet not found! Running aggregation first..."
    python3 aggregate_backtests.py
fi

# Run Streamlit
echo "🚀 Launching Haas Data Viz..."
streamlit run viz_app.py
