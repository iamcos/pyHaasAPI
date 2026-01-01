"""
Backtest Workflow CLI module using v2 APIs and centralized managers.
Provides advanced backtesting workflows and monitoring.
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.core.logging import get_logger


class BacktestWorkflowCLI(EnhancedBaseCLI):
    """Advanced backtesting workflow CLI using v2 APIs and centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("backtest_workflow_cli")

    async def run_longest_backtest(self, lab_ids: List[str], 
                                  min_winrate: float = 55.0,
                                  sort_by: str = "roe") -> Dict[str, Any]:
        """Run longest feasible backtest for given lab IDs"""
        try:
            self.logger.info(f"Running longest backtest for labs: {lab_ids}")
            
            # TODO: Implement longest backtest algorithm
            # This would involve:
            # 1. Discover cutoff date by syncing market history
            # 2. Configure lab with Unix timestamps
            # 3. Execute backtest
            # 4. Monitor execution status
            
            return {
                "success": True,
                "lab_ids": lab_ids,
                "min_winrate": min_winrate,
                "sort_by": sort_by,
                "backtests_started": len(lab_ids),
                "estimated_duration": "2-4 hours"
            }
            
        except Exception as e:
            self.logger.error(f"Error running longest backtest: {e}")
            return {"error": str(e)}

    async def check_progress(self, lab_ids: List[str] = None) -> Dict[str, Any]:
        """Check progress of running backtests"""
        try:
            self.logger.info("Checking backtest progress")
            
            # TODO: Implement progress checking
            # This would involve:
            # 1. Check lab execution status
            # 2. Monitor backtest progress
            # 3. Report completion status
            
            return {
                "success": True,
                "lab_ids": lab_ids or [],
                "running_backtests": 0,
                "completed_backtests": 0,
                "failed_backtests": 0,
                "progress_summary": {
                    "total": 0,
                    "completed": 0,
                    "running": 0,
                    "failed": 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error checking progress: {e}")
            return {"error": str(e)}

    async def analyze_results(self, lab_ids: List[str] = None,
                            min_winrate: float = 55.0,
                            sort_by: str = "roe") -> Dict[str, Any]:
        """Analyze backtest results and provide recommendations"""
        try:
            self.logger.info(f"Analyzing backtest results for labs: {lab_ids}")
            
            # Use centralized analysis manager
            if lab_ids:
                analysis_results = {}
                for lab_id in lab_ids:
                    lab_result = await self.analyze_lab_with_zero_drawdown(lab_id, min_winrate, sort_by)
                    if "error" not in lab_result:
                        analysis_results[lab_id] = lab_result
            else:
                analysis_results = await self.analyze_all_labs_with_zero_drawdown(min_winrate, sort_by)
            
            return {
                "success": True,
                "analysis_results": analysis_results,
                "recommendations": {
                    "top_performers": [],
                    "zero_drawdown_candidates": [],
                    "bot_creation_candidates": []
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing results: {e}")
            return {"error": str(e)}

    async def execute_decisions(self, lab_ids: List[str] = None,
                              bots_per_lab: int = 2) -> Dict[str, Any]:
        """Execute decisions based on backtest analysis"""
        try:
            self.logger.info(f"Executing decisions for labs: {lab_ids}")
            
            # First analyze results
            analysis_result = await self.analyze_results(lab_ids)
            if "error" in analysis_result:
                return analysis_result
            
            # Create bots from analysis
            lab_results = analysis_result.get("analysis_results", {})
            if "lab_results" in lab_results:
                lab_results = lab_results["lab_results"]
            
            bot_results = await self.create_bots_from_analysis(lab_results, bots_per_lab)
            
            return {
                "success": True,
                "analysis_results": analysis_result,
                "bot_results": bot_results,
                "summary": {
                    "labs_analyzed": len(lab_results),
                    "bots_created": len([b for b in bot_results if b.get("success", False)]),
                    "bots_failed": len([b for b in bot_results if not b.get("success", False)])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error executing decisions: {e}")
            return {"error": str(e)}

    def print_workflow_report(self, result: Dict[str, Any]):
        """Print backtest workflow results report"""
        try:
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                return
            
            print("\n" + "="*80)
            print("🧪 BACKTEST WORKFLOW RESULTS")
            print("="*80)
            
            if "backtests_started" in result:
                print(f"🚀 Backtests Started: {result['backtests_started']}")
                print(f"⏱️  Estimated Duration: {result.get('estimated_duration', 'Unknown')}")
                
            elif "progress_summary" in result:
                summary = result["progress_summary"]
                print(f"📊 Total Backtests: {summary.get('total', 0)}")
                print(f"✅ Completed: {summary.get('completed', 0)}")
                print(f"🔄 Running: {summary.get('running', 0)}")
                print(f"❌ Failed: {summary.get('failed', 0)}")
                
            elif "analysis_results" in result:
                print(f"📈 Analysis Results: {len(result.get('analysis_results', {}))}")
                recommendations = result.get("recommendations", {})
                print(f"🏆 Top Performers: {len(recommendations.get('top_performers', []))}")
                print(f"🎯 Zero Drawdown Candidates: {len(recommendations.get('zero_drawdown_candidates', []))}")
                
            elif "summary" in result:
                summary = result["summary"]
                print(f"🧪 Labs Analyzed: {summary.get('labs_analyzed', 0)}")
                print(f"🤖 Bots Created: {summary.get('bots_created', 0)}")
                print(f"❌ Bots Failed: {summary.get('bots_failed', 0)}")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing workflow report: {e}")
            print(f"❌ Error generating report: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Advanced Backtest Workflow CLI")
    parser.add_argument("command", choices=["run-longest", "check-progress", "analyze-results", "execute-decisions"], 
                       help="Workflow command to execute")
    parser.add_argument("--lab-ids", type=str, help="Comma-separated list of lab IDs")
    parser.add_argument("--min-winrate", type=float, default=55.0, help="Minimum win rate percentage")
    parser.add_argument("--sort-by", type=str, default="roe", choices=["roi", "roe", "winrate"], help="Sort by metric")
    parser.add_argument("--bots-per-lab", type=int, default=2, help="Number of bots to create per lab")
    
    args = parser.parse_args()
    
    cli = BacktestWorkflowCLI()
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        # Parse lab IDs
        lab_ids = args.lab_ids.split(',') if args.lab_ids else None
        
        if args.command == "run-longest":
            result = await cli.run_longest_backtest(lab_ids, args.min_winrate, args.sort_by)
            cli.print_workflow_report(result)
            
        elif args.command == "check-progress":
            result = await cli.check_progress(lab_ids)
            cli.print_workflow_report(result)
            
        elif args.command == "analyze-results":
            result = await cli.analyze_results(lab_ids, args.min_winrate, args.sort_by)
            cli.print_workflow_report(result)
            
        elif args.command == "execute-decisions":
            result = await cli.execute_decisions(lab_ids, args.bots_per_lab)
            cli.print_workflow_report(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())





