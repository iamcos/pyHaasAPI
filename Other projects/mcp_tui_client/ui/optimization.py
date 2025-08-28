"""
Parameter Optimization Interface

Advanced parameter optimization with mixed algorithms and real-time progress tracking.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.widget import Widget
from textual.widgets import (
    Static, DataTable, Button, Input, Select, Checkbox, 
    ProgressBar, Label, TabbedContent, TabPane, Tree, 
    TextArea, RadioSet, RadioButton, Collapsible
)
from textual.message import Message
from textual.reactive import reactive
from textual import events

from ..ui.components.panels import BasePanel, StatusPanel
from ..ui.components.charts import ASCIIChart
from ..ui.components.tables import DataTable as EnhancedDataTable
from ..ui.components.forms import FormField, BaseForm as FormContainer
from ..utils.logging import get_logger


class OptimizationAlgorithm(Enum):
    """Available optimization algorithms"""
    GENETIC = "genetic"
    PARTICLE_SWARM = "particle_swarm"
    SIMULATED_ANNEALING = "simulated_annealing"
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    MIXED = "mixed"


class OptimizationStatus(Enum):
    """Optimization execution status"""
    IDLE = "idle"
    CONFIGURING = "configuring"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParameterRange:
    """Parameter optimization range definition"""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    step: Union[int, float] = None
    parameter_type: str = "float"  # int, float, bool, choice
    choices: List[Any] = field(default_factory=list)
    current_value: Union[int, float] = None
    
    def __post_init__(self):
        if self.current_value is None:
            if self.parameter_type == "bool":
                self.current_value = False
            elif self.choices:
                self.current_value = self.choices[0]
            else:
                self.current_value = (self.min_value + self.max_value) / 2


@dataclass
class OptimizationConfig:
    """Optimization configuration"""
    lab_id: str
    algorithm: OptimizationAlgorithm = OptimizationAlgorithm.GENETIC
    max_iterations: int = 100
    population_size: int = 50
    convergence_threshold: float = 0.001
    timeout_minutes: int = 60
    parallel_execution: bool = True
    max_parallel_jobs: int = 4
    parameter_ranges: List[ParameterRange] = field(default_factory=list)
    objective_function: str = "sharpe_ratio"  # sharpe_ratio, total_return, max_drawdown, etc.
    minimize: bool = False  # False = maximize, True = minimize
    
    # Algorithm-specific settings
    genetic_settings: Dict[str, Any] = field(default_factory=lambda: {
        "mutation_rate": 0.1,
        "crossover_rate": 0.8,
        "selection_method": "tournament",
        "elitism_rate": 0.1
    })
    
    pso_settings: Dict[str, Any] = field(default_factory=lambda: {
        "inertia_weight": 0.9,
        "cognitive_weight": 2.0,
        "social_weight": 2.0,
        "velocity_clamp": 0.5
    })
    
    sa_settings: Dict[str, Any] = field(default_factory=lambda: {
        "initial_temperature": 1000.0,
        "cooling_rate": 0.95,
        "min_temperature": 0.01
    })


@dataclass
class OptimizationResult:
    """Single optimization result"""
    iteration: int
    parameters: Dict[str, Any]
    objective_value: float
    metrics: Dict[str, float]
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)


class ParameterRangeEditor(BasePanel):
    """Parameter range configuration editor"""
    
    def __init__(self, parameter_range: ParameterRange = None, **kwargs):
        super().__init__(title="Parameter Range Editor", **kwargs)
        self.parameter_range = parameter_range or ParameterRange("", 0, 100)
        self.logger = get_logger(__name__)
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize the parameter range editor"""
        form_container = FormContainer()
        
        # Parameter name
        form_container.add_field(FormField(
            "name", "Parameter Name", 
            Input(value=self.parameter_range.name, placeholder="Enter parameter name")
        ))
        
        # Parameter type
        type_options = [("int", "Integer"), ("float", "Float"), ("bool", "Boolean"), ("choice", "Choice")]
        form_container.add_field(FormField(
            "type", "Parameter Type",
            Select(type_options, value=self.parameter_range.parameter_type)
        ))
        
        # Min/Max values (for numeric types)
        form_container.add_field(FormField(
            "min_value", "Minimum Value",
            Input(value=str(self.parameter_range.min_value), placeholder="Minimum value")
        ))
        
        form_container.add_field(FormField(
            "max_value", "Maximum Value", 
            Input(value=str(self.parameter_range.max_value), placeholder="Maximum value")
        ))
        
        # Step size
        step_value = str(self.parameter_range.step) if self.parameter_range.step else ""
        form_container.add_field(FormField(
            "step", "Step Size (optional)",
            Input(value=step_value, placeholder="Step size for discrete values")
        ))
        
        # Choices (for choice type)
        choices_text = ", ".join(str(c) for c in self.parameter_range.choices)
        form_container.add_field(FormField(
            "choices", "Choices (comma-separated)",
            Input(value=choices_text, placeholder="value1, value2, value3")
        ))
        
        # Current value
        form_container.add_field(FormField(
            "current_value", "Current Value",
            Input(value=str(self.parameter_range.current_value), placeholder="Current parameter value")
        ))
        
        # Action buttons
        button_container = Horizontal(classes="button-container")
        button_container.mount(Button("Save", id="save-parameter", variant="primary"))
        button_container.mount(Button("Cancel", id="cancel-parameter", variant="default"))
        
        form_container.mount(button_container)
        self.update_content(form_container)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "save-parameter":
            await self._save_parameter()
        elif event.button.id == "cancel-parameter":
            await self._cancel_edit()
    
    async def _save_parameter(self) -> None:
        """Save parameter range configuration"""
        try:
            # Get form values
            form_data = self._get_form_data()
            
            # Update parameter range
            self.parameter_range.name = form_data.get("name", "")
            self.parameter_range.parameter_type = form_data.get("type", "float")
            
            if self.parameter_range.parameter_type in ["int", "float"]:
                self.parameter_range.min_value = float(form_data.get("min_value", 0))
                self.parameter_range.max_value = float(form_data.get("max_value", 100))
                
                if form_data.get("step"):
                    self.parameter_range.step = float(form_data.get("step"))
            
            if self.parameter_range.parameter_type == "choice":
                choices_text = form_data.get("choices", "")
                self.parameter_range.choices = [c.strip() for c in choices_text.split(",") if c.strip()]
            
            # Set current value
            current_str = form_data.get("current_value", "")
            if current_str:
                if self.parameter_range.parameter_type == "int":
                    self.parameter_range.current_value = int(current_str)
                elif self.parameter_range.parameter_type == "float":
                    self.parameter_range.current_value = float(current_str)
                elif self.parameter_range.parameter_type == "bool":
                    self.parameter_range.current_value = current_str.lower() in ["true", "1", "yes"]
                else:
                    self.parameter_range.current_value = current_str
            
            # Post save message
            self.post_message(ParameterSaved(self.parameter_range))
            
        except Exception as e:
            self.logger.error(f"Error saving parameter: {e}")
            self.set_status("error", f"Error saving parameter: {e}")
    
    async def _cancel_edit(self) -> None:
        """Cancel parameter editing"""
        self.post_message(ParameterEditCancelled())
    
    def _get_form_data(self) -> Dict[str, str]:
        """Extract form data from inputs"""
        form_data = {}
        try:
            content = self.query_one("#panel-content")
            for input_widget in content.query(Input):
                if hasattr(input_widget, 'id') and input_widget.id:
                    form_data[input_widget.id] = input_widget.value
            
            for select_widget in content.query(Select):
                if hasattr(select_widget, 'id') and select_widget.id:
                    form_data[select_widget.id] = select_widget.value
        except Exception as e:
            self.logger.error(f"Error extracting form data: {e}")
        
        return form_data


