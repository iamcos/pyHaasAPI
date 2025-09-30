"""
HaasOnline Lab Parameter Optimization Module

This module provides advanced parameter optimization capabilities for HaasOnline Labs,
supporting both traditional linear ranges and sophisticated mixed parameter approaches.

## Core Algorithm: Strategic Values + Intelligent Ranges

The optimization algorithm combines:
1. **Strategic Values**: Proven parameter values from trading literature (e.g., RSI 14, timeframes 1/5/15/60)
2. **Intelligent Ranges**: Systematic exploration around strategic values with intentional gaps
3. **Generic Fallback**: Current-value-centered ranges for unknown parameters

## Key Features

- **Domain Knowledge Integration**: Uses trading expertise for parameter selection
- **Pattern Recognition**: Automatically detects parameter types (RSI, overbought, timeframes, etc.)
- **Mixed Strategy**: Combines specific values with exploration ranges
- **Safety Mechanisms**: Prevents server overload with combination limits
- **Customization**: Supports custom ranges for specific parameters
- **Comprehensive Results**: Detailed optimization reports and analysis

## Quick Start

```python
from pyHaasAPI_v1.optimization import optimize_lab_parameters_mixed

# Basic optimization with mixed strategy
result = optimize_lab_parameters_mixed(executor, lab_id)

if result.success:
    print(f"Optimized {result.optimized_parameters} parameters")
    print(f"Total combinations: {result.total_combinations:,}")
```

## Parameter Recognition Examples

- **RSI Length**: `[5, 9, 10, 12, 14, 16, 21, 25, 28, 31, 34]` (strategic + fine-tuning)
- **Overbought**: `[20, 25, 30, 65, 70, 75, 80]` (conservative + standard levels)
- **Timeframes**: `[1, 2, 4, 5, 6, 15, 60]` (common intervals + variations)
- **Generic**: Current value ± intelligent exploration range

## Documentation

See `docs/PARAMETER_OPTIMIZATION_ALGORITHM.md` for detailed algorithm documentation.
See `docs/PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md` for usage examples.

Author: HaasAPI Team
Version: 1.0.0
"""

from enum import Enum
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass
import logging

from pyHaasAPI_v1.api import SyncExecutor, Authenticated, get_lab_details, update_lab_details
from pyHaasAPI_v1.model import LabDetails
from pyHaasAPI_v1.parameters import ParameterType
from loguru import logger as log


class OptimizationStrategy(Enum):
    """
    Parameter optimization strategies available for lab parameter ranges.
    
    TRADITIONAL: Linear Min/Max/Step ranges (e.g., 10-30 step 2)
    MIXED: Strategic values combined with intelligent ranges
    CONSERVATIVE: Smaller ranges to prevent server overload
    AGGRESSIVE: Larger ranges for comprehensive testing
    """
    TRADITIONAL = "traditional"
    MIXED = "mixed"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


@dataclass
class OptimizationConfig:
    """
    Configuration for parameter optimization.
    
    Attributes:
        strategy: The optimization strategy to use
        max_combinations: Maximum allowed parameter combinations (safety limit)
        enable_all_parameters: Whether to enable all parameters for optimization
        preserve_current_values: Whether to include current values in ranges
        custom_ranges: Custom parameter ranges (overrides automatic generation)
    """
    strategy: OptimizationStrategy = OptimizationStrategy.MIXED
    max_combinations: int = 50000
    enable_all_parameters: bool = True
    preserve_current_values: bool = True
    custom_ranges: Optional[Dict[str, List[str]]] = None


