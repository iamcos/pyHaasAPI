import json
import os
import asyncio
from typing import List, Dict, Any, Optional
from ..api.lab.lab_api import LabAPI
from ..api.script.script_api import ScriptAPI
from ..models.lab import LabDetails, LabParameter
from ..models.script import ScriptItem

class Stage2Service:
    """
    Service for 'Stage 2' actionability: Finetuning, cloning, and script analysis.
    """
    
    def __init__(self, lab_api: LabAPI, script_api: ScriptAPI):
        self.lab_api = lab_api
        self.script_api = script_api

    async def get_lab_finetune_data(self, lab_id: str, winning_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates diffs and prepares a finetune configuration.
        """
        lab = await self.lab_api.get_lab_details(lab_id)
        script = await self.script_api.get_script_item(lab.script_id)
        
        # 1. Map Script Defaults
        script_defaults = {}
        for p in getattr(script, 'parameters', []):
            script_defaults[getattr(p, 'name', '')] = getattr(p, 'default_value', None)

        # 2. Identify 'Iterated' parameters in the lab
        iterated_params = {}
        fixed_params = {}
        
        for p in getattr(lab, 'parameters', []):
            if hasattr(p, 'options') and p.options and len(p.options) > 1:
                iterated_params[p.key] = p.options
            else:
                fixed_params[p.key] = p.value
                
        # 3. Identify Diffs from Script Defaults
        diffs = {}
        for k, v in winning_params.items():
            default = script_defaults.get(k)
            if default is not None and str(v) != str(default):
                diffs[k] = {"current": v, "default": default}
                
        finetune_config = {
            "lab_id": lab_id,
            "script_id": lab.script_id,
            "script_name": getattr(script, 'name', 'Unknown'),
            "original_name": getattr(lab, 'name', 'Unknown'),
            "winning_params": winning_params,
            "iterated_params": iterated_params,
            "fixed_params": fixed_params,
            "diffs_from_default": diffs
        }
        
        return finetune_config

    async def clone_for_finetune(self, lab_id: str, bot_name: str, winning_params: Dict[str, Any]) -> str:
        """
        Clones a lab and sets the winning parameters as the new fixed base.
        """
        # 1. Clone the lab
        new_lab = await self.lab_api.clone_lab(lab_id, new_name=f"Finetune: {bot_name}")
        
        # 2. Update the new lab details with winning params
        if hasattr(new_lab, 'parameters'):
            for p in new_lab.parameters:
                if p.key in winning_params:
                    p.value = winning_params[p.key]
                    p.options = [winning_params[p.key]] # Reset to fixed winning value
            
            await self.lab_api.update_lab_details(new_lab)
        return getattr(new_lab, 'lab_id', '')

    async def analyze_script_for_errors(self, script_id: str) -> Dict[str, Any]:
        """
        Placeholder for script debugging logic.
        """
        script = await self.script_api.get_script_item(script_id)
        # In a real implementation, this would trigger a compile or backtest
        # and parse error logs.
        return {
            "script_id": script_id,
            "status": "ANALYZING",
            "findings": []
        }
