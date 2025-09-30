"""
Parameter optimization utilities for pyHaasAPI
"""

import logging
from typing import Dict, List, Any
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.parameters import ScriptParameter
from config.settings import (
    DISABLED_PARAMETERS, DISABLED_KEYWORDS, PARAM_TYPES,
    DEFAULT_PARAM_RANGE_START, DEFAULT_PARAM_RANGE_END, 
    DEFAULT_PARAM_STEP, MAX_PARAM_VALUES
)

logger = logging.getLogger(__name__)

class ParameterOptimizer:
    """Centralized parameter optimization handler"""
    
    def __init__(self):
        pass
    
    def analyze_parameter_for_optimization(self, param: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a parameter and determine if/how to optimize it"""
        key = param.get('K', '')
        param_type = param.get('T', 0)
        current_value = param.get('O', [None])[0] if param.get('O') else None
        decimals = param.get('D', 0)  # Number of decimal places
        
        # Check if parameter should be disabled
        should_disable = self._should_disable_parameter(key)
        
        if should_disable:
            return {
                "key": key,
                "optimize": False,
                "action": "disable",
                "reason": "Stop/gain/deviation/consensus parameter"
            }
        
        # Check if parameter is numeric and optimizable
        if param_type in [0, 1]:  # INTEGER or DECIMAL
            try:
                if current_value is not None:
                    float(current_value)
                    
                    # Determine optimization range based on parameter characteristics
                    optimization = self._determine_optimization_range(key, current_value, decimals, param_type)
                    
                    return {
                        "key": key,
                        "optimize": True,
                        "action": "optimize",
                        "current_value": current_value,
                        "param_type": param_type,
                        "decimals": decimals,
                        "optimization_range": optimization,
                        "reason": f"Numeric parameter (type {param_type}, decimals {decimals})"
                    }
            except (ValueError, TypeError):
                pass
        
        return {
            "key": key,
            "optimize": False,
            "action": "keep_default",
            "reason": f"Non-numeric or non-optimizable parameter (type {param_type})"
        }
    
    def _should_disable_parameter(self, key: str) -> bool:
        """Check if parameter should be disabled"""
        key_lower = key.lower()
        
        for disable_key in DISABLED_PARAMETERS:
            if disable_key.lower() in key_lower:
                return True
        
        for keyword in DISABLED_KEYWORDS:
            if keyword.lower() in key_lower:
                return True
        
        return False
    
    def _determine_optimization_range(self, key: str, current_value: Any, decimals: int, param_type: int) -> List[float]:
        """Determine intelligent optimization range for a parameter"""
        try:
            current = float(current_value)
        except (ValueError, TypeError):
            return [current_value]
        
        # Base step size based on decimals
        if decimals == 0:
            base_step = 1.0
        elif decimals == 1:
            base_step = 0.1
        elif decimals == 2:
            base_step = 0.01
        elif decimals == 3:
            base_step = 0.001
        else:
            base_step = 0.1
        
        # Parameter-specific ranges
        if 'rate' in key.lower() or 'ratio' in key.lower():
            # For rates/ratios, test around current value
            if current > 0:
                min_val = max(0.1, current * 0.5)
                max_val = current * 2.0
                step = base_step
            else:
                min_val = DEFAULT_PARAM_RANGE_START
                max_val = DEFAULT_PARAM_RANGE_END
                step = DEFAULT_PARAM_STEP
                
        elif 'period' in key.lower() or 'time' in key.lower():
            # For time periods, test reasonable ranges
            min_val = max(1, current * 0.5)
            max_val = current * 3.0
            step = max(1, base_step)
            
        elif 'threshold' in key.lower() or 'limit' in key.lower():
            # For thresholds, test around current value
            min_val = max(0, current * 0.3)
            max_val = current * 2.0
            step = base_step
            
        elif 'multiplier' in key.lower() or 'factor' in key.lower():
            # For multipliers, test reasonable ranges
            min_val = max(0.1, current * 0.5)
            max_val = current * 3.0
            step = base_step
            
        else:
            # Default: test around current value
            min_val = max(0, current * 0.5)
            max_val = current * 2.0
            step = base_step
        
        # Generate range values
        values = []
        val = min_val
        while val <= max_val:
            if param_type == 0:  # INTEGER
                values.append(int(round(val)))
            else:  # DECIMAL
                values.append(round(val, decimals))
            val += step
        
        # Limit to reasonable number of values
        if len(values) > MAX_PARAM_VALUES:
            step_size = len(values) // MAX_PARAM_VALUES
            values = values[::step_size]
        
        logger.info(f"    📊 {key}: {current} → {values} ({len(values)} values)")
        return values
    
    def analyze_lab_parameters(self, lab_details) -> Dict[str, Any]:
        """Analyze lab parameters and identify optimizable ones"""
        logger.info("🔧 Analyzing lab parameters...")
        
        parameter_analysis = {
            "all_params": [],
            "optimizable_params": [],
            "parameter_details": {},
            "numeric_params": []
        }
        
        for param in lab_details.parameters:
            key = param.get('K', '')
            param_type = param.get('T', 0)
            current_options = param.get('O', [])
            is_enabled = param.get('I', True)
            is_selected = param.get('IS', True)
            
            param_info = {
                "key": key,
                "type": param_type,
                "type_name": PARAM_TYPES.get(param_type, f"UNKNOWN({param_type})"),
                "current_options": current_options,
                "is_enabled": is_enabled,
                "is_selected": is_selected,
                "bruteforce": param.get('bruteforce', False),
                "intelligent": param.get('intelligent', False)
            }
            
            parameter_analysis["all_params"].append(key)
            parameter_analysis["parameter_details"][key] = param_info
            
            # Check if parameter is numeric and could be optimized
            if param_type in [0, 1]:  # INTEGER or DECIMAL
                try:
                    if current_options and len(current_options) > 0:
                        float(current_options[0])
                        parameter_analysis["numeric_params"].append(key)
                        logger.info(f"  🔢 {key}: Numeric parameter (Type {param_type})")
                except (ValueError, TypeError):
                    pass
            
            # Check if parameter is optimizable
            is_optimizable = (
                param.get('bruteforce', False) or 
                param.get('intelligent', False) or
                len(current_options) > 1
            )
            
            if is_optimizable:
                parameter_analysis["optimizable_params"].append(key)
                logger.info(f"  ✅ {key}: Already optimizable")
            else:
                logger.info(f"  📝 {key}: Type {param_type} ({PARAM_TYPES.get(param_type, 'UNKNOWN')}), Value: {current_options[0] if current_options else 'None'}")
        
        logger.info(f"✅ Found {len(parameter_analysis['all_params'])} total parameters")
        logger.info(f"✅ Found {len(parameter_analysis['optimizable_params'])} already optimizable parameters")
        logger.info(f"✅ Found {len(parameter_analysis['numeric_params'])} numeric parameters for potential optimization")
        return parameter_analysis
    
    def setup_lab_optimization(self, executor, lab_id: str, optimization_plan: List[Dict[str, Any]]) -> bool:
        """Setup lab parameters with optimization plan"""
        logger.info("🔧 Setting up lab optimization...")
        
        try:
            # Get current lab details
            lab_details = api.get_lab_details(executor, lab_id)
            
            # Convert parameters to ScriptParameter objects
            script_parameters = []
            for param in lab_details.parameters:
                key = param.get('K', '')
                
                # Find corresponding optimization plan
                plan_item = next((item for item in optimization_plan if item['key'] == key), None)
                
                if plan_item:
                    if plan_item["action"] == "disable":
                        # Set to zero or disable
                        script_param = ScriptParameter(
                            K=key,
                            T=param.get('T', 0),
                            O=[0] if param.get('T') in [0, 1] else [False],
                            I=False,  # Disable
                            IS=False  # Not selected
                        )
                        logger.info(f"  ❌ {key}: Disabled ({plan_item['reason']})")
                        
                    elif plan_item["action"] == "optimize":
                        # Enable intelligent optimization
                        script_param = ScriptParameter(
                            K=key,
                            T=param.get('T', 0),
                            O=plan_item["optimization_range"],
                            I=True,  # Enable
                            IS=True  # Selected
                        )
                        logger.info(f"  ✅ {key}: Intelligent optimization with {len(plan_item['optimization_range'])} values")
                        
                    else:
                        # Keep default
                        script_param = ScriptParameter(
                            K=key,
                            T=param.get('T', 0),
                            O=param.get('O', []),
                            I=True,
                            IS=True
                        )
                        logger.info(f"  📝 {key}: Keep default ({plan_item['reason']})")
                else:
                    # Keep parameter as is
                    script_param = ScriptParameter(
                        K=key,
                        T=param.get('T', 0),
                        O=param.get('O', []),
                        I=param.get('I', True),
                        IS=param.get('IS', True)
                    )
                
                script_parameters.append(script_param)
            
            # Convert ScriptParameter objects back to dictionaries for LabDetails
            # LabDetails expects List[Dict[str, Any]] for parameters
            parameter_dicts = []
            for script_param in script_parameters:
                param_dict = {
                    'K': script_param.key,
                    'T': script_param.param_type,
                    'O': script_param.options,
                    'I': script_param.is_included,
                    'IS': script_param.is_selected
                }
                parameter_dicts.append(param_dict)
            
            # Update the lab using update_lab_details
            lab_details.parameters = parameter_dicts
            api.update_lab_details(executor, lab_details)
            logger.info("✅ Lab parameters updated with optimization plan")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup lab optimization: {e}")
            return False
    
    def generate_parameter_ranges(self, start: float = None, end: float = None, step: float = None) -> List[float]:
        """Generate parameter range values"""
        if start is None:
            start = DEFAULT_PARAM_RANGE_START
        if end is None:
            end = DEFAULT_PARAM_RANGE_END
        if step is None:
            step = DEFAULT_PARAM_STEP
            
        values = []
        current = start
        while current <= end:
            values.append(round(current, 1))
            current += step
        return values 