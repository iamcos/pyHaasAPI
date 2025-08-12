"""
History Intelligence Endpoints for MCP Server

This module provides REST API endpoints for the history intelligence functionality,
allowing clients to discover cutoff dates and validate backtest periods.
"""

import logging
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import sys
import os

# Add pyHaasAPI to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pyHaasAPI.enhanced_execution import get_enhanced_executor, EnhancedExecutionResult
from pyHaasAPI.history_intelligence import get_history_service
from pyHaasAPI.api import RequestsExecutor

logger = logging.getLogger(__name__)


# Request/Response Models
class DiscoverCutoffRequest(BaseModel):
    """Request to discover cutoff date for a lab"""
    lab_id: str = Field(description="Lab identifier")
    force_rediscover: bool = Field(default=False, description="Force rediscovery even if already known")


class ValidateBacktestPeriodRequest(BaseModel):
    """Request to validate a backtest period"""
    lab_id: str = Field(description="Lab identifier")
    start_date: str = Field(description="Start date in ISO format")
    end_date: str = Field(description="End date in ISO format")


class ExecuteBacktestRequest(BaseModel):
    """Request to execute backtest with history intelligence"""
    lab_id: str = Field(description="Lab identifier")
    start_date: str = Field(description="Start date in ISO format")
    end_date: str = Field(description="End date in ISO format")
    send_email: bool = Field(default=False, description="Send email notification")
    auto_adjust: bool = Field(default=True, description="Auto-adjust periods if needed")


class BulkDiscoverRequest(BaseModel):
    """Request to discover cutoffs for multiple labs"""
    lab_ids: List[str] = Field(description="List of lab identifiers")


class CutoffDiscoveryResponse(BaseModel):
    """Response for cutoff discovery"""
    success: bool
    lab_id: str
    market_tag: Optional[str] = None
    lab_name: Optional[str] = None
    cutoff_date: Optional[str] = None
    precision_achieved_hours: Optional[int] = None
    discovery_time_seconds: Optional[float] = None
    tests_performed: Optional[int] = None
    error_message: Optional[str] = None


class ValidationResponse(BaseModel):
    """Response for backtest period validation"""
    success: bool
    lab_id: str
    lab_name: Optional[str] = None
    market_tag: Optional[str] = None
    requested_start: str
    requested_end: str
    is_valid: bool
    message: str
    requires_sync: bool
    cutoff_date: Optional[str] = None
    recommended_start: Optional[str] = None
    adjustment_days: Optional[int] = None
    error: Optional[str] = None


class ExecutionResponse(BaseModel):
    """Response for enhanced backtest execution"""
    success: bool
    lab_id: str
    market_tag: str
    original_start_date: str
    actual_start_date: str
    end_date: str
    execution_started: bool
    history_intelligence_used: bool
    cutoff_date: Optional[str] = None
    adjustments_made: List[str]
    execution_time: float
    error_message: Optional[str] = None


