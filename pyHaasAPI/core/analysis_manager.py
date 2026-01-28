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
    """Orchestrates background backtest downloads and performance analysis."""
    
    def __init__(self, cache_dir: str = "unified_cache/runtime_reports"):
        self.cache_dir = Path(cache_dir)
        self.logger = get_logger("analysis_manager")
        self.extractor = BacktestDataExtractor()
        self.active_downloads: Dict[str, asyncio.Task] = {} # lab_id -> task
        self.cached_metrics: Dict[str, List[RunMetrics]] = {} # lab_id -> metrics list
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_report_path(self, server_name: str, lab_id: str, backtest_id: str) -> Path:
        """Get the local path for a backtest report JSON."""
        return self.cache_dir / server_name / lab_id / f"{backtest_id}_runtime.json"

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

    async def start_background_download(self, server_name: str, lab_id: str, backtest_ids: List[str], client: AsyncHaasClient, auth_manager: Any):
        """Start a background task to download missing backtests."""
        if lab_id in self.active_downloads and not self.active_downloads[lab_id].done():
            self.logger.info(f"Download already active for lab {lab_id}")
            return
        
        task = asyncio.create_task(self._download_worker(server_name, lab_id, backtest_ids, client, auth_manager))
        self.active_downloads[lab_id] = task
        return task

    async def _download_worker(self, server_name: str, lab_id: str, backtest_ids: List[str], client: AsyncHaasClient, auth_manager: Any):
        """Worker task for downloading backtests."""
        try:
            backtest_api = BacktestAPI(client, auth_manager)
            missing_ids = [bt_id for bt_id in backtest_ids if not self.is_cached(server_name, lab_id, bt_id)]
            
            if not missing_ids:
                return

            dest_dir = self.cache_dir / server_name / lab_id
            dest_dir.mkdir(parents=True, exist_ok=True)

            for i, bt_id in enumerate(missing_ids, 1):
                try:
                    # Fetch raw runtime data
                    runtime_data = await backtest_api.get_backtest_runtime(lab_id, bt_id)
                    
                    dest_file = dest_dir / f"{bt_id}_runtime.json"
                    with open(dest_file, "w") as f:
                        json.dump(runtime_data, f, indent=2)
                    
                    self.logger.debug(f"Downloaded {bt_id} for lab {lab_id} ({i}/{len(missing_ids)})")
                except Exception as e:
                    self.logger.error(f"Error downloading backtest {bt_id}: {e}")
                
                # Yield control
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Background download failed for lab {lab_id}: {e}")
