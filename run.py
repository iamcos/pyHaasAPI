import os
import sys
import json

# Add project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import necessary modules from your project
from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest, LabBacktestSummary, BacktestRuntimeData, BotRuntimeData
from utils.backtest_tools import get_full_backtest_data, extract_chart_datapoints, create_lab_from_file, get_script_parameter_config
from utils.research_tools import research_indicator_parameters

# Define global constants for convenience
LAB_ID = '55b45ee4-9cc5-42f7-8556-4c3aa2b13a44'
SCRIPT_ID = '7dda6a1e59594d4588b62619a848a6ae'
BOT_ID = '59774e3e57054fdea15991bb1b407f9c' # Example Bot ID from your provided runtime

# Initialize executor (authentication will happen on first use)
_executor = None
def get_executor():
    global _executor
    if _executor is None:
        _executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
    return _executor


def fetch_and_save_all_backtest_results():
    """
    Fetches all backtest results for LAB_ID and saves them to JSON files.
    """
    OUTPUT_DIR = f'experiments/bt_analysis/raw_results/lab_{LAB_ID}'
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    executor = get_executor()

    next_page_id = 0
    page_length = 100

    while True:
        print(f"Fetching page {next_page_id}...")
        req = GetBacktestResultRequest(lab_id=LAB_ID, next_page_id=next_page_id, page_lenght=page_length)
        backtest_results_page = api.get_backtest_result(executor, req)

        if not backtest_results_page.items:
            print("No more results found.")
            break

        for item in backtest_results_page.items:
            print(f"Processing backtest: {item.backtest_id}")
            # Use the new get_full_backtest_data function
            full_data = get_full_backtest_data(executor, LAB_ID, item.backtest_id)

            if full_data:
                file_path = os.path.join(OUTPUT_DIR, f"{item.backtest_id}.json")
                with open(file_path, 'w') as f:
                    json.dump(full_data, f, indent=2)
                print(f"Saved backtest result to {file_path}")
            else:
                print(f"Skipping saving backtest {item.backtest_id} due to incomplete data.")
        
        if backtest_results_page.next_page_id == next_page_id: 
            break
        next_page_id = backtest_results_page.next_page_id

import pandas as pd
from utils import analysis_tools

def analyze_backtest_results():
    """
    Analyzes saved backtest results to identify top and diverse configurations using heuristics.
    """
    RESULTS_DIR = f'experiments/bt_analysis/raw_results/lab_{LAB_ID}'
    all_results = []
    for filename in os.listdir(RESULTS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RESULTS_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_results.append(data)
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {filepath}")
                continue

    analyzed_results = []
    for result in all_results:
        summary = result.get('summary')
        if not summary:
            continue

        detailed_trades = result.get('detailed_trades')
        if not detailed_trades:
            print(f"Skipping backtest {result.get('backtest_id')} due to missing detailed trades data.")
            continue
        print(f"DEBUG: detailed_trades for {result.get('backtest_id')}: {detailed_trades}") # Add this line
        try:
            df = pd.DataFrame(detailed_trades)
            if df.empty:
                print(f"Skipping backtest {result.get('backtest_id')} due to empty DataFrame after conversion.")
                continue

            # Ensure all expected columns are present
            expected_cols = ['ProfitLoss', 'ExitTime', 'EntryTime', 'TradeAmount', 'ExitPrice', 'EntryPrice']
            if not all(col in df.columns for col in expected_cols):
                print(f"Missing expected columns in trades data for backtest {result.get('backtest_id')}. Available columns: {df.columns.tolist()}")
                continue

            df['pnl'] = df['ProfitLoss']
            df['exit_date'] = pd.to_datetime(df['ExitTime'], unit='s')
            df['entry_date'] = pd.to_datetime(df['EntryTime'], unit='s')
            df['position_size'] = df['TradeAmount']
            df['exit_price'] = df['ExitPrice']
            df['entry_price'] = df['EntryPrice']

        except KeyError as e:
            print(f"Missing expected key in trades data for backtest {result.get('backtest_id')}: {e}")
            continue
        except Exception as e:
            print(f"Error processing trades data for backtest {result.get('backtest_id')}: {e}")
            continue

        heuristic_metrics = {}
        for heuristic_cls in analysis_tools.list_heuristics():
            try:
                metrics = heuristic_cls.calculate(df)
                heuristic_metrics.update(metrics)
            except ValueError as e:
                print(f"Heuristic {heuristic_cls.__name__} failed for backtest {result.get('backtest_id')}: {e}")
            except Exception as e:
                print(f"Error calculating {heuristic_cls.__name__} for backtest {result.get('backtest_id')}: {e}")

        analyzed_results.append({
            'backtest_id': result.get('backtest_id'),
            'summary': summary,
            'parameters': result.get('parameters', {}),
            'settings': result.get('settings', {}),
            'heuristic_metrics': heuristic_metrics
        })

    # Ranking strategy: Prioritize Sharpe Ratio, then Total Return, then Win Rate
    def rank_key(item):
        metrics = item['heuristic_metrics']
        sharpe = metrics.get('Sharpe Ratio', -float('inf'))
        total_return = metrics.get('Total Return (%)', -float('inf'))
        win_rate = metrics.get('Win Rate', -float('inf'))
        return (sharpe, total_return, win_rate)

    analyzed_results.sort(key=rank_key, reverse=True)

    print("--- Top Backtest Configurations (Analyzed by Heuristics) ---")
    if not analyzed_results:
        print("No backtests found for analysis.")
    for i, bot in enumerate(analyzed_results[:5]): # Display top 5
        print(f"\nBot {i+1}:")
        print(f"  Backtest ID: {bot['backtest_id']}")
        print(f"  Summary ROI: {bot['summary'].get('ReturnOnInvestment', 0.0):.2f}%")
        print(f"  Summary Positions: {bot['summary'].get('Positions', 0)}")
        print(f"  Summary Orders: {bot['summary'].get('Orders', 0)}")
        print(f"  Parameters: {json.dumps(bot['parameters'], indent=2)}")
        print(f"  Settings: {json.dumps(bot['settings'], indent=2)}")
        print(f"  Heuristic Metrics: {json.dumps(bot['heuristic_metrics'], indent=2)}")



def research_script_indicators():
    """
    Initiates the research workflow for script indicators.
    """
    executor = get_executor()
    research_indicator_parameters(executor, SCRIPT_ID)

def get_bot_runtime_example():
    """
    Fetches and prints the full runtime data for a specific bot.
    """
    executor = get_executor()
    try:
        bot_runtime = api.get_full_bot_runtime_data(executor, BOT_ID)
        print(json.dumps(bot_runtime.dict(), indent=2))
    except Exception as e:
        print(f"Error fetching bot runtime data: {e}")


# Main execution block (example usage)
if __name__ == "__main__":
    # Example of how you might call functions from run.py
    # You can uncomment and modify these calls based on your current task

    # Phase 1: Fetch and Analyze Backtest Results
    # fetch_and_save_all_backtest_results() # Commented out as data is already saved
    analyze_backtest_results()

    # Research Indicators (Manual Web Search Step)
    # research_script_indicators()

    # Example of fetching bot runtime data
    # get_bot_runtime_example()

    print("\n--- Manual Web Search Required ---")
    print("Please perform the searches for the queries printed above.")
    print("Copy the relevant titles, URLs, and snippets from the search results.")
    print("Then, provide them back to me so I can process and summarize the recommendations.")