"""
Comprehensive Data Manager for pyHaasAPI v2

This module provides a unified data management system that can:
- Connect to multiple servers
- Fetch and cache all relevant data (labs, bots, accounts, backtests)
- Manage data updates and synchronization
- Handle rate limiting and connection management
- Provide efficient data access across the entire API
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

from .server_manager import ServerManager
from .client import AsyncHaasClient
from .auth import AuthenticationManager
from ..config.settings import Settings
from ..exceptions import DataManagerError, ConnectionError
from ..core.logging import get_logger


@dataclass
class ServerData:
    """Data structure for server information"""
    server_name: str
    labs: List[Dict[str, Any]] = field(default_factory=list)
    bots: List[Dict[str, Any]] = field(default_factory=list)
    accounts: List[Dict[str, Any]] = field(default_factory=list)
    backtests: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)  # lab_id -> backtests
    last_updated: Optional[datetime] = None
    connection_status: str = "disconnected"


@dataclass
class DataManagerConfig:
    """Configuration for DataManager"""
    cache_duration_minutes: int = 30
    max_concurrent_requests: int = 5
    request_delay_seconds: float = 0.5
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    auto_refresh: bool = True
    refresh_interval_minutes: int = 15


class ComprehensiveDataManager:
    """
    Comprehensive Data Manager for pyHaasAPI v2
    
    Features:
    - Multi-server data management
    - Intelligent caching and synchronization
    - Rate limiting and connection management
    - Background data updates
    - Efficient data access patterns
    - Lab and bot status monitoring
    - Backtest result management
    """
    
    def __init__(self, settings: Settings, config: Optional[DataManagerConfig] = None):
        self.settings = settings
        self.config = config or DataManagerConfig()
        self.logger = get_logger("data_manager")
        
        # Server management
        self.server_manager = ServerManager(settings)
        self.servers_data: Dict[str, ServerData] = {}
        self.active_connections: Dict[str, AsyncHaasClient] = {}
        
        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.refresh_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        
        # Rate limiting
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.last_request_time = 0.0
    
    async def initialize(self) -> bool:
        """Initialize the data manager"""
        try:
            self.logger.info("Initializing Comprehensive Data Manager...")
            
            # Start server monitoring
            await self.server_manager.start_monitoring()
            
            # Initialize server data structures
            for server_name in ["srv01", "srv02", "srv03"]:
                self.servers_data[server_name] = ServerData(server_name=server_name)
            
            # Start background tasks
            if self.config.auto_refresh:
                self.refresh_task = asyncio.create_task(self._background_refresh())
            
            self.logger.info("Data Manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Data Manager: {e}")
            return False
    
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to a specific server and authenticate"""
        try:
            self.logger.info(f"Connecting to server {server_name}...")
            
            # Establish SSH tunnel
            if not await self.server_manager.connect_server(server_name):
                self.logger.error(f"Failed to establish SSH tunnel to {server_name}")
                return False
            
            # Create client
            from ..config.api_config import APIConfig
            config = APIConfig(host='127.0.0.1', port=8090)
            client = AsyncHaasClient(config)
            
            # Authenticate
            auth_manager = AuthenticationManager(client, config)
            await auth_manager.authenticate()
            
            # Store connection
            self.active_connections[server_name] = client
            self.servers_data[server_name].connection_status = "connected"
            
            self.logger.info(f"Successfully connected to {server_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {server_name}: {e}")
            self.servers_data[server_name].connection_status = "failed"
            return False
    
    async def fetch_all_server_data(self, server_name: str) -> bool:
        """Fetch all data from a server"""
        try:
            if server_name not in self.active_connections:
                self.logger.error(f"No active connection to {server_name}")
                return False
            
            client = self.active_connections[server_name]
            server_data = self.servers_data[server_name]
            
            self.logger.info(f"Fetching all data from {server_name}...")
            
            # Fetch labs
            await self._fetch_labs(client, server_data)
            
            # Fetch bots
            await self._fetch_bots(client, server_data)
            
            # Fetch accounts
            await self._fetch_accounts(client, server_data)
            
            # Fetch backtests for each lab
            await self._fetch_all_backtests(client, server_data)
            
            # Update timestamp
            server_data.last_updated = datetime.now()
            
            self.logger.info(f"Successfully fetched all data from {server_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fetch data from {server_name}: {e}")
            return False
    
    async def _fetch_labs(self, client: AsyncHaasClient, server_data: ServerData):
        """Fetch all labs from server"""
        try:
            from ..api.lab import LabAPI
            lab_api = LabAPI(client)
            
            labs = await lab_api.get_all_labs()
            server_data.labs = [lab.model_dump() for lab in labs]
            
            self.logger.info(f"Fetched {len(server_data.labs)} labs")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch labs: {e}")
    
    async def _fetch_bots(self, client: AsyncHaasClient, server_data: ServerData):
        """Fetch all bots from server"""
        try:
            from ..api.bot import BotAPI
            bot_api = BotAPI(client)
            
            bots = await bot_api.get_all_bots()
            server_data.bots = [bot.model_dump() for bot in bots]
            
            self.logger.info(f"Fetched {len(server_data.bots)} bots")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch bots: {e}")
    
    async def _fetch_accounts(self, client: AsyncHaasClient, server_data: ServerData):
        """Fetch all accounts from server"""
        try:
            from ..api.account import AccountAPI
            account_api = AccountAPI(client)
            
            accounts = await account_api.get_all_accounts()
            server_data.accounts = [account.model_dump() for account in accounts]
            
            self.logger.info(f"Fetched {len(server_data.accounts)} accounts")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch accounts: {e}")
    
    async def _fetch_all_backtests(self, client: AsyncHaasClient, server_data: ServerData):
        """Fetch backtests for all labs"""
        try:
            from ..api.backtest import BacktestAPI
            backtest_api = BacktestAPI(client)
            
            total_backtests = 0
            for lab in server_data.labs:
                lab_id = lab.get('lab_id')
                if not lab_id:
                    continue
                
                try:
                    # Fetch backtests for this lab
                    backtests = await backtest_api.get_backtest_results(lab_id)
                    server_data.backtests[lab_id] = [bt.model_dump() for bt in backtests]
                    total_backtests += len(server_data.backtests[lab_id])
                    
                    # Rate limiting
                    await self._rate_limit()
                    
                except Exception as e:
                    self.logger.warning(f"Failed to fetch backtests for lab {lab_id}: {e}")
                    continue
            
            self.logger.info(f"Fetched {total_backtests} total backtests")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch backtests: {e}")
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.request_delay_seconds:
            await asyncio.sleep(self.config.request_delay_seconds - time_since_last)
        
        self.last_request_time = time.time()
    
    async def get_qualifying_backtests(self, server_name: str, min_winrate: float = 55.0, 
                                      max_drawdown: float = 0.0, min_trades: int = 5) -> List[Dict[str, Any]]:
        """Get qualifying backtests from server data"""
        try:
            if server_name not in self.servers_data:
                return []
            
            server_data = self.servers_data[server_name]
            qualifying_backtests = []
            
            for lab_id, backtests in server_data.backtests.items():
                for backtest in backtests:
                    try:
                        winrate = backtest.get('WinRate', 0) or 0
                        max_dd = backtest.get('MaxDrawdown', 0) or 0
                        trades = backtest.get('TotalTrades', 0) or 0
                        roe = backtest.get('ROI', 0) or 0
                        
                        if (winrate >= min_winrate and 
                            max_dd <= max_drawdown and 
                            trades >= min_trades):
                            
                            qualifying_backtests.append({
                                'lab_id': lab_id,
                                'backtest_id': backtest.get('backtest_id'),
                                'roe': roe,
                                'winrate': winrate,
                                'max_drawdown': max_dd,
                                'trades': trades,
                                'server': server_name
                            })
                            
                    except Exception as e:
                        self.logger.warning(f"Error analyzing backtest: {e}")
                        continue
            
            # Sort by ROE descending
            qualifying_backtests.sort(key=lambda x: x['roe'], reverse=True)
            
            self.logger.info(f"Found {len(qualifying_backtests)} qualifying backtests on {server_name}")
            return qualifying_backtests
            
        except Exception as e:
            self.logger.error(f"Failed to get qualifying backtests: {e}")
            return []
    
    async def create_bots_from_qualifying_backtests(self, server_name: str, 
                                                   qualifying_backtests: List[Dict[str, Any]], 
                                                   max_bots: int = 10) -> List[Dict[str, Any]]:
        """Create bots from qualifying backtests"""
        try:
            if server_name not in self.active_connections:
                self.logger.error(f"No active connection to {server_name}")
                return []
            
            client = self.active_connections[server_name]
            created_bots = []
            
            from ..api.bot import BotAPI
            bot_api = BotAPI(client)
            
            for backtest_data in qualifying_backtests[:max_bots]:
                try:
                    # Create bot name
                    bot_name = f"{backtest_data['roe']:.1f}% ROE {backtest_data['winrate']:.1f}% WR"
                    
                    # Create bot from lab backtest
                    bot = await bot_api.create_bot_from_lab(
                        backtest_data['lab_id'],
                        backtest_data['backtest_id'],
                        bot_name
                    )
                    
                    created_bots.append({
                        'bot_id': bot.bot_id,
                        'bot_name': bot.bot_name,
                        'lab_id': backtest_data['lab_id'],
                        'backtest_id': backtest_data['backtest_id'],
                        'server': server_name
                    })
                    
                    self.logger.info(f"Created bot: {bot.bot_name}")
                    
                    # Rate limiting
                    await self._rate_limit()
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create bot from backtest {backtest_data['backtest_id']}: {e}")
                    continue
            
            return created_bots
            
        except Exception as e:
            self.logger.error(f"Failed to create bots: {e}")
            return []
    
    async def _background_refresh(self):
        """Background task to refresh data"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.refresh_interval_minutes * 60)
                
                for server_name in self.active_connections:
                    if self.servers_data[server_name].connection_status == "connected":
                        await self.fetch_all_server_data(server_name)
                        
            except Exception as e:
                self.logger.error(f"Error in background refresh: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def get_server_summary(self) -> Dict[str, Any]:
        """Get summary of all servers and their data"""
        summary = {}
        
        for server_name, server_data in self.servers_data.items():
            summary[server_name] = {
                'status': server_data.connection_status,
                'labs_count': len(server_data.labs),
                'bots_count': len(server_data.bots),
                'accounts_count': len(server_data.accounts),
                'backtests_count': sum(len(backtests) for backtests in server_data.backtests.values()),
                'last_updated': server_data.last_updated.isoformat() if server_data.last_updated else None
            }
        
        return summary
    
    async def shutdown(self):
        """Shutdown the data manager"""
        self.logger.info("Shutting down Data Manager...")
        
        # Stop background tasks
        if self.refresh_task:
            self.refresh_task.cancel()
        
        # Close connections
        for client in self.active_connections.values():
            await client.close()
        
        # Shutdown server manager
        await self.server_manager.shutdown()
        
        self.logger.info("Data Manager shutdown complete")
