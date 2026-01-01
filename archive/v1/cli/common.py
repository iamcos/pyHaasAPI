#!/usr/bin/env python3
"""
Common utilities for pyHaasAPI CLI tools

This module provides shared utilities, argument parsing patterns, and helper functions
extracted from the most comprehensive CLI tools.
"""

import argparse
import os
from typing import List, Dict, Any, Optional
from pyHaasAPI_v1 import api


def add_common_arguments(parser: argparse.ArgumentParser):
    """Add common arguments to CLI parsers - extracted from working patterns"""
    
    # Lab selection (mutually exclusive)
    lab_group = parser.add_mutually_exclusive_group()
    lab_group.add_argument('--lab-ids', nargs='+', type=str, 
                          help='Specific lab IDs to process')
    lab_group.add_argument('--exclude-lab-ids', nargs='+', type=str, 
                          help='Exclude these lab IDs from processing')
    
    # Analysis options
    parser.add_argument('--top-count', type=int, default=10, 
                       help='Number of top results to show (default: 10)')
    parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate', 'profit', 'trades'], 
                       default='roe', help='Sort by metric (default: roe)')
    parser.add_argument('--analyze-count', type=int, default=100,
                       help='Number of backtests to analyze per lab (default: 100)')
    
    # Output options
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--output-format', choices=['json', 'csv', 'markdown'], 
                       default='json', help='Output format (default: json)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    # Common filtering options
    parser.add_argument('--min-roe', type=float, default=0,
                       help='Minimum ROE for filtering (default: 0)')
    parser.add_argument('--max-roe', type=float,
                       help='Maximum ROE for filtering (no default limit)')
    parser.add_argument('--min-winrate', type=float, default=30,
                       help='Minimum win rate for filtering (default: 30)')
    parser.add_argument('--max-winrate', type=float,
                       help='Maximum win rate for filtering (no default limit)')
    parser.add_argument('--min-trades', type=int, default=5,
                       help='Minimum trades for filtering (default: 5)')
    parser.add_argument('--max-trades', type=int,
                       help='Maximum trades for filtering (no default limit)')


def add_bot_selection_arguments(parser: argparse.ArgumentParser):
    """Add bot selection arguments - extracted from working patterns"""
    
    # Bot selection (mutually exclusive)
    bot_group = parser.add_mutually_exclusive_group()
    bot_group.add_argument('--bot-ids', nargs='+', type=str,
                          help='Specific bot IDs to process')
    bot_group.add_argument('--exclude-bot-ids', nargs='+', type=str,
                          help='Exclude these bot IDs from processing')


def add_trade_amount_arguments(parser: argparse.ArgumentParser):
    """Add trade amount calculation arguments - extracted from working patterns"""
    
    parser.add_argument('--target-amount', type=float, default=2000.0,
                       help='Target USDT amount for trade amounts (default: 2000.0)')
    parser.add_argument('--method', choices=['usdt', 'wallet_percentage'], 
                       default='usdt', help='Trade amount calculation method (default: usdt)')
    parser.add_argument('--wallet-percentage', type=float,
                       help='Percentage of wallet to use (for wallet_percentage method)')


def get_complete_labs(executor) -> List[Any]:
    """PROVEN working method to get all complete labs from server"""
    try:
        all_labs = api.get_all_labs(executor)
        
        # Filter for complete labs only
        complete_labs = []
        for lab in all_labs:
            # Check for LabStatus enum with value 3 (COMPLETED)
            if hasattr(lab, 'status') and hasattr(lab.status, 'value') and lab.status.value == 3:
                complete_labs.append(lab)
            # Fallback: check string comparison for backward compatibility
            elif hasattr(lab, 'status') and str(lab.status) == 'LabStatus.COMPLETED':
                complete_labs.append(lab)
            # Alternative status field (numeric)
            elif hasattr(lab, 'ST') and lab.ST == 3:
                complete_labs.append(lab)
        
        return complete_labs
        
    except Exception as e:
        print(f"❌ Failed to get labs: {e}")
        return []


