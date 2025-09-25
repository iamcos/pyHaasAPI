#!/usr/bin/env python3
"""
Create bots directly from our cached analysis results
Uses the bot recommendations we generated earlier
"""

import json
import os
from pyHaasAPI import api
from dotenv import load_dotenv

def create_bots_from_recommendations():
    """Create bots using our analysis recommendations"""
    
    # Load our bot recommendations
    try:
        with open('current_server_bot_recommendations.json', 'r') as f:
            recommendations = json.load(f)
    except FileNotFoundError:
        print("❌ No bot recommendations found. Run analyze_current_server_labs.py first.")
        return
    
    print(f"🤖 Creating bots from {len(recommendations)} recommendations...")
    
    # Connect to API
    try:
        load_dotenv()
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        print("✅ Connected to HaasOnline API")
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return
    
    # Get available accounts
    try:
        accounts = api.get_all_accounts(executor)
        available_accounts = [acc for acc in accounts if 'AID' in acc]
        print(f"📋 Found {len(available_accounts)} available accounts")
    except Exception as e:
        print(f"❌ Failed to get accounts: {e}")
        return
    
    created_bots = []
    failed_bots = []
    
    # Create bots from recommendations
    for i, rec in enumerate(recommendations[:10]):  # Limit to top 10
        try:
            print(f"\n🔧 Creating bot {i+1}/10: {rec['bot_name'][:50]}...")
            
            # Get account for this bot
            if i < len(available_accounts):
                account_id = available_accounts[i]['AID']
            else:
                account_id = available_accounts[0]['AID']  # Use first account if we run out
            
            # Create bot from backtest
            from pyHaasAPI.model import AddBotFromLabRequest
            
            request = AddBotFromLabRequest(
                lab_id=rec['lab_id'],
                backtest_id=rec['backtest_id'],
                bot_name=rec['bot_name'],
                account_id=account_id,
                market=rec['market_tag'],
                leverage=20  # Standard leverage
            )
            
            try:
                bot_result = api.add_bot_from_lab(executor, request)
                
                if bot_result and hasattr(bot_result, 'id'):
                    bot_id = bot_result.id
                    print(f"  ✅ Bot created: {bot_id}")
                    
                    # Activate the bot
                    try:
                        api.activate_bot(executor, bot_id)
                        print(f"  🚀 Bot activated: {bot_id}")
                        created_bots.append({
                            'bot_id': bot_id,
                            'bot_name': rec['bot_name'],
                            'lab_id': rec['lab_id'],
                            'account_id': account_id,
                            'roi': rec['roi'],
                            'win_rate': rec['win_rate']
                        })
                    except Exception as e:
                        print(f"  ⚠️ Bot created but activation failed: {e}")
                        created_bots.append({
                            'bot_id': bot_id,
                            'bot_name': rec['bot_name'],
                            'lab_id': rec['lab_id'],
                            'account_id': account_id,
                            'roi': rec['roi'],
                            'win_rate': rec['win_rate'],
                            'activation_error': str(e)
                        })
                else:
                    print(f"  ❌ Failed to create bot - no result returned")
                    failed_bots.append(rec)
            except Exception as e:
                print(f"  ❌ API Error: {e}")
                failed_bots.append(rec)
                
        except Exception as e:
            print(f"  ❌ Error creating bot: {e}")
            failed_bots.append(rec)
    
    # Summary
    print(f"\n📊 BOT CREATION SUMMARY")
    print(f"=" * 50)
    print(f"✅ Successfully created: {len(created_bots)}")
    print(f"❌ Failed: {len(failed_bots)}")
    
    if created_bots:
        print(f"\n🤖 Created Bots:")
        for bot in created_bots:
            print(f"  - {bot['bot_name'][:40]}... (ROI: {bot['roi']:.1f}%, WR: {bot['win_rate']:.1f}%)")
    
    if failed_bots:
        print(f"\n❌ Failed Bots:")
        for bot in failed_bots:
            print(f"  - {bot['bot_name'][:40]}...")
    
    # Save results
    results = {
        'created_bots': created_bots,
        'failed_bots': failed_bots,
        'total_created': len(created_bots),
        'total_failed': len(failed_bots)
    }
    
    with open('bot_creation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to 'bot_creation_results.json'")

if __name__ == "__main__":
    create_bots_from_recommendations()
