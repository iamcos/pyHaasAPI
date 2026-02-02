import asyncio
import time
import json
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from pyHaasAPI.core.logging import get_logger
from pyHaasAPI.core.analysis_manager import AnalysisManager
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.config.api_config import APIConfig

class LabSyncService:
    """
    Unified service for lab synchronization across all servers.
    Handles periodic background downloads of missing backtest data.
    """
    def __init__(self, tui_app):
        self.tui_app = tui_app
        self.analysis_manager = tui_app.analysis_manager
        self.server_manager = tui_app.server_manager
        self.logger = get_logger("lab_sync_service")
        self.running = False
        self._sync_loop_task: Optional[asyncio.Task] = None
        self.interval = 300 # 5 minutes default
        self.synced_labs: Set[str] = set()
        self.auto_sync_labs: Set[str] = set() # Format "server_name:lab_id"
        self.config_path = Path("unified_cache/autosync_config.json")
        self._load_config()

    def _load_config(self):
        """Load auto-sync configuration from disk."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.auto_sync_labs = set(data.get("auto_sync_labs", []))
            except Exception as e:
                self.logger.error(f"Failed to load autosync config: {e}")

    def _save_config(self):
        """Save auto-sync configuration to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump({"auto_sync_labs": list(self.auto_sync_labs)}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save autosync config: {e}")

    def is_auto_sync_enabled(self, server_name: str, lab_id: str) -> bool:
        """Check if auto-sync is enabled for a specific lab."""
        return f"{server_name}:{lab_id}" in self.auto_sync_labs

    def toggle_auto_sync(self, server_name: str, lab_id: str):
        """Toggle auto-sync for a specific lab."""
        key = f"{server_name}:{lab_id}"
        if key in self.auto_sync_labs:
            self.auto_sync_labs.remove(key)
        else:
            self.auto_sync_labs.add(key)
        self._save_config()

    async def start(self):
        """Start the background sync loop."""
        if self.running:
            return
        self.running = True
        self._sync_loop_task = asyncio.create_task(self._sync_loop())
        self.logger.info("Lab Sync Service started.")

    async def stop(self):
        """Stop the background sync loop."""
        self.running = False
        if self._sync_loop_task:
            self._sync_loop_task.cancel()
            try:
                await self._sync_loop_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Lab Sync Service stopped.")

    async def _sync_loop(self):
        """Infinite loop for periodic synchronization."""
        while self.running:
            try:
                if self.auto_sync_labs:
                    self.logger.info(f"Starting scheduled auto-sync for {len(self.auto_sync_labs)} labs...")
                    # Only sync registered labs during the periodic loop
                    await self.sync_all_servers(full_sweep=False)
                    self.logger.info("Scheduled auto-sync completed.")
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.interval)

    async def sync_all_servers(self, full_sweep: bool = False):
        """Iterates through all servers and syncs their labs."""
        for server_name in list(self.server_manager.servers.keys()):
             if self.server_manager.servers[server_name].config.enabled:
                 await self.sync_server(server_name, full_sweep=full_sweep)

    async def sync_server(self, server_name: str, full_sweep: bool = False):
        """Syncs labs on a specific server based on registry or full sweep."""
        self.logger.info(f"Syncing server: {server_name} (full_sweep={full_sweep})")
        try:
            # Refresh local counts first
            self.tui_app.cached_analysis.refresh_lab_counts()
            
            async with self.server_manager.server_session(server_name):
                # Setup client and config for this server session
                config = APIConfig()
                config.port = self.server_manager.servers[server_name].config.local_ports[0]
                
                async with AsyncHaasClient(config) as client:
                    auth = self.tui_app.get_auth_manager(server_name, client)
                    await auth.ensure_authenticated()
                    
                    lab_api = LabAPI(client, auth)
                    labs = await lab_api.get_labs()
                    
                    for lab in labs:
                        if not self.running: break
                        
                        key = f"{server_name}:{lab.lab_id}"
                        # Check if we should sync this lab
                        if full_sweep or (key in self.auto_sync_labs):
                            local_count = self.tui_app.cached_analysis.get_local_count(lab.lab_id)
                            # Only sync if there are new backtests
                            if local_count < lab.completed_backtests:
                                self.logger.info(f"Updates found for {lab.name} ({local_count}/{lab.completed_backtests})")
                                await self.sync_lab(server_name, lab.lab_id)
                                await asyncio.sleep(0.5) 
                        
        except Exception as e:
            self.logger.error(f"Critical failure syncing server {server_name}: {e}")

    async def sync_lab(self, server_name: str, lab_id: str):
        """Syncs a specific lab on a specific server."""
        self.logger.info(f"Syncing lab {lab_id[:8]} on {server_name}")
        try:
            async with self.server_manager.server_session(server_name):
                # We still need to fetch bt_ids here to pass them to manager
                config = APIConfig()
                config.port = self.server_manager.servers[server_name].config.local_ports[0]
                
                async with AsyncHaasClient(config) as client:
                    auth = self.tui_app.get_auth_manager(server_name, client)
                    await auth.ensure_authenticated()
                    
                    backtest_api = BacktestAPI(client, auth)
                    results = await backtest_api.get_all_backtests_for_lab(lab_id)
                    bt_ids = [getattr(r, "backtest_id") for r in results]
                    
                    if bt_ids:
                        # Manager now handles its own client/session for the actual download
                        await self.analysis_manager.sync_lab(server_name, lab_id, bt_ids)
                        self.synced_labs.add(lab_id)
        except Exception as e:
            self.logger.error(f"Failed to sync lab {lab_id}: {e}")
