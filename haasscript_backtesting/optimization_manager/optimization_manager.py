"""
Main optimization manager for coordinating parameter optimization and sweep operations.

This module integrates with existing optimization frameworks from the project
to provide advanced optimization algorithms including genetic algorithms,
Bayesian optimization, and grid search.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass

from .parameter_sweep_engine import ParameterSweepEngine
from ..models.optimization_models import (
    SweepConfig, SweepExecution, OptimizationResults, RankedResults,
    OptimizationAlgorithm, OptimizationConfig
)
from ..backtest_manager.backtest_manager import BacktestManager
from ..results_manager.results_manager import ResultsManager

# Import existing optimization framework
try:
    from pyHaasAPI.optimization import (
        OptimizationStrategy, ParameterRangeGenerator, 
        LabParameterOptimizer, OptimizationConfig as PyHaasOptimizationConfig
    )
    PYHAAS_OPTIMIZATION_AVAILABLE = True
except ImportError:
    PYHAAS_OPTIMIZATION_AVAILABLE = False
    logging.warning("PyHaasAPI optimization module not available")


logger = logging.getLogger(__name__)


class OptimizationManager:
    """
    Main manager for parameter optimization and sweep operations.
    
    Coordinates between parameter sweep engine, optimization algorithms,
    and concurrent execution management. Integrates with existing optimization
    frameworks for advanced algorithm support.
    """
    
    def __init__(
        self,
        backtest_manager: BacktestManager,
        results_manager: ResultsManager,
        max_concurrent_executions: int = 5
    ):
        """
        Initialize the optimization manager.
        
        Args:
            backtest_manager: Manager for backtest execution
            results_manager: Manager for result processing
            max_concurrent_executions: Maximum concurrent executions
        """
        self.backtest_manager = backtest_manager
        self.results_manager = results_manager
        self.max_concurrent_executions = max_concurrent_executions
        
        # Initialize parameter sweep engine
        self.sweep_engine = ParameterSweepEngine(
            backtest_manager=backtest_manager,
            results_manager=results_manager,
            max_concurrent_executions=max_concurrent_executions
        )
        
        # Initialize optimization algorithms
        self.optimization_algorithms = {
            OptimizationAlgorithm.GRID_SEARCH: self._grid_search_optimization,
            OptimizationAlgorithm.RANDOM_SEARCH: self._random_search_optimization,
            OptimizationAlgorithm.BAYESIAN: self._bayesian_optimization,
            OptimizationAlgorithm.GENETIC: self._genetic_algorithm_optimization,
            OptimizationAlgorithm.PARTICLE_SWARM: self._particle_swarm_optimization
        }
        
        # Optimization history for convergence analysis
        self.optimization_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_parameter_sweep(self, config: SweepConfig) -> SweepExecution:
        """
        Create a new parameter sweep.
        
        Args:
            config: Sweep configuration
            
        Returns:
            Sweep execution object
        """
        return self.sweep_engine.create_sweep(config)
    
    def execute_optimization(self, algorithm: OptimizationAlgorithm, config: OptimizationConfig) -> OptimizationResults:
        """
        Execute optimization using the specified algorithm.
        
        Args:
            algorithm: Optimization algorithm to use
            config: Optimization configuration
            
        Returns:
            Optimization results
        """
        logger.info(f"Starting {algorithm.value} optimization")
        
        # Get the optimization function
        optimization_func = self.optimization_algorithms.get(algorithm)
        if not optimization_func:
            raise ValueError(f"Unsupported optimization algorithm: {algorithm}")
        
        # Initialize optimization history
        optimization_id = f"{algorithm.value}_{config.script_id}_{len(self.optimization_history)}"
        self.optimization_history[optimization_id] = []
        
        try:
            # Execute the optimization algorithm
            results = optimization_func(config, optimization_id)
            
            logger.info(f"Completed {algorithm.value} optimization with {results.total_evaluations} evaluations")
            return results
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise
    
    def get_sweep_status(self, sweep_id: str) -> Optional[SweepExecution]:
        """
        Get status of a parameter sweep.
        
        Args:
            sweep_id: ID of the sweep
            
        Returns:
            Sweep execution status
        """
        return self.sweep_engine.get_sweep_status(sweep_id)
    
    def cancel_sweep(self, sweep_id: str) -> bool:
        """
        Cancel a running parameter sweep.
        
        Args:
            sweep_id: ID of the sweep to cancel
            
        Returns:
            True if successfully cancelled
        """
        return self.sweep_engine.cancel_sweep(sweep_id)
    
    def rank_results(self, results: List[Any], criteria: Dict[str, float] = None) -> RankedResults:
        """
        Rank optimization results using multiple criteria.
        
        Args:
            results: List of processed results to rank
            criteria: Weighting criteria for ranking (default: equal weights)
            
        Returns:
            Ranked results with scores
        """
        if not criteria:
            criteria = {
                'sharpe_ratio': 0.3,
                'total_return': 0.25,
                'max_drawdown': 0.2,  # Lower is better, will be inverted
                'win_rate': 0.15,
                'profit_factor': 0.1
            }
        
        ranked_items = []
        
        for result in results:
            if not hasattr(result, 'execution_metrics'):
                continue
                
            metrics = result.execution_metrics
            score = 0.0
            
            # Calculate weighted score
            for metric, weight in criteria.items():
                if hasattr(metrics, metric):
                    value = getattr(metrics, metric)
                    
                    # Invert metrics where lower is better
                    if metric in ['max_drawdown', 'volatility']:
                        # Use reciprocal for drawdown (avoid division by zero)
                        normalized_value = 1.0 / (1.0 + abs(value)) if value != 0 else 1.0
                    else:
                        normalized_value = max(0, value)  # Ensure non-negative
                    
                    score += normalized_value * weight
            
            ranked_items.append({
                'result': result,
                'score': score,
                'metrics': {
                    metric: getattr(metrics, metric, 0) 
                    for metric in criteria.keys() 
                    if hasattr(metrics, metric)
                }
            })
        
        # Sort by score (highest first)
        ranked_items.sort(key=lambda x: x['score'], reverse=True)
        
        return RankedResults(
            ranked_results=ranked_items,
            ranking_criteria=criteria,
            total_results=len(ranked_items)
        )
    
    # Optimization Algorithm Implementations
    
    def _grid_search_optimization(self, config: OptimizationConfig, optimization_id: str) -> OptimizationResults:
        """
        Execute grid search optimization.
        
        Systematically tests all parameter combinations in the defined ranges.
        """
        logger.info("Executing grid search optimization")
        
        # Create sweep configuration for grid search
        sweep_config = SweepConfig(
            name=f"grid_search_{config.script_id}_{optimization_id}",
            base_config=config.base_backtest_config,
            parameter_ranges=config.parameter_ranges,
            optimization_metric=config.optimization_metric,
            max_concurrent_executions=self.max_concurrent_executions,
            early_stopping=False  # Grid search tests all combinations
        )
        
        # Execute sweep
        sweep_execution = self.sweep_engine.create_sweep(sweep_config)
        completed_sweep = self.sweep_engine.execute_sweep(sweep_execution)
        
        # Convert to optimization results
        return self._convert_sweep_to_optimization_results(
            completed_sweep, OptimizationAlgorithm.GRID_SEARCH, optimization_id
        )
    
    def _random_search_optimization(self, config: OptimizationConfig, optimization_id: str) -> OptimizationResults:
        """
        Execute random search optimization.
        
        Randomly samples parameter combinations within the defined ranges.
        """
        logger.info("Executing random search optimization")
        
        # Generate random parameter combinations
        random_combinations = self._generate_random_combinations(
            config.parameter_ranges, 
            config.max_evaluations or 100
        )
        
        # Create parameter ranges from random combinations
        random_ranges = self._combinations_to_ranges(random_combinations)
        
        # Create sweep configuration
        sweep_config = SweepConfig(
            name=f"random_search_{config.script_id}_{optimization_id}",
            base_config=config.base_backtest_config,
            parameter_ranges=random_ranges,
            optimization_metric=config.optimization_metric,
            max_concurrent_executions=self.max_concurrent_executions,
            early_stopping=config.early_stopping
        )
        
        # Execute sweep
        sweep_execution = self.sweep_engine.create_sweep(sweep_config)
        completed_sweep = self.sweep_engine.execute_sweep(sweep_execution)
        
        return self._convert_sweep_to_optimization_results(
            completed_sweep, OptimizationAlgorithm.RANDOM_SEARCH, optimization_id
        )
    
    def _bayesian_optimization(self, config: OptimizationConfig, optimization_id: str) -> OptimizationResults:
        """
        Execute Bayesian optimization.
        
        Uses Gaussian Process to model the objective function and select
        promising parameter combinations.
        """
        logger.info("Executing Bayesian optimization")
        
        try:
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import Matern
            from scipy.optimize import minimize
        except ImportError:
            logger.warning("Scikit-learn not available, falling back to random search")
            return self._random_search_optimization(config, optimization_id)
        
        # Initialize with random samples
        n_initial = min(10, config.max_evaluations // 4)
        initial_combinations = self._generate_random_combinations(
            config.parameter_ranges, n_initial
        )
        
        # Evaluate initial samples
        X_evaluated = []
        y_evaluated = []
        
        for combination in initial_combinations:
            result = self._evaluate_parameter_combination(config, combination)
            if result:
                X_evaluated.append(list(combination.values()))
                y_evaluated.append(self._extract_metric_value(result, config.optimization_metric))
        
        # Bayesian optimization loop
        gp = GaussianProcessRegressor(kernel=Matern(length_scale=1.0, nu=2.5))
        
        for iteration in range(len(X_evaluated), config.max_evaluations or 50):
            if len(X_evaluated) < 2:
                # Need more samples for GP
                combination = self._generate_random_combinations(config.parameter_ranges, 1)[0]
            else:
                # Fit GP and find next point
                gp.fit(X_evaluated, y_evaluated)
                next_point = self._acquisition_function_optimization(gp, config.parameter_ranges)
                combination = self._point_to_combination(next_point, config.parameter_ranges)
            
            # Evaluate the combination
            result = self._evaluate_parameter_combination(config, combination)
            if result:
                X_evaluated.append(list(combination.values()))
                y_evaluated.append(self._extract_metric_value(result, config.optimization_metric))
                
                # Track optimization history
                self.optimization_history[optimization_id].append({
                    'iteration': iteration,
                    'parameters': combination,
                    'score': y_evaluated[-1],
                    'best_score_so_far': max(y_evaluated)
                })
        
        # Find best result
        best_idx = np.argmax(y_evaluated)
        best_combination = self._point_to_combination(X_evaluated[best_idx], config.parameter_ranges)
        
        return OptimizationResults(
            algorithm=OptimizationAlgorithm.BAYESIAN,
            best_parameters=best_combination,
            best_score=y_evaluated[best_idx],
            optimization_history=self.optimization_history[optimization_id],
            convergence_data=y_evaluated,
            total_evaluations=len(y_evaluated),
            execution_time=0.0  # Would need to track actual time
        )
    
    def _genetic_algorithm_optimization(self, config: OptimizationConfig, optimization_id: str) -> OptimizationResults:
        """
        Execute genetic algorithm optimization.
        
        Evolves parameter combinations using selection, crossover, and mutation.
        """
        logger.info("Executing genetic algorithm optimization")
        
        population_size = min(20, config.max_evaluations // 5)
        generations = config.max_evaluations // population_size
        
        # Initialize population
        population = self._generate_random_combinations(config.parameter_ranges, population_size)
        fitness_scores = []
        
        # Evaluate initial population
        for individual in population:
            result = self._evaluate_parameter_combination(config, individual)
            if result:
                fitness_scores.append(self._extract_metric_value(result, config.optimization_metric))
            else:
                fitness_scores.append(0.0)
        
        best_individual = None
        best_fitness = float('-inf')
        
        # Evolution loop
        for generation in range(generations):
            # Selection (tournament selection)
            new_population = []
            for _ in range(population_size):
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # Crossover
                child = self._crossover(parent1, parent2, config.parameter_ranges)
                
                # Mutation
                child = self._mutate(child, config.parameter_ranges, mutation_rate=0.1)
                
                new_population.append(child)
            
            # Evaluate new population
            new_fitness_scores = []
            for individual in new_population:
                result = self._evaluate_parameter_combination(config, individual)
                if result:
                    fitness = self._extract_metric_value(result, config.optimization_metric)
                    new_fitness_scores.append(fitness)
                    
                    # Track best individual
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_individual = individual.copy()
                else:
                    new_fitness_scores.append(0.0)
            
            population = new_population
            fitness_scores = new_fitness_scores
            
            # Track optimization history
            self.optimization_history[optimization_id].append({
                'generation': generation,
                'best_fitness': best_fitness,
                'avg_fitness': np.mean(fitness_scores),
                'population_diversity': self._calculate_population_diversity(population)
            })
        
        return OptimizationResults(
            algorithm=OptimizationAlgorithm.GENETIC,
            best_parameters=best_individual or {},
            best_score=best_fitness,
            optimization_history=self.optimization_history[optimization_id],
            convergence_data=[h['best_fitness'] for h in self.optimization_history[optimization_id]],
            total_evaluations=population_size * (generations + 1),
            execution_time=0.0
        )
    
    def _particle_swarm_optimization(self, config: OptimizationConfig, optimization_id: str) -> OptimizationResults:
        """
        Execute particle swarm optimization.
        
        Uses swarm intelligence to find optimal parameter combinations.
        """
        logger.info("Executing particle swarm optimization")
        
        swarm_size = min(15, config.max_evaluations // 10)
        iterations = config.max_evaluations // swarm_size
        
        # Initialize swarm
        particles = self._generate_random_combinations(config.parameter_ranges, swarm_size)
        velocities = [{param: 0.0 for param in particles[0].keys()} for _ in range(swarm_size)]
        
        # Personal and global bests
        personal_bests = [p.copy() for p in particles]
        personal_best_scores = []
        
        # Evaluate initial positions
        for particle in particles:
            result = self._evaluate_parameter_combination(config, particle)
            if result:
                personal_best_scores.append(self._extract_metric_value(result, config.optimization_metric))
            else:
                personal_best_scores.append(0.0)
        
        # Find global best
        global_best_idx = np.argmax(personal_best_scores)
        global_best = personal_bests[global_best_idx].copy()
        global_best_score = personal_best_scores[global_best_idx]
        
        # PSO parameters
        w = 0.7  # Inertia weight
        c1 = 1.5  # Cognitive parameter
        c2 = 1.5  # Social parameter
        
        # PSO loop
        for iteration in range(iterations):
            for i, particle in enumerate(particles):
                # Update velocity and position
                for param in particle.keys():
                    r1, r2 = np.random.random(), np.random.random()
                    
                    velocities[i][param] = (
                        w * velocities[i][param] +
                        c1 * r1 * (personal_bests[i][param] - particle[param]) +
                        c2 * r2 * (global_best[param] - particle[param])
                    )
                    
                    particle[param] += velocities[i][param]
                    
                    # Clamp to parameter bounds
                    param_range = next(pr for pr in config.parameter_ranges if pr.name == param)
                    particle[param] = max(param_range.min_value, 
                                        min(param_range.max_value, particle[param]))
                
                # Evaluate new position
                result = self._evaluate_parameter_combination(config, particle)
                if result:
                    fitness = self._extract_metric_value(result, config.optimization_metric)
                    
                    # Update personal best
                    if fitness > personal_best_scores[i]:
                        personal_best_scores[i] = fitness
                        personal_bests[i] = particle.copy()
                        
                        # Update global best
                        if fitness > global_best_score:
                            global_best_score = fitness
                            global_best = particle.copy()
            
            # Track optimization history
            self.optimization_history[optimization_id].append({
                'iteration': iteration,
                'global_best_score': global_best_score,
                'avg_score': np.mean(personal_best_scores),
                'swarm_diversity': self._calculate_swarm_diversity(particles)
            })
        
        return OptimizationResults(
            algorithm=OptimizationAlgorithm.PARTICLE_SWARM,
            best_parameters=global_best,
            best_score=global_best_score,
            optimization_history=self.optimization_history[optimization_id],
            convergence_data=[h['global_best_score'] for h in self.optimization_history[optimization_id]],
            total_evaluations=swarm_size * (iterations + 1),
            execution_time=0.0
        )
    
    # Helper Methods for Optimization Algorithms
    
    def _convert_sweep_to_optimization_results(
        self, 
        sweep: SweepExecution, 
        algorithm: OptimizationAlgorithm,
        optimization_id: str
    ) -> OptimizationResults:
        """Convert sweep execution results to optimization results format."""
        return OptimizationResults(
            algorithm=algorithm,
            best_parameters=sweep.best_parameters or {},
            best_score=getattr(
                sweep.best_result.execution_metrics,
                sweep.config.optimization_metric
            ) if sweep.best_result else 0.0,
            optimization_history=self.optimization_history.get(optimization_id, []),
            convergence_data=[],
            total_evaluations=sweep.completed_backtests,
            execution_time=(
                sweep.completed_at - sweep.started_at
            ).total_seconds() if sweep.completed_at else 0.0
        )
    
    def _generate_random_combinations(
        self, 
        parameter_ranges: List[Any], 
        count: int
    ) -> List[Dict[str, float]]:
        """Generate random parameter combinations within ranges."""
        combinations = []
        
        for _ in range(count):
            combination = {}
            for param_range in parameter_ranges:
                # Generate random value within range
                random_value = np.random.uniform(
                    param_range.min_value, 
                    param_range.max_value
                )
                
                # Apply step size if specified
                if hasattr(param_range, 'step') and param_range.step > 0:
                    steps = int((random_value - param_range.min_value) / param_range.step)
                    random_value = param_range.min_value + steps * param_range.step
                
                combination[param_range.name] = random_value
            
            combinations.append(combination)
        
        return combinations
    
    def _combinations_to_ranges(self, combinations: List[Dict[str, float]]) -> List[Any]:
        """Convert parameter combinations back to parameter ranges."""
        # This is a simplified implementation
        # In practice, you'd need to create proper ParameterRange objects
        ranges = []
        if combinations:
            for param_name in combinations[0].keys():
                values = [combo[param_name] for combo in combinations]
                # Create a mock range object
                from types import SimpleNamespace
                param_range = SimpleNamespace()
                param_range.name = param_name
                param_range.min_value = min(values)
                param_range.max_value = max(values)
                param_range.step = 1.0
                param_range.generate_values = lambda: values
                param_range.total_combinations = len(set(values))
                ranges.append(param_range)
        
        return ranges
    
    def _evaluate_parameter_combination(
        self, 
        config: OptimizationConfig, 
        combination: Dict[str, float]
    ) -> Optional[Any]:
        """Evaluate a single parameter combination by running a backtest."""
        try:
            # Create backtest config with parameter combination
            backtest_config = config.base_backtest_config
            backtest_config.script_parameters.update(combination)
            
            # Execute backtest
            backtest_execution = self.backtest_manager.execute_backtest(backtest_config)
            
            # Wait for completion (simplified)
            while not backtest_execution.status.is_complete:
                backtest_execution = self.backtest_manager.monitor_execution(
                    backtest_execution.backtest_id
                )
                import time
                time.sleep(1)
            
            # Process results
            if backtest_execution.status.is_complete:
                return self.results_manager.process_results(backtest_execution.backtest_id)
            
        except Exception as e:
            logger.error(f"Error evaluating parameter combination: {e}")
        
        return None
    
    def _extract_metric_value(self, result: Any, metric_name: str) -> float:
        """Extract metric value from processed results."""
        if hasattr(result, 'execution_metrics'):
            return getattr(result.execution_metrics, metric_name, 0.0)
        return 0.0
    
    def _point_to_combination(
        self, 
        point: List[float], 
        parameter_ranges: List[Any]
    ) -> Dict[str, float]:
        """Convert optimization point back to parameter combination."""
        combination = {}
        for i, param_range in enumerate(parameter_ranges):
            if i < len(point):
                combination[param_range.name] = point[i]
        return combination
    
    def _acquisition_function_optimization(self, gp, parameter_ranges: List[Any]) -> List[float]:
        """Optimize acquisition function for Bayesian optimization."""
        # Simplified Expected Improvement acquisition function
        def expected_improvement(x):
            mu, sigma = gp.predict([x], return_std=True)
            # Simple EI calculation (would need current best for proper EI)
            return mu[0] + sigma[0]
        
        # Random search for acquisition function maximum (simplified)
        best_x = None
        best_ei = float('-inf')
        
        for _ in range(100):  # Random search iterations
            x = [
                np.random.uniform(pr.min_value, pr.max_value) 
                for pr in parameter_ranges
            ]
            ei = expected_improvement(x)
            if ei > best_ei:
                best_ei = ei
                best_x = x
        
        return best_x or [pr.min_value for pr in parameter_ranges]
    
    def _tournament_selection(
        self, 
        population: List[Dict[str, float]], 
        fitness_scores: List[float],
        tournament_size: int = 3
    ) -> Dict[str, float]:
        """Tournament selection for genetic algorithm."""
        tournament_indices = np.random.choice(
            len(population), 
            size=min(tournament_size, len(population)), 
            replace=False
        )
        
        best_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
        return population[best_idx].copy()
    
    def _crossover(
        self, 
        parent1: Dict[str, float], 
        parent2: Dict[str, float],
        parameter_ranges: List[Any]
    ) -> Dict[str, float]:
        """Crossover operation for genetic algorithm."""
        child = {}
        for param in parent1.keys():
            # Uniform crossover
            if np.random.random() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child
    
    def _mutate(
        self, 
        individual: Dict[str, float], 
        parameter_ranges: List[Any],
        mutation_rate: float = 0.1
    ) -> Dict[str, float]:
        """Mutation operation for genetic algorithm."""
        mutated = individual.copy()
        
        for param in mutated.keys():
            if np.random.random() < mutation_rate:
                # Find parameter range
                param_range = next(pr for pr in parameter_ranges if pr.name == param)
                
                # Gaussian mutation
                mutation_strength = (param_range.max_value - param_range.min_value) * 0.1
                mutated[param] += np.random.normal(0, mutation_strength)
                
                # Clamp to bounds
                mutated[param] = max(param_range.min_value, 
                                   min(param_range.max_value, mutated[param]))
        
        return mutated
    
    def _calculate_population_diversity(self, population: List[Dict[str, float]]) -> float:
        """Calculate diversity measure for genetic algorithm population."""
        if len(population) < 2:
            return 0.0
        
        # Calculate average pairwise distance
        total_distance = 0.0
        comparisons = 0
        
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                distance = 0.0
                for param in population[i].keys():
                    distance += (population[i][param] - population[j][param]) ** 2
                total_distance += np.sqrt(distance)
                comparisons += 1
        
        return total_distance / comparisons if comparisons > 0 else 0.0
    
    def _calculate_swarm_diversity(self, particles: List[Dict[str, float]]) -> float:
        """Calculate diversity measure for particle swarm."""
        return self._calculate_population_diversity(particles)