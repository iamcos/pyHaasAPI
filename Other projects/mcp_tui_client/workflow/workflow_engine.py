"""
Workflow execution engine.

This module provides the core workflow execution engine with dependency resolution,
validation, error handling, and progress tracking.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import logging
import traceback
import uuid

from .node_base import WorkflowNode, ValidationError
from .workflow_definition import WorkflowDefinition, ExecutionContext
from .node_registry import NodeRegistry, get_global_registry


class ExecutionStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class NodeExecutionStatus(Enum):
    """Individual node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    """Result of node execution."""
    node_id: str
    status: NodeExecutionStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'node_id': self.node_id,
            'status': self.status.value,
            'outputs': self.outputs,
            'error': self.error,
            'execution_time': self.execution_time,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    execution_id: str
    status: ExecutionStatus
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_execution_time: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'workflow_id': self.workflow_id,
            'execution_id': self.execution_id,
            'status': self.status.value,
            'node_results': {node_id: result.to_dict() for node_id, result in self.node_results.items()},
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_execution_time': self.total_execution_time,
            'error': self.error
        }


class WorkflowExecutionError(Exception):
    """Exception raised during workflow execution."""
    pass


class WorkflowEngine:
    """Workflow execution engine with dependency resolution and resource management."""
    
    def __init__(self, node_registry: Optional[NodeRegistry] = None, 
                 max_concurrent_nodes: int = 4, logger: Optional[logging.Logger] = None):
        """Initialize workflow engine."""
        self.node_registry = node_registry or get_global_registry()
        self.max_concurrent_nodes = max_concurrent_nodes
        self.logger = logger or logging.getLogger(__name__)
        
        # Execution state
        self._running_executions: Dict[str, asyncio.Task] = {}
        self._execution_semaphore = asyncio.Semaphore(max_concurrent_nodes)
        self._cancelled_executions: Set[str] = set()
        
        # Metrics
        self._execution_metrics: Dict[str, Dict[str, Any]] = {}
    
    async def execute_workflow(self, workflow: WorkflowDefinition, 
                             execution_context: Optional[ExecutionContext] = None,
                             progress_callback: Optional[Callable] = None) -> WorkflowResult:
        """Execute a complete workflow."""
        execution_id = str(uuid.uuid4())
        
        if execution_context is None:
            execution_context = ExecutionContext(
                workflow_id=workflow.workflow_id,
                execution_id=execution_id,
                progress_callback=progress_callback
            )
        
        # Create workflow result
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
            start_time=datetime.now()
        )
        
        try:
            self.logger.info(f"Starting workflow execution: {workflow.workflow_id}")
            
            # Validate workflow before execution
            validation_errors = self.validate_workflow(workflow)
            if validation_errors:
                error_msg = f"Workflow validation failed: {'; '.join([e.message for e in validation_errors])}"
                result.status = ExecutionStatus.FAILED
                result.error = error_msg
                return result
            
            # Update status
            result.status = ExecutionStatus.RUNNING
            
            # Get execution order
            execution_order = workflow.get_execution_order()
            total_nodes = len(execution_order)
            
            self.logger.info(f"Executing {total_nodes} nodes in workflow")
            
            # Execute nodes in dependency order
            completed_nodes = 0
            
            for node_id in execution_order:
                # Check if execution was cancelled
                if execution_id in self._cancelled_executions:
                    result.status = ExecutionStatus.CANCELLED
                    break
                
                node = workflow.get_node(node_id)
                if not node:
                    continue
                
                # Execute node
                node_result = await self._execute_node(node, execution_context, workflow)
                result.node_results[node_id] = node_result
                
                # Update progress
                completed_nodes += 1
                progress = (completed_nodes / total_nodes) * 100
                
                if progress_callback:
                    progress_callback(execution_context, f"Completed {completed_nodes}/{total_nodes} nodes ({progress:.1f}%)")
                
                # Check if node failed and should stop execution
                if node_result.status == NodeExecutionStatus.FAILED:
                    if self._should_stop_on_node_failure(node, workflow):
                        result.status = ExecutionStatus.FAILED
                        result.error = f"Node {node_id} failed: {node_result.error}"
                        break
            
            # Determine final status
            if result.status == ExecutionStatus.RUNNING:
                failed_nodes = [r for r in result.node_results.values() if r.status == NodeExecutionStatus.FAILED]
                if failed_nodes:
                    result.status = ExecutionStatus.FAILED
                    result.error = f"{len(failed_nodes)} nodes failed"
                else:
                    result.status = ExecutionStatus.COMPLETED
            
            result.end_time = datetime.now()
            result.total_execution_time = (result.end_time - result.start_time).total_seconds()
            
            self.logger.info(f"Workflow execution completed: {result.status.value} in {result.total_execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution error: {str(e)}")
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            if result.start_time:
                result.total_execution_time = (result.end_time - result.start_time).total_seconds()
            return result
        
        finally:
            # Cleanup
            if execution_id in self._cancelled_executions:
                self._cancelled_executions.remove(execution_id)
    
    async def execute_node(self, node: WorkflowNode, context: ExecutionContext) -> NodeResult:
        """Execute a single node."""
        return await self._execute_node(node, context)
    
    async def _execute_node(self, node: WorkflowNode, context: ExecutionContext, 
                          workflow: Optional[WorkflowDefinition] = None) -> NodeResult:
        """Execute a single node with resource management."""
        node_result = NodeResult(
            node_id=node.node_id,
            status=NodeExecutionStatus.PENDING,
            start_time=datetime.now()
        )
        
        try:
            # Acquire execution semaphore
            async with self._execution_semaphore:
                self.logger.debug(f"Executing node: {node.node_id} ({node.__class__.__name__})")
                
                node_result.status = NodeExecutionStatus.RUNNING
                context.current_node = node.node_id
                
                # Validate node before execution
                validation_errors = node.validate()
                if validation_errors:
                    error_msg = f"Node validation failed: {'; '.join([e.message for e in validation_errors])}"
                    node_result.status = NodeExecutionStatus.FAILED
                    node_result.error = error_msg
                    return node_result
                
                # Execute node
                start_time = datetime.now()
                outputs = await node.execute(context)
                end_time = datetime.now()
                
                # Store outputs in context
                for port_name, value in outputs.items():
                    context.set_node_output(node.node_id, port_name, value)
                
                node_result.outputs = outputs
                node_result.status = NodeExecutionStatus.COMPLETED
                node_result.execution_time = (end_time - start_time).total_seconds()
                
                # Mark node as completed in context
                context.mark_node_completed(node.node_id)
                
                self.logger.debug(f"Node completed: {node.node_id} in {node_result.execution_time:.2f}s")
                
        except asyncio.CancelledError:
            node_result.status = NodeExecutionStatus.FAILED
            node_result.error = "Execution cancelled"
            context.mark_node_failed(node.node_id)
            
        except Exception as e:
            self.logger.error(f"Node execution error: {node.node_id}: {str(e)}")
            node_result.status = NodeExecutionStatus.FAILED
            node_result.error = str(e)
            context.mark_node_failed(node.node_id)
            
            # Log full traceback for debugging
            self.logger.debug(f"Node error traceback: {traceback.format_exc()}")
        
        finally:
            node_result.end_time = datetime.now()
            if node_result.start_time:
                node_result.execution_time = (node_result.end_time - node_result.start_time).total_seconds()
        
        return node_result
    
    def validate_workflow(self, workflow: WorkflowDefinition) -> List[ValidationError]:
        """Validate workflow before execution."""
        errors = []
        
        # Basic workflow validation
        workflow_errors = workflow.validate()
        errors.extend(workflow_errors)
        
        # Check for unreachable nodes
        try:
            execution_order = workflow.get_execution_order()
            reachable_nodes = set(execution_order)
            all_nodes = set(workflow.nodes.keys())
            unreachable_nodes = all_nodes - reachable_nodes
            
            for node_id in unreachable_nodes:
                errors.append(ValidationError(
                    node_id=node_id,
                    message="Node is unreachable in workflow",
                    error_type="unreachable_node"
                ))
        
        except ValueError as e:
            errors.append(ValidationError(
                node_id="workflow",
                message=str(e),
                error_type="execution_order_error"
            ))
        
        # Validate individual nodes
        for node in workflow.nodes.values():
            node_errors = node.validate()
            errors.extend(node_errors)
        
        # Check for missing node types in registry
        for node in workflow.nodes.values():
            node_type = node.__class__.__name__
            if not self.node_registry.get_node_info(node_type):
                errors.append(ValidationError(
                    node_id=node.node_id,
                    message=f"Node type '{node_type}' not found in registry",
                    error_type="unknown_node_type"
                ))
        
        return errors
    
    async def execute_parallel_nodes(self, nodes: List[WorkflowNode], 
                                   context: ExecutionContext) -> List[NodeResult]:
        """Execute multiple nodes in parallel."""
        tasks = []
        
        for node in nodes:
            task = asyncio.create_task(self._execute_node(node, context))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed node results
        node_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                node_result = NodeResult(
                    node_id=nodes[i].node_id,
                    status=NodeExecutionStatus.FAILED,
                    error=str(result)
                )
                node_results.append(node_result)
            else:
                node_results.append(result)
        
        return node_results
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        if execution_id in self._running_executions:
            task = self._running_executions[execution_id]
            task.cancel()
            self._cancelled_executions.add(execution_id)
            return True
        return False
    
    def pause_execution(self, execution_id: str) -> bool:
        """Pause a running workflow execution."""
        # This would require more complex state management
        # For now, we'll just mark it as cancelled
        return self.cancel_execution(execution_id)
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get the status of a workflow execution."""
        if execution_id in self._running_executions:
            task = self._running_executions[execution_id]
            if task.done():
                if task.cancelled():
                    return ExecutionStatus.CANCELLED
                elif task.exception():
                    return ExecutionStatus.FAILED
                else:
                    return ExecutionStatus.COMPLETED
            else:
                return ExecutionStatus.RUNNING
        return None
    
    def _should_stop_on_node_failure(self, node: WorkflowNode, 
                                   workflow: WorkflowDefinition) -> bool:
        """Determine if workflow should stop when a node fails."""
        # Check if node has any dependent nodes
        # If it does, we should probably stop
        # This is a simplified implementation
        
        for connection in workflow.connections.values():
            if connection.source_node_id == node.node_id:
                # This node has dependents, failure should stop execution
                return True
        
        return False
    
    def get_execution_metrics(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution metrics for a workflow."""
        return self._execution_metrics.get(execution_id)
    
    def _record_execution_metrics(self, execution_id: str, result: WorkflowResult) -> None:
        """Record execution metrics."""
        metrics = {
            'workflow_id': result.workflow_id,
            'execution_id': execution_id,
            'status': result.status.value,
            'total_execution_time': result.total_execution_time,
            'node_count': len(result.node_results),
            'successful_nodes': len([r for r in result.node_results.values() 
                                   if r.status == NodeExecutionStatus.COMPLETED]),
            'failed_nodes': len([r for r in result.node_results.values() 
                               if r.status == NodeExecutionStatus.FAILED]),
            'average_node_time': sum(r.execution_time for r in result.node_results.values()) / len(result.node_results) if result.node_results else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self._execution_metrics[execution_id] = metrics
    
    async def dry_run_workflow(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """Perform a dry run of the workflow without executing nodes."""
        dry_run_result = {
            'workflow_id': workflow.workflow_id,
            'validation_errors': [],
            'execution_plan': [],
            'estimated_duration': 0.0,
            'resource_requirements': {}
        }
        
        # Validate workflow
        validation_errors = self.validate_workflow(workflow)
        dry_run_result['validation_errors'] = [
            {
                'node_id': error.node_id,
                'message': error.message,
                'error_type': error.error_type
            }
            for error in validation_errors
        ]
        
        if not validation_errors:
            try:
                # Get execution order
                execution_order = workflow.get_execution_order()
                
                # Build execution plan
                execution_plan = []
                estimated_duration = 0.0
                
                for node_id in execution_order:
                    node = workflow.get_node(node_id)
                    if node:
                        # Estimate execution time (simplified)
                        estimated_time = self._estimate_node_execution_time(node)
                        estimated_duration += estimated_time
                        
                        execution_plan.append({
                            'node_id': node_id,
                            'node_type': node.__class__.__name__,
                            'estimated_time': estimated_time,
                            'dependencies': list(workflow._dependency_graph.get(node_id, set()))
                        })
                
                dry_run_result['execution_plan'] = execution_plan
                dry_run_result['estimated_duration'] = estimated_duration
                
                # Estimate resource requirements
                dry_run_result['resource_requirements'] = {
                    'max_concurrent_nodes': min(self.max_concurrent_nodes, len(execution_order)),
                    'estimated_memory_mb': len(execution_order) * 50,  # Rough estimate
                    'estimated_cpu_cores': min(4, len(execution_order))
                }
                
            except Exception as e:
                dry_run_result['validation_errors'].append({
                    'node_id': 'workflow',
                    'message': f"Execution planning failed: {str(e)}",
                    'error_type': 'planning_error'
                })
        
        return dry_run_result
    
    def _estimate_node_execution_time(self, node: WorkflowNode) -> float:
        """Estimate execution time for a node (simplified)."""
        # This is a very simplified estimation
        # In practice, you might use historical data or node-specific estimates
        
        node_type = node.__class__.__name__
        
        # Rough estimates based on node type
        time_estimates = {
            'LabNode': 30.0,
            'BacktestNode': 120.0,
            'ParameterOptimizationNode': 300.0,
            'BotNode': 10.0,
            'AnalysisNode': 15.0,
            'MarketDataNode': 5.0,
            'DelayNode': float(node.get_parameter('default_delay', 60)),
            'NotificationNode': 2.0
        }
        
        return time_estimates.get(node_type, 10.0)
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get overall workflow execution statistics."""
        if not self._execution_metrics:
            return {}
        
        metrics_list = list(self._execution_metrics.values())
        
        return {
            'total_executions': len(metrics_list),
            'successful_executions': len([m for m in metrics_list if m['status'] == 'completed']),
            'failed_executions': len([m for m in metrics_list if m['status'] == 'failed']),
            'average_execution_time': sum(m['total_execution_time'] for m in metrics_list) / len(metrics_list),
            'average_node_count': sum(m['node_count'] for m in metrics_list) / len(metrics_list),
            'total_nodes_executed': sum(m['successful_nodes'] for m in metrics_list),
            'total_node_failures': sum(m['failed_nodes'] for m in metrics_list)
        }


class WorkflowScheduler:
    """Scheduler for managing multiple workflow executions."""
    
    def __init__(self, engine: WorkflowEngine, max_concurrent_workflows: int = 2):
        """Initialize workflow scheduler."""
        self.engine = engine
        self.max_concurrent_workflows = max_concurrent_workflows
        self._workflow_queue: asyncio.Queue = asyncio.Queue()
        self._running_workflows: Dict[str, asyncio.Task] = {}
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the workflow scheduler."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    async def stop(self) -> None:
        """Stop the workflow scheduler."""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running workflows
        for task in self._running_workflows.values():
            task.cancel()
        
        if self._running_workflows:
            await asyncio.gather(*self._running_workflows.values(), return_exceptions=True)
    
    async def schedule_workflow(self, workflow: WorkflowDefinition, 
                              context: Optional[ExecutionContext] = None,
                              priority: int = 0) -> str:
        """Schedule a workflow for execution."""
        execution_id = str(uuid.uuid4())
        
        await self._workflow_queue.put({
            'execution_id': execution_id,
            'workflow': workflow,
            'context': context,
            'priority': priority,
            'scheduled_at': datetime.now()
        })
        
        return execution_id
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                # Clean up completed workflows
                completed_workflows = [
                    exec_id for exec_id, task in self._running_workflows.items()
                    if task.done()
                ]
                
                for exec_id in completed_workflows:
                    del self._running_workflows[exec_id]
                
                # Check if we can start new workflows
                if len(self._running_workflows) < self.max_concurrent_workflows:
                    try:
                        # Get next workflow from queue (with timeout)
                        workflow_item = await asyncio.wait_for(
                            self._workflow_queue.get(), timeout=1.0
                        )
                        
                        # Start workflow execution
                        task = asyncio.create_task(
                            self.engine.execute_workflow(
                                workflow_item['workflow'],
                                workflow_item['context']
                            )
                        )
                        
                        self._running_workflows[workflow_item['execution_id']] = task
                        
                    except asyncio.TimeoutError:
                        # No workflows in queue, continue loop
                        pass
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                # Log error but continue running
                logging.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(1.0)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get scheduler queue status."""
        return {
            'queue_size': self._workflow_queue.qsize(),
            'running_workflows': len(self._running_workflows),
            'max_concurrent': self.max_concurrent_workflows,
            'scheduler_running': self._running
        }