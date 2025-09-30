# Comprehensive Backtesting Manager

A complete system for multi-lab backtesting with analysis between steps to identify top configurations.

## Overview

The Comprehensive Backtesting Manager is designed to handle complex backtesting workflows that involve:

1. **Multiple Labs** - Analyze multiple labs simultaneously
2. **Multiple Coins** - Test strategies across different cryptocurrencies
3. **Step-by-Step Analysis** - Analyze results between backtesting steps
4. **Parameter Optimization** - Extract and apply best parameters
5. **Progressive Refinement** - Use results from one step to improve the next

## Architecture

### Core Components

- **ComprehensiveBacktestingManager** - Main orchestrator
- **ProjectConfig** - Project configuration
- **BacktestStep** - Individual backtesting steps
- **LabConfig** - Lab configurations
- **CoinConfig** - Coin configurations
- **AnalysisResult** - Analysis results between steps

### Key Features

- **Multi-Lab Support** - Process multiple labs in parallel
- **Multi-Coin Support** - Test across different cryptocurrencies
- **Analysis Between Steps** - Identify top configurations
- **Parameter Optimization** - Extract and apply best parameters
- **Progress Monitoring** - Track backtest execution
- **Result Persistence** - Save results to JSON files
- **Comprehensive Reporting** - Detailed analysis and recommendations

## Usage

### Basic Usage

```python
from comprehensive_backtesting_manager import (
    ComprehensiveBacktestingManager,
    ProjectConfig,
    BacktestStep,
    LabConfig,
    CoinConfig
)

# Create project configuration
project_config = ProjectConfig(
    project_name="My Backtesting Project",
    description="Multi-lab backtesting project",
    steps=[
        BacktestStep(
            step_id="step1",
            name="Parameter Optimization",
            lab_configs=[
                LabConfig(
                    lab_id="your-lab-id",
                    lab_name="Source Lab",
                    script_id="script123",
                    market_tag="BTC_USDT_PERPETUAL"
                )
            ],
            coin_configs=[
                CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL"),
                CoinConfig(symbol="TRX", market_tag="TRX_USDT_PERPETUAL")
            ],
            analysis_criteria={
                'min_win_rate': 0.3,
                'min_trades': 5,
                'max_drawdown': 50.0,
                'min_roe': 10.0,
                'top_count': 10,
                'top_configs': 5
            },
            max_iterations=1000,
            cutoff_days=730
        )
    ],
    global_settings={
        'trade_amount': 2000.0,
        'leverage': 20.0,
        'position_mode': 1,
        'margin_mode': 0
    }
)

# Create and run manager
manager = ComprehensiveBacktestingManager(project_config)
await manager.initialize()
results = await manager.execute_project()
```

### CLI Usage

#### Create a Project

```bash
python comprehensive_backtesting_cli.py create-project \
    --name "My Project" \
    --description "Multi-lab backtesting" \
    --lab-ids "lab1,lab2,lab3" \
    --coins "BTC,TRX,ETH" \
    --min-win-rate 0.3 \
    --min-trades 5 \
    --max-drawdown 50.0 \
    --min-roe 10.0 \
    --max-iterations 1000 \
    --cutoff-days 730
```

#### Run a Project

```bash
python comprehensive_backtesting_cli.py run-project \
    --config-file "My Project_config.json"
```

#### Analyze Results

```bash
python comprehensive_backtesting_cli.py analyze-results \
    --results-file "My Project_results.json"
```

#### List Projects

```bash
python comprehensive_backtesting_cli.py list-projects
```

## Configuration

### ProjectConfig

- **project_name** - Name of the project
- **description** - Project description
- **steps** - List of BacktestStep objects
- **global_settings** - Global settings for all steps
- **output_directory** - Directory for results

### BacktestStep

- **step_id** - Unique identifier for the step
- **name** - Human-readable name
- **lab_configs** - List of LabConfig objects
- **coin_configs** - List of CoinConfig objects
- **analysis_criteria** - Criteria for analysis
- **max_iterations** - Maximum backtest iterations
- **cutoff_days** - Days of historical data
- **enabled** - Whether the step is enabled

### LabConfig

- **lab_id** - Lab identifier
- **lab_name** - Human-readable name
- **script_id** - Script identifier
- **market_tag** - Market tag
- **priority** - Priority level
- **enabled** - Whether the lab is enabled

