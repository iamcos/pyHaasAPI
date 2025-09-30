#!/usr/bin/env python3
"""
Two-Stage Backtesting CLI for pyHaasAPI v2

This CLI implements a comprehensive two-stage backtesting workflow:
1. Stage 1: Run 100 backtests to identify best parameters
2. Stage 2: Apply best parameters to new lab and run 1000-1500 backtests for longest period

Features:
- Best parameter extraction from source lab
- Lab cloning with parameter configuration
- Cutoff date discovery for longest backtesting
- Exchange account configuration with $2000 USD equivalent
- Multi-coin support (BTC, TRX, etc.)
"""

import asyncio
import argparse
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI_v2.core.client import AsyncHaasClient
from pyHaasAPI_v2.core.auth import AuthenticationManager
from pyHaasAPI_v2.core.config import Settings
from pyHaasAPI_v2.api.lab.lab_api import LabAPI
from pyHaasAPI_v2.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI_v2.api.bot.bot_api import BotAPI
from pyHaasAPI_v2.models.lab import LabConfig, LabSettings, LabParameter
from pyHaasAPI_v2.models.backtest import BacktestAnalysis
from pyHaasAPI_v2.cli.base import BaseCLI
from pyHaasAPI_v2.exceptions import LabError, BacktestError, BotError


@dataclass
class BestParameters:
    """Represents the best parameters extracted from source lab"""
    parameter_values: Dict[str, str]
    backtest_id: str
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    script_name: str
    market_tag: str


@dataclass
class TwoStageConfig:
    """Configuration for two-stage backtesting"""
    source_lab_id: str
    target_lab_id: str
    coin_symbol: str
    stage1_backtests: int = 100
    stage2_backtests: int = 1000
    trade_amount_usd: float = 2000.0
    use_exchange_account: bool = True
    cutoff_date_discovery: bool = True


