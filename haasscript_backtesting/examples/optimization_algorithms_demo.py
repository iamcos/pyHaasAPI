#!/usr/bin/env python3
"""
Optimization Algorithms Integration Demo

This example demonstrates how to use the integrated optimization algorithms
with the HaasScript Backtesting System.
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from haasscript_backtesting.optimization_manager.optimization_manager import OptimizationManager
from haasscript_backtesting.models.optimization_models import (
    OptimizationAlgorithm, OptimizationConfig, ParameterRange
)
from haasscript_backtesting.models.backtest_models import BacktestConfig
from haasscript_backtesting.backtest_manager.backtest_manager import BacktestManager
from haasscript_backtesting.results_manager.results_manager import ResultsManager
from haasscript_backtesting.api_client.haasonline_client import HaasOnlineClient
from haasscript_backtesting.config.system_config import SystemConfig


def create_sample_optimization_config() -> OptimizationConfig:
    """Create a sample optimization configuration for demonstration."""
    
    # Create base backtest configuration
    base_config = BacktestConfig(
        script_id="sample_rsi_script",
        account_id="demo_account",
        market_tag="BINANCE_BTC_USDT",
        start_time=int((datetime.now() - timedelta(days=30)).timestamp()),
        end_time=int(datetime.now().timestamp()),
        interval=1,  # 1-minute intervals
        execution_amount=1000.0,
        leverage=1,
        position_mode=0,
        script_parameters={
            "rsi_length": 14,
            "overbought": 70,
            "oversold": 30,
            "stop_loss": 2.0
        }
    )
    
    # Define parameter ranges for optimization
    parameter_ranges = [
        ParameterRange(
            name="rsi_length",
            min_value=10,
            max_value=25,
            step=2,
            parameter_type=int
        ),
        ParameterRange(
            name="overbought",
            min_value=65,
            max_value=80,
            step=5,
            parameter_type=int
        ),
        ParameterRange(
            name="oversold",
            min_value=20,
            max_value=35,
            step=5,
            parameter_type=int
        ),
        ParameterRange(
            name="stop_loss",
            min_value=1.0,
            max_value=5.0,
            step=0.5,
            parameter_type=float
        )
    ]
    
    return OptimizationConfig(
        script_id="sample_rsi_script",
        base_backtest_config=base_config,
        parameter_ranges=parameter_ranges,
        optimization_metric="sharpe_ratio",
        max_evaluations=50,
        early_stopping=True,
        convergence_threshold=0.001
    )


def demonstrate_grid_search(optimization_manager: OptimizationManager, config: OptimizationConfig):
    """Demonstrate grid search optimization."""
    print("\n" + "="*60)
    print("GRID SEARCH OPTIMIZATION DEMO")
    print("="*60)
    
    try:
        # Execute grid search optimization
        print("Starting grid search optimization...")
        print(f"Parameter combinations to test: {len(config.parameter_ranges[0].generate_values()) * len(config.parameter_ranges[1].generate_values())}")
        
        # Note: In a real scenario, this would execute actual backtests
        # For demo purposes, we'll show the structure
        print("\nGrid search would systematically test all parameter combinations:")
        
        for rsi_length in config.parameter_ranges[0].generate_values()[:3]:  # Show first 3
            for overbought in config.parameter_ranges[1].generate_values()[:2]:  # Show first 2
                print(f"  - RSI Length: {rsi_length}, Overbought: {overbought}")
        
        print("  ... (and all other combinations)")
        
        # Simulate results
        print("\nGrid search optimization completed!")
        print("Best parameters found: {'rsi_length': 16, 'overbought': 75}")
        print("Best Sharpe ratio: 1.45")
        
    except Exception as e:
        print(f"Grid search demo error: {e}")


def demonstrate_bayesian_optimization(optimization_manager: OptimizationManager, config: OptimizationConfig):
    """Demonstrate Bayesian optimization."""
    print("\n" + "="*60)
    print("BAYESIAN OPTIMIZATION DEMO")
    print("="*60)
    
    try:
        print("Starting Bayesian optimization...")
        print("Using Gaussian Process to model objective function")
        print("Intelligently selecting next parameter combinations to test")
        
        # Simulate Bayesian optimization process
        print("\nBayesian optimization iterations:")
        iterations = [
            {"iter": 1, "params": {"rsi_length": 14, "overbought": 70}, "score": 1.2, "acquisition": "exploration"},
            {"iter": 2, "params": {"rsi_length": 18, "overbought": 75}, "score": 1.35, "acquisition": "exploitation"},
            {"iter": 3, "params": {"rsi_length": 12, "overbought": 65}, "score": 1.1, "acquisition": "exploration"},
            {"iter": 4, "params": {"rsi_length": 16, "overbought": 72}, "score": 1.42, "acquisition": "exploitation"},
        ]
        
        for iteration in iterations:
            print(f"  Iteration {iteration['iter']}: {iteration['params']} -> Score: {iteration['score']:.2f} ({iteration['acquisition']})")
        
        print("\nBayesian optimization completed!")
        print("Best parameters found: {'rsi_length': 16, 'overbought': 72}")
        print("Best Sharpe ratio: 1.42")
        print("Total evaluations: 25 (much fewer than grid search!)")
        
    except Exception as e:
        print(f"Bayesian optimization demo error: {e}")


def demonstrate_genetic_algorithm(optimization_manager: OptimizationManager, config: OptimizationConfig):
    """Demonstrate genetic algorithm optimization."""
    print("\n" + "="*60)
    print("GENETIC ALGORITHM OPTIMIZATION DEMO")
    print("="*60)
    
    try:
        print("Starting genetic algorithm optimization...")
        print("Population size: 20, Generations: 10")
        print("Using tournament selection, uniform crossover, and Gaussian mutation")
        
        # Simulate genetic algorithm process
        print("\nGenetic algorithm evolution:")
        generations = [
            {"gen": 0, "best_fitness": 1.1, "avg_fitness": 0.85, "diversity": 0.8},
            {"gen": 1, "best_fitness": 1.25, "avg_fitness": 0.95, "diversity": 0.75},
            {"gen": 2, "best_fitness": 1.32, "avg_fitness": 1.05, "diversity": 0.7},
            {"gen": 3, "best_fitness": 1.38, "avg_fitness": 1.15, "diversity": 0.65},
            {"gen": 4, "best_fitness": 1.41, "avg_fitness": 1.22, "diversity": 0.6},
        ]
        
        for gen in generations:
            print(f"  Generation {gen['gen']}: Best={gen['best_fitness']:.2f}, Avg={gen['avg_fitness']:.2f}, Diversity={gen['diversity']:.2f}")
        
        print("\nGenetic algorithm completed!")
        print("Best parameters found: {'rsi_length': 15, 'overbought': 73}")
        print("Best Sharpe ratio: 1.41")
        print("Population converged after 5 generations")
        
    except Exception as e:
        print(f"Genetic algorithm demo error: {e}")


def demonstrate_particle_swarm(optimization_manager: OptimizationManager, config: OptimizationConfig):
    """Demonstrate particle swarm optimization."""
    print("\n" + "="*60)
    print("PARTICLE SWARM OPTIMIZATION DEMO")
    print("="*60)
    
    try:
        print("Starting particle swarm optimization...")
        print("Swarm size: 15, Iterations: 20")
        print("Using inertia weight: 0.7, cognitive parameter: 1.5, social parameter: 1.5")
        
        # Simulate particle swarm process
        print("\nParticle swarm iterations:")
        iterations = [
            {"iter": 0, "global_best": 1.05, "avg_score": 0.82, "diversity": 0.9},
            {"iter": 5, "global_best": 1.28, "avg_score": 1.01, "diversity": 0.75},
            {"iter": 10, "global_best": 1.36, "avg_score": 1.18, "diversity": 0.6},
            {"iter": 15, "global_best": 1.39, "avg_score": 1.25, "diversity": 0.45},
            {"iter": 20, "global_best": 1.40, "avg_score": 1.28, "diversity": 0.3},
        ]
        
        for iteration in iterations:
            print(f"  Iteration {iteration['iter']}: Global Best={iteration['global_best']:.2f}, Avg={iteration['avg_score']:.2f}, Diversity={iteration['diversity']:.2f}")
        
        print("\nParticle swarm optimization completed!")
        print("Best parameters found: {'rsi_length': 17, 'overbought': 74}")
        print("Best Sharpe ratio: 1.40")
        print("Swarm converged with good exploration-exploitation balance")
        
    except Exception as e:
        print(f"Particle swarm demo error: {e}")


def demonstrate_result_ranking(optimization_manager: OptimizationManager):
    """Demonstrate result ranking functionality."""
    print("\n" + "="*60)
    print("RESULT RANKING DEMO")
    print("="*60)
    
    try:
        print("Ranking optimization results using multiple criteria...")
        
        # Simulate ranking criteria
        criteria = {
            'sharpe_ratio': 0.3,
            'total_return': 0.25,
            'max_drawdown': 0.2,  # Lower is better
            'win_rate': 0.15,
            'profit_factor': 0.1
        }
        
        print(f"Ranking criteria: {criteria}")
        
        # Simulate ranked results
        print("\nTop 5 ranked results:")
        ranked_results = [
            {"rank": 1, "params": {"rsi_length": 16, "overbought": 75}, "score": 0.85, "sharpe": 1.45},
            {"rank": 2, "params": {"rsi_length": 15, "overbought": 73}, "score": 0.82, "sharpe": 1.41},
            {"rank": 3, "params": {"rsi_length": 17, "overbought": 74}, "score": 0.80, "sharpe": 1.40},
            {"rank": 4, "params": {"rsi_length": 14, "overbought": 72}, "score": 0.78, "sharpe": 1.38},
            {"rank": 5, "params": {"rsi_length": 18, "overbought": 76}, "score": 0.75, "sharpe": 1.35},
        ]
        
        for result in ranked_results:
            print(f"  {result['rank']}. {result['params']} -> Composite Score: {result['score']:.2f}, Sharpe: {result['sharpe']:.2f}")
        
        print("\nResult ranking completed!")
        print("Multi-criteria ranking helps identify robust parameter combinations")
        
    except Exception as e:
        print(f"Result ranking demo error: {e}")


def main():
    """Main demonstration function."""
    print("HaasScript Backtesting System - Optimization Algorithms Demo")
    print("=" * 70)
    
    try:
        # Create sample configuration
        config = create_sample_optimization_config()
        print(f"Created optimization configuration for script: {config.script_id}")
        print(f"Parameter ranges: {len(config.parameter_ranges)} parameters")
        print(f"Optimization metric: {config.optimization_metric}")
        
        # Note: In a real scenario, you would initialize with actual managers
        # For demo purposes, we'll create mock managers
        print("\nInitializing optimization manager...")
        print("(Note: This demo shows the structure without executing actual backtests)")
        
        # Create mock managers for demonstration
        from unittest.mock import Mock
        mock_backtest_manager = Mock()
        mock_results_manager = Mock()
        
        optimization_manager = OptimizationManager(
            backtest_manager=mock_backtest_manager,
            results_manager=mock_results_manager,
            max_concurrent_executions=3
        )
        
        print(f"Optimization manager initialized with {len(optimization_manager.optimization_algorithms)} algorithms")
        
        # Demonstrate each optimization algorithm
        demonstrate_grid_search(optimization_manager, config)
        demonstrate_bayesian_optimization(optimization_manager, config)
        demonstrate_genetic_algorithm(optimization_manager, config)
        demonstrate_particle_swarm(optimization_manager, config)
        demonstrate_result_ranking(optimization_manager)
        
        print("\n" + "="*70)
        print("OPTIMIZATION ALGORITHMS COMPARISON")
        print("="*70)
        
        comparison = [
            {"Algorithm": "Grid Search", "Evaluations": "All combinations", "Best For": "Small parameter spaces", "Pros": "Exhaustive", "Cons": "Expensive"},
            {"Algorithm": "Random Search", "Evaluations": "User-defined", "Best For": "High-dimensional spaces", "Pros": "Simple, parallelizable", "Cons": "No learning"},
            {"Algorithm": "Bayesian", "Evaluations": "Adaptive", "Best For": "Expensive evaluations", "Pros": "Sample efficient", "Cons": "Complex setup"},
            {"Algorithm": "Genetic", "Evaluations": "Population-based", "Best For": "Complex landscapes", "Pros": "Global search", "Cons": "Many parameters"},
            {"Algorithm": "Particle Swarm", "Evaluations": "Swarm-based", "Best For": "Continuous spaces", "Pros": "Fast convergence", "Cons": "Local optima risk"},
        ]
        
        for alg in comparison:
            print(f"\n{alg['Algorithm']}:")
            print(f"  Evaluations: {alg['Evaluations']}")
            print(f"  Best for: {alg['Best For']}")
            print(f"  Pros: {alg['Pros']}")
            print(f"  Cons: {alg['Cons']}")
        
        print("\n" + "="*70)
        print("INTEGRATION WITH EXISTING FRAMEWORKS")
        print("="*70)
        
        print("\nThe optimization manager integrates with:")
        print("✓ PyHaasAPI optimization module for parameter range generation")
        print("✓ Existing parameter sweep engine for execution management")
        print("✓ Results manager for performance analysis")
        print("✓ Scikit-learn for advanced algorithms (when available)")
        print("✓ NumPy/SciPy for numerical computations")
        
        print("\nNext steps:")
        print("1. Configure your HaasOnline API credentials")
        print("2. Define your script and parameter ranges")
        print("3. Choose an optimization algorithm based on your needs")
        print("4. Execute optimization and analyze results")
        print("5. Deploy best parameters to live trading")
        
        print("\n🎉 Optimization algorithms integration demo completed successfully!")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()