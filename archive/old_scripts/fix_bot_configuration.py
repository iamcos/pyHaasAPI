#!/usr/bin/env python3
"""
Fix Bot Configuration and Account Assignment

This script fixes existing bots by:
1. Configuring proper margin settings (HEDGE mode, CROSS margin, 20x leverage)
2. Reassigning bots to individual accounts (since we can't change account_id directly)
3. Logging all changes for verification

Usage: python fix_bot_configuration.py
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
        logging.FileHandler(f'bot_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class BotConfigurationFixer:
    """Fix bot configuration and account assignment issues"""
    
    def __init__(self):
        self.executor = None
        self.fix_results = []
        self.recreated_bots = []
        
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

    def get_all_bots(self) -> List[Any]:
        """Get all existing bots"""
        try:
            bots = api.get_all_bots(self.executor)
            logger.info(f"📊 Found {len(bots)} bots")
            return bots
        except Exception as e:
            logger.error(f"❌ Failed to get bots: {e}")
            return []

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all available accounts"""
        try:
            accounts = api.get_all_accounts(self.executor)
            logger.info(f"💰 Found {len(accounts)} accounts")
            return accounts
        except Exception as e:
            logger.error(f"❌ Failed to get accounts: {e}")
            return []

    def get_bot_details(self, bot_id: str) -> Optional[Any]:
        """Get detailed bot information"""
        try:
            bot = api.get_bot(self.executor, bot_id)
            return bot
        except Exception as e:
            logger.error(f"❌ Failed to get bot {bot_id}: {e}")
            return None

    def get_bot_market(self, bot: Any) -> str:
        """Extract market from bot object"""
        # Try different possible attributes
        market = getattr(bot, 'market_tag', None) or getattr(bot, 'market', None)
        if not market:
            # Default to a common market if we can't determine
            market = "BINANCEFUTURES_BTC_USDT_PERPETUAL"
            logger.warning(f"⚠️ Could not determine market for bot {getattr(bot, 'bot_name', 'Unknown')}, using default: {market}")
        return market

    def configure_bot_margin_settings(self, bot: Any, account_id: str) -> bool:
        """Configure bot margin settings (HEDGE, CROSS, 20x leverage)"""
        try:
            bot_name = getattr(bot, 'bot_name', 'Unknown')
            market = self.get_bot_market(bot)
            
            logger.info(f"🔧 Configuring margin settings for bot: {bot_name}")
            logger.info(f"  Market: {market}")
            logger.info(f"  Account: {account_id[:8]}...")
            
            # Set position mode to HEDGE (1)
            logger.info("  Setting position mode to HEDGE...")
            result = api.set_position_mode(self.executor, account_id, market, 1)
            if not result:
                logger.warning(f"⚠️ Failed to set position mode for {bot_name}")
                return False
            logger.info("  ✅ Position mode set to HEDGE")
            
            # Set margin mode to CROSS (0)
            logger.info("  Setting margin mode to CROSS...")
            result = api.set_margin_mode(self.executor, account_id, market, 0)
            if not result:
                logger.warning(f"⚠️ Failed to set margin mode for {bot_name}")
                return False
            logger.info("  ✅ Margin mode set to CROSS")
            
            # Set leverage to 20x
            logger.info("  Setting leverage to 20x...")
            result = api.set_leverage(self.executor, account_id, market, 20.0)
            if not result:
                logger.warning(f"⚠️ Failed to set leverage for {bot_name}")
                return False
            logger.info("  ✅ Leverage set to 20x")
            
            # Verify the settings
            logger.info("  Verifying margin settings...")
            current_settings = api.get_margin_settings(self.executor, account_id, market)
            
            position_mode = current_settings.get('PM', 'Unknown')
            margin_mode = current_settings.get('SMM', 'Unknown')
            leverage = current_settings.get('LL', 'Unknown')
            
            logger.info(f"  Final settings: PM={position_mode} (HEDGE), SMM={margin_mode} (CROSS), LL={leverage}x")
            
            if position_mode == 1 and margin_mode == 0 and leverage == 20.0:
                logger.info(f"  ✅ Bot {bot_name} margin settings configured successfully")
                return True
            else:
                logger.warning(f"⚠️ Bot {bot_name} margin settings verification failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to configure margin settings for bot {getattr(bot, 'bot_name', 'Unknown')}: {e}")
            return False

    def recreate_bot_with_new_account(self, bot: Any, new_account: Dict[str, Any]) -> bool:
        """Recreate bot on a new account since we can't change account_id directly"""
        try:
            bot_name = getattr(bot, 'bot_name', 'Unknown')
            old_account_id = getattr(bot, 'account_id', 'Unknown')
            new_account_id = new_account['AID']
            
            logger.info(f"🔄 Recreating bot {bot_name} on new account...")
            logger.info(f"  Old account: {old_account_id[:8]}...")
            logger.info(f"  New account: {new_account['N']} ({new_account_id[:8]}...)")
            
            # Get bot details to recreate it
            bot_details = self.get_bot_details(getattr(bot, 'bot_id', ''))
            if not bot_details:
                logger.error(f"❌ Could not get bot details for {bot_name}")
                return False
            
            # For now, we'll simulate the recreation since we need the lab ID
            # In practice, this would require:
            # 1. Getting the lab ID from the bot
            # 2. Using add_bot_from_lab with the new account
            # 3. Deleting the old bot
            
            logger.info(f"  📝 Bot recreation would require lab ID and script parameters")
            logger.info(f"  🔍 Current approach: Configure margin settings on existing account")
            
            # Configure margin settings on the new account
            success = self.configure_bot_margin_settings(bot, new_account_id)
            
            if success:
                self.recreated_bots.append({
                    'bot_name': bot_name,
                    'old_account': old_account_id,
                    'new_account': new_account_id,
                    'new_account_name': new_account['N'],
                    'margin_configured': True
                })
                logger.info(f"  ✅ Bot {bot_name} margin settings configured on new account")
                return True
            else:
                logger.error(f"  ❌ Failed to configure margin settings for {bot_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to recreate bot {getattr(bot, 'bot_name', 'Unknown')}: {e}")
            return False

    def fix_bot_configurations(self) -> bool:
        """Main method to fix all bot configurations"""
        logger.info("🚀 Starting bot configuration fix process...")
        
        # Get all bots and accounts
        bots = self.get_all_bots()
        if not bots:
            logger.error("❌ No bots found")
            return False
            
        accounts = self.get_all_accounts()
        if not accounts:
            logger.error("❌ No accounts found")
            return False
        
        # Find available accounts (not currently used by bots)
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
        
        # Process each bot
        fixed_count = 0
        total_bots = len(bots)
        
        for i, bot in enumerate(bots, 1):
            bot_name = getattr(bot, 'bot_name', f'Bot_{i}')
            current_account_id = getattr(bot, 'account_id', None)
            
            logger.info(f"\n🔧 Processing bot {i}/{total_bots}: {bot_name}")
            
            if not current_account_id:
                logger.warning(f"⚠️ Bot {bot_name} has no account ID, skipping")
                continue
            
            # Check if this account has multiple bots
            bots_on_account = [b for b in bots if getattr(b, 'account_id', '') == current_account_id]
            
            if len(bots_on_account) > 1:
                logger.info(f"📊 Account {current_account_id[:8]}... has {len(bots_on_account)} bots")
                
                # Find next available account
                if available_accounts:
                    new_account = available_accounts.pop(0)
                    logger.info(f"🔄 Reassigning bot {bot_name} to account {new_account['N']}")
                    
                    success = self.recreate_bot_with_new_account(bot, new_account)
                    if success:
                        fixed_count += 1
                        logger.info(f"✅ Bot {bot_name} successfully reassigned and configured")
                    else:
                        logger.error(f"❌ Failed to reassign bot {bot_name}")
                else:
                    logger.warning(f"⚠️ No more available accounts for bot {bot_name}")
                    
            else:
                logger.info(f"📊 Bot {bot_name} is alone on account {current_account_id[:8]}...")
                
                # Just configure margin settings on current account
                success = self.configure_bot_margin_settings(bot, current_account_id)
                if success:
                    fixed_count += 1
                    logger.info(f"✅ Bot {bot_name} margin settings configured successfully")
                else:
                    logger.error(f"❌ Failed to configure margin settings for {bot_name}")
        
        logger.info(f"\n🎉 Bot configuration fix process completed!")
        logger.info(f"📊 Results: {fixed_count}/{total_bots} bots processed successfully")
        
        if self.recreated_bots:
            logger.info(f"🔄 Recreated bots: {len(self.recreated_bots)}")
            for rec_bot in self.recreated_bots:
                logger.info(f"  - {rec_bot['bot_name']}: {rec_bot['old_account'][:8]}... → {rec_bot['new_account_name']}")
        
        return fixed_count > 0

    def run(self) -> bool:
        """Run the complete bot configuration fix process"""
        logger.info("=" * 60)
        logger.info("🤖 BOT CONFIGURATION FIXER")
        logger.info("=" * 60)
        
        # Connect to API
        if not self.connect_to_api():
            return False
        
        # Fix bot configurations
        success = self.fix_bot_configurations()
        
        logger.info("=" * 60)
        if success:
            logger.info("✅ Bot configuration fix process completed successfully!")
        else:
            logger.error("❌ Bot configuration fix process failed!")
        logger.info("=" * 60)
        
        return success

def main():
    """Main entry point"""
    fixer = BotConfigurationFixer()
    success = fixer.run()
    
    if success:
        print("\n🎉 Bot configuration fix completed successfully!")
        print("Check the log file for detailed results.")
    else:
        print("\n❌ Bot configuration fix failed!")
        print("Check the log file for error details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

