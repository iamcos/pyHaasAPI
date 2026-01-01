"""
Project Manager CLI for Server Content Revision

Thin CLI wrapper that delegates to native pyHaasAPI services for:
- Server snapshot and gap analysis
- Resumable backtest fetching (5 per lab)
- Analysis with zero-drawdown filtering
- Duplicate-safe bot creation
"""

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

import os
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager
from ..core.server_manager import ServerManager
from ..config.settings import Settings
from ..config.api_config import APIConfig
from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.backtest import BacktestAPI
from ..api.market import MarketAPI
from ..services.server_content_manager import ServerContentManager
from ..services.analysis import AnalysisService
from ..services.analysis.cached_analysis_service import CachedAnalysisService
from ..services.bot import BotService
from ..services.bot_naming_service import BotNamingService, BotNamingContext
from ..services.longest_backtest_service import LongestBacktestService
from ..cli.base import BaseCLI
from ..core.logging import get_logger


class ProjectManagerCLI(BaseCLI):
    """
    Project Manager CLI for server content revision workflow.
    
    Commands:
    - snapshot: Take server snapshot (labs, bots, gaps)
    - fetch: Download N backtests per lab with resume
    - analyze: Analyze with zero-drawdown filtering
    - create-bots: Create bots with duplicate detection
    - run: Complete workflow (snapshot → fetch → analyze → create)
    """
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("project_manager_cli")
        self.bot_naming_service = BotNamingService()
        self.settings = Settings()
        self.server_manager = ServerManager(self.settings)
        self.server_content_managers: Dict[str, ServerContentManager] = {}
        self.server_apis: Dict[str, Dict[str, Any]] = {}

    async def run(self, args: List[str]) -> int:
        """Required by BaseCLI; this CLI is invoked via module main() parser."""
        return 0
        
    async def connect_to_server(self, server: str) -> bool:
        """Connect to a specific server and initialize APIs"""
        try:
            self.logger.info(f"Connecting to {server}...")
            
            # Ensure mandated SSH tunnel
            if server == "srv03":
                if not await self.server_manager.ensure_srv03_tunnel():
                    self.logger.error("Failed to establish SSH tunnel to srv03")
                    return False
            else:
                await self.server_manager.connect_server(server)
            # Preflight check
            if not await self.server_manager.preflight_check():
                self.logger.error("Preflight check failed - tunnel not available")
                return False
            
            # Create API config
            api_config = APIConfig(
                host="127.0.0.1",
                port=8090,
                timeout=30.0,
                # Credentials provided at authenticate() via env
            )
            
            # Create client and auth
            client = AsyncHaasClient(api_config)
            auth_manager = AuthenticationManager(client, api_config)
            # Set credentials from environment
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            # Read credentials from env (standard across CLIs)
            email = os.getenv("API_EMAIL")
            password = os.getenv("API_PASSWORD")
            await auth_manager.authenticate(email, password)
            
            # Create API instances
            lab_api = LabAPI(client, auth_manager)
            bot_api = BotAPI(client, auth_manager)
            account_api = AccountAPI(client, auth_manager)
            backtest_api = BacktestAPI(client, auth_manager)
            market_api = MarketAPI(client, auth_manager)
            analysis_service = AnalysisService(lab_api, backtest_api, bot_api, client, auth_manager)
            
            # Create server content manager with AccountManager
            server_content_manager = ServerContentManager(
                server=server,
                lab_api=lab_api,
                bot_api=bot_api,
                backtest_api=backtest_api,
                account_api=account_api,  # Enable AccountManager
                cache_dir=Path("unified_cache")
            )
            
            # Store APIs and manager
            self.server_apis[server] = {
                "client": client,
                "auth_manager": auth_manager,
                "lab_api": lab_api,
                "bot_api": bot_api,
                "account_api": account_api,
                "backtest_api": backtest_api,
                "market_api": market_api,
                "analysis_service": analysis_service
            }
            self.server_content_managers[server] = server_content_manager
            
            self.logger.info(f"✅ Connected to {server}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to {server}: {e}")
            return False
    
    def _serialize_bot(self, bot: Any) -> Dict[str, Any]:
        """Serialize bot with relevant fields for analysis"""
        return {
            "bot_id": getattr(bot, "bot_id", None) or getattr(bot, "id", None),
            "bot_name": getattr(bot, "bot_name", None) or getattr(bot, "name", None),
            "script_name": getattr(bot, "script_name", None),
            "script_id": getattr(bot, "script_id", None),
            "market_tag": getattr(bot, "market_tag", None) or getattr(bot, "market", None),
            "account_id": getattr(bot, "account_id", None),
            "notes": getattr(bot, "notes", None)
        }

    def _serialize_lab(self, lab: Any) -> Dict[str, Any]:
        """Serialize lab with relevant fields"""
        return {
            "lab_id": getattr(lab, "lab_id", None) or getattr(lab, "id", None),
            "lab_name": getattr(lab, "name", None) or getattr(lab, "lab_name", None),
            "script_name": getattr(lab, "script_name", None),
            "market_tag": getattr(lab, "market_tag", None) or getattr(lab, "marketTag", None)
        }
    
    async def snapshot(self, servers: List[str]) -> Dict[str, Any]:
        """Take snapshots of specified servers"""
        self.logger.info(f"📸 Taking snapshots of servers: {servers}")
        snapshots = {}
        
        for server in servers:
            if not await self.connect_to_server(server):
                continue
                
            try:
                snapshot = await self.server_content_managers[server].snapshot()
                
                # Find orphan bots (not in any lab mapping)
                matched_bot_ids = set()
                for bots in snapshot.lab_id_to_bots.values():
                    for bot in bots:
                        bot_id = getattr(bot, "bot_id", None) or getattr(bot, "id", None)
                        if bot_id:
                            matched_bot_ids.add(bot_id)

                orphan_bots = [
                    bot for bot in snapshot.bots 
                    if (getattr(bot, "bot_id", None) or getattr(bot, "id", None)) not in matched_bot_ids
                ]
                
                snapshots[server] = {
                    "server": snapshot.server,
                    "timestamp": snapshot.timestamp,
                    "labs_count": len(snapshot.labs),
                    "bots_count": len(snapshot.bots),
                    "labs_without_bots": len(snapshot.labs_without_bots),
                    "coins": sorted(list(snapshot.coins)),
                    "labs_without_bots_ids": sorted(list(snapshot.labs_without_bots)),
                    "lab_id_to_bots": {
                        lab_id: [self._serialize_bot(bot) for bot in bots]
                        for lab_id, bots in snapshot.lab_id_to_bots.items()
                    },
                    "orphan_bots": [self._serialize_bot(bot) for bot in orphan_bots],
                    "labs_detail": [self._serialize_lab(lab) for lab in snapshot.labs]
                }
                
                self.logger.info(f"✅ {server}: {len(snapshot.labs)} labs, {len(snapshot.bots)} bots, {len(snapshot.labs_without_bots)} labs without bots")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to snapshot {server}: {e}")
                snapshots[server] = {"error": str(e)}
        
        # Save snapshot results
        snapshot_file = Path("unified_cache") / "snapshots" / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_file, 'w') as f:
            json.dump(snapshots, f, indent=2, default=str)
        
        self.logger.info(f"📁 Snapshot results saved to {snapshot_file}")
        # Clean up client sessions
        try:
            for server in list(self.server_apis.keys()):
                client = self.server_apis[server].get("client")
                if client:
                    await client.close()
        except Exception:
            pass
        return snapshots
    
    async def fetch(self, servers: List[str], count: int = 5, resume: bool = True, max_labs: Optional[int] = None) -> Dict[str, Any]:
        """Download N backtests per lab with resume capability"""
        self.logger.info(f"📥 Fetching {count} backtests per lab on servers: {servers}")
        results = {}
        
        for server in servers:
            if not await self.connect_to_server(server):
                continue
                
            try:
                # Get labs that need backtests
                snapshot = await self.server_content_managers[server].snapshot()
                lab_ids = [getattr(lab, 'lab_id', None) or getattr(lab, 'id', None) for lab in snapshot.labs if (getattr(lab, 'lab_id', None) or getattr(lab, 'id', None))]
                
                # Apply lab limit if specified
                if max_labs:
                    lab_ids = lab_ids[:max_labs]
                    self.logger.info(f"🔢 Limited to {max_labs} labs for testing")
                
                # Fetch backtests for each lab
                fetch_results = await self.server_content_managers[server].fetch_backtests_for_labs(
                    lab_ids, count=count, resume=resume
                )
                
                results[server] = {
                    "labs_processed": len(lab_ids),
                    "backtests_cached": sum(fetch_results.values()),
                    "per_lab": fetch_results
                }
                
                self.logger.info(f"✅ {server}: {len(lab_ids)} labs, {sum(fetch_results.values())} backtests cached")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to fetch backtests on {server}: {e}")
                results[server] = {"error": str(e)}
        
        return results
    
    async def analyze(self, servers: List[str], min_winrate: float = 0.55, max_drawdown: float = 0.0, sort_by: str = "roe", max_labs: Optional[int] = None, max_backtests: int = 50) -> Dict[str, Any]:
        """Analyze backtests using cached analysis service"""
        self.logger.info(f"📊 Analyzing backtests on servers: {servers} (min_winrate={min_winrate}, sort_by={sort_by})")
        results = {}
        
        for server in servers:
            if not await self.connect_to_server(server):
                continue
                
            try:
                # Get snapshot to find labs
                snapshot = await self.server_content_managers[server].snapshot()
                lab_ids = [getattr(lab, 'lab_id', None) or getattr(lab, 'id', None) for lab in snapshot.labs if (getattr(lab, 'lab_id', None) or getattr(lab, 'id', None))]
                
                # Apply lab limit if specified
                if max_labs:
                    lab_ids = lab_ids[:max_labs]
                    self.logger.info(f"🔢 Limited to {max_labs} labs for testing")
                
                # Use cached analysis service
                cache_dir = Path("unified_cache")
                cached_analysis_service = CachedAnalysisService(cache_dir)
                
                analysis_results = {}
                for lab_id in lab_ids:
                    try:
                        # Get lab name from snapshot
                        lab_name = ""
                        for lab in snapshot.labs:
                            if (getattr(lab, 'lab_id', None) or getattr(lab, 'id', None)) == lab_id:
                                lab_name = getattr(lab, 'name', None) or getattr(lab, 'lab_name', None) or f"Lab {lab_id[:8]}"
                                break
                        
                        # Analyze lab using cached data
                        analysis = await cached_analysis_service.analyze_lab_from_cache(
                            lab_id=lab_id,
                            lab_name=lab_name,
                            top_count=max_backtests,
                            min_win_rate=min_winrate,
                            min_trades=10,
                            max_drawdown=max_drawdown,
                            sort_by=sort_by
                        )
                        
                        if analysis.success:
                            analysis_results[lab_id] = {
                                "lab_id": lab_id,
                                "lab_name": lab_name,
                                "total_backtests": analysis.total_backtests,
                                "top_performers": analysis.top_performers[:5],  # Top 5 performers
                                "average_roi": analysis.average_roi,
                                "best_roi": analysis.best_roi,
                                "average_win_rate": analysis.average_win_rate,
                                "best_win_rate": analysis.best_win_rate
                            }
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to analyze lab {lab_id[:8]}: {e}")
                        analysis_results[lab_id] = {"error": str(e)}
                
                results[server] = {
                    "labs_analyzed": len(lab_ids),
                    "analysis_results": analysis_results
                }
                
                total_zero_dd = sum(r.get("zero_drawdown_count", 0) for r in analysis_results.values())
                self.logger.info(f"✅ {server}: {len(lab_ids)} labs analyzed, {total_zero_dd} zero-drawdown backtests found")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to analyze {server}: {e}")
                results[server] = {"error": str(e)}
        
        return results
    
    async def create_bots(self, servers: List[str], bots_per_lab: int = 1) -> Dict[str, Any]:
        """Create bots with duplicate detection"""
        self.logger.info(f"🤖 Creating bots on servers: {servers} (max {bots_per_lab} per lab)")
        results = {}
        
        for server in servers:
            if not await self.connect_to_server(server):
                continue
                
            try:
                # Get AccountManager from ServerContentManager
                account_manager = self.server_content_managers[server].account_manager
                if not account_manager:
                    self.logger.error(f"No AccountManager available on {server}")
                    results[server] = {"created_bots": 0, "skipped_bots": 0, "error": "No AccountManager available"}
                    continue
                
                # Get snapshot for duplicate detection
                snapshot = await self.server_content_managers[server].snapshot()
                
                # Get analysis results
                analysis_results = await self.analyze([server])
                server_analysis = analysis_results.get(server, {}).get("analysis_results", {})
                
                created_bots = []
                skipped_bots = []
                
                for lab_id, analysis in server_analysis.items():
                    if "error" in analysis:
                        continue
                        
                    top_performers = analysis.get("top_performers", [])[:bots_per_lab]
                    
                    for backtest in top_performers:
                        try:
                            # Create naming context with comprehensive metrics
                            naming_context = BotNamingContext(
                                server=server,
                                lab_id=lab_id,
                                lab_name=f"Lab {lab_id[:8]}",
                                script_name=getattr(backtest, 'script_name', 'Unknown'),
                                market_tag=getattr(backtest, 'market_tag', ''),
                                roi_percentage=getattr(backtest, 'roi_percentage', 0.0),
                                win_rate=getattr(backtest, 'win_rate', 0.0),
                                max_drawdown=getattr(backtest, 'max_drawdown', 0.0),
                                total_trades=getattr(backtest, 'total_trades', 0),
                                profit_factor=getattr(backtest, 'profit_factor', 0.0),
                                sharpe_ratio=getattr(backtest, 'sharpe_ratio', 0.0),
                                generation_idx=getattr(backtest, 'generation_idx', 0),
                                population_idx=getattr(backtest, 'population_idx', 0),
                                backtest_id=getattr(backtest, 'backtest_id', ''),
                                account_id=""
                            )
                            
                            # Generate enhanced bot name using server-specific strategy
                            bot_name = self.bot_naming_service.generate_bot_name(
                                naming_context, 
                                strategy="server-specific"
                            )
                            
                            # Check for duplicates
                            skip_pairs = await self.server_content_managers[server].compute_creation_skips(
                                {lab_id: analysis}, snapshot.bots
                            )
                            
                            if (lab_id, getattr(backtest, 'backtest_id', None)) in skip_pairs:
                                skipped_bots.append({
                                    "lab_id": lab_id,
                                    "backtest_id": getattr(backtest, 'backtest_id', None),
                                    "bot_name": bot_name,
                                    "reason": "duplicate"
                                })
                                continue
                            
                            # Get or create account using round-robin assignment
                            account = await account_manager.assign_account_round_robin(
                                exchange="BINANCEFUTURES"
                            )
                            
                            # Create bot
                            bot_result = await self.server_apis[server]["bot_api"].create_bot_from_lab(
                                lab_id=lab_id,
                                backtest_id=getattr(backtest, 'backtest_id', None),
                                account_id=getattr(account, 'account_id', None),
                                bot_name=bot_name,
                                trade_amount_usdt=2000.0,
                                leverage=20.0
                            )
                            
                            created_bots.append({
                                "bot_id": getattr(bot_result, 'bot_id', None),
                                "bot_name": bot_name,
                                "lab_id": lab_id,
                                "backtest_id": getattr(backtest, 'backtest_id', None)
                            })
                            
                        except Exception as e:
                            self.logger.error(f"Failed to create bot for {lab_id[:8]}: {e}")
                
                results[server] = {
                    "created_bots": len(created_bots),
                    "skipped_bots": len(skipped_bots),
                    "created": created_bots,
                    "skipped": skipped_bots
                }
                
                self.logger.info(f"✅ {server}: {len(created_bots)} bots created, {len(skipped_bots)} skipped")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to create bots on {server}: {e}")
                results[server] = {"error": str(e)}
        
        return results
    
    async def run_quick(self, servers: List[str], max_labs: Optional[int] = None, max_backtests: int = 50) -> Dict[str, Any]:
        """Run complete workflow: snapshot → fetch → analyze → create"""
        self.logger.info(f"🚀 Running quick workflow on servers: {servers}")
        
        # Phase 1: Snapshot
        self.logger.info("Phase 1: Taking snapshots...")
        snapshots = await self.snapshot(servers)
        
        # Phase 2: Fetch backtests
        self.logger.info("Phase 2: Fetching backtests...")
        fetch_results = await self.fetch(servers, count=5, resume=True, max_labs=max_labs)
        
        # Phase 3: Analyze
        self.logger.info("Phase 3: Analyzing...")
        analysis_results = await self.analyze(servers, min_winrate=0.55, sort_by="roe", max_labs=max_labs, max_backtests=max_backtests)
        
        # Phase 4: Create bots
        self.logger.info("Phase 4: Creating bots...")
        bot_results = await self.create_bots(servers, bots_per_lab=1)
        
        # Summary
        total_created = sum(r.get("created_bots", 0) for r in bot_results.values())
        total_skipped = sum(r.get("skipped_bots", 0) for r in bot_results.values())
        
        self.logger.info(f"🎉 Quick workflow completed: {total_created} bots created, {total_skipped} skipped")
        
        return {
            "snapshots": snapshots,
            "fetch_results": fetch_results,
            "analysis_results": analysis_results,
            "bot_results": bot_results,
            "summary": {
                "total_created": total_created,
                "total_skipped": total_skipped,
                "servers_processed": len(servers)
            }
        }
    
    async def analyze_mapping(self, servers: List[str], use_cache: bool = True) -> Dict[str, Any]:
        """Analyze bot-to-lab mappings from snapshot"""
        self.logger.info(f"🔍 Analyzing bot-to-lab mappings for: {servers}")
        results = {}
        
        for server in servers:
            # Load most recent snapshot from cache
            snapshot_dir = Path("unified_cache") / "snapshots"
            snapshot_files = sorted(snapshot_dir.glob("snapshot_*.json"), reverse=True)
            
            if not snapshot_files:
                self.logger.warning(f"No cached snapshots found for {server}")
                continue
            
            with open(snapshot_files[0], 'r') as f:
                cached_data = json.load(f)
            
            if server not in cached_data:
                continue
            
            server_data = cached_data[server]
            
            # Generate detailed analysis
            results[server] = {
                "snapshot_file": str(snapshot_files[0]),
                "snapshot_timestamp": server_data.get("timestamp"),
                "summary": {
                    "total_labs": server_data.get("labs_count", 0),
                    "total_bots": server_data.get("bots_count", 0),
                    "labs_with_bots": len(server_data.get("lab_id_to_bots", {})),
                    "matched_bots": sum(len(bots) for bots in server_data.get("lab_id_to_bots", {}).values()),
                    "orphan_bots": len(server_data.get("orphan_bots", [])),
                    "labs_without_bots": len(server_data.get("labs_without_bots_ids", []))
                },
                "lab_mappings": server_data.get("lab_id_to_bots", {}),
                "orphan_bots": server_data.get("orphan_bots", []),
                "labs_without_bots_ids": server_data.get("labs_without_bots_ids", []),
                "labs_detail": server_data.get("labs_detail", [])
            }
        
        return results
    
    def print_mapping_report(self, results: Dict[str, Any]):
        """Print detailed bot-to-lab mapping report"""
        for server, data in results.items():
            if "error" in data:
                print(f"\n❌ {server}: {data['error']}")
                continue
            
            summary = data["summary"]
            print(f"\n{'='*80}")
            print(f"Bot-to-Lab Mapping Report: {server}")
            print(f"Snapshot: {data['snapshot_timestamp']}")
            print(f"{'='*80}")
            
            print(f"\n📊 Summary:")
            print(f"  Total Labs: {summary['total_labs']}")
            print(f"  Total Bots: {summary['total_bots']}")
            print(f"  Labs with Bots: {summary['labs_with_bots']}")
            print(f"  Matched Bots: {summary['matched_bots']} ({summary['matched_bots']/summary['total_bots']*100:.1f}%)")
            print(f"  Orphan Bots: {summary['orphan_bots']} ({summary['orphan_bots']/summary['total_bots']*100:.1f}%)")
            print(f"  Labs Without Bots: {summary['labs_without_bots']}")
            
            # Show matched bots by lab
            print(f"\n🎯 Matched Bots by Lab:")
            for lab_id, bots in data["lab_mappings"].items():
                # Find lab details
                lab_detail = next((l for l in data["labs_detail"] if l["lab_id"] == lab_id), {})
                lab_name = lab_detail.get("lab_name", f"Lab {lab_id[:8]}")
                
                print(f"\n  Lab: {lab_name}")
                print(f"  ID: {lab_id}")
                print(f"  Bots ({len(bots)}):")
                for i, bot in enumerate(bots, 1):
                    print(f"    {i}. {bot['bot_name']}")
                    print(f"       Market: {bot['market_tag']}")
            
            # Show orphan bots
            if data["orphan_bots"]:
                print(f"\n⚠️  Orphan Bots (No Lab Match):")
                for i, bot in enumerate(data["orphan_bots"], 1):
                    print(f"  {i}. {bot['bot_name']}")
                    print(f"     Market: {bot['market_tag']}")
            
            # Show labs without bots
            if data["labs_without_bots_ids"]:
                print(f"\n📭 Labs Without Bots ({len(data['labs_without_bots_ids'])}):")
                for lab_id in data["labs_without_bots_ids"]:
                    lab_detail = next((l for l in data["labs_detail"] if l["lab_id"] == lab_id), {})
                    lab_name = lab_detail.get("lab_name", f"Lab {lab_id[:8]}")
                    print(f"  - {lab_name} ({lab_id[:8]}...)")
            
            print(f"\n{'='*80}\n")
    
    async def deploy_bots(
        self,
        servers: List[str],
        bots_per_lab: int = 5,
        trade_amount_usdt: float = 2000.0,
        leverage: int = 20,
        min_win_rate: float = 0.55,  # Standardized: 55%+ win rate
        max_drawdown: float = 0.0,   # Standardized: Zero drawdown only
        verify_with_backtest: bool = True,
        verification_days: int = 7    # 7-day verification backtest
    ) -> Dict[str, Any]:
        """
        Deploy bots for all labs without bots
        
        Args:
            servers: List of servers to process
            bots_per_lab: Number of bots to create per lab (default: 5)
            trade_amount_usdt: Trade amount in USDT (default: 2000)
            leverage: Leverage to use (default: 20)
            min_win_rate: Minimum win rate filter (default: 0.55 for 55%+)
            max_drawdown: Maximum drawdown (default: 0.0 for zero drawdown only)
            verify_with_backtest: Run verification backtest (default: True)
            verification_days: Days to run verification backtest (default: 7)
            
        Returns:
            Deployment results with success/failure counts and details
        """
        self.logger.info(f"🚀 Starting bot deployment for servers: {servers}")
        results = {}
        
        for server in servers:
            if not await self.connect_to_server(server):
                results[server] = {"error": "Failed to connect to server"}
                continue
            
            try:
                # Load most recent snapshot to find labs without bots
                snapshot_dir = Path("unified_cache") / "snapshots"
                snapshot_files = sorted(snapshot_dir.glob("snapshot_*.json"), reverse=True)
                
                if not snapshot_files:
                    self.logger.warning(f"No cached snapshots found for {server}")
                    results[server] = {"error": "No cached snapshots found"}
                    continue
                
                with open(snapshot_files[0], 'r') as f:
                    cached_data = json.load(f)
                
                if server not in cached_data:
                    results[server] = {"error": f"Server {server} not in snapshot"}
                    continue
                
                server_data = cached_data[server]
                labs_without_bots_ids = server_data.get("labs_without_bots_ids", [])
                labs_detail = server_data.get("labs_detail", [])
                
                # Find lab details for labs without bots
                labs_without_bots = [
                    lab for lab in labs_detail
                    if lab["lab_id"] in labs_without_bots_ids
                ]
                
                if not labs_without_bots:
                    self.logger.info(f"No labs without bots on {server}")
                    results[server] = {"message": "No labs without bots"}
                    continue
                
                self.logger.info(f"Found {len(labs_without_bots)} labs without bots on {server}")
                
                # Import BotDeploymentService
                from ..services.bot_deployment_service import BotDeploymentService
                
                # Create CachedAnalysisService
                cached_analysis_service = CachedAnalysisService(
                    cache_dir=Path("unified_cache") / "backtest_cache"
                )
                
                # Create LongestBacktestService for verification backtests
                longest_backtest_service = LongestBacktestService(
                    lab_api=self.server_apis[server]["lab_api"],
                    market_api=self.server_apis[server]["market_api"],
                    backtest_api=self.server_apis[server]["backtest_api"],
                    client=self.server_apis[server]["client"],
                    auth_manager=self.server_apis[server]["auth_manager"]
                )
                
                # Create BotDeploymentService
                bot_deployment_service = BotDeploymentService(
                    bot_api=self.server_apis[server]["bot_api"],
                    account_api=self.server_apis[server]["account_api"],
                    backtest_api=self.server_apis[server]["backtest_api"],
                    lab_api=self.server_apis[server]["lab_api"],
                    cached_analysis_service=cached_analysis_service,
                    longest_backtest_service=longest_backtest_service
                )
                
                # Deploy bots
                deployment_result = await bot_deployment_service.deploy_bots_for_labs_without_bots(
                    labs_without_bots=labs_without_bots,
                    bots_per_lab=bots_per_lab,
                    trade_amount_usdt=trade_amount_usdt,
                    leverage=leverage,
                    min_win_rate=min_win_rate,
                    max_drawdown=max_drawdown,
                    verify_with_backtest=verify_with_backtest,
                    verification_days=verification_days
                )
                
                results[server] = deployment_result
                
                self.logger.info(f"✅ {server}: Deployed {deployment_result['bots_created']} bots")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to deploy bots on {server}: {e}")
                results[server] = {"error": str(e)}
        
        # Clean up client sessions
        try:
            for server in list(self.server_apis.keys()):
                client = self.server_apis[server].get("client")
                if client:
                    await client.close()
        except Exception:
            pass
        
        return results


