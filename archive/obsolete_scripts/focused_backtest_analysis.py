#!/usr/bin/env python3
"""
Focused backtest analysis: Get one page, filter for positive ROI, select 10 random for detailed analysis
"""

import os
import json
import csv
import logging
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
# Load environment variables if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor, get_full_backtest_runtime_data
from pyHaasAPI.model import GetBacktestResultRequest

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def extract_basic_info_from_object(backtest_obj) -> Optional[Dict[str, Any]]:
    """Extract basic info from backtest object"""
    try:
        backtest_id = backtest_obj.backtest_id
        generation = str(backtest_obj.generation_idx) if hasattr(backtest_obj, 'generation_idx') else ''
        population = str(backtest_obj.population_idx) if hasattr(backtest_obj, 'population_idx') else ''
        
        # Extract settings
        settings = backtest_obj.settings if hasattr(backtest_obj, 'settings') else None
        interval = str(settings.interval) if settings and hasattr(settings, 'interval') else ''
        market_tag = settings.market_tag if settings and hasattr(settings, 'market_tag') else ''
        
        # Extract parameters
        parameters = backtest_obj.parameters if hasattr(backtest_obj, 'parameters') else {}
        rising_length = str(parameters.get('3-3-21-26.Rising Length', ''))
        vwap_window = str(parameters.get('4-4-19-24.VWAP Window', ''))
        stop_loss_percentage = str(parameters.get('6-6-27-32.Stop Loss Percentage', ''))
        stop_loss_shrinkage = str(parameters.get('7-7-26-31.Stop Loss Shrinkage', ''))
        
        return {
            'backtest_id': backtest_id,
            'generation': generation,
            'population': population,
            'interval': interval,
            'market_tag': market_tag,
            'rising_length': rising_length,
            'vwap_window': vwap_window,
            'stop_loss_percentage': stop_loss_percentage,
            'stop_loss_shrinkage': stop_loss_shrinkage,
        }
    except Exception as e:
        logger.error(f"Error extracting basic info from backtest object: {e}")
        return None

def analyze_backtest_with_runtime_data(executor: RequestsExecutor, lab_id: str, backtest_obj) -> Optional[Dict[str, Any]]:
    """Analyze a backtest using runtime data from API"""
    # Extract basic info
    basic_info = extract_basic_info_from_object(backtest_obj)
    if not basic_info:
        logger.warning("Could not extract basic info from backtest object")
        return None
    
    backtest_id = basic_info['backtest_id']
    logger.info(f"Analyzing backtest: {backtest_id}")
    
    try:
        # Get full runtime data
        runtime_data = get_full_backtest_runtime_data(executor, lab_id, backtest_id)
        logger.info(f"Retrieved runtime data for {backtest_id}")
    except Exception as e:
        logger.error(f"Error getting runtime data for {backtest_id}: {e}")
        return None
    
    # Initialize analysis with basic info
    analysis = basic_info.copy()
    
    # Extract performance data from Reports
    if runtime_data.Reports:
        # Get the first (and usually only) report
        report_key = list(runtime_data.Reports.keys())[0]
        report_data = runtime_data.Reports[report_key]
        
        # Extract fees
        if hasattr(report_data, 'F') and hasattr(report_data.F, 'TFC'):
            analysis['fees_usdt'] = float(report_data.F.TFC)
        else:
            analysis['fees_usdt'] = 0.0
        
        # Extract performance metrics
        if hasattr(report_data, 'PR'):
            pr_data = report_data.PR
            analysis['realized_profits_usdt'] = float(pr_data.RP) if hasattr(pr_data, 'RP') else 0.0
            analysis['roi_percentage'] = float(pr_data.ROI) if hasattr(pr_data, 'ROI') else 0.0
            analysis['max_drawdown'] = float(pr_data.RM) if hasattr(pr_data, 'RM') else 0.0
            analysis['pc_value'] = float(pr_data.PC) if hasattr(pr_data, 'PC') else 0.0
        else:
            analysis['realized_profits_usdt'] = 0.0
            analysis['roi_percentage'] = 0.0
            analysis['max_drawdown'] = 0.0
            analysis['pc_value'] = 0.0
        
        # Extract trade statistics
        if hasattr(report_data, 'P'):
            p_data = report_data.P
            analysis['total_trades'] = int(p_data.C) if hasattr(p_data, 'C') else 0
            analysis['winning_trades'] = int(p_data.W) if hasattr(p_data, 'W') else 0
            analysis['losing_trades'] = analysis['total_trades'] - analysis['winning_trades']
            analysis['win_rate'] = (analysis['winning_trades'] / analysis['total_trades']) if analysis['total_trades'] > 0 else 0.0
        else:
            analysis['total_trades'] = 0
            analysis['winning_trades'] = 0
            analysis['losing_trades'] = 0
            analysis['win_rate'] = 0.0
        
        # Extract technical indicators
        if hasattr(report_data, 'T'):
            t_data = report_data.T
            analysis['sharpe_ratio'] = float(t_data.SHR) if hasattr(t_data, 'SHR') else 0.0
            analysis['profit_factor'] = float(t_data.PF) if hasattr(t_data, 'PF') else 0.0
        else:
            analysis['sharpe_ratio'] = 0.0
            analysis['profit_factor'] = 0.0
    else:
        # No reports found
        analysis.update({
            'fees_usdt': 0.0,
            'realized_profits_usdt': 0.0,
            'roi_percentage': 0.0,
            'max_drawdown': 0.0,
            'pc_value': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'profit_factor': 0.0
        })
    
    return analysis

