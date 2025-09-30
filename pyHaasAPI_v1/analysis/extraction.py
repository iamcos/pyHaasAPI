"""
Backtest Data Extraction

This module provides comprehensive tools for extracting and debugging trade-level data
from HaasOnline backtest results, addressing common issues with field mapping and
providing detailed validation and debugging capabilities.
"""

import json
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path

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

    @property
    def duration_seconds(self) -> int:
        """Get trade duration in seconds"""
        return self.exit_time - self.entry_time

    @property
    def is_profitable(self) -> bool:
        """Check if trade was profitable"""
        return self.profit_loss > 0

    @property
    def net_profit(self) -> float:
        """Get net profit after fees"""
        return self.profit_loss - self.fees

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

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def average_profit_per_trade(self) -> float:
        """Calculate average profit per trade"""
        if self.total_trades == 0:
            return 0.0
        return self.total_profit / self.total_trades

    @property
    def profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

class BacktestDataExtractor:
    """Main class for extracting and debugging backtest data"""
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        
    def extract_trade_data_from_position(self, position: Dict) -> Optional[TradeData]:
        """
        Extract trade data from a finished position with correct field mapping.
        
        Based on analysis of the JSON structure:
        - 'rp' field contains the realized profit/loss for the position
        - 'm' field in entry/exit orders contains the margin/trade amount
        - 'fe' field contains fees
        - 'p' field contains price
        - 'ct' field contains completion time
        
        Args:
            position: Position dictionary from backtest results
            
        Returns:
            TradeData object if extraction successful, None otherwise
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
                logger.debug(f"Successfully extracted trade: P&L={trade_data.profit_loss}, Amount={trade_data.trade_amount}")
            
            return trade_data
            
        except Exception as e:
            logger.error(f"Error extracting trade data from position: {e}")
            return None
    
    def extract_backtest_data(self, data_source: Union[str, Dict, Path]) -> Optional[BacktestSummary]:
        """
        Extract comprehensive backtest data from various sources.
        
        Args:
            data_source: Can be a file path, Path object, or dictionary with backtest data
            
        Returns:
            BacktestSummary object if extraction successful, None otherwise
        """
        try:
            # Handle different input types
            if isinstance(data_source, (str, Path)):
                with open(data_source, 'r') as f:
                    data = json.load(f)
            elif isinstance(data_source, dict):
                data = data_source
            else:
                logger.error(f"Unsupported data source type: {type(data_source)}")
                return None
            
            # Extract basic info
            backtest_id = data.get('backtest_id', data.get('BID', ''))
            lab_id = data.get('lab_id', data.get('LID', ''))
            status = data.get('status', data.get('ST', 0))
            generation_idx = data.get('generation_idx', data.get('NG', 0))
            population_idx = data.get('population_idx', data.get('NP', 0))
            
            # Extract parameters and settings
            parameters = data.get('parameters', data.get('P', {}))
            settings = data.get('settings', data.get('SE', {}))
            
            # Extract runtime data
            runtime_data = data.get('runtime_data', data.get('RT', {}))
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
            summary_data = data.get('summary', data.get('S', {}))
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
            logger.error(f"Error extracting backtest data: {e}")
            return None
    
    def debug_data_extraction(self, data_source: Union[str, Dict, Path]) -> Dict[str, Any]:
        """
        Debug data extraction by examining the raw structure
        and identifying where trade-level data is located.
        
        Args:
            data_source: Data source to debug (file path or dictionary)
            
        Returns:
            Dictionary with debug information and recommendations
        """
        debug_report = {
            'source': str(data_source),
            'timestamp': datetime.now().isoformat(),
            'findings': [],
            'recommendations': [],
            'data_quality': 'unknown'
        }
        
        try:
            # Load data
            if isinstance(data_source, (str, Path)):
                with open(data_source, 'r') as f:
                    data = json.load(f)
                debug_report['findings'].append(f"File loaded successfully: {data_source}")
            else:
                data = data_source
                debug_report['findings'].append("Dictionary data provided")
            
            # Check basic structure
            backtest_id = data.get('backtest_id', data.get('BID', 'N/A'))
            status = data.get('status', data.get('ST', 'N/A'))
            debug_report['findings'].append(f"Backtest ID: {backtest_id}")
            debug_report['findings'].append(f"Status: {status}")
            
            # Check runtime data
            runtime_data = data.get('runtime_data', data.get('RT', {}))
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
                    debug_report['data_quality'] = 'good'
                else:
                    debug_report['recommendations'].append("WARNING: All profit values are zero")
                    debug_report['data_quality'] = 'poor'
            else:
                debug_report['recommendations'].append("ERROR: No runtime data found")
                debug_report['data_quality'] = 'missing'
            
            # Check summary data for comparison
            summary = data.get('summary', data.get('S', {}))
            if summary:
                debug_report['findings'].append(f"Summary ROI: {summary.get('ReturnOnInvestment', 'N/A')}")
                debug_report['findings'].append(f"Summary Realized Profits: {summary.get('RealizedProfits', 'N/A')}")
                
                if summary.get('RealizedProfits', 0) != 0:
                    debug_report['recommendations'].append("Summary shows non-zero profits - data extraction should work")
        
        except Exception as e:
            debug_report['findings'].append(f"ERROR: {str(e)}")
            debug_report['recommendations'].append("Check file format and structure")
            debug_report['data_quality'] = 'error'
        
        return debug_report
    
    def validate_extracted_data(self, backtest_summary: BacktestSummary) -> Dict[str, Any]:
        """
        Validate extracted data against summary statistics and expected values.
        
        Args:
            backtest_summary: Extracted backtest summary to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_report = {
            'backtest_id': backtest_summary.backtest_id,
            'validation_passed': True,
            'issues': [],
            'warnings': [],
            'statistics': {},
            'quality_score': 0.0
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
            'losing_trades': backtest_summary.losing_trades,
            'win_rate': backtest_summary.win_rate,
            'profit_factor': backtest_summary.profit_factor
        }
        
        # Quality scoring
        quality_points = 0
        max_points = 10
        
        # Check for reasonable profit values
        if abs(extracted_profit) >= 0.01:
            quality_points += 3
        else:
            validation_report['warnings'].append("Extracted profit is near zero")
        
        # Check for reasonable fees
        if extracted_fees >= 0.01:
            quality_points += 2
        else:
            validation_report['warnings'].append("Extracted fees are near zero")
        
        # Check trade count
        if len(backtest_summary.trades) > 0:
            quality_points += 2
        
        # Check for complete trade data
        complete_trades = [t for t in backtest_summary.trades if t.entry_time > 0 and t.exit_time > 0]
        if len(complete_trades) == len(backtest_summary.trades):
            quality_points += 2
        else:
            validation_report['warnings'].append("Some trades have incomplete time data")
        
        # Check for reasonable win rate
        if 0 <= backtest_summary.win_rate <= 100:
            quality_points += 1
        
        validation_report['quality_score'] = (quality_points / max_points) * 100
        
        # Determine if validation passed
        if len(validation_report['issues']) > 0:
            validation_report['validation_passed'] = False
        elif validation_report['quality_score'] < 50:
            validation_report['validation_passed'] = False
            validation_report['issues'].append("Data quality score too low")
        
        return validation_report
    
    def extract_from_lab_results(self, lab_results: Dict[str, Any]) -> List[BacktestSummary]:
        """
        Extract backtest summaries from lab results containing multiple backtests.
        
        Args:
            lab_results: Lab results dictionary containing multiple backtest results
            
        Returns:
            List of extracted backtest summaries
        """
        summaries = []
        
        try:
            # Handle different lab result formats
            if 'Data' in lab_results and 'I' in lab_results['Data']:
                # Standard lab results format
                backtest_items = lab_results['Data']['I']
            elif 'I' in lab_results:
                # Direct items format
                backtest_items = lab_results['I']
            elif isinstance(lab_results, list):
                # Direct list format
                backtest_items = lab_results
            else:
                logger.error("Unrecognized lab results format")
                return summaries
            
            logger.info(f"Processing {len(backtest_items)} backtest results")
            
            for item in backtest_items:
                summary = self.extract_backtest_data(item)
                if summary:
                    summaries.append(summary)
                else:
                    logger.warning(f"Failed to extract data from backtest {item.get('BID', 'unknown')}")
            
            logger.info(f"Successfully extracted {len(summaries)} backtest summaries")
            
        except Exception as e:
            logger.error(f"Error extracting from lab results: {e}")
        
        return summaries

def extract_trades_from_backtest(data_source: Union[str, Dict, Path]) -> List[TradeData]:
    """
    Convenience function to extract just the trades from a backtest.
    
    Args:
        data_source: Backtest data source
        
    Returns:
        List of extracted trades
    """
    extractor = BacktestDataExtractor()
    summary = extractor.extract_backtest_data(data_source)
    return summary.trades if summary else []

def debug_backtest_data(data_source: Union[str, Dict, Path]) -> Dict[str, Any]:
    """
    Convenience function to debug backtest data extraction.
    
    Args:
        data_source: Backtest data source
        
    Returns:
        Debug report dictionary
    """
    extractor = BacktestDataExtractor()
    return extractor.debug_data_extraction(data_source)