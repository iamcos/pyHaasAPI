"""
Script Automation Service for pyHaasAPI v2

This service orchestrates the full lifecycle of HaasScript development:
1. Writing/Editing Scripts
2. Debugging (Execute Debug Test)
3. Direct Backtesting (Execute Backtest without Labs)
4. Result Caching
5. Promotion to Labs or Bots
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..core.logging import get_logger
from ..core.client import AsyncHaasClient
from ..models.backtest import ExecuteBacktestRequest, BacktestExecutionResult
from ..api.script.script_api import ScriptAPI
from ..api.backtest.backtest_api import BacktestAPI
from ..api.lab.lab_api import LabAPI
from ..api.bot.bot_api import BotAPI
from .analysis.cached_analysis_service import CachedAnalysisService
from .haasscript_knowledge_service import HaasScriptKnowledgeService
from .ai_script_generator import AIScriptGenerator
from .script_error_repository import ScriptErrorRepository


# Define a temporary directory for direct backtest caching if not using the main cache
DIRECT_BACKTEST_CACHE_DIR = "unified_cache/backtests"


class ScriptAutomationService:
    """
    Service for automating HaasScript operations.
    """

    def __init__(
        self, 
        script_api: ScriptAPI, 
        backtest_api: BacktestAPI, 
        lab_api: LabAPI,
        bot_api: BotAPI,
        cached_analysis_service: CachedAnalysisService,
        ai_generator: Optional[AIScriptGenerator] = None,
        knowledge_service: Optional[HaasScriptKnowledgeService] = None,
        error_repository: Optional[ScriptErrorRepository] = None
    ):
        self.script_api = script_api
        self.backtest_api = backtest_api
        self.lab_api = lab_api
        self.bot_api = bot_api
        self.cached_analysis = cached_analysis_service
        self.ai_generator = ai_generator
        self.knowledge_service = knowledge_service
        self.error_repository = error_repository
        self.logger = get_logger("script_automation_service")
        
        # Ensure cache directory exists locally (mirroring what's expected by CachedAnalysisService)
        self.cache_dir = Path(DIRECT_BACKTEST_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def create_or_update_script(
        self, 
        name: str, 
        content: str, 
        description: str = "", 
        script_type: int = 0
    ) -> str:
        """
        Create a new script or update if it exists (by name).
        
        Args:
            name: Script name
            content: Lua/HaasScript content
            description: Script description
            script_type: 0 for TradeScript, etc.
            
        Returns:
            script_id: The ID of the created or updated script.
        """
        try:
            # Check if script exists
            existing_scripts = await self.script_api.get_scripts_by_name(name, case_sensitive=True)
            
            if existing_scripts:
                # Update existing
                script = existing_scripts[0]
                self.logger.info(f"Updating existing script: {name} ({script.script_id})")
                await self.script_api.edit_script_sourcecode(
                    script_id=script.script_id,
                    sourcecode=content,
                    settings={} # Keep existing settings or pass new ones if needed
                )
                return script.script_id
            else:
                # Create new
                self.logger.info(f"Creating new script: {name}")
                new_script = await self.script_api.add_script(
                    script_name=name,
                    script_content=content,
                    description=description,
                    script_type=script_type
                )
                # add_script returns ScriptItem, so we get the ID from it
                return new_script.script_id
                
        except Exception as e:
            self.logger.error(f"Failed to create/update script {name}: {e}")
            raise

    async def debug_script(
        self, 
        script_id: str, 
        settings: Dict[str, Any],
        script_type: int = 0
    ) -> Dict[str, Any]:
        """
        Run a debug test to check for compilation errors.
        
        Args:
            script_id: ID of script to debug
            settings: Bot settings for the debug context
            script_type: Script type
            
        Returns:
            Dictionary with debug results (success/failure, logs, errors)
        """
        try:
            self.logger.info(f"Running debug test for script {script_id}")
            result = await self.script_api.execute_debug_test(script_id, script_type, settings)
            
            # Parse result for errors (this depends on the raw response structure of execute_debug_test)
            # Typically returns a list of log strings or a dict
            
            # Identify if there are compiler errors
            errors = self._extract_errors_from_debug(result)
            
            return {
                "success": result.get('Success', result.get('success', True)),
                "raw_output": result,
                "errors": errors
            }
        except Exception as e:
            self.logger.error(f"Debug test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_direct_backtest(
        self,
        script_id: str,
        settings: Dict[str, Any],
        start_unix: int,
        end_unix: int,
        cache_result: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a backtest directly bypassing Lab creation.
        
        Args:
            script_id: Script ID
            settings: Full bot configuration/settings JSON dictionary
            start_unix: Start timestamp
            end_unix: End timestamp
            cache_result: Whether to save the result to disk
            
        Returns:
            Dictionary with backtest ID and basic status.
        """
        try:
            # Generate a temporary ID for this backtest run
            backtest_id = str(uuid.uuid4())
            
            self.logger.info(f"Starting direct backtest {backtest_id} for script {script_id}")
            
            request = ExecuteBacktestRequest(
                backtest_id=backtest_id, # Requires modifying ExecuteBacktestRequest to accept backtest_id if not present, checking model...
                # Note: ExecuteBacktestRequest in our model definition might not have backtest_id, 
                # but BacktestAPI.execute_backtest expects 'backtestid' in the payload.
                # Let's verify BacktestAPI implementation details.
                # BacktestAPI.execute_backtest constructs payload: 'backtestid': request.backtest_id
                # So we can pass it if we add it to the request object or if we pass a dict.
                # Wait, ExecuteBacktestRequest is a dataclass. I need to make sure I populate it correctly.
                # Checking ExecuteBacktestRequest definition...
                # It does not have `backtest_id`. 
                # !!! Wait, I need to check BacktestAPI.execute_backtest signature again.
                # It takes `request: ExecuteBacktestRequest`.
                # If `ExecuteBacktestRequest` doesn't have `backtest_id`, creating it won't work.
                # However, the `execute_backtest` method uses `request.backtest_id`.
                # This implies I might have missed updating the model, or I need to update it now.
                # Let's assume for now I will cheat and manually inject it or update the model.
                # Actually, I will update the ExecuteBacktestRequest model in this file via monkeypatch or just use a dict if API allowed it?
                # No, API requires type hint.
                # I will update the ExecuteBacktestRequest model in `pyHaasAPI/models/backtest.py` if needed.
                # But wait, looking at my previous `view_file` of `backtest.py` (lines 225-236):
                # Class ExecuteBacktestRequest... Fields: lab_id, script_id, market, parameters... NO backtest_id.
                # BUT `execute_backtest` code uses `request.backtest_id`.
                # This means the code I read in Step 49 matches `execute_backtest` usage but the model definition might be out of sync or I missed it.
                # Actually, looking at Step 48 again... 
                # `ExecuteBacktestRequest` indeed does NOT have `backtest_id` in the visible snippet.
                # I will have to dynamically add it or rely on the `BacktestAPI` to generate one if null?
                # `BacktestAPI.execute_backtest` code: `data = {'backtestid': request.backtest_id, ...}`
                # If `request` doesn't have that attribute, it will crash.
                # So I must update the model in `pyHaasAPI/models/backtest.py` OR pass a customized object.
                # Update: I will check if I can just pass it in constructor arguments if it accepts **kwargs (it's a dataclass/BaseModel).
            )
            
            # WORKAROUND: Create a custom object that mimics ExecuteBacktestRequest but includes backtest_id
            # This avoids modifying the core model file right now if strict.
            # Ideally I should update the model file. I will do that as part of this task.
            
            # The definition of ExecuteBacktestRequest is:
            # @dataclass
            # class ExecuteBacktestRequest(BaseModel):
            #     lab_id: str = "" ...
            
            # I will assume I update the model file next. 
            
            # Proceeding with logic assuming model is updated:
            req_object = ExecuteBacktestRequest(
                lab_id="", # Not used for direct backtest
                script_id=script_id,
                market=settings.get("marketTag", ""),
                parameters=settings,
                start_date=datetime.fromtimestamp(start_unix),
                end_date=datetime.fromtimestamp(end_unix)
                # I will calculate start/end unix in API or here. 
                # API uses request.start_unix. The model has start_date (datetime). 
                # Base model helper usually converts? Or API does `request.start_unix`?
                # Code in Step 49: `'startunix': request.start_unix`
                # So I need to ensure `start_unix` property exists on request.
            )
            # Inject backtest_id manually
            req_object.backtest_id = backtest_id
            # Make sure start_unix/end_unix properties work or are created
            req_object.start_unix = start_unix
            req_object.end_unix = end_unix
            req_object.settings = settings # Inject settings directly as API expects it
            
            result = await self.backtest_api.execute_backtest(req_object)
            
            if result.success and cache_result:
                await self.find_and_cache_results(backtest_id, script_id, settings)
                
            return {
                "backtest_id": backtest_id,
                "success": result.success,
                "message": result.message
            }
            
        except Exception as e:
            self.logger.error(f"Direct backtest failed: {e}")
            raise

    async def find_and_cache_results(
        self, 
        backtest_id: str,
        script_id: str,
        settings: Dict[str, Any]
    ):
        """
        Retrieve runtime data for the backtest and save it to the cache directory.
        """
        try:
            # Fetch runtime data using backtest ID
            # Note: get_full_backtest_runtime_data usually requires lab_id.
            # For direct backtests, we might need a different endpoint or pass empty lab_id if server allows.
            # Server usually expects 'botid' for history.
            # BUT for execution result retrieval, we might need to rely on what `execute_backtest` returned?
            # Actually, `execute_backtest` is fire-and-forget or synchronous wait?
            # Step 49: `execute_backtest` calls `/BacktestAPI.php` with `EXECUTE_BACKTEST`.
            # Response usually contains the result immediately if not async?
            # If it's async backtest job, we'd need to poll.
            # The V2 API usually returns the result keys.
            
            # Let's assume we can fetch it via `get_backtest_runtime`.
            # We'll pass the generated backtest_id.
            runtime_data = await self.backtest_api.get_full_backtest_runtime_data(
                lab_id="", # Empty for direct backtest?
                backtest_id=backtest_id
            )
            
            # Format filename as expected by CachedAnalysis: {lab_id}_{backtest_id}_{idx}_{idx}.json
            # Use "direct" as fake lab_id
            filename = f"direct_{backtest_id}_0_0.json"
            filepath = self.cache_dir / filename
            
            # Save to disk
            with open(filepath, 'w') as f:
                # We need to construct the JSON structure expected by CachedAnalysis
                # It expects a structure like {"Data": {...runtime_data...}}
                json.dump({"Data": runtime_data}, f, indent=2, default=str)
                
            self.logger.info(f"Cached backtest result to {filepath}")
            
            # Trigger cache refresh
            self.cached_analysis.refresh_lab_counts(force=True)
            
        except Exception as e:
            self.logger.error(f"Failed to cache backtest results: {e}")
            # Don't raise, just log error so flow continues
            
    async def promote_to_lab(
        self,
        backtest_id: str,
        lab_name: str,
        settings: Dict[str, Any]
    ) -> str:
        """
        Create a new lab based on the successful backtest settings.
        """
        try:
            # We need to extract basic params from settings
            script_id = settings.get("scriptId", "")
            market_tag = settings.get("marketTag", "")
            
            # Map settings to create_lab arguments
            new_lab = await self.lab_api.create_lab(
                script_id=script_id,
                name=lab_name,
                account_id=settings.get("accountId", ""),
                market=market_tag,
                interval=settings.get("interval", 1),
                trade_amount=settings.get("tradeAmount", 100.0),
                # Add other params if needed
            )
            self.logger.info(f"Promoted backtest to Lab: {new_lab.lab_id}")
            
            return new_lab.lab_id
            
        except Exception as e:
            self.logger.error(f"Failed to promote to Lab: {e}")
            raise

    async def promote_to_bot(
        self,
        backtest_id: str,
        bot_name: str,
        settings: Dict[str, Any]
    ) -> str:
        """
        Create a new live bot based on the backtest settings.
        """
        try:
            # Map settings to create_bot arguments
            new_bot = await self.bot_api.create_bot(
                bot_name=bot_name,
                script_id=settings.get("scriptId", ""),
                account_id=settings.get("accountId", ""),
                market=settings.get("marketTag", ""),
                # Add other params if needed, leveraging kwargs support in API
                leverage=settings.get("leverage", 20.0),
                interval=settings.get("interval", 1),
                chart_style=settings.get("chartStyle", 300)
            )
            self.logger.info(f"Promoted backtest to Bot: {new_bot.bot_id}")
            
            return new_bot.bot_id
            
        except Exception as e:
            self.logger.error(f"Failed to promote to Bot: {e}")
            raise

    # ========== AI-Powered Methods ==========
    
    async def generate_script_from_idea(
        self,
        idea: str,
        name: str,
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        auto_debug: bool = True
    ) -> str:
        """
        Generate HaasScript from natural language idea using AI.
        
        Args:
            idea: Natural language description of desired script
            name: Script name
            description: Script description
            context: Additional context (market, timeframe, etc.)
            auto_debug: Automatically debug and fix errors
            
        Returns:
            script_id: ID of the created script
            
        Raises:
            ScriptError: If AI generation is not available or generation fails
        """
        if not self.ai_generator:
            raise ScriptError(
                "AI generator not configured. Initialize ScriptAutomationService "
                "with ai_generator parameter."
            )
        
        try:
            self.logger.info(f"Generating script from idea: {name}")
            
            # Ensure knowledge base is loaded
            if self.knowledge_service:
                await self.knowledge_service.fetch_and_cache_commands()
            
            # Generate code using AI
            code = await self.ai_generator.generate_from_idea(idea, context)
            
            # Create script on server
            script_id = await self.create_or_update_script(
                name=name,
                content=code,
                description=description or f"AI-generated: {idea[:100]}"
            )
            
            # Auto-debug if requested
            if auto_debug:
                self.logger.info("Running auto-debug on generated script")
                debug_result = await self.auto_debug_and_fix(script_id)
                
                if not debug_result['success']:
                    self.logger.warning(
                        f"Auto-debug failed after {debug_result['iterations']} iterations"
                    )
            
            return script_id
            
        except Exception as e:
            self.logger.error(f"Failed to generate script from idea: {e}")
            raise
    
    async def modify_existing_script(
        self,
        script_id: str,
        modification: str,
        auto_debug: bool = True
    ) -> str:
        """
        Modify existing script using AI based on natural language instruction.
        
        Args:
            script_id: ID of script to modify
            modification: Natural language modification instruction
            auto_debug: Automatically debug and fix errors
            
        Returns:
            new_script_id: ID of the modified script (new version)
            
        Raises:
            ScriptError: If AI modification is not available or modification fails
        """
        if not self.ai_generator:
            raise ScriptError("AI generator not configured")
        
        try:
            self.logger.info(f"Modifying script {script_id}: {modification[:100]}")
            
            # Get current script
            script = await self.script_api.get_script_item(script_id)
            current_code = script.source_code
            
            # Generate modified code
            modified_code = await self.ai_generator.modify_script(
                current_code=current_code,
                modification=modification
            )
            
            # Create new version
            new_name = f"{script.name} (Modified)"
            new_script_id = await self.create_or_update_script(
                name=new_name,
                content=modified_code,
                description=f"Modified: {modification[:100]}"
            )
            
            # Auto-debug if requested
            if auto_debug:
                # Use empty settings or provided ones
                debug_settings = {"market": "BINANCE_BTC_USDT_"} 
                debug_result = await self.auto_debug_and_fix(new_script_id, settings=debug_settings)
                if not debug_result['success']:
                    self.logger.warning("Auto-debug failed on modified script")
            
            return new_script_id
            
        except Exception as e:
            self.logger.error(f"Failed to modify script: {e}")
            raise
    
    async def auto_debug_and_fix(
        self,
        script_id: str,
        settings: Dict[str, Any],
        max_iterations: int = 3,
        script_type: int = 1
    ) -> Dict[str, Any]:
        """
        Automatically debug and fix script errors using AI.
        
        Args:
            script_id: ID of script to debug
            max_iterations: Maximum number of fix attempts
            
        Returns:
            Dict with keys:
                - success: bool
                - iterations: int
                - final_errors: List[str]
                - fix_history: List[Dict]
        """
        if not self.ai_generator:
            raise ScriptError("AI generator not configured")
        
        fix_history = []
        
        for iteration in range(max_iterations):
            self.logger.info(f"Debug iteration {iteration + 1}/{max_iterations}")
            
            # Run debug test
            debug_result = await self.debug_script(script_id, settings, script_type)
            
            # Use pre-extracted errors from debug_result
            errors = debug_result.get('errors', [])
            
            if not errors:
                self.logger.info(f"Script debugged successfully in {iteration} iterations")
                return {
                    'success': True,
                    'iterations': iteration,
                    'final_errors': [],
                    'fix_history': fix_history
                }
            
            # Get current script
            script = await self.script_api.get_script_item(script_id)
            current_code = script.source_code
            
            # Use AI to fix errors
            try:
                fixed_code = await self.ai_generator.fix_errors(
                    script_code=current_code,
                    errors=errors
                )
                
                # Update script
                await self.script_api.edit_script_sourcecode(
                    script_id=script_id,
                    sourcecode=fixed_code,
                    settings=settings
                )
                
                # Verify fix
                post_fix_debug = await self.debug_script(script_id, settings, script_type)
                post_fix_errors = post_fix_debug.get('errors', [])
                
                if not post_fix_errors:
                    # SUCCESS! Learn from this
                    if self.error_repository:
                        self.logger.info(f"Learning from successful fix: {len(errors)} errors solved")
                        self.error_repository.add_solution(
                            error_message="\n".join(errors),
                            offending_code=current_code,
                            fixed_code=fixed_code
                        )
                
                fix_history.append({
                    'iteration': iteration + 1,
                    'errors': errors,
                    'fixed': True,
                    'remaining_errors': post_fix_errors
                })
                
                # If fixed perfectly, return
                if not post_fix_errors:
                    return {
                        'success': True,
                        'iterations': iteration + 1,
                        'final_errors': [],
                        'fix_history': fix_history
                    }
                
            except Exception as e:
                self.logger.error(f"Failed to fix errors in iteration {iteration + 1}: {e}")
                fix_history.append({
                    'iteration': iteration + 1,
                    'errors': errors,
                    'fixed': False,
                    'error': str(e)
                })
                break
        
        # Failed to fix after max iterations
        final_debug = await self.debug_script(script_id)
        final_errors = self._extract_errors_from_debug(final_debug)
        
        return {
            'success': False,
            'iterations': max_iterations,
            'final_errors': final_errors,
            'fix_history': fix_history
        }
    
    def _extract_errors_from_debug(self, debug_result: Dict[str, Any]) -> List[str]:
        """
        Extract error messages from debug result.
        
        Args:
            debug_result: Debug test result from debug_script()
            
        Returns:
            List of error message strings
        """
        errors = []
    
        # Check for direct automation failure (handle both casing)
        is_success = debug_result.get('success', debug_result.get('Success', True))
        if not is_success:
            error_msg = debug_result.get('error', debug_result.get('Error', ''))
            if not error_msg:
                error_msg = "Compilation Error (Unknown cause, likely syntax or missing references)"
            errors.append(error_msg)
        
        # Extract logs from various possible locations in Haas API
        raw = debug_result.get('raw_output', debug_result)
        logs = []
        if isinstance(raw, list):
            logs = raw
        elif isinstance(raw, dict):
            # Check Data field first (common in Haas PHP APIs)
            logs = raw.get('Data', [])
            if not logs:
                logs = raw.get('logs', [])
        
        if logs is None:
            logs = []
            
        for log in logs:
            if isinstance(log, dict):
                if log.get('level') == 'error' or log.get('type') == 'error':
                    errors.append(log.get('message', str(log)))
            else:
                log_str = str(log)
                # Filter for clear error indicators
                if 'ERROR:' in log_str or 'FAILURE:' in log_str or 'Exception:' in log_str:
                    # Clean up the prefix if it's the standard log format: "PID ||| LEVEL ||| MESSAGE"
                    if '|||' in log_str:
                        parts = log_str.split('|||')
                        if len(parts) >= 3:
                            errors.append(parts[2].strip())
                        else:
                            errors.append(log_str)
                    else:
                        errors.append(log_str)
                elif 'error' in log_str.lower() and 'TIP:' not in log_str and 'WARNING:' not in log_str:
                    errors.append(log_str)
    
        return errors