class OptimizationProgressPanel(StatusPanel):
    """Real-time optimization progress tracking"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Optimization Progress", **kwargs)
        self.current_iteration = 0
        self.total_iterations = 0
        self.best_result: Optional[OptimizationResult] = None
        self.results_history: List[OptimizationResult] = []
        self.start_time: Optional[datetime] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize progress panel"""
        self._setup_progress_display()
    
    def _setup_progress_display(self) -> None:
        """Set up the progress display components"""
        # Add status items
        self.add_status_item("status", "Status", "Idle", "normal")
        self.add_status_item("iteration", "Iteration", "0 / 0", "normal")
        self.add_status_item("best_value", "Best Value", "N/A", "normal")
        self.add_status_item("elapsed_time", "Elapsed Time", "00:00:00", "normal")
        self.add_status_item("estimated_remaining", "Est. Remaining", "N/A", "normal")
    
    def update_progress(self, iteration: int, total: int, best_result: OptimizationResult = None) -> None:
        """Update optimization progress"""
        self.current_iteration = iteration
        self.total_iterations = total
        
        if best_result:
            self.best_result = best_result
            self.results_history.append(best_result)
        
        # Update status items
        progress_text = f"{iteration} / {total}"
        self.update_status_item("iteration", progress_text)
        
        if self.best_result:
            self.update_status_item("best_value", f"{self.best_result.objective_value:.4f}")
        
        # Calculate elapsed time
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            self.update_status_item("elapsed_time", elapsed_str)
            
            # Estimate remaining time
            if iteration > 0:
                avg_time_per_iteration = elapsed.total_seconds() / iteration
                remaining_iterations = total - iteration
                remaining_seconds = avg_time_per_iteration * remaining_iterations
                remaining_time = timedelta(seconds=int(remaining_seconds))
                self.update_status_item("estimated_remaining", str(remaining_time).split('.')[0])
    
    def start_optimization(self) -> None:
        """Start optimization tracking"""
        self.start_time = datetime.now()
        self.update_status_item("status", "Running", "success")
        self.results_history.clear()
    
    def complete_optimization(self) -> None:
        """Complete optimization tracking"""
        self.update_status_item("status", "Completed", "success")
        if self.start_time:
            total_time = datetime.now() - self.start_time
            self.update_status_item("estimated_remaining", "Completed")
    
    def fail_optimization(self, error: str) -> None:
        """Mark optimization as failed"""
        self.update_status_item("status", f"Failed: {error}", "error")


