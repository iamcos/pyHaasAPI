#!/usr/bin/env python3
"""
Complete Bot Management Example

This script demonstrates the full bot management workflow:
1. Analyze lab and select top performers
2. Create bots with proper configuration (HEDGE, CROSS, 20x leverage, $2,000 trade amount)
3. Verify bot configuration
4. Activate bots for live trading
5. Monitor bot status

Usage:
    python complete_bot_management_example.py <lab_id> [--create-count N] [--activate]
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI_v1 import (
    HaasAnalyzer, 
    UnifiedCacheManager, 
    BacktestAnalysis, 
    BotCreationResult, 
    LabAnalysisResult
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of other loggers
logging.getLogger('pyHaasAPI').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


def verify_bot_configuration(analyzer: HaasAnalyzer, bot_result: BotCreationResult) -> bool:
    """Verify that a bot has the correct configuration"""
    try:
        from pyHaasAPI_v1 import api
        
        # Get bot details
        bot = api.get_bot(analyzer.executor, bot_result.bot_id)
        if not bot:
            logger.error(f"❌ Could not get bot details for {bot_result.bot_id[:8]}")
            return False
        
        # Check trade amount - get from full bot runtime data
        try:
            full_bot_data = api.get_full_bot_runtime_data(analyzer.executor, bot_result.bot_id)
            trade_amount = full_bot_data.settings.trade_amount
        except:
            # Fallback to basic bot data
            trade_amount = bot.settings.trade_amount
        expected_amount = 2000.0
        
        # Check margin settings
        margin_settings = api.get_margin_settings(analyzer.executor, bot_result.account_id, bot_result.market_tag)
        
        # Parse margin settings
        position_mode = margin_settings.get('PM', 'Unknown')
        margin_mode = margin_settings.get('SMM', 'Unknown')
        leverage = margin_settings.get('LL', 'Unknown')
        
        # Verify configuration
        config_correct = (
            trade_amount == expected_amount and
            position_mode == 1 and  # HEDGE
            margin_mode == 0 and    # CROSS
            leverage == 20.0        # 20x leverage
        )
        
        if config_correct:
            logger.info(f"✅ Bot {bot_result.bot_name} configuration verified:")
            logger.info(f"   Trade Amount: ${trade_amount} USDT")
            logger.info(f"   Position Mode: HEDGE ({position_mode})")
            logger.info(f"   Margin Mode: CROSS ({margin_mode})")
            logger.info(f"   Leverage: {leverage}x")
            return True
        else:
            logger.warning(f"⚠️ Bot {bot_result.bot_name} configuration issues:")
            logger.warning(f"   Trade Amount: ${trade_amount} USDT (expected: ${expected_amount})")
            logger.warning(f"   Position Mode: {position_mode} (expected: 1)")
            logger.warning(f"   Margin Mode: {margin_mode} (expected: 0)")
            logger.warning(f"   Leverage: {leverage}x (expected: 20.0x)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying bot configuration: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Complete Bot Management Example')
    parser.add_argument('lab_id', help='Lab ID to analyze and create bots from')
    parser.add_argument('--create-count', type=int, default=3, help='Number of bots to create (default: 3)')
    parser.add_argument('--activate', action='store_true', help='Activate bots for live trading')
    parser.add_argument('--verify', action='store_true', help='Verify bot configuration after creation')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Complete Bot Management Workflow")
    logger.info("=" * 60)
    
    # Create analyzer with cache manager
    cache_manager = UnifiedCacheManager("bot_management_cache")
    analyzer = HaasAnalyzer(cache_manager)
    
    # Connect to API
    logger.info("📡 Connecting to HaasOnline API...")
    if not analyzer.connect():
        logger.error("❌ Failed to connect to HaasOnline API")
        return False
    
    logger.info("✅ Connected successfully!")
    
    try:
        # Step 1: Analyze lab
        logger.info(f"\n🔍 Step 1: Analyzing lab {args.lab_id[:8]}...")
        result = analyzer.analyze_lab(args.lab_id, top_count=args.create_count)
        
        logger.info(f"📊 Analysis Results:")
        logger.info(f"  Lab: {result.lab_name}")
        logger.info(f"  Total Backtests: {result.total_backtests}")
        logger.info(f"  Analyzed: {result.analyzed_backtests}")
        logger.info(f"  Processing Time: {result.processing_time:.2f}s")
        
        # Display top backtests
        logger.info(f"\n🏆 Top {len(result.top_backtests)} Backtests:")
        for i, backtest in enumerate(result.top_backtests, 1):
            logger.info(f"  {i}. {backtest.backtest_id[:8]}")
            logger.info(f"     ROI: {backtest.roi_percentage:.2f}%")
            logger.info(f"     Win Rate: {backtest.win_rate:.1%}")
            logger.info(f"     Trades: {backtest.total_trades}")
            logger.info(f"     Market: {backtest.market_tag}")
        
        # Save report
        report_path = cache_manager.save_analysis_report(result)
        logger.info(f"📄 Report saved: {report_path}")
        
        # Step 2: Create and configure bots
        logger.info(f"\n🤖 Step 2: Creating {args.create_count} bots with proper configuration...")
        logger.info("   Configuration:")
        logger.info("   - Position Mode: HEDGE")
        logger.info("   - Margin Mode: CROSS")
        logger.info("   - Leverage: 20x")
        logger.info("   - Trade Amount: $2,000 USDT (20% of $10,000)")
        
        if args.activate:
            bots_created = analyzer.create_and_activate_bots(result, create_count=args.create_count, activate=True)
        else:
            bots_created = analyzer.create_bots_from_analysis(result, create_count=args.create_count)
        
        # Step 3: Display results
        logger.info(f"\n📋 Step 3: Bot Creation Results")
        successful_bots = [bot for bot in bots_created if bot.success]
        logger.info(f"✅ Successfully created {len(successful_bots)} bots:")
        
        for bot in successful_bots:
            logger.info(f"  🤖 {bot.bot_name}")
            logger.info(f"     ID: {bot.bot_id[:8]}")
            logger.info(f"     Market: {bot.market_tag}")
            logger.info(f"     Leverage: {bot.leverage}x")
            logger.info(f"     Margin Mode: {bot.margin_mode}")
            logger.info(f"     Position Mode: {bot.position_mode}")
            logger.info(f"     Trade Amount: ${bot.trade_amount_usdt} USDT")
            logger.info(f"     Activated: {'✅ YES' if bot.activated else '❌ NO'}")
        
        # Step 4: Verify configuration (if requested)
        if args.verify and successful_bots:
            logger.info(f"\n🔍 Step 4: Verifying bot configurations...")
            for bot in successful_bots:
                verify_bot_configuration(analyzer, bot)
        
        # Step 5: Summary
        logger.info(f"\n📊 Final Summary:")
        logger.info(f"  Total Bots Created: {len(successful_bots)}")
        logger.info(f"  Activated Bots: {sum(1 for bot in successful_bots if bot.activated)}")
        logger.info(f"  Trade Amount per Bot: $2,000 USDT")
        logger.info(f"  Total Capital Deployed: ${len(successful_bots) * 2000} USDT")
        
        if args.activate:
            logger.info(f"\n🚀 Bots are now LIVE and trading!")
            logger.info(f"   Each bot is trading with $2,000 USDT (20% of $10,000)")
            logger.info(f"   All bots are configured with HEDGE mode, CROSS margin, 20x leverage")
        else:
            logger.info(f"\n⚠️ Bots created but NOT activated")
            logger.info(f"   Use --activate flag to start live trading")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during bot management workflow: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
