#!/usr/bin/env python3
"""
Backtest Execution System
This module provides comprehensive backtest execution functionality for the
distributed trading bot testing automation system, including lab execution,
progress monitoring, and result collection.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.server_manager import ServerManager
from infrastructure.error_handler import retry_on_error, RetryConfig, GracefulErrorHandler, ErrorCategory
from lab_configuration.lab_configurator import LabConfiguration, LabStatus
from account_management.account_manager import AccountManager

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """Backtest execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class ExecutionPriority(Enum):
    """Execution priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class ExecutionProgress:
    """Progress information for backtest execution"""
    lab_id: str
    current_generation: int
    max_generations: int
    current_population: int
    max_population: int
    best_fitness: float
    elapsed_time: float
    estimated_remaining: float
    progress_percentage: float
    last_update: float

@dataclass
class ExecutionResult:
    """Result of backtest execution"""
    lab_id: str
    execution_id: str
    status: ExecutionStatus
    start_time: float
    end_time: Optional[float]
    total_duration: float
    best_configuration: Optional[Dict[str, Any]]
    best_fitness: float
    total_generations: int
    total_evaluations: int
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    server_id: str

@dataclass
class ExecutionRequest:
    """Request for backtest execution"""
    lab_id: str
    lab_configuration: LabConfiguration
    priority: ExecutionPriority
    timeout_minutes: int
    retry_on_failure: bool
    max_retries: int
    callback: Optional[Callable] = None
    created_time: float = None
    
    def __post_init__(self):
        if self.created_time is None:
            self.created_time = time.time()

class BacktestExecutor:
    """Main backtest execution engine"""
    
    def __init__(self, server_manager: ServerManager, account_manager: AccountManager):
        self.server_manager = server_manager
        self.account_manager = account_manager
        self.error_handler = GracefulErrorHandler()
        
        # Execution tracking
        self.execution_queue: List[ExecutionRequest] = []
        self.active_executions: Dict[str, ExecutionRequest] = {}
        self.execution_results: Dict[str, ExecutionResult] = {}
        self.execution_progress: Dict[str, ExecutionProgress] = {}
        
        # Configuration
        self.max_concurrent_executions = 10
        self.default_timeout_minutes = 120
        self.progress_update_interval = 30  # seconds
        
        # Thread pool for concurrent executions
        self.executor_pool = ThreadPoolExecutor(max_workers=self.max_concurrent_executions)
        
        # Register error handlers
        self._register_error_handlers()
    
    def _register_error_handlers(self):
        """Register error handlers for execution operations"""
        def execution_fallback(error, context):
            return f"Execution failed for {context.get('lab_id', 'unknown')}: {error}"
        
        def api_error_fallback(error, context):
            return f"API error during execution: {error}"
        
        self.error_handler.register_fallback_handler(ErrorCategory.API, api_error_fallback)
        self.error_handler.register_fallback_handler(ErrorCategory.CONNECTION, execution_fallback)
    
    def submit_execution(
        self,
        lab_configuration: LabConfiguration,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
        timeout_minutes: int = None,
        retry_on_failure: bool = True,
        max_retries: int = 3,
        callback: Callable = None
    ) -> str:
        """
        Submit a backtest execution request.
        
        Args:
            lab_configuration: Lab configuration to execute
            priority: Execution priority
            timeout_minutes: Execution timeout in minutes
            retry_on_failure: Whether to retry on failure
            max_retries: Maximum retry attempts
            callback: Optional callback function for completion
            
        Returns:
            Execution ID
        """
        execution_id = f"exec_{lab_configuration.lab_id}_{int(time.time())}"
        
        if timeout_minutes is None:
            timeout_minutes = self.default_timeout_minutes
        
        request = ExecutionRequest(
            lab_id=lab_configuration.lab_id,
            lab_configuration=lab_configuration,
            priority=priority,
            timeout_minutes=timeout_minutes,
            retry_on_failure=retry_on_failure,
            max_retries=max_retries,
            callback=callback
        )
        
        # Add to queue (sorted by priority)
        self.execution_queue.append(request)
        self.execution_queue.sort(key=lambda x: x.priority.value, reverse=True)
        
        logger.info(f"Submitted execution request {execution_id} for lab {lab_configuration.lab_id}")
        return execution_id
    
    def start_execution_processing(self):
        """Start processing execution queue"""
        logger.info("Starting backtest execution processing")
        
        while True:
            try:
                # Process queue
                self._process_execution_queue()
                
                # Update progress for active executions
                self._update_execution_progress()
                
                # Clean up completed executions
                self._cleanup_completed_executions()
                
                # Wait before next iteration
                time.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Execution processing interrupted")
                break
            except Exception as e:
                logger.error(f"Error in execution processing: {e}")
                time.sleep(10)
    
    def _process_execution_queue(self):
        """Process pending execution requests"""
        if not self.execution_queue:
            return
        
        # Check if we can start new executions
        available_slots = self.max_concurrent_executions - len(self.active_executions)
        if available_slots <= 0:
            return
        
        # Start executions up to available slots
        for _ in range(min(available_slots, len(self.execution_queue))):
            request = self.execution_queue.pop(0)
            self._start_execution(request)
    
    def _start_execution(self, request: ExecutionRequest):
        """Start a single backtest execution"""
        lab_id = request.lab_id
        
        try:
            # Validate configuration
            is_valid, issues = self._validate_execution_request(request)
            if not is_valid:
                self._handle_execution_failure(request, f"Validation failed: {'; '.join(issues)}")
                return
            
            # Add to active executions
            self.active_executions[lab_id] = request
            
            # Submit to thread pool
            future = self.executor_pool.submit(self._execute_backtest, request)
            
            # Store future for tracking
            request.future = future
            
            logger.info(f"Started execution for lab {lab_id}")
            
        except Exception as e:
            self._handle_execution_failure(request, f"Failed to start execution: {e}")
    
    @retry_on_error(RetryConfig(max_attempts=3, base_delay=2.0))
    def _execute_backtest(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute a single backtest.
        
        Args:
            request: Execution request
            
        Returns:
            ExecutionResult
        """
        lab_id = request.lab_id
        config = request.lab_configuration
        start_time = time.time()
        
        logger.info(f"Executing backtest for lab {lab_id}")
        
        try:
            # Get server executor
            server_executor = self._get_server_executor(config.server_id)
            if not server_executor:
                raise Exception(f"Cannot get executor for server {config.server_id}")
            
            # Create lab on server
            lab_creation_result = self._create_lab_on_server(server_executor, config)
            if not lab_creation_result.get('success', False):
                raise Exception(f"Failed to create lab: {lab_creation_result.get('error', 'Unknown error')}")
            
            # Start backtest
            execution_id = lab_creation_result.get('lab_id', lab_id)
            start_result = self._start_backtest_on_server(server_executor, execution_id, config)
            if not start_result.get('success', False):
                raise Exception(f"Failed to start backtest: {start_result.get('error', 'Unknown error')}")
            
            # Monitor execution
            result = self._monitor_backtest_execution(server_executor, execution_id, request)
            
            # Collect results
            if result.status == ExecutionStatus.COMPLETED:
                result_data = self._collect_backtest_results(server_executor, execution_id)
                result.result_data = result_data
            
            # Update configuration status
            config.status = LabStatus.COMPLETED if result.status == ExecutionStatus.COMPLETED else LabStatus.ERROR
            
            logger.info(f"Backtest execution completed for lab {lab_id}: {result.status.value}")
            return result
            
        except Exception as e:
            error_msg = self.error_handler.handle_error(
                e,
                {'operation': 'execute_backtest', 'lab_id': lab_id},
                f"Backtest execution failed for {lab_id}"
            )
            
            return ExecutionResult(
                lab_id=lab_id,
                execution_id=f"exec_{lab_id}_{int(start_time)}",
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=time.time(),
                total_duration=time.time() - start_time,
                best_configuration=None,
                best_fitness=0.0,
                total_generations=0,
                total_evaluations=0,
                result_data=None,
                error_message=error_msg,
                server_id=config.server_id
            )
    
    def _create_lab_on_server(self, server_executor, config: LabConfiguration) -> Dict[str, Any]:
        """Create lab on server (mock implementation)"""
        try:
            # Mock lab creation - in real implementation, this would use HaasOnline API
            logger.info(f"Creating lab {config.lab_id} on server {config.server_id}")
            
            # Simulate lab creation
            time.sleep(1)  # Simulate API call delay
            
            return {
                'success': True,
                'lab_id': config.lab_id,
                'message': 'Lab created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _start_backtest_on_server(self, server_executor, lab_id: str, config: LabConfiguration) -> Dict[str, Any]:
        """Start backtest on server (mock implementation)"""
        try:
            # Mock backtest start - in real implementation, this would use HaasOnline API
            logger.info(f"Starting backtest for lab {lab_id}")
            
            # Simulate backtest start
            time.sleep(0.5)  # Simulate API call delay
            
            return {
                'success': True,
                'execution_id': f"exec_{lab_id}_{int(time.time())}",
                'message': 'Backtest started successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _monitor_backtest_execution(self, server_executor, execution_id: str, request: ExecutionRequest) -> ExecutionResult:
        """Monitor backtest execution progress"""
        lab_id = request.lab_id
        config = request.lab_configuration
        start_time = time.time()
        timeout_seconds = request.timeout_minutes * 60
        
        logger.info(f"Monitoring backtest execution {execution_id}")
        
        # Initialize progress tracking
        progress = ExecutionProgress(
            lab_id=lab_id,
            current_generation=0,
            max_generations=config.algorithm_config.max_generations,
            current_population=0,
            max_population=config.algorithm_config.max_population,
            best_fitness=0.0,
            elapsed_time=0.0,
            estimated_remaining=0.0,
            progress_percentage=0.0,
            last_update=time.time()
        )
        self.execution_progress[lab_id] = progress
        
        # Mock execution monitoring
        total_generations = config.algorithm_config.max_generations
        generation_time = 30  # seconds per generation (mock)
        
        for generation in range(1, total_generations + 1):
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(f"Backtest {execution_id} timed out after {elapsed:.1f} seconds")
                return ExecutionResult(
                    lab_id=lab_id,
                    execution_id=execution_id,
                    status=ExecutionStatus.TIMEOUT,
                    start_time=start_time,
                    end_time=time.time(),
                    total_duration=elapsed,
                    best_configuration=None,
                    best_fitness=progress.best_fitness,
                    total_generations=generation - 1,
                    total_evaluations=(generation - 1) * config.algorithm_config.max_population,
                    result_data=None,
                    error_message="Execution timed out",
                    server_id=config.server_id
                )
            
            # Simulate generation processing
            time.sleep(min(generation_time, 2))  # Cap sleep for testing
            
            # Update progress
            progress.current_generation = generation
            progress.current_population = config.algorithm_config.max_population
            progress.best_fitness = min(100.0, progress.best_fitness + (10.0 / generation))  # Mock fitness improvement
            progress.elapsed_time = time.time() - start_time
            progress.estimated_remaining = (total_generations - generation) * generation_time
            progress.progress_percentage = (generation / total_generations) * 100
            progress.last_update = time.time()
            
            logger.debug(f"Generation {generation}/{total_generations} completed for {lab_id}")
        
        # Execution completed successfully
        end_time = time.time()
        total_duration = end_time - start_time
        
        return ExecutionResult(
            lab_id=lab_id,
            execution_id=execution_id,
            status=ExecutionStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            best_configuration={'mock': 'configuration'},  # Mock best config
            best_fitness=progress.best_fitness,
            total_generations=total_generations,
            total_evaluations=total_generations * config.algorithm_config.max_population,
            result_data=None,  # Will be populated by _collect_backtest_results
            error_message=None,
            server_id=config.server_id
        )
    
    def _collect_backtest_results(self, server_executor, execution_id: str) -> Dict[str, Any]:
        """Collect backtest results from server"""
        try:
            # Mock result collection - in real implementation, this would fetch actual results
            logger.info(f"Collecting results for execution {execution_id}")
            
            # Simulate result collection
            time.sleep(1)
            
            return {
                'best_parameters': {
                    'param1': 0.75,
                    'param2': 1.25,
                    'param3': 0.5
                },
                'performance_metrics': {
                    'total_return': 15.6,
                    'sharpe_ratio': 1.8,
                    'max_drawdown': -8.2,
                    'win_rate': 0.65
                },
                'trade_statistics': {
                    'total_trades': 156,
                    'winning_trades': 101,
                    'losing_trades': 55,
                    'average_win': 2.3,
                    'average_loss': -1.8
                },
                'equity_curve': [100, 102, 98, 105, 108, 115],  # Mock equity curve
                'collection_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect results for {execution_id}: {e}")
            return {'error': str(e)}
    
    def _validate_execution_request(self, request: ExecutionRequest) -> Tuple[bool, List[str]]:
        """Validate execution request"""
        issues = []
        config = request.lab_configuration
        
        # Validate lab configuration
        if not config.lab_id:
            issues.append("Lab ID is required")
        
        if not config.server_id:
            issues.append("Server ID is required")
        
        if not config.script_id:
            issues.append("Script ID is required")
        
        # Validate algorithm configuration
        if config.algorithm_config.max_population <= 0:
            issues.append("Max population must be positive")
        
        if config.algorithm_config.max_generations <= 0:
            issues.append("Max generations must be positive")
        
        # Validate market configuration
        if not config.market_config.market_tag:
            issues.append("Market tag is required")
        
        # Validate account configuration
        if not config.account_config.account_id:
            issues.append("Account ID is required")
        
        # Validate server availability (simplified for testing)
        # In real implementation, this would check server availability
        available_servers = self.server_manager.get_available_servers()
        if config.server_id not in available_servers:
            issues.append(f"Server {config.server_id} is not available")
        
        # Validate account availability (simplified for testing)
        # In real implementation, this would check account availability
        # For now, just check if account_id is provided
        if not config.account_config.account_id:
            issues.append("Account ID is required")
        
        return len(issues) == 0, issues
    
    def _update_execution_progress(self):
        """Update progress for all active executions"""
        current_time = time.time()
        
        for lab_id, request in list(self.active_executions.items()):
            if hasattr(request, 'future') and request.future.done():
                # Execution completed, move to results
                try:
                    result = request.future.result()
                    self.execution_results[lab_id] = result
                    
                    # Call callback if provided
                    if request.callback:
                        try:
                            request.callback(result)
                        except Exception as e:
                            logger.error(f"Callback failed for {lab_id}: {e}")
                    
                    # Remove from active executions
                    del self.active_executions[lab_id]
                    
                    logger.info(f"Execution completed for {lab_id}: {result.status.value}")
                    
                except Exception as e:
                    logger.error(f"Failed to get result for {lab_id}: {e}")
                    self._handle_execution_failure(request, str(e))
    
    def _cleanup_completed_executions(self):
        """Clean up old completed executions"""
        current_time = time.time()
        cleanup_age = 3600  # 1 hour
        
        # Clean up old results
        to_remove = []
        for lab_id, result in self.execution_results.items():
            if result.end_time and (current_time - result.end_time) > cleanup_age:
                to_remove.append(lab_id)
        
        for lab_id in to_remove:
            del self.execution_results[lab_id]
            if lab_id in self.execution_progress:
                del self.execution_progress[lab_id]
    
    def _handle_execution_failure(self, request: ExecutionRequest, error_message: str):
        """Handle execution failure"""
        lab_id = request.lab_id
        
        # Create failure result
        result = ExecutionResult(
            lab_id=lab_id,
            execution_id=f"exec_{lab_id}_{int(time.time())}",
            status=ExecutionStatus.FAILED,
            start_time=time.time(),
            end_time=time.time(),
            total_duration=0.0,
            best_configuration=None,
            best_fitness=0.0,
            total_generations=0,
            total_evaluations=0,
            result_data=None,
            error_message=error_message,
            server_id=request.lab_configuration.server_id
        )
        
        # Store result
        self.execution_results[lab_id] = result
        
        # Remove from active executions
        if lab_id in self.active_executions:
            del self.active_executions[lab_id]
        
        # Call callback if provided
        if request.callback:
            try:
                request.callback(result)
            except Exception as e:
                logger.error(f"Callback failed for {lab_id}: {e}")
        
        logger.error(f"Execution failed for {lab_id}: {error_message}")
    
    def _get_server_executor(self, server_id: str):
        """Get server executor (mock implementation)"""
        # Mock executor - in real implementation, get from server manager
        return MockServerExecutor(server_id)
    
    def get_execution_status(self, lab_id: str) -> Optional[ExecutionStatus]:
        """Get execution status for a lab"""
        if lab_id in self.active_executions:
            return ExecutionStatus.RUNNING
        elif lab_id in self.execution_results:
            return self.execution_results[lab_id].status
        else:
            # Check if in queue
            for request in self.execution_queue:
                if request.lab_id == lab_id:
                    return ExecutionStatus.PENDING
            return None
    
    def get_execution_progress(self, lab_id: str) -> Optional[ExecutionProgress]:
        """Get execution progress for a lab"""
        return self.execution_progress.get(lab_id)
    
    def get_execution_result(self, lab_id: str) -> Optional[ExecutionResult]:
        """Get execution result for a lab"""
        return self.execution_results.get(lab_id)
    
    def cancel_execution(self, lab_id: str) -> bool:
        """Cancel a pending or running execution"""
        # Cancel if in queue
        for i, request in enumerate(self.execution_queue):
            if request.lab_id == lab_id:
                del self.execution_queue[i]
                logger.info(f"Cancelled queued execution for {lab_id}")
                return True
        
        # Cancel if running
        if lab_id in self.active_executions:
            request = self.active_executions[lab_id]
            if hasattr(request, 'future'):
                request.future.cancel()
            
            # Create cancellation result
            result = ExecutionResult(
                lab_id=lab_id,
                execution_id=f"exec_{lab_id}_{int(time.time())}",
                status=ExecutionStatus.CANCELLED,
                start_time=time.time(),
                end_time=time.time(),
                total_duration=0.0,
                best_configuration=None,
                best_fitness=0.0,
                total_generations=0,
                total_evaluations=0,
                result_data=None,
                error_message="Execution cancelled by user",
                server_id=request.lab_configuration.server_id
            )
            
            self.execution_results[lab_id] = result
            del self.active_executions[lab_id]
            
            logger.info(f"Cancelled running execution for {lab_id}")
            return True
        
        return False
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions"""
        # Count by status
        status_counts = {}
        for result in self.execution_results.values():
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Add active executions
        status_counts['running'] = status_counts.get('running', 0) + len(self.active_executions)
        status_counts['pending'] = len(self.execution_queue)
        
        # Calculate average execution time
        completed_results = [r for r in self.execution_results.values() if r.status == ExecutionStatus.COMPLETED]
        avg_execution_time = sum(r.total_duration for r in completed_results) / len(completed_results) if completed_results else 0
        
        return {
            'total_executions': len(self.execution_results) + len(self.active_executions) + len(self.execution_queue),
            'status_distribution': status_counts,
            'active_executions': len(self.active_executions),
            'queued_executions': len(self.execution_queue),
            'completed_executions': len(completed_results),
            'average_execution_time': avg_execution_time,
            'max_concurrent_executions': self.max_concurrent_executions
        }

class MockServerExecutor:
    """Mock server executor for testing"""
    def __init__(self, server_id: str):
        self.server_id = server_id

def main():
    """Test the backtest execution system"""
    from infrastructure.server_manager import ServerManager
    from account_management.account_manager import AccountManager
    from lab_configuration.lab_configurator import LabConfigurator, LabAlgorithm
    
    print("Testing Backtest Execution System...")
    print("=" * 50)
    
    # Initialize components
    from infrastructure.config_manager import ConfigManager
    
    server_manager = ServerManager()
    config_manager = ConfigManager()
    account_manager = AccountManager(server_manager, config_manager)
    executor = BacktestExecutor(server_manager, account_manager)
    
    # Initialize lab configurator for test configurations
    configurator = LabConfigurator()
    configurator.register_server_config("srv01", 50, 5)
    
    # Get accounts for testing
    test_accounts = account_manager.find_test_accounts("srv01")
    
    print("1. Testing execution submission:")
    
    # Create test lab configuration
    config = configurator.create_lab_configuration(
        template_name="standard",
        lab_id="test-exec-001",
        lab_name="Test Execution Lab",
        script_id="script-123",
        server_id="srv01",
        market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
        exchange_code="BINANCEFUTURES",
        account_id="test_account_1"  # Use a test account
    )
    
    # Submit execution
    execution_id = executor.submit_execution(
        lab_configuration=config,
        priority=ExecutionPriority.HIGH,
        timeout_minutes=60
    )
    
    print(f"  ✓ Submitted execution: {execution_id}")
    print(f"    Lab ID: {config.lab_id}")
    print(f"    Algorithm: {config.algorithm_config.algorithm.value}")
    print(f"    Generations: {config.algorithm_config.max_generations}")
    
    print("\n2. Testing execution processing:")
    
    # Process one iteration of the queue
    executor._process_execution_queue()
    
    # Check status
    status = executor.get_execution_status(config.lab_id)
    print(f"  ✓ Execution status: {status.value if status else 'None'}")
    
    # Wait for execution to start
    time.sleep(2)
    
    # Check progress
    progress = executor.get_execution_progress(config.lab_id)
    if progress:
        print(f"  ✓ Progress: {progress.progress_percentage:.1f}% ({progress.current_generation}/{progress.max_generations})")
    
    print("\n3. Testing execution monitoring:")
    
    # Wait for execution to complete (mock execution is fast)
    max_wait = 30
    wait_time = 0
    while wait_time < max_wait:
        executor._update_execution_progress()
        status = executor.get_execution_status(config.lab_id)
        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
            break
        time.sleep(1)
        wait_time += 1
    
    # Get final result
    result = executor.get_execution_result(config.lab_id)
    if result:
        print(f"  ✓ Execution completed: {result.status.value}")
        print(f"    Duration: {result.total_duration:.1f} seconds")
        print(f"    Generations: {result.total_generations}")
        print(f"    Best fitness: {result.best_fitness:.2f}")
        if result.result_data:
            print(f"    Results collected: {len(result.result_data)} fields")
    
    print("\n4. Testing multiple executions:")
    
    # Create additional test configurations
    configs = []
    for i in range(3):
        test_config = configurator.create_lab_configuration(
            template_name="high_frequency",
            lab_id=f"test-exec-{i+2:03d}",
            lab_name=f"Test Lab {i+2}",
            script_id="script-456",
            server_id="srv01",
            market_tag=f"BINANCE_ETH_USDT",
            exchange_code="BINANCE",
            account_id="test_account_1",
            max_generations=10  # Faster for testing
        )
        configs.append(test_config)
        
        # Submit execution
        exec_id = executor.submit_execution(
            lab_configuration=test_config,
            priority=ExecutionPriority.NORMAL
        )
        print(f"  ✓ Submitted execution {i+2}: {exec_id}")
    
    print("\n5. Testing execution summary:")
    
    summary = executor.get_execution_summary()
    print(f"  Total executions: {summary['total_executions']}")
    print(f"  Active executions: {summary['active_executions']}")
    print(f"  Queued executions: {summary['queued_executions']}")
    print(f"  Status distribution: {summary['status_distribution']}")
    if summary['average_execution_time'] > 0:
        print(f"  Average execution time: {summary['average_execution_time']:.1f} seconds")
    
    print("\n6. Testing execution cancellation:")
    
    # Cancel a queued execution
    if configs:
        cancel_lab_id = configs[0].lab_id
        success = executor.cancel_execution(cancel_lab_id)
        print(f"  ✓ Cancellation result: {success}")
        
        # Check status after cancellation
        status = executor.get_execution_status(cancel_lab_id)
        print(f"  ✓ Status after cancellation: {status.value if status else 'None'}")
    
    print("\n" + "=" * 50)
    print("Backtest execution system test completed!")
    print("Key features demonstrated:")
    print("  - Execution request submission and queuing")
    print("  - Priority-based execution scheduling")
    print("  - Progress monitoring and status tracking")
    print("  - Result collection and storage")
    print("  - Concurrent execution management")
    print("  - Execution cancellation and cleanup")

if __name__ == "__main__":
    main()