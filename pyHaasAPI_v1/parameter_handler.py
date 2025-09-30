"""
Parameter Handler for HaasOnline Labs
Handles parameter optimization, validation, and management
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ParameterType(Enum):
    """Parameter types from HaasOnline API"""
    NUMBER = 0
    BOOLEAN = 2
    STRING = 3
    GROUP_HEADER = 10

@dataclass
class ParameterInfo:
    """Parameter information structure"""
    key: str
    name: str
    group: str
    param_type: ParameterType
    current_value: Any
    default_value: Any
    options: Optional[Dict[str, str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_optimizable: bool = False

class ParameterHandler:
    """Handles parameter optimization and management for HaasOnline labs"""
    
    def __init__(self):
        self.optimization_strategies = {
            'length': self._optimize_length_parameter,
            'fast': self._optimize_fast_parameter,
            'slow': self._optimize_slow_parameter,
            'signal': self._optimize_signal_parameter,
            'level': self._optimize_level_parameter,
            'deviation': self._optimize_deviation_parameter,
            'boolean': self._optimize_boolean_parameter,
            'string': self._optimize_string_parameter,
        }
    
    def analyze_script_parameters(self, script_data: Dict[str, Any]) -> List[ParameterInfo]:
        """Analyze script parameters and extract optimization information"""
        parameters = []
        
        for param in script_data.get('I', []):
            param_info = ParameterInfo(
                key=param.get('K', ''),
                name=param.get('N', ''),
                group=param.get('G', ''),
                param_type=ParameterType(param.get('T', 0)),
                current_value=param.get('V', ''),
                default_value=param.get('D', ''),
                options=param.get('O'),
                min_value=param.get('MIN'),
                max_value=param.get('MAX'),
                is_optimizable=self._is_parameter_optimizable(param)
            )
            parameters.append(param_info)
        
        return parameters
    
    def _is_parameter_optimizable(self, param: Dict[str, Any]) -> bool:
        """Determine if a parameter should be optimized"""
        param_type = param.get('T', 0)
        name = param.get('N', '').lower()
        
        # Skip group headers and non-numeric parameters
        if param_type == ParameterType.GROUP_HEADER.value:
            return False
        
        # Skip boolean parameters unless they're specific ones
        if param_type == ParameterType.BOOLEAN.value:
            return 'consensus' in name
        
        # Skip string parameters unless they have options
        if param_type == ParameterType.STRING.value:
            return param.get('O') is not None and len(param.get('O', {})) > 1
        
        # Optimize numeric parameters that are not safety-related
        if param_type == ParameterType.NUMBER.value:
            safety_keywords = ['stop loss', 'take profit', 'deviation']
            return not any(keyword in name for keyword in safety_keywords)
        
        return False
    
    def create_optimization_plan(self, parameters: List[ParameterInfo]) -> List[Dict[str, Any]]:
        """Create an intelligent optimization plan for parameters"""
        optimization_plan = []
        
        for param in parameters:
            if not param.is_optimizable:
                continue
            
            strategy = self._determine_optimization_strategy(param)
            if strategy:
                optimization_values = strategy(param)
                if optimization_values:
                    optimization_plan.append({
                        'key': param.key,
                        'name': param.name,
                        'values': optimization_values,
                        'param_type': param.param_type
                    })
        
        return optimization_plan
    
    def _determine_optimization_strategy(self, param: ParameterInfo):
        """Determine the best optimization strategy for a parameter"""
        name = param.name.lower()
        
        if 'length' in name:
            return self.optimization_strategies['length']
        elif 'fast' in name:
            return self.optimization_strategies['fast']
        elif 'slow' in name:
            return self.optimization_strategies['slow']
        elif 'signal' in name:
            return self.optimization_strategies['signal']
        elif 'level' in name:
            return self.optimization_strategies['level']
        elif 'deviation' in name:
            return self.optimization_strategies['deviation']
        elif param.param_type == ParameterType.BOOLEAN:
            return self.optimization_strategies['boolean']
        elif param.param_type == ParameterType.STRING and param.options:
            return self.optimization_strategies['string']
        
        return None
    
    def _optimize_length_parameter(self, param: ParameterInfo) -> List[Union[int, float]]:
        """Optimize length parameters with focused ranges"""
        try:
            current = float(param.current_value)
            if current <= 10:
                return [max(1, current-2), current, current+2]
            else:
                return [max(1, current-3), current, current+3]
        except (ValueError, TypeError):
            return [param.current_value]
    
    def _optimize_fast_parameter(self, param: ParameterInfo) -> List[int]:
        """Optimize fast parameters (like MACD Fast)"""
        try:
            current = int(float(param.current_value))
            return [max(1, current-3), current, current+3, current+6, current+9]
        except (ValueError, TypeError):
            return [param.current_value]
    
    def _optimize_slow_parameter(self, param: ParameterInfo) -> List[int]:
        """Optimize slow parameters (like MACD Slow)"""
        try:
            current = int(float(param.current_value))
            return [current-10, current, current+10, current+20, current+30, current+40, current+50, current+60]
        except (ValueError, TypeError):
            return [param.current_value]
    
    def _optimize_signal_parameter(self, param: ParameterInfo) -> List[int]:
        """Optimize signal parameters (like MACD Signal)"""
        try:
            current = int(float(param.current_value))
            return [max(1, current-2), current, current+2, current+4, current+6]
        except (ValueError, TypeError):
            return [param.current_value]
    
    def _optimize_level_parameter(self, param: ParameterInfo) -> List[int]:
        """Optimize level parameters (like RSI levels)"""
        try:
            current = int(float(param.current_value))
            if 'buy' in param.name.lower():
                return [max(10, current-10), current, current+5, current+10]
            elif 'sell' in param.name.lower():
                return [current-10, current-5, current, min(90, current+10)]
            else:
                return [current-5, current, current+5]
        except (ValueError, TypeError):
            return [param.current_value]
    
    def _optimize_deviation_parameter(self, param: ParameterInfo) -> List[Union[int, float]]:
        """Optimize deviation parameters"""
        try:
            current = float(param.current_value)
            return [max(0.1, current-0.5), current, current+0.5]
        except (ValueError, TypeError):
            return [param.current_value]
    
    def _optimize_boolean_parameter(self, param: ParameterInfo) -> List[bool]:
        """Optimize boolean parameters"""
        return [True, False]
    
    def _optimize_string_parameter(self, param: ParameterInfo) -> List[str]:
        """Optimize string parameters with options"""
        if param.options:
            return list(param.options.keys())
        return [param.current_value]
    
    def apply_optimization_to_lab(self, lab_parameters: List[Dict[str, Any]], 
                                 optimization_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply optimization plan to lab parameters using the working pattern"""
        updated_parameters = []
        
        for param in lab_parameters:
            key = param.get('K', '')
            current_value = param.get('O', [None])[0] if param.get('O') else None
            
            # Find corresponding optimization plan
            plan_item = next((item for item in optimization_plan if item['key'] == key), None)
            
            if plan_item:
                # Apply optimization values
                optimization_values = plan_item['values']
                param['O'] = [str(val) for val in optimization_values]
                param['IS'] = False  # Keep IS=false like working EXAMPLE lab
                logger.info(f"  ✅ Optimized {plan_item['name']}: {optimization_values}")
            else:
                # Keep original value, ensure IS=false
                param['IS'] = False
                if not param.get('O'):
                    param['O'] = [str(current_value) if current_value is not None else '']
            
            updated_parameters.append(param)
        
        return updated_parameters
    
    def validate_lab_parameters(self, lab_parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate lab parameters and return statistics"""
        total_params = len(lab_parameters)
        optimized_params = sum(1 for p in lab_parameters if p.get('IS', False))
        param_values = sum(len(p.get('O', [])) for p in lab_parameters)
        
        return {
            'total_parameters': total_params,
            'optimized_parameters': optimized_params,
            'total_parameter_values': param_values,
            'optimization_ratio': optimized_params / total_params if total_params > 0 else 0
        }