def register_history_intelligence_endpoints(app, haas_executor: RequestsExecutor):
    """
    Register history intelligence endpoints with the FastAPI app.
    
    Args:
        app: FastAPI application instance
        haas_executor: Authenticated HaasOnline API executor
    """
    
    @app.post("/discover_cutoff", response_model=CutoffDiscoveryResponse)
    async def discover_cutoff(request: DiscoverCutoffRequest):
        """
        Discover cutoff date for a specific lab.
        
        This endpoint discovers the earliest date for which historical data
        is available for the market used by the specified lab.
        """
        try:
            logger.info(f"Discovering cutoff for lab {request.lab_id}")
            
            executor = get_enhanced_executor(haas_executor)
            result = executor.discover_cutoff_for_lab(request.lab_id)
            
            return CutoffDiscoveryResponse(**result)
            
        except Exception as e:
            logger.error(f"Error in discover_cutoff endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/validate_backtest_period", response_model=ValidationResponse)
    async def validate_backtest_period(request: ValidateBacktestPeriodRequest):
        """
        Validate if a backtest period is valid for a lab.
        
        This endpoint checks if the requested backtest period has sufficient
        historical data available and provides recommendations if adjustments are needed.
        """
        try:
            logger.info(f"Validating backtest period for lab {request.lab_id}")
            
            executor = get_enhanced_executor(haas_executor)
            result = executor.validate_lab_backtest_period(
                request.lab_id, 
                request.start_date, 
                request.end_date
            )
            
            return ValidationResponse(**result)
            
        except Exception as e:
            logger.error(f"Error in validate_backtest_period endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/execute_backtest_intelligent", response_model=ExecutionResponse)
    async def execute_backtest_intelligent(request: ExecuteBacktestRequest):
        """
        Execute a backtest with integrated history intelligence.
        
        This endpoint automatically validates the backtest period, adjusts it if necessary,
        and ensures sufficient historical data is available before starting the backtest.
        """
        try:
            logger.info(f"Executing intelligent backtest for lab {request.lab_id}")
            
            executor = get_enhanced_executor(haas_executor)
            result = executor.execute_backtest_with_intelligence(
                request.lab_id,
                request.start_date,
                request.end_date,
                request.send_email,
                request.auto_adjust
            )
            
            # Convert EnhancedExecutionResult to response format
            response_data = {
                'success': result.success,
                'lab_id': result.lab_id,
                'market_tag': result.market_tag,
                'original_start_date': result.original_start_date.isoformat(),
                'actual_start_date': result.actual_start_date.isoformat(),
                'end_date': result.end_date.isoformat(),
                'execution_started': result.execution_started,
                'history_intelligence_used': result.history_intelligence_used,
                'adjustments_made': result.adjustments_made,
                'execution_time': result.execution_time,
                'error_message': result.error_message
            }
            
            if result.cutoff_date:
                response_data['cutoff_date'] = result.cutoff_date.isoformat()
            
            return ExecutionResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Error in execute_backtest_intelligent endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/bulk_discover_cutoffs")
    async def bulk_discover_cutoffs(request: BulkDiscoverRequest):
        """
        Discover cutoff dates for multiple labs in bulk.
        
        This endpoint efficiently discovers cutoff dates for multiple labs,
        useful for batch processing or system initialization.
        """
        try:
            logger.info(f"Bulk discovering cutoffs for {len(request.lab_ids)} labs")
            
            executor = get_enhanced_executor(haas_executor)
            result = executor.bulk_discover_cutoffs(request.lab_ids)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk_discover_cutoffs endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/history_summary")
    async def get_history_summary():
        """
        Get summary of all known cutoff dates and history intelligence data.
        
        This endpoint provides an overview of the history intelligence database,
        including statistics by exchange and market.
        """
        try:
            logger.info("Getting history intelligence summary")
            
            executor = get_enhanced_executor(haas_executor)
            result = executor.get_history_summary()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in get_history_summary endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/discover_cutoff_by_lab/{lab_id}")
    async def discover_cutoff_by_lab_id(lab_id: str, force_rediscover: bool = False):
        """
        Discover cutoff date for a lab using path parameter.
        
        This is a convenience endpoint that allows discovering cutoff dates
        using a simple GET request with the lab ID in the path.
        """
        try:
            logger.info(f"Discovering cutoff for lab {lab_id} (path param)")
            
            executor = get_enhanced_executor(haas_executor)
            result = executor.discover_cutoff_for_lab(lab_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in discover_cutoff_by_lab_id endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/validate_lab_period/{lab_id}")
    async def validate_lab_period_get(
        lab_id: str, 
        start_date: str, 
        end_date: str
    ):
        """
        Validate backtest period using GET request with query parameters.
        
        This is a convenience endpoint for simple validation requests.
        """
        try:
            logger.info(f"Validating period for lab {lab_id} (GET)")
            
            executor = get_enhanced_executor(haas_executor)
            result = executor.validate_lab_backtest_period(lab_id, start_date, end_date)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in validate_lab_period_get endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Add a health check endpoint for the history intelligence system
    @app.get("/history_intelligence_health")
    async def history_intelligence_health():
        """
        Health check for the history intelligence system.
        
        Returns status information about the history intelligence components.
        """
        try:
            service = get_history_service(haas_executor)
            executor = get_enhanced_executor(haas_executor)
            
            # Get basic stats
            summary = service.get_cutoff_summary()
            
            health_info = {
                'status': 'healthy',
                'service_initialized': service is not None,
                'executor_initialized': executor is not None,
                'database_accessible': 'total_markets' in summary,
                'total_known_cutoffs': summary.get('total_markets', 0),
                'cache_size': summary.get('cache_size', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            return health_info
            
        except Exception as e:
            logger.error(f"Error in history_intelligence_health endpoint: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    logger.info("History intelligence endpoints registered successfully")