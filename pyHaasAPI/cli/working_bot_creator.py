#!/usr/bin/env python3
"""
Working Bot Creator for pyHaasAPI CLI

This module contains the PROVEN working bot creation logic extracted from
mass_bot_creator.py - the most comprehensive and working bot creation tool.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .base import BaseBotCLI
from .common import get_all_accounts, apply_smart_precision


@dataclass
class BotCreationResult:
    """Data class for bot creation results"""
    bot_id: str
    bot_name: str
    backtest_id: str
    account_id: str
    market_tag: str
    leverage: float
    margin_mode: str
    position_mode: str
    trade_amount_usdt: float
    creation_timestamp: str
    success: bool
    activated: bool
    error_message: Optional[str] = None


@dataclass
class MassBotCreationResult:
    """Data class for mass bot creation results"""
    total_labs_processed: int
    total_bots_created: int
    total_bots_activated: int
    successful_labs: List[str]
    failed_labs: List[str]
    bot_results: List[BotCreationResult]
    creation_timestamp: str


class WorkingBotCreator:
    """PROVEN working bot creation logic from mass_bot_creator.py"""
    
    def __init__(self, analyzer, cache_manager):
        self.analyzer = analyzer
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self.accounts = []
        self.account_index = 0
    
    def get_next_account(self) -> Optional[Dict]:
        """PROVEN working account assignment from mass_bot_creator.py"""
        if not self.accounts:
            self.logger.error("❌ No accounts available")
            return None
            
        # Use round-robin assignment
        account = self.accounts[self.account_index % len(self.accounts)]
        self.account_index += 1
        
        return account
    
    def create_bot_name(self, lab_name: str, backtest, script_name: str) -> str:
        """
        PROVEN working bot naming convention from mass_bot_creator.py
        Format: LabName - ScriptName - ROI pop/gen WR%
        """
        # Clean lab name
        lab_name_clean = lab_name.replace('_', ' ').replace('-', ' ')
        
        # Format ROI
        roi_str = f"{backtest.roi_percentage:.0f}"
        
        # Format population/generation
        pop_gen_str = f"{backtest.population_idx or 0}/{backtest.generation_idx or 0}"
        
        # Format win rate as percentage
        win_rate_percent = f"{backtest.win_rate * 100:.0f}%"
        
        # Create bot name following the convention
        bot_name = f"{lab_name_clean} - {script_name} - {roi_str} {pop_gen_str} {win_rate_percent}"
        
        return bot_name
    
    def calculate_trade_amount(self, backtest, target_usdt_amount: float = 2000.0) -> float:
        """
        PROVEN working trade amount calculation from mass_bot_creator.py
        """
        try:
            # Get current price for the market
            market_tag = backtest.market_tag
            price_data = self.analyzer.get_price_data(market_tag)
            
            if not price_data or not hasattr(price_data, 'close'):
                self.logger.warning(f"⚠️ Could not get price for {market_tag}, using default amount")
                return target_usdt_amount
            
            current_price = price_data.close
            
            # Calculate trade amount in base currency
            trade_amount_base = target_usdt_amount / current_price
            
            # Apply smart precision
            trade_amount_base = apply_smart_precision(trade_amount_base)
            
            self.logger.info(f"💰 Calculated trade amount: {trade_amount_base:.6f} base currency (${target_usdt_amount} USDT equivalent)")
            
            return trade_amount_base
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error calculating trade amount: {e}, using default")
            return target_usdt_amount
    
    def create_bot_from_backtest(self, backtest, lab_name: str, target_usdt_amount: float = 2000.0, 
                                dry_run: bool = False) -> Optional[BotCreationResult]:
        """
        PROVEN working bot creation from mass_bot_creator.py
        """
        try:
            # Get next available account
            account = self.get_next_account()
            if not account:
                self.logger.error("❌ No accounts available for bot creation")
                return None
            
            # Create bot name
            bot_name = self.create_bot_name(lab_name, backtest, backtest.script_name)
            
            if dry_run:
                self.logger.info(f"   Would create bot: {bot_name}")
                self.logger.info(f"   Would set trade amount to: {target_usdt_amount} USDT equivalent")
                
                # Create a mock bot result for dry run
                return BotCreationResult(
                    bot_id="dry-run-mock",
                    bot_name=bot_name,
                    backtest_id=backtest.backtest_id,
                    account_id="dry-run-account",
                    market_tag=backtest.market_tag,
                    leverage=20.0,
                    margin_mode="CROSS",
                    position_mode="HEDGE",
                    trade_amount_usdt=target_usdt_amount,
                    creation_timestamp=datetime.now().isoformat(),
                    success=True,
                    activated=False,
                    error_message=None
                )
            
            # Calculate trade amount
            trade_amount_base = self.calculate_trade_amount(backtest, target_usdt_amount)
            
            # Create bot with proper configuration using analyzer
            bot_result = self.analyzer.create_bot_from_backtest(
                backtest=backtest,
                bot_name=bot_name
            )
            
            if bot_result and bot_result.success:
                self.logger.info(f"✅ Created bot: {bot_result.bot_name}")
                self.logger.info(f"💰 Trade amount: {trade_amount_base:.4f} base currency (${target_usdt_amount} USDT equivalent)")
                return bot_result
            else:
                error_msg = bot_result.error_message if bot_result else "Unknown error"
                self.logger.error(f"❌ Failed to create bot from backtest {backtest.backtest_id}: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error creating bot: {e}")
            return None
    
    def activate_bot(self, bot_id: str) -> bool:
        """Activate bot for live trading"""
        try:
            activation_success = self.analyzer.activate_bot(bot_id)
            if activation_success:
                self.logger.info(f"🚀 Bot {bot_id} activated for live trading")
                return True
            else:
                self.logger.warning(f"⚠️ Bot {bot_id} created but activation failed")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error activating bot {bot_id}: {e}")
            return False
    
    def analyze_lab_and_create_bots(self, lab_id: str, lab_name: str, top_count: int = 5,
                                  min_backtests: int = 10, min_winrate: float = 0.0,
                                  target_usdt_amount: float = 2000.0, activate: bool = False,
                                  dry_run: bool = False) -> List[BotCreationResult]:
        """
        PROVEN working lab analysis and bot creation from mass_bot_creator.py
        """
        try:
            self.logger.info(f"🔍 Analyzing lab: {lab_name}")
            
            # Analyze lab using the working analyzer
            analysis_result = self.analyzer.analyze_lab(lab_id, top_count)
            
            if not analysis_result or not analysis_result.top_backtests:
                self.logger.warning(f"⚠️ No backtests found for lab {lab_name}")
                return []
            
            # Check if lab has minimum required backtests
            total_backtests = len(analysis_result.top_backtests)
            if total_backtests < min_backtests:
                self.logger.warning(f"⚠️ Lab {lab_name} has only {total_backtests} backtests (minimum required: {min_backtests}) - skipping")
                return []
            
            self.logger.info(f"📊 Found {total_backtests} backtests for {lab_name} (analyzing top {min(top_count, total_backtests)})")
            
            # Apply win rate filter if specified
            filtered_backtests = analysis_result.top_backtests
            if min_winrate > 0.0:
                filtered_backtests = [bt for bt in analysis_result.top_backtests if bt.win_rate >= min_winrate]
                self.logger.info(f"📊 After win rate filter (>= {min_winrate:.1%}): {len(filtered_backtests)} backtests")
                
                if not filtered_backtests:
                    self.logger.warning(f"⚠️ No backtests meet the minimum win rate requirement of {min_winrate:.1%}")
                    return []
            
            # Create bots from top backtests
            bot_results = []
            for i, backtest in enumerate(filtered_backtests[:top_count]):
                try:
                    self.logger.info(f"🤖 Creating bot {i+1}/{top_count} from backtest {backtest.backtest_id}")
                    
                    # Create bot
                    bot_result = self.create_bot_from_backtest(
                        backtest=backtest,
                        lab_name=lab_name,
                        target_usdt_amount=target_usdt_amount,
                        dry_run=dry_run
                    )
                    
                    if bot_result and bot_result.success:
                        # Activate bot if requested
                        if activate and not dry_run:
                            activation_success = self.activate_bot(bot_result.bot_id)
                            bot_result.activated = activation_success
                        
                        bot_results.append(bot_result)
                    else:
                        self.logger.error(f"❌ Failed to create bot from backtest {backtest.backtest_id}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error creating bot {i+1} for lab {lab_name}: {e}")
                    continue
            
            self.logger.info(f"🎯 Created {len(bot_results)} bots for lab {lab_name}")
            return bot_results
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing lab {lab_name}: {e}")
            return []
    
    def run_mass_creation(self, lab_ids: List[str] = None, exclude_lab_ids: List[str] = None,
                         top_count: int = 5, min_backtests: int = 10, min_winrate: float = 0.0,
                         target_usdt_amount: float = 2000.0, activate: bool = False,
                         dry_run: bool = False) -> MassBotCreationResult:
        """
        PROVEN working mass bot creation process from mass_bot_creator.py
        """
        self.logger.info("🚀 Starting Mass Bot Creation Process")
        self.logger.info("=" * 60)
        
        # Get all accounts for bot assignment
        self.accounts = get_all_accounts(self.analyzer.executor)
        if not self.accounts:
            self.logger.error("❌ No accounts found - cannot create bots")
            return MassBotCreationResult(
                total_labs_processed=0,
                total_bots_created=0,
                total_bots_activated=0,
                successful_labs=[],
                failed_labs=[],
                bot_results=[],
                creation_timestamp=datetime.now().isoformat()
            )
        
        self.logger.info(f"📋 Found {len(self.accounts)} accounts for bot assignment")
        
        # Get all complete labs
        all_labs = self.analyzer.get_complete_labs()
        if not all_labs:
            self.logger.error("❌ No complete labs found")
            return MassBotCreationResult(
                total_labs_processed=0,
                total_bots_created=0,
                total_bots_activated=0,
                successful_labs=[],
                failed_labs=[],
                bot_results=[],
                creation_timestamp=datetime.now().isoformat()
            )
        
        # Filter labs based on criteria
        filtered_labs = self.filter_labs(all_labs, lab_ids, exclude_lab_ids)
        
        if not filtered_labs:
            self.logger.warning("⚠️ No labs match the specified criteria")
            return MassBotCreationResult(
                total_labs_processed=0,
                total_bots_created=0,
                total_bots_activated=0,
                successful_labs=[],
                failed_labs=[],
                bot_results=[],
                creation_timestamp=datetime.now().isoformat()
            )
        
        self.logger.info(f"📊 Processing {len(filtered_labs)} labs")
        self.logger.info(f"🎯 Target: {top_count} bots per lab")
        self.logger.info(f"📈 Min backtests: {min_backtests}")
        self.logger.info(f"🎯 Min win rate: {min_winrate:.1%}")
        self.logger.info(f"💰 Trade amount: ${target_usdt_amount} USDT equivalent")
        self.logger.info(f"🚀 Activate bots: {activate}")
        self.logger.info(f"🧪 Dry run: {dry_run}")
        self.logger.info("=" * 60)
        
        # Process each lab
        all_bot_results = []
        successful_labs = []
        failed_labs = []
        
        for i, lab in enumerate(filtered_labs):
            try:
                lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
                lab_name = getattr(lab, 'name', None) or getattr(lab, 'lab_name', None) or f"Lab {lab_id[:8]}"
                
                self.logger.info(f"\n📊 Processing lab {i+1}/{len(filtered_labs)}: {lab_name}")
                
                # Analyze lab and create bots
                bot_results = self.analyze_lab_and_create_bots(
                    lab_id=lab_id,
                    lab_name=lab_name,
                    top_count=top_count,
                    min_backtests=min_backtests,
                    min_winrate=min_winrate,
                    target_usdt_amount=target_usdt_amount,
                    activate=activate,
                    dry_run=dry_run
                )
                
                if bot_results:
                    all_bot_results.extend(bot_results)
                    successful_labs.append(lab_name)
                    self.logger.info(f"✅ Successfully processed lab {lab_name}")
                else:
                    failed_labs.append(lab_name)
                    self.logger.warning(f"⚠️ No bots created for lab {lab_name}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error processing lab {lab_name}: {e}")
                failed_labs.append(lab_name)
                continue
        
        # Calculate final statistics
        total_bots_created = len(all_bot_results)
        total_bots_activated = sum(1 for bot in all_bot_results if bot.activated)
        
        # Print final summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 MASS BOT CREATION COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Labs processed: {len(filtered_labs)}")
        self.logger.info(f"✅ Successful labs: {len(successful_labs)}")
        self.logger.info(f"❌ Failed labs: {len(failed_labs)}")
        self.logger.info(f"🤖 Total bots created: {total_bots_created}")
        self.logger.info(f"🚀 Total bots activated: {total_bots_activated}")
        self.logger.info("=" * 60)
        
        return MassBotCreationResult(
            total_labs_processed=len(filtered_labs),
            total_bots_created=total_bots_created,
            total_bots_activated=total_bots_activated,
            successful_labs=successful_labs,
            failed_labs=failed_labs,
            bot_results=all_bot_results,
            creation_timestamp=datetime.now().isoformat()
        )
    
    def filter_labs(self, all_labs: List[Any], lab_ids: List[str] = None, 
                   exclude_lab_ids: List[str] = None) -> List[Any]:
        """PROVEN working lab filtering logic from mass_bot_creator.py"""
        filtered_labs = []
        
        for lab in all_labs:
            lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            
            # If specific lab IDs are provided, only include those
            if lab_ids:
                if lab_id in lab_ids:
                    filtered_labs.append(lab)
                continue
            
            # If exclude lab IDs are provided, skip those
            if exclude_lab_ids:
                if lab_id in exclude_lab_ids:
                    continue
            
            # If no filters, include all labs
            filtered_labs.append(lab)
        
        return filtered_labs























