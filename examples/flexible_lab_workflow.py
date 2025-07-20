#!/usr/bin/env python3
"""
Flexible Lab Cloning and Backtesting Workflow

This script demonstrates the flexible workflow that can work with ANY markets.
It's not limited to predefined markets - you can specify any trading pairs you want.

Usage Examples:
1. Use predefined markets: python examples/flexible_lab_workflow.py
2. Use custom markets: python examples/flexible_lab_workflow.py --markets "BTC/USDT,ETH/USDT,SOL/USDT"
3. Use markets from file: python examples/flexible_lab_workflow.py --markets-file markets.txt
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI import api
from pyHaasAPI.parameters import LabConfig
from utils.auth.authenticator import authenticator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_markets_from_string(markets_string: str) -> list[str]:
    """Parse markets from comma-separated string"""
    return [market.strip() for market in markets_string.split(',') if market.strip()]

def parse_markets_from_file(file_path: str) -> list[str]:
    """Parse markets from file (one market per line)"""
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logger.error(f"❌ Markets file not found: {file_path}")
        return []

def get_default_markets() -> list[str]:
    """Get default markets (can be modified)"""
    return [
        'BTC/USDT', 'ETH/USDT', 'AVAX/USDT', 'SOL/USDT', 'ADA/USDT',
        'XRP/USDT', 'BNB/USDT', 'DOT/USDT', 'LINK/USDT', 'MATIC/USDT',
        'DOGE/USDT', 'TRX/USDT', 'LTC/USDT', 'ATOM/USDT', 'NEAR/USDT'
    ]

def convert_pair_to_market_tag(pair: str, exchange: str = "BINANCE") -> str:
    """Convert trading pair to market tag format"""
    if '/' in pair:
        primary, secondary = pair.split('/')
        return f"{exchange.upper()}_{primary.upper()}_{secondary.upper()}_"
    else:
        raise ValueError(f"Invalid pair format: {pair}. Expected format: 'BTC/USDT'")

def get_available_markets(executor) -> list[str]:
    """Get list of available markets from the API"""
    try:
        markets = api.get_all_markets(executor)
        available_pairs = []
        for market in markets:
            if hasattr(market, 'primary') and hasattr(market, 'secondary'):
                pair = f"{market.primary}/{market.secondary}"
                available_pairs.append(pair)
        return available_pairs
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch available markets: {e}")
        return []

def validate_markets(markets: list[str], available_markets: list[str] = None) -> tuple[list[str], list[str]]:
    """Validate markets and return valid and invalid ones"""
    if available_markets is None:
        # If we can't get available markets, assume all are valid
        return markets, []
    
    valid_markets = []
    invalid_markets = []
    
    for market in markets:
        if market in available_markets:
            valid_markets.append(market)
        else:
            invalid_markets.append(market)
    
    return valid_markets, invalid_markets

def main():
    """Main function demonstrating the flexible workflow"""
    parser = argparse.ArgumentParser(description='Flexible Lab Cloning and Backtesting Workflow')
    parser.add_argument('--markets', type=str, help='Comma-separated list of markets (e.g., "BTC/USDT,ETH/USDT")')
    parser.add_argument('--markets-file', type=str, help='File containing markets (one per line)')
    parser.add_argument('--exchange', type=str, default='BINANCE', help='Exchange name (default: BINANCE)')
    parser.add_argument('--source-lab', type=str, help='Source lab name (default: "Example")')
    parser.add_argument('--account-id', type=str, help='Specific account ID to use (default: first available account)')
    parser.add_argument('--start-time', type=str, help='Start time in format YYYY-MM-DD HH:MM (default: April 7th 2025 13:00)')
    parser.add_argument('--end-time', type=str, help='End time in format YYYY-MM-DD HH:MM (default: now)')
    parser.add_argument('--list-markets', action='store_true', help='List available markets and exit')
    parser.add_argument('--list-accounts', action='store_true', help='List available accounts and exit')
    parser.add_argument('--validate-only', action='store_true', help='Only validate markets, don\'t run workflow')
    
    args = parser.parse_args()
    
    load_dotenv()
    
    logger.info("🚀 Flexible Lab Cloning and Backtesting Workflow")
    logger.info("=" * 70)
    
    # Step 1: Authentication
    logger.info("🔐 Setting up authentication...")
    success = authenticator.authenticate()
    if not success:
        logger.error("❌ Authentication failed!")
        return
    
    executor = authenticator.get_executor()
    logger.info("✅ Authentication successful")
    
    # Step 2: Get available accounts if requested
    if args.list_accounts:
        logger.info("\n📋 Available Accounts:")
        accounts = api.get_accounts(executor)
        if accounts:
            for account in accounts:
                logger.info(f"   {account.name} (ID: {account.account_id})")
        else:
            logger.info("   No accounts available")
        return
    
    # Step 3: Get available markets if requested
    if args.list_markets:
        logger.info("\n📊 Available Markets:")
        available_markets = get_available_markets(executor)
        if available_markets:
            for market in sorted(available_markets):
                logger.info(f"   {market}")
        else:
            logger.info("   No markets available or could not fetch market list")
        return
    
    # Step 4: Determine target markets
    target_markets = []
    
    if args.markets:
        target_markets = parse_markets_from_string(args.markets)
        logger.info(f"📊 Using markets from command line: {len(target_markets)} markets")
    elif args.markets_file:
        target_markets = parse_markets_from_file(args.markets_file)
        logger.info(f"📊 Using markets from file: {len(target_markets)} markets")
    else:
        target_markets = get_default_markets()
        logger.info(f"📊 Using default markets: {len(target_markets)} markets")
    
    if not target_markets:
        logger.error("❌ No markets specified!")
        return
    
    # Step 5: Validate markets
    logger.info(f"\n🔍 Validating {len(target_markets)} markets...")
    available_markets = get_available_markets(executor)
    valid_markets, invalid_markets = validate_markets(target_markets, available_markets)
    
    if invalid_markets:
        logger.warning(f"⚠️ Invalid markets found: {invalid_markets}")
        logger.info(f"   These markets may not be available on the exchange")
    
    if not valid_markets:
        logger.error("❌ No valid markets found!")
        return
    
    logger.info(f"✅ Valid markets: {len(valid_markets)}")
    logger.info(f"❌ Invalid markets: {len(invalid_markets)}")
    
    if args.validate_only:
        logger.info("\n🔍 Market validation complete!")
        return
    
    # Step 6: Find the source lab
    source_lab_name = args.source_lab or "Example"
    logger.info(f"\n🔍 Looking for source lab: {source_lab_name}")
    labs = api.get_all_labs(executor)
    source_labs = [lab for lab in labs if lab.name == source_lab_name]
    
    if not source_labs:
        logger.error(f"❌ No lab named '{source_lab_name}' found!")
        logger.info("Available labs:")
        for lab in labs:
            logger.info(f"   - {lab.name}")
        return
    
    source_lab = source_labs[0]
    logger.info(f"✅ Found source lab: {source_lab.lab_id}")
    
    # Step 7: Get account
    logger.info("\n📋 Getting account information...")
    accounts = api.get_accounts(executor)
    if not accounts:
        logger.error("❌ No accounts found!")
        return
    
    # Use specific account ID if provided
    if args.account_id:
        account = None
        for acc in accounts:
            if acc.account_id == args.account_id:
                account = acc
                break
        
        if not account:
            logger.error(f"❌ Account with ID '{args.account_id}' not found!")
            logger.info("Available accounts:")
            for acc in accounts:
                logger.info(f"   - {acc.name} (ID: {acc.account_id})")
            return
        
        logger.info(f"✅ Using specified account: {account.name} (ID: {account.account_id})")
    else:
        account = accounts[0]
        logger.info(f"✅ Using first available account: {account.name} (ID: {account.account_id})")
    
    # Step 8: Prepare market configurations
    logger.info(f"\n📊 Preparing market configurations for {len(valid_markets)} markets...")
    market_configs = []
    
    for pair in valid_markets:
        try:
            market_tag = convert_pair_to_market_tag(pair, args.exchange)
            market_configs.append({
                "name": f"{pair.replace('/', '_')}_Backtest",
                "market_tag": market_tag,
                "account_id": account.account_id
            })
        except ValueError as e:
            logger.warning(f"⚠️ Skipping invalid pair: {e}")
            continue
    
    logger.info(f"✅ Prepared {len(market_configs)} market configurations")
    
    # Step 9: Define backtest period
    if args.start_time:
        try:
            start_dt = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M")
            start_unix = int(start_dt.timestamp())
        except ValueError:
            logger.error(f"❌ Invalid start time format: {args.start_time}. Use YYYY-MM-DD HH:MM")
            return
    else:
        start_unix = 1744009200  # April 7th 2025 13:00 UTC
    
    if args.end_time:
        try:
            end_dt = datetime.strptime(args.end_time, "%Y-%m-%d %H:%M")
            end_unix = int(end_dt.timestamp())
        except ValueError:
            logger.error(f"❌ Invalid end time format: {args.end_time}. Use YYYY-MM-DD HH:MM")
            return
    else:
        end_unix = int(time.time())  # Now
    
    logger.info(f"\n⏰ Backtest period:")
    logger.info(f"   Start: {datetime.fromtimestamp(start_unix)} (Unix: {start_unix})")
    logger.info(f"   End: {datetime.fromtimestamp(end_unix)} (Unix: {end_unix})")
    
    # Step 10: Define config
    config = LabConfig(
        max_population=10,    # Max Population
        max_generations=100,  # Max Generations
        max_elites=3,         # Max Elites
        mix_rate=40.0,        # Mix Rate
        adjust_rate=25.0      # Adjust Rate
    )
    
    logger.info(f"\n⚙️ Config parameters:")
    logger.info(f"   Max Population: {config.max_population}")
    logger.info(f"   Max Generations: {config.max_generations}")
    logger.info(f"   Max Elites: {config.max_elites}")
    logger.info(f"   Mix Rate: {config.mix_rate}")
    logger.info(f"   Adjust Rate: {config.adjust_rate}")
    
    # Step 11: Run the workflow
    logger.info(f"\n🚀 Starting flexible workflow for {len(market_configs)} markets...")
    
    results = api.bulk_clone_and_backtest_labs(
        executor=executor,
        source_lab_id=source_lab.lab_id,
        market_configs=market_configs,
        start_unix=start_unix,
        end_unix=end_unix,
        config=config,
        send_email=False,
        delay_between_labs=2.0
    )
    
    # Step 12: Process results
    logger.info(f"\n📊 Final Results Summary:")
    logger.info("=" * 50)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    logger.info(f"✅ Successful: {len(successful)}/{len(market_configs)}")
    logger.info(f"❌ Failed: {len(failed)}/{len(market_configs)}")
    
    if successful:
        logger.info(f"\n🏆 Successful Labs:")
        for result in successful:
            logger.info(f"   ✅ {result['lab_name']}")
            logger.info(f"      Lab ID: {result['lab_id']}")
            logger.info(f"      Market: {result['market_tag']}")
            logger.info(f"      Backtest Started: {result['backtest_started']}")
            logger.info(f"      Status: {result['execution_status']}")
            logger.info("")
    
    if failed:
        logger.info(f"\n❌ Failed Labs:")
        for result in failed:
            logger.info(f"   ❌ {result['lab_name']}: {result['error']}")
    
    # Step 13: Summary
    logger.info(f"\n🎉 Flexible Workflow Complete!")
    logger.info(f"   Total Markets: {len(market_configs)}")
    logger.info(f"   Successful: {len(successful)}")
    logger.info(f"   Failed: {len(failed)}")
    logger.info(f"   Success Rate: {(len(successful)/len(market_configs)*100):.1f}%")
    
    if len(successful) > 0:
        logger.info(f"\n🚀 All successful labs are now running backtests!")
        logger.info(f"   You can monitor their progress in the HaasOnline interface.")
        logger.info(f"   Lab IDs for monitoring:")
        for result in successful:
            logger.info(f"     - {result['lab_name']}: {result['lab_id']}")

if __name__ == "__main__":
    main() 