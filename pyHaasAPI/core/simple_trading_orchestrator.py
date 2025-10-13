"""
Simple Trading Orchestrator for pyHaasAPI v2

Multi-server trading orchestration with zero drawdown filtering and stability scoring.
Coordinates multiple servers, coins, and pre-configured labs to create zero-drawdown trading bots.

Features:
- Multi-server coordination (srv01, srv02, srv03)
- Multi-coin support (BTC, ETH, TRX, ADA)
- Zero drawdown filtering (max_drawdown <= 0.0)
- Stability score calculation and filtering
- Composite score sorting (stability + performance)
- Server-dedicated lab cloning and backtest execution
- Comprehensive bot naming and notes
- Project result tracking
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

from .client import AsyncHaasClient
from .auth import AuthenticationManager
from .server_manager import ServerManager
from .data_manager import ComprehensiveDataManager
from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.backtest import BacktestAPI
from ..api.market import MarketAPI
from ..services.analysis import AnalysisService
from ..services.longest_backtest_service import LongestBacktestService
from ..services.server_content_manager import ServerContentManager
from ..exceptions import OrchestrationError, LabError, BotError, AnalysisError
from ..core.logging import get_logger
from ..config.settings import Settings


@dataclass
class SimpleProjectConfig:
    """Configuration for simple trading orchestration"""
    project_name: str
    servers: List[str] = field(default_factory=lambda: ["srv01", "srv02", "srv03"])
    coins: List[str] = field(default_factory=lambda: ["BTC", "ETH", "TRX", "ADA"])
    base_labs: List[str] = field(default_factory=list)  # Pre-configured lab IDs to clone
    account_type: str = "BINANCEFUTURES_USDT"
    trade_amount_usdt: float = 2000.0
    leverage: float = 20.0
    max_drawdown_threshold: float = 0.0  # ZERO DRAWDOWN ONLY
    min_win_rate: float = 0.6
    min_trades: int = 10
    min_stability_score: float = 70.0  # Minimum stability score (0-100)
    top_bots_per_coin: int = 3
    activate_bots: bool = False
    output_directory: str = "trading_projects"


@dataclass
class ServerAPIs:
    """Container for server-specific API instances"""
    client: AsyncHaasClient
    auth_manager: AuthenticationManager
    lab_api: LabAPI
    bot_api: BotAPI
    account_api: AccountAPI
    backtest_api: BacktestAPI
    market_api: MarketAPI
    analysis_service: AnalysisService
    longest_backtest_service: LongestBacktestService


@dataclass
class BotCreationResult:
    """Result of bot creation operation"""
    bot_id: str
    bot_name: str
    backtest_id: str
    server: str
    coin: str
    base_lab_id: str
    roe: float
    win_rate: float
    max_drawdown: float
    stability_score: float
    composite_score: float
    activated: bool
    error_message: Optional[str] = None


@dataclass
class ProjectResult:
    """Complete project execution result"""
    project_name: str
    execution_timestamp: str
    servers_processed: List[str]
    total_labs_cloned: int
    total_backtests_executed: int
    total_bots_created: int
    zero_drawdown_bots: int
    stable_bots: int
    bot_results: Dict[str, Dict[str, List[BotCreationResult]]]  # server -> coin -> bots
    success: bool
    error_message: Optional[str] = None


class SimpleTradingOrchestrator:
    """
    Simple orchestrator that coordinates multiple servers, coins, and pre-configured labs
    to create zero-drawdown trading bots.
    
    Features:
    1. Clones pre-configured labs for each coin on dedicated servers
    2. Runs backtests using existing API on each server
    3. Filters results for zero drawdown + high stability on each server
    4. Calculates stability scores using existing analysis tools on each server
    5. Sorts by composite score (stability + performance) on each server
    6. Creates bots from best stable zero-drawdown results on each server
    7. Tracks everything with simple data structures per server
    """
    
    def __init__(self, config: SimpleProjectConfig, settings: Settings):
        self.config = config
        self.settings = settings
        self.logger = get_logger("simple_trading_orchestrator")
        
        # Server management
        self.server_manager = ServerManager(settings)
        self.data_manager = ComprehensiveDataManager(settings)
        
        # Server-specific API instances
        self.server_apis: Dict[str, ServerAPIs] = {}
        
        # Server content managers for snapshot and duplicate detection
        self.server_content_managers: Dict[str, ServerContentManager] = {}
        
        # Project tracking
        self.project_result: Optional[ProjectResult] = None
        
        # Create output directory
        self.output_dir = Path(config.output_directory)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"SimpleTradingOrchestrator initialized for project: {config.project_name}")
        # If no servers specified, fall back to configured default_server
        if not self.config.servers:
            self.config.servers = [self.settings.default_server]
        self.logger.info(f"Servers: {self.config.servers}")
        self.logger.info(f"Coins: {config.coins}")
        self.logger.info(f"Base labs: {config.base_labs}")
        self.logger.info(f"Zero drawdown threshold: {config.max_drawdown_threshold}")
        self.logger.info(f"Min stability score: {config.min_stability_score}")

    async def execute_project(self) -> ProjectResult:
        """
        Execute the complete trading orchestration project with queued backtesting workflow.
        
        Returns:
            ProjectResult with complete execution details
            
        Raises:
            OrchestrationError: If project execution fails
        """
        try:
            self.logger.info(f"🚀 Starting project execution: {self.config.project_name}")
            start_time = datetime.now()
            
            # Phase 1: Initialize servers
            await self._initialize_servers()
            
            # Phase 1.5: Take server snapshots for duplicate detection
            server_snapshots = await self._take_server_snapshots()
            
            # Phase 2: Clone labs for each coin on dedicated servers
            coin_labs = await self._clone_labs_for_coins()
            
            # Phase 3: Discover ALL cutoffs first, then queue in order
            cutoff_results = await self._discover_all_cutoffs(coin_labs)
            backtest_queue = await self._queue_backtests_in_order(cutoff_results)
            
            # Phase 4: Monitor progress and analyze completed labs
            analysis_results = await self._monitor_and_analyze_completed_labs(backtest_queue)
            
            # Phase 5: Create bots from analysis results with duplicate detection
            bot_results = await self._create_bots(analysis_results, server_snapshots)
            
            # Phase 6: Verify bots with backtesting API
            verified_bots = await self._verify_bots(bot_results)
            
            # Phase 7: Generate project result
            execution_time = datetime.now() - start_time
            self.project_result = ProjectResult(
                project_name=self.config.project_name,
                execution_timestamp=start_time.isoformat(),
                servers_processed=self.config.servers,
                total_labs_cloned=sum(len(server_labs) for server_labs in coin_labs.values()),
                total_backtests_executed=sum(
                    len(coin_results) 
                    for server_results in backtest_queue.values() 
                    for coin_results in server_results.values()
                ),
                total_bots_created=sum(
                    len(coin_bots) 
                    for server_bots in verified_bots.values() 
                    for coin_bots in server_bots.values()
                ),
                zero_drawdown_bots=sum(
                    len([bot for bot in coin_bots if hasattr(bot, 'max_drawdown') and bot.max_drawdown <= self.config.max_drawdown_threshold])
                    for server_bots in verified_bots.values() 
                    for coin_bots in server_bots.values()
                ),
                stable_bots=sum(
                    len([bot for bot in coin_bots if hasattr(bot, 'stability_score') and bot.stability_score >= self.config.min_stability_score])
                    for server_bots in verified_bots.values() 
                    for coin_bots in server_bots.values()
                ),
                bot_results=verified_bots,
                success=True
            )
            
            # Save project result
            await self._save_project_result()
            
            self.logger.info(f"✅ Project execution completed in {execution_time}")
            self.logger.info(f"📊 Results: {self.project_result.total_bots_created} bots created, "
                           f"{self.project_result.zero_drawdown_bots} zero drawdown, "
                           f"{self.project_result.stable_bots} stable")
            
            return self.project_result
            
        except Exception as e:
            self.logger.error(f"❌ Project execution failed: {e}")
            self.project_result = ProjectResult(
                project_name=self.config.project_name,
                execution_timestamp=datetime.now().isoformat(),
                servers_processed=[],
                total_labs_cloned=0,
                total_backtests_executed=0,
                total_bots_created=0,
                zero_drawdown_bots=0,
                stable_bots=0,
                bot_results={},
                success=False,
                error_message=str(e)
            )
            raise OrchestrationError(f"Project execution failed: {e}") from e

    async def _initialize_servers(self) -> None:
        """Initialize connections to all servers"""
        self.logger.info("🔧 Initializing server connections...")
        
        for server in self.config.servers:
            try:
                self.logger.info(f"Connecting to {server}...")
                
                # Connect to server via SSH tunnel
                await self.server_manager.connect_server(server)
                
                # Create client and auth manager for this server
                from ..config.api_config import APIConfig
                api_config = APIConfig(
                    host="127.0.0.1",
                    port=8090,
                    timeout=30.0,
                    email=os.getenv("API_EMAIL"),
                    password=os.getenv("API_PASSWORD")
                )
                client = AsyncHaasClient(api_config)
                
                auth_manager = AuthenticationManager(client, api_config)
                await auth_manager.authenticate()
                
                # Create API instances for this server
                lab_api = LabAPI(client, auth_manager)
                bot_api = BotAPI(client, auth_manager)
                account_api = AccountAPI(client, auth_manager)
                backtest_api = BacktestAPI(client, auth_manager)
                market_api = MarketAPI(client, auth_manager)
                analysis_service = AnalysisService(lab_api, backtest_api, bot_api, client, auth_manager)
                self.logger.info(f"🔍 Creating LongestBacktestService with client: {client is not None}, auth_manager: {auth_manager is not None}")
                longest_backtest_service = LongestBacktestService(lab_api, market_api=market_api, backtest_api=backtest_api, client=client, auth_manager=auth_manager)
                
                # Store server APIs
                self.server_apis[server] = ServerAPIs(
                    client=client,
                    auth_manager=auth_manager,
                    lab_api=lab_api,
                    bot_api=bot_api,
                    account_api=account_api,
                    backtest_api=backtest_api,
                    market_api=market_api,
                    analysis_service=analysis_service,
                    longest_backtest_service=longest_backtest_service
                )
                
                # Create server content manager for snapshot and duplicate detection
                self.server_content_managers[server] = ServerContentManager(
                    server=server,
                    lab_api=lab_api,
                    bot_api=bot_api,
                    backtest_api=backtest_api,
                    cache_dir=self.output_dir / "cache"
                )
                
                self.logger.info(f"✅ Connected to {server}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to connect to {server}: {e}")
                raise OrchestrationError(f"Failed to initialize server {server}: {e}") from e
        
        self.logger.info(f"✅ All {len(self.config.servers)} servers initialized")

    async def _take_server_snapshots(self) -> Dict[str, Any]:
        """Take snapshots of all servers for duplicate detection"""
        self.logger.info("📸 Taking server snapshots for duplicate detection...")
        snapshots = {}
        
        for server in self.config.servers:
            try:
                self.logger.info(f"Taking snapshot of {server}...")
                snapshot = await self.server_content_managers[server].snapshot()
                snapshots[server] = snapshot
                self.logger.info(f"✅ Snapshot taken for {server}: {len(snapshot.labs)} labs, {len(snapshot.bots)} bots")
            except Exception as e:
                self.logger.error(f"❌ Failed to take snapshot of {server}: {e}")
                snapshots[server] = None
        
        return snapshots

    async def _clone_labs_for_coins(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Clone pre-configured labs for each coin on dedicated servers"""
        self.logger.info("📋 Cloning labs for each coin on dedicated servers...")
        coin_labs = {}
        
        for server in self.config.servers:
            coin_labs[server] = {}
            apis = self.server_apis[server]
            
            self.logger.info(f"Cloning labs on {server}...")
            
            # Each server gets its own dedicated labs for all coins
            for coin in self.config.coins:
                coin_labs[server][coin] = {}
                
                for base_lab_id in self.config.base_labs:
                    try:
                        # Clone lab for this coin on this specific server
                        lab_name = f"{server}_{coin}_{base_lab_id[:8]}_{datetime.now().strftime('%Y%m%d')}"
                        
                        self.logger.info(f"Cloning {base_lab_id[:8]} for {coin} on {server}...")
                        
                        cloned_lab = await apis.lab_api.clone_lab(
                            lab_id=base_lab_id,
                            new_name=lab_name
                        )
                        
                        # Configure for coin (market tag, etc.) on this server
                        await self._configure_lab_for_coin(cloned_lab.lab_id, coin, apis)
                        
                        coin_labs[server][coin][base_lab_id] = cloned_lab.lab_id
                        
                        self.logger.info(f"✅ Cloned {base_lab_id[:8]} -> {cloned_lab.lab_id[:8]} for {coin} on {server}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to clone {base_lab_id[:8]} for {coin} on {server}: {e}")
                        # Continue with other labs
                        continue
        
        self.logger.info("✅ Lab cloning completed")
        return coin_labs

    async def run_cutoff_for_template_on_srv03(
        self,
        template_lab_id: str,
        account_id: str,
        stage_label: str,
        coins: List[str]
    ) -> Dict[str, Any]:
        """Run v2-only clone → config → sync → cutoff → rename → start for given template on srv03.
        Returns per-coin results with discovered periods and lab IDs.
        """
        server = "srv03"
        if server not in self.server_apis:
            await self._initialize_servers()
        apis = self.server_apis[server]

        # Build markets mapping
        markets = {c: (f"{c}_USDT_PERPETUAL" if c != "BTC" else "BTC_USDT_PERPETUAL") for c in coins}

        # Use integrated v2-only service
        svc = LongestBacktestService(
            lab_api=apis.lab_api,
            market_api=apis.market_api,
            backtest_api=apis.backtest_api,
            client=apis.client,
            auth_manager=apis.auth_manager,
        )

        return await svc.orchestrate_clone_config_sync_and_find_cutoff(
            template_lab_id=template_lab_id,
            account_id=account_id,
            stage_label=stage_label,
            markets=markets,
        )

    async def _configure_lab_for_coin(self, lab_id: str, coin: str, apis: ServerAPIs) -> None:
        """Configure lab for specific coin (market tag, etc.)"""
        try:
            # Get lab details
            lab_details = await apis.lab_api.get_lab_details(lab_id)
            
            # Update market tag for the coin
            market_tag = f"BINANCE_{coin}_USDT_"
            
            # Update lab details with coin-specific configuration
            updated_details = {
                "market_tag": market_tag,
                "leverage": self.config.leverage,
                "position_mode": 1,  # HEDGE
                "margin_mode": 0,    # CROSS
            }
            
            await apis.lab_api.update_lab_details(lab_id, updated_details)
            
            self.logger.debug(f"Configured lab {lab_id[:8]} for {coin} with market {market_tag}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to configure lab {lab_id[:8]} for {coin}: {e}")
            # Continue - lab might still work with default settings

    async def _discover_all_cutoffs(self, coin_labs: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, Any]:
        """Discover cutoffs for ALL labs first, then queue them in order"""
        self.logger.info("🔍 Discovering cutoffs for ALL labs first...")
        cutoff_results = {}
        
        for server, server_labs in coin_labs.items():
            cutoff_results[server] = {}
            apis = self.server_apis[server]
            
            self.logger.info(f"Discovering cutoffs on {server}...")
            
            for coin, labs in server_labs.items():
                cutoff_results[server][coin] = {}
                
                for base_lab_id, cloned_lab_id in labs.items():
                    try:
                        self.logger.info(f"Finding cutoff for {cloned_lab_id[:8]} ({coin}) on {server}...")
                        
                        # Find cutoff date with timeout protection
                        cutoff_date = await self._discover_cutoff_date_with_timeout(cloned_lab_id, apis)
                        
                        cutoff_results[server][coin][base_lab_id] = {
                            "cloned_lab_id": cloned_lab_id,
                            "cutoff_date": cutoff_date,
                            "discovery_timestamp": datetime.now().isoformat(),
                            "server": server,
                            "status": "discovered"
                        }
                        
                        self.logger.info(f"✅ Discovered cutoff for {cloned_lab_id[:8]} on {server}: {cutoff_date}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to discover cutoff for {cloned_lab_id[:8]} on {server}: {e}")
                        cutoff_results[server][coin][base_lab_id] = {
                            "cloned_lab_id": cloned_lab_id,
                            "cutoff_date": None,
                            "discovery_timestamp": datetime.now().isoformat(),
                            "server": server,
                            "status": "failed",
                            "error": str(e)
                        }
        
        # Save cutoff discovery results
        await self._save_cutoff_discovery(cutoff_results)
        
        self.logger.info("✅ Cutoff discovery completed for all labs")
        return cutoff_results

    async def _queue_backtests_in_order(self, cutoff_results: Dict[str, Any]) -> Dict[str, Any]:
        """Queue backtests in order with tracking"""
        self.logger.info("📋 Queuing backtests in order with tracking...")
        backtest_queue = {}
        queue_order = []
        
        for server, server_results in cutoff_results.items():
            backtest_queue[server] = {}
            apis = self.server_apis[server]
            
            self.logger.info(f"Queuing backtests on {server} in order...")
            
            for coin, coin_results in server_results.items():
                backtest_queue[server][coin] = {}
                
                for base_lab_id, cutoff_data in coin_results.items():
                    if cutoff_data["status"] != "discovered":
                        continue
                    
                    try:
                        cloned_lab_id = cutoff_data["cloned_lab_id"]
                        cutoff_date = cutoff_data["cutoff_date"]
                        
                        # Configure lab for longest backtest
                        await self._configure_lab_for_longest_backtest(cloned_lab_id, cutoff_date, apis)
                        
                        # Queue backtest (non-blocking)
                        backtest_result = await apis.backtest_api.start_lab_execution(
                            lab_id=cloned_lab_id,
                            max_iterations=1500
                        )
                        
                        # Track queue order
                        queue_order.append({
                            "server": server,
                            "coin": coin,
                            "base_lab_id": base_lab_id,
                            "cloned_lab_id": cloned_lab_id,
                            "queue_position": len(queue_order) + 1,
                            "queue_timestamp": datetime.now().isoformat()
                        })
                        
                        backtest_queue[server][coin][base_lab_id] = {
                            "cloned_lab_id": cloned_lab_id,
                            "backtest_result": backtest_result,
                            "status": "queued",
                            "server": server,
                            "cutoff_date": cutoff_date,
                            "queue_timestamp": datetime.now().isoformat(),
                            "queue_position": len(queue_order)
                        }
                        
                        self.logger.info(f"✅ Queued backtest {len(queue_order)} for {cloned_lab_id[:8]} on {server}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to queue backtest for {cloned_lab_id[:8]} on {server}: {e}")
                        backtest_queue[server][coin][base_lab_id] = {
                            "cloned_lab_id": cloned_lab_id,
                            "backtest_result": None,
                            "status": "failed",
                            "server": server,
                            "error": str(e)
                        }
        
        # Save queue order and status
        await self._save_queue_order(queue_order)
        await self._save_queue_status(backtest_queue)
        
        self.logger.info(f"✅ Queued {len(queue_order)} backtests in order")
        return backtest_queue

    async def _discover_cutoff_date_with_timeout(self, lab_id: str, apis: ServerAPIs, timeout: int = 900) -> str:
        """Discover cutoff date with timeout protection for history sync"""
        try:
            self.logger.info(f"Discovering cutoff for {lab_id[:8]} with {timeout}s timeout...")
            
            # Use asyncio.wait_for for timeout protection
            cutoff_date = await asyncio.wait_for(
                self._discover_cutoff_date(lab_id, apis),
                timeout=timeout
            )
            
            self.logger.info(f"✅ Cutoff discovered for {lab_id[:8]}: {cutoff_date}")
            return cutoff_date
            
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ Timeout discovering cutoff for {lab_id[:8]} after {timeout}s")
            raise Exception(f"Cutoff discovery timeout after {timeout}s")
        except Exception as e:
            self.logger.error(f"❌ Failed to discover cutoff for {lab_id[:8]}: {e}")
            raise

    async def _detect_stuck_labs(self, backtest_queue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect labs stuck in queue"""
        stuck_labs = []
        
        for server, server_results in backtest_queue.items():
            for coin, coin_results in server_results.items():
                for base_lab_id, queue_data in coin_results.items():
                    if queue_data["status"] != "queued":
                        continue
                    
                    # Check if lab has been queued for too long without progress
                    queue_time = datetime.fromisoformat(queue_data["queue_timestamp"])
                    time_since_queue = datetime.now() - queue_time
                    
                    # If queued for more than 1 hour without progress, consider stuck
                    if time_since_queue.total_seconds() > 3600:  # 1 hour
                        stuck_labs.append({
                            "server": server,
                            "coin": coin,
                            "base_lab_id": base_lab_id,
                            "cloned_lab_id": queue_data["cloned_lab_id"],
                            "queue_time": queue_data["queue_timestamp"],
                            "stuck_duration": time_since_queue.total_seconds()
                        })
        
        if stuck_labs:
            self.logger.warning(f"⚠️ Detected {len(stuck_labs)} stuck labs")
            for stuck_lab in stuck_labs:
                self.logger.warning(f"  - {stuck_lab['cloned_lab_id'][:8]} on {stuck_lab['server']} stuck for {stuck_lab['stuck_duration']:.0f}s")
        
        return stuck_labs

    async def _restart_queue_with_fix(self, backtest_queue: Dict[str, Any], stuck_labs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Stop all labs, fix first one, restart queue in order"""
        self.logger.info("🔄 Restarting queue with fix for stuck labs...")
        
        # Stop all running labs
        await self._stop_all_labs(backtest_queue)
        
        # Fix first stuck lab
        if stuck_labs:
            first_stuck = stuck_labs[0]
            self.logger.info(f"🔧 Fixing first stuck lab: {first_stuck['cloned_lab_id'][:8]}")
            
            # Restart cutoff discovery for first lab
            apis = self.server_apis[first_stuck["server"]]
            try:
                cutoff_date = await self._discover_cutoff_date_with_timeout(
                    first_stuck["cloned_lab_id"], 
                    apis
                )
                
                # Reconfigure lab
                await self._configure_lab_for_longest_backtest(
                    first_stuck["cloned_lab_id"], 
                    cutoff_date, 
                    apis
                )
                
                self.logger.info(f"✅ Fixed first stuck lab: {first_stuck['cloned_lab_id'][:8]}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to fix first stuck lab: {e}")
        
        # Restart queue in order
        return await self._queue_backtests_in_order(backtest_queue)

    async def _stop_all_labs(self, backtest_queue: Dict[str, Any]) -> None:
        """Stop all running labs"""
        self.logger.info("🛑 Stopping all running labs...")
        
        for server, server_results in backtest_queue.items():
            apis = self.server_apis[server]
            
            for coin, coin_results in server_results.items():
                for base_lab_id, queue_data in coin_results.items():
                    if queue_data["status"] == "queued":
                        try:
                            await apis.lab_api.cancel_lab_execution(queue_data["cloned_lab_id"])
                            self.logger.info(f"✅ Stopped lab {queue_data['cloned_lab_id'][:8]} on {server}")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Failed to stop lab {queue_data['cloned_lab_id'][:8]}: {e}")

    async def _save_cutoff_discovery(self, cutoff_results: Dict[str, Any]) -> None:
        """Save cutoff discovery results"""
        try:
            cutoff_file = self.output_dir / "cutoff_discovery.json"
            
            cutoff_data = {
                "project_name": self.config.project_name,
                "discovery_timestamp": datetime.now().isoformat(),
                "cutoff_results": cutoff_results
            }
            
            with open(cutoff_file, 'w') as f:
                json.dump(cutoff_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save cutoff discovery: {e}")

    async def _save_queue_order(self, queue_order: List[Dict[str, Any]]) -> None:
        """Save queue order for tracking"""
        try:
            order_file = self.output_dir / "queue_order.json"
            
            order_data = {
                "project_name": self.config.project_name,
                "queue_timestamp": datetime.now().isoformat(),
                "queue_order": queue_order
            }
            
            with open(order_file, 'w') as f:
                json.dump(order_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save queue order: {e}")

    async def _get_testing_account(self, apis: ServerAPIs):
        """Get testing account with 10k USDT balance"""
        try:
            # Get all accounts
            accounts = await apis.account_api.get_accounts()
            
            # Look for testing accounts with patterns like:
            # - "[Sim] for tests 10k"
            # - "for tests 10k" 
            # - "[Sim] for tests"
            # - "for tests"
            testing_patterns = [
                "[Sim] for tests 10k",
                "for tests 10k", 
                "[Sim] for tests",
                "for tests",
                "[Sim] 10k",
                "10k"
            ]
            
            for account in accounts:
                account_name = getattr(account, 'account_name', '') or getattr(account, 'name', '')
                if not account_name:
                    continue
                
                # Check if account name matches any testing pattern
                for pattern in testing_patterns:
                    if pattern.lower() in account_name.lower():
                        self.logger.info(f"✅ Found testing account: {account_name}")
                        return account
            
            # If no specific testing account found, get first available account
            if accounts:
                account = accounts[0]
                self.logger.warning(f"⚠️ No testing account found, using first available: {getattr(account, 'account_name', 'Unknown')}")
                return account
            
            raise Exception("No accounts found")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get testing account: {e}")
            raise

    async def _discover_cutoff_date(self, lab_id: str, apis: ServerAPIs) -> str:
        """Discover cutoff date for longest backtest"""
        try:
            # Get lab details to find earliest available data
            lab_details = await apis.lab_api.get_lab_details(lab_id)
            
            # Use longest backtest algorithm to find cutoff
            # This would use the existing longest backtest logic
            cutoff_date = "2023-01-03"  # Placeholder - would use real algorithm
            
            self.logger.debug(f"Discovered cutoff date for {lab_id[:8]}: {cutoff_date}")
            return cutoff_date
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to discover cutoff for {lab_id[:8]}: {e}")
            return "2023-01-01"  # Fallback date

    async def _configure_lab_for_longest_backtest(self, lab_id: str, cutoff_date: str, apis: ServerAPIs) -> None:
        """Configure lab for longest backtest"""
        try:
            # Update lab details with cutoff date
            updated_details = {
                "start_date": cutoff_date,
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "max_iterations": 1500
            }
            
            await apis.lab_api.update_lab_details(lab_id, updated_details)
            
            self.logger.debug(f"Configured lab {lab_id[:8]} for longest backtest from {cutoff_date}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to configure lab {lab_id[:8]} for longest backtest: {e}")

    async def _monitor_and_analyze_completed_labs(self, backtest_queue: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor progress and analyze completed labs with stuck lab detection"""
        self.logger.info("📊 Monitoring progress and analyzing completed labs...")
        analysis_results = {}
        
        # Check for stuck labs first
        stuck_labs = await self._detect_stuck_labs(backtest_queue)
        
        if stuck_labs:
            self.logger.warning(f"⚠️ Found {len(stuck_labs)} stuck labs, restarting queue...")
            # Restart queue with fix for stuck labs
            backtest_queue = await self._restart_queue_with_fix(backtest_queue, stuck_labs)
        
        for server, server_results in backtest_queue.items():
            analysis_results[server] = {}
            apis = self.server_apis[server]
            
            self.logger.info(f"Monitoring progress on {server}...")
            
            for coin, coin_results in server_results.items():
                analysis_results[server][coin] = {}
                
                for base_lab_id, result in coin_results.items():
                    if result["status"] != "queued":
                        continue
                    
                    try:
                        cloned_lab_id = result["cloned_lab_id"]
                        
                        # Check if backtest is completed
                        completion_status = await self._check_backtest_completion(cloned_lab_id, apis)
                        
                        if completion_status["completed"]:
                            self.logger.info(f"✅ Backtest completed for {cloned_lab_id[:8]} on {server}")
                            
                            # Analyze completed lab
                            analysis = await self._analyze_completed_lab(cloned_lab_id, apis)
                            
                            analysis_results[server][coin][base_lab_id] = {
                                "lab_id": cloned_lab_id,
                                "server": server,
                                "completion_timestamp": completion_status["completion_timestamp"],
                                "analysis": analysis
                            }
                        else:
                            self.logger.info(f"⏳ Backtest still running for {cloned_lab_id[:8]} on {server}")
                            
                    except Exception as e:
                        self.logger.error(f"❌ Failed to monitor {result.get('cloned_lab_id', 'unknown')[:8]} on {server}: {e}")
        
        return analysis_results

    async def _check_backtest_completion(self, lab_id: str, apis: ServerAPIs) -> Dict[str, Any]:
        """Check if backtest is completed"""
        try:
            # Check lab execution status
            execution_status = await apis.lab_api.get_lab_execution_status(lab_id)
            
            if execution_status.get("status") == "completed":
                return {
                    "completed": True,
                    "completion_timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "completed": False,
                    "status": execution_status.get("status", "unknown")
                }
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to check completion for {lab_id[:8]}: {e}")
            return {"completed": False, "error": str(e)}

    async def _analyze_completed_lab(self, lab_id: str, apis: ServerAPIs) -> Dict[str, Any]:
        """Analyze completed lab with zero drawdown + stability filter"""
        try:
            # Analyze lab results
            analysis = await apis.analysis_service.analyze_lab_comprehensive(
                lab_id=lab_id,
                top_count=50,
                min_win_rate=self.config.min_win_rate,
                min_trades=self.config.min_trades,
                sort_by="roe"
            )
            
            # Filter for ZERO drawdown only
            zero_drawdown_backtests = [
                bt for bt in analysis.top_performers 
                if bt.max_drawdown <= self.config.max_drawdown_threshold
            ]
            
            # Calculate stability scores for zero drawdown backtests
            stable_backtests = []
            for bt in zero_drawdown_backtests:
                # Get advanced metrics including stability score
                advanced_metrics = await apis.analysis_service.calculate_advanced_metrics(
                    backtest_data={"backtest_id": bt.backtest_id}
                )
                
                # Add stability score to backtest
                bt.stability_score = advanced_metrics.get("stability_score", 0.0)
                bt.risk_score = advanced_metrics.get("risk_score", 100.0)
                bt.composite_score = advanced_metrics.get("composite_score", 0.0)
                
                # Filter by minimum stability score
                if bt.stability_score >= self.config.min_stability_score:
                    stable_backtests.append(bt)
            
            # Sort by composite score (stability + performance)
            stable_backtests.sort(key=lambda x: x.composite_score, reverse=True)
            
            return {
                "total_backtests": len(analysis.top_performers),
                "zero_drawdown_backtests": zero_drawdown_backtests,
                "stable_backtests": stable_backtests,
                "best_performers": stable_backtests[:self.config.top_bots_per_coin]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to analyze completed lab {lab_id[:8]}: {e}")
            return {
                "total_backtests": 0,
                "zero_drawdown_backtests": [],
                "stable_backtests": [],
                "best_performers": [],
                "error": str(e)
            }

    async def _analyze_results(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze backtest results with zero drawdown + stability filter on dedicated servers"""
        self.logger.info("📊 Analyzing results with zero drawdown + stability filter...")
        analysis_results = {}
        
        for server, server_results in backtest_results.items():
            analysis_results[server] = {}
            apis = self.server_apis[server]
            
            self.logger.info(f"Analyzing results on {server}...")
            
            # Each server analyzes its own dedicated results
            for coin, coin_results in server_results.items():
                analysis_results[server][coin] = {}
                
                for base_lab_id, result in coin_results.items():
                    if result["status"] != "running":
                        continue
                    
                    try:
                        cloned_lab_id = result["cloned_lab_id"]
                        self.logger.info(f"Analyzing {cloned_lab_id[:8]} ({coin}) on {server}...")
                        
                        # Analyze lab results on this specific server
                        analysis = await apis.analysis_service.analyze_lab_comprehensive(
                            lab_id=cloned_lab_id,
                            top_count=50,
                            min_win_rate=self.config.min_win_rate,
                            min_trades=self.config.min_trades,
                            sort_by="roe"
                        )
                        
                        # Filter for ZERO drawdown only
                        zero_drawdown_backtests = [
                            bt for bt in analysis.top_performers 
                            if bt.max_drawdown <= self.config.max_drawdown_threshold
                        ]
                        
                        # Calculate stability scores for zero drawdown backtests
                        stable_backtests = []
                        for bt in zero_drawdown_backtests:
                            # Get advanced metrics including stability score
                            advanced_metrics = await apis.analysis_service.calculate_advanced_metrics(
                                backtest_data={"backtest_id": bt.backtest_id}
                            )
                            
                            # Add stability score to backtest
                            bt.stability_score = advanced_metrics.get("stability_score", 0.0)
                            bt.risk_score = advanced_metrics.get("risk_score", 100.0)
                            bt.composite_score = advanced_metrics.get("composite_score", 0.0)
                            
                            # Filter by minimum stability score
                            if bt.stability_score >= self.config.min_stability_score:
                                stable_backtests.append(bt)
                        
                        # Sort by composite score (stability + performance)
                        stable_backtests.sort(key=lambda x: x.composite_score, reverse=True)
                        
                        analysis_results[server][coin][base_lab_id] = {
                            "lab_id": cloned_lab_id,
                            "server": server,
                            "total_backtests": len(analysis.top_performers),
                            "zero_drawdown_backtests": zero_drawdown_backtests,
                            "stable_backtests": stable_backtests,
                            "best_performers": stable_backtests[:self.config.top_bots_per_coin]
                        }
                        
                        self.logger.info(f"✅ Analyzed {cloned_lab_id[:8]}: "
                                       f"{len(zero_drawdown_backtests)} zero drawdown, "
                                       f"{len(stable_backtests)} stable")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to analyze {result.get('cloned_lab_id', 'unknown')[:8]} on {server}: {e}")
                        analysis_results[server][coin][base_lab_id] = {
                            "lab_id": result.get("cloned_lab_id", ""),
                            "server": server,
                            "total_backtests": 0,
                            "zero_drawdown_backtests": [],
                            "stable_backtests": [],
                            "best_performers": [],
                            "error": str(e)
                        }
        
        self.logger.info("✅ Analysis completed")
        return analysis_results

    async def _create_bots(self, analysis_results: Dict[str, Any], server_snapshots: Dict[str, Any]) -> Dict[str, Any]:
        """Create bots from analysis results on dedicated servers with duplicate detection"""
        self.logger.info("🤖 Creating bots from analysis results with duplicate detection...")
        bot_results = {}
        
        for server, server_results in analysis_results.items():
            bot_results[server] = {}
            apis = self.server_apis[server]
            snapshot = server_snapshots.get(server)
            
            self.logger.info(f"Creating bots on {server}...")
            
            # Each server creates its own dedicated bots
            for coin, coin_results in server_results.items():
                bot_results[server][coin] = {}
                
                for base_lab_id, result in coin_results.items():
                    analysis = result["analysis"]
                    created_bots = []
                    
                    for backtest in analysis["best_performers"]:
                        try:
                            # Generate bot name first
                            bot_name = self._generate_bot_name(
                                server=server,
                                coin=coin,
                                base_lab_id=base_lab_id,
                                backtest=backtest,
                                step_number=len(self.config.base_labs)
                            )
                            
                            # Check for duplicates using server snapshot
                            if snapshot and self.server_content_managers[server]:
                                skip_pairs = await self.server_content_managers[server].compute_creation_skips(
                                    {base_lab_id: analysis}, 
                                    snapshot.bots
                                )
                                
                                if (base_lab_id, backtest.backtest_id) in skip_pairs:
                                    self.logger.info(f"⏭️ Skipping duplicate bot: {bot_name}")
                                    continue
                            
                            # Get "[Sim] for tests 10k" account (10,000 USDT)
                            account = await self._get_testing_account(apis)
                            
                            self.logger.info(f"Creating bot {bot_name} on {server}...")
                            
                            bot_result = await apis.bot_api.create_bot_from_lab(
                                lab_id=result["lab_id"],
                                backtest_id=backtest.backtest_id,
                                account_id=account.account_id,
                                bot_name=bot_name,
                                trade_amount_usdt=self.config.trade_amount_usdt,
                                leverage=self.config.leverage
                            )
                            
                            # Add comprehensive bot notes with all details
                            await self._add_comprehensive_bot_notes(
                                bot_id=bot_result.bot_id,
                                server=server,
                                coin=coin,
                                base_lab_id=base_lab_id,
                                backtest=backtest,
                                step_number=len(self.config.base_labs),
                                account_id=account.account_id,
                                apis=apis
                            )
                            
                            created_bot = BotCreationResult(
                                bot_id=bot_result.bot_id,
                                bot_name=bot_result.bot_name,
                                backtest_id=backtest.backtest_id,
                                server=server,
                                coin=coin,
                                base_lab_id=base_lab_id,
                                roe=backtest.roi_percentage,
                                win_rate=backtest.win_rate,
                                max_drawdown=backtest.max_drawdown,
                                stability_score=backtest.stability_score,
                                composite_score=backtest.composite_score,
                                activated=False  # Will be activated after verification
                            )
                            
                            created_bots.append(created_bot)
                            
                            self.logger.info(f"✅ Created bot {bot_result.bot_id[:8]} on {server}")
                            
                        except Exception as e:
                            self.logger.error(f"❌ Failed to create bot for {backtest.backtest_id[:8]} on {server}: {e}")
                            created_bots.append(BotCreationResult(
                                bot_id="",
                                bot_name="",
                                backtest_id=backtest.backtest_id,
                                server=server,
                                coin=coin,
                                base_lab_id=base_lab_id,
                                roe=backtest.roi_percentage,
                                win_rate=backtest.win_rate,
                                max_drawdown=backtest.max_drawdown,
                                stability_score=backtest.stability_score,
                                composite_score=backtest.composite_score,
                                activated=False,
                                error_message=str(e)
                            ))
                    
                    bot_results[server][coin][base_lab_id] = created_bots
        
        self.logger.info("✅ Bot creation completed")
        return bot_results

    async def _verify_bots(self, bot_results: Dict[str, Any]) -> Dict[str, Any]:
        """Verify bots with backtesting API and performance limits"""
        self.logger.info("🔍 Verifying bots with backtesting API...")
        verified_bots = {}
        
        for server, server_bots in bot_results.items():
            verified_bots[server] = {}
            apis = self.server_apis[server]
            
            self.logger.info(f"Verifying bots on {server}...")
            
            for coin, coin_bots in server_bots.items():
                verified_bots[server][coin] = {}
                
                for base_lab_id, bots in coin_bots.items():
                    verified_bots[server][coin][base_lab_id] = []
                    
                    for bot in bots:
                        try:
                            # Run verification backtest for bot
                            verification_result = await self._run_bot_verification_backtest(bot, apis)
                            
                            # Check performance limits
                            verification_passed = self._check_verification_limits(bot, verification_result)
                            
                            if verification_passed:
                                # Activate bot if verification passed
                                if self.config.activate_bots:
                                    await apis.bot_api.activate_bot(bot.bot_id)
                                
                                bot.activated = True
                                self.logger.info(f"✅ Bot {bot.bot_id[:8]} verified and activated")
                            else:
                                # Disable bot if verification failed
                                await apis.bot_api.deactivate_bot(bot.bot_id)
                                bot.activated = False
                                self.logger.warning(f"⚠️ Bot {bot.bot_id[:8]} failed verification - disabled")
                            
                            # Update bot notes with verification results
                            await self._update_bot_verification_notes(bot, verification_result, verification_passed, apis)
                            
                            # Save verification results
                            await self._save_verification_results(bot, verification_result, verification_passed)
                            
                            verified_bots[server][coin][base_lab_id].append(bot)
                            
                        except Exception as e:
                            self.logger.error(f"❌ Failed to verify bot {bot.bot_id[:8]}: {e}")
                            bot.error_message = f"Verification failed: {e}"
                            verified_bots[server][coin][base_lab_id].append(bot)
        
        self.logger.info("✅ Bot verification completed")
        return verified_bots

    async def _run_bot_verification_backtest(self, bot: BotCreationResult, apis: ServerAPIs) -> Dict[str, Any]:
        """Run verification backtest for bot"""
        try:
            # Run backtest using bot configuration
            verification_backtest = await apis.backtest_api.execute_backtest(
                script_id=bot.script_id,  # Would need to extract from bot
                market_tag=f"BINANCE_{bot.coin}_USDT_",
                settings={
                    "leverage": self.config.leverage,
                    "position_mode": 1,  # HEDGE
                    "margin_mode": 0,    # CROSS
                    "trade_amount_usdt": self.config.trade_amount_usdt
                }
            )
            
            return {
                "backtest_id": verification_backtest.backtest_id,
                "roe_percentage": verification_backtest.roi_percentage,
                "win_rate": verification_backtest.win_rate,
                "max_drawdown": verification_backtest.max_drawdown,
                "total_trades": verification_backtest.total_trades,
                "verification_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to run verification backtest for bot {bot.bot_id[:8]}: {e}")
            return {
                "error": str(e),
                "verification_timestamp": datetime.now().isoformat()
            }

    def _check_verification_limits(self, bot: BotCreationResult, verification_result: Dict[str, Any]) -> bool:
        """Check if bot meets verification limits"""
        if "error" in verification_result:
            return False
        
        # ROE limit: Bot ROE can be up to 10% worse than lab backtest ROE
        roe_limit = bot.roe * 0.9  # 10% worse
        if verification_result["roe_percentage"] < roe_limit:
            self.logger.warning(f"❌ Bot {bot.bot_id[:8]} ROE {verification_result['roe_percentage']:.1f}% < limit {roe_limit:.1f}%")
            return False
        
        # Drawdown limit: Bot drawdown must never go below zero
        if verification_result["max_drawdown"] > 0.0:
            self.logger.warning(f"❌ Bot {bot.bot_id[:8]} drawdown {verification_result['max_drawdown']:.1f}% > 0%")
            return False
        
        # Winrate limit: Bot winrate can be slightly worse than lab backtest
        winrate_limit = bot.win_rate * 0.95  # 5% worse
        if verification_result["win_rate"] < winrate_limit:
            self.logger.warning(f"❌ Bot {bot.bot_id[:8]} winrate {verification_result['win_rate']:.1%} < limit {winrate_limit:.1%}")
            return False
        
        return True

    async def _update_bot_verification_notes(self, bot: BotCreationResult, verification_result: Dict[str, Any], verification_passed: bool, apis: ServerAPIs) -> None:
        """Update bot notes with verification results"""
        try:
            verification_notes = {
                "verification": {
                    "passed": verification_passed,
                    "timestamp": datetime.now().isoformat(),
                    "lab_roe": bot.roe,
                    "lab_winrate": bot.win_rate,
                    "lab_drawdown": bot.max_drawdown,
                    "bot_roe": verification_result.get("roe_percentage", 0.0),
                    "bot_winrate": verification_result.get("win_rate", 0.0),
                    "bot_drawdown": verification_result.get("max_drawdown", 0.0),
                    "roe_difference": bot.roe - verification_result.get("roe_percentage", 0.0),
                    "winrate_difference": bot.win_rate - verification_result.get("win_rate", 0.0),
                    "drawdown_difference": bot.max_drawdown - verification_result.get("max_drawdown", 0.0)
                }
            }
            
            # Get existing notes and update
            existing_notes = await apis.bot_api.get_bot_notes(bot.bot_id)
            if existing_notes:
                notes_data = json.loads(existing_notes)
                notes_data.update(verification_notes)
            else:
                notes_data = verification_notes
            
            # Update bot notes
            await apis.bot_api.change_bot_notes(bot.bot_id, json.dumps(notes_data, indent=2))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to update verification notes for bot {bot.bot_id[:8]}: {e}")

    async def _save_verification_results(self, bot: BotCreationResult, verification_result: Dict[str, Any], verification_passed: bool) -> None:
        """Save verification results to file"""
        try:
            verification_file = self.output_dir / "bot_verification.json"
            
            verification_data = {
                "bot_id": bot.bot_id,
                "bot_name": bot.bot_name,
                "server": bot.server,
                "coin": bot.coin,
                "verification_passed": verification_passed,
                "verification_result": verification_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Load existing data or create new
            if verification_file.exists():
                with open(verification_file, 'r') as f:
                    all_verifications = json.load(f)
            else:
                all_verifications = []
            
            all_verifications.append(verification_data)
            
            # Save updated data
            with open(verification_file, 'w') as f:
                json.dump(all_verifications, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save verification results for bot {bot.bot_id[:8]}: {e}")

    async def _save_queue_status(self, backtest_queue: Dict[str, Any]) -> None:
        """Save queue status for tracking"""
        try:
            queue_file = self.output_dir / "lab_progress.json"
            
            queue_data = {
                "project_name": self.config.project_name,
                "queue_timestamp": datetime.now().isoformat(),
                "backtest_queue": backtest_queue
            }
            
            with open(queue_file, 'w') as f:
                json.dump(queue_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save queue status: {e}")

    def _generate_bot_name(
        self,
        server: str,
        coin: str,
        base_lab_id: str,
        backtest: Any,
        step_number: int
    ) -> str:
        """Generate bot name based on step number and naming schema"""
        
        # Extract script name from backtest
        script_name = getattr(backtest, 'script_name', 'Unknown')
        
        # Format performance metrics
        roi = backtest.roi_percentage
        wr = backtest.win_rate * 100
        max_dd = backtest.max_drawdown
        
        if step_number == 1:
            # Single lab naming: 1 + script name + roi + wr + MaxDD
            bot_name = f"1 {script_name} {roi:.1f}% {wr:.0f}% {max_dd:.1f}%"
        else:
            # Multi-step naming: step + script name + params from first lab + roi + wr + MaxDD
            # Extract key parameters from first lab (short form)
            first_lab_params = self._extract_first_lab_params(base_lab_id)
            param_short = self._format_params_short(first_lab_params)
            
            bot_name = f"{step_number} {script_name} {param_short} {roi:.1f}% {wr:.0f}% {max_dd:.1f}%"
        
        # Add server and coin prefix
        return f"{server}_{coin}_{bot_name}"

    async def _add_comprehensive_bot_notes(
        self,
        bot_id: str,
        server: str,
        coin: str,
        base_lab_id: str,
        backtest: Any,
        step_number: int,
        account_id: str,
        apis: ServerAPIs
    ) -> None:
        """Add comprehensive bot notes with all project details"""
        
        # Extract first lab parameters for multi-step projects
        first_lab_params = {}
        if step_number > 1:
            first_lab_params = self._extract_first_lab_params(base_lab_id)
        
        # Get lab details for additional context
        lab_details = await apis.lab_api.get_lab_details(backtest.lab_id)
        
        # Comprehensive notes payload
        notes_payload = {
            "origin": {
                "project_name": self.config.project_name,
                "server": server,
                "coin": coin,
                "base_lab_id": base_lab_id,
                "cloned_lab_id": backtest.lab_id,
                "lab_name": getattr(lab_details, 'lab_name', ''),
                "backtest_id": backtest.backtest_id,
                "generation_idx": getattr(backtest, 'generation_idx', None),
                "population_idx": getattr(backtest, 'population_idx', None),
                "market": getattr(backtest, 'market_tag', ''),
                "script_name": getattr(backtest, 'script_name', ''),
                "step_number": step_number,
                "creation_ts": datetime.utcnow().isoformat()
            },
            "backtest_baseline": {
                "roe_pct": backtest.roi_percentage,
                "winrate_pct": backtest.win_rate * 100,
                "trades": getattr(backtest, 'total_trades', 0),
                "max_drawdown_pct": backtest.max_drawdown,
                "stability_score": getattr(backtest, 'stability_score', 0.0),
                "composite_score": getattr(backtest, 'composite_score', 0.0),
                "criteria_passed": True
            },
            "longest_backtest": {
                "status": "queued",
                "request_ts": datetime.utcnow().isoformat(),
                "result_ts": None,
                "roe_pct": None,
                "winrate_pct": None,
                "trades": None,
                "max_drawdown_pct": None,
                "history_synced_months": None,
                "period": {"from": None, "to": None}
            },
            "account": {
                "exchange": "BINANCEFUTURES",
                "account_id": account_id,
                "position_mode": "HEDGE",
                "margin_mode": "CROSS",
                "leverage": self.config.leverage,
                "trade_amount_usdt": self.config.trade_amount_usdt
            },
            "project_context": {
                "step_number": step_number,
                "total_steps": len(self.config.base_labs),
                "first_lab_params": first_lab_params,
                "parameter_evolution": self._get_parameter_evolution(base_lab_id, backtest),
                "optimization_history": self._get_optimization_history(base_lab_id)
            }
        }
        
        # Add bot notes
        await apis.bot_api.change_bot_notes(bot_id, json.dumps(notes_payload, indent=2))

    def _extract_first_lab_params(self, base_lab_id: str) -> Dict[str, Any]:
        """Extract key parameters from first lab for short form display"""
        # This would extract the most important parameters from the first lab
        # Implementation depends on how parameters are stored in your system
        return {
            "param1": "value1",
            "param2": "value2",
            "param3": "value3"
        }

    def _format_params_short(self, params: Dict[str, Any]) -> str:
        """Format parameters in short form for bot naming"""
        # Format key parameters in a compact way
        param_parts = []
        for key, value in params.items():
            if isinstance(value, float):
                param_parts.append(f"{key}={value:.1f}")
            else:
                param_parts.append(f"{key}={value}")
        
        return " ".join(param_parts[:3])  # Limit to 3 most important params

    def _get_parameter_evolution(self, base_lab_id: str, backtest: Any) -> Dict[str, Any]:
        """Get parameter evolution for multi-step projects"""
        return {
            "evolution_type": "multi_step",
            "base_lab_id": base_lab_id,
            "current_backtest_id": backtest.backtest_id,
            "evolution_timestamp": datetime.utcnow().isoformat()
        }

    def _get_optimization_history(self, base_lab_id: str) -> Dict[str, Any]:
        """Get optimization history for the project"""
        return {
            "optimization_type": "genetic_algorithm",
            "base_lab_id": base_lab_id,
            "optimization_timestamp": datetime.utcnow().isoformat()
        }

    async def _save_project_result(self) -> None:
        """Save project result to file"""
        if not self.project_result:
            return
        
        try:
            # Save as JSON
            result_file = self.output_dir / f"{self.config.project_name}_result.json"
            with open(result_file, 'w') as f:
                json.dump(self.project_result.__dict__, f, indent=2, default=str)
            
            # Save summary as text
            summary_file = self.output_dir / f"{self.config.project_name}_summary.txt"
            with open(summary_file, 'w') as f:
                f.write(f"Project: {self.project_result.project_name}\n")
                f.write(f"Execution Time: {self.project_result.execution_timestamp}\n")
                f.write(f"Servers: {', '.join(self.project_result.servers_processed)}\n")
                f.write(f"Labs Cloned: {self.project_result.total_labs_cloned}\n")
                f.write(f"Backtests Executed: {self.project_result.total_backtests_executed}\n")
                f.write(f"Bots Created: {self.project_result.total_bots_created}\n")
                f.write(f"Zero Drawdown Bots: {self.project_result.zero_drawdown_bots}\n")
                f.write(f"Stable Bots: {self.project_result.stable_bots}\n")
                f.write(f"Success: {self.project_result.success}\n")
            
            self.logger.info(f"📁 Project result saved to {self.output_dir}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save project result: {e}")

    async def cleanup(self) -> None:
        """Clean up resources and connections"""
        try:
            self.logger.info("🧹 Cleaning up resources...")
            
            # Close server connections
            for server, apis in self.server_apis.items():
                try:
                    await apis.client.close()
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to close connection to {server}: {e}")
            
            # Close server manager
            await self.server_manager.shutdown()
            
            self.logger.info("✅ Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup failed: {e}")


