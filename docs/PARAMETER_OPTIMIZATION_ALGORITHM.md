# HaasOnline Parameter Optimization Algorithm Documentation

## Overview

The HaasOnline Parameter Optimization Algorithm is a sophisticated system for generating intelligent parameter ranges for trading bot optimization. It combines **strategic values** (proven parameter values from trading literature) with **intelligent ranges** (systematic exploration around optimal areas) to create efficient parameter spaces for backtesting.

## Table of Contents

1. [Algorithm Overview](#algorithm-overview)
2. [Core Concepts](#core-concepts)
3. [Parameter Recognition System](#parameter-recognition-system)
4. [Strategic Values & Intelligent Ranges](#strategic-values--intelligent-ranges)
5. [Generic Parameter Handling](#generic-parameter-handling)
6. [Implementation Details](#implementation-details)
7. [Usage Examples](#usage-examples)
8. [Customization Options](#customization-options)
9. [Performance Considerations](#performance-considerations)
10. [Future Enhancements](#future-enhancements)

## Algorithm Overview

### Philosophy

The algorithm is based on the principle that **not all parameter values are equally likely to be optimal**. Instead of uniform sampling across parameter ranges, it focuses testing effort on:

1. **Proven values** from trading literature and common practice
2. **Exploration ranges** around these proven values
3. **Strategic gaps** to test extreme scenarios

### Key Benefits

- **Efficiency**: Finds optimal parameters faster than linear ranges
- **Domain Knowledge**: Incorporates trading expertise into optimization
- **Adaptability**: Handles both known and unknown parameter types
- **Safety**: Prevents combinatorial explosion while maintaining coverage

## Core Concepts

### 1. Strategic Values

**Definition**: Specific parameter values that are known to work well based on:
- Trading literature (e.g., RSI 14 from Wilder's original work)
- Common industry practices (e.g., 1min, 5min, 15min timeframes)
- Institutional trading standards
- Empirical research findings

**Examples**:
```python
# RSI Length strategic values
strategic_values = [5, 9, 14, 21]  # 14 is Wilder's original, others are common variants

# Timeframe strategic values  
strategic_values = [1, 5, 15, 60]  # 1min, 5min, 15min, 1hour
```

### 2. Intelligent Ranges

**Definition**: Systematic exploration ranges around strategic values or current parameter values, designed to:
- Fine-tune around optimal areas
- Test variations of proven values
- Explore adjacent parameter spaces

**Examples**:
```python
# Fine-tuning range around RSI 14
range1 = list(range(10, 18, 2))   # [10, 12, 14, 16] - dense sampling around 14

# Extended exploration range
range2 = list(range(25, 35, 3))   # [25, 28, 31, 34] - sparse sampling of longer periods
```

### 3. Mixed Parameter Lists

**Definition**: The combination of strategic values and intelligent ranges, with deduplication and sorting:

```python
mixed_list = strategic_values + range1 + range2
final_result = [str(v) for v in sorted(set(mixed_list))]
```

## Parameter Recognition System

The algorithm uses pattern matching on parameter names to determine the appropriate optimization strategy:

### Recognition Patterns

```python
param_lower = param_name.lower()

# RSI Parameters
if 'rsi' in param_lower and 'length' in param_lower:
    # Apply RSI-specific optimization

# Overbought/Oversold Levels
elif 'overbought' in param_lower:
    # Apply overbought-specific optimization
elif 'oversold' in param_lower:
    # Apply oversold-specific optimization

# Timeframe Parameters
elif 'interval' in param_lower:
    # Apply timeframe-specific optimization

# Risk Management
elif 'stoploss' in param_lower or 'stop' in param_lower:
    # Apply stoploss-specific optimization

# Generic Parameters
else:
    # Apply generic optimization strategy
```

### Case Insensitive Matching

The system converts all parameter names to lowercase for matching, making it robust against different naming conventions:
- "RSI Length" → "rsi length"
- "RSI_LENGTH" → "rsi_length"  
- "rsiLength" → "rsilength"

## Strategic Values & Intelligent Ranges

### RSI Length Parameters

**Parameter Pattern**: `'rsi' in param_name and 'length' in param_name`

**Strategic Values**: `[5, 9, 14, 21]`
- **RSI 5**: Ultra-short term, used in scalping
- **RSI 9**: Short-term trading standard
- **RSI 14**: Wilder's original (1978), most widely used
- **RSI 21**: Fibonacci-based period, swing trading

**Intelligent Ranges**:
```python
range1 = list(range(10, 18, 2))   # [10, 12, 14, 16] - Fine-tune around 14
range2 = list(range(25, 35, 3))   # [25, 28, 31, 34] - Test longer periods
```

**Final Result**: `[5, 9, 10, 12, 14, 16, 21, 25, 28, 31, 34]`

**Rationale**:
- Includes the most common RSI periods
- Dense sampling around RSI 14 (most popular)
- Sparse sampling of longer periods for different market conditions
- Strategic gaps to avoid over-testing similar values

### Overbought Parameters

**Parameter Pattern**: `'overbought' in param_name`

**Strategic Values**: `[20, 25, 30]`
- **20**: Very sensitive, more signals
- **25**: Moderate sensitivity
- **30**: Conservative, fewer false signals

**Intelligent Ranges**:
```python
range1 = list(range(65, 85, 5))   # [65, 70, 75, 80] - Higher sensitivity range
```

**Final Result**: `[20, 25, 30, 65, 70, 75, 80]`

**Rationale**:
- Tests both conservative (20-30) and standard (65-80) overbought levels
- Strategic gap between 30 and 65 avoids testing ineffective middle ranges
- Covers different market volatility scenarios

### Oversold Parameters

**Parameter Pattern**: `'oversold' in param_name`

**Strategic Values**: `[70, 75, 80]`
- **70**: Standard oversold level (Wilder's original)
- **75**: Moderate oversold
- **80**: Conservative oversold

**Intelligent Ranges**:
```python
range1 = list(range(15, 35, 5))   # [15, 20, 25, 30] - Lower sensitivity range
```

**Final Result**: `[15, 20, 25, 30, 70, 75, 80]`

**Rationale**:
- Tests both aggressive (15-30) and standard (70-80) oversold levels
- Strategic gap prevents testing ineffective middle ranges
- Balances signal frequency vs accuracy

### Timeframe/Interval Parameters

**Parameter Pattern**: `'interval' in param_name`

**Strategic Values**: `[1, 5, 15, 60]`
- **1**: 1-minute scalping
- **5**: 5-minute day trading standard
- **15**: 15-minute swing trading
- **60**: 1-hour position trading

**Intelligent Ranges**:
```python
range1 = list(range(2, 8, 2))     # [2, 4, 6] - Short-term variations
```

**Final Result**: `[1, 2, 4, 5, 6, 15, 60]`

**Rationale**:
- Covers major timeframe categories
- Tests variations in short-term range (2, 4, 6 minutes)
- Strategic gaps avoid over-testing similar timeframes

### Stoploss Parameters

**Parameter Pattern**: `'stoploss' in param_name or 'stop' in param_name`

**Strategic Values**: `[1, 2, 3, 5]`
- **1-2%**: Conservative risk management
- **3%**: Moderate risk (Elder's recommendations)
- **5%**: Aggressive but within risk management guidelines

**Intelligent Ranges**:
```python
range1 = list(range(7, 15, 2))    # [7, 9, 11, 13] - Wider stops
```

**Final Result**: `[1, 2, 3, 5, 7, 9, 11, 13]`

**Rationale**:
- Tests tight risk management (1-5%)
- Explores wider stops for different market conditions
- Strategic gap between 5% and 7% separates risk categories

## Generic Parameter Handling

For parameters that don't match any known patterns, the algorithm uses a **current-value-centered approach**:

### Integer Parameters

```python
# Generic integer parameter
specific_values = [current_val]                                    # Anchor point
range1 = list(range(max(1, current_val - 3), current_val, 1))     # Lower range
range2 = list(range(current_val + 1, current_val + 8, 2))         # Upper range
```

**Example**: `current_value = 10`
- **Strategic Values**: `[10]`
- **Lower Range**: `[7, 8, 9]` (dense sampling below)
- **Upper Range**: `[11, 13, 15, 17]` (sparse sampling above)
- **Final Result**: `[7, 8, 9, 10, 11, 13, 15, 17]`

**Rationale**:
- Current value assumed to have some validity
- Asymmetric sampling (parameters often work better when reduced)
- Safety bounds prevent negative values

### Decimal Parameters

```python
# Generic decimal parameter
specific_values = [current_val]
range1 = [round(current_val + i * 0.1, 2) for i in range(-5, 6)]
```

**Example**: `current_value = 2.5`
- **Final Result**: `[2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0]`

**Rationale**:
- Fine-grained exploration around current value
- Symmetric sampling for decimal precision
- Reasonable range size (11 values)

### Special Decimal Parameters

**Multiplier/Factor Parameters**:
```python
if 'multiplier' in param_lower or 'factor' in param_lower:
    specific_values = [0.5, 1.0, 1.5, 2.0]  # Common multipliers
    range1 = [current_val + i * 0.25 for i in range(-2, 3)]  # Fine adjustments
```

## Implementation Details

### Algorithm Flow

1. **Parameter Name Analysis**
   ```python
   param_lower = param_name.lower()
   ```

2. **Pattern Matching**
   ```python
   if 'rsi' in param_lower and 'length' in param_lower:
       # RSI-specific logic
   elif 'overbought' in param_lower:
       # Overbought-specific logic
   # ... other patterns
   else:
       # Generic logic
   ```

3. **Range Generation**
   ```python
   strategic_values = [...]  # Domain-specific values
   range1 = list(range(...))  # Exploration range 1
   range2 = list(range(...))  # Exploration range 2 (optional)
   ```

4. **Combination & Deduplication**
   ```python
   mixed_list = strategic_values + range1 + range2
   final_result = [str(v) for v in sorted(set(mixed_list))]
   ```

### Safety Mechanisms

1. **Negative Value Prevention**
   ```python
   max(1, current_val - 3)  # For integer parameters
   [v for v in mixed_list if v > 0]  # For decimal parameters
   ```

2. **Combination Limits**
   ```python
   if total_combinations > config.max_combinations:
       return OptimizationResult(success=False, error_message="Too many combinations")
   ```

3. **Parameter Validation**
   ```python
   if not all(key in param_dict for key in ['K', 'T', 'O']):
       log.warning(f"⚠️ Skipping invalid parameter: {param_dict}")
       continue
   ```

## Usage Examples

### Basic Usage

```python
from pyHaasAPI.optimization import optimize_lab_parameters_mixed

# Optimize with mixed strategy
result = optimize_lab_parameters_mixed(executor, lab_id, max_combinations=50000)

if result.success:
    print(f"Optimized {result.optimized_parameters} parameters")
    print(f"Total combinations: {result.total_combinations:,}")
else:
    print(f"Optimization failed: {result.error_message}")
```

### Advanced Configuration

```python
from pyHaasAPI.optimization import LabParameterOptimizer, OptimizationConfig, OptimizationStrategy

# Create custom configuration
config = OptimizationConfig(
    strategy=OptimizationStrategy.MIXED,
    max_combinations=25000,
    enable_all_parameters=True,
    preserve_current_values=True,
    custom_ranges={
        "MyCustomParameter": ["5", "10", "15", "20", "25"],
        "AnotherParameter": ["1.0", "1.5", "2.0", "2.5", "3.0"]
    }
)

# Run optimization
optimizer = LabParameterOptimizer(executor)
result = optimizer.optimize_lab_parameters(lab_id, config)
```

### Result Analysis

```python
if result.success:
    print(f"Optimization Results:")
    print(f"  Strategy: {result.strategy_used.value}")
    print(f"  Total Parameters: {result.total_parameters}")
    print(f"  Optimized Parameters: {result.optimized_parameters}")
    print(f"  Total Combinations: {result.total_combinations:,}")
    
    print(f"\nParameter Details:")
    for param in result.parameter_details:
        print(f"  {param['name']}: {param['options_count']} options")
        print(f"    Values: {param['options']}")
        print(f"    Enabled: {param['enabled']}")
```

## Customization Options

### Custom Parameter Ranges

Override automatic range generation for specific parameters:

```python
custom_ranges = {
    "RSI Length": ["10", "14", "21"],  # Override RSI with specific values
    "CustomFactor": ["1", "2", "5", "10"],  # Define range for unknown parameter
}

config = OptimizationConfig(custom_ranges=custom_ranges)
```

### Strategy Selection

Choose different optimization strategies:

```python
# Traditional linear ranges
config = OptimizationConfig(strategy=OptimizationStrategy.TRADITIONAL)

# Mixed strategic + intelligent ranges
config = OptimizationConfig(strategy=OptimizationStrategy.MIXED)

# Conservative (smaller ranges)
config = OptimizationConfig(strategy=OptimizationStrategy.CONSERVATIVE)
```

### Safety Limits

Control the maximum number of parameter combinations:

```python
config = OptimizationConfig(
    max_combinations=10000,  # Prevent server overload
    enable_all_parameters=False  # Only enable parameters with ranges
)
```

## Performance Considerations

### Combination Explosion

The algorithm includes several mechanisms to prevent combinatorial explosion:

1. **Strategic Gaps**: Intentional gaps in parameter ranges avoid testing similar values
2. **Asymmetric Sampling**: Different step sizes for different ranges
3. **Safety Limits**: Maximum combination limits with early termination
4. **Intelligent Defaults**: Reasonable range sizes for each parameter type

### Memory Usage

Parameter ranges are generated on-demand and stored as lists of strings:

```python
# Memory-efficient string storage
return [str(v) for v in sorted(set(mixed_list))]
```

### Computational Complexity

- **Time Complexity**: O(n) where n is the number of parameters
- **Space Complexity**: O(m) where m is the total number of parameter values
- **Range Generation**: O(k) where k is the size of each range

## Future Enhancements

### 1. Data-Driven Strategic Values

Replace hardcoded strategic values with values derived from:
- Historical backtest performance data
- Market research databases
- Community-contributed optimal values

```python
def get_strategic_values_from_data(param_name: str) -> List[str]:
    """Get strategic values from performance database"""
    research_data = load_parameter_research(param_name)
    return research_data.get_top_performers(percentile=90)
```

### 2. Adaptive Range Generation

Adjust ranges based on:
- Current market conditions
- Asset class (crypto vs forex vs stocks)
- Strategy type (scalping vs swing trading)

```python
def generate_adaptive_range(param_name: str, market_context: MarketContext) -> List[str]:
    """Generate ranges adapted to market conditions"""
    if market_context.volatility > 0.5:
        return generate_high_volatility_range(param_name)
    else:
        return generate_low_volatility_range(param_name)
```

### 3. Machine Learning Integration

Use ML models to predict optimal parameter ranges:
- Neural networks trained on backtest results
- Reinforcement learning for parameter exploration
- Bayesian optimization for efficient parameter search

### 4. Multi-Objective Optimization

Extend to optimize multiple objectives simultaneously:
- ROI vs Risk (Sharpe ratio)
- Profit vs Drawdown
- Win rate vs Average win size

### 5. Dynamic Range Adjustment

Adjust ranges based on optimization progress:
- Narrow ranges around promising areas
- Expand ranges if no good solutions found
- Use genetic algorithm principles for range evolution

## Conclusion

The HaasOnline Parameter Optimization Algorithm represents a sophisticated approach to trading bot parameter optimization that combines domain expertise with systematic exploration. By focusing testing effort on proven parameter values and their intelligent variations, it achieves better optimization results with fewer backtests compared to traditional linear range approaches.

The algorithm's modular design allows for easy customization and extension, making it suitable for a wide range of trading strategies and parameter types. Its safety mechanisms and performance considerations ensure reliable operation even with complex parameter spaces.

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Authors**: HaasAPI Development Team