class OptimizationResultsPanel(BasePanel):
    """Optimization results analysis and visualization"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Optimization Results", **kwargs)
        self.results: List[OptimizationResult] = []
        self.logger = get_logger(__name__)
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize results panel"""
        self._setup_results_display()
    
    def _setup_results_display(self) -> None:
        """Set up results display"""
        container = TabbedContent()
        
        # Results table tab
        with container.add_pane("table", "Results Table"):
            results_table = EnhancedDataTable(id="results-table")
            results_table.add_columns(
                "Iteration", "Objective Value", "Parameters", "Execution Time", "Timestamp"
            )
        
        # Convergence chart tab
        with container.add_pane("chart", "Convergence Chart"):
            chart = ASCIIChart(
                title="Optimization Convergence",
                width=80,
                height=20,
                chart_type="line"
            )
        
        # Parameter analysis tab
        with container.add_pane("analysis", "Parameter Analysis"):
            analysis_container = ScrollableContainer()
        
        self.update_content(container)
    
    def update_results(self, results: List[OptimizationResult]) -> None:
        """Update results display"""
        self.results = results
        self._update_results_table()
        self._update_convergence_chart()
        self._update_parameter_analysis()
    
    def _update_results_table(self) -> None:
        """Update the results table"""
        try:
            table = self.query_one("#results-table", EnhancedDataTable)
            table.clear()
            
            for result in self.results:
                params_str = ", ".join([f"{k}={v}" for k, v in result.parameters.items()])
                table.add_row(
                    str(result.iteration),
                    f"{result.objective_value:.6f}",
                    params_str,
                    f"{result.execution_time:.2f}s",
                    result.timestamp.strftime("%H:%M:%S")
                )
        except Exception as e:
            self.logger.error(f"Error updating results table: {e}")
    
    def _update_convergence_chart(self) -> None:
        """Update convergence chart"""
        try:
            if not self.results:
                return
            
            # Prepare data for chart
            iterations = [r.iteration for r in self.results]
            values = [r.objective_value for r in self.results]
            
            # Find best values so far (cumulative best)
            best_values = []
            current_best = values[0] if values else 0
            
            for value in values:
                if value > current_best:  # Assuming maximization
                    current_best = value
                best_values.append(current_best)
            
            # Update chart (simplified for now)
            chart_container = self.query_one("#chart")
            chart_text = self._create_simple_chart(iterations, best_values)
            chart_container.update(chart_text)
            
        except Exception as e:
            self.logger.error(f"Error updating convergence chart: {e}")
    
    def _create_simple_chart(self, x_data: List[int], y_data: List[float]) -> str:
        """Create a simple ASCII chart"""
        if not x_data or not y_data:
            return "No data available"
        
        # Simple text-based chart representation
        min_y, max_y = min(y_data), max(y_data)
        chart_lines = []
        
        chart_lines.append(f"Convergence Chart (Best Value: {max_y:.6f})")
        chart_lines.append("=" * 50)
        
        # Show last 10 iterations
        recent_x = x_data[-10:] if len(x_data) > 10 else x_data
        recent_y = y_data[-10:] if len(y_data) > 10 else y_data
        
        for i, (x, y) in enumerate(zip(recent_x, recent_y)):
            bar_length = int((y - min_y) / (max_y - min_y + 0.001) * 30)
            bar = "█" * bar_length
            chart_lines.append(f"Iter {x:3d}: {bar} {y:.6f}")
        
        return "\n".join(chart_lines)
    
    def _update_parameter_analysis(self) -> None:
        """Update parameter analysis"""
        try:
            if not self.results:
                return
            
            # Analyze parameter correlations and ranges
            analysis_text = self._analyze_parameters()
            
            analysis_container = self.query_one("#analysis")
            analysis_container.update(Static(analysis_text))
            
        except Exception as e:
            self.logger.error(f"Error updating parameter analysis: {e}")
    
    def _analyze_parameters(self) -> str:
        """Analyze parameter performance"""
        if not self.results:
            return "No results available for analysis"
        
        analysis_lines = []
        analysis_lines.append("Parameter Analysis")
        analysis_lines.append("=" * 30)
        
        # Get all parameter names
        all_params = set()
        for result in self.results:
            all_params.update(result.parameters.keys())
        
        # Analyze each parameter
        for param_name in sorted(all_params):
            param_values = []
            objective_values = []
            
            for result in self.results:
                if param_name in result.parameters:
                    param_values.append(result.parameters[param_name])
                    objective_values.append(result.objective_value)
            
            if param_values:
                min_val = min(param_values)
                max_val = max(param_values)
                
                # Find best parameter value
                best_idx = objective_values.index(max(objective_values))
                best_param_val = param_values[best_idx]
                
                analysis_lines.append(f"\n{param_name}:")
                analysis_lines.append(f"  Range: {min_val} - {max_val}")
                analysis_lines.append(f"  Best Value: {best_param_val}")
                analysis_lines.append(f"  Best Objective: {max(objective_values):.6f}")
        
        return "\n".join(analysis_lines)


