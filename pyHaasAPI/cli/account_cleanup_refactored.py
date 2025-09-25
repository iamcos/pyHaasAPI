#!/usr/bin/env python3
"""
Refactored Account Cleanup Tool for pyHaasAPI

This tool cleans up simulated account naming schemes by:
1. Finding all Binance Futures accounts with naming pattern "4**-10k"
2. Renaming them to proper sequential format: [Sim] 4AA-10k, [Sim] 4AB-10k, etc.
3. Preserving account order and not deleting any accounts

Refactored to use base classes.
"""

import argparse
import re
from typing import List, Dict, Tuple

from .base import BaseDirectAPICLI
from .common import add_common_arguments
from pyHaasAPI.api import get_all_accounts, rename_account
from pyHaasAPI.accounts import AccountNamingManager


class AccountCleanupToolRefactored(BaseDirectAPICLI):
    """Refactored tool for cleaning up simulated account naming schemes"""
    
    def __init__(self):
        super().__init__()
        self.naming_manager = AccountNamingManager()
        self.renamed_count = 0
        self.failed_count = 0
        
    def run(self, args) -> bool:
        """Main execution method"""
        try:
            # Connect to API
            if not self.connect():
                return False
            
            if args.dry_run:
                self.logger.info("🧪 DRY RUN MODE - No changes will be made")
            
            # Run cleanup
            success = self.cleanup_account_names(dry_run=args.dry_run)
            
            if success:
                self.logger.info("✅ Account cleanup completed successfully")
            else:
                self.logger.error("❌ Account cleanup failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in account cleanup: {e}")
            return False
    
    def cleanup_account_names(self, dry_run: bool = False) -> bool:
        """Main cleanup process"""
        try:
            self.logger.info("🧹 Starting Account Cleanup Process")
            self.logger.info("=" * 60)
            
            # Get all accounts
            all_accounts = get_all_accounts(self.executor)
            if not all_accounts:
                self.logger.error("❌ No accounts found")
                return False
            
            self.logger.info(f"📋 Found {len(all_accounts)} total accounts")
            
            # Find accounts to rename
            accounts_to_rename = self.find_accounts_to_rename(all_accounts)
            
            if not accounts_to_rename:
                self.logger.info("✅ No accounts need renaming")
                return True
            
            self.logger.info(f"🎯 Found {len(accounts_to_rename)} accounts to rename")
            
            # Show what will be renamed
            self.show_rename_plan(accounts_to_rename)
            
            if dry_run:
                self.logger.info("🧪 DRY RUN - No actual changes made")
                return True
            
            # Perform renaming
            success = self.rename_accounts(accounts_to_rename)
            
            # Show results
            self.show_results()
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in cleanup process: {e}")
            return False
    
    def find_accounts_to_rename(self, all_accounts: List) -> List[Tuple]:
        """Find accounts that match the pattern and need renaming"""
        accounts_to_rename = []
        
        # Pattern to match: "4**-10k" (where ** are any characters)
        pattern = r'^4.*-10k$'
        
        for account in all_accounts:
            account_name = getattr(account, 'name', '') or getattr(account, 'Name', '')
            account_id = getattr(account, 'id', '') or getattr(account, 'ID', '')
            
            if re.match(pattern, account_name):
                # Generate new name
                new_name = self.generate_new_name(len(accounts_to_rename))
                accounts_to_rename.append((account, account_name, new_name))
        
        return accounts_to_rename
    
    def generate_new_name(self, index: int) -> str:
        """Generate new sequential name"""
        # Generate sequential names: 4AA, 4AB, 4AC, etc.
        letter1 = chr(ord('A') + (index // 26))
        letter2 = chr(ord('A') + (index % 26))
        return f"[Sim] 4{letter1}{letter2}-10k"
    
    def show_rename_plan(self, accounts_to_rename: List[Tuple]):
        """Show the renaming plan"""
        self.logger.info("\n📋 RENAME PLAN:")
        self.logger.info("-" * 60)
        
        for i, (account, old_name, new_name) in enumerate(accounts_to_rename, 1):
            account_id = getattr(account, 'id', '') or getattr(account, 'ID', '')
            self.logger.info(f"{i:2d}. {old_name} → {new_name} (ID: {account_id})")
        
        self.logger.info("-" * 60)
    
    def rename_accounts(self, accounts_to_rename: List[Tuple]) -> bool:
        """Perform the actual renaming"""
        self.logger.info("\n🔄 Starting renaming process...")
        
        for i, (account, old_name, new_name) in enumerate(accounts_to_rename, 1):
            try:
                account_id = getattr(account, 'id', '') or getattr(account, 'ID', '')
                
                self.logger.info(f"🔄 Renaming {i}/{len(accounts_to_rename)}: {old_name} → {new_name}")
                
                # Perform rename
                success = rename_account(self.executor, account_id, new_name)
                
                if success:
                    self.logger.info(f"✅ Successfully renamed: {old_name} → {new_name}")
                    self.renamed_count += 1
                else:
                    self.logger.error(f"❌ Failed to rename: {old_name}")
                    self.failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Error renaming {old_name}: {e}")
                self.failed_count += 1
                continue
        
        return self.failed_count == 0
    
    def show_results(self):
        """Show final results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 ACCOUNT CLEANUP RESULTS")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Successfully renamed: {self.renamed_count}")
        self.logger.info(f"❌ Failed to rename: {self.failed_count}")
        self.logger.info(f"📊 Total processed: {self.renamed_count + self.failed_count}")
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Account cleanup tool for simulated accounts")
    
    # Add common arguments
    add_common_arguments(parser)
    
    args = parser.parse_args()
    
    # Create and run cleanup tool
    cleanup_tool = AccountCleanupToolRefactored()
    success = cleanup_tool.run(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
