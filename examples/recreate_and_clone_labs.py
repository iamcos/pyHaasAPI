#!/usr/bin/env python3
"""
Recreate Example Lab and Clone to All Markets

This script recreates the example lab with MadHatter script and parameters,
then clones it to all Binance USDT markets, updates market tags and account IDs,
and starts backtests from April 7th 2025 13:00.
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

from pyHaasAPI import api
from pyHaasAPI.model import (
    CreateLabRequest, 
    StartLabExecutionRequest,
    GetBacktestResultRequest,
    AddBotFromLabRequest
)
from utils.auth.authenticator import authenticator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LabClonerAndExecutor:
    def __init__(self):
        self.executor = None
        self.account = None
        self.example_lab_id = None
        self.cloned_labs = []
        
        # Backtest configuration
        self.start_unix = 1744009200  # April 7th 2025 13:00 UTC
        self.end_unix = 1752994800    # End time (approximately 1 year later)
        
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
        
    def create_example_lab(self):
        """Create the example lab with MadHatter script and parameters"""
        logger.info("🔧 Creating example lab with MadHatter script...")
        
        # Get MadHatter script
        scripts = api.get_scripts_by_name(self.executor, "MadHatter")
        if not scripts:
            raise Exception("MadHatter script not found")
        
        madhatter_script = scripts[0]
        logger.info(f"✅ Found MadHatter script: {madhatter_script.script_name}")
        
        # Create lab request
        timestamp = int(time.time())
        lab_name = f"Example_MadHatter_{timestamp}"
        
        lab_request = CreateLabRequest(
            script_id=madhatter_script.script_id,
            name=lab_name,
            account_id=self.account.account_id,
            market="BINANCE_BTC_USDT_",
            interval=1,
            default_price_data_style="CandleStick",
            trade_amount=100,
            chart_style=300,
            order_template=500,
            leverage=0,
            position_mode=0,
            margin_mode=0
        )
        
        # Create lab
        lab = api.create_lab(self.executor, lab_request)
        self.example_lab_id = lab.lab_id
        logger.info(f"✅ Created example lab: {lab.name} (ID: {lab.lab_id})")
        
        # Update lab with parameters (based on the working example)
        self.update_lab_parameters()
        
        return lab
    
    def update_lab_parameters(self):
        """Update the example lab with the correct parameters"""
        logger.info("⚙️ Updating lab parameters...")
        
        lab_details = api.get_lab_details(self.executor, self.example_lab_id)
        
        # Update parameters based on the working example
        updated_parameters = []
        for param in lab_details.parameters:
            key = param.get('K', '')
            
            # Set specific parameter values based on the working example
            if "Stop Loss (%)" in key:
                param['O'] = [1, 2, 3, 4, 5]
                param['I'] = True
            elif "Take Profit (%)" in key:
                param['O'] = [1, 2, 3, 4, 5]
                param['I'] = True
            elif "BBands Length" in key:
                param['O'] = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
                param['I'] = True
            elif "BBands DevUp" in key:
                param['O'] = [1, 1.25, 1.5, 1.75, 2]
                param['I'] = True
            elif "BBands DevDown" in key:
                param['O'] = [1, 1.25, 1.5, 1.75, 2]
                param['I'] = True
            elif "MACD Fast" in key:
                param['O'] = [12, 17, 22, 27, 32, 37, 42, 47]
                param['I'] = True
            elif "MACD Slow" in key:
                param['O'] = [70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140]
                param['I'] = True
            elif "MACD Signal" in key:
                param['O'] = [7, 12, 17, 22]
                param['I'] = True
            elif "RSI Length" in key:
                param['O'] = [6, 8, 10, 12, 14, 16, 18, 20]
                param['I'] = True
            elif "RSI Buy Level" in key:
                param['O'] = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]
                param['I'] = True
            elif "RSI Sell Level" in key:
                param['O'] = [55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70]
                param['I'] = True
            elif "Indicator Consensus" in key:
                param['O'] = ["True"]
                param['I'] = True
            elif "BBands Require FCC" in key:
                param['O'] = ["False"]
                param['I'] = True
            elif "BBands Reset Middle" in key:
                param['O'] = ["False"]
                param['I'] = True
            elif "BBands Allow Mid Sells" in key:
                param['O'] = ["False"]
                param['I'] = True
            elif "BBands Deviation" in key:
                param['O'] = ["0.2"]
                param['I'] = False
            elif "BBands MA Type" in key:
                param['O'] = ["Sma", "Wma", "Trima", "Mama"]
                param['I'] = True
            
            updated_parameters.append(param)
        
        # Update lab details
        lab_details.parameters = updated_parameters
        updated_lab = api.update_lab_details(self.executor, lab_details)
        logger.info(f"✅ Updated lab parameters: {len(updated_parameters)} parameters")
        
        return updated_lab
    
    def get_binance_markets(self):
        """Get all Binance USDT markets"""
        logger.info("📊 Getting Binance USDT markets...")
        
        markets = api.get_all_markets(self.executor)
        binance_markets = [
            market for market in markets 
            if market.price_source == "BINANCE" and market.secondary == "USDT"
        ]
        
        logger.info(f"✅ Found {len(binance_markets)} Binance USDT markets")
        return binance_markets
    
    def clone_to_markets(self, markets: List):
        """Clone the example lab to all markets"""
        logger.info(f"🔄 Cloning lab to {len(markets)} markets...")
        
        cloned_labs = []
        
        for i, market in enumerate(markets, 1):
            try:
                # Generate market tag
                market_tag = f"BINANCE_{market.primary.upper()}_{market.secondary.upper()}_"
                
                # Generate lab name
                timestamp = int(time.time())
                lab_name = f"MadHatter_{market.primary}_{market.secondary}_{timestamp}"
                
                logger.info(f"  [{i}/{len(markets)}] Cloning to {market_tag}...")
                
                # Clone lab
                cloned_lab = api.clone_lab(self.executor, self.example_lab_id, lab_name)
                
                # Update market tag and account ID
                lab_details = api.get_lab_details(self.executor, cloned_lab.lab_id)
                lab_details.settings.market_tag = market_tag
                lab_details.settings.account_id = self.account.account_id
                updated_lab = api.update_lab_details(self.executor, lab_details)
                
                cloned_labs.append({
                    'lab': updated_lab,
                    'market': market,
                    'market_tag': market_tag
                })
                
                logger.info(f"  ✅ Cloned: {updated_lab.name} -> {market_tag}")
                
                # Small delay to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ Failed to clone to {market.primary}/{market.secondary}: {e}")
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
                
                logger.info(f"  [{i}/{len(self.cloned_labs)}] Starting backtest for {market_tag}...")
                
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
                    'status': result.status if hasattr(result, 'status') else 'STARTED'
                })
                
                logger.info(f"  ✅ Started backtest: {lab.name} (Status: {result.status if hasattr(result, 'status') else 'STARTED'})")
                
                # Small delay to avoid overwhelming the server
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"  ❌ Failed to start backtest for {lab_info['market_tag']}: {e}")
                continue
        
        logger.info(f"✅ Started backtests on {len(started_labs)} labs")
        return started_labs
    
    def wait_for_backtest_completion(self, timeout_minutes=60):
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
                            logger.warning(f"⚠️ Backtest cancelled for {lab_info['market_tag']}")
                
                except Exception as e:
                    logger.debug(f"Error checking status for {lab_info['market_tag']}: {e}")
            
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
                
                logger.info(f"📊 Getting backtest results for {market_tag}...")
                
                # Get backtest results
                request = GetBacktestResultRequest(
                    lab_id=lab.lab_id,
                    next_page_id=0,
                    page_lenght=1000
                )
                
                results = api.get_backtest_result(self.executor, request)
                
                if not results or not results.items:
                    logger.warning(f"⚠️ No backtest results for {market_tag}")
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
                            bot_name=f"Bot_{market_tag.replace('_', '')}_{i}_{int(time.time())}",
                            account_id=self.account.account_id
                        )
                        
                        bot = api.add_bot_from_lab(self.executor, bot_request)
                        
                        created_bots.append({
                            'bot': bot,
                            'market_tag': market_tag,
                            'roi': result.summary.ReturnOnInvestment if result.summary else 0,
                            'rank': i
                        })
                        
                        logger.info(f"  ✅ Created bot: {bot.bot_name} (ROI: {result.summary.ReturnOnInvestment if result.summary else 0:.2f}%)")
                        
                    except Exception as e:
                        logger.error(f"  ❌ Failed to create bot {i} for {market_tag}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"❌ Failed to get backtest results for {lab_info['market_tag']}: {e}")
                continue
        
        logger.info(f"✅ Created {len(created_bots)} bots from backtest results")
        return created_bots
    
    def run_complete_workflow(self):
        """Run the complete workflow"""
        logger.info("🚀 Starting complete lab cloning and execution workflow...")
        
        try:
            # Step 1: Setup
            self.setup()
            
            # Step 2: Create example lab
            self.create_example_lab()
            
            # Step 3: Get markets
            markets = self.get_binance_markets()
            
            # Step 4: Clone to markets
            self.clone_to_markets(markets)
            
            # Step 5: Start backtests
            self.start_backtests()
            
            # Step 6: Wait for completion
            self.wait_for_backtest_completion()
            
            # Step 7: Create bots
            self.create_bots_from_results()
            
            logger.info("🎉 Complete workflow finished successfully!")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            raise

def main():
    """Main function"""
    load_dotenv()
    
    cloner = LabClonerAndExecutor()
    cloner.run_complete_workflow()

if __name__ == "__main__":
    main() 