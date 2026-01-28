import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.project import ProjectConfig, LabProjectConfig
from ..models.lab import StartLabExecutionRequest
from ..core.analysis_manager import AnalysisManager
from ..core.logging import get_logger
from ..api.lab.lab_api import LabAPI
from ..api.backtest import BacktestAPI
from ..core.client import AsyncHaasClient

class ProjectOrchestrator:
    """Orchestrates sequential lab execution and parameter injection for projects."""
    
    def __init__(self, tui_app):
        self.tui_app = tui_app
        self.logger = get_logger("project_orchestrator")
        self.analysis_manager = tui_app.analysis_manager
        self.server_manager = tui_app.server_manager
        self.active_project: Optional[str] = None
        self.current_step_index: int = 0
        self.is_running: bool = False

    async def run_project(self, project: ProjectConfig):
        """Execute the project labs sequentially with parameter injection."""
        if self.is_running:
            self.logger.warning(f"Project already running: {self.active_project}")
            return
        
        self.is_running = True
        self.active_project = project.name
        self.current_step_index = 0
        
        try:
            self.tui_app.notify(f"🚀 Starting Project: {project.name}")
            
            for i, lab_config in enumerate(project.labs):
                self.current_step_index = i
                self.tui_app.notify(f"🔄 Step {i+1}/{len(project.labs)}: {lab_config.lab_name}")
                
                # 1. Run Lab and wait for completion
                await self._run_lab_step(lab_config)
                
                # 2. Analyze results and get best params
                best_params = await self._analyze_step_and_get_params(lab_config)
                
                # 3. Inject params into NEXT lab if available
                if i < len(project.labs) - 1:
                    next_lab = project.labs[i+1]
                    await self._inject_params_into_lab(next_lab, best_params)
            
            self.tui_app.notify(f"✅ Project {project.name} completed successfully!")
            
        except Exception as e:
            self.logger.exception(f"Project {project.name} failed at step {self.current_step_index}")
            self.tui_app.notify(f"❌ Project failed: {e}", severity="error")
        finally:
            self.is_running = False
            self.active_project = None

    async def _run_lab_step(self, lab_config: LabProjectConfig):
        """Start lab and poll for completion."""
        async with self.server_manager.server_session(lab_config.server_name):
            from pyHaasAPI.config.api_config import APIConfig
            config = APIConfig()
            config.port = self.server_manager.get_active_server_config().local_ports[0]
            
            async with AsyncHaasClient(config) as client:
                auth = self.tui_app.get_auth_manager(lab_config.server_name, client)
                await auth.ensure_authenticated()
                
                lab_api = LabAPI(client, auth)
                # Note: We assume the lab is already configured for iteration
                # We start execution using standard cutoff (e.g. 730 days)
                from datetime import timedelta
                cutoff = datetime.now() - timedelta(days=730)
                
                request = StartLabExecutionRequest(
                    lab_id=lab_config.lab_id,
                    start_unix=int(cutoff.timestamp()),
                    end_unix=int(datetime.now().timestamp())
                )
                
                execution = await lab_api.start_lab_execution(request)
                
                # Use safe_get_success_flag for robust validation
                from ..core.field_utils import safe_get_success_flag, safe_get_field
                if not safe_get_success_flag(execution):
                    error_msg = safe_get_field(execution, "Error", "Unknown error")
                    raise Exception(f"Failed to start lab execution: {error_msg}")
                
                self.logger.info(f"Started lab {lab_config.lab_name} ({lab_config.lab_id})")
                
                # Poll for completion
                while True:
                    status = await lab_api.get_lab_execution_status(lab_config.lab_id)
                    self.logger.debug(f"Lab {lab_config.lab_name} status: {status.status}, {status.progress_percentage}%")
                    
                    if status.is_completed:
                        break
                    elif status.is_failed:
                        raise Exception(f"Lab execution failed: {status.error_message}")
                    elif status.is_cancelled:
                        raise Exception("Lab execution was cancelled")
                    
                    await asyncio.sleep(20) # Poll every 20s

    async def _analyze_step_and_get_params(self, lab_config: LabProjectConfig) -> Dict[str, Any]:
        """Analyze lab results and extract best parameters."""
        # 1. Get backtest list
        async with self.server_manager.server_session(lab_config.server_name):
            from pyHaasAPI.config.api_config import APIConfig
            config = APIConfig()
            config.port = self.server_manager.get_active_server_config().local_ports[0]
            
            async with AsyncHaasClient(config) as client:
                auth = self.tui_app.get_auth_manager(lab_config.server_name, client)
                await auth.ensure_authenticated()
                
                backtest_api = BacktestAPI(client, auth)
                results = await backtest_api.get_backtest_results(lab_config.lab_id)
                bt_ids = [getattr(r, "backtest_id") for r in results]
                
                # 2. Sync to cache
                await self.analysis_manager.start_background_download(
                    lab_config.server_name, lab_config.lab_id, bt_ids, client, auth
                )
                
                # Wait for sync
                while True:
                    cached = sum(1 for bid in bt_ids if self.analysis_manager.is_cached(lab_config.server_name, lab_config.lab_id, bid))
                    if cached == len(bt_ids) and cached > 0:
                        break
                    await asyncio.sleep(5)
                
                # 3. Analyze and get best
                metrics_list = await self.analysis_manager.analyze_lab(lab_config.server_name, lab_config.lab_id, bt_ids)
                if not metrics_list:
                    raise Exception(f"No results found for lab {lab_config.lab_id}")
                
                best_bt = metrics_list[0]
                
                # 4. Extract parameters from raw JSON
                report_path = self.analysis_manager.get_report_path(lab_config.server_name, lab_config.lab_id, best_bt.backtest_id)
                with open(report_path, "r") as f:
                    data = json.load(f)
                
                # HaasAnalyzer/Extractor logic for params
                from ..analysis.extraction import BacktestDataExtractor
                extractor = BacktestDataExtractor()
                return extractor.extract_parameter_values(data)

    async def _inject_params_into_lab(self, lab_config: LabProjectConfig, params: Dict[str, Any]):
        """Inject parameters as fixed values into the target lab."""
        async with self.server_manager.server_session(lab_config.server_name):
            from pyHaasAPI.config.api_config import APIConfig
            config = APIConfig()
            config.port = self.server_manager.get_active_server_config().local_ports[0]
            
            async with AsyncHaasClient(config) as client:
                auth = self.tui_app.get_auth_manager(lab_config.server_name, client)
                await auth.ensure_authenticated()
                
                lab_api = LabAPI(client, auth)
                lab_details = await lab_api.get_lab_details(lab_config.lab_id)
                
                # Update parameters that match keys
                updated_count = 0
                for p in lab_details.parameters:
                    if p.key in params:
                        p.value = params[p.key]
                        p.is_selected = True # Set as fixed value
                        updated_count += 1
                
                if updated_count > 0:
                    await lab_api.update_lab_details(lab_config.lab_id, lab_details)
                    self.logger.info(f"Injected {updated_count} params into lab {lab_config.lab_name}")
                else:
                    self.logger.warning(f"No matching parameters found for lab {lab_config.lab_name}")
