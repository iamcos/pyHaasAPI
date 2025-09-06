#!/usr/bin/env python3
"""
Test script to analyze a specific lab and create bots from it
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest, AddBotFromLabRequest

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_specific_lab():
    """Test the specific lab mentioned by the user"""
    lab_id = "e4616b35-8065-4095-966b-546de68fd493"
    
    # Initialize API connection
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        logger.error("API_EMAIL and API_PASSWORD must be set in .env file")
        return

    logger.info(f"🔌 Connecting to HaasOnline API: {api_host}:{api_port}")

    try:
        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )

        # Authenticate
        executor = haas_api.authenticate(api_email, api_password)
        logger.info("✅ Successfully connected to HaasOnline API")
        
        # Fetch backtests from the specific lab
        logger.info(f"📥 Fetching backtests from lab {lab_id[:8]}...")
        
        request = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=100
        )
        
        response = api.get_backtest_result(executor, request)
        if not response or not hasattr(response, 'items'):
            logger.error("No response or items from lab")
            return
        
        backtests = response.items
        logger.info(f"✅ Found {len(backtests)} backtests")
        
        # Analyze first few backtests to see what data is available
        logger.info("🔍 Analyzing first 5 backtests to see available data...")
        
        for i, backtest in enumerate(backtests[:5], 1):
            logger.info(f"\n--- Backtest {i} ---")
            logger.info(f"Type: {type(backtest)}")
            logger.info(f"Attributes: {dir(backtest)}")
            
            # Try to get basic info
            backtest_id = getattr(backtest, 'backtest_id', 'No ID')
            logger.info(f"ID: {backtest_id}")
            
            # Check summary field
            summary = getattr(backtest, 'summary', None)
            if summary:
                logger.info(f"Summary type: {type(summary)}")
                logger.info(f"Summary attributes: {dir(summary)}")
                
                # Print summary as dict to see all available fields
                if hasattr(summary, 'model_dump'):
                    logger.info(f"Summary dict: {summary.model_dump()}")
                elif hasattr(summary, 'dict'):
                    logger.info(f"Summary dict: {summary.dict()}")
                else:
                    logger.info(f"Summary repr: {repr(summary)}")
                
                # Try to get performance metrics from summary using correct field names
                roi = getattr(summary, 'ReturnOnInvestment', 'No ROI in summary')
                trades = getattr(summary, 'Trades', 'No Trades in summary')
                profits = getattr(summary, 'RealizedProfits', 'No Profits in summary')
                fees = getattr(summary, 'FeeCosts', 'No Fees in summary')
                
                # Calculate win rate if we have trades data
                win_rate = 'No Win Rate'
                if trades and hasattr(trades, 'winning_trades') and hasattr(trades, 'losing_trades'):
                    winning = getattr(trades, 'winning_trades', 0)
                    losing = getattr(trades, 'losing_trades', 0)
                    total = winning + losing
                    if total > 0:
                        win_rate = winning / total
                
                logger.info(f"Summary ROI: {roi}")
                logger.info(f"Summary Win Rate: {win_rate}")
                logger.info(f"Summary Total Trades: {trades}")
                logger.info(f"Summary Profits: {profits}")
                logger.info(f"Summary Fees: {fees}")
            else:
                logger.info("No summary field")
            
            # Try to get performance metrics directly
            roi = getattr(backtest, 'roi_percentage', 'No ROI')
            win_rate = getattr(backtest, 'win_rate', 'No Win Rate')
            trades = getattr(backtest, 'total_trades', 'No Trades')
            drawdown = getattr(backtest, 'max_drawdown', 'No Drawdown')
            
            logger.info(f"Direct ROI: {roi}")
            logger.info(f"Direct Win Rate: {win_rate}")
            logger.info(f"Direct Total Trades: {trades}")
            logger.info(f"Direct Max Drawdown: {drawdown}")
            
            # Try to get market info
            market = getattr(backtest, 'market_tag', 'No Market')
            script_id = getattr(backtest, 'script_id', 'No Script ID')
            
            logger.info(f"Market: {market}")
            logger.info(f"Script ID: {script_id}")
            
            # Try to get generation/population info
            gen_idx = getattr(backtest, 'generation_idx', 'No Gen')
            pop_idx = getattr(backtest, 'population_idx', 'No Pop')
            
            logger.info(f"Generation: {gen_idx}")
            logger.info(f"Population: {pop_idx}")
        
        # Now try to create a bot from the first backtest with good data
        logger.info("\n🤖 Attempting to create a bot from the first backtest...")
        
        if backtests:
            first_backtest = backtests[0]
            backtest_id = getattr(first_backtest, 'backtest_id', '')
            
            if backtest_id:
                # Get available account
                accounts = api.get_all_accounts(executor)
                if not accounts:
                    logger.error("❌ No accounts available")
                    return
                
                logger.info(f"Found {len(accounts)} accounts")
                account = accounts[0]
                logger.info(f"Account type: {type(account)}")
                logger.info(f"Account attributes: {dir(account)}")
                
                # If account is a dictionary, check its keys
                if isinstance(account, dict):
                    logger.info(f"Account keys: {list(account.keys())}")
                    account_id = account.get('AID', '')  # Account ID is likely in AID field
                    logger.info(f"Account AID: {account_id}")
                else:
                    # Try object attributes
                    account_id = getattr(account, 'account_id', '')
                    if not account_id:
                        # Try other possible attribute names
                        account_id = getattr(account, 'id', '')
                        if not account_id:
                            account_id = getattr(account, 'Id', '')
                
                if not account_id:
                    logger.error("❌ Could not find account ID in any known attribute")
                    return
                
                if account_id:
                    # Create bot name using summary data
                    summary = getattr(first_backtest, 'summary', None)
                    roi = 0.0
                    win_rate = 0.0
                    if summary:
                        roi = getattr(summary, 'ReturnOnInvestment', 0.0)
                        # Try to get win rate from trades
                        trades = getattr(summary, 'Trades', None)
                        if trades and hasattr(trades, 'winning_trades') and hasattr(trades, 'losing_trades'):
                            winning = getattr(trades, 'winning_trades', 0)
                            losing = getattr(trades, 'losing_trades', 0)
                            total = winning + losing
                            if total > 0:
                                win_rate = winning / total
                    
                    market = getattr(first_backtest, 'market_tag', 'BINANCEFUTURES_BTC_USDT_PERPETUAL')
                    
                    bot_name = f"TestBot_WR{win_rate:.2f}_ROI{int(roi)}"
                    bot_name = bot_name.replace('.', '')
                    
                    logger.info(f"Creating bot: {bot_name}")
                    logger.info(f"From backtest: {backtest_id[:8]}")
                    logger.info(f"Market: {market}")
                    logger.info(f"Account: {account_id[:8]}")
                    
                    # Create bot
                    request = AddBotFromLabRequest(
                        lab_id=lab_id,
                        backtest_id=backtest_id,
                        account_id=account_id,
                        bot_name=bot_name,
                        market=market,
                        leverage=20
                    )
                    
                    new_bot = api.add_bot_from_lab(executor, request)
                    if new_bot:
                        bot_id = getattr(new_bot, 'bot_id', '')
                        logger.info(f"✅ Bot created successfully: {bot_id[:8]}")
                        
                        # Try to configure the bot
                        try:
                            from pyHaasAPI.api import configure_bot_settings
                            configure_result = configure_bot_settings(
                                executor,
                                bot_id,
                                position_mode=1,  # HEDGE
                                margin_mode=0,     # CROSS
                                leverage=20.0
                            )
                            
                            if configure_result.get("success"):
                                logger.info(f"✅ Bot {bot_id[:8]} configured with HEDGE, CROSS, 20x leverage")
                            else:
                                logger.warning(f"⚠️ Bot {bot_id[:8]} configuration failed: {configure_result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Error configuring bot {bot_id[:8]}: {e}")
                    else:
                        logger.error("❌ Failed to create bot")
                else:
                    logger.error("❌ Account has no ID")
            else:
                logger.error("❌ Backtest has no ID")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    test_specific_lab()
