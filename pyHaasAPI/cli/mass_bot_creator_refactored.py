#!/usr/bin/env python3
"""
Refactored Mass Bot Creator for pyHaasAPI CLI

This tool creates bots from all qualifying labs with advanced filtering.
Refactored to use base classes and working bot creator.
"""

import argparse
from typing import List, Dict, Any, Optional

from .base import BaseBotCLI
from .common import add_common_arguments, add_trade_amount_arguments, get_all_accounts
from .working_bot_creator import WorkingBotCreator, MassBotCreationResult


class MassBotCreatorRefactored(BaseBotCLI):
    """Refactored mass bot creator using base classes and working bot creator"""
    
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
            self.show_final_results(result)
            
            return result.total_bots_created > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error in mass bot creation: {e}")
            return False
    
    def show_final_results(self, result: MassBotCreationResult):
        """Show final mass bot creation results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 MASS BOT CREATION COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Labs processed: {result.total_labs_processed}")
        self.logger.info(f"✅ Successful labs: {len(result.successful_labs)}")
        self.logger.info(f"❌ Failed labs: {len(result.failed_labs)}")
        self.logger.info(f"🤖 Total bots created: {result.total_bots_created}")
        self.logger.info(f"🚀 Total bots activated: {result.total_bots_activated}")
        
        if result.successful_labs:
            self.logger.info(f"\n✅ Successful labs:")
            for lab in result.successful_labs:
                self.logger.info(f"   - {lab}")
        
        if result.failed_labs:
            self.logger.info(f"\n❌ Failed labs:")
            for lab in result.failed_labs:
                self.logger.info(f"   - {lab}")
        
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Create bots from all qualifying labs with advanced filtering")
    
    # Add common arguments
    add_common_arguments(parser)
    
    # Add trade amount arguments
    add_trade_amount_arguments(parser)
    
    # Add specific arguments
    parser.add_argument('--min-backtests', type=int, default=10,
                       help='Minimum number of backtests required per lab (default: 10)')
    parser.add_argument('--activate', action='store_true',
                       help='Activate created bots for live trading')
    
    args = parser.parse_args()
    
    # Create and run mass bot creator
    creator = MassBotCreatorRefactored()
    success = creator.run(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
