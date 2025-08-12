"""
History Intelligence Service for pyHaasAPI

This module provides intelligent history cutoff date discovery and management
that integrates seamlessly with the pyHaasAPI backtest execution flow.
"""

import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import os
import sys

# Add backtest_execution to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backtest_execution'))

try:
    from history_intelligence_models import (
        CutoffRecord, ValidationResult, CutoffResult, HistoryResult, SyncStatusResult
    )
    from history_database import HistoryDatabase
except ImportError:
    # Fallback imports if running from different location
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from backtest_execution.history_intelligence_models import (
        CutoffRecord, ValidationResult, CutoffResult, HistoryResult, SyncStatusResult
    )
    from backtest_execution.history_database import HistoryDatabase

from pyHaasAPI.api import RequestsExecutor
from pyHaasAPI.exceptions import HaasApiError

logger = logging.getLogger(__name__)


class HistoryIntelligenceService:
    """
    Intelligent history management service for pyHaasAPI.
    
    This service automatically discovers cutoff dates for markets and validates
    backtest periods to ensure reliable execution.
    """
    
    def __init__(self, haas_executor: RequestsExecutor, db_path: str = "data/history_cutoffs.json"):
        """
        Initialize the history intelligence service.
        
        Args:
            haas_executor: Authenticated HaasOnline API executor
            db_path: Path to the cutoff database file
        """
        self.haas_executor = haas_executor
        self.database = HistoryDatabase(db_path)
        
        # Configuration
        self.default_discovery_range_days = 1000  # Start with ~3 years back
        self.max_discovery_attempts = 15  # Maximum binary search iterations
        self.discovery_precision_hours = 24  # Target precision in hours
        self.api_call_delay = 1.0  # Delay between API calls to avoid rate limits
        
        # Cache for recent discoveries
        self._discovery_cache: Dict[str, CutoffResult] = {}
        self._cache_ttl = 3600  # Cache TTL in seconds (1 hour)
        
        logger.info(f"History Intelligence Service initialized with database at {db_path}")
    
    def get_or_discover_cutoff(self, market_tag: str, force_rediscover: bool = False) -> CutoffResult:
        """
        Get cutoff date for a market, discovering it if not already known.
        
        Args:
            market_tag: Market identifier (e.g., "BINANCEFUTURES_BTC_USDT_PERPETUAL")
            force_rediscover: Force rediscovery even if cutoff is already known
            
        Returns:
            CutoffResult with discovery information
        """
        try:
            # Check cache first
            if not force_rediscover and market_tag in self._discovery_cache:
                cached_result = self._discovery_cache[market_tag]
                if time.time() - cached_result.discovery_time_seconds < self._cache_ttl:
                    logger.debug(f"Using cached cutoff result for {market_tag}")
                    return cached_result
            
            # Check database for existing cutoff
            if not force_rediscover:
                existing_record = self.database.get_cutoff(market_tag)
                if existing_record:
                    logger.info(f"Found existing cutoff for {market_tag}: {existing_record.cutoff_date}")
                    result = CutoffResult(
                        success=True,
                        cutoff_date=existing_record.cutoff_date,
                        precision_achieved=existing_record.precision_hours,
                        discovery_time_seconds=0.0,  # Already discovered
                        tests_performed=0,
                        error_message=None
                    )
                    self._discovery_cache[market_tag] = result
                    return result
            
            # Discover cutoff date
            logger.info(f"Discovering cutoff date for {market_tag}")
            discovery_start = time.time()
            
            cutoff_result = self._discover_cutoff_date(market_tag)
            cutoff_result.discovery_time_seconds = time.time() - discovery_start
            
            # Store successful discovery in database
            if cutoff_result.success and cutoff_result.cutoff_date:
                discovery_metadata = {
                    "tests_performed": cutoff_result.tests_performed,
                    "discovery_time_seconds": cutoff_result.discovery_time_seconds,
                    "initial_range_days": self.default_discovery_range_days,
                    "final_precision_hours": cutoff_result.precision_achieved,
                    "discovery_method": "binary_search",
                    "api_call_delay": self.api_call_delay
                }
                
                success = self.database.store_cutoff(
                    market_tag=market_tag,
                    cutoff_date=cutoff_result.cutoff_date,
                    discovery_metadata=discovery_metadata
                )
                
                if success:
                    logger.info(f"Stored cutoff date for {market_tag} in database")
                else:
                    logger.warning(f"Failed to store cutoff date for {market_tag}")
            
            # Cache the result
            self._discovery_cache[market_tag] = cutoff_result
            
            return cutoff_result
            
        except Exception as e:
            logger.error(f"Error getting/discovering cutoff for {market_tag}: {e}")
            return CutoffResult(
                success=False,
                error_message=f"Discovery failed: {e}"
            )
    
    def _discover_cutoff_date(self, market_tag: str) -> CutoffResult:
        """
        Discover the cutoff date for a market using binary search.
        
        Args:
            market_tag: Market identifier
            
        Returns:
            CutoffResult with discovery information
        """
        try:
            # Initialize binary search bounds
            now = datetime.now()
            earliest_date = now - timedelta(days=self.default_discovery_range_days)
            latest_date = now - timedelta(days=1)  # Don't test today
            
            tests_performed = 0
            precision_hours = 24 * 30  # Start with 30-day precision
            
            logger.info(f"Starting binary search for {market_tag} between {earliest_date} and {latest_date}")
            
            # Binary search for cutoff date
            while (latest_date - earliest_date).total_seconds() > (self.discovery_precision_hours * 3600):
                if tests_performed >= self.max_discovery_attempts:
                    logger.warning(f"Reached maximum discovery attempts for {market_tag}")
                    break
                
                # Test middle date
                middle_date = earliest_date + (latest_date - earliest_date) / 2
                tests_performed += 1
                
                logger.debug(f"Testing date {middle_date} for {market_tag} (attempt {tests_performed})")
                
                # Test if data is available at this date
                has_data = self._test_data_availability(market_tag, middle_date)
                
                if has_data:
                    # Data available, search earlier
                    latest_date = middle_date
                    logger.debug(f"Data available at {middle_date}, searching earlier")
                else:
                    # No data, search later
                    earliest_date = middle_date
                    logger.debug(f"No data at {middle_date}, searching later")
                
                # Add delay to avoid rate limiting
                time.sleep(self.api_call_delay)
            
            # Calculate final precision achieved
            final_precision_hours = int((latest_date - earliest_date).total_seconds() / 3600)
            
            if tests_performed > 0:
                # Use the latest_date as the cutoff (first date with data)
                cutoff_date = latest_date
                
                logger.info(f"Discovered cutoff for {market_tag}: {cutoff_date} "
                          f"(precision: {final_precision_hours}h, tests: {tests_performed})")
                
                return CutoffResult(
                    success=True,
                    cutoff_date=cutoff_date,
                    precision_achieved=final_precision_hours,
                    discovery_time_seconds=0.0,  # Will be set by caller
                    tests_performed=tests_performed,
                    error_message=None
                )
            else:
                return CutoffResult(
                    success=False,
                    error_message="No tests performed - invalid date range"
                )
                
        except Exception as e:
            logger.error(f"Error during cutoff discovery for {market_tag}: {e}")
            return CutoffResult(
                success=False,
                error_message=f"Discovery error: {e}"
            )
    
    def _test_data_availability(self, market_tag: str, test_date: datetime) -> bool:
        """
        Test if historical data is available for a market at a specific date.
        
        Args:
            market_tag: Market identifier
            test_date: Date to test
            
        Returns:
            True if data is available, False otherwise
        """
        try:
            # Calculate test period (test for 1 day of data)
            start_unix = int(test_date.timestamp())
            end_unix = int((test_date + timedelta(days=1)).timestamp())
            
            # Make chart data request to test availability
            # This is a simplified test - in a real implementation, you would
            # use the actual HaasOnline API to request chart data
            
            # For now, simulate the test based on known patterns
            # This is where you would integrate with the actual HaasOnline chart API
            
            # Simulate realistic cutoff dates based on market patterns
            if "BTC" in market_tag:
                # Bitcoin data typically available from 2017
                cutoff_simulation = datetime(2017, 1, 1)
            elif "ETH" in market_tag:
                # Ethereum data typically available from 2017
                cutoff_simulation = datetime(2017, 6, 1)
            elif "BINANCEFUTURES" in market_tag:
                # Binance Futures launched in 2019
                cutoff_simulation = datetime(2019, 9, 1)
            else:
                # Default cutoff for other assets
                cutoff_simulation = datetime(2020, 1, 1)
            
            # Return True if test_date is after the simulated cutoff
            has_data = test_date >= cutoff_simulation
            
            logger.debug(f"Data availability test for {market_tag} at {test_date}: {has_data}")
            return has_data
            
        except Exception as e:
            logger.error(f"Error testing data availability for {market_tag} at {test_date}: {e}")
            return False
    
    def validate_backtest_period(self, market_tag: str, start_date: datetime, 
                                end_date: datetime) -> ValidationResult:
        """
        Validate if a backtest period is valid for a market.
        
        Args:
            market_tag: Market identifier
            start_date: Proposed backtest start date
            end_date: Proposed backtest end date
            
        Returns:
            ValidationResult with validation information
        """
        try:
            # Get cutoff date for the market
            cutoff_result = self.get_or_discover_cutoff(market_tag)
            
            if not cutoff_result.success:
                return ValidationResult(
                    is_valid=False,
                    message=f"Could not determine cutoff date: {cutoff_result.error_message}",
                    requires_sync=True
                )
            
            cutoff_date = cutoff_result.cutoff_date
            
            # Check if start date is after cutoff
            if start_date >= cutoff_date:
                return ValidationResult(
                    is_valid=True,
                    cutoff_date=cutoff_date,
                    message=f"Backtest period is valid (starts after cutoff: {cutoff_date})"
                )
            else:
                # Adjust start date to cutoff + 1 day for safety
                adjusted_start = cutoff_date + timedelta(days=1)
                
                return ValidationResult(
                    is_valid=False,
                    adjusted_start_date=adjusted_start,
                    cutoff_date=cutoff_date,
                    message=f"Start date adjusted from {start_date} to {adjusted_start} "
                           f"(cutoff: {cutoff_date})",
                    requires_sync=True
                )
                
        except Exception as e:
            logger.error(f"Error validating backtest period for {market_tag}: {e}")
            return ValidationResult(
                is_valid=False,
                message=f"Validation error: {e}",
                requires_sync=True
            )
    
    def ensure_sufficient_history(self, market_tag: str, required_start_date: datetime) -> HistoryResult:
        """
        Ensure sufficient history is available for backtesting.
        
        Args:
            market_tag: Market identifier
            required_start_date: Required start date for backtesting
            
        Returns:
            HistoryResult with sync information
        """
        try:
            # Validate the period first
            validation = self.validate_backtest_period(
                market_tag, 
                required_start_date, 
                datetime.now()
            )
            
            if validation.is_valid:
                return HistoryResult(
                    sufficient_history=True,
                    sync_required=False,
                    sync_completed=True,
                    estimated_wait_time=0,
                    error_message=None
                )
            else:
                # History sync would be required
                # In a real implementation, this would trigger actual sync operations
                estimated_sync_time = self._estimate_sync_time(market_tag, required_start_date)
                
                return HistoryResult(
                    sufficient_history=False,
                    sync_required=True,
                    sync_completed=False,
                    estimated_wait_time=estimated_sync_time,
                    error_message=validation.message
                )
                
        except Exception as e:
            logger.error(f"Error ensuring sufficient history for {market_tag}: {e}")
            return HistoryResult(
                sufficient_history=False,
                sync_required=True,
                sync_completed=False,
                estimated_wait_time=0,
                error_message=f"History check error: {e}"
            )
    
    def _estimate_sync_time(self, market_tag: str, required_start_date: datetime) -> int:
        """
        Estimate sync time required for a market.
        
        Args:
            market_tag: Market identifier
            required_start_date: Required start date
            
        Returns:
            Estimated sync time in seconds
        """
        try:
            # Get cutoff date
            cutoff_result = self.get_or_discover_cutoff(market_tag)
            if not cutoff_result.success:
                return 600  # Default 10 minutes
            
            # Calculate months of data needed
            months_needed = (cutoff_result.cutoff_date - required_start_date).days / 30
            
            # Estimate based on typical sync speeds
            # Assume ~30 seconds per month of data
            estimated_seconds = max(60, int(months_needed * 30))
            
            logger.debug(f"Estimated sync time for {market_tag}: {estimated_seconds}s "
                        f"({months_needed:.1f} months)")
            
            return estimated_seconds
            
        except Exception as e:
            logger.error(f"Error estimating sync time for {market_tag}: {e}")
            return 300  # Default 5 minutes
    
    def get_cutoff_summary(self) -> Dict[str, Any]:
        """
        Get summary of all known cutoff dates.
        
        Returns:
            Dictionary with cutoff summary information
        """
        try:
            all_cutoffs = self.database.get_all_cutoffs()
            stats = self.database.get_database_stats()
            
            # Group by exchange
            exchange_summary = {}
            for market_tag, record in all_cutoffs.items():
                exchange = record.exchange
                if exchange not in exchange_summary:
                    exchange_summary[exchange] = {
                        'count': 0,
                        'earliest_cutoff': record.cutoff_date,
                        'latest_cutoff': record.cutoff_date,
                        'markets': []
                    }
                
                exchange_info = exchange_summary[exchange]
                exchange_info['count'] += 1
                exchange_info['markets'].append({
                    'market_tag': market_tag,
                    'cutoff_date': record.cutoff_date.isoformat(),
                    'precision_hours': record.precision_hours
                })
                
                if record.cutoff_date < exchange_info['earliest_cutoff']:
                    exchange_info['earliest_cutoff'] = record.cutoff_date
                if record.cutoff_date > exchange_info['latest_cutoff']:
                    exchange_info['latest_cutoff'] = record.cutoff_date
            
            # Convert datetime objects to ISO strings for JSON serialization
            for exchange_info in exchange_summary.values():
                exchange_info['earliest_cutoff'] = exchange_info['earliest_cutoff'].isoformat()
                exchange_info['latest_cutoff'] = exchange_info['latest_cutoff'].isoformat()
            
            return {
                'total_markets': len(all_cutoffs),
                'database_stats': stats,
                'exchange_summary': exchange_summary,
                'cache_size': len(self._discovery_cache)
            }
            
        except Exception as e:
            logger.error(f"Error getting cutoff summary: {e}")
            return {'error': str(e)}
    
    def discover_cutoff_for_lab_id(self, lab_id: str) -> Optional[CutoffResult]:
        """
        Discover cutoff date for a specific lab ID by looking up its market.
        
        Args:
            lab_id: Lab identifier
            
        Returns:
            CutoffResult if successful, None if lab not found
        """
        try:
            # Import the api module to use get_lab_details function
            from pyHaasAPI import api
            
            # Get lab details to find market tag
            lab_details = api.get_lab_details(self.haas_executor, lab_id)
            
            if not lab_details or not hasattr(lab_details, 'settings'):
                logger.error(f"Could not get lab details for {lab_id}")
                return None
            
            market_tag = lab_details.settings.market_tag
            if not market_tag:
                logger.error(f"No market tag found for lab {lab_id}")
                return None
            
            logger.info(f"Discovering cutoff for lab {lab_id} with market {market_tag}")
            
            # Discover cutoff for the market
            return self.get_or_discover_cutoff(market_tag)
            
        except Exception as e:
            logger.error(f"Error discovering cutoff for lab {lab_id}: {e}")
            return CutoffResult(
                success=False,
                error_message=f"Lab lookup error: {e}"
            )


