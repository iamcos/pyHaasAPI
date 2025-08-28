#!/usr/bin/env python3
"""
Parameter Optimization Interface Demo

Demonstrates the parameter optimization interface functionality.
"""

import asyncio
from textual.app import App

from mcp_tui_client.ui.optimization import (
    ParameterOptimizationInterface, 
    ParameterRange, 
    OptimizationConfig,
    OptimizationAlgorithm
)


class OptimizationDemoApp(App):
    """Demo app for parameter optimization interface"""
    
    def compose(self):
        # Create optimization interface with sample configuration
        optimization_interface = ParameterOptimizationInterface(lab_id="demo-lab")
        
        # Add some sample parameter ranges
        optimization_interface.config.parameter_ranges = [
            ParameterRange("stop_loss", 0.01, 0.10, 0.01, "float"),
            ParameterRange("take_profit", 0.02, 0.20, 0.01, "float"),
            ParameterRange("rsi_period", 10, 30, 1, "int"),
            ParameterRange("ma_type", choices=["SMA", "EMA", "WMA"], parameter_type="choice")
        ]
        
        optimization_interface.config.algorithm = OptimizationAlgorithm.GENETIC
        optimization_interface.config.max_iterations = 50
        optimization_interface.config.population_size = 20
        
        yield optimization_interface


def main():
    """Run the optimization demo"""
    app = OptimizationDemoApp()
    app.run()


if __name__ == "__main__":
    main()