def main():
    """Main function to fetch, filter, and analyze backtests"""
    # Configuration
    lab_id = "caed4df4-bcf9-4d4c-a8af-a51af6b7982e"
    page_size = 100
    max_positive_backtests = 10
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"focused_analysis_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting focused backtest analysis for lab: {lab_id}")
    
    # Initialize API connection
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        logger.error("API_EMAIL and API_PASSWORD must be set in .env file")
        return

    logger.info(f"Connecting to HaasOnline API: {api_host}:{api_port}")

    try:
        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )

        # Authenticate
        executor = haas_api.authenticate(api_email, api_password)
        logger.info("Successfully connected to HaasOnline API")
    except Exception as e:
        logger.error(f"Failed to initialize API connection: {e}")
        return
    
    # Fetch one page of backtests
    logger.info("Fetching first page of backtests...")
    response = fetch_backtests_page(executor, lab_id, next_page_id=0, page_size=page_size)
    
    if not response.get('Success', False):
        logger.error("Failed to fetch backtests")
        return
    
    backtests = response.get('Data', [])
    logger.info(f"Fetched {len(backtests)} backtests from first page")
    
    # Analyze all backtests to get their ROI
    logger.info("Analyzing all backtests to get ROI data...")
    all_analyses = []
    
    for i, backtest_obj in enumerate(backtests):
        logger.info(f"Analyzing backtest {i+1}/{len(backtests)}")
        analysis = analyze_backtest_with_runtime_data(executor, lab_id, backtest_obj)
        if analysis:
            all_analyses.append(analysis)
    
    logger.info(f"Successfully analyzed {len(all_analyses)} backtests")
    
    # Filter for positive ROI
    positive_backtests = [analysis for analysis in all_analyses if analysis['roi_percentage'] > 0]
    logger.info(f"Found {len(positive_backtests)} backtests with positive ROI")
    
    # Select random 10 (or all if less than 10)
    selected_count = min(max_positive_backtests, len(positive_backtests))
    selected_backtests = random.sample(positive_backtests, selected_count) if positive_backtests else []
    
    logger.info(f"Selected {len(selected_backtests)} backtests for detailed analysis")
    
    # Save results
    if selected_backtests:
        # Save as CSV
        csv_file = os.path.join(output_dir, "positive_backtests_analysis.csv")
        with open(csv_file, 'w', newline='') as f:
            if selected_backtests:
                writer = csv.DictWriter(f, fieldnames=selected_backtests[0].keys())
                writer.writeheader()
                writer.writerows(selected_backtests)
        
        # Save as JSON
        json_file = os.path.join(output_dir, "positive_backtests_analysis.json")
        with open(json_file, 'w') as f:
            json.dump(selected_backtests, f, indent=2)
        
        logger.info(f"Results saved to {output_dir}")
        
        # Print summary
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Total backtests analyzed: {len(all_analyses)}")
        print(f"Positive ROI backtests: {len(positive_backtests)}")
        print(f"Selected for detailed analysis: {len(selected_backtests)}")
        
        if selected_backtests:
            print(f"\n=== SELECTED BACKTESTS ===")
            for i, backtest in enumerate(selected_backtests, 1):
                print(f"{i}. Backtest {backtest['backtest_id'][:8]}...")
                print(f"   ROI: {backtest['roi_percentage']:.2f}%")
                print(f"   Profits: {backtest['realized_profits_usdt']:.2f} USDT")
                print(f"   Trades: {backtest['total_trades']} (Win Rate: {backtest['win_rate']:.1%})")
                print(f"   Max Drawdown: {backtest['max_drawdown']:.2f}%")
                print(f"   Parameters: Rising Length={backtest['rising_length']}, VWAP={backtest['vwap_window']}, SL={backtest['stop_loss_percentage']}%")
                print()
    else:
        logger.warning("No positive ROI backtests found")
        print("No backtests with positive ROI found in this page.")

if __name__ == "__main__":
    main()
