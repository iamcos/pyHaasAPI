#!/usr/bin/env python3
"""
Create bots from current server recommendations using pyHaasAPI v2

This script reads the current server bot recommendations and creates bots
using the v2 API with proper account auto-selection and longest backtest workflow.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add pyHaasAPI_v2 to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI_v2"))

from pyHaasAPI_v2.core.client import AsyncHaasClient
from pyHaasAPI_v2.core.auth import AuthenticationManager
from pyHaasAPI_v2.api.bot import BotAPI
from pyHaasAPI_v2.api.account import AccountAPI
from pyHaasAPI_v2.api.backtest import BacktestAPI
from pyHaasAPI_v2.api.market import MarketAPI
from pyHaasAPI_v2.services.bot import BotService
from pyHaasAPI_v2.core.logging import get_logger
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

logger = get_logger("create_bots_v2")


async def create_bots_from_recommendations(
    recommendations_file: str = "current_server_bot_recommendations.json",
    max_bots: int = 5,
    activate: bool = True
) -> None:
    """
    Create bots from server recommendations using v2 API.
    
    Args:
        recommendations_file: Path to recommendations JSON file
        max_bots: Maximum number of bots to create
        activate: Whether to activate bots immediately
    """
    try:
        logger.info("🚀 Starting bot creation from server recommendations (v2)")
        
        # Load recommendations
        with open(recommendations_file, 'r') as f:
            recommendations = json.load(f)
        
        logger.info(f"📋 Loaded {len(recommendations)} recommendations")
        
        # Limit to max_bots
        if len(recommendations) > max_bots:
            recommendations = recommendations[:max_bots]
            logger.info(f"📊 Limited to top {max_bots} recommendations")
        
        # Initialize v2 API components
        from pyHaasAPI_v2.config.api_config import APIConfig
        config = APIConfig(
            host='127.0.0.1',
            port=8090
        )
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        # Authenticate
        logger.info("🔐 Authenticating with HaasOnline API...")
        await auth_manager.authenticate(
            email=os.getenv('API_EMAIL'),
            password=os.getenv('API_PASSWORD')
        )
        logger.info("✅ Authentication successful")
        
        # Initialize APIs
        bot_api = BotAPI(client, auth_manager)
        account_api = AccountAPI(client, auth_manager)
        backtest_api = BacktestAPI(client, auth_manager)
        market_api = MarketAPI(client, auth_manager)
        
        # Initialize bot service
        bot_service = BotService(
            bot_api=bot_api,
            account_api=account_api,
            backtest_api=backtest_api,
            market_api=market_api,
            client=client,
            auth_manager=auth_manager
        )
        
        # Create bots
        created_bots = []
        failed_bots = []
        
        for i, rec in enumerate(recommendations, 1):
            try:
                logger.info(f"🤖 Creating bot {i}/{len(recommendations)}: {rec['bot_name']}")
                
                # Get available account
                available_account = await account_api.get_available_binancefutures_account()
                if not available_account:
                    logger.error("❌ No available BinanceFutures accounts")
                    failed_bots.append({
                        'recommendation': rec,
                        'error': 'No available accounts'
                    })
                    continue
                
                # Create bot from lab analysis
                bot_result = await bot_service.create_bot_from_lab_analysis(
                    lab_id=rec['lab_id'],
                    backtest_id=rec['backtest_id'],
                    account_id=available_account.account_id,
                    bot_name=rec['bot_name'],
                    trade_amount_usdt=2000.0,  # 20% of $10k account
                    leverage=20.0,
                    activate=activate,
                    lab_name=rec['lab_name']
                )
                
                if bot_result.success:
                    created_bots.append(bot_result)
                    logger.info(f"✅ Bot created successfully: {bot_result.bot_id}")
                    logger.info(f"   Name: {bot_result.bot_name}")
                    logger.info(f"   Account: {bot_result.account_id}")
                    logger.info(f"   Market: {bot_result.market_tag}")
                    logger.info(f"   Activated: {bot_result.activated}")
                else:
                    failed_bots.append({
                        'recommendation': rec,
                        'error': bot_result.error_message or 'Unknown error'
                    })
                    logger.error(f"❌ Bot creation failed: {bot_result.error_message}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create bot from recommendation {i}: {e}")
                failed_bots.append({
                    'recommendation': rec,
                    'error': str(e)
                })
        
        # Summary
        logger.info(f"\n📊 Bot Creation Summary")
        logger.info(f"{'='*50}")
        logger.info(f"Total recommendations: {len(recommendations)}")
        logger.info(f"Successfully created: {len(created_bots)}")
        logger.info(f"Failed: {len(failed_bots)}")
        
        if created_bots:
            logger.info(f"\n✅ Successfully Created Bots:")
            for bot in created_bots:
                logger.info(f"  {bot.bot_id}: {bot.bot_name}")
                logger.info(f"    Account: {bot.account_id}")
                logger.info(f"    Market: {bot.market_tag}")
                logger.info(f"    Activated: {bot.activated}")
        
        if failed_bots:
            logger.info(f"\n❌ Failed Bot Creations:")
            for failure in failed_bots:
                logger.info(f"  {failure['recommendation']['bot_name']}")
                logger.info(f"    Error: {failure['error']}")
        
        # Save results
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_recommendations': len(recommendations),
            'successful_creations': len(created_bots),
            'failed_creations': len(failed_bots),
            'created_bots': [
                {
                    'bot_id': bot.bot_id,
                    'bot_name': bot.bot_name,
                    'backtest_id': bot.backtest_id,
                    'account_id': bot.account_id,
                    'market_tag': bot.market_tag,
                    'leverage': bot.leverage,
                    'margin_mode': bot.margin_mode,
                    'position_mode': bot.position_mode,
                    'trade_amount_usdt': bot.trade_amount_usdt,
                    'activated': bot.activated,
                    'creation_timestamp': bot.creation_timestamp
                }
                for bot in created_bots
            ],
            'failed_bots': failed_bots
        }
        
        results_file = f"bot_creation_results_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Results saved to: {results_file}")
        
        # Check backtest progress
        if created_bots:
            logger.info(f"\n📊 Checking longest backtest progress...")
            try:
                bot_ids = [bot.bot_id for bot in created_bots]
                progress_info = await bot_service.check_longest_backtest_progress(bot_ids)
                
                logger.info(f"Backtest Progress:")
                logger.info(f"  Total bots: {progress_info['total_bots']}")
                logger.info(f"  Completed: {progress_info['completed_backtests']}")
                logger.info(f"  Failed: {progress_info['failed_backtests']}")
                logger.info(f"  Pending: {progress_info['pending_backtests']}")
                
            except Exception as e:
                logger.warning(f"Failed to check backtest progress: {e}")
        
    except Exception as e:
        logger.error(f"❌ Bot creation process failed: {e}")
        raise


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create bots from server recommendations using v2 API")
    parser.add_argument('--recommendations', default='current_server_bot_recommendations.json',
                       help='Path to recommendations JSON file')
    parser.add_argument('--max-bots', type=int, default=5,
                       help='Maximum number of bots to create')
    parser.add_argument('--no-activate', action='store_true',
                       help='Do not activate bots immediately')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without actually creating bots')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No bots will be created")
        
        # Load and display recommendations
        with open(args.recommendations, 'r') as f:
            recommendations = json.load(f)
        
        logger.info(f"📋 Would create {min(len(recommendations), args.max_bots)} bots:")
        for i, rec in enumerate(recommendations[:args.max_bots], 1):
            logger.info(f"  {i}. {rec['bot_name']}")
            logger.info(f"     Lab: {rec['lab_name']}")
            logger.info(f"     Market: {rec['market_tag']}")
            logger.info(f"     ROE: {rec['roe']:.1f}%, WR: {rec['win_rate']:.1f}%")
            logger.info(f"     Trades: {rec['total_trades']}")
        
        return
    
    # Create bots
    await create_bots_from_recommendations(
        recommendations_file=args.recommendations,
        max_bots=args.max_bots,
        activate=not args.no_activate
    )


if __name__ == "__main__":
    asyncio.run(main())
