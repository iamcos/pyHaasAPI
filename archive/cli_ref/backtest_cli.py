"""
Backtest CLI module using v2 APIs and centralized managers.
Provides backtest management functionality.
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.core.logging import get_logger


class BacktestCLI(EnhancedBaseCLI):
    """Backtest management CLI using v2 APIs and centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("backtest_cli")

    async def list_backtests(self, lab_id: str = None) -> Dict[str, Any]:
        """List backtests for a lab or all labs"""
        try:
            if lab_id:
                self.logger.info(f"Listing backtests for lab {lab_id}")
            else:
                self.logger.info("Listing all backtests")
            
            if not self.backtest_api:
                return {"error": "Backtest API not available"}
            
            if lab_id:
                backtests = await self.backtest_api.list_lab_backtests(lab_id)
            else:
                backtests = await self.backtest_api.list_all_backtests()
            
            return {
                "success": True,
                "backtests": backtests,
                "count": len(backtests) if backtests else 0,
                "lab_id": lab_id
            }
            
        except Exception as e:
            self.logger.error(f"Error listing backtests: {e}")
            return {"error": str(e)}

    async def get_backtest_details(self, backtest_id: str) -> Dict[str, Any]:
        """Get backtest details"""
        try:
            self.logger.info(f"Getting backtest details for {backtest_id}")
            
            if not self.backtest_api:
                return {"error": "Backtest API not available"}
            
            backtest = await self.backtest_api.get_backtest_details(backtest_id)
            
            if backtest:
                return {
                    "success": True,
                    "backtest": backtest
                }
            else:
                return {
                    "success": False,
                    "error": f"Backtest {backtest_id} not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting backtest details: {e}")
            return {"error": str(e)}

    async def get_backtest_results(self, backtest_id: str) -> Dict[str, Any]:
        """Get backtest results"""
        try:
            self.logger.info(f"Getting backtest results for {backtest_id}")
            
            if not self.backtest_api:
                return {"error": "Backtest API not available"}
            
            results = await self.backtest_api.get_backtest_results(backtest_id)
            
            if results:
                return {
                    "success": True,
                    "backtest_id": backtest_id,
                    "results": results
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not retrieve results for backtest {backtest_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting backtest results: {e}")
            return {"error": str(e)}

    async def cancel_backtest(self, backtest_id: str) -> Dict[str, Any]:
        """Cancel a running backtest"""
        try:
            self.logger.info(f"Cancelling backtest {backtest_id}")
            
            if not self.backtest_api:
                return {"error": "Backtest API not available"}
            
            success = await self.backtest_api.cancel_backtest(backtest_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Backtest {backtest_id} cancelled successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to cancel backtest {backtest_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error cancelling backtest: {e}")
            return {"error": str(e)}

    def print_backtests_report(self, backtests_data: Dict[str, Any]):
        """Print backtests report"""
        try:
            if "error" in backtests_data:
                print(f"❌ Error: {backtests_data['error']}")
                return
            
            backtests = backtests_data.get("backtests", [])
            count = backtests_data.get("count", 0)
            lab_id = backtests_data.get("lab_id")
            
            print("\n" + "="*80)
            print("📊 BACKTESTS REPORT")
            print("="*80)
            if lab_id:
                print(f"🏷️  Lab ID: {lab_id}")
            print(f"📊 Total Backtests: {count}")
            print("-"*80)
            
            if backtests:
                for backtest in backtests:
                    backtest_id = getattr(backtest, 'id', 'Unknown')
                    script_name = getattr(backtest, 'script_name', 'Unknown')
                    status = getattr(backtest, 'status', 'Unknown')
                    roi = getattr(backtest, 'roi_percentage', 0)
                    win_rate = getattr(backtest, 'win_rate', 0) * 100
                    
                    print(f"🧪 {script_name}")
                    print(f"   ID: {backtest_id}")
                    print(f"   Status: {status}")
                    print(f"   ROI: {roi:.1f}%")
                    print(f"   Win Rate: {win_rate:.0f}%")
                    print()
            else:
                print("No backtests found")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing backtests report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_backtest_details_report(self, backtest_data: Dict[str, Any]):
        """Print backtest details report"""
        try:
            if "error" in backtest_data:
                print(f"❌ Error: {backtest_data['error']}")
                return
            
            if not backtest_data.get("success", False):
                print(f"❌ {backtest_data.get('error', 'Unknown error')}")
                return
            
            backtest = backtest_data.get("backtest")
            if not backtest:
                print("❌ No backtest data available")
                return
            
            print("\n" + "="*80)
            print("📊 BACKTEST DETAILS")
            print("="*80)
            
            # Basic info
            backtest_id = getattr(backtest, 'id', 'Unknown')
            script_name = getattr(backtest, 'script_name', 'Unknown')
            status = getattr(backtest, 'status', 'Unknown')
            roi = getattr(backtest, 'roi_percentage', 0)
            win_rate = getattr(backtest, 'win_rate', 0) * 100
            
            print(f"🧪 {script_name}")
            print(f"   ID: {backtest_id}")
            print(f"   Status: {status}")
            print(f"   ROI: {roi:.1f}%")
            print(f"   Win Rate: {win_rate:.0f}%")
            
            # Additional details
            if hasattr(backtest, 'max_drawdown'):
                print(f"   Max Drawdown: {backtest.max_drawdown:.2f}%")
            if hasattr(backtest, 'total_trades'):
                print(f"   Total Trades: {backtest.total_trades}")
            if hasattr(backtest, 'start_date'):
                print(f"   Start Date: {backtest.start_date}")
            if hasattr(backtest, 'end_date'):
                print(f"   End Date: {backtest.end_date}")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing backtest details report: {e}")
            print(f"❌ Error generating report: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Backtest Management CLI")
    parser.add_argument("--list", action="store_true", help="List all backtests")
    parser.add_argument("--list-lab", type=str, help="List backtests for specific lab")
    parser.add_argument("--details", type=str, help="Get backtest details by ID")
    parser.add_argument("--results", type=str, help="Get backtest results by ID")
    parser.add_argument("--cancel", type=str, help="Cancel backtest by ID")
    
    args = parser.parse_args()
    
    cli = BacktestCLI()
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        if args.list:
            # List all backtests
            backtests_data = await cli.list_backtests()
            cli.print_backtests_report(backtests_data)
            
        elif args.list_lab:
            # List backtests for specific lab
            backtests_data = await cli.list_backtests(args.list_lab)
            cli.print_backtests_report(backtests_data)
            
        elif args.details:
            # Get backtest details
            backtest_data = await cli.get_backtest_details(args.details)
            cli.print_backtest_details_report(backtest_data)
            
        elif args.results:
            # Get backtest results
            results_data = await cli.get_backtest_results(args.results)
            if results_data.get("success"):
                print(f"📊 Backtest {args.results} Results: {results_data['results']}")
            else:
                print(f"❌ {results_data.get('error', 'Unknown error')}")
                
        elif args.cancel:
            # Cancel backtest
            cancel_data = await cli.cancel_backtest(args.cancel)
            if cancel_data.get("success"):
                print(f"✅ {cancel_data['message']}")
            else:
                print(f"❌ {cancel_data.get('error', 'Unknown error')}")
                
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())





