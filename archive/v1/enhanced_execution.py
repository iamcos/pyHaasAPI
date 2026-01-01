"""
Enhanced Backtest Execution with History Intelligence

This module provides enhanced backtest execution that automatically integrates
history intelligence to ensure reliable backtest execution.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import json

from pyHaasAPI_v1.api import RequestsExecutor
from pyHaasAPI_v1.model import LabDetails, StartLabExecutionRequest
from pyHaasAPI_v1.exceptions import HaasApiError
from pyHaasAPI_v1.history_intelligence import get_history_service, integrate_with_backtest_execution

logger = logging.getLogger(__name__)


@dataclass
class EnhancedExecutionResult:
    """Result of enhanced backtest execution"""
    success: bool
    lab_id: str
    market_tag: str
    original_start_date: datetime
    actual_start_date: datetime
    end_date: datetime
    execution_started: bool
    history_intelligence_used: bool
    cutoff_date: Optional[datetime] = None
    adjustments_made: List[str] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.adjustments_made is None:
            self.adjustments_made = []


class EnhancedBacktestExecutor:
    """
    Enhanced backtest executor with integrated history intelligence.
    
    This executor automatically:
    1. Discovers cutoff dates for markets
    2. Validates backtest periods
    3. Adjusts periods if necessary
    4. Ensures sufficient history before execution
    """
    
    def __init__(self, haas_executor: RequestsExecutor):
        """
        Initialize the enhanced executor.
        
        Args:
            haas_executor: Authenticated HaasOnline API executor
        """
        self.haas_executor = haas_executor
        self.history_service = get_history_service(haas_executor)
        
        # Configuration
        self.auto_adjust_periods = True
        self.require_history_validation = True
        self.default_safety_margin_days = 1
        
        logger.info("Enhanced Backtest Executor initialized with history intelligence")
    
    def execute_backtest_with_intelligence(
        self,
        lab_id: str,
        start_date: Union[datetime, str],
        end_date: Union[datetime, str],
        send_email: bool = False,
        auto_adjust: bool = None
    ) -> EnhancedExecutionResult:
        """
        Execute a backtest with integrated history intelligence.
        
        Args:
            lab_id: Lab identifier
            start_date: Backtest start date (datetime or ISO string)
            end_date: Backtest end date (datetime or ISO string)
            send_email: Whether to send email notification
            auto_adjust: Whether to auto-adjust periods (overrides default)
            
        Returns:
            EnhancedExecutionResult with execution details
        """
        execution_start_time = time.time()
        
        try:
            # Parse dates if they're strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            original_start_date = start_date
            adjustments_made = []
            
            logger.info(f"Starting enhanced backtest execution for lab {lab_id}")
            logger.info(f"Requested period: {start_date} to {end_date}")
            
            # Get lab details to find market
            lab_details = self._get_lab_details(lab_id)
            if not lab_details:
                return EnhancedExecutionResult(
                    success=False,
                    lab_id=lab_id,
                    market_tag="unknown",
                    original_start_date=original_start_date,
                    actual_start_date=start_date,
                    end_date=end_date,
                    execution_started=False,
                    history_intelligence_used=False,
                    error_message="Could not retrieve lab details"
                )
            
            market_tag = lab_details.settings.market_tag
            logger.info(f"Lab {lab_id} uses market {market_tag}")
            
            # Use history intelligence to validate and adjust period
            if self.require_history_validation:
                is_ready, history_info = integrate_with_backtest_execution(
                    market_tag, start_date, end_date, self.haas_executor
                )
                
                logger.info(f"History intelligence check: ready={is_ready}")
                
                # Handle adjustments if needed
                auto_adjust_enabled = auto_adjust if auto_adjust is not None else self.auto_adjust_periods
                
                if not is_ready and auto_adjust_enabled:
                    validation = history_info.get('validation', {})
                    
                    if validation.get('adjusted_start_date'):
                        adjusted_start = datetime.fromisoformat(validation['adjusted_start_date'])
                        
                        # Add safety margin
                        adjusted_start += timedelta(days=self.default_safety_margin_days)
                        
                        logger.info(f"Auto-adjusting start date from {start_date} to {adjusted_start}")
                        start_date = adjusted_start
                        adjustments_made.append(f"Start date adjusted to {adjusted_start} due to history cutoff")
                        
                        # Re-validate with adjusted date
                        is_ready, history_info = integrate_with_backtest_execution(
                            market_tag, start_date, end_date, self.haas_executor
                        )
                
                if not is_ready and not auto_adjust_enabled:
                    return EnhancedExecutionResult(
                        success=False,
                        lab_id=lab_id,
                        market_tag=market_tag,
                        original_start_date=original_start_date,
                        actual_start_date=start_date,
                        end_date=end_date,
                        execution_started=False,
                        history_intelligence_used=True,
                        cutoff_date=datetime.fromisoformat(validation.get('cutoff_date')) if validation.get('cutoff_date') else None,
                        adjustments_made=adjustments_made,
                        error_message="Backtest period is invalid and auto-adjustment is disabled"
                    )
            
            # Execute the backtest
            execution_success = self._execute_backtest(lab_id, start_date, end_date, send_email)
            
            execution_time = time.time() - execution_start_time
            
            result = EnhancedExecutionResult(
                success=execution_success,
                lab_id=lab_id,
                market_tag=market_tag,
                original_start_date=original_start_date,
                actual_start_date=start_date,
                end_date=end_date,
                execution_started=execution_success,
                history_intelligence_used=self.require_history_validation,
                adjustments_made=adjustments_made,
                execution_time=execution_time
            )
            
            if self.require_history_validation and 'validation' in history_info:
                validation = history_info['validation']
                if validation.get('cutoff_date'):
                    result.cutoff_date = datetime.fromisoformat(validation['cutoff_date'])
            
            logger.info(f"Enhanced backtest execution completed: success={execution_success}")
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced backtest execution: {e}")
            execution_time = time.time() - execution_start_time
            
            return EnhancedExecutionResult(
                success=False,
                lab_id=lab_id,
                market_tag="unknown",
                original_start_date=original_start_date,
                actual_start_date=start_date,
                end_date=end_date,
                execution_started=False,
                history_intelligence_used=self.require_history_validation,
                adjustments_made=adjustments_made,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _get_lab_details(self, lab_id: str) -> Optional[LabDetails]:
        """Get lab details from HaasOnline API"""
        try:
            from pyHaasAPI_v1 import api
            return api.get_lab_details(self.haas_executor, lab_id)
        except Exception as e:
            logger.error(f"Error getting lab details for {lab_id}: {e}")
            return None
    
    def _execute_backtest(self, lab_id: str, start_date: datetime, 
                         end_date: datetime, send_email: bool) -> bool:
        """Execute the actual backtest"""
        try:
            from pyHaasAPI_v1 import api
            
            # Convert dates to Unix timestamps
            start_unix = int(start_date.timestamp())
            end_unix = int(end_date.timestamp())
            
            # Create execution request
            request = api.StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=start_unix,
                end_unix=end_unix,
                send_email=send_email
            )
            
            # Start the backtest
            result = api.start_lab_execution(self.haas_executor, request)
            
            if hasattr(result, 'Success') and result.Success:
                logger.info(f"Successfully started backtest for lab {lab_id}")
                return True
            else:
                error_msg = getattr(result, 'Error', 'Unknown error')
                logger.error(f"Failed to start backtest for lab {lab_id}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing backtest for lab {lab_id}: {e}")
            return False
    
    def discover_cutoff_for_lab(self, lab_id: str) -> Dict[str, Any]:
        """
        Discover cutoff date for a specific lab.
        
        Args:
            lab_id: Lab identifier
            
        Returns:
            Dictionary with cutoff discovery results
        """
        try:
            logger.info(f"Discovering cutoff date for lab {lab_id}")
            
            # Use the history service to discover cutoff
            cutoff_result = self.history_service.discover_cutoff_for_lab_id(lab_id)
            
            if cutoff_result is None:
                return {
                    'success': False,
                    'lab_id': lab_id,
                    'error': 'Could not find lab or determine market'
                }
            
            result_dict = {
                'success': cutoff_result.success,
                'lab_id': lab_id,
                'cutoff_date': cutoff_result.cutoff_date.isoformat() if cutoff_result.cutoff_date else None,
                'precision_achieved_hours': cutoff_result.precision_achieved,
                'discovery_time_seconds': cutoff_result.discovery_time_seconds,
                'tests_performed': cutoff_result.tests_performed,
                'error_message': cutoff_result.error_message
            }
            
            # Get lab details for additional context
            lab_details = self._get_lab_details(lab_id)
            if lab_details:
                result_dict['market_tag'] = lab_details.settings.market_tag
                result_dict['lab_name'] = lab_details.name
            
            logger.info(f"Cutoff discovery completed for lab {lab_id}: success={cutoff_result.success}")
            return result_dict
            
        except Exception as e:
            logger.error(f"Error discovering cutoff for lab {lab_id}: {e}")
            return {
                'success': False,
                'lab_id': lab_id,
                'error': str(e)
            }
    
    def validate_lab_backtest_period(self, lab_id: str, start_date: Union[datetime, str], 
                                   end_date: Union[datetime, str]) -> Dict[str, Any]:
        """
        Validate a backtest period for a specific lab.
        
        Args:
            lab_id: Lab identifier
            start_date: Proposed start date
            end_date: Proposed end date
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Parse dates if they're strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Get lab details
            lab_details = self._get_lab_details(lab_id)
            if not lab_details:
                return {
                    'success': False,
                    'lab_id': lab_id,
                    'error': 'Could not retrieve lab details'
                }
            
            market_tag = lab_details.settings.market_tag
            
            # Validate using history intelligence
            validation = self.history_service.validate_backtest_period(
                market_tag, start_date, end_date
            )
            
            result = {
                'success': True,
                'lab_id': lab_id,
                'lab_name': lab_details.name,
                'market_tag': market_tag,
                'requested_start': start_date.isoformat(),
                'requested_end': end_date.isoformat(),
                'is_valid': validation.is_valid,
                'message': validation.message,
                'requires_sync': validation.requires_sync
            }
            
            if validation.cutoff_date:
                result['cutoff_date'] = validation.cutoff_date.isoformat()
            
            if validation.adjusted_start_date:
                result['recommended_start'] = validation.adjusted_start_date.isoformat()
                result['adjustment_days'] = (validation.adjusted_start_date - start_date).days
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating backtest period for lab {lab_id}: {e}")
            return {
                'success': False,
                'lab_id': lab_id,
                'error': str(e)
            }
    
    def get_history_summary(self) -> Dict[str, Any]:
        """
        Get summary of history intelligence data.
        
        Returns:
            Dictionary with history summary
        """
        try:
            return self.history_service.get_cutoff_summary()
        except Exception as e:
            logger.error(f"Error getting history summary: {e}")
            return {'error': str(e)}
    
    def bulk_discover_cutoffs(self, lab_ids: List[str]) -> Dict[str, Any]:
        """
        Discover cutoff dates for multiple labs.
        
        Args:
            lab_ids: List of lab identifiers
            
        Returns:
            Dictionary with bulk discovery results
        """
        try:
            results = {}
            successful = 0
            failed = 0
            
            logger.info(f"Starting bulk cutoff discovery for {len(lab_ids)} labs")
            
            for lab_id in lab_ids:
                try:
                    result = self.discover_cutoff_for_lab(lab_id)
                    results[lab_id] = result
                    
                    if result.get('success'):
                        successful += 1
                    else:
                        failed += 1
                        
                    # Add small delay to avoid overwhelming the API
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error discovering cutoff for lab {lab_id}: {e}")
                    results[lab_id] = {
                        'success': False,
                        'lab_id': lab_id,
                        'error': str(e)
                    }
                    failed += 1
            
            summary = {
                'total_labs': len(lab_ids),
                'successful_discoveries': successful,
                'failed_discoveries': failed,
                'results': results
            }
            
            logger.info(f"Bulk cutoff discovery completed: {successful} successful, {failed} failed")
            return summary
            
        except Exception as e:
            logger.error(f"Error in bulk cutoff discovery: {e}")
            return {
                'error': str(e),
                'total_labs': len(lab_ids),
                'successful_discoveries': 0,
                'failed_discoveries': len(lab_ids)
            }


