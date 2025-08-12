# Miguel Workflow Final - Clean Implementation

A refactored, streamlined implementation of the 2-stage trading bot optimization workflow. This clean version combines the best components from previous iterations into a maintainable, single-lab focused system.

## Overview

The workflow implements a systematic 2-stage optimization approach:

1. **Stage 0**: Timeframe exploration (100 backtests) with default numerical parameters
2. **Stage 0 Analysis**: Identify top 3 timeframe combinations based on performance and diversity
3. **Stage 1**: Numerical parameter optimization (3 labs × 1000 backtests each) with fixed timeframes

**Total**: 3,100 backtests across both stages

## Architecture

```
Stage 0: Timeframe Explorer
    ↓ (100 backtests, 2 years)
Stage 0: Analyzer  
    ↓ (identifies top 3 timeframe combinations)
Stage 1: Numerical Optimizer
    ↓ (3 labs × 1000 backtests each, 3 years)
Complete Workflow Orchestrator
```

## Files Structure

```
miguel_workflow_final/
├── README.md                    # This file
├── config.py                    # Centralized configuration
├── stage0_timeframe_explorer.py # Stage 0: Timeframe exploration
├── stage0_analyzer.py          # Stage 0: Results analysis  
├── stage1_numerical_optimizer.py # Stage 1: Numerical optimization
└── complete_workflow.py        # Complete workflow orchestrator
```

## Key Features

### ✅ Clean & Refactored
- Removed duplicate code and clutter
- Centralized configuration
- Clear separation of concerns
- Consistent error handling

### ✅ Single Lab Focus
- No multi-coin distribution
- Focus on one trading pair at a time
- Simplified lab management
- Clear workflow progression

### ✅ Intelligent Parameter Classification
- Automatic parameter detection and classification
- Timeframe vs structural vs numerical parameters
- Dynamic parameter range generation
- Trading indicator specific optimizations

### ✅ Standardized Naming
- Consistent lab naming convention
- Version tracking and identification
- Clear stage and purpose indication

### ✅ Comprehensive Analysis
- Performance-based ranking
- Diversity scoring for timeframe combinations
- Statistical analysis of results
- Detailed reporting and insights

## Usage

### 1. Complete Workflow (Recommended)

Run the entire 2-stage workflow:

```bash
python complete_workflow.py
```

This will:
- Create Stage 0 timeframe exploration lab
- Wait for completion (or use mock data for demo)
- Analyze Stage 0 results
- Create 3 Stage 1 numerical optimization labs

### 2. Individual Stages

Run stages individually for more control:

#### Stage 0: Timeframe Exploration
```bash
python stage0_timeframe_explorer.py
```

#### Stage 0: Analysis (after Stage 0 completes)
```bash
python stage0_analyzer.py
```

#### Stage 1: Numerical Optimization
```bash
python stage1_numerical_optimizer.py
```

### 3. Configuration

Modify `config.py` to adjust:
- Target backtests per stage
- Backtest periods
- Genetic algorithm settings
- Parameter classification rules
- Default parameter ranges

## Configuration

### Workflow Settings
```python
# Stage 0
stage0_target_backtests = 100
stage0_backtest_years = 2
stage0_focus = "timeframes_and_ma_types"

# Stage 1  
stage1_target_backtests = 1000
stage1_backtest_years = 3
stage1_focus = "numerical_parameters"
stage1_top_combinations = 3

# Genetic Algorithm
genetic_max_generations = 20
genetic_max_population = 50
genetic_max_elites = 3
genetic_mix_rate = 30.0
genetic_adjust_rate = 25.0
```

### Lab Naming Convention
```
Stage 0: "0 - {script_name} - {period} years {coin} (timeframe_exploration) - after: initial exploration"
Stage 1: "1 - {script_name} - {period} years {coin} ({timeframes}) - after: numerical_optim_rank{rank}"
```

## Parameter Classification

The system automatically classifies parameters into three categories:

### Timeframe Parameters (Fixed in Stage 1)
- Low TF, High TF
- Timeframe, Interval
- Any parameter containing "tf" or "timeframe"

### Structural Parameters (Fixed in Stage 1)  
- MA type, Indicator type
- Signal type, Mode
- Non-numerical configuration parameters

