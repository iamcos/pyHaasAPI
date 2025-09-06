#!/usr/bin/env python3
"""
Account Cleanup Tool for pyHaasAPI

This tool cleans up simulated account naming schemes by:
1. Finding all Binance Futures accounts with naming pattern "4**-10k"
2. Renaming them to proper sequential format: [Sim] 4AA-10k, [Sim] 4AB-10k, etc.
3. Preserving account order and not deleting any accounts
"""

import os
import sys
import re
import logging
from typing import List, Dict, Tuple
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI.api import RequestsExecutor, get_all_accounts, rename_account
from pyHaasAPI.accounts import AccountNamingManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccountCleanupTool:
    """Tool for cleaning up simulated account naming schemes"""
    
    def __init__(self):
        self.executor = None
        self.naming_manager = AccountNamingManager()
        self.renamed_count = 0
        self.failed_count = 0
        
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            logger.info("🔌 Connecting to HaasOnline API...")
            
            # Get connection parameters
            host = os.getenv('API_HOST', '127.0.0.1')
            port = int(os.getenv('API_PORT', 8090))
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                logger.error("❌ Missing API_EMAIL or API_PASSWORD in environment")
                return False
            
            # Create executor with proper initialization
            from pyHaasAPI.api import Guest
            haas_api = RequestsExecutor(
                host=host,
                port=port,
                state=Guest()
            )
            
            # Authenticate
            self.executor = haas_api.authenticate(email, password)
                
            logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_simulated_accounts(self) -> List[Dict]:
        """Get all simulated accounts with 4**-10k naming pattern"""
        try:
            logger.info("📋 Fetching all accounts...")
            accounts = get_all_accounts(self.executor)
            
            # First, let's see what accounts we have
            logger.info(f"📊 Total accounts found: {len(accounts)}")
            logger.info("📋 All accounts:")
            for i, account in enumerate(accounts[:5]):  # Show first 5
                logger.info(f"  {i+1:2d}. Raw account data: {account}")
            
            if len(accounts) > 5:
                logger.info(f"  ... and {len(accounts) - 5} more accounts")
            
            # Filter for Binance Futures accounts with 4**-10k pattern
            simulated_accounts = []
            pattern = re.compile(r'4[A-Z]+-10k')
            
            for account in accounts:
                account_name = account.get('N', '')  # 'N' is the name field
                exchange = account.get('EC', '')     # 'EC' is the exchange code field
                
                # Check if it's Binance Futures and matches the pattern
                if (exchange == 'BINANCEFUTURES' and pattern.match(account_name)):
                    
                    simulated_accounts.append({
                        'id': account.get('AID'),    # 'AID' is the account ID
                        'name': account_name,
                        'exchange': exchange,
                        'balance': account.get('V', 0)  # 'V' might be balance/volume
                    })
            
            # Sort by current name to preserve order
            simulated_accounts.sort(key=lambda x: x['name'])
            
            logger.info(f"📊 Found {len(simulated_accounts)} simulated accounts to rename")
            return simulated_accounts
            
        except Exception as e:
            logger.error(f"❌ Error fetching accounts: {e}")
            return []
    
    def generate_new_name(self, index: int) -> str:
        """Generate new account name with proper sequence"""
        # Generate sequence letters (AA, AB, AC, etc.)
        sequence_letters = self.naming_manager._number_to_letters(index + 1)
        return f"[Sim] 4{sequence_letters}-10k"
    
    def rename_accounts(self, accounts: List[Dict]) -> bool:
        """Rename accounts to proper sequential format"""
        logger.info("🔄 Starting account renaming process...")
        
        for i, account in enumerate(accounts):
            current_name = account['name']
            new_name = self.generate_new_name(i)
            account_id = account['id']
            
            # Skip if name is already correct
            if current_name == new_name:
                logger.info(f"⏭️  Skipping {current_name} (already correct)")
                continue
            
            try:
                logger.info(f"🔄 Renaming: {current_name} → {new_name}")
                
                # Rename the account
                success = rename_account(self.executor, account_id, new_name)
                
                if success:
                    logger.info(f"✅ Successfully renamed: {new_name}")
                    self.renamed_count += 1
                else:
                    logger.error(f"❌ Failed to rename: {current_name}")
                    self.failed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error renaming {current_name}: {e}")
                self.failed_count += 1
        
        return True
    
    def run_cleanup(self) -> bool:
        """Run the complete cleanup process"""
        logger.info("🚀 Starting Account Cleanup Tool")
        logger.info("=" * 50)
        
        # Connect to API
        if not self.connect():
            return False
        
        # Get simulated accounts
        accounts = self.get_simulated_accounts()
        if not accounts:
            logger.info("ℹ️  No simulated accounts found to rename")
            return True
        
        # Display accounts to be renamed
        logger.info("📋 Accounts to be renamed:")
        for i, account in enumerate(accounts):
            new_name = self.generate_new_name(i)
            logger.info(f"  {i+1:2d}. {account['name']} → {new_name}")
        
        # Confirm before proceeding
        print("\n" + "=" * 50)
        response = input("🤔 Proceed with renaming? (y/N): ").strip().lower()
        if response != 'y':
            logger.info("❌ Cleanup cancelled by user")
            return False
        
        # Rename accounts
        self.rename_accounts(accounts)
        
        # Summary
        logger.info("=" * 50)
        logger.info("📊 CLEANUP SUMMARY:")
        logger.info(f"  ✅ Successfully renamed: {self.renamed_count}")
        logger.info(f"  ❌ Failed to rename: {self.failed_count}")
        logger.info(f"  📋 Total processed: {len(accounts)}")
        
        if self.failed_count == 0:
            logger.info("🎉 All accounts renamed successfully!")
        else:
            logger.warning(f"⚠️  {self.failed_count} accounts failed to rename")
        
        return True


def main():
    """Main entry point"""
    try:
        tool = AccountCleanupTool()
        success = tool.run_cleanup()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n❌ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
