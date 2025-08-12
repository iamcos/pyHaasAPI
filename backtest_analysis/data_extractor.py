#!/usr/bin/env python3
"""
Backtest Data Extraction and Debugging System

This module provides comprehensive tools for extracting and debugging trade-level data
from HaasOnline backtest results, addressing the issue where ProfitLoss and TradeAmount
values were showing as zero due to incorrect field mapping.
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeData:
    """Represents a single trade extracted from backtest data"""
    position_id: str
    backtest_id: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    trade_amount: float
    profit_loss: float
    fees: float
    direction: int  # 1 for long, -1 for short
    entry_order_id: str
    exit_order_id: str
    roi: float

@dataclass
class BacktestSummary:
    """Comprehensive backtest summary with corrected data"""
    backtest_id: str
    lab_id: str
    status: int
    generation_idx: int
    population_idx: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit: float
    total_fees: float
    roi: float
    parameters: Dict[str, Any]
    settings: Dict[str, Any]
    trades: List[TradeData]

class BacktestDataExtractor:
    """Main class for extracting and debugging backtest data"""
    
    def __init__(self, results_directory: str):
        self.results_directory = results_directory
        self.debug_mode = True
        
    def extract_trade_data_from_position(self, position: Dict) -> Optional[TradeData]:
        """
        Extract trade data from a finished position with correct field mapping.
        
        Based on analysis of the JSON structure:
        - 'rp' field contains the realized profit/loss for the position
        - 'm' field in entry/exit orders contains the margin/trade amount
        - 'fe' field contains fees
        - 'p' field contains price
        - 'ct' field contains completion time
        """
        try:
            # Extract basic position info
            position_id = position.get('g', '')
            entry_orders = position.get('eno', [])
            exit_orders = position.get('exo', [])
            
            if not entry_orders or not exit_orders:
                if self.debug_mode:
                    logger.warning(f"Position {position_id} missing entry or exit orders")
                return None
            
            # Get first entry and exit orders (most common case)
            entry_order = entry_orders[0]
            exit_order = exit_orders[0]
            
            # Extract trade data with correct field mapping
            trade_data = TradeData(
                position_id=position_id,
                backtest_id="",  # Will be set by caller
                entry_time=entry_order.get('ct', 0),
                exit_time=exit_order.get('ct', 0),
                entry_price=float(entry_order.get('ep', 0.0)),
                exit_price=float(exit_order.get('ep', 0.0)),
                trade_amount=float(entry_order.get('m', 0.0)),  # Margin amount
                profit_loss=float(position.get('rp', 0.0)),  # Realized profit from position
                fees=float(position.get('fe', 0.0)),  # Total fees for position
                direction=position.get('d', 0),  # Direction: 1=long, -1=short
                entry_order_id=entry_order.get('id', ''),
                exit_order_id=exit_order.get('id', ''),
                roi=float(position.get('roi', 0.0))
            )
            
            if self.debug_mode and trade_data.profit_loss != 0.0:
                logger.info(f"Successfully extracted trade: P&L={trade_data.profit_loss}, Amount={trade_data.trade_amount}")
            
            return trade_data
            
        except Exception as e:
            logger.error(f"Error extracting trade data from position: {e}")
            return None
    
    def extract_backtest_data(self, filepath: str) -> Optional[BacktestSummary]:
        """Extract comprehensive backtest data from a JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Extract basic info
            backtest_id = data.get('backtest_id', '')
            lab_id = data.get('lab_id', '')
            status = data.get('status', 0)
            generation_idx = data.get('generation_idx', 0)
            population_idx = data.get('population_idx', 0)
            
            # Extract parameters and settings
            parameters = data.get('parameters', {})
            settings = data.get('settings', {})
            
            # Extract runtime data
            runtime_data = data.get('runtime_data', {})
            finished_positions = runtime_data.get('FinishedPositions', [])
            
            # Extract trades from finished positions
            trades = []
            for position in finished_positions:
                trade_data = self.extract_trade_data_from_position(position)
                if trade_data:
                    trade_data.backtest_id = backtest_id
                    trades.append(trade_data)
            
            # Calculate summary statistics
            winning_trades = len([t for t in trades if t.profit_loss > 0])
            losing_trades = len([t for t in trades if t.profit_loss < 0])
            total_profit = sum(t.profit_loss for t in trades)
            total_fees = sum(t.fees for t in trades)
            
            # Get ROI from summary or calculate
            summary_data = data.get('summary', {})
            roi = summary_data.get('ReturnOnInvestment', 0.0)
            
            return BacktestSummary(
                backtest_id=backtest_id,
                lab_id=lab_id,
                status=status,
                generation_idx=generation_idx,
                population_idx=population_idx,
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                total_profit=total_profit,
                total_fees=total_fees,
                roi=roi,
                parameters=parameters,
                settings=settings,
                trades=trades
            )
            
        except Exception as e:
            logger.error(f"Error extracting backtest data from {filepath}: {e}")
            return None
    
    def debug_data_extraction(self, filepath: str) -> Dict[str, Any]:
        """
        Debug data extraction by examining the raw JSON structure
        and identifying where trade-level data is located.
        """
        debug_report = {
            'file': filepath,
            'timestamp': datetime.now().isoformat(),
            'findings': [],
            'recommendations': []
        }
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Check basic structure
            debug_report['findings'].append(f"File loaded successfully")
            debug_report['findings'].append(f"Backtest ID: {data.get('backtest_id', 'N/A')}")
            debug_report['findings'].append(f"Status: {data.get('status', 'N/A')}")
            
            # Check runtime data
            runtime_data = data.get('runtime_data', {})
            if runtime_data:
                debug_report['findings'].append("Runtime data found")
                
                # Check finished positions
                finished_positions = runtime_data.get('FinishedPositions', [])
                debug_report['findings'].append(f"Finished positions count: {len(finished_positions)}")
                
                if finished_positions:
                    # Analyze first position in detail
                    first_pos = finished_positions[0]
                    debug_report['findings'].append("First position analysis:")
                    debug_report['findings'].append(f"  - Position ID: {first_pos.get('g', 'N/A')}")
                    debug_report['findings'].append(f"  - Realized Profit (rp): {first_pos.get('rp', 'N/A')}")
                    debug_report['findings'].append(f"  - Fees (fe): {first_pos.get('fe', 'N/A')}")
                    debug_report['findings'].append(f"  - ROI: {first_pos.get('roi', 'N/A')}")
                    debug_report['findings'].append(f"  - Direction (d): {first_pos.get('d', 'N/A')}")
                    
                    # Check entry orders
                    entry_orders = first_pos.get('eno', [])
                    if entry_orders:
                        entry_order = entry_orders[0]
                        debug_report['findings'].append(f"  - Entry order margin (m): {entry_order.get('m', 'N/A')}")
                        debug_report['findings'].append(f"  - Entry price (ep): {entry_order.get('ep', 'N/A')}")
                        debug_report['findings'].append(f"  - Entry time (ct): {entry_order.get('ct', 'N/A')}")
                    
                    # Check exit orders
                    exit_orders = first_pos.get('exo', [])
                    if exit_orders:
                        exit_order = exit_orders[0]
                        debug_report['findings'].append(f"  - Exit order margin (m): {exit_order.get('m', 'N/A')}")
                        debug_report['findings'].append(f"  - Exit price (ep): {exit_order.get('ep', 'N/A')}")
                        debug_report['findings'].append(f"  - Exit time (ct): {exit_order.get('ct', 'N/A')}")
                
                # Check for non-zero values
                non_zero_profits = [pos for pos in finished_positions if pos.get('rp', 0) != 0]
                debug_report['findings'].append(f"Positions with non-zero profit: {len(non_zero_profits)}")
                
                if non_zero_profits:
                    debug_report['recommendations'].append("SUCCESS: Found non-zero profit values in 'rp' field")
                    debug_report['recommendations'].append("Use 'rp' field for realized profit/loss")
                    debug_report['recommendations'].append("Use 'm' field from entry orders for trade amount")
                else:
                    debug_report['recommendations'].append("WARNING: All profit values are zero")
            
            # Check summary data for comparison
            summary = data.get('summary', {})
            if summary:
                debug_report['findings'].append(f"Summary ROI: {summary.get('ReturnOnInvestment', 'N/A')}")
                debug_report['findings'].append(f"Summary Realized Profits: {summary.get('RealizedProfits', 'N/A')}")
                debug_report['findings'].append(f"Summary Total Trades: {summary.get('Trades', 'N/A')}")
                
                if summary.get('RealizedProfits', 0) != 0:
                    debug_report['recommendations'].append("Summary shows non-zero profits - data extraction should work")
        
        except Exception as e:
            debug_report['findings'].append(f"ERROR: {str(e)}")
            debug_report['recommendations'].append("Check file format and structure")
        
        return debug_report
    
    def validate_extracted_data(self, backtest_summary: BacktestSummary) -> Dict[str, Any]:
        """Validate extracted data against summary statistics"""
        validation_report = {
            'backtest_id': backtest_summary.backtest_id,
            'validation_passed': True,
            'issues': [],
            'statistics': {}
        }
        
        # Check if we have trades
        if not backtest_summary.trades:
            validation_report['validation_passed'] = False
            validation_report['issues'].append("No trades extracted")
            return validation_report
        
        # Calculate statistics
        extracted_profit = sum(t.profit_loss for t in backtest_summary.trades)
        extracted_fees = sum(t.fees for t in backtest_summary.trades)
        
        validation_report['statistics'] = {
            'extracted_trades': len(backtest_summary.trades),
            'extracted_profit': extracted_profit,
            'extracted_fees': extracted_fees,
            'summary_roi': backtest_summary.roi,
            'winning_trades': backtest_summary.winning_trades,
            'losing_trades': backtest_summary.losing_trades
        }
        
        # Validate against expected values
        if abs(extracted_profit) < 0.01:  # Very small profit
            validation_report['issues'].append("Extracted profit is near zero")
        
        if extracted_fees < 0.01:  # Very small fees
            validation_report['issues'].append("Extracted fees are near zero")
        
        if len(validation_report['issues']) > 0:
            validation_report['validation_passed'] = False
        
        return validation_report
    
    def process_all_backtests(self) -> List[BacktestSummary]:
        """Process all backtest files in the results directory"""
        backtest_summaries = []
        
        if not os.path.exists(self.results_directory):
            logger.error(f"Results directory not found: {self.results_directory}")
            return backtest_summaries
        
        json_files = [f for f in os.listdir(self.results_directory) if f.endswith('.json')]
        logger.info(f"Processing {len(json_files)} backtest files...")
        
        for filename in json_files:
            filepath = os.path.join(self.results_directory, filename)
            backtest_summary = self.extract_backtest_data(filepath)
            
            if backtest_summary:
                # Validate the extracted data
                validation = self.validate_extracted_data(backtest_summary)
                if validation['validation_passed']:
                    backtest_summaries.append(backtest_summary)
                    logger.info(f"Successfully processed {filename}: {len(backtest_summary.trades)} trades")
                else:
                    logger.warning(f"Validation failed for {filename}: {validation['issues']}")
            else:
                logger.error(f"Failed to extract data from {filename}")
        
        logger.info(f"Successfully processed {len(backtest_summaries)} backtests")
        return backtest_summaries

