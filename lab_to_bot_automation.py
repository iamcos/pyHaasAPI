#!/usr/bin/env python3
"""
Lab to Bot Automation System

This script analyzes lab backtests and converts the best-performing strategies
into live trading bots with minimal human intervention.

Features:
- Walk Forward Optimization (WFO) analysis for strategy robustness
- Diversity filtering to avoid similar strategies
- Automated account management and bot deployment
- Comprehensive error handling and rollback capabilities
- Configurable thresholds and scoring weights

Author: AI Assistant
Date: 2024
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from lab_to_bot_automation import (
    LabToBotAutomation,
    AutomationConfig,
    WFOConfig,
    AccountConfig,
    BotCreationConfig
)


def create_default_config(lab_id: str) -> AutomationConfig:
    """Create default configuration for automation"""
    
    # WFO Analysis Configuration
    wfo_config = WFOConfig(
        min_roi_pct=50.0,  # Minimum ROI to consider
        min_trades=10,  # Minimum trades for statistical significance
        min_sample_size=5,  # Minimum sample size for calculations
        
        # Scoring weights (0.0 to 1.0)
        roi_weight=0.4,  # Weight for ROI in overall score
        win_rate_weight=0.2,  # Weight for win rate
        profitability_weight=0.2,  # Weight for profitability
        risk_weight=0.2,  # Weight for risk assessment
        
        # Diversity filtering thresholds
        roi_similarity_threshold=0.15,  # 15% ROI difference threshold
        trade_count_similarity_threshold=0.3,  # 30% trade count difference threshold
        win_rate_similarity_threshold=0.1,  # 10% win rate difference threshold
        
        # Bot deployment settings
        max_bots_per_lab=5,  # Maximum bots to deploy per lab
        min_overall_score=70.0,  # Minimum overall score for deployment
    )
    
    # Account Management Configuration
    account_config = AccountConfig(
        account_suffix="-10k",  # Suffix for account names
        initial_balance=10000.0,  # Initial USDT balance per account
        required_currency="USDT",  # Required currency for accounts
        exchange="BINANCEFUTURES",  # Exchange for accounts
        creation_delay=0.1,  # Delay between account creations
        max_retries=3,  # Maximum retries for account creation
    )
    
    # Bot Configuration
    bot_config = BotCreationConfig(
        position_size_usdt=2000.0,  # Position size in USDT per trade
        leverage=1,  # Default leverage (1x for spot-like behavior)
        activate_immediately=True,  # Activate bots after creation
        max_creation_attempts=3,  # Max retries for bot creation
        creation_delay=1.0,  # Delay between bot creations
        enable_position_sizing=True,  # Enable position size configuration
    )
    
    return AutomationConfig(
        lab_id=lab_id,
        max_backtests=50,
        wfo_config=wfo_config,
        account_config=account_config,
        bot_config=bot_config,
        dry_run=False,
        verbose=False
    )


def main():
    """Main entry point for Lab to Bot Automation"""
    parser = argparse.ArgumentParser(
        description="Lab to Bot Automation - Convert lab backtests to live trading bots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lab_to_bot_automation.py --lab-id 6e04e13c-1a12-4759-b037-b6997f830edf
  python lab_to_bot_automation.py --lab-id YOUR_LAB_ID --dry-run --verbose
  python lab_to_bot_automation.py --lab-id YOUR_LAB_ID --max-bots 3 --position-size 1500

Special Features:
  • Handles ZERO accounts scenario (bootstraps from empty state)
  • Diversity filtering prevents duplicate strategies
  • 2,000 USDT position sizing with full 10,000 USDT account access
  • Comprehensive error handling and rollback capabilities
        """
    )

    parser.add_argument('--lab-id', required=True, help='Laboratory ID to analyze')
    parser.add_argument('--max-backtests', type=int, default=50, help='Maximum backtests to analyze (default: 50)')
    parser.add_argument('--max-bots', type=int, default=5, help='Maximum bots to deploy (default: 5)')
    parser.add_argument('--position-size', type=float, default=2000.0, help='Position size in USDT (default: 2000)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run - analyze without deploying bots')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--output-dir', default='automation_reports', help='Output directory for reports')

    args = parser.parse_args()

    print("🚀 Lab to Bot Automation")
    print("=" * 60)
    print(f"📊 Lab ID: {args.lab_id}")
    print(f"🎯 Max Bots: {args.max_bots}")
    print(f"💰 Position Size: {args.position_size} USDT")
    print(f"🔍 Dry Run: {args.dry_run}")
    print()

    # Connect to HaasOnline API
    try:
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            print("❌ Error: API_EMAIL and API_PASSWORD must be set in .env file")
            return

        print(f"🔌 Connecting to HaasOnline API: {api_host}:{api_port}")

        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )

        # Authenticate
        haas_executor = haas_api.authenticate(api_email, api_password)
        print("✅ Successfully connected to HaasOnline API")

    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return

    # Create automation configuration
    config = create_default_config(args.lab_id)
    config.max_backtests = args.max_backtests
    config.wfo_config.max_bots_per_lab = args.max_bots
    config.bot_config.position_size_usdt = args.position_size
    config.dry_run = args.dry_run
    config.verbose = args.verbose
    config.output_dir = args.output_dir

    # Create and execute automation
    automation = LabToBotAutomation(haas_executor, config)
    
    # Set logging level based on verbose flag
    if not args.verbose:
        # Reduce logging verbosity for non-verbose mode
        logging.getLogger().setLevel(logging.WARNING)
        logging.getLogger('pyHaasAPI').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)

    print("\n🚀 Starting automation process...")
    success = automation.execute_automation()

    if success:
        print("\n🎉 Lab to Bot Automation completed successfully!")
        print(f"📄 Reports saved to: {config.output_dir}/")
    else:
        print("\n❌ Lab to Bot Automation failed!")
        print("Check the log file for detailed error information.")


if __name__ == "__main__":
    main()
