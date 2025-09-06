#!/usr/bin/env python3
"""
Advanced Bot Reassignment with Recreation

This script can actually move bots to new accounts by:
1. Extracting bot configuration from existing bots
2. Creating new bots on new accounts using add_bot_from_lab
3. Deleting old bots
4. Configuring proper margin settings

Usage: python advanced_bot_reassignment.py
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'advanced_bot_reassignment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class AdvancedBotReassigner:
    """Advanced bot reassignment with recreation capability"""
    
    def __init__(self):
        self.executor = None
        self.reassignment_results = []
        self.lab_cache = {}
        
    def connect_to_api(self) -> bool:
        """Connect to HaasOnline API"""
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            logger.error("❌ API_EMAIL and API_PASSWORD must be set in .env file")
            return False

        logger.info("🔌 Connecting to HaasOnline API...")

        try:
            haas_api = api.RequestsExecutor(
                host=api_host,
                port=api_port,
                state=api.Guest()
            )
            self.executor = haas_api.authenticate(api_email, api_password)
            logger.info("✅ Connected to API successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to API: {e}")
            return False

    def get_all_labs(self) -> List[Dict[str, Any]]:
        """Get all labs for bot recreation"""
        try:
            labs = api.get_all_labs(self.executor)
            logger.info(f"🧪 Found {len(labs)} labs")
            
            # Cache labs by name for quick lookup
            for lab in labs:
                lab_name = lab.get('N', 'Unknown')
                self.lab_cache[lab_name] = lab
                
            return labs
        except Exception as e:
            logger.error(f"❌ Failed to get labs: {e}")
            return []

    def find_lab_for_bot(self, bot_name: str) -> Optional[Dict[str, Any]]:
        """Find the lab that was used to create a bot based on bot name"""
        try:
            # Try to extract lab name from bot name
            # Bot names often follow pattern: "LabName_ROI_PopGen"
            if '_' in bot_name:
                lab_name = bot_name.split('_')[0]
                if lab_name in self.lab_cache:
                    logger.info(f"🔍 Found lab '{lab_name}' for bot '{bot_name}'")
                    return self.lab_cache[lab_name]
            
            # If no pattern match, try to find by partial name
            for lab_name, lab in self.lab_cache.items():
                if lab_name.lower() in bot_name.lower() or bot_name.lower() in lab_name.lower():
                    logger.info(f"🔍 Found lab '{lab_name}' for bot '{bot_name}' (partial match)")
                    return lab
            
            # If still no match, try to find any lab with similar characteristics
            logger.warning(f"⚠️ Could not find exact lab match for bot '{bot_name}'")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding lab for bot '{bot_name}': {e}")
            return None

    def extract_bot_parameters(self, bot: Any) -> Dict[str, Any]:
        """Extract bot parameters for recreation"""
        try:
            bot_name = getattr(bot, 'bot_name', 'Unknown')
            
            # Try to get script parameters
            script_params = getattr(bot, 'script_parameters', {}) or {}
            
            # Extract key parameters
            params = {
                'bot_name': bot_name,
                'script_parameters': script_params,
                'trade_amount': getattr(bot, 'trade_amount', 100.0),
                'interval': getattr(bot, 'interval', 15),
                'chart_style': getattr(bot, 'chart_style', 300),
                'order_template': getattr(bot, 'order_template', 500),
            }
            
            logger.info(f"📋 Extracted parameters for bot '{bot_name}':")
            logger.info(f"  Trade Amount: {params['trade_amount']}")
            logger.info(f"  Interval: {params['interval']}")
            logger.info(f"  Chart Style: {params['chart_style']}")
            logger.info(f"  Order Template: {params['order_template']}")
            logger.info(f"  Script Parameters: {len(script_params)} items")
            
            return params
            
        except Exception as e:
            logger.error(f"❌ Failed to extract parameters for bot '{getattr(bot, 'bot_name', 'Unknown')}': {e}")
            return {}

    def recreate_bot_on_new_account(self, bot: Any, new_account: Dict[str, Any], lab: Dict[str, Any]) -> bool:
        """Actually recreate bot on a new account"""
        try:
            bot_name = getattr(bot, 'bot_name', 'Unknown')
            old_account_id = getattr(bot, 'account_id', 'Unknown')
            new_account_id = new_account['AID']
            lab_id = lab.get('LID', '')
            
            logger.info(f"🔄 Recreating bot '{bot_name}' on new account...")
            logger.info(f"  Lab: {lab.get('N', 'Unknown')} ({lab_id[:8]}...)")
            logger.info(f"  Old account: {old_account_id[:8]}...")
            logger.info(f"  New account: {new_account['N']} ({new_account_id[:8]}...)")
            
            # Extract bot parameters
            bot_params = self.extract_bot_parameters(bot)
            if not bot_params:
                logger.error(f"❌ Could not extract parameters for bot '{bot_name}'")
                return False
            
            # Create new bot from lab
            logger.info(f"  🆕 Creating new bot from lab...")
            
            try:
                # Use add_bot_from_lab to create the bot
                new_bot = api.add_bot_from_lab(
                    executor=self.executor,
                    lab_id=lab_id,
                    account_id=new_account_id,
                    bot_name=f"{bot_name}_NEW",
                    leverage=20,  # Set 20x leverage
                    market=bot_params.get('market', 'BINANCEFUTURES_BTC_USDT_PERPETUAL'),
                    trade_amount=bot_params['trade_amount'],
                    interval=bot_params['interval'],
                    chart_style=bot_params['chart_style'],
                    order_template=bot_params['order_template'],
                    script_parameters=bot_params['script_parameters']
                )
                
                if new_bot:
                    logger.info(f"  ✅ New bot created successfully: {getattr(new_bot, 'bot_name', 'Unknown')}")
                    
                    # Configure margin settings on the new account
                    logger.info(f"  🔧 Configuring margin settings...")
                    success = self.configure_margin_settings(new_account_id, bot_params.get('market', 'BINANCEFUTURES_BTC_USDT_PERPETUAL'))
                    
                    if success:
                        # Delete the old bot
                        logger.info(f"  🗑️ Deleting old bot...")
                        try:
                            delete_success = api.delete_bot(self.executor, getattr(bot, 'bot_id', ''))
                            if delete_success:
                                logger.info(f"  ✅ Old bot deleted successfully")
                            else:
                                logger.warning(f"  ⚠️ Failed to delete old bot (may need manual cleanup)")
                        except Exception as e:
                            logger.warning(f"  ⚠️ Error deleting old bot: {e}")
                        
                        # Record the reassignment
                        self.reassignment_results.append({
                            'bot_name': bot_name,
                            'old_account': old_account_id,
                            'new_account': new_account_id,
                            'new_account_name': new_account['N'],
                            'lab_name': lab.get('N', 'Unknown'),
                            'status': 'success'
                        })
                        
                        logger.info(f"  🎉 Bot '{bot_name}' successfully reassigned to account {new_account['N']}")
                        return True
                    else:
                        logger.error(f"  ❌ Failed to configure margin settings for new bot")
                        # Try to delete the failed new bot
                        try:
                            api.delete_bot(self.executor, getattr(new_bot, 'bot_id', ''))
                            logger.info(f"  🗑️ Cleaned up failed new bot")
                        except:
                            pass
                        return False
                else:
                    logger.error(f"  ❌ Failed to create new bot from lab")
                    return False
                    
            except Exception as e:
                logger.error(f"  ❌ Error creating bot from lab: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to recreate bot '{getattr(bot, 'bot_name', 'Unknown')}': {e}")
            return False

    def configure_margin_settings(self, account_id: str, market: str) -> bool:
        """Configure margin settings for an account/market"""
        try:
            logger.info(f"  🔧 Configuring margin settings for account {account_id[:8]}...")
            
            # Set position mode to HEDGE (1)
            result = api.set_position_mode(self.executor, account_id, market, 1)
            if not result:
                logger.warning(f"  ⚠️ Failed to set position mode")
                return False
            
            # Set margin mode to CROSS (0)
            result = api.set_margin_mode(self.executor, account_id, market, 0)
            if not result:
                logger.warning(f"  ⚠️ Failed to set margin mode")
                return False
            
            # Set leverage to 20x
            result = api.set_leverage(self.executor, account_id, market, 20.0)
            if not result:
                logger.warning(f"  ⚠️ Failed to set leverage")
                return False
            
            # Verify settings
            current_settings = api.get_margin_settings(self.executor, account_id, market)
            position_mode = current_settings.get('PM', 'Unknown')
            margin_mode = current_settings.get('SMM', 'Unknown')
            leverage = current_settings.get('LL', 'Unknown')
            
            if position_mode == 1 and margin_mode == 0 and leverage == 20.0:
                logger.info(f"  ✅ Margin settings configured: HEDGE, CROSS, 20x")
                return True
            else:
                logger.warning(f"  ⚠️ Margin settings verification failed: PM={position_mode}, SMM={margin_mode}, LL={leverage}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Error configuring margin settings: {e}")
            return False

    def reassign_bots_to_individual_accounts(self) -> bool:
        """Main method to reassign bots to individual accounts"""
        logger.info("🚀 Starting advanced bot reassignment process...")
        
        # Get all labs first
        if not self.get_all_labs():
            logger.error("❌ No labs found - cannot recreate bots")
            return False
        
        # Get all bots and accounts
        bots = api.get_all_bots(self.executor)
        if not bots:
            logger.error("❌ No bots found")
            return False
            
        accounts = api.get_all_accounts(self.executor)
        if not accounts:
            logger.error("❌ No accounts found")
            return False
        
        # Find available accounts
        used_accounts = set()
        for bot in bots:
            account_id = getattr(bot, 'account_id', None)
            if account_id:
                used_accounts.add(account_id)
        
        available_accounts = [acc for acc in accounts if acc['AID'] not in used_accounts]
        logger.info(f"📊 Account usage: {len(used_accounts)} used, {len(available_accounts)} available")
        
        if not available_accounts:
            logger.error("❌ No available accounts for bot reassignment")
            return False
        
        # Group bots by account
        bots_by_account = {}
        for bot in bots:
            account_id = getattr(bot, 'account_id', None)
            if account_id:
                if account_id not in bots_by_account:
                    bots_by_account[account_id] = []
                bots_by_account[account_id].append(bot)
        
        # Process accounts with multiple bots
        reassigned_count = 0
        total_bots = len(bots)
        
        for account_id, bots_on_account in bots_by_account.items():
            if len(bots_on_account) > 1:
                logger.info(f"\n📊 Account {account_id[:8]}... has {len(bots_on_account)} bots")
                
                # Reassign all but one bot to new accounts
                for i, bot in enumerate(bots_on_account[1:], 1):  # Skip first bot
                    if not available_accounts:
                        logger.warning(f"⚠️ No more available accounts for bot reassignment")
                        break
                    
                    new_account = available_accounts.pop(0)
                    logger.info(f"🔄 Reassigning bot {i}/{len(bots_on_account)-1} from account {account_id[:8]}...")
                    
                    # Find lab for this bot
                    lab = self.find_lab_for_bot(getattr(bot, 'bot_name', 'Unknown'))
                    if lab:
                        success = self.recreate_bot_on_new_account(bot, new_account, lab)
                        if success:
                            reassigned_count += 1
                        else:
                            logger.error(f"❌ Failed to reassign bot {getattr(bot, 'bot_name', 'Unknown')}")
                    else:
                        logger.warning(f"⚠️ Could not find lab for bot {getattr(bot, 'bot_name', 'Unknown')}, skipping")
            else:
                logger.info(f"📊 Account {account_id[:8]}... has 1 bot - no reassignment needed")
        
        logger.info(f"\n🎉 Bot reassignment process completed!")
        logger.info(f"📊 Results: {reassigned_count} bots reassigned successfully")
        
        if self.reassignment_results:
            logger.info(f"🔄 Reassignment details:")
            for result in self.reassignment_results:
                logger.info(f"  - {result['bot_name']}: {result['old_account'][:8]}... → {result['new_account_name']}")
        
        return reassigned_count > 0

    def run(self) -> bool:
        """Run the complete bot reassignment process"""
        logger.info("=" * 60)
        logger.info("🔄 ADVANCED BOT REASSIGNMENT")
        logger.info("=" * 60)
        
        # Connect to API
        if not self.connect_to_api():
            return False
        
        # Reassign bots
        success = self.reassign_bots_to_individual_accounts()
        
        logger.info("=" * 60)
        if success:
            logger.info("✅ Bot reassignment process completed successfully!")
        else:
            logger.error("❌ Bot reassignment process failed!")
        logger.info("=" * 60)
        
        return success

def main():
    """Main entry point"""
    reassigner = AdvancedBotReassigner()
    success = reassigner.run()
    
    if success:
        print("\n🎉 Bot reassignment completed successfully!")
        print("Check the log file for detailed results.")
    else:
        print("\n❌ Bot reassignment failed!")
        print("Check the log file for error details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

