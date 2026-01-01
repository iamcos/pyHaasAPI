import json
import os
from config import settings
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.model import GetBacktestResultRequest, LabBacktestSummary
from .backtest_fetcher import BacktestFetcher, BacktestFetchConfig

def extract_chart_datapoints(filepath: str, indicator_name: str) -> dict:
    """
    Extracts data points for a specific indicator from a saved chart JSON file.

    Args:
        filepath: The absolute path to the chart JSON file.
        indicator_name: The name of the indicator to extract (e.g., "STOCH", "KC", "bbands").

    Returns:
        A dictionary of data points (timestamp: value) for the specified indicator,
        or an empty dictionary if not found.
    """
    try:
        with open(filepath, 'r') as f:
            chart_data = json.load(f)

        if not chart_data.get('Success') or not chart_data.get('Data'):
            print(f"Error: Invalid chart data format in {filepath}")
            return {}

        charts_section = chart_data['Data'].get('Charts', {})
        
        for plot_id, plot_data in charts_section.items():
            data_lines = plot_data.get('DataLines', {})
            for line_key, line_data in data_lines.items():
                # The 'Name' field might contain the indicator name, or we might need to infer it
                # from the 'Guid' or other properties. For now, let's assume 'Name' is descriptive.
                if indicator_name.lower() in line_data.get('Name', '').lower():
                    return line_data.get('DataPoints', {})
                # Also check if the indicator name is part of the line_key (e.g., rgba(0, 255, 0, 1.00) for STOCH)
                # This is a heuristic and might need refinement based on actual data
                if indicator_name.lower() in line_key.lower():
                    return line_data.get('DataPoints', {})

    except FileNotFoundError:
        print(f"Error: Chart file not found at {filepath}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
    except Exception as e:
        print(f"An unexpected error occurred while extracting chart data: {e}")
    return {}

def get_full_backtest_data(executor, lab_id: str, backtest_id: str) -> dict:
    """
    Fetches and consolidates all available data for a single backtest.

    Args:
        executor: An authenticated pyHaasAPI executor instance.
        lab_id: The ID of the lab.
        backtest_id: The ID of the specific backtest.

    Returns:
        A dictionary containing consolidated backtest data, or an empty dictionary if data cannot be fetched.
    """
    consolidated_data = {}
    try:
        # Get basic backtest result item using centralized fetcher
        fetcher = BacktestFetcher(executor, BacktestFetchConfig(page_size=100))
        all_backtests = fetcher.fetch_all_backtests(lab_id)
        item = next((i for i in all_backtests if i.backtest_id == backtest_id), None)

        if not item:
            print(f"Error: Backtest {backtest_id} not found in lab {lab_id}.")
            return {}

        consolidated_data.update(item.dict())

        # Fetch detailed runtime data
        runtime_response = api.get_backtest_runtime(executor, lab_id=lab_id, backtest_id=backtest_id)
        if runtime_response:
            consolidated_data['runtime_data'] = runtime_response

            # Extract orders from FinishedPositions and UnmanagedPositions
            orders_data = []
            finished_positions = runtime_response.get('FinishedPositions', [])
            unmanaged_positions = runtime_response.get('UnmanagedPositions', [])
            for pos in finished_positions + unmanaged_positions:
                if 'eno' in pos: # Entry orders
                    orders_data.extend(pos['eno'])
                if 'exo' in pos: # Exit orders
                    orders_data.extend(pos['exo'])
            consolidated_data['orders_data'] = orders_data
            
            # Positions data is the FinishedPositions and UnmanagedPositions themselves
            consolidated_data['positions_data'] = finished_positions + unmanaged_positions

            # Extract detailed trade information
            detailed_trades = []
            for pos in finished_positions + unmanaged_positions:
                # Assuming each position represents a single logical trade for simplicity
                # and that eno and exo contain the relevant order details.
                # If a position can have multiple entry/exit order pairs forming distinct trades,
                # this logic would need to be expanded.

                entry_order = pos.get('eno', [{}])[0] # Get first entry order, or empty dict if none
                exit_order = pos.get('exo', [{}])[0]  # Get first exit order, or empty dict if none

                # Extracting relevant fields. Adjust key names if they differ in actual API response.
                trade_info = {
                    'ProfitLoss': float(exo[0].get('pr', 0.0)), # Use 'pr' from exit order
                    'ExitTime': exit_order.get('ct', 0),
                    'EntryTime': entry_order.get('ct', 0),
                    'TradeAmount': float(entry_order.get('m', 0.0)), # Use 'm' from entry order
                    'ExitPrice': float(exit_order.get('p', 0.0)),
                    'EntryPrice': float(entry_order.get('p', 0.0)),
                    'PositionId': pos.get('g', '')
                }
                print(f"DEBUG: Position ID: {pos.get('g')}, ProfitLoss: {pos.get('rp')}, TradeAmount: {entry_order.get('m')}, EntryPrice: {entry_order.get('p')}, ExitPrice: {exit_order.get('p')}")
                detailed_trades.append(trade_info)
            consolidated_data['detailed_trades'] = detailed_trades

            # Logs data
            consolidated_data['logs_data'] = runtime_response.get('ExecutionLog', [])

            # Update summary from runtime_data's Reports section
            detailed_summary = {}
            if 'Reports' in runtime_response and runtime_response['Reports']:
                report_key = list(runtime_response['Reports'].keys())[0]
                detailed_summary = runtime_response['Reports'][report_key]
            
            # Ensure summary is a dictionary before updating
            if 'summary' not in consolidated_data or not isinstance(consolidated_data['summary'], dict):
                consolidated_data['summary'] = {}

            consolidated_data['summary']['Orders'] = detailed_summary.get('O', {}).get('F', 0) 
            consolidated_data['summary']['Trades'] = detailed_summary.get('O', {}).get('F', 0) 
            consolidated_data['summary']['Positions'] = detailed_summary.get('P', {}).get('C', 0) 
            consolidated_data['summary']['FeeCosts'] = detailed_summary.get('F', {}).get('FC', 0.0) 
            consolidated_data['summary']['RealizedProfits'] = detailed_summary.get('PR', {}).get('RP', 0.0) 
            consolidated_data['summary']['ReturnOnInvestment'] = detailed_summary.get('PR', {}).get('ROI', 0.0) 

            # Extract InputFields (parameters) from runtime_data
            consolidated_data['script_parameters_from_runtime'] = runtime_response.get('InputFields', {})

            # Extract more detailed metrics from Reports
            if detailed_summary:
                consolidated_data['detailed_reports'] = detailed_summary
                consolidated_data['roi_history'] = detailed_summary.get('PR', {}).get('ROIH', [])
                consolidated_data['realized_profit_history'] = detailed_summary.get('PR', {}).get('RPH', [])
                consolidated_data['winning_positions'] = detailed_summary.get('P', {}).get('W', 0)
                consolidated_data['losing_positions'] = detailed_summary.get('P', {}).get('L', 0)
                consolidated_data['average_win'] = detailed_summary.get('P', {}).get('AW', 0.0)
                consolidated_data['average_loss'] = detailed_summary.get('P', {}).get('AL', 0.0)

            # Extract FinishedPositions directly
            consolidated_data['finished_positions_data'] = runtime_response.get('FinishedPositions', [])

            # Extract top-level bot/script metadata
            consolidated_data['bot_id'] = runtime_response.get('BotId', '')
            consolidated_data['bot_name'] = runtime_response.get('BotName', '')
            consolidated_data['script_id'] = runtime_response.get('ScriptId', '')
            consolidated_data['script_name'] = runtime_response.get('ScriptName', '')
            consolidated_data['account_id'] = runtime_response.get('AccountId', '')
            consolidated_data['price_market'] = runtime_response.get('PriceMarket', '')
            consolidated_data['leverage'] = runtime_response.get('Leverage', 0.0)
            consolidated_data['margin_mode'] = runtime_response.get('MarginMode', 0)
            consolidated_data['position_mode'] = runtime_response.get('PositionMode', 0)
            consolidated_data['trade_amount'] = runtime_response.get('TradeAmount', 0.0)
            consolidated_data['default_interval'] = runtime_response.get('DefaultInterval', 0)
            consolidated_data['default_chart_type'] = runtime_response.get('DefaultChartType', 0)

    except api.HaasApiError as e:
        print(f"HaasAPI Error fetching data for backtest {backtest_id}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred fetching data for backtest {backtest_id}: {e}")
    return consolidated_data

def get_backtest_summary(executor, lab_id: str, backtest_id: str) -> dict:
    """
    Fetches and returns the summary data for a specific backtest.
    """
    data = get_full_backtest_data(executor, lab_id, backtest_id)
    return data.get('summary', {})

def get_backtest_parameters(executor, lab_id: str, backtest_id: str) -> dict:
    """
    Fetches and returns the parameters used for a specific backtest.
    """
    data = get_full_backtest_data(executor, lab_id, backtest_id)
    return data.get('parameters', {})

def get_backtest_settings(executor, lab_id: str, backtest_id: str) -> dict:
    """
    Fetches and returns the settings for a specific backtest.
    """
    data = get_full_backtest_data(executor, lab_id, backtest_id)
    return data.get('settings', {})

def get_backtest_orders(executor, lab_id: str, backtest_id: str) -> list:
    """
    Fetches and returns the orders data for a specific backtest.
    """
    data = get_full_backtest_data(executor, lab_id, backtest_id)
    return data.get('orders_data', [])

def get_backtest_positions(executor, lab_id: str, backtest_id: str) -> list:
    """
    Fetches and returns the positions data for a specific backtest.
    """
    data = get_full_backtest_data(executor, lab_id, backtest_id)
    return data.get('positions_data', [])

def get_backtest_logs(executor, lab_id: str, backtest_id: str) -> list:
    """
    Fetches and returns the logs data for a specific backtest.
    """
    data = get_full_backtest_data(executor, lab_id, backtest_id)
    return data.get('logs_data', [])

def create_lab_from_file(executor, filepath: str) -> dict:
    """
    Creates a new lab on the server from a lab configuration file.

    Args:
        executor: An authenticated pyHaasAPI executor instance.
        filepath: The absolute path to the lab configuration JSON file.

    Returns:
        A dictionary representing the newly created LabDetails, or an empty dictionary on failure.
    """
    try:
        with open(filepath, 'r') as f:
            lab_config = json.load(f)
        
        # Assuming lab_config contains the necessary fields for CreateLabRequest
        # You might need to map these fields explicitly if the file format differs
        from pyHaasAPI_v1.model import CreateLabRequest
        req = CreateLabRequest(
            script_id=lab_config['script_id'],
            name=lab_config['name'],
            account_id=lab_config['account_id'],
            market=lab_config['market'],
            interval=lab_config['interval'],
            default_price_data_style=lab_config['default_price_data_style'],
            trade_amount=lab_config.get('trade_amount', 100.0),
            chart_style=lab_config.get('chart_style', 300),
            order_template=lab_config.get('order_template', 500),
            leverage=lab_config.get('leverage', 0.0),
            position_mode=lab_config.get('position_mode', 0),
            margin_mode=lab_config.get('margin_mode', 0)
        )
        new_lab = api.create_lab(executor, req)
        print(f"Successfully created lab: {new_lab.name} (ID: {new_lab.lab_id})")
        return new_lab.dict()
    except FileNotFoundError:
        print(f"Error: Lab configuration file not found at {filepath}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
    except KeyError as e:
        print(f"Error: Missing key in lab configuration file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating lab from file: {e}")
    return {}

def get_script_parameter_config(backtest_data: dict) -> dict:
    """
    Extracts the script parameters from a full backtest data object
    in a format suitable for applying to a bot.

    Args:
        backtest_data: A dictionary containing consolidated backtest data
                       (e.g., from get_full_backtest_data).

    Returns:
        A dictionary of script parameters, or an empty dictionary if not found.
    """
    settings = backtest_data.get('settings', {})
    return settings.get('script_parameters', {})
