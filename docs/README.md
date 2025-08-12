# HaasOnline Parameter Optimization Documentation

This directory contains comprehensive documentation for the HaasOnline Parameter Optimization system.

## 📚 Documentation Files

### [PARAMETER_OPTIMIZATION_ALGORITHM.md](PARAMETER_OPTIMIZATION_ALGORITHM.md)
**Complete technical documentation** of the parameter optimization algorithm including:
- Algorithm philosophy and core concepts
- Detailed parameter recognition system
- Strategic values and intelligent ranges for each parameter type
- Generic parameter handling for unknown parameters
- Implementation details and safety mechanisms
- Performance considerations and future enhancements

### [PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md](PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md)
**Quick reference guide** for developers including:
- Quick start examples
- Parameter recognition patterns table
- Common use cases and troubleshooting
- Performance guidelines and best practices

## 🎯 Algorithm Overview

The HaasOnline Parameter Optimization Algorithm uses a **Mixed Strategy** approach that combines:

1. **Strategic Values**: Proven parameter values from trading literature
2. **Intelligent Ranges**: Systematic exploration around optimal areas  
3. **Generic Fallback**: Current-value-centered ranges for unknown parameters

## 🚀 Quick Start

```python
from pyHaasAPI.optimization import optimize_lab_parameters_mixed

# Basic optimization
result = optimize_lab_parameters_mixed(executor, lab_id)

if result.success:
    print(f"✅ Optimized {result.optimized_parameters} parameters")
    print(f"🚀 Total combinations: {result.total_combinations:,}")
```

## 📊 Parameter Recognition Examples

| Parameter Type | Example Names | Generated Values |
|---------------|---------------|------------------|
| **RSI Length** | "RSI length", "rsi_period" | `[5, 9, 10, 12, 14, 16, 21, 25, 28, 31, 34]` |
| **Overbought** | "Overbought", "overbought_level" | `[20, 25, 30, 65, 70, 75, 80]` |
| **Oversold** | "Oversold", "oversold_threshold" | `[15, 20, 25, 30, 70, 75, 80]` |
| **Timeframes** | "Interval", "timeframe" | `[1, 2, 4, 5, 6, 15, 60]` |
| **Stop Loss** | "Stoploss", "stop_loss" | `[1, 2, 3, 5, 7, 9, 11, 13]` |
| **Generic** | "CustomParam", "MyFactor" | Current value ± intelligent range |

## 🔧 Key Benefits

- **Efficiency**: Finds optimal parameters faster than linear ranges
- **Domain Knowledge**: Incorporates trading expertise into optimization
- **Adaptability**: Handles both known and unknown parameter types
- **Safety**: Prevents combinatorial explosion with intelligent limits
- **Customization**: Supports custom ranges for specific parameters

## 📈 Performance Comparison

| Approach | Combinations | Coverage | Efficiency |
|----------|-------------|----------|------------|
| **Linear Ranges** | 3,000,000+ | Uniform | Low |
| **Mixed Strategy** | 150,000 | Intelligent | High |
| **Traditional** | 10,000 | Basic | Medium |

## 🛠️ Advanced Usage

```python
from pyHaasAPI.optimization import LabParameterOptimizer, OptimizationConfig, OptimizationStrategy

# Custom configuration
config = OptimizationConfig(
    strategy=OptimizationStrategy.MIXED,
    max_combinations=25000,
    custom_ranges={
        "MyCustomParameter": ["5", "10", "15", "20", "25"]
    }
)

optimizer = LabParameterOptimizer(executor)
result = optimizer.optimize_lab_parameters(lab_id, config)
```

## 📖 Further Reading

- **Algorithm Details**: See [PARAMETER_OPTIMIZATION_ALGORITHM.md](PARAMETER_OPTIMIZATION_ALGORITHM.md)
- **Quick Reference**: See [PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md](PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md)
- **Code Documentation**: See inline documentation in `pyHaasAPI/optimization.py`

## 🤝 Contributing

When contributing to the parameter optimization system:

1. **Add new parameter patterns** to the recognition system
2. **Update strategic values** based on research or community feedback
3. **Enhance documentation** with new examples and use cases
4. **Test thoroughly** with different parameter combinations

## 📝 Version History

- **v1.0.0**: Initial release with mixed strategy algorithm
- Strategic values for RSI, overbought/oversold, timeframes, stop loss
- Generic parameter handling for unknown parameters
- Safety mechanisms and performance optimizations

---

**Last Updated**: January 2025  
**Maintainers**: HaasAPI Development Team