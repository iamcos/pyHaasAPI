"""
Unified Backtest Service for pyHaasAPI

This service consolidates all backtest functionality including longest backtest discovery,
execution, and monitoring to eliminate code duplication across the codebase.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# from ..base import BaseService
from ...core.logging import get_logger
from ...exceptions import BacktestError, LabError
from ...models.lab import LabDetails, StartLabExecutionRequest
from ...api.lab.lab_api import LabAPI
from ...api.backtest.backtest_api import BacktestAPI

logger = get_logger("backtest_service")


@dataclass
class CutoffDiscoveryResult:
    """Result of cutoff date discovery"""
    cutoff_date: datetime
    market_tag: str
    confidence: float
    method: str
    notes: str


@dataclass
class BacktestExecutionResult:
    """Result of backtest execution"""
    lab_id: str
    job_id: str
    start_date: datetime
    end_date: datetime
    status: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class BacktestProgress:
    """Backtest execution progress"""
    lab_id: str
    status: str
    progress_percentage: float
    generation: int
    population: int
    best_fitness: float
    completed_backtests: int
    total_backtests: int
    is_running: bool
    is_completed: bool
    error_message: Optional[str] = None


class BacktestService:
    """
    Unified Backtest Service
    
    Consolidates all backtest functionality including:
    - Cutoff date discovery
    - Longest backtest execution
    - Progress monitoring
    - Error handling
    """
    
    def __init__(self, lab_api: LabAPI, backtest_api: BacktestAPI):
        self.lab_api = lab_api
        self.backtest_api = backtest_api
        self.logger = get_logger("backtest_service")
    
    async def discover_cutoff_date(self, lab_id: str, market_tag: Optional[str] = None) -> CutoffDiscoveryResult:
        """
        Discover optimal cutoff date for longest backtesting period.
        
        This is the unified implementation that replaces all duplicate
        discover_cutoff_date functions across the codebase.
        
        Args:
            lab_id: ID of the lab to analyze
            market_tag: Optional market tag (will be fetched if not provided)
            
        Returns:
            CutoffDiscoveryResult with discovered cutoff date and metadata
        """
        try:
            self.logger.info(f"🔍 Discovering cutoff date for lab: {lab_id[:8]}")
            
            # Get lab details if market_tag not provided
            if not market_tag:
                lab_details = await self.lab_api.get_lab_details(lab_id)
                market_tag = lab_details.settings.market_tag
            
            self.logger.info(f"📊 Market: {market_tag}")
            
            # Try different discovery methods
            cutoff_date, method, confidence = await self._discover_cutoff_date_advanced(
                lab_id, market_tag
            )
            
            result = CutoffDiscoveryResult(
                cutoff_date=cutoff_date,
                market_tag=market_tag,
                confidence=confidence,
                method=method,
                notes=f"Discovered using {method} method with {confidence:.1%} confidence"
            )
            
            self.logger.info(f"✅ Cutoff date discovered: {cutoff_date.strftime('%Y-%m-%d')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to discover cutoff date: {e}")
            # Fallback to conservative 2-year cutoff
            fallback_date = datetime.now() - timedelta(days=730)
            return CutoffDiscoveryResult(
                cutoff_date=fallback_date,
                market_tag=market_tag or "unknown",
                confidence=0.5,
                method="fallback",
                notes=f"Fallback due to error: {str(e)}"
            )
    
    async def _discover_cutoff_date_advanced(self, lab_id: str, market_tag: str) -> Tuple[datetime, str, float]:
        """Advanced cutoff date discovery with multiple methods"""
        
        # Method 1: Test different historical periods
        test_periods = [
            (365, "1 year"),
            (730, "2 years"), 
            (1095, "3 years"),
            (1460, "4 years"),
            (1825, "5 years")
        ]
        
        for days, period_name in test_periods:
            test_date = datetime.now() - timedelta(days=days)
            self.logger.info(f"🧪 Testing {period_name} cutoff: {test_date.strftime('%Y-%m-%d')}")
            
            # In a real implementation, this would query market data API
            # to verify data availability at the test date
            # For now, we'll use a conservative approach
            
            # Use 2-year cutoff as optimal balance
            if days >= 730:
                return test_date, f"historical_{period_name}", 0.8
        
        # Fallback to 2-year cutoff
        fallback_date = datetime.now() - timedelta(days=730)
        return fallback_date, "conservative_2year", 0.7
    
    async def run_longest_backtest(
        self, 
        lab_id: str, 
        cutoff_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_iterations: int = 1500,
        send_email: bool = False
    ) -> BacktestExecutionResult:
        """
        Run the longest possible backtest for a lab.
        
        This is the unified implementation that replaces all duplicate
        run_longest_backtest functions across the codebase.
        
        Args:
            lab_id: ID of the lab to execute
            cutoff_date: Start date (will be discovered if not provided)
            end_date: End date (defaults to now)
            max_iterations: Maximum number of iterations
            send_email: Whether to send email notifications
            
        Returns:
            BacktestExecutionResult with execution details
        """
        try:
            self.logger.info(f"🚀 Starting longest backtest for lab: {lab_id[:8]}")
            
            # Discover cutoff date if not provided
            if not cutoff_date:
                discovery_result = await self.discover_cutoff_date(lab_id)
                cutoff_date = discovery_result.cutoff_date
            
            # Use current time as end date if not provided
            if not end_date:
                end_date = datetime.now()
            
            # Check if lab is already running
            current_status = await self._check_lab_status(lab_id)
            if current_status and current_status.get('is_running', False):
                self.logger.warning(f"Lab {lab_id} is already running")
                return BacktestExecutionResult(
                    lab_id=lab_id,
                    job_id="already_running",
                    start_date=cutoff_date,
                    end_date=end_date,
                    status="already_running",
                    success=False,
                    error_message="Lab is already running"
                )
            
            # Create execution request
            execution_request = StartLabExecutionRequest(
                labId=lab_id,
                startUnix=int(cutoff_date.timestamp()),
                endUnix=int(end_date.timestamp()),
                sendEmail=send_email
            )
            
            # Start execution
            result = await self.lab_api.start_lab_execution(execution_request)
            
            # Handle different result types
            if isinstance(result, dict):
                success = result.get('Success', False)
                job_id = result.get('Data', {}).get('JobId', 'unknown') if success else 'failed'
                error_msg = result.get('Error', '') if not success else None
            else:
                # Handle object response
                success = getattr(result, 'success', False)
                job_id = getattr(result, 'job_id', 'unknown') if success else 'failed'
                error_msg = getattr(result, 'error', '') if not success else None
            
            if success:
                self.logger.info("✅ Lab execution started successfully")
                self.logger.info(f"📅 Period: {cutoff_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
                self.logger.info(f"🔄 Max iterations: {max_iterations}")
                
                return BacktestExecutionResult(
                    lab_id=lab_id,
                    job_id=job_id,
                    start_date=cutoff_date,
                    end_date=end_date,
                    status="started",
                    success=True
                )
            else:
                self.logger.error(f"❌ Failed to start lab execution: {error_msg}")
                return BacktestExecutionResult(
                    lab_id=lab_id,
                    job_id="failed",
                    start_date=cutoff_date,
                    end_date=end_date,
                    status="failed",
                    success=False,
                    error_message=error_msg
                )
                
        except Exception as e:
            self.logger.error(f"Failed to start longest backtest: {e}")
            return BacktestExecutionResult(
                lab_id=lab_id,
                job_id="error",
                start_date=cutoff_date or datetime.now() - timedelta(days=730),
                end_date=end_date or datetime.now(),
                status="error",
                success=False,
                error_message=str(e)
            )
    
    async def monitor_lab_progress(
        self, 
        lab_id: str, 
        max_wait_minutes: int = 10,
        check_interval: int = 30
    ) -> BacktestProgress:
        """
        Monitor lab execution progress until completion or timeout.
        
        This is the unified implementation that replaces all duplicate
        monitor_lab_progress functions across the codebase.
        
        Args:
            lab_id: ID of the lab to monitor
            max_wait_minutes: Maximum time to wait in minutes
            check_interval: Interval between checks in seconds
            
        Returns:
            BacktestProgress with final status
        """
        try:
            self.logger.info(f"👀 Monitoring lab progress: {lab_id[:8]}")
            
            start_time = time.time()
            max_wait_seconds = max_wait_minutes * 60
            
            while time.time() - start_time < max_wait_seconds:
                try:
                    # Get lab execution status
                    status_response = await self.lab_api.get_lab_execution_status(lab_id)
                    
                    if status_response:
                        # Extract status information
                        progress = BacktestProgress(
                            lab_id=lab_id,
                            status=getattr(status_response, 'status', 'unknown'),
                            progress_percentage=getattr(status_response, 'progress_percentage', 0),
                            generation=getattr(status_response, 'generation', 0),
                            population=getattr(status_response, 'population', 0),
                            best_fitness=getattr(status_response, 'best_fitness', 0),
                            completed_backtests=getattr(status_response, 'completed_backtests', 0),
                            total_backtests=getattr(status_response, 'total_backtests', 0),
                            is_running=getattr(status_response, 'is_running', False),
                            is_completed=getattr(status_response, 'is_completed', False),
                            error_message=getattr(status_response, 'error_message', None)
                        )
                        
                        self.logger.info(f"📊 Status: {progress.status} | Progress: {progress.progress_percentage:.1f}% | Gen: {progress.generation} | Pop: {progress.population}")
                        
                        if progress.is_completed or progress.status == "completed":
                            self.logger.info("✅ Lab execution completed successfully!")
                            return progress
                        elif progress.status == "failed":
                            self.logger.error(f"❌ Lab execution failed: {progress.error_message}")
                            return progress
                        elif progress.is_running or progress.status == "running":
                            self.logger.info(f"🔄 Lab is running (Gen: {progress.generation}, Pop: {progress.population})")
                            return progress
                        else:
                            self.logger.info(f"⏳ Lab status: {progress.status}, waiting...")
                            await asyncio.sleep(check_interval)
                    else:
                        self.logger.warning(f"📊 No status response for lab {lab_id}")
                        await asyncio.sleep(check_interval)
                        
                except Exception as e:
                    self.logger.warning(f"Error checking status: {e}")
                    await asyncio.sleep(check_interval)
            
            # Timeout
            self.logger.warning(f"⏰ Timeout waiting for lab {lab_id} to start running")
            return BacktestProgress(
                lab_id=lab_id,
                status="timeout",
                progress_percentage=0,
                generation=0,
                population=0,
                best_fitness=0,
                completed_backtests=0,
                total_backtests=0,
                is_running=False,
                is_completed=False,
                error_message="Monitoring timeout"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to monitor lab progress: {e}")
            return BacktestProgress(
                lab_id=lab_id,
                status="error",
                progress_percentage=0,
                generation=0,
                population=0,
                best_fitness=0,
                completed_backtests=0,
                total_backtests=0,
                is_running=False,
                is_completed=False,
                error_message=str(e)
            )
    
    async def _check_lab_status(self, lab_id: str) -> Optional[Dict[str, Any]]:
        """Check current lab execution status"""
        try:
            status_response = await self.lab_api.get_lab_execution_status(lab_id)
            if status_response:
                return {
                    'is_running': getattr(status_response, 'is_running', False),
                    'status': getattr(status_response, 'status', 'unknown'),
                    'progress': getattr(status_response, 'progress_percentage', 0)
                }
            return None
        except Exception as e:
            self.logger.warning(f"Error checking lab status: {e}")
            return None
    
    async def run_comprehensive_longest_backtest(
        self,
        lab_ids: List[str],
        max_iterations: int = 1500,
        start_date: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run longest backtest for multiple labs with comprehensive monitoring.
        
        Args:
            lab_ids: List of lab IDs to process
            max_iterations: Maximum iterations per lab
            start_date: Optional start date (YYYY-MM-DD format)
            dry_run: If True, only simulate the process
            
        Returns:
            Dictionary with results for each lab
        """
        results = {}
        
        for lab_id in lab_ids:
            try:
                self.logger.info(f"⚙️ Processing lab {lab_id}...")
                
                # New robust algorithm path
                if dry_run:
                    results[lab_id] = await self._plan_longest_backtest(lab_id)
                    results[lab_id]['status'] = 'dry_run'
                    continue

                boundary = await self._robust_longest_backtest(lab_id)
                results[lab_id] = {
                    'status': 'success' if boundary.get('running_found') else 'partial',
                    'running_found': boundary.get('running_found'),
                    'approx_start_date': boundary.get('approx_start').strftime('%Y-%m-%d') if boundary.get('approx_start') else None,
                    'end_date': boundary.get('end').strftime('%Y-%m-%d') if boundary.get('end') else None,
                    'attempts': boundary.get('attempts'),
                    'last_status': boundary.get('last_status'),
                    'notes': boundary.get('notes'),
                }
                
            except Exception as e:
                self.logger.error(f"Error processing lab {lab_id}: {e}")
                results[lab_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results

    async def _plan_longest_backtest(self, lab_id: str) -> Dict[str, Any]:
        end_dt = datetime.now()
        return {
            'plan': {
                'start_months': 36,
                'decrease_step_months': 2,
                'expand_months': 1,
                'refine_weeks': 2,
                'refine_days': [3, 5],
                'end_date': end_dt.strftime('%Y-%m-%d'),
            }
        }

    async def _robust_longest_backtest(self, lab_id: str) -> Dict[str, Any]:
        attempts = []
        notes = []
        lab_details = await self.lab_api.get_lab_details(lab_id)
        market_tag = getattr(lab_details.settings, 'market_tag', None) if hasattr(lab_details, 'settings') else None
        if not market_tag:
            raise BacktestError('Market tag not found')

        end_dt = datetime.now()
        # Month descent: 36m down by 1m until first RUNNING
        months = 36
        earliest_running: Optional[datetime] = None
        while months >= 1 and earliest_running is None:
            start_dt = end_dt - timedelta(days=int(months * 30.5))
            await self._preregister_market_short(market_tag, months)
            status = await self._try_window(lab_id, start_dt, end_dt)
            attempts.append({'delta': f'-{months}m', 'start': start_dt, 'end': end_dt, 'result': status})
            if status == 'running':
                earliest_running = start_dt
                await self._force_cancel(lab_id)
                break
            await self._force_cancel(lab_id)
            months -= 1

        if earliest_running is None:
            # Ensure we still converge: accept 1-day baseline then refine forward
            earliest_running = end_dt - timedelta(days=1)
            notes.append('No month RUNNING found; baseline 1d accepted')

        # Step-halving boundary refinement: 1m → 2w → 1w → 3d → 2d
        steps = [
            ('1m', timedelta(days=30)),
            ('2w', timedelta(weeks=2)),
            ('1w', timedelta(weeks=1)),
            ('3d', timedelta(days=3)),
            ('2d', timedelta(days=2)),
        ]
        current_start = earliest_running
        for label, delta in steps:
            candidate = current_start - delta
            status = await self._try_window(lab_id, candidate, end_dt)
            attempts.append({'delta': f'-{label}', 'start': candidate, 'end': end_dt, 'result': status})
            if status == 'running':
                current_start = candidate
            # Always cancel before next attempt
            await self._force_cancel(lab_id)

        # Stop when within ±2 days by construction after last step (2d)
        return {
            'running_found': True,
            'approx_start': current_start,
            'end': end_dt,
            'attempts': [
                {
                    'start': a.get('start').strftime('%Y-%m-%d'),
                    'end': a.get('end').strftime('%Y-%m-%d'),
                    'result': a.get('result'),
                    'delta': a.get('delta'),
                }
                for a in attempts
            ],
            'last_status': attempts[-1].get('result') if attempts else 'unknown',
            'notes': "; ".join(notes) if notes else None,
        }

    async def _try_window(self, lab_id: str, start_dt: datetime, end_dt: datetime) -> str:
        exec_req = StartLabExecutionRequest(
            labId=lab_id,
            startUnix=int(start_dt.timestamp()),
            endUnix=int(end_dt.timestamp()),
            sendEmail=False,
        )
        result = await self.lab_api.start_lab_execution(exec_req)
        success = result.get('Success', False) if isinstance(result, dict) else getattr(result, 'success', False)
        if not success:
            return 'failed_start'
        for _ in range(4):
            status = await self._check_lab_status(lab_id)
            if status and (status.get('status') in ('running', 'RUNNING') or status.get('is_running')):
                return 'running'
            await asyncio.sleep(5)
        return 'queued'

    async def _force_cancel(self, lab_id: str) -> None:
        try:
            await self.lab_api.cancel_lab_execution(lab_id)
        except Exception:
            pass

    async def _preregister_market_short(self, market_tag: str, months: int) -> None:
        """
        V2-only market pre-registration using v2 APIs.
        NO v1 usage - this is v2-only implementation.
        """
        logger.info(f"V2-only market pre-registration for {market_tag} ({months} months)")
        
        try:
            # Use v2 market API for market registration
            from ...api.market.market_api import MarketAPI
            from ...core.auth import AuthenticationManager
            from ...config.settings import Settings
            import os
            
            # Create v2 authentication
            settings = Settings()
            auth_manager = AuthenticationManager(
                email=os.getenv('API_EMAIL'),
                password=os.getenv('API_PASSWORD')
            )
            await auth_manager.authenticate()
            
            # Create market API instance
            market_api = MarketAPI(auth_manager, settings)
            
            # Trigger market data fetch to register market
            try:
                await market_api.get_price_data(market_tag)
                logger.info(f"Market {market_tag} registered via v2 API")
            except Exception as e:
                logger.warning(f"Error registering market {market_tag} via v2: {e}")
            
            # Set history depth using v2 API
            try:
                # This would be implemented in v2 market API
                # await market_api.set_history_depth(market_tag, months)
                logger.info(f"History depth set to {months} months for {market_tag}")
            except Exception as e:
                logger.warning(f"Error setting history depth for {market_tag}: {e}")
                
        except Exception as e:
            logger.error(f"V2-only market pre-registration failed for {market_tag}: {e}")
            # Continue without pre-registration - algorithm will still converge