# Global enhanced executor instance
_enhanced_executor: Optional[EnhancedBacktestExecutor] = None


def get_enhanced_executor(haas_executor: RequestsExecutor) -> EnhancedBacktestExecutor:
    """
    Get or create the global enhanced backtest executor.
    
    Args:
        haas_executor: Authenticated HaasOnline API executor
        
    Returns:
        EnhancedBacktestExecutor instance
    """
    global _enhanced_executor
    
    if _enhanced_executor is None:
        _enhanced_executor = EnhancedBacktestExecutor(haas_executor)
        logger.info("Created global enhanced backtest executor instance")
    
    return _enhanced_executor


def execute_backtest_with_intelligence(
    haas_executor: RequestsExecutor,
    lab_id: str,
    start_date: Union[datetime, str],
    end_date: Union[datetime, str],
    send_email: bool = False,
    auto_adjust: bool = True
) -> EnhancedExecutionResult:
    """
    Convenience function to execute a backtest with history intelligence.
    
    Args:
        haas_executor: Authenticated HaasOnline API executor
        lab_id: Lab identifier
        start_date: Backtest start date
        end_date: Backtest end date
        send_email: Whether to send email notification
        auto_adjust: Whether to auto-adjust periods
        
    Returns:
        EnhancedExecutionResult with execution details
    """
    executor = get_enhanced_executor(haas_executor)
    return executor.execute_backtest_with_intelligence(
        lab_id, start_date, end_date, send_email, auto_adjust
    )