# Message classes for component communication
class ParameterSaved(Message):
    """Message sent when a parameter is saved"""
    def __init__(self, parameter_range: ParameterRange):
        super().__init__()
        self.parameter_range = parameter_range


class ParameterEditCancelled(Message):
    """Message sent when parameter editing is cancelled"""
    pass


class OptimizationStarted(Message):
    """Message sent when optimization starts"""
    def __init__(self, config: OptimizationConfig):
        super().__init__()
        self.config = config


class OptimizationCompleted(Message):
    """Message sent when optimization completes"""
    def __init__(self, results: List[OptimizationResult]):
        super().__init__()
        self.results = results


class ParameterOptimizationInterface(Widget):
    """Main parameter optimization interface"""
    
    def __init__(self, lab_id: str = None, **kwargs):
        super().__init__(**kwargs)
        self.lab_id = lab_id
        self.config = OptimizationConfig(lab_id or "")
        self.status = OptimizationStatus.IDLE
        self.logger = get_logger(__name__)
        
        # Components
        self.progress_panel: Optional[OptimizationProgressPanel] = None
        self.results_panel: Optional[OptimizationResultsPanel] = None
        self.parameter_editor: Optional[ParameterRangeEditor] = None
    
    def compose(self) -> ComposeResult:
        """Compose the optimization interface"""
        with TabbedContent():
            with TabPane("Configuration", id="config-tab"):
                yield self._create_configuration_panel()
            
            with TabPane("Progress", id="progress-tab"):
                self.progress_panel = OptimizationProgressPanel()
                yield self.progress_panel
            
            with TabPane("Results", id="results-tab"):
                self.results_panel = OptimizationResultsPanel()
                yield self.results_panel
    
    def _create_configuration_panel(self) -> Widget:
        """Create the configuration panel"""
        container = ScrollableContainer()
        
        # Algorithm selection
        algo_section = Collapsible(title="Algorithm Configuration", collapsed=False)
        algo_options = [(algo.value, algo.value.replace("_", " ").title()) for algo in OptimizationAlgorithm]
        algo_select = Select(algo_options, value=self.config.algorithm.value, id="algorithm-select")
        algo_section.mount(algo_select)
        
        # Basic settings
        settings_section = Collapsible(title="Optimization Settings", collapsed=False)
        settings_form = FormContainer()
        
        settings_form.add_field(FormField(
            "max_iterations", "Max Iterations",
            Input(value=str(self.config.max_iterations), placeholder="100")
        ))
        
        settings_form.add_field(FormField(
            "population_size", "Population Size",
            Input(value=str(self.config.population_size), placeholder="50")
        ))
        
        settings_form.add_field(FormField(
            "timeout_minutes", "Timeout (minutes)",
            Input(value=str(self.config.timeout_minutes), placeholder="60")
        ))
        
        settings_form.add_field(FormField(
            "objective_function", "Objective Function",
            Select([
                ("sharpe_ratio", "Sharpe Ratio"),
                ("total_return", "Total Return"),
                ("max_drawdown", "Max Drawdown"),
                ("profit_factor", "Profit Factor"),
                ("win_rate", "Win Rate")
            ], value=self.config.objective_function)
        ))
        
        settings_form.add_field(FormField(
            "minimize", "Optimization Goal",
            RadioSet(
                RadioButton("Maximize", value=True, id="maximize"),
                RadioButton("Minimize", value=False, id="minimize")
            )
        ))
        
        settings_section.mount(settings_form)
        
        # Parameter ranges
        params_section = Collapsible(title="Parameter Ranges", collapsed=False)
        params_container = Container(id="parameters-container")
        
        # Add parameter button
        add_param_btn = Button("Add Parameter", id="add-parameter", variant="primary")
        params_container.mount(add_param_btn)
        
        # Parameters list
        params_list = Container(id="parameters-list")
        params_container.mount(params_list)
        params_section.mount(params_container)
        
        # Control buttons
        controls = Horizontal(classes="control-buttons")
        controls.mount(Button("Start Optimization", id="start-optimization", variant="success"))
        controls.mount(Button("Stop Optimization", id="stop-optimization", variant="error"))
        controls.mount(Button("Reset Configuration", id="reset-config", variant="default"))
        
        # Assemble container
        container.mount(algo_section)
        container.mount(settings_section)
        container.mount(params_section)
        container.mount(controls)
        
        return container
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "add-parameter":
            await self._add_parameter()
        elif event.button.id == "start-optimization":
            await self._start_optimization()
        elif event.button.id == "stop-optimization":
            await self._stop_optimization()
        elif event.button.id == "reset-config":
            await self._reset_configuration()
    
    async def _add_parameter(self) -> None:
        """Add a new parameter range"""
        try:
            # Create new parameter editor
            new_param = ParameterRange(f"param_{len(self.config.parameter_ranges) + 1}", 0, 100)
            self.parameter_editor = ParameterRangeEditor(new_param)
            
            # Add to parameters list
            params_list = self.query_one("#parameters-list")
            params_list.mount(self.parameter_editor)
            
        except Exception as e:
            self.logger.error(f"Error adding parameter: {e}")
    
    async def _start_optimization(self) -> None:
        """Start the optimization process"""
        try:
            if self.status != OptimizationStatus.IDLE:
                return
            
            # Update configuration from form
            await self._update_config_from_form()
            
            # Validate configuration
            if not self._validate_config():
                return
            
            # Start optimization
            self.status = OptimizationStatus.RUNNING
            if self.progress_panel:
                self.progress_panel.start_optimization()
            
            # Post start message
            self.post_message(OptimizationStarted(self.config))
            
            # Run optimization (mock for now)
            await self._run_optimization()
            
        except Exception as e:
            self.logger.error(f"Error starting optimization: {e}")
            self.status = OptimizationStatus.FAILED
            if self.progress_panel:
                self.progress_panel.fail_optimization(str(e))
    
    async def _run_optimization(self) -> None:
        """Run the optimization process (mock implementation)"""
        try:
            results = []
            
            for iteration in range(1, self.config.max_iterations + 1):
                # Mock optimization step
                await asyncio.sleep(0.1)  # Simulate computation time
                
                # Generate mock result
                mock_params = {}
                for param_range in self.config.parameter_ranges:
                    if param_range.parameter_type == "float":
                        import random
                        mock_params[param_range.name] = random.uniform(
                            param_range.min_value, param_range.max_value
                        )
                    elif param_range.parameter_type == "int":
                        import random
                        mock_params[param_range.name] = random.randint(
                            int(param_range.min_value), int(param_range.max_value)
                        )
                
                # Mock objective value (improving over time)
                base_value = 0.5 + (iteration / self.config.max_iterations) * 0.3
                import random
                objective_value = base_value + random.uniform(-0.1, 0.1)
                
                result = OptimizationResult(
                    iteration=iteration,
                    parameters=mock_params,
                    objective_value=objective_value,
                    metrics={"return": objective_value * 100, "drawdown": -objective_value * 10},
                    execution_time=0.1
                )
                
                results.append(result)
                
                # Update progress
                if self.progress_panel:
                    self.progress_panel.update_progress(iteration, self.config.max_iterations, result)
                
                # Update results
                if self.results_panel:
                    self.results_panel.update_results(results)
                
                # Check for cancellation
                if self.status != OptimizationStatus.RUNNING:
                    break
            
            # Complete optimization
            self.status = OptimizationStatus.COMPLETED
            if self.progress_panel:
                self.progress_panel.complete_optimization()
            
            self.post_message(OptimizationCompleted(results))
            
        except Exception as e:
            self.logger.error(f"Error during optimization: {e}")
            self.status = OptimizationStatus.FAILED
            if self.progress_panel:
                self.progress_panel.fail_optimization(str(e))
    
    async def _stop_optimization(self) -> None:
        """Stop the optimization process"""
        if self.status == OptimizationStatus.RUNNING:
            self.status = OptimizationStatus.CANCELLED
    
    async def _reset_configuration(self) -> None:
        """Reset optimization configuration"""
        self.config = OptimizationConfig(self.lab_id or "")
        self.status = OptimizationStatus.IDLE
        # TODO: Reset form fields
    
    async def _update_config_from_form(self) -> None:
        """Update configuration from form inputs"""
        try:
            # Get algorithm selection
            algo_select = self.query_one("#algorithm-select", Select)
            self.config.algorithm = OptimizationAlgorithm(algo_select.value)
            
            # Get other form values
            # TODO: Extract values from form inputs
            
        except Exception as e:
            self.logger.error(f"Error updating config from form: {e}")
    
    def _validate_config(self) -> bool:
        """Validate optimization configuration"""
        if not self.config.parameter_ranges:
            self.logger.error("No parameter ranges defined")
            return False
        
        if self.config.max_iterations <= 0:
            self.logger.error("Max iterations must be positive")
            return False
        
        return True
    
    async def on_parameter_saved(self, message: ParameterSaved) -> None:
        """Handle parameter saved message"""
        # Add parameter to configuration
        self.config.parameter_ranges.append(message.parameter_range)
        self.logger.info(f"Parameter '{message.parameter_range.name}' added to configuration")
    
    async def on_parameter_edit_cancelled(self, message: ParameterEditCancelled) -> None:
        """Handle parameter edit cancelled message"""
        # Remove the parameter editor
        if self.parameter_editor:
            await self.parameter_editor.remove()
            self.parameter_editor = None