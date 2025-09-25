"""
Bot CLI for pyHaasAPI v2

This module provides command-line interface for bot operations
using the new v2 architecture with async support and type safety.
"""

import asyncio
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseCLI, CLIConfig
from ..core.logging import get_logger
from ..core.type_definitions import BotID, BotStatus
from ..exceptions import APIError, ValidationError

logger = get_logger("bot_cli")


class BotCLI(BaseCLI):
    """
    CLI for bot operations.
    
    Provides command-line interface for bot management, creation,
    activation, and monitoring operations.
    """

    def __init__(self, config: Optional[CLIConfig] = None):
        super().__init__(config)
        self.logger = get_logger("bot_cli")

    async def run(self, args: List[str]) -> int:
        """
        Run the bot CLI with the given arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parser = self.create_bot_parser()
            parsed_args = parser.parse_args(args)
            
            # Update config from args
            self.update_config_from_args(parsed_args)
            
            # Connect to API
            if not await self.connect():
                self.logger.error("Failed to connect to API")
                return 1
            
            # Execute command
            if parsed_args.action == 'list':
                return await self.list_bots(parsed_args)
            elif parsed_args.action == 'create':
                return await self.create_bots(parsed_args)
            elif parsed_args.action == 'delete':
                return await self.delete_bot(parsed_args)
            elif parsed_args.action == 'activate':
                return await self.activate_bots(parsed_args)
            elif parsed_args.action == 'deactivate':
                return await self.deactivate_bots(parsed_args)
            elif parsed_args.action == 'pause':
                return await self.pause_bots(parsed_args)
            elif parsed_args.action == 'resume':
                return await self.resume_bots(parsed_args)
            elif parsed_args.action == 'set-notes':
                return await self.set_bot_notes(parsed_args)
            elif parsed_args.action == 'get-notes':
                return await self.get_bot_notes(parsed_args)
            else:
                self.logger.error(f"Unknown action: {parsed_args.action}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in bot CLI: {e}")
            return 1

    def create_bot_parser(self) -> argparse.ArgumentParser:
        """Create bot-specific argument parser"""
        parser = argparse.ArgumentParser(
            description="Bot operations for pyHaasAPI v2",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # List all bots
  python -m pyHaasAPI_v2.cli bot list
  
  # Create bots from lab
  python -m pyHaasAPI_v2.cli bot create --from-lab lab123 --count 3 --activate
  
  # Activate specific bots
  python -m pyHaasAPI_v2.cli bot activate --bot-ids bot1,bot2,bot3
  
  # Deactivate all bots
  python -m pyHaasAPI_v2.cli bot deactivate --all
  
  # Pause bots
  python -m pyHaasAPI_v2.cli bot pause --bot-ids bot1,bot2
            """
        )
        
        # Add common options
        parser = self.create_parser("Bot operations")
        
        # Bot-specific options
        parser.add_argument(
            'action',
            choices=['list', 'create', 'delete', 'activate', 'deactivate', 'pause', 'resume', 'set-notes', 'get-notes'],
            help='Bot action to perform'
        )
        parser.add_argument('--bot-id', help='Bot ID')
        parser.add_argument('--bot-ids', help='Comma-separated bot IDs')
        parser.add_argument('--from-lab', help='Create bots from lab ID')
        parser.add_argument('--count', type=int, default=1, help='Number of bots to create')
        parser.add_argument('--activate', action='store_true', help='Activate bots after creation')
        parser.add_argument('--all', action='store_true', help='Apply to all bots')
        parser.add_argument('--status', choices=['active', 'inactive', 'paused', 'error'], help='Filter by status')
        parser.add_argument('--output-format', choices=['json', 'csv', 'table'], default='table', help='Output format')
        parser.add_argument('--output-file', help='Output file path')
        parser.add_argument('--notes', help='Notes text (JSON string recommended)')
        
        return parser

    async def list_bots(self, args: argparse.Namespace) -> int:
        """List all bots"""
        try:
            self.logger.info("Fetching bots...")
            
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            
            # Get bots
            bots = await self.bot_service.get_all_bots()
            
            # Filter by status if specified
            if args.status:
                bots = [bot for bot in bots if bot.status == args.status]
            
            if not bots:
                self.logger.info("No bots found")
                return 0
            
            # Display results
            if args.output_format == 'json':
                import json
                output = json.dumps([bot.dict() for bot in bots], indent=2)
                if args.output_file:
                    with open(args.output_file, 'w') as f:
                        f.write(output)
                else:
                    print(output)
            elif args.output_format == 'csv':
                import csv
                if args.output_file:
                    with open(args.output_file, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'status', 'account_id', 'market_tag', 'created_at'])
                        writer.writeheader()
                        for bot in bots:
                            writer.writerow(bot.dict())
                else:
                    print("id,name,status,account_id,market_tag,created_at")
                    for bot in bots:
                        print(f"{bot.id},{bot.name},{bot.status},{bot.account_id},{bot.market_tag},{bot.created_at}")
            else:
                # Table format
                print(f"\nFound {len(bots)} bots:")
                print("-" * 120)
                print(f"{'ID':<20} {'Name':<40} {'Status':<10} {'Account ID':<20} {'Market':<20}")
                print("-" * 120)
                for bot in bots:
                    print(f"{bot.id:<20} {bot.name[:40]:<40} {bot.status:<10} {bot.account_id:<20} {bot.market_tag:<20}")
                print("-" * 120)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error listing bots: {e}")
            return 1

    async def create_bots(self, args: argparse.Namespace) -> int:
        """Create bots"""
        try:
            if not args.from_lab:
                self.logger.error("Lab ID is required for bot creation (use --from-lab)")
                return 1
            
            self.logger.info(f"Creating {args.count} bots from lab '{args.from_lab}'...")
            
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            
            # Create bots
            result = await self.bot_service.create_bots_from_lab(
                lab_id=args.from_lab,
                count=args.count,
                activate=args.activate
            )
            
            if result.success:
                self.logger.info(f"Successfully created {len(result.data)} bots")
                
                # Display results
                print(f"\nCreated {len(result.data)} bots:")
                print("-" * 100)
                print(f"{'Bot ID':<20} {'Name':<40} {'Status':<10} {'Account ID':<20}")
                print("-" * 100)
                for bot in result.data:
                    print(f"{bot.bot_id:<20} {bot.bot_name[:40]:<40} {'Active' if bot.activated else 'Inactive':<10} {bot.account_id:<20}")
                print("-" * 100)
                
                # Activate bots if requested
                if args.activate:
                    self.logger.info("Activating created bots...")
                    activation_result = await self.bot_service.activate_bots([bot.bot_id for bot in result.data])
                    if activation_result.success:
                        self.logger.info("Successfully activated all bots")
                    else:
                        self.logger.warning(f"Some bots failed to activate: {activation_result.error}")
                
                return 0
            else:
                self.logger.error(f"Failed to create bots: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error creating bots: {e}")
            return 1

    async def delete_bot(self, args: argparse.Namespace) -> int:
        """Delete a bot"""
        try:
            if not args.bot_id:
                self.logger.error("Bot ID is required for deletion")
                return 1
            
            self.logger.info(f"Deleting bot '{args.bot_id}'...")
            
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            
            # Delete bot
            result = await self.bot_service.delete_bot(args.bot_id)
            
            if result.success:
                self.logger.info(f"Successfully deleted bot: {args.bot_id}")
                return 0
            else:
                self.logger.error(f"Failed to delete bot: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error deleting bot: {e}")
            return 1

    async def activate_bots(self, args: argparse.Namespace) -> int:
        """Activate bots"""
        try:
            bot_ids = []
            
            if args.bot_ids:
                bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
            elif args.all:
                # Get all inactive bots
                bots = await self.bot_service.get_all_bots()
                bot_ids = [bot.id for bot in bots if bot.status == 'inactive']
            else:
                self.logger.error("Either --bot-ids or --all is required for activation")
                return 1
            
            if not bot_ids:
                self.logger.info("No bots to activate")
                return 0
            
            self.logger.info(f"Activating {len(bot_ids)} bots...")
            
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            
            # Activate bots
            result = await self.bot_service.activate_bots(bot_ids)
            
            if result.success:
                self.logger.info(f"Successfully activated {len(result.data)} bots")
                print(f"Activated bots: {', '.join(result.data)}")
                return 0
            else:
                self.logger.error(f"Failed to activate bots: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error activating bots: {e}")
            return 1

    async def deactivate_bots(self, args: argparse.Namespace) -> int:
        """Deactivate bots"""
        try:
            bot_ids = []
            
            if args.bot_ids:
                bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
            elif args.all:
                # Get all active bots
                bots = await self.bot_service.get_all_bots()
                bot_ids = [bot.id for bot in bots if bot.status == 'active']
            else:
                self.logger.error("Either --bot-ids or --all is required for deactivation")
                return 1
            
            if not bot_ids:
                self.logger.info("No bots to deactivate")
                return 0
            
            self.logger.info(f"Deactivating {len(bot_ids)} bots...")
            
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            
            # Deactivate bots
            result = await self.bot_service.deactivate_bots(bot_ids)
            
            if result.success:
                self.logger.info(f"Successfully deactivated {len(result.data)} bots")
                print(f"Deactivated bots: {', '.join(result.data)}")
                return 0
            else:
                self.logger.error(f"Failed to deactivate bots: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error deactivating bots: {e}")
            return 1

    async def pause_bots(self, args: argparse.Namespace) -> int:
        """Pause bots"""
        try:
            if not args.bot_ids:
                self.logger.error("Bot IDs are required for pausing (use --bot-ids)")
                return 1
            
            bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
            
            self.logger.info(f"Pausing {len(bot_ids)} bots...")
            
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            
            # Pause bots
            result = await self.bot_service.pause_bots(bot_ids)
            
            if result.success:
                self.logger.info(f"Successfully paused {len(result.data)} bots")
                print(f"Paused bots: {', '.join(result.data)}")
                return 0
            else:
                self.logger.error(f"Failed to pause bots: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error pausing bots: {e}")
            return 1

    async def resume_bots(self, args: argparse.Namespace) -> int:
        """Resume bots"""
        try:
            if not args.bot_ids:
                self.logger.error("Bot IDs are required for resuming (use --bot-ids)")
                return 1
            
            bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
            
            self.logger.info(f"Resuming {len(bot_ids)} bots...")
            
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            
            # Resume bots
            result = await self.bot_service.resume_bots(bot_ids)
            
            if result.success:
                self.logger.info(f"Successfully resumed {len(result.data)} bots")
                print(f"Resumed bots: {', '.join(result.data)}")
                return 0
            else:
                self.logger.error(f"Failed to resume bots: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error resuming bots: {e}")
            return 1

    async def get_bot_notes(self, args: argparse.Namespace) -> int:
        """Get notes for a bot"""
        try:
            if not args.bot_id:
                self.logger.error("--bot-id is required for get-notes")
                return 1
            if not self.bot_service:
                self.logger.error("Bot service not initialized")
                return 1
            bot = await self.bot_service.get_bot_details(args.bot_id)
            notes = getattr(bot, 'notes', '')
            print(notes or '')
            return 0
        except Exception as e:
            self.logger.error(f"Failed to get bot notes: {e}")
            return 1

    async def set_bot_notes(self, args: argparse.Namespace) -> int:
        """Set notes for a bot"""
        try:
            if not args.bot_id:
                self.logger.error("--bot-id is required for set-notes")
                return 1
            if args.notes is None:
                self.logger.error("--notes is required for set-notes")
                return 1
            if not self.bot_service or not hasattr(self.bot_service, 'bot_api'):
                self.logger.error("Bot service not initialized")
                return 1
            await self.bot_service.bot_api.change_bot_notes(args.bot_id, args.notes)
            print(f"Notes updated for bot {args.bot_id}")
            return 0
        except Exception as e:
            self.logger.error(f"Failed to set bot notes: {e}")
            return 1
