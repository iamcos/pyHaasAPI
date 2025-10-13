"""
Main entry point for the refactored CLI system.
Provides unified access to all CLI modules with centralized managers.
"""

import asyncio
import argparse
import sys
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.cli_ref.orchestrator_cli import OrchestratorCLI
from pyHaasAPI.cli_ref.backtest_workflow_cli import BacktestWorkflowCLI
from pyHaasAPI.cli_ref.cache_analysis_cli import CacheAnalysisCLI
from pyHaasAPI.cli_ref.data_manager_cli import DataManagerCLI
from pyHaasAPI.cli_ref.project_manager_cli import ProjectManagerCLI
from pyHaasAPI.core.logging import get_logger


class RefactoredCLI(EnhancedBaseCLI):
    """Main refactored CLI with all functionality"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("refactored_cli")

    async def run(self, args: List[str]) -> int:
        """Run the refactored CLI with the given arguments"""
        try:
            parser = argparse.ArgumentParser(description="Refactored CLI System")
            
            # Workflow commands
            parser.add_argument("--workflow", action="store_true", help="Run comprehensive workflow")
            parser.add_argument("--lab-ids", type=str, help="Comma-separated list of lab IDs")
            parser.add_argument("--min-winrate", type=float, default=55.0, help="Minimum winrate (default: 55.0)")
            parser.add_argument("--sort-by", type=str, default="roe", choices=["roi", "roe", "winrate"], help="Sort by metric (default: roe)")
            parser.add_argument("--bots-per-lab", type=int, default=2, help="Bots per lab (default: 2)")
            
            # Analysis commands
            parser.add_argument("--analyze-lab", type=str, help="Analyze specific lab")
            parser.add_argument("--analyze-all-labs", action="store_true", help="Analyze all labs")
            
            # Bot creation commands
            parser.add_argument("--create-bot", nargs=5, metavar=("BACKTEST_ID", "LAB_NAME", "SCRIPT_NAME", "ROI", "WIN_RATE"), help="Create bot from backtest")
            parser.add_argument("--create-bots-from-analysis", action="store_true", help="Create bots from analysis results")
            
            # Help
            parser.add_argument("--help-detailed", action="store_true", help="Show detailed help")
            
            parsed_args = parser.parse_args(args)
            
            # Show detailed help
            if parsed_args.help_detailed:
                self.print_help()
                return 0
            
            # Connect
            if not await self.connect():
                print("❌ Failed to connect to APIs")
                return 1
            
            try:
                if parsed_args.workflow:
                    # Run comprehensive workflow
                    lab_ids = parsed_args.lab_ids.split(',') if parsed_args.lab_ids else None
                    result = await self.run_comprehensive_workflow(
                        lab_ids=lab_ids,
                        min_winrate=parsed_args.min_winrate,
                        sort_by=parsed_args.sort_by,
                        bots_per_lab=parsed_args.bots_per_lab
                    )
                    
                    if result.get("success"):
                        print("✅ Comprehensive workflow completed successfully")
                    else:
                        print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
                        
                elif parsed_args.analyze_lab:
                    # Analyze specific lab
                    result = await self.analyze_lab_with_zero_drawdown(parsed_args.analyze_lab, parsed_args.min_winrate, parsed_args.sort_by)
                    self.print_analysis_report(result)
                    
                elif parsed_args.analyze_all_labs:
                    # Analyze all labs
                    result = await self.analyze_all_labs_with_zero_drawdown(parsed_args.min_winrate, parsed_args.sort_by)
                    self.print_analysis_report(result)
                    
                elif parsed_args.create_bot:
                    # Create bot from backtest
                    backtest_id, lab_name, script_name, roi_str, win_rate_str = parsed_args.create_bot
                    try:
                        roi = float(roi_str)
                        win_rate = float(win_rate_str)
                    except ValueError:
                        print("❌ Invalid ROI or win rate values")
                        return 1
                    
                    result = await self.create_bot_from_backtest(backtest_id, lab_name, script_name, roi, win_rate)
                    self.print_bot_creation_report([result])
                    
                elif parsed_args.create_bots_from_analysis:
                    # Create bots from analysis (requires previous analysis)
                    print("❌ This command requires previous analysis results. Use --workflow instead.")
                    
                else:
                    parser.print_help()
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return 1
            finally:
                await self.disconnect()
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    async def run_comprehensive_workflow(self, lab_ids: List[str] = None, 
                                        min_winrate: float = 55.0, 
                                        sort_by: str = "roe", 
                                        bots_per_lab: int = 2) -> Dict[str, Any]:
        """Run the comprehensive analysis and bot creation workflow"""
        try:
            self.logger.info("Starting comprehensive workflow")
            
            # Use the enhanced base CLI workflow
            result = await self.run_comprehensive_analysis_and_bot_creation(
                lab_ids=lab_ids,
                min_winrate=min_winrate,
                sort_by=sort_by,
                bots_per_lab=bots_per_lab
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def print_help(self):
        """Print comprehensive help"""
        print("\n" + "="*80)
        print("🚀 REFACTORED CLI SYSTEM")
        print("="*80)
        print("This is the refactored CLI system with centralized managers and v2 APIs.")
        print("\n📋 Available Commands:")
        print("  python -m pyHaasAPI.cli_ref.main --help")
        print("  python -m pyHaasAPI.cli_ref.account_cli --help")
        print("  python -m pyHaasAPI.cli_ref.backtest_cli --help")
        print("  python -m pyHaasAPI.cli_ref.market_cli --help")
        print("  python -m pyHaasAPI.cli_ref.order_cli --help")
        print("  python -m pyHaasAPI.cli_ref.script_cli --help")
        print("  python -m pyHaasAPI.cli_ref.orchestrator_cli --help")
        print("  python -m pyHaasAPI.cli_ref.backtest_workflow_cli --help")
        print("  python -m pyHaasAPI.cli_ref.cache_analysis_cli --help")
        print("  python -m pyHaasAPI.cli_ref.data_manager_cli --help")
        print("  python -m pyHaasAPI.cli_ref.project_manager_cli --help")
        print("\n🔄 Comprehensive Workflow:")
        print("  python -m pyHaasAPI.cli_ref.main --workflow")
        print("  python -m pyHaasAPI.cli_ref.main --workflow --lab-ids LAB1,LAB2")
        print("  python -m pyHaasAPI.cli_ref.main --workflow --min-winrate 60 --sort-by roi")
        print("\n📊 Analysis Commands:")
        print("  python -m pyHaasAPI.cli_ref.main --analyze-lab LAB_ID")
        print("  python -m pyHaasAPI.cli_ref.main --analyze-all-labs")
        print("\n🤖 Bot Creation Commands:")
        print("  python -m pyHaasAPI.cli_ref.main --create-bot BACKTEST_ID LAB_NAME SCRIPT_NAME ROI WIN_RATE")
        print("  python -m pyHaasAPI.cli_ref.main --create-bots-from-analysis")
        print("\n📋 Project Manager Commands (Server Content Revision):")
        print("  python -m pyHaasAPI.cli_ref.project_manager_cli snapshot --servers srv03")
        print("  python -m pyHaasAPI.cli_ref.project_manager_cli fetch --servers srv03 --count 5")
        print("  python -m pyHaasAPI.cli_ref.project_manager_cli analyze --servers srv03 --min-winrate 0.55")
        print("  python -m pyHaasAPI.cli_ref.project_manager_cli create-bots --servers srv03 --bots-per-lab 1")
        print("  python -m pyHaasAPI.cli_ref.project_manager_cli run --servers srv03")
        print("="*80)


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Refactored CLI System")
    
    # Workflow commands
    parser.add_argument("--workflow", action="store_true", help="Run comprehensive workflow")
    parser.add_argument("--lab-ids", type=str, help="Comma-separated list of lab IDs")
    parser.add_argument("--min-winrate", type=float, default=55.0, help="Minimum winrate (default: 55.0)")
    parser.add_argument("--sort-by", type=str, default="roe", choices=["roi", "roe", "winrate"], help="Sort by metric (default: roe)")
    parser.add_argument("--bots-per-lab", type=int, default=2, help="Bots per lab (default: 2)")
    
    # Analysis commands
    parser.add_argument("--analyze-lab", type=str, help="Analyze specific lab")
    parser.add_argument("--analyze-all-labs", action="store_true", help="Analyze all labs")
    
    # Bot creation commands
    parser.add_argument("--create-bot", nargs=5, metavar=("BACKTEST_ID", "LAB_NAME", "SCRIPT_NAME", "ROI", "WIN_RATE"), help="Create bot from backtest")
    parser.add_argument("--create-bots-from-analysis", action="store_true", help="Create bots from analysis results")
    
    # Help
    parser.add_argument("--help-detailed", action="store_true", help="Show detailed help")
    
    args = parser.parse_args()
    
    cli = RefactoredCLI()
    
    # Show detailed help
    if args.help_detailed:
        cli.print_help()
        return
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        if args.workflow:
            # Run comprehensive workflow
            lab_ids = args.lab_ids.split(',') if args.lab_ids else None
            result = await cli.run_comprehensive_workflow(
                lab_ids=lab_ids,
                min_winrate=args.min_winrate,
                sort_by=args.sort_by,
                bots_per_lab=args.bots_per_lab
            )
            
            if result.get("success"):
                print("✅ Comprehensive workflow completed successfully")
            else:
                print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
                
        elif args.analyze_lab:
            # Analyze specific lab
            result = await cli.analyze_lab_with_zero_drawdown(args.analyze_lab, args.min_winrate, args.sort_by)
            cli.print_analysis_report(result)
            
        elif args.analyze_all_labs:
            # Analyze all labs
            result = await cli.analyze_all_labs_with_zero_drawdown(args.min_winrate, args.sort_by)
            cli.print_analysis_report(result)
            
        elif args.create_bot:
            # Create bot from backtest
            backtest_id, lab_name, script_name, roi_str, win_rate_str = args.create_bot
            try:
                roi = float(roi_str)
                win_rate = float(win_rate_str)
            except ValueError:
                print("❌ Invalid ROI or win rate values")
                return
            
            result = await cli.create_bot_from_backtest(backtest_id, lab_name, script_name, roi, win_rate)
            cli.print_bot_creation_report([result])
            
        elif args.create_bots_from_analysis:
            # Create bots from analysis (requires previous analysis)
            print("❌ This command requires previous analysis results. Use --workflow instead.")
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
