# Parameter Optimization Quick Reference

## Quick Start

```python
from pyHaasAPI.optimization import optimize_lab_parameters_mixed

# Basic optimization
result = optimize_lab_parameters_mixed(executor, lab_id)

if result.success:
    print(f"✅ Optimized {result.optimized_parameters} parameters")
    print(f"🚀 Total combinations: {result.total_combinations:,}")
else:
    print(f"❌ Failed: {result.error_message}")
```

## Parameter Recognition Patterns

| Parameter Name Contains | Strategy Applied | Example Values |
|------------------------|------------------|----------------|
| `rsi` + `length` | RSI Length | `[5, 9, 10, 12, 14, 16, 21, 25, 28, 31, 34]` |
| `overbought` | Overbought Levels | `[20, 25, 30, 65, 70, 75, 80]` |
| `oversold` | Oversold Levels | `[15, 20, 25, 30, 70, 75, 80]` |
| `interval` | Timeframes | `[1, 2, 4, 5, 6, 15, 60]` |
| `stoploss` or `stop` | Stop Loss | `[1, 2, 3, 5, 7, 9, 11, 13]` |
| `multiplier` or `factor` | Multipliers | `[0.5, 1.0, 1.5, 2.0] + fine adjustments` |
| *anything else* | Generic | Current value ± intelligent range |

## Optimization Strategies

### Mixed Strategy (Recommended)
```python
from pyHaasAPI.optimization import optimize_lab_parameters_mixed

result = optimize_lab_parameters_mixed(executor, lab_id, max_combinations=50000)
```
- **Best for**: Most trading strategies
- **Combines**: Strategic values + intelligent ranges
- **Typical combinations**: 10,000 - 150,000

### Traditional Strategy
```python
from pyHaasAPI.optimization import optimize_lab_parameters_traditional

result = optimize_lab_parameters_traditional(executor, lab_id, max_combinations=10000)
```
- **Best for**: Simple linear testing
- **Creates**: Min/Max/Step ranges
- **Typical combinations**: 1,000 - 10,000

## Custom Configuration

```python
from pyHaasAPI.optimization import LabParameterOptimizer, OptimizationConfig, OptimizationStrategy

config = OptimizationConfig(
    strategy=OptimizationStrategy.MIXED,
    max_combinations=25000,
    custom_ranges={
        "MyParameter": ["1", "5", "10", "20"],
        "AnotherParam": ["0.5", "1.0", "1.5", "2.0"]
    }
)

optimizer = LabParameterOptimizer(executor)
result = optimizer.optimize_lab_parameters(lab_id, config)
```

## Result Analysis

```python
if result.success:
    print(f"Strategy: {result.strategy_used.value}")
    print(f"Parameters: {result.optimized_parameters}/{result.total_parameters}")
    print(f"Combinations: {result.total_combinations:,}")
    
    for param in result.parameter_details:
        print(f"{param['name']}: {param['options_count']} values")
```

## Common Use Cases

### RSI Strategy Optimization
```python
# Will automatically recognize RSI parameters and apply intelligent ranges
result = optimize_lab_parameters_mixed(executor, rsi_lab_id)
# Expected: RSI Length gets [5,9,14,21] + fine-tuning ranges
```

### Custom Strategy with Unknown Parameters
```python
# Unknown parameters get current-value-centered ranges
config = OptimizationConfig(
    custom_ranges={
        "UnknownParam1": ["10", "20", "30", "40", "50"],  # Override generic
        "UnknownParam2": None  # Use generic algorithm
    }
)
```

### Safety-First Optimization
```python
config = OptimizationConfig(
    strategy=OptimizationStrategy.CONSERVATIVE,
    max_combinations=5000,  # Small, safe ranges
    enable_all_parameters=False  # Only enable parameters with ranges
)
```

## Troubleshooting

### Too Many Combinations
```python
# Reduce max_combinations or use traditional strategy
result = optimize_lab_parameters_traditional(executor, lab_id, max_combinations=5000)
```

### Parameter Not Recognized
```python
# Use custom ranges for unknown parameters
config = OptimizationConfig(
    custom_ranges={"WeirdParameterName": ["1", "2", "5", "10"]}
)
```

### Server Overload
```python
# Use conservative limits
config = OptimizationConfig(
    max_combinations=1000,
    strategy=OptimizationStrategy.CONSERVATIVE
)
```

## Algorithm Logic Summary

1. **Parameter Name Analysis**: Convert to lowercase, pattern matching
2. **Strategic Values**: Domain-specific proven values (RSI 14, timeframes 1/5/15/60)
3. **Intelligent Ranges**: Systematic exploration around strategic values
4. **Generic Fallback**: Current-value-centered ranges for unknown parameters
5. **Combination & Safety**: Deduplicate, sort, check limits

## Performance Guidelines

| Lab Complexity | Recommended Strategy | Max Combinations | Expected Time |
|----------------|---------------------|------------------|---------------|
| Simple (1-3 params) | Mixed | 50,000 | Fast |
| Medium (4-6 params) | Mixed | 25,000 | Medium |
| Complex (7+ params) | Traditional | 10,000 | Medium |
| Very Complex | Conservative | 5,000 | Fast |

## Best Practices

1. **Start with Mixed strategy** for most use cases
2. **Use custom ranges** for critical parameters
3. **Monitor combination counts** to prevent server overload
4. **Test with small ranges first** before full optimization
5. **Analyze results** to understand which parameters matter most