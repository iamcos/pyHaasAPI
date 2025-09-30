#!/usr/bin/env python3
"""
Comprehensive Backtesting CLI

Command-line interface for the comprehensive backtesting manager.
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Add pyHaasAPI_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from comprehensive_backtesting_manager import (
    ComprehensiveBacktestingManager,
    ProjectConfig,
    BacktestStep,
    LabConfig,
    CoinConfig
)


class ComprehensiveBacktestingCLI:
    """CLI for comprehensive backtesting manager"""
    
    def __init__(self):
        self.manager = None
    
    async def run(self, args):
        """Main CLI entry point"""
        try:
            if args.command == "create-project":
                await self.create_project(args)
            elif args.command == "run-project":
                await self.run_project(args)
            elif args.command == "analyze-results":
                await self.analyze_results(args)
            elif args.command == "list-projects":
                await self.list_projects(args)
            else:
                print(f"Unknown command: {args.command}")
                return 1
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    async def create_project(self, args):
        """Create a new backtesting project"""
        try:
            print("🏗️ Creating new backtesting project...")
            
            # Parse lab IDs
            lab_ids = args.lab_ids.split(',') if args.lab_ids else []
            lab_configs = []
            
            for i, lab_id in enumerate(lab_ids):
                lab_configs.append(LabConfig(
                    lab_id=lab_id.strip(),
                    lab_name=f"Lab {i+1}",
                    script_id="",  # Will be filled from lab details
                    market_tag="BTC_USDT_PERPETUAL",  # Default
                    priority=i+1
                ))
            
            # Parse coin symbols
            coin_symbols = args.coins.split(',') if args.coins else ['BTC', 'TRX']
            coin_configs = []
            
            for i, symbol in enumerate(coin_symbols):
                coin_configs.append(CoinConfig(
                    symbol=symbol.strip(),
                    market_tag=f"{symbol.strip()}_USDT_PERPETUAL",
                    priority=i+1
                ))
            
            # Create project configuration
            project_config = ProjectConfig(
                project_name=args.name or "Backtesting Project",
                description=args.description or "Multi-lab backtesting project",
                steps=[
                    BacktestStep(
                        step_id="step1",
                        name="Parameter Optimization",
                        lab_configs=lab_configs,
                        coin_configs=coin_configs,
                        analysis_criteria={
                            'min_win_rate': args.min_win_rate,
                            'min_trades': args.min_trades,
                            'max_drawdown': args.max_drawdown,
                            'min_roe': args.min_roe,
                            'top_count': args.top_count,
                            'top_configs': args.top_configs
                        },
                        max_iterations=args.max_iterations,
                        cutoff_days=args.cutoff_days
                    )
                ],
                global_settings={
                    'trade_amount': args.trade_amount,
                    'leverage': args.leverage,
                    'position_mode': 1,
                    'margin_mode': 0
                },
                output_directory=args.output_dir or "backtesting_results"
            )
            
            # Save project configuration
            project_file = Path(args.output_dir or "backtesting_results") / f"{project_config.project_name}_config.json"
            project_file.parent.mkdir(exist_ok=True)
            
            with open(project_file, 'w') as f:
                json.dump(project_config.__dict__, f, indent=2, default=str)
            
            print(f"✅ Project created: {project_file}")
            print(f"   Labs: {len(lab_configs)}")
            print(f"   Coins: {len(coin_configs)}")
            print(f"   Output: {project_config.output_directory}")
            
        except Exception as e:
            print(f"❌ Failed to create project: {e}")
            return 1
    
    async def run_project(self, args):
        """Run a backtesting project"""
        try:
            print("🚀 Running backtesting project...")
            
            # Load project configuration
            project_file = Path(args.config_file)
            if not project_file.exists():
                print(f"❌ Project file not found: {project_file}")
                return 1
            
            with open(project_file, 'r') as f:
                config_data = json.load(f)
            
            # Create project config
            project_config = ProjectConfig(**config_data)
            
            # Create and run manager
            manager = ComprehensiveBacktestingManager(project_config)
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
            print(f"❌ Failed to run project: {e}")
            return 1
    
    async def analyze_results(self, args):
        """Analyze project results"""
        try:
            print("📊 Analyzing project results...")
            
            # Load results
            results_file = Path(args.results_file)
            if not results_file.exists():
                print(f"❌ Results file not found: {results_file}")
                return 1
            
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            # Print analysis
            print(f"\n📋 Project: {results.get('project_name', 'Unknown')}")
            print(f"⏱️ Duration: {results.get('start_time', 'Unknown')} - {results.get('end_time', 'Unknown')}")
            print(f"✅ Success: {results.get('success', False)}")
            
            # Step analysis
            steps = results.get('steps', {})
            print(f"\n📊 Steps Completed: {len(steps)}")
            
            for step_id, step_result in steps.items():
                print(f"   {step_id}: {step_result.get('name', 'Unknown')} - Success: {step_result.get('success', False)}")
            
            # Final analysis
            final_analysis = results.get('final_analysis', {})
            if final_analysis:
                print(f"\n🏆 Final Analysis:")
                print(f"   Total configurations: {final_analysis.get('total_configurations_analyzed', 0)}")
                
                top_configs = final_analysis.get('overall_top_configurations', [])
                if top_configs:
                    print(f"   Top configurations:")
                    for i, config in enumerate(top_configs[:5], 1):
                        print(f"     {i}. {config.get('lab_name', 'Unknown')} - {config.get('coin_symbol', 'Unknown')} - ROE: {config.get('best_roe', 0):.2f}%")
                
                recommendations = final_analysis.get('final_recommendations', [])
                if recommendations:
                    print(f"   Recommendations:")
                    for rec in recommendations:
                        print(f"     • {rec}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to analyze results: {e}")
            return 1
    
    async def list_projects(self, args):
        """List available projects"""
        try:
            print("📋 Available projects:")
            
            output_dir = Path(args.output_dir or "backtesting_results")
            if not output_dir.exists():
                print("   No projects found")
                return 0
            
            # Find project files
            project_files = list(output_dir.glob("*_config.json"))
            
            if not project_files:
                print("   No projects found")
                return 0
            
            for project_file in project_files:
                try:
                    with open(project_file, 'r') as f:
                        config = json.load(f)
                    
                    print(f"   📁 {config.get('project_name', 'Unknown')}")
                    print(f"      Description: {config.get('description', 'No description')}")
                    print(f"      Steps: {len(config.get('steps', []))}")
                    print(f"      File: {project_file}")
                    
                except Exception as e:
                    print(f"   ❌ Error reading {project_file}: {e}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to list projects: {e}")
            return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Backtesting Manager CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create project command
    create_parser = subparsers.add_parser('create-project', help='Create a new backtesting project')
    create_parser.add_argument('--name', help='Project name')
    create_parser.add_argument('--description', help='Project description')
    create_parser.add_argument('--lab-ids', help='Comma-separated lab IDs')
    create_parser.add_argument('--coins', help='Comma-separated coin symbols (default: BTC,TRX)')
    create_parser.add_argument('--min-win-rate', type=float, default=0.3, help='Minimum win rate (default: 0.3)')
    create_parser.add_argument('--min-trades', type=int, default=5, help='Minimum trades (default: 5)')
    create_parser.add_argument('--max-drawdown', type=float, default=50.0, help='Maximum drawdown (default: 50.0)')
    create_parser.add_argument('--min-roe', type=float, default=10.0, help='Minimum ROE (default: 10.0)')
    create_parser.add_argument('--top-count', type=int, default=10, help='Top count for analysis (default: 10)')
    create_parser.add_argument('--top-configs', type=int, default=5, help='Top configurations to keep (default: 5)')
    create_parser.add_argument('--max-iterations', type=int, default=1000, help='Maximum iterations (default: 1000)')
    create_parser.add_argument('--cutoff-days', type=int, default=730, help='Cutoff days (default: 730)')
    create_parser.add_argument('--trade-amount', type=float, default=2000.0, help='Trade amount (default: 2000.0)')
    create_parser.add_argument('--leverage', type=float, default=20.0, help='Leverage (default: 20.0)')
    create_parser.add_argument('--output-dir', help='Output directory (default: backtesting_results)')
    
    # Run project command
    run_parser = subparsers.add_parser('run-project', help='Run a backtesting project')
    run_parser.add_argument('--config-file', required=True, help='Project configuration file')
    
    # Analyze results command
    analyze_parser = subparsers.add_parser('analyze-results', help='Analyze project results')
    analyze_parser.add_argument('--results-file', required=True, help='Results file to analyze')
    
    # List projects command
    list_parser = subparsers.add_parser('list-projects', help='List available projects')
    list_parser.add_argument('--output-dir', help='Output directory (default: backtesting_results)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run CLI
    cli = ComprehensiveBacktestingCLI()
    exit_code = asyncio.run(cli.run(args))
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
