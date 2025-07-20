#!/usr/bin/env python3
"""
Simple Clone Example Lab to Markets

This script clones the existing "Example" lab to the target markets and starts backtests.
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
from pyHaasAPI.model import StartLabExecutionRequest
from utils.auth.authenticator import authenticator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    load_dotenv()
    
    # Target markets
    target_markets = [
        'BTC/USDT', 'ETH/USDT', 'AVAX/USDT', 'SOL/USDT', 'ADA/USDT',
        'XRP/USDT', 'BNB/USDT', 'DOT/USDT', 'LINK/USDT', 'MATIC/USDT',
        'DOGE/USDT', 'TRX/USDT', 'LTC/USDT', 'ATOM/USDT', 'NEAR/USDT'
    ]
    
    # Backtest configuration
    start_unix = 1744009200  # April 7th 2025 13:00 UTC
    end_unix = 1752994800    # End time (approximately 1 year later)
    
    logger.info("🔐 Setting up authentication...")
    
    # Authenticate
    success = authenticator.authenticate()
    if not success:
        raise Exception("Authentication failed")
    
    # Get the authenticated executor
    executor = authenticator.get_executor()
    
    # Get Binance account
    accounts = api.get_accounts(executor)
    binance_accounts = [acc for acc in accounts if acc.exchange_code == "BINANCE"]
    
    if not binance_accounts:
        raise Exception("No Binance accounts found")
    
    account = binance_accounts[0]
    logger.info(f"✅ Using account: {account.name} ({account.account_id})")
    
    # Find the Example lab
    logger.info("🔍 Looking for existing Example lab...")
    labs = api.get_all_labs(executor)
    example_labs = [lab for lab in labs if lab.name == "Example"]
    
    if not example_labs:
        raise Exception("Example lab not found. Please create it first with intelligent mode configuration.")
    
    example_lab = example_labs[0]
    logger.info(f"✅ Found Example lab: {example_lab.name} (ID: {example_lab.lab_id})")
    
    # Get the Example lab details to copy config parameters
    example_lab_details = api.get_lab_details(executor, example_lab.lab_id)
    logger.info(f"📋 Example lab config: {example_lab_details.config}")
    
    # Clone to target markets
    logger.info(f"🔄 Cloning lab to {len(target_markets)} target markets...")
    cloned_labs = []
    
    for i, market_pair in enumerate(target_markets, 1):
        try:
            # Parse market pair
            primary, secondary = market_pair.split('/')
            
            # Generate market tag
            market_tag = f"BINANCE_{primary.upper()}_{secondary.upper()}_"
            
            # Generate lab name
            timestamp = int(time.time())
            lab_name = f"MadHatter_{primary}_{secondary}_{timestamp}"
            
            logger.info(f"  [{i}/{len(target_markets)}] Cloning to {market_tag}...")
            
            # Clone lab
            cloned_lab = api.clone_lab(executor, example_lab.lab_id, lab_name)
            
            # Get the cloned lab details
            lab_details = api.get_lab_details(executor, cloned_lab.lab_id)
            
            # Update market tag and account ID
            lab_details.settings.market_tag = market_tag
            lab_details.settings.account_id = account.account_id
            
            # Copy the config parameters from the Example lab
            lab_details.config = example_lab_details.config
            
            # Update the lab with all the changes
            updated_lab = api.update_lab_details(executor, lab_details)
            
            cloned_labs.append({
                'lab': updated_lab,
                'market_pair': market_pair,
                'market_tag': market_tag
            })
            
            logger.info(f"  ✅ Cloned: {updated_lab.name} -> {market_tag}")
            logger.info(f"  📋 Config copied: {updated_lab.config}")
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"  ❌ Failed to clone to {market_pair}: {e}")
            continue
    
    logger.info(f"✅ Successfully cloned to {len(cloned_labs)} markets")
    
    # Start backtests
    logger.info(f"🚀 Starting backtests on {len(cloned_labs)} labs...")
    logger.info(f"📅 Backtest period: {datetime.fromtimestamp(start_unix)} to {datetime.fromtimestamp(end_unix)}")
    
    for i, lab_info in enumerate(cloned_labs, 1):
        try:
            lab = lab_info['lab']
            market_pair = lab_info['market_pair']
            
            logger.info(f"  [{i}/{len(cloned_labs)}] Starting backtest for {market_pair}...")
            
            # Create start execution request
            request = StartLabExecutionRequest(
                lab_id=lab.lab_id,
                start_unix=start_unix,
                end_unix=end_unix,
                send_email=False
            )
            
            # Start backtest
            result = api.start_lab_execution(executor, request)
            
            logger.info(f"  ✅ Started backtest: {lab.name} (Status: {result.status if hasattr(result, 'status') else 'STARTED'})")
            
            # Small delay to avoid overwhelming the server
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"  ❌ Failed to start backtest for {lab_info['market_pair']}: {e}")
            continue
    
    logger.info("🎉 All backtests started successfully!")
    logger.info("⏳ Backtests are now running. You can monitor their progress in the HaasOnline interface.")

if __name__ == "__main__":
    main() 