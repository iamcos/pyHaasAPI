#!/usr/bin/env python3
"""
Unified Bot Management CLI for pyHaasAPI

This tool provides a unified interface for all bot management operations:
- Mass bot creation from labs
- Fix bot trade amounts
- Account cleanup and management
- Bot activation and deactivation

Combines the best functionality from multiple bot management tools.
"""

import argparse
from typing import List, Dict, Any, Optional

from .base import BaseBotCLI
from .common import add_common_arguments, add_trade_amount_arguments, add_bot_selection_arguments, get_all_accounts, get_all_bots
from .working_bot_creator import WorkingBotCreator


class UnifiedBotManagementCLI(BaseBotCLI):
    """Unified bot management CLI combining all bot management functionality"""
    
    def __init__(self):
        super().__init__()
        self.working_bot_creator = None
        
    def run(self, args) -> bool:
        """Main execution method"""
        try:
            # Connect to API
            if not self.connect():
                return False
            
            # Initialize working bot creator
            self.working_bot_creator = WorkingBotCreator(self.analyzer, self.cache)
            
            # Route to appropriate subcommand
            if args.command == 'create':
                return self.run_mass_creation(args)
            elif args.command == 'fix-amounts':
                return self.run_fix_trade_amounts(args)
            elif args.command == 'cleanup-accounts':
                return self.run_account_cleanup(args)
            elif args.command == 'activate':
                return self.run_bot_activation(args)
            elif args.command == 'deactivate':
                return self.run_bot_deactivation(args)
            else:
                self.logger.error(f"❌ Unknown command: {args.command}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error in unified bot management: {e}")
            return False
    
    def run_mass_creation(self, args) -> bool:
        """Run mass bot creation"""
        try:
            self.logger.info("🚀 Starting Mass Bot Creation")
            self.logger.info("=" * 60)
            
            # Get all accounts for bot assignment
            self.accounts = get_all_accounts(self.analyzer.executor)
            if not self.accounts:
                self.logger.error("❌ No accounts found - cannot create bots")
                return False
            
            self.logger.info(f"📋 Found {len(self.accounts)} accounts for bot assignment")
            
            # Get all complete labs
            all_labs = self.analyzer.get_complete_labs()
            if not all_labs:
                self.logger.error("❌ No complete labs found")
                return False
            
            # Filter labs based on criteria
            filtered_labs = self.filter_labs(all_labs, args.lab_ids, args.exclude_lab_ids)
            
            if not filtered_labs:
                self.logger.warning("⚠️ No labs match the specified criteria")
                return False
            
            # Extract lab IDs for processing
            lab_ids = []
            for lab in filtered_labs:
                lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
                if lab_id:
                    lab_ids.append(lab_id)
            
            if not lab_ids:
                self.logger.error("❌ No valid lab IDs found")
                return False
            
            # Run mass bot creation
            result = self.working_bot_creator.run_mass_creation(
                lab_ids=lab_ids,
                exclude_lab_ids=args.exclude_lab_ids,
                top_count=args.top_count,
                min_backtests=args.min_backtests,
                min_winrate=args.min_winrate / 100.0,  # Convert percentage to decimal
                target_usdt_amount=args.target_amount,
                activate=args.activate,
                dry_run=args.dry_run
            )
            
            # Show final results
            self.show_mass_creation_results(result)
            
            return result.total_bots_created > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error in mass bot creation: {e}")
            return False
    
    def run_fix_trade_amounts(self, args) -> bool:
        """Run bot trade amount fixing"""
        try:
            self.logger.info("🔧 Starting Bot Trade Amount Fixing")
            self.logger.info("=" * 60)
            
            # Get all bots
            all_bots = get_all_bots(self.analyzer.executor)
            if not all_bots:
                self.logger.error("❌ No bots found")
                return False
            
            self.logger.info(f"📋 Found {len(all_bots)} total bots")
            
            # Filter bots based on criteria
            filtered_bots = self.filter_bots(all_bots, args.bot_ids, args.exclude_bot_ids)
            
            if not filtered_bots:
                self.logger.warning("⚠️ No bots match the specified criteria")
                return False
            
            self.logger.info(f"🎯 Processing {len(filtered_bots)} bots")
            
            if args.dry_run:
                self.logger.info("🧪 DRY RUN MODE - No changes will be made")
            
            # Fix bot trade amounts
            success = self.fix_all_bot_trade_amounts(filtered_bots, args)
            
            # Show results
            self.show_fix_results()
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in bot trade amount fixing: {e}")
            return False
    
    def run_account_cleanup(self, args) -> bool:
        """Run account cleanup"""
        try:
            self.logger.info("🧹 Starting Account Cleanup")
            self.logger.info("=" * 60)
            
            # Get all accounts
            all_accounts = get_all_accounts(self.analyzer.executor)
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
            
            if args.dry_run:
                self.logger.info("🧪 DRY RUN - No actual changes made")
                return True
            
            # Perform renaming
            success = self.rename_accounts(accounts_to_rename)
            
            # Show results
            self.show_cleanup_results()
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in account cleanup: {e}")
            return False
    
    def run_bot_activation(self, args) -> bool:
        """Run bot activation"""
        try:
            self.logger.info("🚀 Starting Bot Activation")
            self.logger.info("=" * 60)
            
            # Get all bots
            all_bots = get_all_bots(self.analyzer.executor)
            if not all_bots:
                self.logger.error("❌ No bots found")
                return False
            
            # Filter bots based on criteria
            filtered_bots = self.filter_bots(all_bots, args.bot_ids, args.exclude_bot_ids)
            
            if not filtered_bots:
                self.logger.warning("⚠️ No bots match the specified criteria")
                return False
            
            self.logger.info(f"🎯 Activating {len(filtered_bots)} bots")
            
            if args.dry_run:
                self.logger.info("🧪 DRY RUN MODE - No changes will be made")
            
            # Activate bots
            success = self.activate_bots(filtered_bots, args.dry_run)
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in bot activation: {e}")
            return False
    
    def run_bot_deactivation(self, args) -> bool:
        """Run bot deactivation"""
        try:
            self.logger.info("🛑 Starting Bot Deactivation")
            self.logger.info("=" * 60)
            
            # Get all bots
            all_bots = get_all_bots(self.analyzer.executor)
            if not all_bots:
                self.logger.error("❌ No bots found")
                return False
            
            # Filter bots based on criteria
            filtered_bots = self.filter_bots(all_bots, args.bot_ids, args.exclude_bot_ids)
            
            if not filtered_bots:
                self.logger.warning("⚠️ No bots match the specified criteria")
                return False
            
            self.logger.info(f"🎯 Deactivating {len(filtered_bots)} bots")
            
            if args.dry_run:
                self.logger.info("🧪 DRY RUN MODE - No changes will be made")
            
            # Deactivate bots
            success = self.deactivate_bots(filtered_bots, args.dry_run)
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in bot deactivation: {e}")
            return False
    
    def show_mass_creation_results(self, result):
        """Show mass bot creation results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 MASS BOT CREATION COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Labs processed: {result.total_labs_processed}")
        self.logger.info(f"✅ Successful labs: {len(result.successful_labs)}")
        self.logger.info(f"❌ Failed labs: {len(result.failed_labs)}")
        self.logger.info(f"🤖 Total bots created: {result.total_bots_created}")
        self.logger.info(f"🚀 Total bots activated: {result.total_bots_activated}")
        self.logger.info("=" * 60)
    
    def fix_all_bot_trade_amounts(self, bots, args) -> bool:
        """Fix trade amounts for all specified bots"""
        from .fix_bot_trade_amounts_refactored import BotTradeAmountFixerRefactored
        
        fixer = BotTradeAmountFixerRefactored()
        fixer.executor = self.analyzer.executor
        fixer.price_api = fixer.price_api  # Initialize price API
        
        return fixer.fix_all_bot_trade_amounts(bots, args)
    
    def show_fix_results(self):
        """Show fix results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 BOT TRADE AMOUNT FIXING COMPLETE")
        self.logger.info("=" * 60)
        # Results will be shown by the fixer
        self.logger.info("=" * 60)
    
    def find_accounts_to_rename(self, all_accounts):
        """Find accounts that need renaming"""
        import re
        
        accounts_to_rename = []
        pattern = r'^4.*-10k$'
        
        for account in all_accounts:
            account_name = getattr(account, 'name', '') or getattr(account, 'Name', '')
            account_id = getattr(account, 'id', '') or getattr(account, 'ID', '')
            
            if re.match(pattern, account_name):
                new_name = self.generate_new_name(len(accounts_to_rename))
                accounts_to_rename.append((account, account_name, new_name))
        
        return accounts_to_rename
    
    def generate_new_name(self, index: int) -> str:
        """Generate new sequential name"""
        letter1 = chr(ord('A') + (index // 26))
        letter2 = chr(ord('A') + (index % 26))
        return f"[Sim] 4{letter1}{letter2}-10k"
    
    def show_rename_plan(self, accounts_to_rename):
        """Show the renaming plan"""
        self.logger.info("\n📋 RENAME PLAN:")
        self.logger.info("-" * 60)
        
        for i, (account, old_name, new_name) in enumerate(accounts_to_rename, 1):
            account_id = getattr(account, 'id', '') or getattr(account, 'ID', '')
            self.logger.info(f"{i:2d}. {old_name} → {new_name} (ID: {account_id})")
        
        self.logger.info("-" * 60)
    
    def rename_accounts(self, accounts_to_rename) -> bool:
        """Perform the actual renaming"""
        from pyHaasAPI.api import rename_account
        
        self.logger.info("\n🔄 Starting renaming process...")
        
        renamed_count = 0
        failed_count = 0
        
        for i, (account, old_name, new_name) in enumerate(accounts_to_rename, 1):
            try:
                account_id = getattr(account, 'id', '') or getattr(account, 'ID', '')
                
                self.logger.info(f"🔄 Renaming {i}/{len(accounts_to_rename)}: {old_name} → {new_name}")
                
                success = rename_account(self.analyzer.executor, account_id, new_name)
                
                if success:
                    self.logger.info(f"✅ Successfully renamed: {old_name} → {new_name}")
                    renamed_count += 1
                else:
                    self.logger.error(f"❌ Failed to rename: {old_name}")
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Error renaming {old_name}: {e}")
                failed_count += 1
                continue
        
        self.renamed_count = renamed_count
        self.failed_count = failed_count
        
        return failed_count == 0
    
    def show_cleanup_results(self):
        """Show cleanup results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 ACCOUNT CLEANUP COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Successfully renamed: {getattr(self, 'renamed_count', 0)}")
        self.logger.info(f"❌ Failed to rename: {getattr(self, 'failed_count', 0)}")
        self.logger.info("=" * 60)
    
    def activate_bots(self, bots, dry_run: bool) -> bool:
        """Activate bots"""
        from pyHaasAPI.api import activate_bot
        
        activated_count = 0
        failed_count = 0
        
        for i, bot in enumerate(bots, 1):
            try:
                bot_id = getattr(bot, 'bot_id', None) or getattr(bot, 'ID', '')
                bot_name = getattr(bot, 'name', None) or getattr(bot, 'Name', '') or f"Bot {bot_id[:8]}"
                
                self.logger.info(f"🚀 Activating bot {i}/{len(bots)}: {bot_name}")
                
                if dry_run:
                    self.logger.info(f"   Would activate: {bot_name}")
                    activated_count += 1
                else:
                    success = activate_bot(self.analyzer.executor, bot_id)
                    
                    if success:
                        self.logger.info(f"✅ Successfully activated: {bot_name}")
                        activated_count += 1
                    else:
                        self.logger.error(f"❌ Failed to activate: {bot_name}")
                        failed_count += 1
                        
            except Exception as e:
                self.logger.error(f"❌ Error activating bot {bot_name}: {e}")
                failed_count += 1
                continue
        
        self.logger.info(f"\n🎉 Activation complete: {activated_count} activated, {failed_count} failed")
        return failed_count == 0
    
    def deactivate_bots(self, bots, dry_run: bool) -> bool:
        """Deactivate bots"""
        from pyHaasAPI.api import deactivate_bot
        
        deactivated_count = 0
        failed_count = 0
        
        for i, bot in enumerate(bots, 1):
            try:
                bot_id = getattr(bot, 'bot_id', None) or getattr(bot, 'ID', '')
                bot_name = getattr(bot, 'name', None) or getattr(bot, 'Name', '') or f"Bot {bot_id[:8]}"
                
                self.logger.info(f"🛑 Deactivating bot {i}/{len(bots)}: {bot_name}")
                
                if dry_run:
                    self.logger.info(f"   Would deactivate: {bot_name}")
                    deactivated_count += 1
                else:
                    success = deactivate_bot(self.analyzer.executor, bot_id)
                    
                    if success:
                        self.logger.info(f"✅ Successfully deactivated: {bot_name}")
                        deactivated_count += 1
                    else:
                        self.logger.error(f"❌ Failed to deactivate: {bot_name}")
                        failed_count += 1
                        
            except Exception as e:
                self.logger.error(f"❌ Error deactivating bot {bot_name}: {e}")
                failed_count += 1
                continue
        
        self.logger.info(f"\n🎉 Deactivation complete: {deactivated_count} deactivated, {failed_count} failed")
        return failed_count == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Unified bot management CLI for pyHaasAPI")
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Mass creation subcommand
    create_parser = subparsers.add_parser('create', help='Create bots from labs')
    add_common_arguments(create_parser)
    add_trade_amount_arguments(create_parser)
    create_parser.add_argument('--min-backtests', type=int, default=10,
                              help='Minimum number of backtests required per lab')
    create_parser.add_argument('--activate', action='store_true',
                              help='Activate created bots for live trading')
    
    # Fix amounts subcommand
    fix_parser = subparsers.add_parser('fix-amounts', help='Fix bot trade amounts')
    add_common_arguments(fix_parser)
    add_trade_amount_arguments(fix_parser)
    add_bot_selection_arguments(fix_parser)
    
    # Account cleanup subcommand
    cleanup_parser = subparsers.add_parser('cleanup-accounts', help='Clean up account names')
    add_common_arguments(cleanup_parser)
    
    # Bot activation subcommand
    activate_parser = subparsers.add_parser('activate', help='Activate bots')
    add_common_arguments(activate_parser)
    add_bot_selection_arguments(activate_parser)
    
    # Bot deactivation subcommand
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate bots')
    add_common_arguments(deactivate_parser)
    add_bot_selection_arguments(deactivate_parser)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create and run unified bot management CLI
    bot_mgmt_cli = UnifiedBotManagementCLI()
    success = bot_mgmt_cli.run(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())















