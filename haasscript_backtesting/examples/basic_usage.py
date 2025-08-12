"""
Basic usage example of the HaasScript Backtesting System.

This example demonstrates how to:
1. Initialize the system with configuration
2. Load and debug a script
3. Execute a backtest
4. Process and analyze results
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from ..config import ConfigManager
from ..script_manager import ScriptManager
from ..backtest_manager import BacktestManager
from ..results_manager import ResultsManager
from ..models import BacktestConfig, PositionMode


def setup_logging():
    """Set up basic logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main example function demonstrating basic system usage."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting HaasScript Backtesting System example")
    
    try:
        # 1. Initialize configuration manager
        logger.info("Initializing configuration...")
        config_manager = ConfigManager()
        
        # Create sample configuration files if they don't exist
        config_manager.create_sample_configs()
        
        # 2. Initialize core managers
        logger.info("Initializing system managers...")
        script_manager = ScriptManager(config_manager)
        backtest_manager = BacktestManager(config_manager)
        results_manager = ResultsManager(config_manager)
        
        # 3. Load and debug a script
        logger.info("Loading and debugging script...")
        script_id = "sample_script_001"
        
        try:
            script = script_manager.load_script(script_id)
            logger.info(f"Loaded script: {script.name}")
            
            # Debug the script
            debug_result = script_manager.debug_script(script)
            if debug_result.success:
                logger.info("Script debug successful")
            else:
                logger.warning(f"Script debug found issues: {debug_result.errors}")
            
            # Validate the script
            validation_result = script_manager.validate_script(script)
            if validation_result.is_valid:
                logger.info("Script validation passed")
            else:
                logger.warning(f"Script validation issues: {validation_result.logic_errors}")
            
        except Exception as e:
            logger.error(f"Script operations failed: {e}")
            return
        
        # 4. Configure and execute a backtest
        logger.info("Configuring backtest...")
        
        # Create backtest configuration
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        backtest_config = BacktestConfig(
            script_id=script_id,
            account_id="demo_account",
            market_tag="EXAMPLE_MARKET",
            start_time=int(start_time.timestamp()),
            end_time=int(end_time.timestamp()),
            interval=60,  # 1-hour candles
            execution_amount=1000.0,
            script_parameters={
                "threshold_high": 100.0,
                "threshold_low": 110.0,
                "stop_value": 95.0
            },
            position_mode=PositionMode.LONG_ONLY
        )
        
        # Execute the backtest
        logger.info("Starting backtest execution...")
        try:
            execution = backtest_manager.execute_backtest(backtest_config)
            logger.info(f"Backtest started with ID: {execution.backtest_id}")
            
            # Monitor execution (simplified for example)
            import time
            while execution.status.is_running:
                status = backtest_manager.monitor_execution(execution.backtest_id)
                logger.info(f"Backtest progress: {status.progress_percentage:.1f}% - {status.current_phase}")
                time.sleep(2)  # Wait 2 seconds before checking again
                
                # Break after a few iterations for demo purposes
                if status.progress_percentage > 50:
                    break
            
            logger.info("Backtest execution completed")
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            return
        
        # 5. Process and analyze results
        logger.info("Processing backtest results...")
        try:
            results = results_manager.process_results(execution.backtest_id)
            
            # Display key metrics
            logger.info("=== Backtest Results ===")
            logger.info(f"Total Return: {results.execution_metrics.total_return:.2f}%")
            logger.info(f"Sharpe Ratio: {results.execution_metrics.sharpe_ratio:.2f}")
            logger.info(f"Max Drawdown: {results.execution_metrics.max_drawdown:.2f}%")
            logger.info(f"Total Trades: {len(results.trade_history)}")
            logger.info(f"Win Rate: {results.performance_data.win_rate:.1f}%")
            logger.info(f"Profit Factor: {results.execution_metrics.profit_factor:.2f}")
            
            # Export results
            logger.info("Exporting results...")
            json_export = results_manager.export_results(results, 'json')
            csv_export = results_manager.export_results(results, 'csv')
            
            # Save exports to files
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            with open(results_dir / f"{execution.backtest_id}_results.json", 'wb') as f:
                f.write(json_export)
            
            with open(results_dir / f"{execution.backtest_id}_trades.csv", 'wb') as f:
                f.write(csv_export)
            
            logger.info(f"Results exported to {results_dir}")
            
        except Exception as e:
            logger.error(f"Results processing failed: {e}")
            return
        
        # 6. Demonstrate additional features
        logger.info("Demonstrating additional features...")
        
        # Get script capabilities
        capabilities = script_manager.get_script_capabilities()
        logger.info(f"Available functions: {len(capabilities.available_functions)}")
        logger.info(f"Available indicators: {len(capabilities.available_indicators)}")
        
        # Get execution history
        history = backtest_manager.get_execution_history(limit=5)
        logger.info(f"Recent executions: {len(history)}")
        
        # Get active executions
        active = backtest_manager.get_active_executions()
        logger.info(f"Active executions: {len(active)}")
        
        logger.info("Example completed successfully!")
        
    except Exception as e:
        logger.error(f"Example failed with error: {e}")
        raise


if __name__ == "__main__":
    main()