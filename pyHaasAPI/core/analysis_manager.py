import asyncio
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from ..models.project import LabProjectConfig
from ..analysis.extraction import BacktestDataExtractor, BacktestSummary
from ..analysis.metrics import compute_metrics, RunMetrics
from ..core.logging import get_logger
from ..api.backtest import BacktestAPI
from ..core.client import AsyncHaasClient
from ..config.api_config import APIConfig

class AnalysisManager:
    """
    Orchestrates background backtest downloads and performance analysis.
    
    SAFETY MANDATE: 
    1. NEVER delete or prune data from the backtesting cache.
    2. NEVER re-download backtests that are already stored locally (No Re-Syncs).
    Backtests are immutable records kept for permanent local retention.
    """
    
    def __init__(self, tui_app=None, cache_dir: str = "unified_cache/backtests"):
        self.tui_app = tui_app
        self.cache_dir = Path(cache_dir)
        self.logger = get_logger("analysis_manager")
        self.extractor = BacktestDataExtractor()
        self.active_downloads: Dict[str, asyncio.Task] = {} # lab_id -> task
        self.cached_metrics: Dict[str, List[RunMetrics]] = {} # lab_id -> metrics list
        self.sync_semaphore = asyncio.Semaphore(5) # Max 5 concurrent lab syncs
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def get_all_available_backtest_ids(self, lab_id: str, online_ids: List[str]) -> List[str]:
        """Combine online IDs with cached ones to ensure full analysis availability."""
        cached_ids = self.get_cached_backtest_ids(lab_id)
        
        # Merge and maintain uniqueness
        all_ids = list(set(online_ids + cached_ids))
        self.logger.info(f"Unified backtest IDs for lab {lab_id[:8]}: {len(online_ids)} online, {len(cached_ids)} cached. Total: {len(all_ids)}")
        return all_ids

    def get_cached_backtest_ids(self, lab_id: str) -> List[str]:
        """Get all backtest IDs currently in cache for this lab."""
        ids = []
        try:
            # Pattern: labID_backtestID.json
            for f in self.cache_dir.glob(f"{lab_id}_*.json"):
                parts = f.name.split('_')
                if len(parts) >= 2:
                    bt_id = parts[1].replace('.json', '')
                    ids.append(bt_id)
        except Exception as e:
            self.logger.error(f"Error scanning cache for lab {lab_id}: {e}")
        return ids

    def get_report_path(self, server_name: str, lab_id: str, backtest_id: str) -> Path:
        """Get the local path for a backtest report JSON."""
        return self.cache_dir / f"{lab_id}_{backtest_id}.json"

    def is_cached(self, server_name: str, lab_id: str, backtest_id: str) -> bool:
        """Check if a backtest report exists in cache."""
        return self.get_report_path(server_name, lab_id, backtest_id).exists()

    async def get_metrics(self, server_name: str, lab_id: str, backtest_id: str) -> Optional[RunMetrics]:
        """Load and compute metrics for a single backtest."""
        path = self.get_report_path(server_name, lab_id, backtest_id)
        if not path.exists():
            return None
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            # Use extractor to get summary
            summary = self.extractor.extract_backtest_summary(data)
            if not summary:
                return None
            
            # Ensure backtest_id and lab_id are set in summary if missing in data
            summary.backtest_id = backtest_id
            summary.lab_id = lab_id
            
            return compute_metrics(summary)
        except Exception as e:
            self.logger.error(f"Failed to analyze backtest {backtest_id}: {e}")
            return None

    async def analyze_lab(self, server_name: str, lab_id: str, backtest_ids: List[str]) -> List[RunMetrics]:
        """Analyze all cached backtests for a lab."""
        results = []
        for bt_id in backtest_ids:
            metrics = await self.get_metrics(server_name, lab_id, bt_id)
            if metrics:
                results.append(metrics)
        
        # Sort by net profit or ROE? Let's do ROE/Profit
        results.sort(key=lambda x: x.net_profit, reverse=True)
        return results

    async def start_background_download(self, server_name: str, lab_id: str, backtest_ids: List[str]):
        """Start a background task to download missing backtests."""
        return await self.sync_lab(server_name, lab_id, backtest_ids)

    async def sync_lab(self, server_name: str, lab_id: str, backtest_ids: List[str]):
        """Standardized lab synchronization into unified_cache/backtests"""
        if lab_id in self.active_downloads and not self.active_downloads[lab_id].done():
            self.logger.info(f"Sync already active for lab {lab_id}")
            return self.active_downloads[lab_id]
        
        task = asyncio.create_task(self._lab_sync_worker(server_name, lab_id, backtest_ids))
        self.active_downloads[lab_id] = task
        return task

    async def _lab_sync_worker(self, server_name: str, lab_id: str, backtest_ids: List[str]):
        """Worker for lab-level sync into unified_cache/backtests"""
        if not self.tui_app:
            self.logger.error("No TUI App reference to manage sessions.")
            return

        try:
            async with self.sync_semaphore:
                # Ensure session is open for this server
                async with self.tui_app.server_manager.server_session(server_name):
                    # Setup own client
                    config = APIConfig()
                    config.port = self.tui_app.server_manager.servers[server_name].config.local_ports[0]
                    
                    async with AsyncHaasClient(config) as client:
                        auth = self.tui_app.get_auth_manager(server_name, client)
                        await auth.ensure_authenticated()
                        
                        backtest_api = BacktestAPI(client, auth)
                        
                        # Identify missing backtests
                        missing_ids = []
                        for bt_id in backtest_ids:
                            path = self.cache_dir / f"{lab_id}_{bt_id}.json"
                            if not path.exists():
                                missing_ids.append(bt_id)
                        
                        if not missing_ids:
                            self.logger.info(f"Lab {lab_id} is already fully synchronized.")
                            return

                        self.logger.info(f"Starting sync for lab {lab_id}: {len(missing_ids)} missing backtests.")
                        
                        for i, bt_id in enumerate(missing_ids, 1):
                            try:
                                runtime_data = await backtest_api.get_backtest_runtime(lab_id, bt_id)
                                dest_file = self.cache_dir / f"{lab_id}_{bt_id}.json"
                                
                                with open(dest_file, "w") as f:
                                    json.dump(runtime_data, f, indent=2)
                                
                                if i % 10 == 0:
                                    self.logger.info(f"Sync progress {lab_id}: {i}/{len(missing_ids)}")
                            except Exception as e:
                                self.logger.error(f"Error syncing backtest {bt_id} for lab {lab_id}: {e}")
                            
                            await asyncio.sleep(0.05) 
                        
                        self.logger.info(f"Completed sync for lab {lab_id}.")
        except Exception as e:
            self.logger.error(f"Lab sync failed for {lab_id}: {e}")
