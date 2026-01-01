#!/usr/bin/env python3
"""
Refactored Fix Bot Trade Amounts Tool

This tool updates all existing bots to use the new price-based trade amount calculation,
ensuring each bot has the equivalent of $2000 USDT in base currency based on current market prices.
Refactored to use base classes.
"""

import argparse
from typing import List, Dict, Any, Optional

from .base import BaseDirectAPICLI
from .common import add_common_arguments, add_trade_amount_arguments, add_bot_selection_arguments, get_all_bots, apply_smart_precision
from pyHaasAPI_v1.price import PriceAPI, PriceData


class BotTradeAmountFixerRefactored(BaseDirectAPICLI):
    """Refactored tool to fix bot trade amounts using current market prices"""
    
    def __init__(self):
        super().__init__()
        self.price_api = None
        self.fixed_count = 0
        self.failed_count = 0
        
    def run(self, args) -> bool:
        """Main execution method"""
        try:
            # Connect to API
            if not self.connect():
                return False
            
            # Initialize price API
            self.price_api = PriceAPI(self.executor)
            
            # Get all bots
            all_bots = get_all_bots(self.executor)
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
            self.show_results()
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in bot trade amount fixer: {e}")
            return False
    
    def filter_bots(self, all_bots: List, bot_ids: List[str] = None, 
                   exclude_bot_ids: List[str] = None) -> List:
        """Filter bots based on criteria"""
        filtered_bots = []
        
        for bot in all_bots:
            bot_id = getattr(bot, 'bot_id', None) or getattr(bot, 'ID', '')
            
            # If specific bot IDs are provided, only include those
            if bot_ids:
                if bot_id in bot_ids:
                    filtered_bots.append(bot)
                continue
            
            # If exclude bot IDs are provided, skip those
            if exclude_bot_ids:
                if bot_id in exclude_bot_ids:
                    continue
            
            # If no filters, include all bots
            filtered_bots.append(bot)
        
        return filtered_bots
    
    def fix_all_bot_trade_amounts(self, bots: List, args) -> bool:
        """Fix trade amounts for all specified bots"""
        self.logger.info("🔧 Starting bot trade amount fixing process")
        self.logger.info("=" * 60)
        
        for i, bot in enumerate(bots, 1):
            try:
                bot_id = getattr(bot, 'bot_id', None) or getattr(bot, 'ID', '')
                bot_name = getattr(bot, 'name', None) or getattr(bot, 'Name', '') or f"Bot {bot_id[:8]}"
                
                self.logger.info(f"🔧 Fixing bot {i}/{len(bots)}: {bot_name}")
                
                # Fix bot trade amount
                success = self.fix_bot_trade_amount(bot, args)
                
                if success:
                    self.fixed_count += 1
                    self.logger.info(f"✅ Successfully fixed: {bot_name}")
                else:
                    self.failed_count += 1
                    self.logger.error(f"❌ Failed to fix: {bot_name}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error fixing bot {bot_name}: {e}")
                self.failed_count += 1
                continue
        
        return self.failed_count == 0
    
    def fix_bot_trade_amount(self, bot, args) -> bool:
        """Fix trade amount for a single bot"""
        try:
            bot_id = getattr(bot, 'bot_id', None) or getattr(bot, 'ID', '')
            market_tag = getattr(bot, 'market_tag', None) or getattr(bot, 'MarketTag', '')
            
            if not market_tag:
                self.logger.warning(f"⚠️ No market tag found for bot {bot_id}")
                return False
            
            # Calculate new trade amount
            new_trade_amount = self.calculate_trade_amount(market_tag, args)
            
            if new_trade_amount is None:
                self.logger.warning(f"⚠️ Could not calculate trade amount for {market_tag}")
                return False
            
            if args.dry_run:
                self.logger.info(f"   Would set trade amount to: {new_trade_amount:.6f} base currency")
                return True
            
            # Update bot trade amount
            success = self.update_bot_trade_amount(bot_id, new_trade_amount)
            
            if success:
                self.logger.info(f"💰 Set trade amount to: {new_trade_amount:.6f} base currency")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing bot trade amount: {e}")
            return False
    
    def calculate_trade_amount(self, market_tag: str, args) -> Optional[float]:
        """Calculate trade amount based on method"""
        try:
            if args.method == 'usdt':
                return self.calculate_usdt_amount(market_tag, args.target_amount)
            elif args.method == 'wallet_percentage':
                return self.calculate_wallet_percentage_amount(market_tag, args.wallet_percentage)
            else:
                self.logger.error(f"❌ Unknown method: {args.method}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating trade amount: {e}")
            return None
    
    def calculate_usdt_amount(self, market_tag: str, target_usdt: float) -> Optional[float]:
        """Calculate trade amount in base currency for target USDT amount"""
        try:
            # Get current price
            price_data = self.price_api.get_price_data(market_tag)
            if not price_data:
                self.logger.warning(f"⚠️ Could not get price for {market_tag}")
                return None
            
            current_price = price_data.close
            
            # Calculate trade amount in base currency
            trade_amount_base = target_usdt / current_price
            
            # Apply smart precision
            trade_amount_base = apply_smart_precision(trade_amount_base)
            
            return trade_amount_base
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating USDT amount: {e}")
            return None
    
    def calculate_wallet_percentage_amount(self, market_tag: str, wallet_percentage: float) -> Optional[float]:
        """Calculate trade amount based on wallet percentage"""
        try:
            # Get current price
            price_data = self.price_api.get_price_data(market_tag)
            if not price_data:
                self.logger.warning(f"⚠️ Could not get price for {market_tag}")
                return None
            
            current_price = price_data.close
            
            # Assume $10,000 wallet balance (standard for simulated accounts)
            wallet_balance_usdt = 10000.0
            target_usdt = wallet_balance_usdt * (wallet_percentage / 100.0)
            
            # Calculate trade amount in base currency
            trade_amount_base = target_usdt / current_price
            
            # Apply smart precision
            trade_amount_base = apply_smart_precision(trade_amount_base)
            
            return trade_amount_base
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating wallet percentage amount: {e}")
            return None
    
    def update_bot_trade_amount(self, bot_id: str, trade_amount: float) -> bool:
        """Update bot trade amount via API"""
        try:
            from pyHaasAPI_v1.api import edit_bot_parameter
            
            # Update trade amount parameter
            success = edit_bot_parameter(
                self.executor,
                bot_id,
                "TradeAmount",
                trade_amount
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error updating bot trade amount: {e}")
            return False
    
    def show_results(self):
        """Show final results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 BOT TRADE AMOUNT FIXING RESULTS")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Successfully fixed: {self.fixed_count}")
        self.logger.info(f"❌ Failed to fix: {self.failed_count}")
        self.logger.info(f"📊 Total processed: {self.fixed_count + self.failed_count}")
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fix bot trade amounts using current market prices")
    
    # Add common arguments
    add_common_arguments(parser)
    
    # Add trade amount arguments
    add_trade_amount_arguments(parser)
    
    # Add bot selection arguments
    add_bot_selection_arguments(parser)
    
    args = parser.parse_args()
    
    # Create and run fixer
    fixer = BotTradeAmountFixerRefactored()
    success = fixer.run(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
















