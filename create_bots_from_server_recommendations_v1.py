#!/usr/bin/env python3
"""
Create bots from current server recommendations using pyHaasAPI v1

This script reads the current server bot recommendations and creates bots
using the v1 API with proper account assignment and bot configuration.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


def create_bots_from_recommendations(
    recommendations_file: str = "current_server_bot_recommendations.json",
    max_bots: int = 5,
    activate: bool = True
) -> None:
    """
    Create bots from server recommendations using v1 API.
    
    Args:
        recommendations_file: Path to recommendations JSON file
        max_bots: Maximum number of bots to create
        activate: Whether to activate bots immediately
    """
    try:
        print("🚀 Starting bot creation from server recommendations (v1)")
        
        # Load recommendations
        with open(recommendations_file, 'r') as f:
            recommendations = json.load(f)
        
        print(f"📋 Loaded {len(recommendations)} recommendations")
        
        # Limit to max_bots
        if len(recommendations) > max_bots:
            recommendations = recommendations[:max_bots]
            print(f"📊 Limited to top {max_bots} recommendations")
        
        # Initialize v1 API
        print("🔐 Authenticating with HaasOnline API...")
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'),
            os.getenv('API_PASSWORD')
        )
        print("✅ Authentication successful")
        
        # Get available accounts
        print("📋 Getting available accounts...")
        accounts = api.get_all_accounts(executor)
        binancefutures_accounts = [
            acc for acc in accounts 
            if acc.get('EC', '').upper() == "BINANCEFUTURES"
        ]
        
        if not binancefutures_accounts:
            print("❌ No BinanceFutures accounts found")
            return
        
        print(f"✅ Found {len(binancefutures_accounts)} BinanceFutures accounts")
        
        # Get existing bots to track account usage
        existing_bots = api.get_all_bots(executor)
        account_bot_counts = {}
        for bot in existing_bots:
            account_id = bot.account_id
            account_bot_counts[account_id] = account_bot_counts.get(account_id, 0) + 1
        
        # Sort accounts by bot count (ascending)
        available_accounts = sorted(
            binancefutures_accounts,
            key=lambda acc: account_bot_counts.get(acc.get('AID', ''), 0)
        )
        
        # Create bots
        created_bots = []
        failed_bots = []
        account_index = 0
        
        for i, rec in enumerate(recommendations, 1):
            try:
                print(f"🤖 Creating bot {i}/{len(recommendations)}: {rec['bot_name']}")
                
                # Select account
                if account_index < len(available_accounts):
                    account = available_accounts[account_index]
                    account_index += 1
                else:
                    # Reuse accounts if we have more bots than accounts
                    account = available_accounts[account_index % len(available_accounts)]
                    account_index += 1
                
                print(f"   Using account: {account.get('AID')} ({account.get('EC')})")
                
                # Create bot from lab backtest
                from pyHaasAPI.model import AddBotFromLabRequest
                request = AddBotFromLabRequest(
                    lab_id=rec['lab_id'],
                    backtest_id=rec['backtest_id'],
                    account_id=account.get('AID'),
                    bot_name=rec['bot_name'],
                    market=rec['market_tag'],
                    leverage=20
                )
                bot_details = api.add_bot_from_lab(executor, request)
                
                print(f"✅ Bot created: {bot_details.bot_id}")
                
                # Configure bot with standard settings
                try:
                    # Set leverage
                    api.set_leverage(
                        executor=executor,
                        account_id=account.get('AID'),
                        market=rec['market_tag'],
                        leverage=20.0
                    )
                    
                    # Set position mode to HEDGE
                    api.set_position_mode(
                        executor=executor,
                        account_id=account.get('AID'),
                        position_mode=1  # HEDGE
                    )
                    
                    # Set margin mode to CROSS
                    api.set_margin_mode(
                        executor=executor,
                        account_id=account.get('AID'),
                        margin_mode=0  # CROSS
                    )
                    
                    print(f"   ✅ Bot configured with standard settings")
                    
                except Exception as e:
                    print(f"   ⚠️ Bot created but configuration failed: {e}")
                
                # Activate if requested
                if activate:
                    try:
                        api.activate_bot(executor, bot_details.bot_id)
                        print(f"   ✅ Bot activated")
                    except Exception as e:
                        print(f"   ⚠️ Bot created but activation failed: {e}")
                
                created_bots.append({
                    'bot_id': bot_details.bot_id,
                    'bot_name': bot_details.bot_name,
                    'backtest_id': rec['backtest_id'],
                    'account_id': account.get('AID'),
                    'market_tag': rec['market_tag'],
                    'roe': rec['roe'],
                    'win_rate': rec['win_rate'],
                    'total_trades': rec['total_trades']
                })
                
            except Exception as e:
                print(f"❌ Failed to create bot from recommendation {i}: {e}")
                failed_bots.append({
                    'recommendation': rec,
                    'error': str(e)
                })
        
        # Summary
        print(f"\n📊 Bot Creation Summary")
        print(f"{'='*50}")
        print(f"Total recommendations: {len(recommendations)}")
        print(f"Successfully created: {len(created_bots)}")
        print(f"Failed: {len(failed_bots)}")
        
        if created_bots:
            print(f"\n✅ Successfully Created Bots:")
            for bot in created_bots:
                print(f"  {bot['bot_id']}: {bot['bot_name']}")
                print(f"    Account: {bot['account_id']}")
                print(f"    Market: {bot['market_tag']}")
                print(f"    ROE: {bot['roe']:.1f}%, WR: {bot['win_rate']:.1f}%")
        
        if failed_bots:
            print(f"\n❌ Failed Bot Creations:")
            for failure in failed_bots:
                print(f"  {failure['recommendation']['bot_name']}")
                print(f"    Error: {failure['error']}")
        
        # Save results
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_recommendations': len(recommendations),
            'successful_creations': len(created_bots),
            'failed_creations': len(failed_bots),
            'created_bots': created_bots,
            'failed_bots': failed_bots
        }
        
        results_file = f"bot_creation_results_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ Bot creation process failed: {e}")
        raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create bots from server recommendations using v1 API")
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
        print("🔍 DRY RUN MODE - No bots will be created")
        
        # Load and display recommendations
        with open(args.recommendations, 'r') as f:
            recommendations = json.load(f)
        
        print(f"📋 Would create {min(len(recommendations), args.max_bots)} bots:")
        for i, rec in enumerate(recommendations[:args.max_bots], 1):
            print(f"  {i}. {rec['bot_name']}")
            print(f"     Lab: {rec['lab_name']}")
            print(f"     Market: {rec['market_tag']}")
            print(f"     ROE: {rec['roe']:.1f}%, WR: {rec['win_rate']:.1f}%")
            print(f"     Trades: {rec['total_trades']}")
        
        return
    
    # Create bots
    create_bots_from_recommendations(
        recommendations_file=args.recommendations,
        max_bots=args.max_bots,
        activate=not args.no_activate
    )


if __name__ == "__main__":
    main()