### CoinConfig

- **symbol** - Coin symbol (e.g., "BTC")
- **market_tag** - Market tag (e.g., "BTC_USDT_PERPETUAL")
- **priority** - Priority level
- **enabled** - Whether the coin is enabled

### Analysis Criteria

- **min_win_rate** - Minimum win rate (0.0-1.0)
- **min_trades** - Minimum number of trades
- **max_drawdown** - Maximum drawdown percentage
- **min_roe** - Minimum Return on Equity percentage
- **top_count** - Number of top backtests to analyze
- **top_configs** - Number of top configurations to keep

## Workflow

### Step 1: Project Creation
1. Define project configuration
2. Specify labs and coins
3. Set analysis criteria
4. Configure global settings

### Step 2: Execution
1. Initialize manager
2. Connect to API
3. Execute each step
4. Analyze results between steps
5. Update next step configuration

### Step 3: Analysis
1. Collect all results
2. Perform final analysis
3. Generate recommendations
4. Save results to files

## Output Files

### Results File
- **{project_name}_results.json** - Complete project results
- Contains step results, analysis results, and final analysis

### Analysis File
- **{project_name}_analysis.json** - Analysis results between steps
- Contains top configurations and recommendations

### Configuration File
- **{project_name}_config.json** - Project configuration
- Can be used to recreate or modify the project

## Examples

### Simple Project

```python
# Create a simple project with one lab and two coins
project_config = ProjectConfig(
    project_name="Simple BTC/TRX Test",
    description="Simple backtesting test",
    steps=[
        BacktestStep(
            step_id="step1",
            name="Basic Optimization",
            lab_configs=[
                LabConfig(
                    lab_id="your-lab-id",
                    lab_name="Test Lab",
                    script_id="script123",
                    market_tag="BTC_USDT_PERPETUAL"
                )
            ],
            coin_configs=[
                CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL"),
                CoinConfig(symbol="TRX", market_tag="TRX_USDT_PERPETUAL")
            ],
            analysis_criteria={
                'min_win_rate': 0.3,
                'min_trades': 5,
                'max_drawdown': 50.0,
                'min_roe': 10.0,
                'top_count': 10,
                'top_configs': 5
            }
        )
    ]
)
```

### Multi-Step Project

```python
# Create a multi-step project with progressive refinement
project_config = ProjectConfig(
    project_name="Progressive Optimization",
    description="Multi-step optimization project",
    steps=[
        # Step 1: Initial optimization
        BacktestStep(
            step_id="step1",
            name="Initial Optimization",
            lab_configs=[...],
            coin_configs=[...],
            analysis_criteria={
                'min_win_rate': 0.3,
                'min_trades': 5,
                'max_drawdown': 50.0,
                'min_roe': 10.0,
                'top_count': 10,
                'top_configs': 5
            }
        ),
        # Step 2: Advanced optimization
        BacktestStep(
            step_id="step2",
            name="Advanced Optimization",
            lab_configs=[],  # Will be populated from step 1 results
            coin_configs=[...],
            analysis_criteria={
                'min_win_rate': 0.4,  # Higher standards
                'min_trades': 10,
                'max_drawdown': 30.0,
                'min_roe': 20.0,
                'top_count': 5,
                'top_configs': 3
            }
        )
    ]
)
```

## Error Handling

The system includes comprehensive error handling:

- **Connection Errors** - Handles API connection issues
- **Authentication Errors** - Handles authentication failures
- **Lab Errors** - Handles lab-specific errors
- **Backtest Errors** - Handles backtest execution errors
- **Analysis Errors** - Handles analysis failures

## Performance Considerations

- **Parallel Processing** - Labs are processed in parallel
- **Efficient Data Fetching** - Uses BacktestFetcher for efficient data retrieval
- **Progress Monitoring** - Tracks execution progress
- **Resource Management** - Proper cleanup of resources

## Troubleshooting

### Common Issues

1. **Authentication Errors** - Check credentials and server connectivity
2. **Lab Not Found** - Verify lab IDs are correct
3. **No Qualifying Backtests** - Adjust analysis criteria
4. **Memory Issues** - Reduce max_iterations or cutoff_days

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to the comprehensive backtesting manager:

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include detailed logging
4. Update documentation
5. Add tests for new features

## License

This project is part of pyHaasAPI and follows the same license terms.
