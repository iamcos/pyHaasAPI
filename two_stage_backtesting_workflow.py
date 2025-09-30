#!/usr/bin/env python3
"""
Two-Stage Backtesting Workflow

This script implements the specific two-stage backtesting workflow requested:
1. Analyze lab 305d8510-8bf8-4bcf-8004-8f547c3bc530 for best parameters
2. Clone lab cc4bb1d8-5ebd-4a65-b5f5-9dfe9790de96 with best parameters
3. Run longest backtest (1000-1500 iterations) with cutoff date discovery
4. Configure for exchange account with $2000 USD equivalent
5. Support for TRX coin as well
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


class TwoStageBacktestingWorkflow:
    """Two-stage backtesting workflow implementation"""
    
    def __init__(self):
        self.analyzer = None
        self.executor = None
        self.cache = None
        self.best_parameters = None
        self.cloned_lab_id = None
    
    async def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            # Get credentials
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                print("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Initialize analyzer and connect
            self.cache = UnifiedCacheManager()
            self.analyzer = HaasAnalyzer(self.cache)
            success = self.analyzer.connect(
                host='127.0.0.1',
                port=8090,
                email=email,
                password=password
            )
            
            if success:
                self.executor = self.analyzer.executor
                print("Successfully connected to HaasOnline API")
                return True
            else:
                print("Failed to connect to HaasOnline API")
                return False
                
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def analyze_source_lab(self, lab_id: str, top_count: int = 100) -> Dict[str, Any]:
        """Analyze source lab to find best backtest result"""
        try:
            print(f"Analyzing source lab: {lab_id[:8]}")
            
            # Get lab details
            from pyHaasAPI.model import GetLabDetailsRequest
            lab_request = GetLabDetailsRequest(lab_id=lab_id)
            lab_details = api.get_lab_details(self.executor, lab_request)
            
            print(f"Lab: {lab_details.lab_name}")
            print(f"Script: {lab_details.script_name}")
            print(f"Market: {lab_details.market_tag}")
            
            # Analyze lab to get best backtests
            result = self.analyzer.analyze_lab(lab_id=lab_id, top_count=top_count)
            
            if not result or not result.top_backtests:
                raise Exception(f"No backtests found in lab {lab_id}")
            
            print(f"Found {len(result.top_backtests)} backtests")
            
            # Get the best backtest (first one after sorting by ROE)
            best_backtest = result.top_backtests[0]
            
            print(f"Best backtest: {best_backtest.backtest_id[:8]}")
            print(f"ROE: {best_backtest.roi_percentage:.2f}%")
            print(f"Win Rate: {best_backtest.win_rate:.2f}%")
            print(f"Trades: {best_backtest.total_trades}")
            print(f"Drawdown: {best_backtest.max_drawdown:.2f}%")
            print(f"Script: {best_backtest.script_name}")
            print(f"Market: {best_backtest.market_tag}")
            
            return {
                'backtest_id': best_backtest.backtest_id,
                'roi_percentage': best_backtest.roi_percentage,
                'win_rate': best_backtest.win_rate,
                'total_trades': best_backtest.total_trades,
                'max_drawdown': best_backtest.max_drawdown,
                'realized_profits_usdt': best_backtest.realized_profits_usdt,
                'script_name': best_backtest.script_name,
                'market_tag': best_backtest.market_tag,
                'parameter_values': getattr(best_backtest, 'parameter_values', {})
            }
            
        except Exception as e:
            print(f"Failed to analyze source lab: {e}")
            raise
    
    async def clone_lab_with_parameters(self, source_lab_id: str, target_lab_id: str, 
                                      coin_symbol: str, best_params: Dict[str, Any]) -> str:
        """Clone target lab and configure with best parameters"""
        try:
            print(f"Cloning target lab: {target_lab_id[:8]}")
            
            # Get target lab details
            from pyHaasAPI.model import GetLabDetailsRequest
            target_request = GetLabDetailsRequest(lab_id=target_lab_id)
            target_lab = api.get_lab_details(self.executor, target_request)
            
            # Create new lab name based on source and target
            new_lab_name = f"{target_lab.lab_name} - {coin_symbol} - Optimized"
            
            # Clone the lab
            from pyHaasAPI.model import CloneLabRequest
            clone_request = CloneLabRequest(
                source_lab_id=target_lab_id,
                new_lab_name=new_lab_name,
                new_market_tag=f"{coin_symbol}_USDT_PERPETUAL" if coin_symbol != "BTC" else "BTC_USDT_PERPETUAL"
            )
            
            cloned_lab = api.clone_lab(self.executor, clone_request)
            
            if not cloned_lab.success:
                raise Exception(f"Failed to clone lab: {cloned_lab.error}")
            
            self.cloned_lab_id = cloned_lab.lab_id
            print(f"Cloned lab created: {cloned_lab.lab_id[:8]} - {new_lab_name}")
            
            # Configure lab with best parameters
            await self.configure_lab_parameters(cloned_lab.lab_id, best_params)
            
            # Configure lab settings for exchange account
            await self.configure_lab_settings(cloned_lab.lab_id, coin_symbol)
            
            return cloned_lab.lab_id
            
        except Exception as e:
            print(f"Failed to clone lab: {e}")
            raise
    
    async def configure_lab_parameters(self, lab_id: str, best_params: Dict[str, Any]):
        """Configure lab with best parameters"""
        try:
            print(f"Configuring lab parameters: {lab_id[:8]}")
            
            # Get current lab parameters
            from pyHaasAPI.model import GetLabDetailsRequest
            lab_request = GetLabDetailsRequest(lab_id=lab_id)
            lab_details = api.get_lab_details(self.executor, lab_request)
            
            # Update parameters with best values
            updated_parameters = []
            for param in lab_details.parameters:
                if param.key in best_params.get('parameter_values', {}):
                    param.value = best_params['parameter_values'][param.key]
                    param.is_selected = True
                    print(f"  Set {param.key} = {param.value}")
                updated_parameters.append(param)
            
            # Update lab parameters
            from pyHaasAPI.model import UpdateLabParametersRequest
            param_request = UpdateLabParametersRequest(
                lab_id=lab_id,
                parameters=updated_parameters
            )
            
            result = api.update_lab_parameters(self.executor, param_request)
            if not result.success:
                raise Exception(f"Failed to update parameters: {result.error}")
            
            print("Lab parameters configured successfully")
            
        except Exception as e:
            print(f"Failed to configure lab parameters: {e}")
            raise
    
    async def configure_lab_settings(self, lab_id: str, coin_symbol: str):
        """Configure lab settings for exchange account"""
        try:
            print(f"Configuring lab settings: {lab_id[:8]}")
            
            # Create lab settings
            from pyHaasAPI.model import LabSettings
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
            from pyHaasAPI.model import UpdateLabSettingsRequest
            settings_request = UpdateLabSettingsRequest(
                lab_id=lab_id,
                settings=settings
            )
            
            result = api.update_lab_settings(self.executor, settings_request)
            if not result.success:
                raise Exception(f"Failed to update settings: {result.error}")
            
            # Configure lab for maximum backtests
            from pyHaasAPI.model import UpdateLabConfigRequest
            config_request = UpdateLabConfigRequest(
                lab_id=lab_id,
                max_parallel=10,  # Maximum parallel backtests
                max_generations=100,  # High generation count
                max_epochs=15,  # High epoch count for 1000-1500 backtests
                max_runtime=0,  # No time limit
                auto_restart=1  # Auto restart enabled
            )
            
            result = api.update_lab_config(self.executor, config_request)
            if not result.success:
                raise Exception(f"Failed to update config: {result.error}")
            
            print("Lab settings configured successfully")
            
        except Exception as e:
            print(f"Failed to configure lab settings: {e}")
            raise
    
    async def discover_cutoff_date(self, lab_id: str) -> datetime:
        """Discover optimal cutoff date for longest backtesting period"""
        try:
            print("Discovering optimal cutoff date...")
            
            # Get lab details
            from pyHaasAPI.model import GetLabDetailsRequest
            lab_request = GetLabDetailsRequest(lab_id=lab_id)
            lab_details = api.get_lab_details(self.executor, lab_request)
            
            # Set history depth to maximum (24 months)
            from pyHaasAPI.model import SetHistoryDepthRequest
            history_request = SetHistoryDepthRequest(
                market_tag=lab_details.market_tag,
                months=24
            )
            
            result = api.set_history_depth(self.executor, history_request)
            if not result.success:
                print(f"Warning: Failed to set history depth: {result.error}")
            
            # Calculate cutoff date (start from 2 years ago)
            cutoff_date = datetime.now() - timedelta(days=730)  # 2 years ago
            
            print(f"Cutoff date set to: {cutoff_date.strftime('%Y-%m-%d')}")
            
            return cutoff_date
            
        except Exception as e:
            print(f"Failed to discover cutoff date: {e}")
            raise
    
    async def run_longest_backtest(self, lab_id: str, cutoff_date: datetime) -> str:
        """Run the longest possible backtest"""
        try:
            print(f"Starting longest backtest for lab: {lab_id[:8]}")
            
            # Start lab execution
            from pyHaasAPI.model import StartLabExecutionRequest
            execution_request = StartLabExecutionRequest(lab_id=lab_id)
            
            execution_result = api.start_lab_execution(self.executor, execution_request)
            
            if not execution_result.success:
                raise Exception(f"Failed to start lab execution: {execution_result.error}")
            
            print("Lab execution started successfully")
            print(f"Expected backtests: 1000-1500")
            print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
            
            return execution_result.job_id
            
        except Exception as e:
            print(f"Failed to start longest backtest: {e}")
            raise
    
    async def monitor_lab_progress(self, lab_id: str, job_id: str):
        """Monitor lab execution progress"""
        try:
            print(f"Monitoring lab progress: {lab_id[:8]}")
            
            while True:
                # Get execution status
                from pyHaasAPI.model import GetLabExecutionStatusRequest
                status_request = GetLabExecutionStatusRequest(lab_id=lab_id)
                
                status = api.get_lab_execution_status(self.executor, status_request)
                
                print(f"Status: {status.status}")
                print(f"Progress: {status.progress_percentage:.1f}%")
                print(f"Generation: {status.generation}")
                print(f"Population: {status.population}")
                print(f"Best Fitness: {status.best_fitness:.2f}")
                
                if status.status == "completed":
                    print("Lab execution completed successfully!")
                    break
                elif status.status == "failed":
                    raise Exception(f"Lab execution failed: {status.error}")
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
        except Exception as e:
            print(f"Failed to monitor lab progress: {e}")
            raise
    
    async def run_two_stage_workflow(self, source_lab_id: str, target_lab_id: str, 
                                   coin_symbol: str) -> Dict[str, Any]:
        """Run complete two-stage backtesting workflow"""
        try:
            print("Starting two-stage backtesting workflow...")
            
            # Stage 1: Extract best parameters
            print("=== STAGE 1: Parameter Optimization ===")
            best_params = await self.analyze_source_lab(source_lab_id, 100)
            
            # Stage 2: Clone and configure lab
            print("=== STAGE 2: Longest Backtesting ===")
            cloned_lab_id = await self.clone_lab_with_parameters(
                source_lab_id,
                target_lab_id,
                coin_symbol,
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
                'source_lab_id': source_lab_id,
                'target_lab_id': target_lab_id,
                'cloned_lab_id': cloned_lab_id,
                'best_parameters': best_params,
                'cutoff_date': cutoff_date.isoformat(),
                'job_id': job_id,
                'coin_symbol': coin_symbol
            }
            
        except Exception as e:
            print(f"Two-stage workflow failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


async def main():
    """Main entry point"""
    workflow = TwoStageBacktestingWorkflow()
    
    try:
        # Connect to API
        if not await workflow.connect():
            return 1
        
        # Run two-stage workflow for BTC
        print("=== RUNNING TWO-STAGE WORKFLOW FOR BTC ===")
        result_btc = await workflow.run_two_stage_workflow(
            source_lab_id="305d8510-8bf8-4bcf-8004-8f547c3bc530",
            target_lab_id="cc4bb1d8-5ebd-4a65-b5f5-9dfe9790de96",
            coin_symbol="BTC"
        )
        
        if result_btc['success']:
            print(f"✅ BTC workflow completed successfully!")
            print(f"Cloned lab: {result_btc['cloned_lab_id']}")
            print(f"Best parameters extracted from: {result_btc['best_parameters']['backtest_id']}")
            print(f"Cutoff date: {result_btc['cutoff_date']}")
        else:
            print(f"❌ BTC workflow failed: {result_btc['error']}")
            return 1
        
        # Run two-stage workflow for TRX
        print("\n=== RUNNING TWO-STAGE WORKFLOW FOR TRX ===")
        result_trx = await workflow.run_two_stage_workflow(
            source_lab_id="305d8510-8bf8-4bcf-8004-8f547c3bc530",
            target_lab_id="cc4bb1d8-5ebd-4a65-b5f5-9dfe9790de96",
            coin_symbol="TRX"
        )
        
        if result_trx['success']:
            print(f"✅ TRX workflow completed successfully!")
            print(f"Cloned lab: {result_trx['cloned_lab_id']}")
            print(f"Best parameters extracted from: {result_trx['best_parameters']['backtest_id']}")
            print(f"Cutoff date: {result_trx['cutoff_date']}")
        else:
            print(f"❌ TRX workflow failed: {result_trx['error']}")
            return 1
        
        print("\n🎉 Both workflows completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

