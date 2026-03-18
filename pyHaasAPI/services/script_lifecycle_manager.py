
import asyncio
import re
import json
from typing import List, Dict, Any, Set, Optional
from pathlib import Path

from ..core.logging import get_logger
from ..api.script.script_api import ScriptAPI
from ..models.script import ScriptItem, ScriptRecord

class ScriptLifecycleManager:
    """
    Autonomous manager for the HaasScript life-cycle.
    Handles ingestion, dependency discovery, and automated compilation orchestration.
    """

    def __init__(self, script_api: ScriptAPI):
        self.script_api = script_api
        self.logger = get_logger("script_lifecycle_manager")
        self._command_map: Dict[str, str] = {} # CC_Name -> ScriptID
        self._processed_ids: Set[str] = set()

    async def initialize(self):
        """Build the initial command map from existing scripts on the server."""
        self.logger.info("Initializing ScriptLifecycleManager: Mapping existing commands...")
        scripts = await self.script_api.get_all_scripts()
        for s in scripts:
            # We use get_script_item to get source if necessary, 
            # but for initial mapping, names like [pshaiCmd] often tell us.
            # However, the "Correct Way" is to check the actual DefineCommand in source.
            pass
        
        # In a real scenario, we might want to lazy-load source code.
        # For now, let's assume we map as we go or on first run.
        self.logger.info(f"Command map initialized with {len(self._command_map)} entries.")

    async def manage_script(self, script_id: str, force_recompile: bool = False) -> bool:
        """
        Autonomous entry point to ensure a script and all its dependencies are compiled.
        """
        if script_id in self._processed_ids and not force_recompile:
            return True

        self.logger.info(f"Managing lifecycle for script: {script_id}")
        
        # 1. Fetch script details
        try:
            item = await self.script_api.get_script_item(script_id)
        except Exception as e:
            self.logger.error(f"Failed to fetch script {script_id}: {e}")
            return False

        # 2. Check for dependencies (CC_ references)
        deps = self._parse_dependencies(item.source_code)
        if deps:
            self.logger.info(f"Found dependencies for {item.name}: {deps}")
            for dep in deps:
                # Find the script that defines this command
                dep_script_id = await self._find_command_provider(dep)
                if dep_script_id:
                    # Recursive call to ensure dependency is compiled
                    success = await self.manage_script(dep_script_id)
                    if not success:
                        self.logger.error(f"Failed to resolve dependency {dep} for {item.name}")
                        return False
                else:
                    self.logger.warning(f"No provider found for dependency: {dep}")

        # 3. Compilation phase
        self.logger.info(f"Compiling {item.name}...")
        try:
            # Using same source to trigger compile
            res = await self.script_api.edit_script_sourcecode(script_id, item.source_code, {})
            
            # 4. Verification phase
            record = await self.script_api.get_script_record(script_id)
            if record.is_valid:
                self.logger.info(f"✅ SUCCESS: {item.name} is now compiled and ready.")
                self._processed_ids.add(script_id)
                return True
            else:
                logs = record.compilation_result.compile_logs if record.compilation_result else []
                self.logger.error(f"❌ FAILED: {item.name} compilation issues: {logs}")
                return False
                
        except Exception as e:
            self.logger.error(f"Autonomous compilation failed for {item.name}: {e}")
            return False

    def _parse_dependencies(self, source: str) -> List[str]:
        """Exerts the 'Correct Way' of parsing for CC_ references."""
        # Find matches for CC_ followed by word characters, avoiding definitions
        # We look for usage like CC_SuperTrend(..., or CC_StorchRSI
        pattern = r"\bCC_([A-Za-z0-9_]+)\b"
        matches = re.findall(pattern, source)
        
        # Also check if this script IS a definition to avoid self-dependency
        defined = self._parse_definitions(source)
        
        # Return unique usages that aren't defined here
        return list(set([f"CC_{m}" for m in matches if f"CC_{m}" not in defined]))

    def _parse_definitions(self, source: str) -> List[str]:
        """Finds CC_ commands defined in this script."""
        # DefineCommand('Name', ...)
        pattern = r"DefineCommand\s*\(\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, source)
        return [f"CC_{m}" for m in matches]

    async def _find_command_provider(self, command_name: str) -> Optional[str]:
        """Search the server scripts for a script defining the specific command."""
        # Check cache first
        if command_name in self._command_map:
            return self._command_map[command_name]

        self.logger.info(f"Searching for provider of {command_name}...")
        scripts = await self.script_api.get_all_scripts()
        
        # Heuristic: Scripts with [pshaiCmd] or similar in name are high priority
        # but the only true way is checking source.
        for s in scripts:
            # Optimization: only check scripts with 'Cmd' or 'CC_' in name first
            if any(x in s.name for x in ['Cmd', 'CC_', 'Command']):
                item = await self.script_api.get_script_item(s.script_id)
                defs = self._parse_definitions(item.source_code)
                if command_name in defs:
                    self.logger.info(f"Found provider for {command_name}: {s.name} ({s.script_id})")
                    self._command_map[command_name] = s.script_id
                    return s.script_id

        return None
