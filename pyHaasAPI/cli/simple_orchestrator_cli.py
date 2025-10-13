"""
Simple Trading Orchestrator CLI

Command-line interface for multi-server trading orchestration with zero drawdown filtering.
Coordinates multiple servers, coins, and pre-configured labs to create zero-drawdown trading bots.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..core.simple_trading_orchestrator import (
    SimpleTradingOrchestrator,
    SimpleProjectConfig
)
from ..config.settings import Settings
from ..core.logging import get_logger
from ..exceptions import OrchestrationError


class SimpleOrchestratorCLI:
    """CLI for Simple Trading Orchestrator"""
    
    def __init__(self):
        self.logger = get_logger("simple_orchestrator_cli")
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI"""
        parser = argparse.ArgumentParser(
            description="Simple Trading Orchestrator - Multi-server trading orchestration with zero drawdown filtering",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic orchestration with default settings
  python -m pyHaasAPI.cli.simple_orchestrator_cli execute --project-name "MyProject" --base-labs lab1,lab2,lab3
  
  # Custom configuration
  python -m pyHaasAPI.cli.simple_orchestrator_cli execute --project-name "CustomProject" \\
    --servers srv01,srv02 --coins BTC,ETH --base-labs lab1,lab2 \\
    --min-stability-score 80 --top-bots-per-coin 5 --activate-bots
  
  # Dry run to test configuration
  python -m pyHaasAPI.cli.simple_orchestrator_cli execute --project-name "TestProject" \\
    --base-labs lab1,lab2 --dry-run
  
  # Load configuration from file
  python -m pyHaasAPI.cli.simple_orchestrator_cli execute --config-file config.json
            """
        )
        
        # Global options
        parser.add_argument(
            "--config-file",
            type=str,
            help="Load configuration from JSON file"
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="trading_projects",
            help="Output directory for project results (default: trading_projects)"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Execute command
        execute_parser = subparsers.add_parser("execute", help="Execute trading orchestration project")
        self._add_execute_arguments(execute_parser)
        
        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Validate configuration without execution")
        self._add_validate_arguments(validate_parser)
        
        # Status command
        status_parser = subparsers.add_parser("status", help="Check project status")
        self._add_status_arguments(status_parser)
        
        return parser
    
    def _add_execute_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add arguments for execute command"""
        # Project configuration
        parser.add_argument(
            "--project-name",
            type=str,
            required=True,
            help="Name of the trading project"
        )
        parser.add_argument(
            "--servers",
            type=str,
            default="srv01,srv02,srv03",
            help="Comma-separated list of servers (default: srv01,srv02,srv03)"
        )
        parser.add_argument(
            "--coins",
            type=str,
            default="BTC,ETH,TRX,ADA",
            help="Comma-separated list of coins (default: BTC,ETH,TRX,ADA)"
        )
        parser.add_argument(
            "--base-labs",
            type=str,
            required=True,
            help="Comma-separated list of base lab IDs to clone"
        )
        
        # Trading configuration
        parser.add_argument(
            "--account-type",
            type=str,
            default="BINANCEFUTURES_USDT",
            help="Account type (default: BINANCEFUTURES_USDT)"
        )
        parser.add_argument(
            "--trade-amount-usdt",
            type=float,
            default=2000.0,
            help="Trade amount in USDT (default: 2000.0)"
        )
        parser.add_argument(
            "--leverage",
            type=float,
            default=20.0,
            help="Leverage (default: 20.0)"
        )
        
        # Filtering configuration
        parser.add_argument(
            "--max-drawdown-threshold",
            type=float,
            default=0.0,
            help="Maximum drawdown threshold (default: 0.0 - zero drawdown only)"
        )
        parser.add_argument(
            "--min-win-rate",
            type=float,
            default=0.6,
            help="Minimum win rate (default: 0.6)"
        )
        parser.add_argument(
            "--min-trades",
            type=int,
            default=10,
            help="Minimum number of trades (default: 10)"
        )
        parser.add_argument(
            "--min-stability-score",
            type=float,
            default=70.0,
            help="Minimum stability score (default: 70.0)"
        )
        parser.add_argument(
            "--top-bots-per-coin",
            type=int,
            default=3,
            help="Number of top bots per coin (default: 3)"
        )
        
        # Execution options
        parser.add_argument(
            "--activate-bots",
            action="store_true",
            help="Activate bots after creation"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run - validate configuration without execution"
        )
    
    def _add_validate_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add arguments for validate command"""
        parser.add_argument(
            "--config-file",
            type=str,
            help="Configuration file to validate"
        )
        parser.add_argument(
            "--project-name",
            type=str,
            help="Project name to validate"
        )
        parser.add_argument(
            "--base-labs",
            type=str,
            help="Base labs to validate"
        )
    
    def _add_status_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add arguments for status command"""
        parser.add_argument(
            "--project-name",
            type=str,
            help="Project name to check status for"
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="trading_projects",
            help="Output directory to check"
        )
    
    def load_config_from_file(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Loaded configuration from {config_file}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_file}: {e}")
            raise
    
    def create_config_from_args(self, args: argparse.Namespace) -> SimpleProjectConfig:
        """Create configuration from command line arguments"""
        # Parse comma-separated lists
        servers = [s.strip() for s in args.servers.split(",")]
        coins = [c.strip() for c in args.coins.split(",")]
        base_labs = [l.strip() for l in args.base_labs.split(",")]
        
        config = SimpleProjectConfig(
            project_name=args.project_name,
            servers=servers,
            coins=coins,
            base_labs=base_labs,
            account_type=args.account_type,
            trade_amount_usdt=args.trade_amount_usdt,
            leverage=args.leverage,
            max_drawdown_threshold=args.max_drawdown_threshold,
            min_win_rate=args.min_win_rate,
            min_trades=args.min_trades,
            min_stability_score=args.min_stability_score,
            top_bots_per_coin=args.top_bots_per_coin,
            activate_bots=args.activate_bots,
            output_directory=args.output_dir
        )
        
        return config
    
    def create_settings(self) -> Settings:
        """Create settings from environment variables"""
        return Settings(
            email="",  # Will be loaded from environment
            password="",  # Will be loaded from environment
            host="127.0.0.1",
            port=8090
        )
    
    async def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the orchestration project"""
        try:
            self.logger.info("🚀 Starting Simple Trading Orchestrator")
            
            # Load configuration
            if args.config_file:
                config_dict = self.load_config_from_file(args.config_file)
                config = SimpleProjectConfig(**config_dict)
            else:
                config = self.create_config_from_args(args)
            
            # Create settings
            settings = self.create_settings()
            
            # Validate configuration
            self._validate_config(config)
            
            if args.dry_run:
                self.logger.info("✅ Configuration validation passed (dry run)")
                self.logger.info(f"Project: {config.project_name}")
                self.logger.info(f"Servers: {config.servers}")
                self.logger.info(f"Coins: {config.coins}")
                self.logger.info(f"Base labs: {config.base_labs}")
                self.logger.info(f"Zero drawdown threshold: {config.max_drawdown_threshold}")
                self.logger.info(f"Min stability score: {config.min_stability_score}")
                return 0
            
            # Create orchestrator
            orchestrator = SimpleTradingOrchestrator(config, settings)
            
            # Execute project
            result = await orchestrator.execute_project()
            
            # Display results
            self._display_results(result)
            
            # Cleanup
            await orchestrator.cleanup()
            
            if result.success:
                self.logger.info("✅ Project execution completed successfully")
                return 0
            else:
                self.logger.error("❌ Project execution failed")
                return 1
                
        except Exception as e:
            self.logger.error(f"❌ Execution failed: {e}")
            return 1
    
    async def validate_command(self, args: argparse.Namespace) -> int:
        """Validate configuration without execution"""
        try:
            self.logger.info("🔍 Validating configuration...")
            
            # Load configuration
            if args.config_file:
                config_dict = self.load_config_from_file(args.config_file)
                config = SimpleProjectConfig(**config_dict)
            else:
                # Create config from args
                config = SimpleProjectConfig(
                    project_name=args.project_name or "test_project",
                    servers=["srv01", "srv02", "srv03"],
                    coins=["BTC", "ETH", "TRX", "ADA"],
                    base_labs=args.base_labs.split(",") if args.base_labs else ["lab1", "lab2"],
                    output_directory="test_projects"
                )
            
            # Validate configuration
            self._validate_config(config)
            
            self.logger.info("✅ Configuration validation passed")
            self.logger.info(f"Project: {config.project_name}")
            self.logger.info(f"Servers: {config.servers}")
            self.logger.info(f"Coins: {config.coins}")
            self.logger.info(f"Base labs: {config.base_labs}")
            self.logger.info(f"Zero drawdown threshold: {config.max_drawdown_threshold}")
            self.logger.info(f"Min stability score: {config.min_stability_score}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ Configuration validation failed: {e}")
            return 1
    
    async def status_command(self, args: argparse.Namespace) -> int:
        """Check project status"""
        try:
            output_dir = Path(args.output_dir)
            project_name = args.project_name
            
            if not output_dir.exists():
                self.logger.info(f"Output directory {output_dir} does not exist")
                return 0
            
            # Look for project files
            result_file = output_dir / f"{project_name}_result.json"
            summary_file = output_dir / f"{project_name}_summary.txt"
            
            if result_file.exists():
                with open(result_file, 'r') as f:
                    result_data = json.load(f)
                
                self.logger.info(f"Project: {result_data.get('project_name', 'Unknown')}")
                self.logger.info(f"Execution time: {result_data.get('execution_timestamp', 'Unknown')}")
                self.logger.info(f"Success: {result_data.get('success', False)}")
                self.logger.info(f"Servers processed: {result_data.get('servers_processed', [])}")
                self.logger.info(f"Labs cloned: {result_data.get('total_labs_cloned', 0)}")
                self.logger.info(f"Backtests executed: {result_data.get('total_backtests_executed', 0)}")
                self.logger.info(f"Bots created: {result_data.get('total_bots_created', 0)}")
                self.logger.info(f"Zero drawdown bots: {result_data.get('zero_drawdown_bots', 0)}")
                self.logger.info(f"Stable bots: {result_data.get('stable_bots', 0)}")
                
                if not result_data.get('success', False):
                    error_msg = result_data.get('error_message', 'Unknown error')
                    self.logger.error(f"Error: {error_msg}")
                
            elif summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary = f.read()
                self.logger.info("Project summary:")
                self.logger.info(summary)
            else:
                self.logger.info(f"No project files found for {project_name}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ Status check failed: {e}")
            return 1
    
    def _validate_config(self, config: SimpleProjectConfig) -> None:
        """Validate configuration"""
        if not config.project_name:
            raise ValueError("Project name is required")
        
        if not config.servers:
            raise ValueError("At least one server is required")
        
        if not config.coins:
            raise ValueError("At least one coin is required")
        
        if not config.base_labs:
            raise ValueError("At least one base lab is required")
        
        if config.max_drawdown_threshold > 0.0:
            raise ValueError("Max drawdown threshold must be <= 0.0 for zero drawdown filtering")
        
        if config.min_stability_score < 0.0 or config.min_stability_score > 100.0:
            raise ValueError("Min stability score must be between 0.0 and 100.0")
        
        if config.trade_amount_usdt <= 0:
            raise ValueError("Trade amount must be positive")
        
        if config.leverage <= 0:
            raise ValueError("Leverage must be positive")
        
        self.logger.info("✅ Configuration validation passed")
    
    def _display_results(self, result) -> None:
        """Display project results"""
        self.logger.info("📊 Project Results:")
        self.logger.info(f"  Project: {result.project_name}")
        self.logger.info(f"  Execution time: {result.execution_timestamp}")
        self.logger.info(f"  Success: {result.success}")
        self.logger.info(f"  Servers processed: {len(result.servers_processed)}")
        self.logger.info(f"  Labs cloned: {result.total_labs_cloned}")
        self.logger.info(f"  Backtests executed: {result.total_backtests_executed}")
        self.logger.info(f"  Bots created: {result.total_bots_created}")
        self.logger.info(f"  Zero drawdown bots: {result.zero_drawdown_bots}")
        self.logger.info(f"  Stable bots: {result.stable_bots}")
        
        if result.error_message:
            self.logger.error(f"  Error: {result.error_message}")
        
        # Display bot results by server
        for server, server_bots in result.bot_results.items():
            self.logger.info(f"  {server}:")
            for coin, coin_bots in server_bots.items():
                self.logger.info(f"    {coin}: {len(coin_bots)} bots")
                for bot in coin_bots:
                    if bot.error_message:
                        self.logger.error(f"      ❌ {bot.bot_name}: {bot.error_message}")
                    else:
                        self.logger.info(f"      ✅ {bot.bot_name}: ROE={bot.roe:.1f}%, WR={bot.win_rate:.1%}, DD={bot.max_drawdown:.1f}%, Stability={bot.stability_score:.1f}")
    
    async def run(self, args: List[str]) -> int:
        """Run the CLI with given arguments"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        try:
            if parsed_args.command == "execute":
                return await self.execute_command(parsed_args)
            elif parsed_args.command == "validate":
                return await self.validate_command(parsed_args)
            elif parsed_args.command == "status":
                return await self.status_command(parsed_args)
            else:
                self.logger.error(f"Unknown command: {parsed_args.command}")
                return 1
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Execution interrupted by user")
            return 1
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            return 1


async def main():
    """Main entry point"""
    cli = SimpleOrchestratorCLI()
    return await cli.run(sys.argv[1:])


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)