### Numerical Parameters (Optimized in Stage 1)
- ADX, Stochastic, DEMA, RSI, BB, ATR
- Stop Loss (SL), Take Profit (TP)
- Periods, triggers, thresholds
- Risk management parameters

## Parameter Range Generation

The system generates intelligent parameter ranges based on:

### Indicator-Specific Ranges
- **ADX Trigger**: 15-35 (step: 2)
- **Stoch Oversold**: 10-30 (step: 5)  
- **Stoch Overbought**: 70-90 (step: 5)
- **DEMA Fast**: 5-20 (step: 2)
- **DEMA Slow**: 20-50 (step: 5)

### Dynamic Ranges
- Small percentages: 0.5x to 2x current value
- Large percentages: 0.7x to 1.5x current value
- Cooldown periods: 0.5x to 2x current value
- General numerical: Context-appropriate ranges

## Output Files

The workflow generates several output files:

### Stage 0
- `stage0_timeframe_exploration_results.json` - Stage 0 lab creation results
- `stage0_analysis_results.json` - Stage 0 analysis and top combinations

### Stage 1  
- `stage1_numerical_optimization_results.json` - Stage 1 lab creation results

### Complete Workflow
- `complete_workflow_results.json` - Comprehensive workflow results

## Example Output

### Stage 0 Analysis
```
🏆 TOP 3 TIMEFRAME COMBINATIONS:

🥇 RANK #1 - 5min/1h
   Low TF: 5 Minutes
   High TF: 1 Hour  
   Avg ROI: 15.2%
   Max ROI: 45.8%
   Profitable Ratio: 65.0%
   Composite Score: 28.5

🥇 RANK #2 - 10min/4h
   Low TF: 10 Minutes
   High TF: 4 Hours
   Avg ROI: 12.8%
   Max ROI: 38.4%
   Profitable Ratio: 58.0%
   Composite Score: 24.2
```

### Stage 1 Labs Created
```
🧬 1 - ADX BB STOCH Scalper - 3 years ETH (5min/1h) - after: numerical_optim_rank1
   Lab ID: abc123-def456-ghi789
   Timeframes: 5 Minutes / 1 Hour (FIXED)
   Target Backtests: 1,000
   Baseline Avg ROI: 15.2%

🧬 1 - ADX BB STOCH Scalper - 3 years ETH (10min/4h) - after: numerical_optim_rank2  
   Lab ID: def456-ghi789-jkl012
   Timeframes: 10 Minutes / 4 Hours (FIXED)
   Target Backtests: 1,000
   Baseline Avg ROI: 12.8%
```

## Requirements

- Python 3.8+
- `requests` library
- `numpy` library (for analysis)
- Access to MCP server (default: http://localhost:8000)
- HaasOnline trading platform with lab access

## Error Handling

The system includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **Lab Creation Failures**: Detailed error reporting and continuation
- **Analysis Failures**: Graceful degradation with partial results
- **Parameter Extraction Issues**: Fallback to default ranges

## Best Practices

### Before Running
1. Ensure MCP server is running and accessible
2. Verify source lab ID exists and is accessible
3. Check account permissions for lab creation
4. Review configuration settings in `config.py`

### During Execution
1. Monitor lab creation progress in logs
2. Check for error messages and warnings
3. Verify lab names follow naming convention
4. Confirm backtests start successfully

### After Completion
1. Review generated JSON result files
2. Monitor backtest progress in HaasOnline interface
3. Analyze results when backtests complete
4. Select top configurations for live trading

## Troubleshooting

### Common Issues

**Connection Refused**
- Check MCP server is running on correct port
- Verify network connectivity
- Check firewall settings

**Lab Creation Failed**
- Verify source lab ID exists
- Check account permissions
- Ensure sufficient system resources

**Parameter Classification Issues**
- Review parameter names in source lab
- Adjust classification keywords in config.py
- Check for non-standard parameter formats

**Analysis Failures**
- Ensure Stage 0 backtest completed successfully
- Check for sufficient result data
- Verify JSON result file format

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to this codebase:

1. Follow the established naming conventions
2. Add comprehensive error handling
3. Update configuration options in `config.py`
4. Include detailed docstrings and comments
5. Test with various lab configurations
6. Update this README with new features

## License

This project is part of the pyHaasAPI trading bot automation system.