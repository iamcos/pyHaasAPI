#!/usr/bin/env python3
"""
Comprehensive Backtesting Manager

A complete system for multi-lab backtesting with analysis between steps to identify top configurations.
Uses existing pyHaasAPI tools for backtesting and analysis.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI import api
from pyHaasAPI.analysis import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.tools.utils import BacktestFetcher, BacktestFetchConfig
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


@dataclass
class LabConfig:
    """Configuration for a lab in the backtesting project"""
    lab_id: str
    lab_name: str
    script_id: str
    market_tag: str
    priority: int = 1  # Higher number = higher priority
    enabled: bool = True


@dataclass
class CoinConfig:
    """Configuration for a coin in the backtesting project"""
    symbol: str
    market_tag: str
    priority: int = 1  # Higher number = higher priority
    enabled: bool = True


@dataclass
class BacktestStep:
    """A single backtesting step in the project"""
    step_id: str
    name: str
    lab_configs: List[LabConfig]
    coin_configs: List[CoinConfig]
    analysis_criteria: Dict[str, Any]
    max_iterations: int = 1000
    cutoff_days: int = 730  # 2 years
    enabled: bool = True


@dataclass
class AnalysisResult:
    """Result of analysis between backtesting steps"""
    step_id: str
    top_configs: List[Dict[str, Any]]
    analysis_timestamp: str
    total_backtests_analyzed: int
    qualifying_backtests: int
    best_roe: float
    best_win_rate: float
    recommendations: List[str]


@dataclass
class ProjectConfig:
    """Complete project configuration"""
    project_name: str
    description: str
    steps: List[BacktestStep]
    global_settings: Dict[str, Any]
    output_directory: str = "backtesting_results"


class ComprehensiveBacktestingManager:
    """Comprehensive manager for multi-lab backtesting with analysis"""
    
    def __init__(self, project_config: ProjectConfig):
        self.project_config = project_config
        self.cache_manager = UnifiedCacheManager()
        self.analyzer = HaasAnalyzer(self.cache_manager)
        self.api_executor = None
        self.results = {}
        self.analysis_results = {}
        
    async def initialize(self):
        """Initialize the manager and connect to API"""
        try:
            print("🚀 Initializing Comprehensive Backtesting Manager...")
            
            # Create API connection
            haas_api = api.RequestsExecutor(
                host='127.0.0.1',
                port=8090,
                state=api.Guest()
            )
            
            # Authenticate
            self.api_executor = haas_api.authenticate(
                os.getenv('API_EMAIL'), 
                os.getenv('API_PASSWORD')
            )
            
            # Connect analyzer
            self.analyzer.connect()
            
            print("✅ Manager initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize manager: {e}")
            raise
    
    async def execute_project(self) -> Dict[str, Any]:
        """Execute the complete backtesting project"""
        try:
            print(f"🎯 Starting project: {self.project_config.project_name}")
            print(f"📋 Description: {self.project_config.description}")
            print(f"📊 Steps: {len(self.project_config.steps)}")
            
            project_results = {
                'project_name': self.project_config.project_name,
                'start_time': datetime.now().isoformat(),
                'steps': {},
                'final_analysis': {},
                'success': True
            }
            
            # Execute each step
            for i, step in enumerate(self.project_config.steps, 1):
                if not step.enabled:
                    print(f"⏭️ Skipping disabled step: {step.name}")
                    continue
                
                print(f"\n{'='*60}")
                print(f"🔄 STEP {i}/{len(self.project_config.steps)}: {step.name}")
                print(f"{'='*60}")
                
                try:
                    # Execute step
                    step_result = await self.execute_step(step)
                    project_results['steps'][step.step_id] = step_result
                    
                    # Analyze results if not the last step
                    if i < len(self.project_config.steps):
                        analysis_result = await self.analyze_step_results(step, step_result)
                        self.analysis_results[step.step_id] = analysis_result
                        project_results['analysis'][step.step_id] = analysis_result
                        
                        # Update next step with analysis results
                        if i < len(self.project_config.steps):
                            await self.update_next_step_config(step, analysis_result)
                    
                except Exception as e:
                    print(f"❌ Step {step.name} failed: {e}")
                    project_results['steps'][step.step_id] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Final analysis
            print(f"\n{'='*60}")
            print("📊 FINAL PROJECT ANALYSIS")
            print(f"{'='*60}")
            
            final_analysis = await self.perform_final_analysis()
            project_results['final_analysis'] = final_analysis
            
            project_results['end_time'] = datetime.now().isoformat()
            project_results['success'] = True
            
            # Save results
            await self.save_project_results(project_results)
            
            return project_results
            
        except Exception as e:
            print(f"❌ Project execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'end_time': datetime.now().isoformat()
            }
    
    async def execute_step(self, step: BacktestStep) -> Dict[str, Any]:
        """Execute a single backtesting step"""
        try:
            print(f"🔄 Executing step: {step.name}")
            print(f"   Labs: {len(step.lab_configs)}")
            print(f"   Coins: {len(step.coin_configs)}")
            print(f"   Max iterations: {step.max_iterations}")
            
            step_results = {
                'step_id': step.step_id,
                'name': step.name,
                'start_time': datetime.now().isoformat(),
                'lab_results': {},
                'success': True
            }
            
            # Process each lab configuration
            for lab_config in step.lab_configs:
                if not lab_config.enabled:
                    continue
                
                print(f"\n   🔬 Processing lab: {lab_config.lab_name}")
                
                try:
                    # Analyze lab and get top backtests
                    lab_analysis = await self.analyze_lab_for_step(lab_config, step)
                    
                    # Create optimized labs for each coin
                    for coin_config in step.coin_configs:
                        if not coin_config.enabled:
                            continue
                        
                        print(f"      💰 Creating optimized lab for {coin_config.symbol}")
                        
                        # Create optimized lab
                        optimized_lab = await self.create_optimized_lab(
                            lab_config, coin_config, lab_analysis, step
                        )
                        
                        # Run backtest
                        backtest_result = await self.run_backtest_for_lab(
                            optimized_lab, step
                        )
                        
                        # Store results
                        lab_key = f"{lab_config.lab_id}_{coin_config.symbol}"
                        step_results['lab_results'][lab_key] = {
                            'lab_config': asdict(lab_config),
                            'coin_config': asdict(coin_config),
                            'optimized_lab': optimized_lab,
                            'backtest_result': backtest_result,
                            'success': True
                        }
                        
                        print(f"      ✅ {coin_config.symbol} backtest completed")
                
                except Exception as e:
                    print(f"      ❌ Lab {lab_config.lab_name} failed: {e}")
                    step_results['lab_results'][lab_config.lab_id] = {
                        'success': False,
                        'error': str(e)
                    }
            
            step_results['end_time'] = datetime.now().isoformat()
            return step_results
            
        except Exception as e:
            print(f"❌ Step execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'end_time': datetime.now().isoformat()
            }
    
    async def analyze_lab_for_step(self, lab_config: LabConfig, step: BacktestStep) -> Dict[str, Any]:
        """Analyze a lab to get top backtests for the step"""
        try:
            print(f"      🔍 Analyzing lab: {lab_config.lab_name}")
            
            # Use BacktestFetcher to get all backtests
            config = BacktestFetchConfig(page_size=100, max_retries=3)
            fetcher = BacktestFetcher(self.api_executor, config)
            
            # Fetch all backtests for the lab
            backtests = fetcher.fetch_all_backtests(lab_config.lab_id)
            
            if not backtests:
                raise Exception(f"No backtests found in lab {lab_config.lab_id}")
            
            print(f"         📊 Found {len(backtests)} backtests")
            
            # Filter and sort by analysis criteria
            filtered_backtests = self.filter_backtests_by_criteria(backtests, step.analysis_criteria)
            
            if not filtered_backtests:
                raise Exception(f"No qualifying backtests found in lab {lab_config.lab_id}")
            
            # Sort by ROE (Return on Equity)
            sorted_backtests = sorted(
                filtered_backtests,
                key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100,
                reverse=True
            )
            
            # Get top performers
            top_count = step.analysis_criteria.get('top_count', 10)
            top_backtests = sorted_backtests[:top_count]
            
            print(f"         ✅ Found {len(top_backtests)} top performers")
            
            return {
                'lab_id': lab_config.lab_id,
                'total_backtests': len(backtests),
                'qualifying_backtests': len(filtered_backtests),
                'top_backtests': [
                    {
                        'backtest_id': bt.backtest_id,
                        'roi_percentage': bt.roi_percentage,
                        'win_rate': bt.win_rate,
                        'total_trades': bt.total_trades,
                        'max_drawdown': bt.max_drawdown,
                        'realized_profits_usdt': bt.realized_profits_usdt,
                        'parameter_values': getattr(bt, 'parameter_values', {})
                    }
                    for bt in top_backtests
                ],
                'best_backtest': {
                    'backtest_id': top_backtests[0].backtest_id,
                    'roi_percentage': top_backtests[0].roi_percentage,
                    'win_rate': top_backtests[0].win_rate,
                    'total_trades': top_backtests[0].total_trades,
                    'max_drawdown': top_backtests[0].max_drawdown,
                    'realized_profits_usdt': top_backtests[0].realized_profits_usdt,
                    'parameter_values': getattr(top_backtests[0], 'parameter_values', {})
                }
            }
            
        except Exception as e:
            print(f"         ❌ Lab analysis failed: {e}")
            raise
    
    def filter_backtests_by_criteria(self, backtests: List, criteria: Dict[str, Any]) -> List:
        """Filter backtests based on analysis criteria"""
        filtered = []
        
        for bt in backtests:
            # Check minimum criteria
            if criteria.get('min_win_rate', 0) > 0 and bt.win_rate < criteria['min_win_rate']:
                continue
            
            if criteria.get('min_trades', 0) > 0 and bt.total_trades < criteria['min_trades']:
                continue
            
            if criteria.get('max_drawdown', 100) < 100 and bt.max_drawdown > criteria['max_drawdown']:
                continue
            
            if criteria.get('min_roe', 0) > 0:
                roe = (bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100
                if roe < criteria['min_roe']:
                    continue
            
            filtered.append(bt)
        
        return filtered
    
    async def create_optimized_lab(self, lab_config: LabConfig, coin_config: CoinConfig, 
                                 lab_analysis: Dict[str, Any], step: BacktestStep) -> Dict[str, Any]:
        """Create an optimized lab for a specific coin"""
        try:
            # Get the best backtest parameters
            best_backtest = lab_analysis['best_backtest']
            
            # Create new lab name
            new_lab_name = f"{lab_config.lab_name} - {coin_config.symbol} - Optimized"
            
            # Clone the original lab
            cloned_lab = api.clone_lab(
                self.api_executor,
                source_lab_id=lab_config.lab_id,
                new_lab_name=new_lab_name
            )
            
            cloned_lab_id = cloned_lab.lab_id
            print(f"         🧬 Cloned lab: {cloned_lab_id[:8]} - {new_lab_name}")
            
            # Configure lab with best parameters
            await self.configure_lab_parameters(cloned_lab_id, best_backtest['parameter_values'])
            
            # Configure lab settings for the coin
            await self.configure_lab_for_coin(cloned_lab_id, coin_config, step)
            
            return {
                'cloned_lab_id': cloned_lab_id,
                'lab_name': new_lab_name,
                'source_lab_id': lab_config.lab_id,
                'coin_symbol': coin_config.symbol,
                'best_parameters': best_backtest['parameter_values'],
                'best_roe': best_backtest['roi_percentage'],
                'best_win_rate': best_backtest['win_rate']
            }
            
        except Exception as e:
            print(f"         ❌ Failed to create optimized lab: {e}")
            raise
    
    async def configure_lab_parameters(self, lab_id: str, best_params: Dict[str, Any]):
        """Configure lab with best parameters"""
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.api_executor, lab_id)
            
            # Update parameters
            if hasattr(lab_details, 'parameters') and lab_details.parameters:
                for param in lab_details.parameters:
                    if hasattr(param, 'key') and param.key in best_params:
                        param.value = best_params[param.key]
                        param.is_selected = True
            
            # Update lab
            api.update_lab_details(self.api_executor, lab_id, lab_details)
            
        except Exception as e:
            print(f"         ❌ Failed to configure parameters: {e}")
            raise
    
    async def configure_lab_for_coin(self, lab_id: str, coin_config: CoinConfig, step: BacktestStep):
        """Configure lab settings for a specific coin"""
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.api_executor, lab_id)
            
            # Update settings
            if hasattr(lab_details, 'settings'):
                lab_details.settings.trade_amount = 2000.0  # $2000 USD
                lab_details.settings.leverage = 20.0  # 20x leverage
                lab_details.settings.position_mode = 1  # HEDGE mode
                lab_details.settings.margin_mode = 0  # CROSS margin
                lab_details.settings.interval = 15  # 15 minutes
                lab_details.settings.market_tag = coin_config.market_tag
            
            # Update lab
            api.update_lab_details(self.api_executor, lab_id, lab_details)
            
        except Exception as e:
            print(f"         ❌ Failed to configure lab for coin: {e}")
            raise
    
    async def run_backtest_for_lab(self, optimized_lab: Dict[str, Any], step: BacktestStep) -> Dict[str, Any]:
        """Run backtest for an optimized lab"""
        try:
            lab_id = optimized_lab['cloned_lab_id']
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=step.cutoff_days)
            
            # Start lab execution
            execution_result = api.start_lab_execution(
                self.api_executor,
                lab_id=lab_id,
                max_parallel=step.max_iterations,
                cutoff_date=cutoff_date
            )
            
            if not execution_result.success:
                raise Exception(f"Failed to start lab execution: {execution_result.error}")
            
            print(f"         🚀 Started backtest: {execution_result.job_id}")
            
            # Monitor progress
            await self.monitor_backtest_progress(lab_id, execution_result.job_id)
            
            return {
                'job_id': execution_result.job_id,
                'cutoff_date': cutoff_date.isoformat(),
                'max_iterations': step.max_iterations,
                'success': True
            }
            
        except Exception as e:
            print(f"         ❌ Backtest failed: {e}")
            raise
    
    async def monitor_backtest_progress(self, lab_id: str, job_id: str):
        """Monitor backtest progress"""
        try:
            while True:
                # Get execution status
                status = api.get_lab_execution_update(self.api_executor, job_id)
                
                print(f"         📊 Progress: {status.progress_percentage:.1f}% - Gen: {status.generation} - Pop: {status.population}")
                
                if status.status == "completed":
                    print("         ✅ Backtest completed successfully!")
                    break
                elif status.status == "failed":
                    raise Exception(f"Backtest failed: {status.error}")
                
                # Wait 30 seconds
                await asyncio.sleep(30)
                
        except Exception as e:
            print(f"         ❌ Progress monitoring failed: {e}")
            raise
    
    async def analyze_step_results(self, step: BacktestStep, step_result: Dict[str, Any]) -> AnalysisResult:
        """Analyze results from a step to identify top configurations"""
        try:
            print(f"📊 Analyzing step results: {step.name}")
            
            all_results = []
            
            # Collect all lab results
            for lab_key, lab_result in step_result.get('lab_results', {}).items():
                if lab_result.get('success', False):
                    all_results.append({
                        'lab_key': lab_key,
                        'optimized_lab': lab_result.get('optimized_lab', {}),
                        'backtest_result': lab_result.get('backtest_result', {})
                    })
            
            # Sort by performance metrics
            sorted_results = sorted(
                all_results,
                key=lambda x: x.get('optimized_lab', {}).get('best_roe', 0),
                reverse=True
            )
            
            # Get top configurations
            top_count = step.analysis_criteria.get('top_configs', 5)
            top_configs = sorted_results[:top_count]
            
            # Generate recommendations
            recommendations = self.generate_recommendations(top_configs, step)
            
            analysis_result = AnalysisResult(
                step_id=step.step_id,
                top_configs=[
                    {
                        'lab_key': config['lab_key'],
                        'lab_name': config['optimized_lab'].get('lab_name', ''),
                        'coin_symbol': config['optimized_lab'].get('coin_symbol', ''),
                        'best_roe': config['optimized_lab'].get('best_roe', 0),
                        'best_win_rate': config['optimized_lab'].get('best_win_rate', 0),
                        'parameters': config['optimized_lab'].get('best_parameters', {})
                    }
                    for config in top_configs
                ],
                analysis_timestamp=datetime.now().isoformat(),
                total_backtests_analyzed=len(all_results),
                qualifying_backtests=len(top_configs),
                best_roe=max([config['optimized_lab'].get('best_roe', 0) for config in top_configs]) if top_configs else 0,
                best_win_rate=max([config['optimized_lab'].get('best_win_rate', 0) for config in top_configs]) if top_configs else 0,
                recommendations=recommendations
            )
            
            print(f"   ✅ Analysis complete: {len(top_configs)} top configurations identified")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Step analysis failed: {e}")
            raise
    
    def generate_recommendations(self, top_configs: List[Dict[str, Any]], step: BacktestStep) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        if not top_configs:
            recommendations.append("No qualifying configurations found")
            return recommendations
        
        # Analyze performance patterns
        avg_roe = sum([config['optimized_lab'].get('best_roe', 0) for config in top_configs]) / len(top_configs)
        avg_win_rate = sum([config['optimized_lab'].get('best_win_rate', 0) for config in top_configs]) / len(top_configs)
        
        recommendations.append(f"Average ROE: {avg_roe:.2f}%")
        recommendations.append(f"Average Win Rate: {avg_win_rate:.2f}%")
        
        # Coin performance analysis
        coin_performance = {}
        for config in top_configs:
            coin = config['optimized_lab'].get('coin_symbol', 'Unknown')
            if coin not in coin_performance:
                coin_performance[coin] = []
            coin_performance[coin].append(config['optimized_lab'].get('best_roe', 0))
        
        for coin, roes in coin_performance.items():
            avg_coin_roe = sum(roes) / len(roes)
            recommendations.append(f"{coin} average ROE: {avg_coin_roe:.2f}%")
        
        # Top performer
        best_config = top_configs[0]
        recommendations.append(f"Top performer: {best_config['optimized_lab'].get('lab_name', 'Unknown')} - {best_config['optimized_lab'].get('coin_symbol', 'Unknown')} - ROE: {best_config['optimized_lab'].get('best_roe', 0):.2f}%")
        
        return recommendations
    
    async def update_next_step_config(self, current_step: BacktestStep, analysis_result: AnalysisResult):
        """Update next step configuration based on analysis results"""
        # This would update the next step's lab configurations with the best performers
        # Implementation depends on specific requirements
        pass
    
    async def perform_final_analysis(self) -> Dict[str, Any]:
        """Perform final analysis across all steps"""
        try:
            print("📊 Performing final project analysis...")
            
            # Collect all analysis results
            all_top_configs = []
            for step_id, analysis in self.analysis_results.items():
                all_top_configs.extend(analysis.top_configs)
            
            # Sort by ROE
            sorted_configs = sorted(
                all_top_configs,
                key=lambda x: x.get('best_roe', 0),
                reverse=True
            )
            
            # Get overall top performers
            overall_top = sorted_configs[:10]
            
            # Generate final recommendations
            final_recommendations = self.generate_final_recommendations(overall_top)
            
            return {
                'total_configurations_analyzed': len(all_top_configs),
                'overall_top_configurations': overall_top,
                'final_recommendations': final_recommendations,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Final analysis failed: {e}")
            return {'error': str(e)}
    
    def generate_final_recommendations(self, top_configs: List[Dict[str, Any]]) -> List[str]:
        """Generate final recommendations"""
        recommendations = []
        
        if not top_configs:
            recommendations.append("No qualifying configurations found in final analysis")
            return recommendations
        
        # Overall performance
        avg_roe = sum([config.get('best_roe', 0) for config in top_configs]) / len(top_configs)
        avg_win_rate = sum([config.get('best_win_rate', 0) for config in top_configs]) / len(top_configs)
        
        recommendations.append(f"Overall Average ROE: {avg_roe:.2f}%")
        recommendations.append(f"Overall Average Win Rate: {avg_win_rate:.2f}%")
        
        # Best performer
        best = top_configs[0]
        recommendations.append(f"Best Overall Configuration: {best.get('lab_name', 'Unknown')} - {best.get('coin_symbol', 'Unknown')} - ROE: {best.get('best_roe', 0):.2f}%")
        
        # Coin analysis
        coin_performance = {}
        for config in top_configs:
            coin = config.get('coin_symbol', 'Unknown')
            if coin not in coin_performance:
                coin_performance[coin] = []
            coin_performance[coin].append(config.get('best_roe', 0))
        
        recommendations.append("Coin Performance:")
        for coin, roes in coin_performance.items():
            avg_coin_roe = sum(roes) / len(roes)
            recommendations.append(f"  {coin}: {avg_coin_roe:.2f}% ROE ({len(roes)} configurations)")
        
        return recommendations
    
    async def save_project_results(self, project_results: Dict[str, Any]):
        """Save project results to files"""
        try:
            # Create output directory
            output_dir = Path(self.project_config.output_directory)
            output_dir.mkdir(exist_ok=True)
            
            # Save main results
            results_file = output_dir / f"{self.project_config.project_name}_results.json"
            with open(results_file, 'w') as f:
                json.dump(project_results, f, indent=2, default=str)
            
            # Save analysis results
            analysis_file = output_dir / f"{self.project_config.project_name}_analysis.json"
            with open(analysis_file, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            
            print(f"💾 Results saved to: {output_dir}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")


async def main():
    """Main entry point for testing"""
    
    # Define project configuration
    project_config = ProjectConfig(
        project_name="Multi-Lab Backtesting Project",
        description="Comprehensive backtesting with analysis between steps",
        steps=[
            BacktestStep(
                step_id="step1",
                name="Initial Parameter Optimization",
                lab_configs=[
                    LabConfig(
                        lab_id="305d8510-8bf8-4bcf-8004-8f547c3bc530",
                        lab_name="Source Lab",
                        script_id="script123",
                        market_tag="BTC_USDT_PERPETUAL",
                        priority=1
                    )
                ],
                coin_configs=[
                    CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL", priority=1),
                    CoinConfig(symbol="TRX", market_tag="TRX_USDT_PERPETUAL", priority=2)
                ],
                analysis_criteria={
                    'min_win_rate': 0.3,
                    'min_trades': 5,
                    'max_drawdown': 50,
                    'min_roe': 10,
                    'top_count': 10,
                    'top_configs': 5
                },
                max_iterations=1000,
                cutoff_days=730
            )
        ],
        global_settings={
            'trade_amount': 2000.0,
            'leverage': 20.0,
            'position_mode': 1,
            'margin_mode': 0
        }
    )
    
    # Create and run manager
    manager = ComprehensiveBacktestingManager(project_config)
    
    try:
        await manager.initialize()
        results = await manager.execute_project()
        
        print(f"\n{'='*60}")
        print("🎉 PROJECT COMPLETED")
        print(f"{'='*60}")
        print(f"Success: {results.get('success', False)}")
        print(f"Steps completed: {len(results.get('steps', {}))}")
        
        if results.get('success'):
            print("✅ Project completed successfully!")
            return 0
        else:
            print("❌ Project failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
