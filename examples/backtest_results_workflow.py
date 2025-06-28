#!/usr/bin/env python3
"""
Complete Backtest Results Workflow Example

This example demonstrates the full workflow for working with backtest results:
1. Get labs and their details
2. Retrieve backtest results (list of configurations)
3. Analyze specific configurations with runtime, chart, and log data
4. Create bots from the best performing configurations

Each backtest result represents a different parameter configuration that was tested.
"""

import time
import random
from typing import Optional
from loguru import logger
from pyHaasAPI import api
from pyHaasAPI.model import (
    GetBacktestResultRequest, 
    AddBotFromLabRequest,
    LabBacktestResult
)


def setup_logging():
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def get_labs_with_backtests(executor: api.RequestsExecutor):
    """Get all labs that have completed backtests"""
    logger.info("🔍 Getting labs with completed backtests...")
    
    labs = api.get_all_labs(executor)
    labs_with_backtests = [lab for lab in labs if lab.completed_backtests > 0]
    
    if not labs_with_backtests:
        logger.warning("⚠️ No labs with completed backtests found")
        return []
    
    logger.info(f"✅ Found {len(labs_with_backtests)} labs with backtests")
    for lab in labs_with_backtests:
        logger.info(f"   📊 {lab.name}: {lab.completed_backtests} backtests")
    
    return labs_with_backtests


def get_backtest_results(executor: api.RequestsExecutor, lab_id: str, page_size: int = 100):
    """Get backtest results for a specific lab"""
    logger.info(f"📋 Getting backtest results for lab {lab_id}...")
    
    try:
        results = api.get_backtest_result(
            executor,
            GetBacktestResultRequest(
                lab_id=lab_id,
                next_page_id=0,
                page_lenght=page_size
            )
        )
        
        logger.info(f"✅ Retrieved {len(results.items)} backtest configurations")
        logger.info(f"   📄 Total pages: {results.next_page_id if results.next_page_id else 'No more pages'}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Failed to get backtest results: {e}")
        return None


def analyze_backtest_configuration(
    executor: api.RequestsExecutor, 
    lab_id: str, 
    backtest_result: LabBacktestResult
):
    """Analyze a specific backtest configuration in detail"""
    logger.info(f"🔬 Analyzing configuration {backtest_result.backtest_id}...")
    
    # Display basic info
    logger.info(f"   📊 Generation: {backtest_result.generation_idx}, Population: {backtest_result.population_idx}")
    logger.info(f"   📈 Status: {backtest_result.status}")
    
    # Display performance summary
    summary = backtest_result.summary
    if summary:
        logger.info(f"   💰 Fee Costs: {summary.FeeCosts}")
        logger.info(f"   📈 Realized Profits: {summary.RealizedProfits}")
        logger.info(f"   🎯 ROI: {summary.ReturnOnInvestment}")
        
        if summary.CustomReport:
            logger.info(f"   📋 Custom Report: {summary.CustomReport}")
    
    # Get detailed runtime data (with timeout handling)
    try:
        logger.info("   ⚡ Getting runtime data...")
        runtime = api.get_backtest_runtime(executor, lab_id, backtest_result.backtest_id)
        logger.info(f"   ✅ Runtime data retrieved: {len(str(runtime))} chars")
    except Exception as e:
        if "504" in str(e):
            logger.warning("   ⚠️ Runtime data request timed out (504 error)")
        else:
            logger.error(f"   ❌ Runtime data failed: {e}")
    
    # Get chart data (with timeout handling)
    try:
        logger.info("   📊 Getting chart data...")
        chart = api.get_backtest_chart(executor, lab_id, backtest_result.backtest_id)
        logger.info(f"   ✅ Chart data retrieved: {len(chart) if isinstance(chart, dict) else 'N/A'} data points")
    except Exception as e:
        if "504" in str(e):
            logger.warning("   ⚠️ Chart data request timed out (504 error)")
        else:
            logger.error(f"   ❌ Chart data failed: {e}")
    
    # Get execution logs
    try:
        logger.info("   📝 Getting log data...")
        logs = api.get_backtest_log(executor, lab_id, backtest_result.backtest_id)
        logger.info(f"   ✅ Log entries retrieved: {len(logs)} entries")
        
        # Show last few log entries
        if logs and len(logs) > 0:
            logger.info("   📋 Last log entries:")
            for entry in logs[-3:]:  # Last 3 entries
                logger.info(f"      {entry}")
                
    except Exception as e:
        logger.error(f"   ❌ Log data failed: {e}")


def find_best_configurations(results, top_n: int = 5):
    """Find the best performing configurations based on ROI"""
    if not results or not results.items:
        return []
    
    # Sort by ROI (descending)
    sorted_results = sorted(
        results.items, 
        key=lambda x: x.summary.ReturnOnInvestment if x.summary else 0,
        reverse=True
    )
    
    logger.info(f"🏆 Top {min(top_n, len(sorted_results))} configurations by ROI:")
    for i, result in enumerate(sorted_results[:top_n], 1):
        roi = result.summary.ReturnOnInvestment if result.summary else 0
        logger.info(f"   {i}. ROI: {roi:.4f}% (Config: {result.backtest_id})")
    
    return sorted_results[:top_n]


