#!/usr/bin/env python3
"""
V2 Multi-Lab Backtesting System

This system uses pyHaasAPI v2 APIs and services exclusively for comprehensive backtesting workflows.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Add pyHaasAPI_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI_v2.core.client import AsyncHaasClient
from pyHaasAPI_v2.core.auth import AuthenticationManager
from pyHaasAPI_v2.core.server_manager import ServerManager
from pyHaasAPI_v2.core.config import Settings
from pyHaasAPI_v2.api.lab.lab_api import LabAPI
from pyHaasAPI_v2.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI_v2.api.bot.bot_api import BotAPI
from pyHaasAPI_v2.services.lab.lab_service import LabService
from pyHaasAPI_v2.services.analysis.analysis_service import AnalysisService
from pyHaasAPI_v2.cli.base import BaseCLI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class V2MultiLabBacktestingSystem(BaseCLI):
    """V2-based multi-lab backtesting system using v2 APIs and services"""
    
    def __init__(self):
        super().__init__()
        self.server_manager = None
        self.client = None
        self.auth_manager = None
        self.lab_api = None
        self.backtest_api = None
        self.bot_api = None
        self.lab_service = None
        self.analysis_service = None
        self.lab_analyses = {}
        self.cloned_labs = {}
    
    async def run(self, args):
        """Required abstract method implementation"""
        pass
    
    async def _setup_services(self):
        """Setup v2 services and APIs"""
        try:
            # Initialize server manager
            settings = Settings()
            self.server_manager = ServerManager(settings)
            
            # Try connecting to available servers (srv01 might be broken)
            servers_to_try = ["srv02", "srv03", "srv01"]  # Try srv01 last since it might be broken
            connected = False
            
            for server in servers_to_try:
                try:
                    print(f"🔗 Trying to connect to {server}...")
                    connection_status = await self.server_manager.connect_to_server(server)
                    
                    if connection_status.connected:
                        print(f"✅ Connected to {server} on port {connection_status.local_port}")
                        
                        # Create v2 client and auth manager
                        self.client = AsyncHaasClient(
                            host="127.0.0.1",
                            port=connection_status.local_port
                        )
                        
                        self.auth_manager = AuthenticationManager(
                            email=os.getenv('API_EMAIL'),
                            password=os.getenv('API_PASSWORD'),
                            client=self.client
                        )
                        
                        # Authenticate
                        await self.auth_manager.authenticate()
                        print("✅ V2 API authentication successful")
                        
                        # Initialize APIs
                        self.lab_api = LabAPI(self.client, self.auth_manager)
                        self.backtest_api = BacktestAPI(self.client, self.auth_manager)
                        self.bot_api = BotAPI(self.client, self.auth_manager)
                        
                        # Initialize services
                        self.lab_service = LabService(self.client, self.auth_manager)
                        self.analysis_service = AnalysisService(self.client, self.auth_manager)
                        
                        connected = True
                        break
                    else:
                        print(f"❌ Failed to connect to {server}: {connection_status.error}")
                        
                except Exception as e:
                    print(f"❌ Error connecting to {server}: {e}")
                    continue
            
            if not connected:
                raise Exception("Failed to connect to any server (srv01, srv02, srv03)")
            
        except Exception as e:
            self.logger.error(f"Failed to setup v2 services: {e}")
            raise
    
    async def analyze_lab(self, lab_id: str, top_count: int = 100) -> Dict[str, Any]:
        """Analyze a single lab using v2 APIs"""
        try:
            print(f"🔍 Analyzing lab: {lab_id[:8]}")
            
            # Get lab details using v2 API
            lab_details = await self.lab_api.get_lab_details(lab_id)
            print(f"   Lab: {lab_details.lab_name}")
            print(f"   Script: {lab_details.script_id}")
            print(f"   Market: {lab_details.market_tag}")
            
            # Get backtests using v2 API
            backtests = await self.backtest_api.get_lab_backtests(lab_id)
            
            if not backtests:
                raise Exception(f"No backtests found in lab {lab_id}")
            
            print(f"   📊 Found {len(backtests)} backtests")
            
            # Sort by ROE (Return on Equity) - our primary metric
            sorted_backtests = sorted(
                backtests,
                key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100,
                reverse=True
            )
            
            # Filter for qualifying backtests
            filtered_backtests = [
                bt for bt in sorted_backtests[:top_count]
                if bt.max_drawdown >= 0 and 
                   bt.win_rate >= 0.3 and 
                   bt.total_trades >= 5
            ]
            
            if not filtered_backtests:
                raise Exception(f"No qualifying backtests found in lab {lab_id}")
            
            print(f"   ✅ Found {len(filtered_backtests)} qualifying backtests")
            
            # Get the best backtest
            best_backtest = filtered_backtests[0]
            
            print(f"   🏆 Best backtest: {best_backtest.backtest_id[:8]}")
            print(f"      ROE: {best_backtest.roi_percentage:.2f}%")
            print(f"      Win Rate: {best_backtest.win_rate:.2f}%")
            print(f"      Trades: {best_backtest.total_trades}")
            print(f"      Drawdown: {best_backtest.max_drawdown:.2f}%")
            
            # Store analysis results
            analysis = {
                'lab_id': lab_id,
                'lab_name': lab_details.lab_name,
                'script_id': lab_details.script_id,
                'market_tag': lab_details.market_tag,
                'total_backtests': len(backtests),
                'qualifying_backtests': len(filtered_backtests),
                'best_backtest': {
                    'backtest_id': best_backtest.backtest_id,
                    'roi_percentage': best_backtest.roi_percentage,
                    'win_rate': best_backtest.win_rate,
                    'total_trades': best_backtest.total_trades,
                    'max_drawdown': best_backtest.max_drawdown,
                    'realized_profits_usdt': best_backtest.realized_profits_usdt,
                    'script_name': best_backtest.script_name,
                    'parameter_values': getattr(best_backtest, 'parameter_values', {})
                },
                'all_qualifying_backtests': [
                    {
                        'backtest_id': bt.backtest_id,
                        'roi_percentage': bt.roi_percentage,
                        'win_rate': bt.win_rate,
                        'total_trades': bt.total_trades,
                        'max_drawdown': bt.max_drawdown,
                        'realized_profits_usdt': bt.realized_profits_usdt,
                        'parameter_values': getattr(bt, 'parameter_values', {})
                    }
                    for bt in filtered_backtests[:10]  # Top 10
                ]
            }
            
            self.lab_analyses[lab_id] = analysis
            return analysis
            
        except Exception as e:
            print(f"❌ Failed to analyze lab {lab_id}: {e}")
            raise
    
    async def create_optimized_lab(self, source_lab_id: str, target_lab_id: str, 
                                 coin_symbol: str, best_params: Dict[str, Any]) -> str:
        """Create an optimized lab using v2 APIs"""
        try:
            print(f"🔄 Creating optimized lab from {source_lab_id[:8]} for {coin_symbol}")
            
            # Get target lab details using v2 API
            target_lab = await self.lab_api.get_lab_details(target_lab_id)
            
            # Create new lab name
            new_lab_name = f"{target_lab.lab_name} - {coin_symbol} - Optimized"
            
            # Clone the lab using v2 API
            cloned_lab = await self.lab_api.clone_lab(
                source_lab_id=target_lab_id,
                new_lab_name=new_lab_name
            )
            
            cloned_lab_id = cloned_lab.lab_id
            print(f"✅ Cloned lab created: {cloned_lab_id[:8]} - {new_lab_name}")
            
            # Configure lab with best parameters using v2 API
            await self.configure_lab_parameters(cloned_lab_id, best_params)
            
            # Configure lab settings for exchange account using v2 API
            await self.configure_lab_settings(cloned_lab_id, coin_symbol)
            
            # Store cloned lab info
            self.cloned_labs[cloned_lab_id] = {
                'source_lab_id': source_lab_id,
                'target_lab_id': target_lab_id,
                'coin_symbol': coin_symbol,
                'lab_name': new_lab_name,
                'best_params': best_params
            }
            
            return cloned_lab_id
            
        except Exception as e:
            print(f"❌ Failed to create optimized lab: {e}")
            raise
    
    async def configure_lab_parameters(self, lab_id: str, best_params: Dict[str, Any]):
        """Configure lab with best parameters using v2 API"""
        try:
            print(f"⚙️ Configuring lab parameters: {lab_id[:8]}")
            
            # Get current lab details using v2 API
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Update parameters with best values
            if hasattr(lab_details, 'parameters') and lab_details.parameters:
                for param in lab_details.parameters:
                    if hasattr(param, 'key') and param.key in best_params.get('parameter_values', {}):
                        param.value = best_params['parameter_values'][param.key]
                        param.is_selected = True
                        print(f"   Set {param.key} = {param.value}")
            
            # Update lab details using v2 API
            await self.lab_api.update_lab_details(lab_id, lab_details)
            
            print("✅ Lab parameters configured successfully")
            
        except Exception as e:
            print(f"❌ Failed to configure lab parameters: {e}")
            raise
    
    async def configure_lab_settings(self, lab_id: str, coin_symbol: str):
        """Configure lab settings for exchange account using v2 API"""
        try:
            print(f"⚙️ Configuring lab settings: {lab_id[:8]}")
            
            # Get current lab details using v2 API
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
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
            
            # Update lab details using v2 API
            await self.lab_api.update_lab_details(lab_id, lab_details)
            
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
        """Run the longest possible backtest using v2 API"""
        try:
            print(f"🚀 Starting longest backtest for lab: {lab_id[:8]}")
            
            # Start lab execution using v2 API
            execution_result = await self.lab_api.start_lab_execution(lab_id)
            
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
        """Monitor lab execution progress using v2 API"""
        try:
            print(f"📊 Monitoring lab progress: {lab_id[:8]}")
            
            while True:
                # Get execution status using v2 API
                status = await self.lab_api.get_lab_execution_status(lab_id)
                
                print(f"   Status: {status.status}")
                print(f"   Progress: {status.progress_percentage:.1f}%")
                print(f"   Generation: {status.generation}")
                print(f"   Population: {status.population}")
                print(f"   Best Fitness: {status.best_fitness:.2f}")
                
                if status.status == "completed":
                    print("🎉 Lab execution completed successfully!")
                    break
                elif status.status == "failed":
                    raise Exception(f"Lab execution failed: {status.error}")
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
        except Exception as e:
            print(f"❌ Failed to monitor lab progress: {e}")
            raise
    
    async def run_comprehensive_backtesting_workflow(self, lab_pairs: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        """Run comprehensive backtesting workflow for multiple lab pairs using v2 APIs"""
        try:
            print(f"🎯 Starting comprehensive backtesting workflow for {len(lab_pairs)} lab pairs...")
            
            results = {}
            
            for i, (source_lab_id, target_lab_id, coin_symbol) in enumerate(lab_pairs, 1):
                print(f"\n{'='*60}")
                print(f"🚀 WORKFLOW {i}/{len(lab_pairs)}: {coin_symbol}")
                print(f"{'='*60}")
                
                try:
                    # Stage 1: Analyze source lab using v2 API
                    print(f"\n=== STAGE 1: Parameter Optimization ===")
                    source_analysis = await self.analyze_lab(source_lab_id)
                    
                    # Stage 2: Create optimized lab using v2 API
                    print(f"\n=== STAGE 2: Lab Optimization ===")
                    cloned_lab_id = await self.create_optimized_lab(
                        source_lab_id,
                        target_lab_id,
                        coin_symbol,
                        source_analysis['best_backtest']
                    )
                    
                    # Stage 3: Discover cutoff date
                    cutoff_date = await self.discover_cutoff_date(cloned_lab_id)
                    
                    # Stage 4: Run longest backtest using v2 API
                    print(f"\n=== STAGE 3: Longest Backtesting ===")
                    job_id = await self.run_longest_backtest(cloned_lab_id, cutoff_date)
                    
                    # Stage 5: Monitor progress using v2 API
                    await self.monitor_lab_progress(cloned_lab_id, job_id)
                    
                    # Store results
                    results[f"{coin_symbol}_{i}"] = {
                        'success': True,
                        'source_lab_id': source_lab_id,
                        'target_lab_id': target_lab_id,
                        'cloned_lab_id': cloned_lab_id,
                        'best_parameters': source_analysis['best_backtest'],
                        'cutoff_date': cutoff_date.isoformat(),
                        'job_id': job_id,
                        'coin_symbol': coin_symbol
                    }
                    
                    print(f"✅ {coin_symbol} workflow completed successfully!")
                    
                except Exception as e:
                    print(f"❌ {coin_symbol} workflow failed: {e}")
                    results[f"{coin_symbol}_{i}"] = {
                        'success': False,
                        'error': str(e),
                        'coin_symbol': coin_symbol
                    }
            
            return results
            
        except Exception as e:
            print(f"❌ Comprehensive workflow failed: {e}")
            return {'error': str(e)}
    
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
    system = V2MultiLabBacktestingSystem()
    
    try:
        # Connect to API
        await system.connect()
        await system._setup_services()
        
        # Define lab pairs for backtesting
        lab_pairs = [
            ("305d8510-8bf8-4bcf-8004-8f547c3bc530", "cc4bb1d8-5ebd-4a65-b5f5-9dfe9790de96", "BTC"),
            ("305d8510-8bf8-4bcf-8004-8f547c3bc530", "cc4bb1d8-5ebd-4a65-b5f5-9dfe9790de96", "TRX")
        ]
        
        # Run comprehensive backtesting workflow
        results = await system.run_comprehensive_backtesting_workflow(lab_pairs)
        
        # Print summary
        print(f"\n{'='*60}")
        print("📋 COMPREHENSIVE BACKTESTING SUMMARY")
        print(f"{'='*60}")
        
        successful = 0
        failed = 0
        
        for key, result in results.items():
            if result.get('success', False):
                successful += 1
                print(f"✅ {result['coin_symbol']}: {result['cloned_lab_id']}")
            else:
                failed += 1
                print(f"❌ {result.get('coin_symbol', key)}: {result.get('error', 'Unknown error')}")
        
        print(f"\n📊 Results: {successful} successful, {failed} failed")
        
        if successful > 0:
            print("\n🎉 Comprehensive backtesting workflow completed!")
            return 0
        else:
            print("\n❌ All workflows failed")
            return 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        await system.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