def main():
    """Main function for testing the data extractor"""
    # Configuration
    LAB_ID = '55b45ee4-9cc5-42f7-8556-4c3aa2b13a44'
    RESULTS_DIR = f'/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/experiments/bt_analysis/raw_results/lab_{LAB_ID}'
    
    # Initialize extractor
    extractor = BacktestDataExtractor(RESULTS_DIR)
    
    # Debug first file
    json_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.json')]
    if json_files:
        first_file = os.path.join(RESULTS_DIR, json_files[0])
        print("=== DEBUG REPORT ===")
        debug_report = extractor.debug_data_extraction(first_file)
        
        for finding in debug_report['findings']:
            print(f"FINDING: {finding}")
        
        for recommendation in debug_report['recommendations']:
            print(f"RECOMMENDATION: {recommendation}")
        
        print("\n=== EXTRACTION TEST ===")
        # Test extraction
        backtest_summary = extractor.extract_backtest_data(first_file)
        if backtest_summary:
            print(f"Extracted {len(backtest_summary.trades)} trades")
            print(f"Total profit: {backtest_summary.total_profit}")
            print(f"Total fees: {backtest_summary.total_fees}")
            print(f"ROI: {backtest_summary.roi}")
            
            # Show first few trades
            for i, trade in enumerate(backtest_summary.trades[:3]):
                print(f"Trade {i+1}: P&L={trade.profit_loss}, Amount={trade.trade_amount}, Fees={trade.fees}")
        
        print("\n=== PROCESSING ALL FILES ===")
        # Process all files
        all_summaries = extractor.process_all_backtests()
        print(f"Successfully processed {len(all_summaries)} backtests")
        
        # Show statistics
        if all_summaries:
            total_trades = sum(len(s.trades) for s in all_summaries)
            total_profit = sum(s.total_profit for s in all_summaries)
            print(f"Total trades across all backtests: {total_trades}")
            print(f"Total profit across all backtests: {total_profit}")

if __name__ == "__main__":
    main()