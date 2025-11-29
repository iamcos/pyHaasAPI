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
            elif parsed_args.action == 'create-from-analysis':
                return await self.create_from_analysis(parsed_args)
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
            choices=['list', 'create', 'delete', 'activate', 'deactivate', 'pause', 'resume', 'set-notes', 'get-notes', 'create-from-analysis'],
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
                from ..models.enumerations import AccountStatus
                bots = self.filter_by_status(
                    bots,
                    status_field='status',
                    target_status=args.status.upper(),
                    enum_class=AccountStatus
                )
            
            if not bots:
                self.logger.info("No bots found")
                return 0
            
            # Display results using utility method
            self.format_output(
                bots,
                format_type=args.output_format,
                output_file=args.output_file,
                field_mapping={
                    'bot_id': 'id',
                    'bot_name': 'name',
                    'status': 'status',
                    'account_id': 'account_id',
                    'market_tag': 'market_tag',
                    'created_at': 'created_at'
                }
            )
            
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
                from ..models.enumerations import AccountStatus
                bots = await self.bot_service.get_all_bots()
                inactive_bots = self.filter_by_status(
                    bots,
                    status_field='status',
                    target_status='INACTIVE',
                    enum_class=AccountStatus
                )
                bot_ids = [bot.id for bot in inactive_bots]
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
                from ..models.enumerations import AccountStatus
                bots = await self.bot_service.get_all_bots()
                active_bots = self.filter_by_status(
                    bots,
                    status_field='status',
                    target_status='ACTIVE',
                    enum_class=AccountStatus
                )
                bot_ids = [bot.id for bot in active_bots]
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
            notes = self.safe_get(bot, 'notes', '')
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
    
    async def create_from_analysis(self, args: argparse.Namespace) -> int:
        """Create bots from analysis results"""
        try:
            # Parse arguments
            server = getattr(args, 'server', None)
            analysis_file = getattr(args, 'analysis_file', None)
            
            if not server:
                print("❌ Server name required. Use --server <name>")
                return 1
            
            if not analysis_file:
                print("❌ Analysis file required. Use --analysis-file <path>")
                return 1
            
            print(f"🤖 Creating bots from analysis for {server}...")
            print(f"📁 Loading analysis file: {analysis_file}")
            
            # Load analysis file
            import json
            from pathlib import Path
            
            if not Path(analysis_file).exists():
                print(f"❌ Analysis file not found: {analysis_file}")
                return 1
            
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
            
            results = analysis_data.get('results', {})
            if not results:
                print("❌ No analysis results found in file")
                return 1
            
            print(f"📊 Found {len(results)} labs with analysis results")
            
            # Setup server configuration
            server_configs = {
                'srv01': {'port': 8089, 'tunnel_cmd': 'ssh -N -L 8089:127.0.0.1:8090 -L 8091:127.0.0.1:8092 prod@srv01'},
                'srv02': {'port': 8090, 'tunnel_cmd': None},  # Already running
                'srv03': {'port': 8091, 'tunnel_cmd': 'ssh -N -L 8091:127.0.0.1:8090 -L 8093:127.0.0.1:8092 prod@srv03'},
            }
            
            if server not in server_configs:
                print(f"❌ Unknown server: {server}. Available: srv01, srv02, srv03")
                return 1
            
            config = server_configs[server]
            
            # Setup client for this server
            from pyHaasAPI.core.client import AsyncHaasClient
            from pyHaasAPI.core.auth import AuthenticationManager
            from pyHaasAPI.config.api_config import APIConfig
            from pyHaasAPI.api.lab.lab_api import LabAPI
            from pyHaasAPI.api.bot.bot_api import BotAPI
            
            server_config = APIConfig()
            server_config.host = "127.0.0.1"
            server_config.port = config['port']
            
            # Connect and authenticate
            client = AsyncHaasClient(server_config)
            auth_manager = AuthenticationManager(client, server_config)
            
            await client.connect()
            await auth_manager.authenticate()
            print(f"✅ Connected to {server}")
            
            # Create API instances
            lab_api = LabAPI(client, auth_manager)
            bot_api = BotAPI(client, auth_manager)
            
            # Create bots for each lab
            bot_creation_results = {}
            total_bots_created = 0
            
            for lab_id, lab_data in results.items():
                lab_name = lab_data.get('lab_name', lab_id[:8])
                top_5_backtests = lab_data.get('top_5', [])
                
                if not top_5_backtests:
                    print(f"   ⚠️  No top 5 backtests for lab {lab_name}")
                    continue
                
                print(f"\n🤖 Creating bots for lab {lab_name}...")
                print(f"   📊 Top 5 backtests: {len(top_5_backtests)}")
                
                try:
                    # Get lab details for account/market info
                    lab_details = await lab_api.get_lab_details(lab_id)
                    
                    # Create 5 bots (one for each top backtest)
                    lab_bot_results = []
                    
                    for i, backtest in enumerate(top_5_backtests, 1):
                        try:
                            backtest_id = backtest['backtest_id']
                            roi = backtest['roi_percentage']
                            win_rate = backtest['win_rate']
                            
                            # Create bot name
                            bot_name = f"{lab_name} - Top {i} - ROE {roi:.1f}%"
                            
                            # Get lab configuration
                            account_id = self.safe_get(lab_details, 'account_id') or self.safe_get(lab_details, 'accountId', '')
                            market_tag = self.safe_get(lab_details, 'market_tag') or self.safe_get(lab_details, 'marketTag', '')
                            leverage = self.safe_get(lab_details, 'leverage', 20.0) or 20.0
                            
                            if not account_id or not market_tag:
                                print(f"   ❌ Missing lab config (account_id: {account_id}, market_tag: {market_tag})")
                                continue
                            
                            # Create bot
                            print(f"   🔄 Creating bot {i}/5: {bot_name}")
                            bot_details = await bot_api.create_bot_from_lab(
                                lab_id=lab_id,
                                backtest_id=backtest_id,
                                bot_name=bot_name,
                                account_id=account_id,
                                market=market_tag,
                                leverage=leverage
                            )
                            
                            print(f"   ✅ Created bot: {bot_details.bot_id[:8]} - {bot_name}")
                            
                            lab_bot_results.append({
                                'bot_id': bot_details.bot_id,
                                'bot_name': bot_name,
                                'backtest_id': backtest_id,
                                'roi_percentage': roi,
                                'win_rate': win_rate,
                                'status': 'created'
                            })
                            
                            total_bots_created += 1
                            
                        except Exception as e:
                            print(f"   ❌ Failed to create bot {i}: {e}")
                            lab_bot_results.append({
                                'bot_name': f"{lab_name} - Top {i} - ROE {backtest['roi_percentage']:.1f}%",
                                'backtest_id': backtest['backtest_id'],
                                'error': str(e),
                                'status': 'failed'
                            })
                    
                    # Count bots using utility method
                    bots_created = len([r for r in lab_bot_results if self.safe_get(r, 'status') == 'created'])
                    bots_failed = len([r for r in lab_bot_results if self.safe_get(r, 'status') == 'failed'])
                    
                    bot_creation_results[lab_id] = {
                        'lab_name': lab_name,
                        'bots_created': bots_created,
                        'bots_failed': bots_failed,
                        'results': lab_bot_results
                    }
                    
                    print(f"   📊 Lab {lab_name}: {bots_created} bots created, {bots_failed} failed")
                    
                except Exception as e:
                    print(f"   ❌ Error processing lab {lab_name}: {e}")
                    bot_creation_results[lab_id] = {
                        'lab_name': lab_name,
                        'error': str(e),
                        'bots_created': 0,
                        'bots_failed': 0,
                        'results': []
                    }
            
            # Save bot creation results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"unified_cache/bot_creation/{server}_results_{timestamp}.json"
            Path("unified_cache/bot_creation").mkdir(parents=True, exist_ok=True)
            
            creation_data = {
                'server': server,
                'timestamp': datetime.now().isoformat(),
                'analysis_file': analysis_file,
                'summary': {
                    'labs_processed': len(results),
                    'total_bots_created': total_bots_created,
                    'total_bots_failed': sum(self.safe_get(result, 'bots_failed', 0) for result in bot_creation_results.values()),
                    'labs_with_success': len([r for r in bot_creation_results.values() if self.safe_get(r, 'bots_created', 0) > 0])
                },
                'results': bot_creation_results
            }
            
            with open(results_file, 'w') as f:
                json.dump(creation_data, f, indent=2, default=str)
            
            # Summary
            print(f"\n🎉 Bot creation completed for {server}!")
            print(f"📊 Summary:")
            print(f"   - Labs processed: {len(results)}")
            print(f"   - Total bots created: {total_bots_created}")
            total_failed = sum(self.safe_get(result, 'bots_failed', 0) for result in bot_creation_results.values())
            labs_with_success = len([r for r in bot_creation_results.values() if self.safe_get(r, 'bots_created', 0) > 0])
            print(f"   - Total bots failed: {total_failed}")
            print(f"   - Labs with successful bot creation: {labs_with_success}")
            print(f"   - Results saved: {results_file}")
            
            # Show per-lab results
            print(f"\n📋 Per-lab results:")
            for lab_id, result in bot_creation_results.items():
                bots_created = self.safe_get(result, 'bots_created', 0)
                lab_name = self.safe_get(result, 'lab_name', 'Unknown')
                error = self.safe_get(result, 'error')
                
                if bots_created > 0:
                    print(f"   ✅ {lab_name}: {bots_created} bots created")
                elif error:
                    print(f"   ❌ {lab_name}: ERROR - {error}")
                else:
                    print(f"   ⚠️  {lab_name}: No bots created")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error creating bots from analysis: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            await client.close()