def create_bot_from_configuration(
    executor: api.RequestsExecutor,
    lab_id: str,
    backtest_result: LabBacktestResult,
    account_id: str,
    market_tag: str
) -> Optional[str]:
    """Create a trading bot from a specific backtest configuration"""
    logger.info(f"🤖 Creating bot from configuration {backtest_result.backtest_id}...")
    
    try:
        # Get accounts to find the one we want to use
        accounts = api.get_accounts(executor)
        target_account = None
        
        # Try to find the account by ID first
        for account in accounts:
            if account.account_id == account_id:
                target_account = account
                break
        
        # If not found, use the first available
        if not target_account and accounts:
            target_account = accounts[0]
            logger.warning(f"⚠️ Account {account_id} not found, using {target_account.account_id}")
        
        if not target_account:
            logger.error("❌ No accounts available for bot creation")
            return None
        
        # Create bot name
        roi = backtest_result.summary.ReturnOnInvestment if backtest_result.summary else 0
        bot_name = f"Bot_ROI_{roi:.2f}%_Config_{backtest_result.backtest_id[:8]}"
        
        # Parse market tag to create CloudMarket object
        # Market tag format: "BINANCE_SOL_USDC_"
        parts = market_tag.split("_")
        if len(parts) >= 3:
            exchange = parts[0]
            primary = parts[1]
            secondary = parts[2]
            
            from pyHaasAPI.model import CloudMarket
            market = CloudMarket(
                category="SPOT",
                price_source=exchange,
                primary=primary,
                secondary=secondary
            )
        else:
            logger.error(f"❌ Invalid market tag format: {market_tag}")
            return None
        
        # Create the bot
        bot = api.add_bot_from_lab(
            executor,
            AddBotFromLabRequest(
                lab_id=lab_id,
                backtest_id=backtest_result.backtest_id,
                bot_name=bot_name,
                account_id=target_account.account_id,
                market=market,
                leverage=0  # Default leverage
            )
        )
        
        logger.info(f"✅ Bot created successfully: {bot.bot_name} (ID: {bot.bot_id})")
        return bot.bot_id
        
    except Exception as e:
        logger.error(f"❌ Failed to create bot: {e}")
        return None


def main():
    """Main workflow demonstration"""
    setup_logging()
    
    logger.info("🚀 Starting Backtest Results Workflow Demo")
    
    # Initialize and authenticate
    try:
        executor = api.RequestsExecutor(
            host="127.0.0.1",
            port=8090,
            state=api.Guest()
        ).authenticate(
            email="garrypotterr@gmail.com",
            password="IQYTCQJIQYTCQJ"
        )
        logger.info("✅ Authentication successful")
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        return
    
    # Step 1: Get labs with backtests
    labs_with_backtests = get_labs_with_backtests(executor)
    if not labs_with_backtests:
        logger.error("❌ No labs with backtests available")
        return
    
    # Step 2: Select a lab and get its details
    selected_lab = random.choice(labs_with_backtests)
    logger.info(f"🎯 Selected lab: {selected_lab.name}")
    
    try:
        lab_details = api.get_lab_details(executor, selected_lab.lab_id)
        logger.info(f"✅ Lab details retrieved: {len(lab_details.parameters)} parameters")
        
        # Get market information from settings
        market_tag = lab_details.settings.market_tag if hasattr(lab_details.settings, 'market_tag') else "UNKNOWN"
        logger.info(f"📊 Market: {market_tag}")
        
    except Exception as e:
        logger.error(f"❌ Failed to get lab details: {e}")
        return
    
    # Step 3: Get backtest results (list of configurations)
    results = get_backtest_results(executor, selected_lab.lab_id, page_size=50)
    if not results or not results.items:
        logger.error("❌ No backtest results available")
        return
    
    # Step 4: Find best configurations
    best_configs = find_best_configurations(results, top_n=3)
    if not best_configs:
        logger.warning("⚠️ No valid configurations found")
        return
    
    # Step 5: Analyze the best configuration in detail
    best_config = best_configs[0]
    logger.info(f"\n🔬 Detailed analysis of best configuration:")
    analyze_backtest_configuration(executor, selected_lab.lab_id, best_config)
    
    # Step 6: Create a bot from the best configuration
    logger.info(f"\n🤖 Creating bot from best configuration...")
    bot_id = create_bot_from_configuration(
        executor,
        selected_lab.lab_id,
        best_config,
        account_id="",  # Will be auto-selected
        market_tag=market_tag
    )
    
    if bot_id:
        logger.info(f"🎉 Workflow completed successfully! Bot created: {bot_id}")
        
        # Optional: List all bots to confirm
        try:
            bots = api.get_all_bots(executor)
            logger.info(f"📋 Total bots: {len(bots)}")
        except Exception as e:
            logger.error(f"❌ Failed to list bots: {e}")
    else:
        logger.error("❌ Bot creation failed")
    
    logger.info("🏁 Backtest Results Workflow Demo completed")


if __name__ == "__main__":
    main() 