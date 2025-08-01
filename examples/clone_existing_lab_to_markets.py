#!/usr/bin/env python3
"""
Clone Existing Example Lab to Markets

This script clones the existing "Example" lab to the target markets and starts backtests.
The Example lab should already be configured with intelligent mode parameters.
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI import api
from pyHaasAPI.model import (
    StartLabExecutionRequest,
    GetBacktestResultRequest,
    AddBotFromLabRequest
)
from utils.auth.authenticator import authenticator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LabCloner:
    def __init__(self):
        self.executor = None
        self.account = None
        self.example_lab_id = None
        self.cloned_labs = []
        
        # Backtest configuration
        self.start_unix = 1744009200  # April 7th 2025 13:00 UTC
        self.end_unix = 1752994800    # End time (approximately 1 year later)
        
        # Target markets
        self.target_markets = [
            'BTC/USDT',
            'ETH/USDT',
            'AVAX/USDT',
            'SOL/USDT',
            'ADA/USDT',
            'XRP/USDT',
            'BNB/USDT',
            'DOT/USDT',
            'LINK/USDT',
            'MATIC/USDT',
            'DOGE/USDT',
            'TRX/USDT',
            'LTC/USDT',
            'ATOM/USDT',
            'NEAR/USDT'
        ]
        
    def setup(self):
        """Initialize authentication and get account"""
        logger.info("🔐 Setting up authentication...")
        
        # Authenticate
        success = authenticator.authenticate()
        if not success:
            raise Exception("Authentication failed")
        
        # Get the authenticated executor
        self.executor = authenticator.get_executor()
        
        # Get Binance account
        accounts = api.get_accounts(self.executor)
        binance_accounts = [acc for acc in accounts if acc.exchange_code == "BINANCE"]
        
        if not binance_accounts:
            raise Exception("No Binance accounts found")
        
        self.account = binance_accounts[0]
        logger.info(f"✅ Using account: {self.account.name} ({self.account.account_id})")
        
    def find_example_lab(self):
        """Find the existing Example lab"""
        logger.info("🔍 Looking for existing Example lab...")
        
        # Get all labs
        labs = api.get_all_labs(self.executor)
        
        # Find the Example lab
        example_labs = [lab for lab in labs if lab.name == "Example"]
        
        if not example_labs:
            raise Exception("Example lab not found. Please create it first with intelligent mode configuration.")
        
        self.example_lab_id = example_labs[0].lab_id
        logger.info(f"✅ Found Example lab: {example_labs[0].name} (ID: {self.example_lab_id})")
        
        return example_labs[0]
    
    def clone_to_target_markets(self):
        """Clone the example lab to the target markets"""
        logger.info(f"🔄 Cloning lab to {len(self.target_markets)} target markets...")
        
        cloned_labs = []
        
        for i, market_pair in enumerate(self.target_markets, 1):
            try:
                # Parse market pair
                primary, secondary = market_pair.split('/')
                
                # Generate market tag
                market_tag = f"BINANCE_{primary.upper()}_{secondary.upper()}_"
                
                # Generate lab name
                timestamp = int(time.time())
                lab_name = f"MadHatter_{primary}_{secondary}_{timestamp}"
                
                logger.info(f"  [{i}/{len(self.target_markets)}] Cloning to {market_tag}...")
                
                # Clone lab
                cloned_lab = api.clone_lab(self.executor, self.example_lab_id, lab_name)
                
                # Update market tag and account ID
                lab_details = api.get_lab_details(self.executor, cloned_lab.lab_id)
                lab_details.settings.market_tag = market_tag
                lab_details.settings.account_id = self.account.account_id
                updated_lab = api.update_lab_details(self.executor, lab_details)
                
                cloned_labs.append({
                    'lab': updated_lab,
                    'market_pair': market_pair,
                    'market_tag': market_tag
                })
                
                logger.info(f"  ✅ Cloned: {updated_lab.name} -> {market_tag}")
                
                # Small delay to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ Failed to clone to {market_pair}: {e}")
                continue
        
        self.cloned_labs = cloned_labs
        logger.info(f"✅ Successfully cloned to {len(cloned_labs)} markets")
        return cloned_labs
    
    def start_backtests(self):
        """Start backtests on all cloned labs"""
        logger.info(f"🚀 Starting backtests on {len(self.cloned_labs)} labs...")
        logger.info(f"📅 Backtest period: {datetime.fromtimestamp(self.start_unix)} to {datetime.fromtimestamp(self.end_unix)}")
        
        started_labs = []
        
        for i, lab_info in enumerate(self.cloned_labs, 1):
            try:
                lab = lab_info['lab']
                market_tag = lab_info['market_tag']
                market_pair = lab_info['market_pair']
                
                logger.info(f"  [{i}/{len(self.cloned_labs)}] Starting backtest for {market_pair}...")
                
                # Create start execution request
                request = StartLabExecutionRequest(
                    lab_id=lab.lab_id,
                    start_unix=self.start_unix,
                    end_unix=self.end_unix,
                    send_email=False
                )
                
                # Start backtest
                result = api.start_lab_execution(self.executor, request)
                
                started_labs.append({
                    'lab': lab,
                    'market_tag': market_tag,
                    'market_pair': market_pair,
                    'status': result.status if hasattr(result, 'status') else 'STARTED'
                })
                
                logger.info(f"  ✅ Started backtest: {lab.name} (Status: {result.status if hasattr(result, 'status') else 'STARTED'})")
                
                # Small delay to avoid overwhelming the server
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"  ❌ Failed to start backtest for {lab_info['market_pair']}: {e}")
                continue
        
        logger.info(f"✅ Started backtests on {len(started_labs)} labs")
        return started_labs
    
    def wait_for_backtest_completion(self, timeout_minutes=120):
        """Wait for backtests to complete"""
        logger.info(f"⏳ Waiting for backtests to complete (timeout: {timeout_minutes} minutes)...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            completed_count = 0
            total_count = len(self.cloned_labs)
            
            for lab_info in self.cloned_labs:
                try:
                    lab_details = api.get_lab_details(self.executor, lab_info['lab'].lab_id)
                    
                    # Check if backtest is completed
                    if hasattr(lab_details, 'status'):
                        if str(lab_details.status) == '3':  # COMPLETED
                            completed_count += 1
                        elif str(lab_details.status) == '4':  # CANCELLED
                            logger.warning(f"⚠️ Backtest cancelled for {lab_info['market_pair']}")
                
                except Exception as e:
                    logger.debug(f"Error checking status for {lab_info['market_pair']}: {e}")
            
            logger.info(f"📊 Progress: {completed_count}/{total_count} backtests completed")
            
            if completed_count == total_count:
                logger.info("✅ All backtests completed!")
                return True
            
            # Wait before checking again
            time.sleep(30)
        
        logger.warning(f"⚠️ Timeout reached. Some backtests may still be running.")
        return False
    
    def create_bots_from_results(self, top_n=3):
        """Create bots from backtest results"""
        logger.info(f"🤖 Creating top {top_n} bots from backtest results...")
        
        created_bots = []
        
        for lab_info in self.cloned_labs:
            try:
                lab = lab_info['lab']
                market_tag = lab_info['market_tag']
                market_pair = lab_info['market_pair']
                
                logger.info(f"📊 Getting backtest results for {market_pair}...")
                
                # Get backtest results
                request = GetBacktestResultRequest(
                    lab_id=lab.lab_id,
                    next_page_id=0,
                    page_lenght=1000
                )
                
                results = api.get_backtest_result(self.executor, request)
                
                if not results or not results.items:
                    logger.warning(f"⚠️ No backtest results for {market_pair}")
                    continue
                
                # Sort by ROI and get top results
                sorted_results = sorted(
                    results.items, 
                    key=lambda x: x.summary.ReturnOnInvestment if x.summary else 0,
                    reverse=True
                )
                
                top_results = sorted_results[:top_n]
                
                for i, result in enumerate(top_results, 1):
                    try:
                        # Create bot from backtest result
                        bot_request = AddBotFromLabRequest(
                            lab_id=lab.lab_id,
                            backtest_id=result.backtest_id,
                            bot_name=f"Bot_{market_pair.replace('/', '')}_{i}_{int(time.time())}",
                            account_id=self.account.account_id
                        )
                        
                        bot = api.add_bot_from_lab(self.executor, bot_request)
                        
                        created_bots.append({
                            'bot': bot,
                            'market_pair': market_pair,
                            'roi': result.summary.ReturnOnInvestment if result.summary else 0,
                            'rank': i
                        })
                        
                        logger.info(f"  ✅ Created bot: {bot.bot_name} (ROI: {result.summary.ReturnOnInvestment if result.summary else 0:.2f}%)")
                        
                    except Exception as e:
                        logger.error(f"  ❌ Failed to create bot {i} for {market_pair}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"❌ Failed to get backtest results for {lab_info['market_pair']}: {e}")
                continue
        
        logger.info(f"✅ Created {len(created_bots)} bots from backtest results")
        return created_bots
    
    def run_complete_workflow(self):
        """Run the complete workflow"""
        logger.info("🚀 Starting complete lab cloning workflow...")
        logger.info(f"📋 Target markets: {', '.join(self.target_markets)}")
        
        try:
            # Step 1: Setup
            self.setup()
            
            # Step 2: Find existing Example lab
            self.find_example_lab()
            
            # Step 3: Clone to target markets
            self.clone_to_target_markets()
            
            # Step 4: Start backtests
            self.start_backtests()
            
            # Step 5: Wait for completion
            self.wait_for_backtest_completion()
            
            # Step 6: Create bots
            self.create_bots_from_results()
            
            logger.info("🎉 Complete workflow finished successfully!")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            raise

def main():
    """Main function"""
    load_dotenv()
    
    cloner = LabCloner()
    cloner.run_complete_workflow()

if __name__ == "__main__":
    main() 