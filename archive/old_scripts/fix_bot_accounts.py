#!/usr/bin/env python3
"""
Fix Bot Account Assignment

This script fixes the issue where all bots are using a single account.
It will:
1. Get all existing bots and their current accounts
2. Find available accounts
3. Reassign bots to individual accounts using edit_bot_parameter
4. Log all changes for verification

Usage: python fix_bot_accounts.py
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
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'bot_account_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Reduce verbosity
logging.getLogger('pyHaasAPI').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

class BotAccountFixer:
    """Fix bot account assignment issues"""
    
    def __init__(self, executor: RequestsExecutor):
        self.executor = executor
        self.bots = []
        self.accounts = []
        self.fix_results = []
        self.output_dir = f"bot_account_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _connect_api(self):
        """Connect to HaasOnline API"""
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            logger.error("❌ API_EMAIL and API_PASSWORD must be set in .env file")
            return False

        logger.info("Connecting to HaasOnline API...")

        try:
            haas_api = api.RequestsExecutor(
                host=api_host,
                port=api_port,
                state=api.Guest()
            )
            self.executor = haas_api.authenticate(api_email, api_password)
            logger.info("✅ Connected to API")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to API: {e}")
            return False

    def get_current_bot_status(self):
        """Get current status of all bots and their accounts"""
        try:
            logger.info("🔍 Getting current bot status...")
            
            # Get all bots
            self.bots = api.get_all_bots(self.executor)
            logger.info(f"Found {len(self.bots)} bots")
            
            # Get all accounts
            self.accounts = api.get_all_accounts(self.executor)
            logger.info(f"Found {len(self.accounts)} accounts")
            
            # Analyze current assignment
            account_usage = {}
            bots_without_accounts = []
            
            for bot in self.bots:
                bot_id = getattr(bot, 'bot_id', 'Unknown')
                bot_name = getattr(bot, 'bot_name', 'Unknown')
                current_account = getattr(bot, 'account_id', None)
                
                if current_account:
                    if current_account not in account_usage:
                        account_usage[current_account] = []
                    account_usage[current_account].append({
                        'bot_id': bot_id,
                        'bot_name': bot_name
                    })
                else:
                    bots_without_accounts.append({
                        'bot_id': bot_id,
                        'bot_name': bot_name
                    })
            
            # Log current status
            logger.info("\n📊 CURRENT BOT ACCOUNT ASSIGNMENT:")
            logger.info("=" * 50)
            
            for account_id, bots_list in account_usage.items():
                account_name = next((acc['N'] for acc in self.accounts if acc['AID'] == account_id), 'Unknown')
                logger.info(f"Account {account_name} ({account_id[:8]}) has {len(bots_list)} bots:")
                for bot in bots_list:
                    logger.info(f"  • {bot['bot_name']} (ID: {bot['bot_id'][:8]})")
            
            if bots_without_accounts:
                logger.info(f"\n⚠️ {len(bots_without_accounts)} bots without accounts:")
                for bot in bots_without_accounts:
                    logger.info(f"  • {bot['bot_name']} (ID: {bot['bot_id'][:8]})")
            
            # Find the problematic account (the one with multiple bots)
            problematic_account = None
            for account_id, bots_list in account_usage.items():
                if len(bots_list) > 1:
                    problematic_account = account_id
                    break
            
            if problematic_account:
                account_name = next((acc['N'] for acc in self.accounts if acc['AID'] == problematic_account), 'Unknown')
                logger.warning(f"\n🚨 PROBLEM DETECTED: Account {account_name} ({problematic_account[:8]}) has {len(account_usage[problematic_account])} bots!")
                logger.warning("This needs to be fixed by redistributing bots to separate accounts.")
            
            return account_usage, problematic_account
            
        except Exception as e:
            logger.error(f"Error getting current bot status: {e}")
            return {}, None

    def find_available_accounts(self):
        """Find available accounts for bot reassignment"""
        try:
            logger.info("\n🔍 Finding available accounts...")
            
            # Get current bot account assignments
            current_assignments = set()
            for bot in self.bots:
                account_id = getattr(bot, 'account_id', None)
                if account_id:
                    current_assignments.add(account_id)
            
            # Find accounts not currently used by bots
            available_accounts = []
            for account in self.accounts:
                if account['AID'] not in current_assignments:
                    available_accounts.append(account)
            
            logger.info(f"Found {len(available_accounts)} available accounts")
            
            # Log available accounts
            for i, account in enumerate(available_accounts):
                logger.info(f"  {i+1}. {account['N']} (ID: {account['AID'][:8]}) - Exchange: {account['EC']}")
            
            return available_accounts
            
        except Exception as e:
            logger.error(f"Error finding available accounts: {e}")
            return []

    def reassign_bot_accounts(self, account_usage: Dict, problematic_account: str):
        """Reassign bots to individual accounts"""
        try:
            if not problematic_account:
                logger.info("✅ No problematic account assignments found. All bots are properly distributed.")
                return True
            
            logger.info(f"\n🔧 Reassigning bots from problematic account {problematic_account[:8]}...")
            
            # Get available accounts
            available_accounts = self.find_available_accounts()
            if not available_accounts:
                logger.error("❌ No available accounts found for reassignment")
                return False
            
            # Get bots that need to be reassigned
            bots_to_reassign = account_usage[problematic_account]
            logger.info(f"Need to reassign {len(bots_to_reassign)} bots")
            
            if len(available_accounts) < len(bots_to_reassign):
                logger.warning(f"⚠️ Only {len(available_accounts)} available accounts for {len(bots_to_reassign)} bots")
                logger.warning("Some bots will remain on the problematic account")
            
            # Reassign bots
            reassigned_count = 0
            for i, bot_info in enumerate(bots_to_reassign):
                if i >= len(available_accounts):
                    logger.warning(f"⚠️ No more available accounts. Bot {bot_info['bot_name']} will remain on current account.")
                    break
                
                new_account = available_accounts[i]
                bot_id = bot_info['bot_id']
                bot_name = bot_info['bot_name']
                
                logger.info(f"Reassigning bot {bot_name} (ID: {bot_id[:8]}) to account {new_account['N']} ({new_account['AID'][:8]})...")
                
                try:
                    # Actually change the bot's account using the new API function
                    logger.info(f"  🔧 Changing account from {problematic_account[:8]} to {new_account['AID'][:8]}...")
                    
                    # Use the new change_bot_account function
                    success = api.change_bot_account(self.executor, bot_id, new_account['AID'])
                    
                    if success:
                        reassigned_count += 1
                        logger.info(f"  ✅ Bot {bot_name} successfully reassigned to account {new_account['N']}")
                        
                        # Record the change
                        self.fix_results.append({
                            'bot_id': bot_id,
                            'bot_name': bot_name,
                            'old_account': problematic_account,
                            'new_account': new_account['AID'],
                            'new_account_name': new_account['N'],
                            'status': 'reassigned',
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        logger.error(f"  ❌ Failed to update bot {bot_name} account")
                        self.fix_results.append({
                            'bot_id': bot_id,
                            'bot_name': bot_name,
                            'old_account': problematic_account,
                            'new_account': None,
                            'new_account_name': None,
                            'status': 'failed',
                            'error': 'Account update failed',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # Small delay to avoid overwhelming the API
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to reassign bot {bot_name}: {e}")
                    self.fix_results.append({
                        'bot_id': bot_id,
                        'bot_name': bot_name,
                        'old_account': problematic_account,
                        'new_account': None,
                        'new_account_name': None,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            logger.info(f"✅ Successfully reassigned {reassigned_count} bots")
            return reassigned_count > 0
            
        except Exception as e:
            logger.error(f"Error reassigning bot accounts: {e}")
            return False

    def verify_fixes(self):
        """Verify that the account assignment fixes worked"""
        try:
            logger.info("\n🔍 Verifying account assignment fixes...")
            
            # Get updated bot status
            updated_bots = api.get_all_bots(self.executor)
            
            # Analyze new assignment
            new_account_usage = {}
            for bot in updated_bots:
                bot_id = getattr(bot, 'bot_id', 'Unknown')
                bot_name = getattr(bot, 'bot_name', 'Unknown')
                current_account = getattr(bot, 'account_id', None)
                
                if current_account:
                    if current_account not in new_account_usage:
                        new_account_usage[current_account] = []
                    new_account_usage[current_account].append({
                        'bot_id': bot_id,
                        'bot_name': bot_name
                    })
            
            # Check for any remaining problematic assignments
            problematic_accounts = []
            for account_id, bots_list in new_account_usage.items():
                if len(bots_list) > 1:
                    problematic_accounts.append({
                        'account_id': account_id,
                        'bot_count': len(bots_list),
                        'bots': bots_list
                    })
            
            if problematic_accounts:
                logger.warning(f"⚠️ Found {len(problematic_accounts)} accounts still with multiple bots:")
                for problem in problematic_accounts:
                    account_name = next((acc['N'] for acc in self.accounts if acc['problematic_account_id'] == problem['account_id']), 'Unknown')
                    logger.warning(f"  • Account {account_name} ({problem['account_id'][:8]}) has {problem['bot_count']} bots")
                return False
            else:
                logger.info("✅ All bots are now properly distributed across individual accounts!")
                return True
                
        except Exception as e:
            logger.error(f"Error verifying fixes: {e}")
            return False

    def save_results(self):
        """Save fix results to files"""
        try:
            logger.info("💾 Saving fix results...")
            
            # Save fix results
            results_file = os.path.join(self.output_dir, "bot_account_fix_results.csv")
            with open(results_file, 'w', newline='', encoding='utf-8') as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(['Bot ID', 'Bot Name', 'Old Account', 'New Account', 'New Account Name', 'Status', 'Error', 'Timestamp'])
                for result in self.fix_results:
                    writer.writerow([
                        result['bot_id'][:8],
                        result['bot_name'],
                        result['old_account'][:8] if result['old_account'] else 'None',
                        result['new_account'][:8] if result['new_account'] else 'None',
                        result.get('new_account_name', 'Unknown'),
                        result['status'],
                        result.get('error', ''),
                        result['timestamp']
                    ])
            
            # Save summary report
            summary_file = os.path.join(self.output_dir, "fix_summary.txt")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("BOT ACCOUNT ASSIGNMENT FIX SUMMARY\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Bots Processed: {len(self.bots)}\n")
                f.write(f"Total Accounts Available: {len(self.accounts)}\n")
                f.write(f"Bots Reassigned: {len([r for r in self.fix_results if r['status'] == 'reassigned'])}\n")
                f.write(f"Bots Failed: {len([r for r in self.fix_results if r['status'] == 'failed'])}\n\n")
                
                f.write("REASSIGNMENT RESULTS:\n")
                f.write("-" * 20 + "\n")
                for result in self.fix_results:
                    f.write(f"Bot: {result['bot_name']} (ID: {result['bot_id'][:8]})\n")
                    f.write(f"  Old Account: {result['old_account'][:8] if result['old_account'] else 'None'}\n")
                    f.write(f"  New Account: {result['new_account'][:8] if result['new_account'] else 'None'}\n")
                    f.write(f"  Status: {result['status']}\n")
                    if result.get('error'):
                        f.write(f"  Error: {result['error']}\n")
                    f.write("\n")
            
            logger.info(f"Results saved to: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting Bot Account Assignment Fix")
        logger.info("=" * 50)
        
        try:
            # Step 1: Get current status
            account_usage, problematic_account = self.get_current_bot_status()
            
            if not problematic_account:
                logger.info("✅ No account assignment issues found!")
                return
            
            # Step 2: Reassign bots
            success = self.reassign_bot_accounts(account_usage, problematic_account)
            
            if success:
                # Step 3: Verify fixes
                verification_success = self.verify_fixes()
                
                if verification_success:
                    logger.info("🎉 Bot account assignment fix completed successfully!")
                else:
                    logger.warning("⚠️ Fix completed but verification failed. Some issues may remain.")
            else:
                logger.error("❌ Bot account reassignment failed")
            
            # Step 4: Save results
            self.save_results()
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            self.save_results()  # Save what we have

if __name__ == "__main__":
    executor = None
    fixer = BotAccountFixer(executor)
    
    if not fixer._connect_api():
        sys.exit(1)
    
    fixer.run()
