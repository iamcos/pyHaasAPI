#!/usr/bin/env python3
"""
Integrated Lab Cloning and Backtesting Workflow - DEMONSTRATION

This script demonstrates the new integrated workflow that automatically handles:
1. ✅ Lab cloning with all settings preserved
2. ✅ Market and account updates
3. ✅ Config parameter validation and correction
4. ✅ Backtest execution with proper validation

⚠️ NOTE: This example uses predefined markets for demonstration purposes.
For flexible market selection, use examples/flexible_lab_workflow.py instead.

This is the RECOMMENDED approach for production use.
"""

import os
import sys
import time
import logging
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

def main():
    """Main function demonstrating the integrated workflow"""
    load_dotenv()
    
    logger.info("🚀 Integrated Lab Cloning and Backtesting Workflow Demo")
    logger.info("=" * 70)
    
    # Step 1: Authentication
    logger.info("🔐 Setting up authentication...")
    success = authenticator.authenticate()
    if not success:
        logger.error("❌ Authentication failed!")
        return
    
    executor = authenticator.get_executor()
    logger.info("✅ Authentication successful")
    
    # Step 2: Find the Example lab
    logger.info("\n🔍 Looking for existing Example lab...")
    labs = api.get_all_labs(executor)
    example_labs = [lab for lab in labs if lab.name == "Example"]
    
    if not example_labs:
        logger.error("❌ No Example lab found! Please create an Example lab first.")
        return
    
    example_lab = example_labs[0]
    logger.info(f"✅ Found Example lab: {example_lab.lab_id}")
    
    # Step 3: Define target markets
    target_markets = [
        'BTC/USDT', 'ETH/USDT', 'AVAX/USDT', 'SOL/USDT', 'ADA/USDT',
        'XRP/USDT', 'BNB/USDT', 'DOT/USDT', 'LINK/USDT', 'MATIC/USDT',
        'DOGE/USDT', 'TRX/USDT', 'LTC/USDT', 'ATOM/USDT', 'NEAR/USDT'
    ]
    
    # Step 4: Get account
    logger.info("\n📋 Getting account information...")
    accounts = api.get_accounts(executor)
    if not accounts:
        logger.error("❌ No accounts found!")
        return
    
    account = accounts[0]
    logger.info(f"✅ Using account: {account.name} (ID: {account.account_id})")
    
    # Step 5: Prepare market configurations
    logger.info("\n📊 Preparing market configurations...")
    market_configs = []
    
    for pair in target_markets:
        # Convert pair to market tag format
        if '/' in pair:
            primary, secondary = pair.split('/')
            market_tag = f"BINANCE_{primary.upper()}_{secondary.upper()}_"
        else:
            logger.warning(f"⚠️ Skipping invalid pair format: {pair}")
            continue
            
        market_configs.append({
            "name": f"{pair.replace('/', '_')}_Backtest",
            "market_tag": market_tag,
            "account_id": account.account_id
        })
    
    logger.info(f"✅ Prepared {len(market_configs)} market configurations")
    
    # Step 6: Define backtest period (April 7th 2025 13:00 to now)
    start_unix = 1744009200  # April 7th 2025 13:00 UTC
    end_unix = int(time.time())  # Now
    
    logger.info(f"\n⏰ Backtest period:")
    logger.info(f"   Start: {datetime.fromtimestamp(start_unix)} (Unix: {start_unix})")
    logger.info(f"   End: {datetime.fromtimestamp(end_unix)} (Unix: {end_unix})")
    
    # Step 7: Define config (optional - will use default if not provided)
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
    
    # Step 8: Run the integrated workflow
    logger.info(f"\n🚀 Starting integrated workflow for {len(market_configs)} markets...")
    
    results = api.bulk_clone_and_backtest_labs(
        executor=executor,
        source_lab_id=example_lab.lab_id,
        market_configs=market_configs,
        start_unix=start_unix,
        end_unix=end_unix,
        config=config,
        send_email=False,
        delay_between_labs=2.0
    )
    
    # Step 9: Process results
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
    
    # Step 10: Summary
    logger.info(f"\n🎉 Integrated Workflow Complete!")
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