async def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Manager CLI for Server Content Revision")
    parser.add_argument("command", choices=["snapshot", "fetch", "analyze", "create-bots", "run", "analyze-mapping", "deploy-bots"], 
                       help="Command to execute")
    parser.add_argument("--servers", nargs="+", default=[Settings().default_server],
                       help="Servers to process (default: from API_DEFAULT_SERVER)")
    parser.add_argument("--count", type=int, default=5,
                       help="Number of backtests per lab to fetch (default: 5)")
    parser.add_argument("--min-winrate", type=float, default=0.55,
                       help="Minimum win rate for analysis (default: 0.55 for 55%+)")
    parser.add_argument("--max-drawdown", type=float, default=0.0,
                       help="Maximum drawdown allowed (default: 0.0 for zero drawdown only)")
    parser.add_argument("--sort-by", default="roe",
                       help="Sort analysis by field (default: roe)")
    parser.add_argument("--bots-per-lab", type=int, default=1,
                       help="Maximum bots to create per lab (default: 1)")
    parser.add_argument("--resume", action="store_true", default=True,
                       help="Resume fetching from cache (default: True)")
    parser.add_argument("--test-mode", action="store_true",
                       help="Run in test mode (5 labs, 50 backtests per lab)")
    parser.add_argument("--max-labs", type=int, default=None,
                       help="Maximum labs to process")
    parser.add_argument("--max-backtests", type=int, default=50,
                       help="Maximum backtests per lab (default: 50)")
    parser.add_argument("--trade-amount", type=float, default=2000.0,
                       help="Trade amount in USDT for bot deployment (default: 2000)")
    parser.add_argument("--leverage", type=int, default=20,
                       help="Leverage for bot deployment (default: 20)")
    parser.add_argument("--verify", action="store_true", default=True,
                       help="Run verification backtest after bot creation (default: True)")
    parser.add_argument("--no-verify", dest="verify", action="store_false",
                       help="Skip verification backtest")
    parser.add_argument("--verification-days", type=int, default=7,
                       help="Days to run verification backtest (default: 7)")
    
    args = parser.parse_args()
    
    cli = ProjectManagerCLI()
    
    try:
        # Determine test mode limits
        max_labs = 5 if args.test_mode else args.max_labs
        max_backtests = 50 if args.test_mode else args.max_backtests
        
        if args.command == "snapshot":
            result = await cli.snapshot(args.servers)
        elif args.command == "fetch":
            result = await cli.fetch(args.servers, count=args.count, resume=args.resume, max_labs=max_labs)
        elif args.command == "analyze":
            result = await cli.analyze(args.servers, min_winrate=args.min_winrate, max_drawdown=args.max_drawdown, sort_by=args.sort_by, max_labs=max_labs, max_backtests=max_backtests)
        elif args.command == "create-bots":
            result = await cli.create_bots(args.servers, bots_per_lab=args.bots_per_lab)
        elif args.command == "run":
            result = await cli.run_quick(args.servers, max_labs=max_labs, max_backtests=max_backtests)
        elif args.command == "analyze-mapping":
            result = await cli.analyze_mapping(args.servers)
            cli.print_mapping_report(result)
            return 0
        elif args.command == "deploy-bots":
            result = await cli.deploy_bots(
                servers=args.servers,
                bots_per_lab=args.bots_per_lab,
                trade_amount_usdt=args.trade_amount,
                leverage=args.leverage,
                min_win_rate=args.min_winrate,
                max_drawdown=args.max_drawdown,
                verify_with_backtest=args.verify,
                verification_days=args.verification_days
            )
        
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