class TwoStageBacktestingCLI(BaseCLI):
    """CLI for two-stage backtesting workflow"""
    
    def __init__(self):
        super().__init__()
        self.lab_api = None
        self.backtest_api = None
        self.bot_api = None
        self.best_parameters = None
        self.cloned_lab_id = None
    
    async def _setup_services(self):
        """Setup API services"""
        try:
            # Initialize APIs
            self.lab_api = LabAPI(self.client, self.auth_manager)
            self.backtest_api = BacktestAPI(self.client, self.auth_manager)
            self.bot_api = BotAPI(self.client, self.auth_manager)
            
            self.logger.info("Two-stage backtesting services initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup services: {e}")
            raise
    
    async def analyze_source_lab(self, lab_id: str, top_count: int = 100) -> List[BacktestAnalysis]:
        """Analyze source lab to find best backtest results"""
        try:
            self.logger.info(f"Analyzing source lab: {lab_id[:8]}")
            
            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            self.logger.info(f"Lab: {lab_details.lab_name}")
            self.logger.info(f"Script: {lab_details.script_name}")
            self.logger.info(f"Market: {lab_details.market_tag}")
            
            # Get all backtests from the lab
            all_backtests = await self.backtest_api.get_lab_backtests(lab_id)
            
            if not all_backtests:
                raise LabError(f"No backtests found in lab {lab_id}")
            
            self.logger.info(f"Found {len(all_backtests)} backtests")
            
            # Sort by ROE (Return on Equity) - our primary metric
            sorted_backtests = sorted(
                all_backtests,
                key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100,
                reverse=True
            )
            
            # Filter for zero drawdown and minimum performance
            filtered_backtests = [
                bt for bt in sorted_backtests[:top_count]
                if bt.max_drawdown >= 0 and bt.win_rate >= 0.3 and bt.total_trades >= 5
            ]
            
            if not filtered_backtests:
                raise LabError(f"No qualifying backtests found in lab {lab_id}")
            
            self.logger.info(f"Found {len(filtered_backtests)} qualifying backtests")
            
            return filtered_backtests
            
        except Exception as e:
            self.logger.error(f"Failed to analyze source lab: {e}")
            raise
    
    async def extract_best_parameters(self, lab_id: str, top_count: int = 100) -> BestParameters:
        """Extract best parameters from source lab"""
        try:
            self.logger.info("Extracting best parameters from source lab...")
            
            # Analyze source lab
            backtests = await self.analyze_source_lab(lab_id, top_count)
            
            if not backtests:
                raise LabError("No qualifying backtests found")
            
            # Get the best backtest
            best_backtest = backtests[0]
            
            self.logger.info(f"Best backtest: {best_backtest.backtest_id[:8]}")
            self.logger.info(f"ROE: {best_backtest.roi_percentage:.2f}%")
            self.logger.info(f"Win Rate: {best_backtest.win_rate:.2f}%")
            self.logger.info(f"Trades: {best_backtest.total_trades}")
            self.logger.info(f"Drawdown: {best_backtest.max_drawdown:.2f}%")
            
            # Extract parameter values
            parameter_values = {}
            if best_backtest.parameter_values:
                parameter_values = best_backtest.parameter_values
            else:
                # Try to extract from backtest data
                backtest_data = await self.backtest_api.get_backtest_runtime_data(
                    lab_id, best_backtest.backtest_id
                )
                if backtest_data and 'parameters' in backtest_data:
                    parameter_values = backtest_data['parameters']
            
            if not parameter_values:
                self.logger.warning("No parameter values found in best backtest")
                parameter_values = {}
            
            self.logger.info(f"Extracted {len(parameter_values)} parameters")
            for key, value in parameter_values.items():
                self.logger.info(f"  {key}: {value}")
            
            best_params = BestParameters(
                parameter_values=parameter_values,
                backtest_id=best_backtest.backtest_id,
                roi_percentage=best_backtest.roi_percentage,
                win_rate=best_backtest.win_rate,
                total_trades=best_backtest.total_trades,
                max_drawdown=best_backtest.max_drawdown,
                realized_profits_usdt=best_backtest.realized_profits_usdt,
                script_name=best_backtest.script_name,
                market_tag=best_backtest.market_tag
            )
            
            self.best_parameters = best_params
            return best_params
            
        except Exception as e:
            self.logger.error(f"Failed to extract best parameters: {e}")
            raise
    
    async def clone_lab_with_parameters(self, source_lab_id: str, target_lab_id: str, 
                                     coin_symbol: str, best_params: BestParameters) -> str:
        """Clone target lab and configure with best parameters"""
        try:
            self.logger.info(f"Cloning lab: {target_lab_id[:8]}")
            
            # Get target lab details
            target_lab = await self.lab_api.get_lab_details(target_lab_id)
            
            # Create new lab name based on source and target
            new_lab_name = f"{target_lab.lab_name} - {coin_symbol} - Optimized"
            
            # Clone the lab
            cloned_lab = await self.lab_api.clone_lab(
                source_lab_id=target_lab_id,
                new_lab_name=new_lab_name,
                new_market_tag=f"{coin_symbol}_USDT_PERPETUAL" if coin_symbol != "BTC" else "BTC_USDT_PERPETUAL"
            )
            
            self.cloned_lab_id = cloned_lab.lab_id
            self.logger.info(f"Cloned lab created: {cloned_lab.lab_id[:8]} - {new_lab_name}")
            
            # Configure lab with best parameters
            await self.configure_lab_parameters(cloned_lab.lab_id, best_params)
            
            # Configure lab settings for exchange account
            await self.configure_lab_settings(cloned_lab.lab_id, coin_symbol)
            
            return cloned_lab.lab_id
            
        except Exception as e:
            self.logger.error(f"Failed to clone lab: {e}")
            raise
    
    async def configure_lab_parameters(self, lab_id: str, best_params: BestParameters):
        """Configure lab with best parameters"""
        try:
            self.logger.info(f"Configuring lab parameters: {lab_id[:8]}")
            
            # Get current lab parameters
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Update parameters with best values
            updated_parameters = []
            for param in lab_details.parameters:
                if param.key in best_params.parameter_values:
                    param.value = best_params.parameter_values[param.key]
                    param.is_selected = True
                    self.logger.info(f"  Set {param.key} = {param.value}")
                updated_parameters.append(param)
            
            # Update lab parameters
            await self.lab_api.update_lab_parameters(lab_id, updated_parameters)
            
            self.logger.info("Lab parameters configured successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to configure lab parameters: {e}")
            raise
    
    async def configure_lab_settings(self, lab_id: str, coin_symbol: str):
        """Configure lab settings for exchange account"""
        try:
            self.logger.info(f"Configuring lab settings: {lab_id[:8]}")
            
            # Create lab settings
            settings = LabSettings(
                trade_amount=2000.0,  # $2000 USD equivalent
                leverage=20.0,  # 20x leverage
                position_mode=1,  # HEDGE mode
                margin_mode=0,  # CROSS margin
                interval=15,  # 15 minutes
                chart_style=300,  # Default chart style
                order_template=500  # Default order template
            )
            
            # Update lab settings
            await self.lab_api.update_lab_settings(lab_id, settings)
            
            # Configure lab for maximum backtests
            config = LabConfig(
                max_parallel=10,  # Maximum parallel backtests
                max_generations=100,  # High generation count
                max_epochs=15,  # High epoch count for 1000-1500 backtests
                max_runtime=0,  # No time limit
                auto_restart=1  # Auto restart enabled
            )
            
            await self.lab_api.ensure_lab_config_parameters(lab_id, config)
            
            self.logger.info("Lab settings configured successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to configure lab settings: {e}")
            raise
    
    async def discover_cutoff_date(self, lab_id: str) -> datetime:
        """Discover optimal cutoff date for longest backtesting period"""
        try:
            self.logger.info("Discovering optimal cutoff date...")
            
            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Set history depth to maximum (24 months)
            await self.backtest_api.set_history_depth(lab_details.market_tag, 24)
            
            # Calculate cutoff date (start from 2 years ago)
            cutoff_date = datetime.now() - timedelta(days=730)  # 2 years ago
            
            self.logger.info(f"Cutoff date set to: {cutoff_date.strftime('%Y-%m-%d')}")
            
            return cutoff_date
            
        except Exception as e:
            self.logger.error(f"Failed to discover cutoff date: {e}")
            raise
    
    async def run_longest_backtest(self, lab_id: str, cutoff_date: datetime) -> str:
        """Run the longest possible backtest"""
        try:
            self.logger.info(f"Starting longest backtest for lab: {lab_id[:8]}")
            
            # Start lab execution
            execution_result = await self.lab_api.start_lab_execution(lab_id)
            
            if not execution_result.success:
                raise LabError(f"Failed to start lab execution: {execution_result.error}")
            
            self.logger.info("Lab execution started successfully")
            self.logger.info(f"Expected backtests: 1000-1500")
            self.logger.info(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
            
            return execution_result.job_id
            
        except Exception as e:
            self.logger.error(f"Failed to start longest backtest: {e}")
            raise
    
    async def monitor_lab_progress(self, lab_id: str, job_id: str):
        """Monitor lab execution progress"""
        try:
            self.logger.info(f"Monitoring lab progress: {lab_id[:8]}")
            
            while True:
                # Get execution status
                status = await self.lab_api.get_lab_execution_status(lab_id)
                
                self.logger.info(f"Status: {status.status}")
                self.logger.info(f"Progress: {status.progress_percentage:.1f}%")
                self.logger.info(f"Generation: {status.generation}")
                self.logger.info(f"Population: {status.population}")
                self.logger.info(f"Best Fitness: {status.best_fitness:.2f}")
                
                if status.status == "completed":
                    self.logger.info("Lab execution completed successfully!")
                    break
                elif status.status == "failed":
                    raise LabError(f"Lab execution failed: {status.error}")
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
        except Exception as e:
            self.logger.error(f"Failed to monitor lab progress: {e}")
            raise
    
    async def run_two_stage_workflow(self, config: TwoStageConfig) -> Dict[str, Any]:
        """Run complete two-stage backtesting workflow"""
        try:
            self.logger.info("Starting two-stage backtesting workflow...")
            
            # Stage 1: Extract best parameters
            self.logger.info("=== STAGE 1: Parameter Optimization ===")
            best_params = await self.extract_best_parameters(
                config.source_lab_id, 
                config.stage1_backtests
            )
            
            # Stage 2: Clone and configure lab
            self.logger.info("=== STAGE 2: Longest Backtesting ===")
            cloned_lab_id = await self.clone_lab_with_parameters(
                config.source_lab_id,
                config.target_lab_id,
                config.coin_symbol,
                best_params
            )
            
            # Discover cutoff date
            cutoff_date = await self.discover_cutoff_date(cloned_lab_id)
            
            # Run longest backtest
            job_id = await self.run_longest_backtest(cloned_lab_id, cutoff_date)
            
            # Monitor progress
            await self.monitor_lab_progress(cloned_lab_id, job_id)
            
            # Return results
            return {
                'success': True,
                'source_lab_id': config.source_lab_id,
                'target_lab_id': config.target_lab_id,
                'cloned_lab_id': cloned_lab_id,
                'best_parameters': best_params,
                'cutoff_date': cutoff_date.isoformat(),
                'job_id': job_id,
                'coin_symbol': config.coin_symbol
            }
            
        except Exception as e:
            self.logger.error(f"Two-stage workflow failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Two-Stage Backtesting CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Two-stage workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run two-stage backtesting workflow')
    workflow_parser.add_argument('--source-lab', required=True, help='Source lab ID for parameter extraction')
    workflow_parser.add_argument('--target-lab', required=True, help='Target lab ID to clone')
    workflow_parser.add_argument('--coin', required=True, help='Coin symbol (BTC, TRX, etc.)')
    workflow_parser.add_argument('--stage1-backtests', type=int, default=100, help='Number of backtests for stage 1')
    workflow_parser.add_argument('--stage2-backtests', type=int, default=1000, help='Number of backtests for stage 2')
    workflow_parser.add_argument('--trade-amount', type=float, default=2000.0, help='Trade amount in USD')
    
    # Analyze source lab command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze source lab for best parameters')
    analyze_parser.add_argument('--lab-id', required=True, help='Lab ID to analyze')
    analyze_parser.add_argument('--top-count', type=int, default=100, help='Number of top backtests to analyze')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = TwoStageBacktestingCLI()
    
    try:
        # Connect to server
        await cli.connect()
        await cli._setup_services()
        
        if args.command == 'workflow':
            # Create config
            config = TwoStageConfig(
                source_lab_id=args.source_lab,
                target_lab_id=args.target_lab,
                coin_symbol=args.coin,
                stage1_backtests=args.stage1_backtests,
                stage2_backtests=args.stage2_backtests,
                trade_amount_usd=args.trade_amount
            )
            
            # Run workflow
            result = await cli.run_two_stage_workflow(config)
            
            if result['success']:
                print(f"✅ Two-stage workflow completed successfully!")
                print(f"Cloned lab: {result['cloned_lab_id']}")
                print(f"Best parameters extracted from: {result['best_parameters'].backtest_id}")
                print(f"Cutoff date: {result['cutoff_date']}")
            else:
                print(f"❌ Workflow failed: {result['error']}")
                return 1
        
        elif args.command == 'analyze':
            # Analyze source lab
            best_params = await cli.extract_best_parameters(args.lab_id, args.top_count)
            
            print(f"✅ Best parameters extracted:")
            print(f"Backtest ID: {best_params.backtest_id}")
            print(f"ROE: {best_params.roi_percentage:.2f}%")
            print(f"Win Rate: {best_params.win_rate:.2f}%")
            print(f"Parameters: {best_params.parameter_values}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