def get_cached_labs(cache_manager) -> List[str]:
    """PROVEN working method to get list of labs with cached data"""
    cache_dir = cache_manager.base_dir / "backtests"
    if not cache_dir.exists():
        return []
    
    # Get unique lab IDs from cached files
    lab_ids = set()
    for cache_file in cache_dir.glob("*.json"):
        lab_id = cache_file.name.split('_')[0]
        lab_ids.add(lab_id)
    
    return list(lab_ids)


def get_all_bots(executor) -> List[Any]:
    """PROVEN working method to get all bots from server"""
    try:
        return api.get_all_bots(executor)
    except Exception as e:
        print(f"❌ Failed to get bots: {e}")
        return []


def get_all_accounts(executor) -> List[Any]:
    """PROVEN working method to get all accounts from server"""
    try:
        return api.get_all_accounts(executor)
    except Exception as e:
        print(f"❌ Failed to get accounts: {e}")
        return []


def format_lab_name(lab_id: str, lab_name: str = None) -> str:
    """Format lab name for display"""
    if lab_name and lab_name != f"Lab {lab_id[:8]}":
        return f"{lab_name} ({lab_id[:8]})"
    else:
        return f"Lab {lab_id[:8]}"


def format_bot_name(bot_name: str, bot_id: str = None) -> str:
    """Format bot name for display"""
    if bot_id:
        return f"{bot_name} ({bot_id[:8]})"
    else:
        return bot_name


def calculate_roe(realized_profits: float, starting_balance: float) -> float:
    """Calculate ROE (Return on Equity) percentage"""
    if starting_balance <= 0:
        return 0.0
    return (realized_profits / starting_balance) * 100


def convert_win_rate(win_rate: float) -> float:
    """Convert win rate to percentage if needed"""
    if win_rate <= 1.0:  # If it's a decimal, convert to percentage
        return win_rate * 100
    elif win_rate > 100:  # If it's already been converted, don't convert again
        return win_rate / 100
    else:
        return win_rate


def apply_smart_precision(amount: float) -> float:
    """Apply smart precision based on decimal places - keep 3 significant digits after zeros"""
    if amount == 0:
        return 0.0
    
    # Convert to string to analyze decimal places
    amount_str = f"{amount:.15f}".rstrip('0').rstrip('.')
    
    # Find the position of the first non-zero digit after decimal
    if '.' in amount_str:
        decimal_part = amount_str.split('.')[1]
        first_non_zero = 0
        for i, char in enumerate(decimal_part):
            if char != '0':
                first_non_zero = i
                break
        
        # Keep 3 significant digits after the first non-zero
        precision = first_non_zero + 3
    else:
        # For whole numbers, keep 3 decimal places
        precision = 3
    
    # Round to the calculated precision
    rounded_amount = round(amount, precision)
    
    # Convert back to float and remove trailing zeros
    return float(f"{rounded_amount:.{precision}f}".rstrip('0').rstrip('.'))


def print_progress(current: int, total: int, operation: str = "Processing"):
    """Print progress indicator"""
    percentage = (current / total) * 100 if total > 0 else 0
    print(f"\r{operation}: {current}/{total} ({percentage:.1f}%)", end="", flush=True)
    if current == total:
        print()  # New line when complete


def validate_environment():
    """Validate that required environment variables are set"""
    required_vars = ['API_EMAIL', 'API_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Please set these in your .env file or environment")
        return False
    
    return True


def get_environment_info():
    """Get environment configuration info"""
    return {
        'host': os.getenv('API_HOST', '127.0.0.1'),
        'port': int(os.getenv('API_PORT', 8090)),
        'email': os.getenv('API_EMAIL', 'Not set'),
        'has_password': bool(os.getenv('API_PASSWORD'))
    }