@dataclass
class OptimizationResult:
    """
    Result of parameter optimization operation.
    
    Attributes:
        success: Whether the optimization was successful
        lab_id: ID of the optimized lab
        total_parameters: Total number of parameters in the lab
        optimized_parameters: Number of parameters with optimization ranges
        total_combinations: Total possible parameter combinations
        strategy_used: The optimization strategy that was applied
        parameter_details: Details of each optimized parameter
        error_message: Error message if optimization failed
    """
    success: bool
    lab_id: str
    total_parameters: int = 0
    optimized_parameters: int = 0
    total_combinations: int = 0
    strategy_used: OptimizationStrategy = OptimizationStrategy.MIXED
    parameter_details: List[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ParameterRangeGenerator:
    """
    Generates parameter ranges based on different optimization strategies.
    """
    
    @staticmethod
    def generate_traditional_range(param_name: str, current_value: Union[int, float], param_type: str) -> List[str]:
        """
        Generate traditional linear parameter ranges (Min/Max/Step approach).
        
        Creates simple linear ranges that match web interface display:
        - RSI length: 10-25 step 3
        - Overbought: 20-35 step 5
        - Oversold: 65-80 step 5
        
        Args:
            param_name: Name of the parameter for range selection
            current_value: Current parameter value
            param_type: 'integer' or 'decimal'
            
        Returns:
            List of string values for traditional optimization
        """
        param_lower = param_name.lower()
        
        if param_type == 'integer':
            current_val = int(current_value)
            
            # RSI Length traditional range
            if 'rsi' in param_lower and 'length' in param_lower:
                return [str(v) for v in range(10, 26, 3)]  # 10, 13, 16, 19, 22, 25
            
            # Overbought traditional range
            elif 'overbought' in param_lower:
                return [str(v) for v in range(20, 36, 5)]  # 20, 25, 30, 35
                
            # Oversold traditional range
            elif 'oversold' in param_lower:
                return [str(v) for v in range(65, 81, 5)]  # 65, 70, 75, 80
            
            # Interval traditional range
            elif 'interval' in param_lower:
                return ['1', '5', '15']  # Common timeframes
            
            # Stoploss traditional range
            elif 'stoploss' in param_lower or 'stop' in param_lower:
                return [str(v) for v in range(1, 8, 2)]  # 1, 3, 5, 7
            
            # Generic integer parameter
            else:
                return [str(current_val - 1), str(current_val), str(current_val + 1), str(current_val + 2)]
        
        else:  # decimal
            current_val = float(current_value)
            start = max(0.1, current_val - 1.0)
            end = current_val + 2.0
            step = 0.5
            values = []
            val = start
            while val <= end:
                values.append(str(round(val, 2)))
                val += step
            return values

    @staticmethod
    def generate_mixed_range(param_name: str, current_value: Union[int, float], param_type: str) -> List[str]:
        """
        Generate sophisticated mixed parameter ranges with strategic values AND intelligent ranges.
        
        ## Algorithm Overview
        
        1. **Parameter Recognition**: Pattern matching on parameter name (case-insensitive)
        2. **Strategic Values**: Domain-specific proven values from trading literature
        3. **Intelligent Ranges**: Systematic exploration around strategic areas
        4. **Combination**: Merge, deduplicate, and sort all values
        
        ## Examples
        
        **RSI Length** (`param_name="6-6-9-14.RSI length"`, `current_value=13`):
        - Strategic: [5, 9, 14, 21] (Wilder's original + common variants)
        - Range 1: [10, 12, 14, 16] (fine-tune around 14)
        - Range 2: [25, 28, 31, 34] (test longer periods)
        - Result: [5, 9, 10, 12, 14, 16, 21, 25, 28, 31, 34]
        
        **Overbought** (`param_name="Overbought"`, `current_value=70`):
        - Strategic: [20, 25, 30] (conservative levels)
        - Range 1: [65, 70, 75, 80] (standard levels)
        - Result: [20, 25, 30, 65, 70, 75, 80]
        
        **Generic Parameter** (`param_name="CustomFactor"`, `current_value=10`):
        - Strategic: [10] (current value as anchor)
        - Range 1: [7, 8, 9] (below current, dense)
        - Range 2: [11, 13, 15, 17] (above current, sparse)
        - Result: [7, 8, 9, 10, 11, 13, 15, 17]
        
        Args:
            param_name: Name of the parameter for intelligent range selection
            current_value: Current parameter value (used as fallback anchor)
            param_type: 'integer' or 'decimal'
            
        Returns:
            List of string values for mixed optimization, sorted and deduplicated
            
        Note:
            The algorithm uses intentional gaps in parameter ranges to avoid testing
            similar values and focus effort on high-probability optimal regions.
        """
        param_lower = param_name.lower()
        
        if param_type == 'integer':
            current_val = int(current_value)
            
            # RSI Length optimization
            if 'rsi' in param_lower and 'length' in param_lower:
                specific_values = [5, 9, 14, 21]  # Common RSI periods
                range1 = list(range(10, 18, 2))   # Fine-tune around 14
                range2 = list(range(25, 35, 3))   # Test longer periods
                mixed_list = specific_values + range1 + range2
                return [str(v) for v in sorted(set(mixed_list))]
            
            # Overbought/Oversold levels
            elif 'overbought' in param_lower:
                specific_values = [20, 25, 30]    # Common overbought levels
                range1 = list(range(65, 85, 5))   # Higher sensitivity range
                mixed_list = specific_values + range1
                return [str(v) for v in sorted(set(mixed_list))]
                
            elif 'oversold' in param_lower:
                specific_values = [70, 75, 80]    # Common oversold levels  
                range1 = list(range(15, 35, 5))   # Lower sensitivity range
                mixed_list = specific_values + range1
                return [str(v) for v in sorted(set(mixed_list))]
            
            # Interval/Timeframe optimization
            elif 'interval' in param_lower:
                specific_values = [1, 5, 15, 60]  # Common timeframes
                range1 = list(range(2, 8, 2))     # Short-term range
                mixed_list = specific_values + range1
                return [str(v) for v in sorted(set(mixed_list))]
            
            # Stoploss optimization
            elif 'stoploss' in param_lower or 'stop' in param_lower:
                specific_values = [1, 2, 3, 5]    # Conservative stops
                range1 = list(range(7, 15, 2))    # Wider stops
                mixed_list = specific_values + range1
                return [str(v) for v in sorted(set(mixed_list))]
            
            # Generic integer parameter
            else:
                specific_values = [current_val]
                range1 = list(range(max(1, current_val - 3), current_val, 1))
                range2 = list(range(current_val + 1, current_val + 8, 2))
                mixed_list = specific_values + range1 + range2
                return [str(v) for v in sorted(set(mixed_list))]
        
        else:  # decimal
            current_val = float(current_value)
            
            # Decimal parameter optimization with mixed approach
            if 'multiplier' in param_lower or 'factor' in param_lower:
                specific_values = [0.5, 1.0, 1.5, 2.0]  # Common multipliers
                range1 = [round(x, 2) for x in [current_val + i * 0.25 for i in range(-2, 3)]]
                mixed_list = specific_values + range1
                return [str(v) for v in sorted(set(mixed_list))]
            
            # Generic decimal parameter
            else:
                specific_values = [current_val]
                range1 = [round(current_val + i * 0.1, 2) for i in range(-5, 6)]
                mixed_list = specific_values + range1
                return [str(v) for v in sorted(set([v for v in mixed_list if v > 0]))]


class LabParameterOptimizer:
    """
    Main class for optimizing lab parameters with different strategies.
    """
    
    def __init__(self, executor: SyncExecutor[Authenticated]):
        """
        Initialize the parameter optimizer.
        
        Args:
            executor: Authenticated HaasOnline API executor
        """
        self.executor = executor
        self.range_generator = ParameterRangeGenerator()
    
    def optimize_lab_parameters(
        self, 
        lab_id: str, 
        config: OptimizationConfig = None
    ) -> OptimizationResult:
        """
        Optimize lab parameters using the specified strategy.
        
        Args:
            lab_id: ID of the lab to optimize
            config: Optimization configuration (uses defaults if None)
            
        Returns:
            OptimizationResult with details of the optimization
        """
        if config is None:
            config = OptimizationConfig()
        
        try:
            # Get current lab details
            lab_details = get_lab_details(self.executor, lab_id)
            
            # Generate optimized parameters
            updated_parameters = self._generate_optimized_parameters(
                lab_details.parameters, 
                config
            )
            
            # Calculate total combinations
            total_combinations = self._calculate_combinations(updated_parameters)
            
            # Check safety limits
            if total_combinations > config.max_combinations:
                return OptimizationResult(
                    success=False,
                    lab_id=lab_id,
                    error_message=f"Too many combinations ({total_combinations:,}). Max allowed: {config.max_combinations:,}"
                )
            
            # Update lab with optimized parameters
            lab_details.parameters = updated_parameters
            updated_lab = update_lab_details(self.executor, lab_details)
            
            # Count optimized parameters
            optimized_count = sum(1 for p in updated_parameters if len(p.get('O', [])) > 1)
            
            # Create parameter details
            parameter_details = []
            for param in updated_parameters:
                param_name = param.get('K', 'Unknown')
                param_options = param.get('O', [])
                parameter_details.append({
                    'name': param_name,
                    'options_count': len(param_options),
                    'options': param_options,
                    'enabled': param.get('I', False)
                })
            
            return OptimizationResult(
                success=True,
                lab_id=lab_id,
                total_parameters=len(updated_parameters),
                optimized_parameters=optimized_count,
                total_combinations=total_combinations,
                strategy_used=config.strategy,
                parameter_details=parameter_details
            )
            
        except Exception as e:
            log.error(f"Parameter optimization failed: {e}")
            return OptimizationResult(
                success=False,
                lab_id=lab_id,
                error_message=str(e)
            )
    
    def _generate_optimized_parameters(
        self, 
        parameters: List[Dict[str, Any]], 
        config: OptimizationConfig
    ) -> List[Dict[str, Any]]:
        """
        Generate optimized parameters based on the configuration.
        
        Args:
            parameters: Current lab parameters
            config: Optimization configuration
            
        Returns:
            List of optimized parameter dictionaries
        """
        updated_parameters = []
        
        for param in parameters:
            # Handle both dict and object parameters
            if isinstance(param, dict):
                param_dict = param.copy()
            elif hasattr(param, 'model_dump'):
                param_dict = param.model_dump()
            else:
                param_dict = dict(param) if hasattr(param, '__iter__') else {'K': str(param)}
            
            # Validate parameter has required fields
            if not all(key in param_dict for key in ['K', 'T', 'O']):
                log.warning(f"⚠️ Skipping invalid parameter: {param_dict}")
                continue
            
            # Check if custom range is provided
            param_name = param_dict['K']
            if config.custom_ranges and param_name in config.custom_ranges:
                param_dict['O'] = config.custom_ranges[param_name]
                param_dict['I'] = True
                log.info(f"🔧 Applied custom range for {param_name}: {param_dict['O']}")
            
            # Generate ranges for numeric parameters
            elif param_dict.get('T') in [0, 1]:  # INTEGER or DECIMAL types
                current_value = param_dict['O'][0] if param_dict['O'] else '0'
                
                try:
                    current_val = float(current_value)
                    
                    # Skip boolean or string values
                    if str(current_value).lower() in ['true', 'false'] or param_dict.get('T') == 3:
                        log.info(f"⏭️ Skipping non-numeric parameter {param_name}: {current_value}")
                        updated_parameters.append(param_dict)
                        continue
                    
                    # Generate range based on strategy
                    if config.strategy == OptimizationStrategy.TRADITIONAL:
                        param_type = 'integer' if param_dict.get('T') == 0 else 'decimal'
                        new_options = self.range_generator.generate_traditional_range(
                            param_name, current_val, param_type
                        )
                    elif config.strategy == OptimizationStrategy.MIXED:
                        param_type = 'integer' if param_dict.get('T') == 0 else 'decimal'
                        new_options = self.range_generator.generate_mixed_range(
                            param_name, current_val, param_type
                        )
                    else:
                        # Default to mixed strategy
                        param_type = 'integer' if param_dict.get('T') == 0 else 'decimal'
                        new_options = self.range_generator.generate_mixed_range(
                            param_name, current_val, param_type
                        )
                    
                    param_dict['O'] = new_options
                    param_dict['I'] = config.enable_all_parameters
                    
                    log.info(f"🔧 Generated {config.strategy.value} range for {param_name}: {new_options}")
                    
                except (ValueError, TypeError):
                    log.info(f"⏭️ Skipping non-numeric parameter {param_name}: {current_value}")
            
            # Ensure the parameter has the enabled field set properly
            if 'I' not in param_dict:
                param_dict['I'] = len(param_dict.get('O', [])) > 1 and config.enable_all_parameters
            
            updated_parameters.append(param_dict)
        
        return updated_parameters
    
    def _calculate_combinations(self, parameters: List[Dict[str, Any]]) -> int:
        """
        Calculate total possible parameter combinations.
        
        Args:
            parameters: List of parameter dictionaries
            
        Returns:
            Total number of possible combinations
        """
        total_combinations = 1
        for param in parameters:
            if param.get('I', False) and len(param.get('O', [])) > 1:
                total_combinations *= len(param['O'])
        return total_combinations


# Convenience functions for backward compatibility and ease of use
def optimize_lab_parameters_mixed(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    max_combinations: int = 50000
) -> OptimizationResult:
    """
    Optimize lab parameters using mixed strategy (strategic values + ranges).
    
    Args:
        executor: Authenticated HaasOnline API executor
        lab_id: ID of the lab to optimize
        max_combinations: Maximum allowed parameter combinations
        
    Returns:
        OptimizationResult with details of the optimization
    """
    optimizer = LabParameterOptimizer(executor)
    config = OptimizationConfig(
        strategy=OptimizationStrategy.MIXED,
        max_combinations=max_combinations
    )
    return optimizer.optimize_lab_parameters(lab_id, config)


def optimize_lab_parameters_traditional(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    max_combinations: int = 10000
) -> OptimizationResult:
    """
    Optimize lab parameters using traditional linear ranges (Min/Max/Step).
    
    Args:
        executor: Authenticated HaasOnline API executor
        lab_id: ID of the lab to optimize
        max_combinations: Maximum allowed parameter combinations
        
    Returns:
        OptimizationResult with details of the optimization
    """
    optimizer = LabParameterOptimizer(executor)
    config = OptimizationConfig(
        strategy=OptimizationStrategy.TRADITIONAL,
        max_combinations=max_combinations
    )
    return optimizer.optimize_lab_parameters(lab_id, config)


# Legacy function names for backward compatibility
def update_lab_parameter_ranges(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    randomize: bool = True
) -> LabDetails:
    """
    Legacy function for updating lab parameter ranges (mixed strategy).
    
    Note: This function is deprecated. Use optimize_lab_parameters_mixed() instead.
    """
    result = optimize_lab_parameters_mixed(executor, lab_id)
    if result.success:
        return get_lab_details(executor, lab_id)
    else:
        raise Exception(result.error_message)


def update_lab_parameter_ranges_traditional(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    randomize: bool = True
) -> LabDetails:
    """
    Legacy function for updating lab parameter ranges (traditional strategy).
    
    Note: This function is deprecated. Use optimize_lab_parameters_traditional() instead.
    """
    result = optimize_lab_parameters_traditional(executor, lab_id)
    if result.success:
        return get_lab_details(executor, lab_id)
    else:
        raise Exception(result.error_message)