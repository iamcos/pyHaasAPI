"""
Data models for parameter optimization and sweep operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from .backtest_models import BacktestConfig, BacktestExecution
from .result_models import ProcessedResults


class OptimizationAlgorithm(Enum):
    """Available optimization algorithms."""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    PARTICLE_SWARM = "particle_swarm"


class SweepStatus(Enum):
    """Status of parameter sweep execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParameterRange:
    """Defines a range for parameter optimization."""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    step: Union[int, float]
    parameter_type: type
    
    def generate_values(self) -> List[Union[int, float]]:
        """Generate all values in the parameter range."""
        values = []
        current = self.min_value
        while current <= self.max_value:
            values.append(current)
            current += self.step
        return values
    
    @property
    def total_combinations(self) -> int:
        """Calculate total number of parameter combinations."""
        return len(self.generate_values())


@dataclass
class SweepConfig:
    """Configuration for parameter sweep operations."""
    name: str
    base_config: BacktestConfig
    parameter_ranges: List[ParameterRange]
    optimization_metric: str = "sharpe_ratio"  # Metric to optimize for
    max_concurrent_executions: int = 5
    early_stopping: bool = False
    early_stopping_patience: int = 10
    
    @property
    def total_combinations(self) -> int:
        """Calculate total parameter combinations to test."""
        total = 1
        for param_range in self.parameter_ranges:
            total *= param_range.total_combinations
        return total
    
    def generate_parameter_sets(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations for the sweep."""
        if not self.parameter_ranges:
            return [{}]
        
        # Generate cartesian product of all parameter ranges
        import itertools
        
        param_values = []
        param_names = []
        
        for param_range in self.parameter_ranges:
            param_names.append(param_range.name)
            param_values.append(param_range.generate_values())
        
        combinations = []
        for combination in itertools.product(*param_values):
            param_set = dict(zip(param_names, combination))
            combinations.append(param_set)
        
        return combinations


@dataclass
class SweepExecution:
    """Tracks execution of a parameter sweep."""
    sweep_id: str
    config: SweepConfig
    status: SweepStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Execution tracking
    total_backtests: int = 0
    completed_backtests: int = 0
    failed_backtests: int = 0
    active_executions: List[BacktestExecution] = field(default_factory=list)
    
    # Results
    best_result: Optional[ProcessedResults] = None
    best_parameters: Optional[Dict[str, Any]] = None
    all_results: List[ProcessedResults] = field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate sweep progress percentage."""
        if self.total_backtests == 0:
            return 0.0
        return (self.completed_backtests / self.total_backtests) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if sweep has completed."""
        return self.status == SweepStatus.COMPLETED
    
    def update_best_result(self, result: ProcessedResults, parameters: Dict[str, Any]) -> None:
        """Update best result if this one is better."""
        if self.best_result is None:
            self.best_result = result
            self.best_parameters = parameters
            return
        
        # Compare based on optimization metric
        current_metric = getattr(result.execution_metrics, self.config.optimization_metric)
        best_metric = getattr(self.best_result.execution_metrics, self.config.optimization_metric)
        
        if current_metric > best_metric:
            self.best_result = result
            self.best_parameters = parameters


@dataclass
class OptimizationResults:
    """Results from an optimization algorithm execution."""
    algorithm: OptimizationAlgorithm
    best_parameters: Dict[str, Any]
    best_score: float
    optimization_history: List[Dict[str, Any]]
    convergence_data: List[float]
    total_evaluations: int
    execution_time: float
    
    # Statistical analysis
    parameter_importance: Dict[str, float] = field(default_factory=dict)
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    
    def get_top_results(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N results from optimization history."""
        sorted_results = sorted(
            self.optimization_history,
            key=lambda x: x.get('score', 0),
            reverse=True
        )
        return sorted_results[:n]


@dataclass
class OptimizationConfig:
    """Configuration for optimization algorithms."""
    script_id: str
    base_backtest_config: BacktestConfig
    parameter_ranges: List[ParameterRange]
    optimization_metric: str = "sharpe_ratio"
    max_evaluations: Optional[int] = None
    early_stopping: bool = False
    convergence_threshold: float = 0.001
    
    # Algorithm-specific parameters
    algorithm_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankedResults:
    """Results ranked by optimization criteria."""
    ranked_results: List[Dict[str, Any]]  # Each item has 'result', 'score', 'metrics'
    ranking_criteria: Dict[str, float]  # metric_name -> weight
    total_results: int
    
    def get_best_result(self) -> Optional[ProcessedResults]:
        """Get the best ranked result."""
        if not self.ranked_results:
            return None
        return self.ranked_results[0]['result']
    
    def get_top_n_results(self, n: int = 5) -> List[ProcessedResults]:
        """Get top N ranked results."""
        return [item['result'] for item in self.ranked_results[:n]]
    
    def get_ranking_summary(self) -> Dict[str, Any]:
        """Get summary of ranking results."""
        if not self.ranked_results:
            return {}
        
        return {
            'best_score': self.ranked_results[0]['score'],
            'worst_score': self.ranked_results[-1]['score'],
            'average_score': sum(item['score'] for item in self.ranked_results) / len(self.ranked_results),
            'score_range': self.ranked_results[0]['score'] - self.ranked_results[-1]['score']
        }