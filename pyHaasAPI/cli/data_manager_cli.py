#!/usr/bin/env python3
"""
Data Manager CLI for pyHaasAPI v2

This CLI provides comprehensive data management capabilities:
- Connect to multiple servers
- Fetch and cache all data
- Analyze labs and create bots
- Monitor server status
- Manage data synchronization
"""

import asyncio
import argparse
import sys
from typing import List, Dict, Any, Optional

from ..core.data_manager import ComprehensiveDataManager, DataManagerConfig
from ..config.settings import Settings
from ..core.logging import get_logger
from .base import BaseCLI


logger = get_logger("data_manager_cli")


class DataManagerCLI(BaseCLI):
    """CLI for comprehensive data management"""
    
    def __init__(self, config):
        super().__init__(config)
        self.data_manager: Optional[ComprehensiveDataManager] = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for data manager CLI"""
        parser = argparse.ArgumentParser(
            description="Comprehensive Data Manager for pyHaasAPI v2",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Connect to all servers and fetch data
  python -m pyHaasAPI_v2.cli.data_manager connect-all --fetch-data
  
  # Analyze labs and create bots with specific criteria
  python -m pyHaasAPI_v2.cli.data_manager analyze-and-create --server srv01 --min-winrate 55 --max-drawdown 0
  
  # Get server summary
  python -m pyHaasAPI_v2.cli.data_manager summary
  
  # Monitor server status
  python -m pyHaasAPI_v2.cli.data_manager status
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Connect command
        connect_parser = subparsers.add_parser('connect', help='Connect to a server')
        connect_parser.add_argument('server', help='Server name (srv01, srv02, srv03)')
        connect_parser.add_argument('--fetch-data', action='store_true', help='Fetch all data after connecting')
        
        # Connect all command
        connect_all_parser = subparsers.add_parser('connect-all', help='Connect to all available servers')
        connect_all_parser.add_argument('--fetch-data', action='store_true', help='Fetch all data after connecting')
        
        # Analyze and create command
        analyze_parser = subparsers.add_parser('analyze-and-create', help='Analyze labs and create bots')
        analyze_parser.add_argument('--server', default='srv01', help='Server to analyze')
        analyze_parser.add_argument('--min-winrate', type=float, default=55.0, help='Minimum win rate')
        analyze_parser.add_argument('--max-drawdown', type=float, default=0.0, help='Maximum drawdown')
        analyze_parser.add_argument('--min-trades', type=int, default=5, help='Minimum trades')
        analyze_parser.add_argument('--max-bots', type=int, default=10, help='Maximum bots to create')
        
        # Summary command
        subparsers.add_parser('summary', help='Get server data summary')
        
        # Status command
        subparsers.add_parser('status', help='Get server status')
        
        # Refresh command
        refresh_parser = subparsers.add_parser('refresh', help='Refresh data from servers')
        refresh_parser.add_argument('--server', help='Specific server to refresh (optional)')
        
        return parser
    
    async def run(self, args: argparse.Namespace) -> int:
        """Run the data manager CLI"""
        try:
            # Initialize data manager
            settings = Settings()
            data_config = DataManagerConfig(
                cache_duration_minutes=30,
                max_concurrent_requests=3,
                request_delay_seconds=1.0,
                auto_refresh=True,
                refresh_interval_minutes=15
            )
            
            self.data_manager = ComprehensiveDataManager(settings, data_config)
            
            if not await self.data_manager.initialize():
                logger.error("Failed to initialize data manager")
                return 1
            
            # Route to appropriate command
            if args.command == 'connect':
                return await self._connect_server(args)
            elif args.command == 'connect-all':
                return await self._connect_all_servers(args)
            elif args.command == 'analyze-and-create':
                return await self._analyze_and_create_bots(args)
            elif args.command == 'summary':
                return await self._get_summary()
            elif args.command == 'status':
                return await self._get_status()
            elif args.command == 'refresh':
                return await self._refresh_data(args)
            else:
                logger.error(f"Unknown command: {args.command}")
                return 1
                
        except Exception as e:
            logger.error(f"Error in data manager CLI: {e}")
            return 1
        finally:
            if self.data_manager:
                await self.data_manager.shutdown()
    
    async def _connect_server(self, args: argparse.Namespace) -> int:
        """Connect to a specific server"""
        try:
            logger.info(f"Connecting to server {args.server}...")
            
            if await self.data_manager.connect_to_server(args.server):
                logger.info(f"✅ Successfully connected to {args.server}")
                
                if args.fetch_data:
                    logger.info("Fetching all server data...")
                    if await self.data_manager.fetch_all_server_data(args.server):
                        logger.info("✅ Successfully fetched all data")
                    else:
                        logger.error("❌ Failed to fetch data")
                        return 1
                
                return 0
            else:
                logger.error(f"❌ Failed to connect to {args.server}")
                return 1
                
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            return 1
    
    async def _connect_all_servers(self, args: argparse.Namespace) -> int:
        """Connect to all available servers"""
        try:
            servers = ["srv01", "srv02", "srv03"]
            connected_count = 0
            
            for server in servers:
                logger.info(f"Connecting to {server}...")
                if await self.data_manager.connect_to_server(server):
                    logger.info(f"✅ Connected to {server}")
                    connected_count += 1
                    
                    if args.fetch_data:
                        logger.info(f"Fetching data from {server}...")
                        await self.data_manager.fetch_all_server_data(server)
                else:
                    logger.warning(f"⚠️ Failed to connect to {server}")
            
            logger.info(f"Connected to {connected_count}/{len(servers)} servers")
            return 0 if connected_count > 0 else 1
            
        except Exception as e:
            logger.error(f"Error connecting to servers: {e}")
            return 1
    
    async def _analyze_and_create_bots(self, args: argparse.Namespace) -> int:
        """Analyze labs and create bots"""
        try:
            logger.info(f"Analyzing labs on {args.server}...")
            
            # Get qualifying backtests
            qualifying_backtests = await self.data_manager.get_qualifying_backtests(
                args.server,
                min_winrate=args.min_winrate,
                max_drawdown=args.max_drawdown,
                min_trades=args.min_trades
            )
            
            if not qualifying_backtests:
                logger.info("No qualifying backtests found")
                return 0
            
            logger.info(f"Found {len(qualifying_backtests)} qualifying backtests")
            
            # Display top results
            logger.info("Top qualifying backtests:")
            for i, bt in enumerate(qualifying_backtests[:5]):
                logger.info(f"  {i+1}. {bt['roe']:.1f}% ROE, {bt['winrate']:.1f}% WR, {bt['trades']} trades")
            
            # Create bots
            logger.info(f"Creating up to {args.max_bots} bots...")
            created_bots = await self.data_manager.create_bots_from_qualifying_backtests(
                args.server,
                qualifying_backtests,
                max_bots=args.max_bots
            )
            
            logger.info(f"✅ Created {len(created_bots)} bots")
            for bot in created_bots:
                logger.info(f"  - {bot['bot_name']} (ID: {bot['bot_id']})")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error analyzing and creating bots: {e}")
            return 1
    
    async def _get_summary(self) -> int:
        """Get server data summary"""
        try:
            summary = await self.data_manager.get_server_summary()
            
            logger.info("Server Data Summary:")
            logger.info("=" * 50)
            
            for server_name, data in summary.items():
                logger.info(f"\n{server_name.upper()}:")
                logger.info(f"  Status: {data['status']}")
                logger.info(f"  Labs: {data['labs_count']}")
                logger.info(f"  Bots: {data['bots_count']}")
                logger.info(f"  Accounts: {data['accounts_count']}")
                logger.info(f"  Backtests: {data['backtests_count']}")
                if data['last_updated']:
                    logger.info(f"  Last Updated: {data['last_updated']}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return 1
    
    async def _get_status(self) -> int:
        """Get server status"""
        try:
            # This would use the server manager to get status
            logger.info("Server Status:")
            logger.info("=" * 30)
            
            # For now, show data manager status
            summary = await self.data_manager.get_server_summary()
            
            for server_name, data in summary.items():
                status_icon = "✅" if data['status'] == 'connected' else "❌"
                logger.info(f"{status_icon} {server_name}: {data['status']}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return 1
    
    async def _refresh_data(self, args: argparse.Namespace) -> int:
        """Refresh data from servers"""
        try:
            if args.server:
                # Refresh specific server
                logger.info(f"Refreshing data from {args.server}...")
                if await self.data_manager.fetch_all_server_data(args.server):
                    logger.info(f"✅ Refreshed data from {args.server}")
                    return 0
                else:
                    logger.error(f"❌ Failed to refresh data from {args.server}")
                    return 1
            else:
                # Refresh all connected servers
                logger.info("Refreshing data from all connected servers...")
                refreshed_count = 0
                
                for server_name in self.data_manager.active_connections:
                    if await self.data_manager.fetch_all_server_data(server_name):
                        logger.info(f"✅ Refreshed {server_name}")
                        refreshed_count += 1
                    else:
                        logger.warning(f"⚠️ Failed to refresh {server_name}")
                
                logger.info(f"Refreshed {refreshed_count} servers")
                return 0
                
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            return 1


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Data Manager CLI")
    args = parser.parse_args()
    
    # Create CLI instance
    from ..cli.base import CLIConfig
    config = CLIConfig()
    cli = DataManagerCLI(config)
    
    # Create parser and parse args
    cli_parser = cli.create_parser()
    args = cli_parser.parse_args()
    
    # Run CLI
    return await cli.run(args)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
