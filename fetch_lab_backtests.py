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

def dump_raw_data(backtests: List[Dict[str, Any]], output_dir: str):
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
            json.dump(backtest_dict, f, indent=2, default=str)

def analyze_backtest(executor: RequestsExecutor, backtest: Any, lab_id: str) -> Optional[Dict[str, Any]]:
    """Analyze a single backtest and return analytics"""
    try:
        backtest_id = backtest.backtest_id if hasattr(backtest, 'backtest_id') else str(backtest)
        if not backtest_id:
            logger.warning("Backtest missing backtest_id")
            return None
            
        # Get full runtime data
        runtime_data = get_full_backtest_runtime_data(executor, lab_id, backtest_id)
        if not runtime_data:
            logger.warning(f"Could not get runtime data for {backtest_id}")
            return None
            
        # Create backtest object
        backtest_obj = BacktestObject(executor, lab_id, backtest_id)
        
        # Extract basic info from backtest object
        analysis = {
            'backtest_id': backtest_id,
            'script_name': getattr(backtest, 'script_name', ''),
            'generation': getattr(backtest, 'generation', ''),
            'population': getattr(backtest, 'population', ''),
            'orders': getattr(backtest, 'orders', 0),
            'trades': getattr(backtest, 'trades', 0),
            'positions': getattr(backtest, 'positions', 0),
            'fees_usdt': getattr(backtest, 'fees', 0.0),
            'realized_profits_usdt': getattr(backtest, 'realized_profits', 0.0),
            'roi_percentage': getattr(backtest, 'roi', 0.0),
            'interval': getattr(backtest, 'interval', ''),
            'rising_length': getattr(backtest, 'rising_length', ''),
            'vwap_window': getattr(backtest, 'vwap_window', ''),
            'stop_loss_percentage': getattr(backtest, 'stop_loss_percentage', ''),
            'stop_loss_shrinkage': getattr(backtest, 'stop_loss_shrinkage', ''),
            'start_time': getattr(backtest, 'start_time', ''),
            'end_time': getattr(backtest, 'end_time', ''),
        }
        
        # Add runtime analytics if available
        if hasattr(backtest_obj, 'runtime') and backtest_obj.runtime:
            runtime = backtest_obj.runtime
            analysis.update({
                'total_trades': runtime.total_trades,
                'winning_trades': runtime.winning_trades,
                'losing_trades': runtime.losing_trades,
                'win_rate': runtime.win_rate,
                'total_profit': runtime.total_profit,
                'max_drawdown': runtime.max_drawdown,
                'sharpe_ratio': runtime.sharpe_ratio,
                'profit_factor': runtime.profit_factor,
            })
        
        # Add metadata if available
        if hasattr(backtest_obj, 'metadata') and backtest_obj.metadata:
            metadata = backtest_obj.metadata
            analysis.update({
                'account_id': metadata.account_id,
                'market_tag': metadata.market_tag,
                'script_id': metadata.script_id,
            })
        
        # Extract PC value (Buy & Hold %) if available
        pc_value = 0.0
        if hasattr(backtest_obj, 'runtime') and backtest_obj.runtime and backtest_obj.runtime.raw_data:
            raw_data = backtest_obj.runtime.raw_data
            if 'Reports' in raw_data:
                for report_key, report_data in raw_data['Reports'].items():
                    if 'PR' in report_data and 'PC' in report_data['PR']:
                        pc_value = float(report_data['PR']['PC'])
                        break
        
        analysis['pc_value'] = pc_value
        analysis['beats_buy_hold'] = analysis['roi_percentage'] >= pc_value
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing backtest {getattr(backtest, 'backtest_id', 'unknown')}: {e}")
        return None

def create_csv_report(analytics: List[Dict[str, Any]], output_dir: str):
    """Create CSV report with all analytics"""
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
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for analysis in analytics:
            # Fill missing fields with empty values
            row = {field: analysis.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Created CSV report: {csv_file}")
    logger.info(f"CSV contains {len(analytics)} backtests with {len(fieldnames)} fields")

def main():
    """Main function to fetch and analyze lab backtests"""
    lab_id = "caed4df4-bcf9-4d4c-a8af-a51af6b7982e"
    max_backtests = 1000
    
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
    dump_raw_data(backtests, output_dir)
    
    # Analyze backtests
    logger.info("Analyzing backtests...")
    analytics = []
    
    for i, backtest in enumerate(backtests):
        logger.info(f"Analyzing backtest {i+1}/{len(backtests)}: {getattr(backtest, 'backtest_id', 'unknown')}")
        analysis = analyze_backtest(executor, backtest, lab_id)
        if analysis:
            analytics.append(analysis)
    
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
