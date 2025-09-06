#!/usr/bin/env python3
"""
Fetch and analyze backtests from a specific lab
Dumps raw data and creates CSV with analytics
"""

import os
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor, get_full_backtest_runtime_data
from pyHaasAPI.model import GetBacktestResultRequest
from pyHaasAPI.backtest_object import BacktestObject
from lab_to_bot_automation.wfo_analyzer import WFOAnalyzer, WFOConfig

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_output_directory(lab_id: str) -> str:
    """Create output directory for this lab's data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("cache", f"lab_backtests_{lab_id}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Created output directory: {output_dir}")
    return output_dir

def fetch_backtests_page(executor: RequestsExecutor, lab_id: str, next_page_id: int = 0, page_size: int = 100) -> Dict[str, Any]:
    """Fetch a single page of backtests"""
    try:
        request = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=next_page_id,
            page_lenght=page_size
        )
        
        response = api.get_backtest_result(executor, request)
        
        if response and response.items:
            logger.info(f"Fetched page with next_page_id {next_page_id}: {len(response.items)} backtests")
            return {
                "Data": response.items,
                "Success": True,
                "next_page_id": response.next_page_id
            }
        else:
            logger.info(f"No backtests found for page with next_page_id {next_page_id}")
            return {"Data": [], "Success": True, "next_page_id": None}
            
    except Exception as e:
        logger.error(f"Error fetching page with next_page_id {next_page_id}: {e}")
        return {"Data": [], "Success": False, "Error": str(e)}

def fetch_all_backtests(executor: RequestsExecutor, lab_id: str, max_backtests: int = 1000) -> List[Dict[str, Any]]:
    """Fetch all backtests from the lab"""
    all_backtests = []
    next_page_id = 0
    page_size = 100
    
    logger.info(f"Starting to fetch up to {max_backtests} backtests from lab {lab_id}")
    
    while len(all_backtests) < max_backtests:
        response = fetch_backtests_page(executor, lab_id, next_page_id, page_size)
        
        if not response.get('Success', False):
            logger.error(f"Failed to fetch page with next_page_id {next_page_id}: {response.get('Error', 'Unknown error')}")
            break
            
        backtests = response.get('Data', [])
        if not backtests:
            logger.info(f"No more backtests found with next_page_id {next_page_id}")
            break
            
        all_backtests.extend(backtests)
        logger.info(f"Total backtests fetched so far: {len(all_backtests)}")
        
        # Get next page ID for pagination
        next_page_id = response.get('next_page_id')
        if not next_page_id:
            logger.info("Reached last page (no next_page_id)")
            break
    
    logger.info(f"Finished fetching {len(all_backtests)} backtests")
    return all_backtests[:max_backtests]

def dump_raw_data(executor: RequestsExecutor, backtests: List[Dict[str, Any]], output_dir: str, lab_id: str):
    """Dump raw backtest data to JSON files"""
    # Dump the main backtests list
    backtests_file = os.path.join(output_dir, "backtests_list.json")
    with open(backtests_file, 'w') as f:
        json.dump(backtests, f, indent=2, default=str)
    logger.info(f"Dumped backtests list to {backtests_file}")
    
    # Dump individual backtest details
    details_dir = os.path.join(output_dir, "backtest_details")
    os.makedirs(details_dir, exist_ok=True)
    
    for i, backtest in enumerate(backtests):
        backtest_id = getattr(backtest, 'backtest_id', f"backtest_{i}")
        detail_file = os.path.join(details_dir, f"{backtest_id}.json")
        with open(detail_file, 'w') as f:
            # Convert backtest object to dict for JSON serialization
            backtest_dict = {attr: getattr(backtest, attr, None) for attr in dir(backtest)
                           if not attr.startswith('_') and not callable(getattr(backtest, attr, None))}

            # Fetch and include runtime data if not already present
            if hasattr(backtest, 'runtime') and backtest.runtime is None:
                try:
                    runtime_data = get_full_backtest_runtime_data(executor, lab_id, backtest_id)
                    if runtime_data:
                        backtest_dict['runtime'] = runtime_data.model_dump() if hasattr(runtime_data, 'model_dump') else runtime_data
                except Exception as e:
                    logger.warning(f"Could not fetch runtime data for {backtest_id}: {e}")

            json.dump(backtest_dict, f, indent=2, default=str)

def analyze_backtest(executor: RequestsExecutor, backtest: Any, lab_id: str) -> Optional[Dict[str, Any]]:
    """Analyze a single backtest and return analytics"""
    try:
        backtest_id = backtest.backtest_id if hasattr(backtest, 'backtest_id') else str(backtest)
        if not backtest_id:
            logger.warning("Backtest missing backtest_id")
            return None

        # Get full runtime data
        try:
            runtime_data = get_full_backtest_runtime_data(executor, lab_id, backtest_id)
            if not runtime_data:
                logger.warning(f"Could not get runtime data for {backtest_id} - returned None")
                return None
            logger.info(f"Successfully got runtime data for {backtest_id}, type: {type(runtime_data)}")
        except Exception as e:
            logger.error(f"Error getting runtime data for {backtest_id}: {e}")
            return None

        # Create backtest object
        backtest_obj = BacktestObject(executor, lab_id, backtest_id)

        # Store runtime data in backtest object for later use
        if hasattr(backtest, 'runtime'):
            backtest.runtime = runtime_data

        # Debug: Print runtime data structure if it's the first backtest
        if backtest_id == "51284b78-80e8-4560-9308-9303b597b7ec":  # First backtest ID from sample
            # Convert Pydantic model to dict if needed
            if hasattr(runtime_data, 'model_dump'):
                raw_data = runtime_data.model_dump()
            else:
                raw_data = runtime_data

            logger.info(f"First backtest runtime data keys: {list(raw_data.keys())}")
            if 'Reports' in raw_data:
                logger.info(f"Reports found: {len(raw_data['Reports'])} reports")
                for report_key in list(raw_data['Reports'].keys())[:1]:  # First report only
                    report = raw_data['Reports'][report_key]
                    logger.info(f"Report {report_key} keys: {list(report.keys())}")
                    if 'PR' in report:
                        logger.info(f"PR data: {report['PR']}")
                    if 'F' in report:
                        logger.info(f"F data: {report['F']}")
        
        # Extract basic info from backtest object
        analysis = {
            'backtest_id': backtest_id,
            'script_name': '',  # Will be populated from runtime if available
            'generation': getattr(backtest, 'generation', ''),
            'population': getattr(backtest, 'population', ''),
            'interval': getattr(backtest, 'interval', ''),
            'rising_length': getattr(backtest, 'rising_length', ''),
            'vwap_window': getattr(backtest, 'vwap_window', ''),
            'stop_loss_percentage': getattr(backtest, 'stop_loss_percentage', ''),
            'stop_loss_shrinkage': getattr(backtest, 'stop_loss_shrinkage', ''),
            'start_time': '',  # Will be populated from runtime
            'end_time': '',    # Will be populated from runtime
        }

        # Extract data from runtime structure
        if runtime_data:
            # Convert Pydantic model to dict if needed
            if hasattr(runtime_data, 'model_dump'):
                runtime_dict = runtime_data.model_dump()
            else:
                runtime_dict = runtime_data

            # Extract analytics from Reports section
            if 'Reports' in runtime_dict:
                for report_key, report_data in runtime_dict['Reports'].items():
                    if 'F' in report_data and 'TFC' in report_data['F']:
                        analysis['fees_usdt'] = float(report_data['F']['TFC'])

                    if 'PR' in report_data:
                        pr_data = report_data['PR']
                        analysis['pc_value'] = float(pr_data.get('PC', 0.0))
                        analysis['realized_profits_usdt'] = float(pr_data.get('RP', 0.0))
                        analysis['roi_percentage'] = float(pr_data.get('ROI', 0.0))
                        analysis['max_drawdown'] = float(pr_data.get('RM', 0.0))

                    if 'AID' in report_data:
                        analysis['account_id'] = report_data['AID']
                    if 'M' in report_data:
                        analysis['market_tag'] = report_data['M']

                    break  # Use first report

            # Extract script information from runtime
            if 'ScriptId' in runtime_dict:
                analysis['script_id'] = runtime_dict['ScriptId']
            if 'ScriptName' in runtime_dict:
                analysis['script_name'] = runtime_dict['ScriptName']

            # Extract timestamps from runtime
            if 'Timestamp' in runtime_dict:
                analysis['end_time'] = str(runtime_dict['Timestamp'])
            if 'MinuteTimestamp' in runtime_dict:
                analysis['start_time'] = str(runtime_dict['MinuteTimestamp'])

            # Extract trade data from runtime
            total_trades = 0
            winning_trades = 0
            losing_trades = 0
            total_orders = 0
            total_positions = 0

            # Count trades and positions from runtime data
            # Check both FinishedPositions and UnmanagedPositions
            positions_data = []
            if 'FinishedPositions' in runtime_dict and isinstance(runtime_dict['FinishedPositions'], list):
                positions_data.extend(runtime_dict['FinishedPositions'])
            if 'UnmanagedPositions' in runtime_dict and isinstance(runtime_dict['UnmanagedPositions'], list):
                positions_data.extend(runtime_dict['UnmanagedPositions'])

            for position in positions_data:
                if isinstance(position, dict):
                    total_positions += 1
                    # Count entry orders
                    if 'eno' in position and isinstance(position['eno'], list):
                        total_orders += len(position['eno'])
                    # Count exit orders
                    if 'exo' in position and isinstance(position['exo'], list):
                        total_orders += len(position['exo'])
                    # Count winning/losing trades based on profit
                    if 'rp' in position:
                        total_trades += 1
                        profit = float(position['rp'])
                        if profit > 0:
                            winning_trades += 1
                        elif profit < 0:
                            losing_trades += 1

            analysis.update({
                'orders': total_orders,
                'trades': total_trades,
                'positions': total_positions,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': (winning_trades / total_trades) if total_trades > 0 else 0.0,
                'total_profit': analysis.get('realized_profits_usdt', 0.0),
            })

            # Debug: Print final analysis
            if backtest_id == "51284b78-80e8-4560-9308-9303b597b7ec":  # First backtest ID from sample
                logger.info(f"Final analysis for {backtest_id}: ROI={analysis.get('roi_percentage', 'N/A')}, PC={analysis.get('pc_value', 'N/A')}, Profit={analysis.get('realized_profits_usdt', 'N/A')}")

        # Set defaults for missing values
        analysis.setdefault('fees_usdt', 0.0)
        analysis.setdefault('pc_value', 0.0)
        analysis.setdefault('realized_profits_usdt', 0.0)
        analysis.setdefault('roi_percentage', 0.0)
        analysis.setdefault('max_drawdown', 0.0)
        analysis.setdefault('account_id', '')
        analysis.setdefault('market_tag', '')
        analysis.setdefault('script_id', '')

        # Determine if beats buy & hold
        pc_value = analysis.get('pc_value', 0.0)
        roi_value = analysis.get('roi_percentage', 0.0)
        analysis['beats_buy_hold'] = roi_value >= pc_value
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing backtest {getattr(backtest, 'backtest_id', 'unknown')}: {e}")
        return None

def create_csv_report(analytics: List[Dict[str, Any]], output_dir: str):
    """Create CSV report with all analytics"""
    logger.info(f"Creating CSV with {len(analytics)} analytics entries")
    if not analytics:
        logger.warning("No analytics data to write to CSV")
        return

    csv_file = os.path.join(output_dir, "backtests_analytics.csv")

    # Get all possible fields
    all_fields = set()
    for analysis in analytics:
        all_fields.update(analysis.keys())

    # Sort fields for consistent ordering
    fieldnames = sorted(list(all_fields))
    logger.info(f"CSV will have fields: {fieldnames}")

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, analysis in enumerate(analytics):
            # Fill missing fields with empty values
            row = {field: analysis.get(field, '') for field in fieldnames}
            logger.info(f"Writing row {i+1}: backtest_id={row.get('backtest_id', 'N/A')}, roi={row.get('roi_percentage', 'N/A')}")
            writer.writerow(row)

    logger.info(f"Created CSV report: {csv_file}")
    logger.info(f"CSV contains {len(analytics)} backtests with {len(fieldnames)} fields")

def main():
    """Main function to fetch and analyze lab backtests"""
    lab_id = "caed4df4-bcf9-4d4c-a8af-a51af6b7982e"
    max_backtests = 1  # Debug - fetch only 1 backtest
    
    # Initialize executor
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        logger.error("API_EMAIL and API_PASSWORD must be set in .env file")
        return

    logger.info(f"Connecting to HaasOnline API: {api_host}:{api_port}")

    # Create API connection
    haas_api = api.RequestsExecutor(
        host=api_host,
        port=api_port,
        state=api.Guest()
    )

    # Authenticate
    executor = haas_api.authenticate(api_email, api_password)
    logger.info("Successfully connected to HaasOnline API")
    
    # Create output directory
    output_dir = create_output_directory(lab_id)
    
    # Fetch all backtests
    logger.info("Fetching backtests...")
    backtests = fetch_all_backtests(executor, lab_id, max_backtests)
    
    if not backtests:
        logger.error("No backtests found")
        return
    
    # Dump raw data
    logger.info("Dumping raw data...")
    dump_raw_data(executor, backtests, output_dir, lab_id)
    
    # Analyze backtests
    logger.info("Analyzing backtests...")
    analytics = []
    
    for i, backtest in enumerate(backtests):
        logger.info(f"Analyzing backtest {i+1}/{len(backtests)}: {getattr(backtest, 'backtest_id', 'unknown')}")
        analysis = analyze_backtest(executor, backtest, lab_id)
        if analysis:
            logger.info(f"Adding analysis for {analysis.get('backtest_id', 'unknown')} to results")
            analytics.append(analysis)
        else:
            logger.warning(f"No analysis returned for backtest {getattr(backtest, 'backtest_id', 'unknown')}")
    
    # Create CSV report
    logger.info("Creating CSV report...")
    create_csv_report(analytics, output_dir)
    
    # Print summary
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Total backtests fetched: {len(backtests)}")
    logger.info(f"Successfully analyzed: {len(analytics)}")
    logger.info(f"Output directory: {output_dir}")
    
    # Show top performers by ROI
    if analytics:
        sorted_by_roi = sorted(analytics, key=lambda x: x.get('roi_percentage', 0), reverse=True)
        logger.info(f"\n=== TOP 5 PERFORMERS BY ROI ===")
        for i, analysis in enumerate(sorted_by_roi[:5]):
            logger.info(f"{i+1}. {analysis.get('script_name', 'Unknown')} - ROI: {analysis.get('roi_percentage', 0):.2f}%")
    
    # Show buy & hold comparison
    if analytics:
        beats_buy_hold = [a for a in analytics if a.get('beats_buy_hold', False)]
        logger.info(f"\n=== BUY & HOLD COMPARISON ===")
        logger.info(f"Backtests beating buy & hold: {len(beats_buy_hold)}/{len(analytics)} ({len(beats_buy_hold)/len(analytics)*100:.1f}%)")

if __name__ == "__main__":
    main()