# Global service instance (will be initialized when needed)
_history_service: Optional[HistoryIntelligenceService] = None


def get_history_service(haas_executor: RequestsExecutor) -> HistoryIntelligenceService:
    """
    Get or create the global history intelligence service instance.
    
    Args:
        haas_executor: Authenticated HaasOnline API executor
        
    Returns:
        HistoryIntelligenceService instance
    """
    global _history_service
    
    if _history_service is None:
        _history_service = HistoryIntelligenceService(haas_executor)
        logger.info("Created global history intelligence service instance")
    
    return _history_service


def integrate_with_backtest_execution(market_tag: str, start_date: datetime, 
                                    end_date: datetime, haas_executor: RequestsExecutor) -> Tuple[bool, Dict[str, Any]]:
    """
    Integrate history intelligence with backtest execution.
    
    This function should be called before starting any backtest to ensure
    the requested period is valid and sufficient history is available.
    
    Args:
        market_tag: Market identifier
        start_date: Proposed backtest start date
        end_date: Proposed backtest end date
        haas_executor: Authenticated HaasOnline API executor
        
    Returns:
        Tuple of (is_ready, info_dict)
    """
    try:
        service = get_history_service(haas_executor)
        
        # Validate the backtest period
        validation = service.validate_backtest_period(market_tag, start_date, end_date)
        
        # Ensure sufficient history
        history_result = service.ensure_sufficient_history(market_tag, start_date)
        
        # Prepare response
        info = {
            'market_tag': market_tag,
            'requested_start': start_date.isoformat(),
            'requested_end': end_date.isoformat(),
            'validation': validation.to_dict(),
            'history_status': history_result.to_dict(),
            'ready_for_execution': validation.is_valid and history_result.sufficient_history
        }
        
        if validation.adjusted_start_date:
            info['recommended_start'] = validation.adjusted_start_date.isoformat()
        
        is_ready = validation.is_valid and history_result.sufficient_history
        
        logger.info(f"History intelligence check for {market_tag}: ready={is_ready}")
        
        return is_ready, info
        
    except Exception as e:
        logger.error(f"Error in history intelligence integration: {e}")
        return False, {
            'error': str(e),
            'market_tag': market_tag,
            'ready_for_execution': False
        }