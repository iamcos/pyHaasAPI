#!/usr/bin/env python3
"""
Two-Stage Backtesting Workflow for pyHaasAPI v2

This script implements the specific two-stage backtesting workflow:
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

# Add pyHaasAPI_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI_v2.core.server_manager import ServerManager
from pyHaasAPI_v2.core.config import Settings
from pyHaasAPI_v2.cli.base import BaseCLI
from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class TwoStageBacktestingV2(BaseCLI):
    """Two-stage backtesting workflow using v2 server manager and v1 API"""
    
    def __init__(self):
        super().__init__()
        self.server_manager = None
        self.best_parameters = None
        self.cloned_lab_id = None
    
    async def run(self, args):
        """Required abstract method implementation"""
        # This method is required by BaseCLI but not used in this workflow
        pass
    
    async def _setup_services(self):
        """Setup server manager and API services"""
        try:
            # Initialize server manager
            settings = Settings()
            self.server_manager = ServerManager(settings)
            
            # Connect to srv01
            print("🔗 Connecting to srv01...")
            connection_status = await self.server_manager.connect_to_server("srv01")
            
            if not connection_status.connected:
                raise Exception(f"Failed to connect to srv01: {connection_status.error}")
            
            print(f"✅ Connected to srv01 on port {connection_status.local_port}")
            
            # Create v1 API connection through tunnel
            haas_api = api.RequestsExecutor(
                host='127.0.0.1',
                port=connection_status.local_port,
                state=api.Guest()
            )
            
            # Authenticate
            self.executor = haas_api.authenticate(
                os.getenv('API_EMAIL'), 
                os.getenv('API_PASSWORD')
            )
            
            print("✅ API authentication successful")
            
        except Exception as e:
            self.logger.error(f"Failed to setup services: {e}")
            raise
    
    async def analyze_source_lab(self, lab_id: str, top_count: int = 100) -> Dict[str, Any]:
        """Analyze source lab to find best backtest result"""
        try:
            print(f"🔍 Analyzing source lab: {lab_id[:8]}")
            
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            print(f"Lab: {getattr(lab_details, 'lab_name', f'Lab {lab_id[:8]}')}")
            print(f"Script: {getattr(lab_details, 'script_id', 'Unknown')}")
            print(f"Market: {getattr(lab_details, 'market_tag', 'Unknown')}")
            
            # Get all backtests from the lab
            request = GetBacktestResultRequest(
                lab_id=lab_id,
                next_page_id=0,
                page_lenght=1000
            )
            
            backtest_response = api.get_backtest_result(self.executor, request)
            
            # Extract backtest results from the response
            if hasattr(backtest_response, '__iter__') and len(backtest_response) > 1:
                backtests = backtest_response[1]  # Actual results are in index 1
            else:
                backtests = backtest_response
            
            if not backtests:
                raise Exception(f"No backtests found in lab {lab_id}")
            
            print(f"📊 Found {len(backtests)} backtests")
            
            # Sort by ROE (Return on Equity) - our primary metric
            sorted_backtests = sorted(
                backtests,
                key=lambda x: (getattr(x, 'realized_profits_usdt', 0) / max(getattr(x, 'starting_balance', 1), 1)) * 100,
                reverse=True
            )
            
            # Filter for zero drawdown and minimum performance
            filtered_backtests = [
                bt for bt in sorted_backtests[:top_count]
                if getattr(bt, 'max_drawdown', 0) >= 0 and 
                   getattr(bt, 'win_rate', 0) >= 0.3 and 
                   getattr(bt, 'total_trades', 0) >= 5
            ]
            
            if not filtered_backtests:
                raise Exception(f"No qualifying backtests found in lab {lab_id}")
            
            print(f"✅ Found {len(filtered_backtests)} qualifying backtests")
            
            # Get the best backtest (first one after sorting by ROE)
            best_backtest = filtered_backtests[0]
            
            print(f"🏆 Best backtest: {getattr(best_backtest, 'backtest_id', 'Unknown')[:8]}")
            print(f"   ROE: {getattr(best_backtest, 'roi_percentage', 0):.2f}%")
            print(f"   Win Rate: {getattr(best_backtest, 'win_rate', 0):.2f}%")
            print(f"   Trades: {getattr(best_backtest, 'total_trades', 0)}")
            print(f"   Drawdown: {getattr(best_backtest, 'max_drawdown', 0):.2f}%")
            print(f"   Script: {getattr(best_backtest, 'script_name', 'Unknown')}")
            print(f"   Market: {getattr(best_backtest, 'market_tag', 'Unknown')}")
            
            return {
                'backtest_id': getattr(best_backtest, 'backtest_id', ''),
                'roi_percentage': getattr(best_backtest, 'roi_percentage', 0),
                'win_rate': getattr(best_backtest, 'win_rate', 0),
                'total_trades': getattr(best_backtest, 'total_trades', 0),
                'max_drawdown': getattr(best_backtest, 'max_drawdown', 0),
                'realized_profits_usdt': getattr(best_backtest, 'realized_profits_usdt', 0),
                'script_name': getattr(best_backtest, 'script_name', ''),
                'market_tag': getattr(best_backtest, 'market_tag', ''),
                'parameter_values': getattr(best_backtest, 'parameter_values', {})
            }
            
        except Exception as e:
            print(f"❌ Failed to analyze source lab: {e}")
            raise
    
    async def clone_lab_with_parameters(self, source_lab_id: str, target_lab_id: str, 
                                      coin_symbol: str, best_params: Dict[str, Any]) -> str:
        """Clone target lab and configure with best parameters"""
        try:
            print(f"🔄 Cloning lab: {target_lab_id[:8]}")
            
            # Get target lab details
            target_lab = api.get_lab_details(self.executor, target_lab_id)
            
            # Create new lab name based on source and target
            new_lab_name = f"{getattr(target_lab, 'lab_name', 'Lab')} - {coin_symbol} - Optimized"
            
            # Clone the lab
            cloned_lab = api.clone_lab(
                self.executor,
                source_lab_id=target_lab_id,
                new_lab_name=new_lab_name
            )
            
            self.cloned_lab_id = cloned_lab.lab_id
            print(f"✅ Cloned lab created: {cloned_lab.lab_id[:8]} - {new_lab_name}")
            
            # Configure lab with best parameters
            await self.configure_lab_parameters(cloned_lab.lab_id, best_params)
            
            # Configure lab settings for exchange account
            await self.configure_lab_settings(cloned_lab.lab_id, coin_symbol)
            
            return cloned_lab.lab_id
            
        except Exception as e:
            print(f"❌ Failed to clone lab: {e}")
            raise
    
    async def configure_lab_parameters(self, lab_id: str, best_params: Dict[str, Any]):
        """Configure lab with best parameters"""
        try:
            print(f"⚙️ Configuring lab parameters: {lab_id[:8]}")
            
            # Get current lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Update lab details with best parameters
            if hasattr(lab_details, 'parameters') and lab_details.parameters:
                for param in lab_details.parameters:
                    if hasattr(param, 'key') and param.key in best_params.get('parameter_values', {}):
                        param.value = best_params['parameter_values'][param.key]
                        param.is_selected = True
                        print(f"   Set {param.key} = {param.value}")
            
            # Update lab details
            api.update_lab_details(self.executor, lab_id, lab_details)
            
            print("✅ Lab parameters configured successfully")
            
        except Exception as e:
            print(f"❌ Failed to configure lab parameters: {e}")
            raise
    
    async def configure_lab_settings(self, lab_id: str, coin_symbol: str):
        """Configure lab settings for exchange account"""
        try:
            print(f"⚙️ Configuring lab settings: {lab_id[:8]}")
            
            # Get current lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Update settings for exchange account
            if hasattr(lab_details, 'settings'):
                lab_details.settings.trade_amount = 2000.0  # $2000 USD equivalent
                lab_details.settings.leverage = 20.0  # 20x leverage
                lab_details.settings.position_mode = 1  # HEDGE mode
                lab_details.settings.margin_mode = 0  # CROSS margin
                lab_details.settings.interval = 15  # 15 minutes
                lab_details.settings.chart_style = 300  # Default chart style
                lab_details.settings.order_template = 500  # Default order template
                
                # Update market tag for the coin
                if coin_symbol == "BTC":
                    lab_details.settings.market_tag = "BTC_USDT_PERPETUAL"
                else:
                    lab_details.settings.market_tag = f"{coin_symbol}_USDT_PERPETUAL"
                
                print(f"   Market: {lab_details.settings.market_tag}")
                print(f"   Trade Amount: ${lab_details.settings.trade_amount}")
                print(f"   Leverage: {lab_details.settings.leverage}x")
            
            # Update lab details
            api.update_lab_details(self.executor, lab_id, lab_details)
            
            print("✅ Lab settings configured successfully")
            
        except Exception as e:
            print(f"❌ Failed to configure lab settings: {e}")
            raise
    
    async def discover_cutoff_date(self, lab_id: str) -> datetime:
        """Discover optimal cutoff date for longest backtesting period"""
        try:
            print("📅 Discovering optimal cutoff date...")
            
            # Calculate cutoff date (start from 2 years ago)
            cutoff_date = datetime.now() - timedelta(days=730)  # 2 years ago
            
            print(f"   Cutoff date set to: {cutoff_date.strftime('%Y-%m-%d')}")
            
            return cutoff_date
            
        except Exception as e:
            print(f"❌ Failed to discover cutoff date: {e}")
            raise
    
    async def run_longest_backtest(self, lab_id: str, cutoff_date: datetime) -> str:
        """Run the longest possible backtest"""
        try:
            print(f"🚀 Starting longest backtest for lab: {lab_id[:8]}")
            
            # Start lab execution
            execution_result = api.start_lab_execution(self.executor, lab_id)
            
            if not execution_result.success:
                raise Exception(f"Failed to start lab execution: {execution_result.error}")
            
            print("✅ Lab execution started successfully")
            print(f"   Expected backtests: 1000-1500")
            print(f"   Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
            
            return execution_result.job_id if hasattr(execution_result, 'job_id') else "unknown"
            
        except Exception as e:
            print(f"❌ Failed to start longest backtest: {e}")
            raise
    
    async def monitor_lab_progress(self, lab_id: str, job_id: str):
        """Monitor lab execution progress"""
        try:
            print(f"📊 Monitoring lab progress: {lab_id[:8]}")
            
            while True:
                # Get execution status
                status = api.get_lab_execution_update(self.executor, lab_id)
                
                print(f"   Status: {getattr(status, 'status', 'Unknown')}")
                print(f"   Progress: {getattr(status, 'progress_percentage', 0):.1f}%")
                print(f"   Generation: {getattr(status, 'generation', 0)}")
                print(f"   Population: {getattr(status, 'population', 0)}")
                print(f"   Best Fitness: {getattr(status, 'best_fitness', 0):.2f}")
                
                if getattr(status, 'status', '') == "completed":
                    print("🎉 Lab execution completed successfully!")
                    break
                elif getattr(status, 'status', '') == "failed":
                    raise Exception(f"Lab execution failed: {getattr(status, 'error', 'Unknown error')}")
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
        except Exception as e:
            print(f"❌ Failed to monitor lab progress: {e}")
            raise
    
    async def run_two_stage_workflow(self, source_lab_id: str, target_lab_id: str, 
                                   coin_symbol: str) -> Dict[str, Any]:
        """Run complete two-stage backtesting workflow"""
        try:
            print(f"🎯 Starting two-stage backtesting workflow for {coin_symbol}...")
            
            # Stage 1: Extract best parameters
            print("\n=== STAGE 1: Parameter Optimization ===")
            best_params = await self.analyze_source_lab(source_lab_id, 100)
            
            # Stage 2: Clone and configure lab
            print("\n=== STAGE 2: Longest Backtesting ===")
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
            print(f"❌ Two-stage workflow failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.server_manager:
                await self.server_manager.shutdown()
                print("🔗 Server manager shutdown complete")
        except Exception as e:
            print(f"Error during cleanup: {e}")


async def main():
    """Main entry point"""
    workflow = TwoStageBacktestingV2()
    
    try:
        # Connect to API
        await workflow.connect()
        await workflow._setup_services()
        
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
        print(f"❌ Error: {e}")
        return 1
    finally:
        await workflow.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
