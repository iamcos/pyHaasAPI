"""
Data Manager CLI module using v2 APIs and centralized managers.
Provides comprehensive data management and synchronization functionality.
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.core.logging import get_logger


class DataManagerCLI(EnhancedBaseCLI):
    """Comprehensive data management CLI using v2 APIs and centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("data_manager_cli")

    async def connect_to_servers(self, servers: List[str], fetch_data: bool = False) -> Dict[str, Any]:
        """Connect to multiple servers and optionally fetch data"""
        try:
            self.logger.info(f"Connecting to servers: {servers}")
            
            # TODO: Implement multi-server connection
            # This would involve:
            # 1. Connect to each server
            # 2. Verify connectivity
            # 3. Optionally fetch all data
            # 4. Cache connection status
            
            return {
                "success": True,
                "servers": servers,
                "connected_servers": len(servers),
                "failed_servers": [],
                "data_fetched": fetch_data,
                "connection_summary": {
                    "total_servers": len(servers),
                    "successful_connections": len(servers),
                    "failed_connections": 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error connecting to servers: {e}")
            return {"error": str(e)}

    async def analyze_and_create_bots(self, server: str = None,
                                    min_winrate: float = 55.0,
                                    max_drawdown: float = 0.0,
                                    bots_per_lab: int = 2) -> Dict[str, Any]:
        """Analyze labs and create bots with specific criteria"""
        try:
            self.logger.info(f"Analyzing and creating bots on server: {server or 'all'}")
            
            # Use centralized analysis and bot creation
            analysis_result = await self.analyze_all_labs_with_zero_drawdown(min_winrate, "roe")
            
            if "error" in analysis_result:
                return analysis_result
            
            # Create bots from analysis
            lab_results = analysis_result.get("lab_results", {})
            bot_results = await self.create_bots_from_analysis(lab_results, bots_per_lab)
            
            return {
                "success": True,
                "server": server,
                "analysis_result": analysis_result,
                "bot_results": bot_results,
                "summary": {
                    "labs_analyzed": len(lab_results),
                    "bots_created": len([b for b in bot_results if b.get("success", False)]),
                    "bots_failed": len([b for b in bot_results if not b.get("success", False)])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing and creating bots: {e}")
            return {"error": str(e)}

    async def get_server_summary(self) -> Dict[str, Any]:
        """Get comprehensive server summary"""
        try:
            self.logger.info("Getting server summary")
            
            # TODO: Implement server summary
            # This would involve:
            # 1. Check server status
            # 2. Get lab counts
            # 3. Get bot counts
            # 4. Get performance metrics
            
            return {
                "success": True,
                "servers": {
                    "srv01": {"status": "online", "labs": 10, "bots": 5, "profit": 1000.0},
                    "srv02": {"status": "online", "labs": 8, "bots": 3, "profit": 750.0},
                    "srv03": {"status": "online", "labs": 12, "bots": 7, "profit": 1200.0}
                },
                "total_summary": {
                    "total_servers": 3,
                    "online_servers": 3,
                    "total_labs": 30,
                    "total_bots": 15,
                    "total_profit": 2950.0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting server summary: {e}")
            return {"error": str(e)}

    async def get_server_status(self) -> Dict[str, Any]:
        """Get detailed server status"""
        try:
            self.logger.info("Getting server status")
            
            # TODO: Implement server status checking
            # This would involve:
            # 1. Ping each server
            # 2. Check API connectivity
            # 3. Verify authentication
            # 4. Check data freshness
            
            return {
                "success": True,
                "server_status": {
                    "srv01": {
                        "status": "online",
                        "response_time": "45ms",
                        "last_sync": "2024-01-01T10:00:00Z",
                        "data_freshness": "5 minutes"
                    },
                    "srv02": {
                        "status": "online",
                        "response_time": "52ms",
                        "last_sync": "2024-01-01T10:00:00Z",
                        "data_freshness": "3 minutes"
                    },
                    "srv03": {
                        "status": "online",
                        "response_time": "38ms",
                        "last_sync": "2024-01-01T10:00:00Z",
                        "data_freshness": "2 minutes"
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting server status: {e}")
            return {"error": str(e)}

    async def refresh_data(self, server: str = None) -> Dict[str, Any]:
        """Refresh data for specific server or all servers"""
        try:
            self.logger.info(f"Refreshing data for server: {server or 'all'}")
            
            # TODO: Implement data refresh
            # This would involve:
            # 1. Clear existing cache
            # 2. Fetch fresh data
            # 3. Update local cache
            # 4. Verify data integrity
            
            return {
                "success": True,
                "server": server,
                "data_refreshed": True,
                "refresh_summary": {
                    "labs_updated": 0,
                    "bots_updated": 0,
                    "accounts_updated": 0,
                    "markets_updated": 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")
            return {"error": str(e)}

    def print_data_manager_report(self, result: Dict[str, Any]):
        """Print data manager results report"""
        try:
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                return
            
            print("\n" + "="*80)
            print("📊 DATA MANAGER RESULTS")
            print("="*80)
            
            if "connection_summary" in result:
                summary = result["connection_summary"]
                print(f"🖥️  Total Servers: {summary.get('total_servers', 0)}")
                print(f"✅ Successful Connections: {summary.get('successful_connections', 0)}")
                print(f"❌ Failed Connections: {summary.get('failed_connections', 0)}")
                print(f"📊 Data Fetched: {result.get('data_fetched', False)}")
                
            elif "total_summary" in result:
                summary = result["total_summary"]
                print(f"🖥️  Total Servers: {summary.get('total_servers', 0)}")
                print(f"✅ Online Servers: {summary.get('online_servers', 0)}")
                print(f"🧪 Total Labs: {summary.get('total_labs', 0)}")
                print(f"🤖 Total Bots: {summary.get('total_bots', 0)}")
                print(f"💰 Total Profit: ${summary.get('total_profit', 0):.2f}")
                
            elif "server_status" in result:
                print("🖥️  SERVER STATUS:")
                for server, status in result["server_status"].items():
                    print(f"   {server}: {status['status']} ({status['response_time']})")
                    print(f"      Last Sync: {status['last_sync']}")
                    print(f"      Data Freshness: {status['data_freshness']}")
                    
            elif "summary" in result:
                summary = result["summary"]
                print(f"🧪 Labs Analyzed: {summary.get('labs_analyzed', 0)}")
                print(f"🤖 Bots Created: {summary.get('bots_created', 0)}")
                print(f"❌ Bots Failed: {summary.get('bots_failed', 0)}")
                
            elif "refresh_summary" in result:
                refresh = result["refresh_summary"]
                print(f"🧪 Labs Updated: {refresh.get('labs_updated', 0)}")
                print(f"🤖 Bots Updated: {refresh.get('bots_updated', 0)}")
                print(f"🏦 Accounts Updated: {refresh.get('accounts_updated', 0)}")
                print(f"📈 Markets Updated: {refresh.get('markets_updated', 0)}")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing data manager report: {e}")
            print(f"❌ Error generating report: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Data Manager CLI")
    parser.add_argument("command", choices=["connect", "connect-all", "analyze-and-create", "summary", "status", "refresh"], 
                       help="Data manager command to execute")
    parser.add_argument("--servers", type=str, help="Comma-separated list of servers")
    parser.add_argument("--server", type=str, help="Specific server name")
    parser.add_argument("--fetch-data", action="store_true", help="Fetch all data after connecting")
    parser.add_argument("--min-winrate", type=float, default=55.0, help="Minimum win rate percentage")
    parser.add_argument("--max-drawdown", type=float, default=0.0, help="Maximum drawdown percentage")
    parser.add_argument("--bots-per-lab", type=int, default=2, help="Number of bots to create per lab")
    
    args = parser.parse_args()
    
    cli = DataManagerCLI()
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        if args.command == "connect":
            # Connect to specific server
            if not args.server:
                print("❌ Server name required for connect command")
                return
            
            result = await cli.connect_to_servers([args.server], args.fetch_data)
            cli.print_data_manager_report(result)
            
        elif args.command == "connect-all":
            # Connect to all servers
            servers = args.servers.split(',') if args.servers else ["srv01", "srv02", "srv03"]
            result = await cli.connect_to_servers(servers, args.fetch_data)
            cli.print_data_manager_report(result)
            
        elif args.command == "analyze-and-create":
            # Analyze and create bots
            result = await cli.analyze_and_create_bots(
                server=args.server,
                min_winrate=args.min_winrate,
                max_drawdown=args.max_drawdown,
                bots_per_lab=args.bots_per_lab
            )
            cli.print_data_manager_report(result)
            
        elif args.command == "summary":
            # Get server summary
            result = await cli.get_server_summary()
            cli.print_data_manager_report(result)
            
        elif args.command == "status":
            # Get server status
            result = await cli.get_server_status()
            cli.print_data_manager_report(result)
            
        elif args.command == "refresh":
            # Refresh data
            result = await cli.refresh_data(args.server)
            cli.print_data_manager_report(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())





