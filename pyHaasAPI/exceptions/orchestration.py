"""
Orchestration exceptions for pyHaasAPI v2

Handles errors related to multi-server orchestration, project execution,
and complex workflow coordination.
"""

from .base import HaasAPIError


class OrchestrationError(HaasAPIError):
    """Base exception for orchestration errors"""
    pass


class ProjectExecutionError(OrchestrationError):
    """Error during project execution"""
    pass


class ServerCoordinationError(OrchestrationError):
    """Error in server coordination"""
    pass


class WorkflowError(OrchestrationError):
    """Error in workflow execution"""
    pass


class ConfigurationError(OrchestrationError):
    """Error in orchestration configuration"""
    pass


class ResourceError(OrchestrationError):
    """Error in resource management"""
    pass























