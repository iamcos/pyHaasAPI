"""
Backtest Manager for pyHaasAPI

This module provides comprehensive backtest management including:
- Tracking created labs and backtests
- Monitoring execution status
- Managing WFO lab creation
- Pre-bot validation backtesting
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .. import api
from ..model import CreateLabRequest, CloudMarket, StartLabExecutionRequest, LabDetails
from .cache import UnifiedCacheManager

logger = logging.getLogger(__name__)


@dataclass
class BacktestJob:
    """Represents a backtest job (lab or individual backtest)"""
    job_id: str
    job_type: str  # 'lab' or 'individual'
    lab_id: str
    backtest_id: Optional[str] = None
    script_id: str = ""
    market_tag: str = ""
    account_id: str = ""
    start_unix: int = 0
    end_unix: int = 0
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


@dataclass
class WFOJob:
    """Represents a Walk Forward Optimization job"""
    wfo_id: str
    base_script_id: str
    base_market_tag: str
    base_account_id: str
    time_periods: List[Dict[str, Any]]
    parameter_ranges: Dict[str, List[float]]
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    completed_at: Optional[str] = None
    lab_jobs: List[BacktestJob] = None
    results: Optional[Dict[str, Any]] = None


class BacktestManager:
    """Manages backtest jobs and WFO operations"""
    
    def __init__(self, cache_manager: Optional[UnifiedCacheManager] = None):
        self.cache_manager = cache_manager or UnifiedCacheManager()
        self.executor = None
        self.jobs_file = self.cache_manager.base_dir / "backtest_jobs.json"
        self.wfo_jobs_file = self.cache_manager.base_dir / "wfo_jobs.json"
        
        # Load existing jobs
        self.jobs = self._load_jobs()
        self.wfo_jobs = self._load_wfo_jobs()
    
    def connect(self, executor) -> bool:
        """Connect to HaasOnline API"""
        try:
            self.executor = executor
            logger.info("Connected to HaasOnline API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to API: {e}")
            return False
    
    def _load_jobs(self) -> Dict[str, BacktestJob]:
        """Load existing backtest jobs from cache"""
        if self.jobs_file.exists():
            try:
                with open(self.jobs_file, 'r') as f:
                    data = json.load(f)
                    return {job_id: BacktestJob(**job_data) for job_id, job_data in data.items()}
            except Exception as e:
                logger.warning(f"Failed to load jobs: {e}")
        return {}
    
    def _save_jobs(self) -> None:
        """Save backtest jobs to cache"""
        try:
            with open(self.jobs_file, 'w') as f:
                json.dump({job_id: asdict(job) for job_id, job in self.jobs.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def _load_wfo_jobs(self) -> Dict[str, WFOJob]:
        """Load existing WFO jobs from cache"""
        if self.wfo_jobs_file.exists():
            try:
                with open(self.wfo_jobs_file, 'r') as f:
                    data = json.load(f)
                    return {wfo_id: WFOJob(**wfo_data) for wfo_id, wfo_data in data.items()}
            except Exception as e:
                logger.warning(f"Failed to load WFO jobs: {e}")
        return {}
    
    def _save_wfo_jobs(self) -> None:
        """Save WFO jobs to cache"""
        try:
            with open(self.wfo_jobs_file, 'w') as f:
                json.dump({wfo_id: asdict(wfo) for wfo_id, wfo in self.wfo_jobs.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save WFO jobs: {e}")
    
    def create_individual_backtest_with_cutoff(self,
                                             script_id: str,
                                             market_tag: str,
                                             account_id: str,
                                             job_name: str = None) -> BacktestJob:
        """Create an individual backtest using simplified cutoff discovery for maximum period"""
        
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        # Generate job ID
        job_id = f"individual_cutoff_{int(time.time())}_{script_id[:8]}"
        
        try:
            # Create lab for individual backtest
            logger.info(f"Creating lab for cutoff-based individual backtest")
            
            # Parse market tag to create CloudMarket
            market_parts = market_tag.split('_')
            if len(market_parts) >= 3:
                exchange_code = market_parts[0]
                primary = market_parts[1]
                secondary = market_parts[2]
            else:
                raise ValueError(f"Invalid market tag format: {market_tag}")
            
            cloud_market = CloudMarket(
                category="",
                price_source=exchange_code,
                primary=primary,
                secondary=secondary
            )
            
            # Create lab request
            lab_name = job_name or f"CutoffBacktest_{script_id}_{int(time.time())}"
            req = CreateLabRequest.with_generated_name(
                script_id=script_id,
                account_id=account_id,
                market=cloud_market,
                exchange_code=exchange_code,
                interval=1,
                default_price_data_style="CandleStick"
            )
            
            # Create lab
            lab = api.create_lab(self.executor, req)
            logger.info(f"Created lab {lab.lab_id} for cutoff-based individual backtest")
            
            # Use simplified cutoff discovery
            logger.info(f"Discovering cutoff date for lab {lab.lab_id}")
            cutoff_date = self._discover_cutoff_simple(lab.lab_id, market_tag)
            
            # Calculate optimal backtest period
            end_date = datetime.now()
            
            # Add safety margin (1 day after cutoff)
            start_date = cutoff_date + timedelta(days=1)
            
            logger.info(f"Cutoff date: {cutoff_date}")
            logger.info(f"Optimal backtest period: {start_date} to {end_date}")
            logger.info(f"Backtest duration: {(end_date - start_date).days} days")
            
            # Create backtest job
            job = BacktestJob(
                job_id=job_id,
                job_type="individual",
                lab_id=lab.lab_id,
                script_id=script_id,
                market_tag=market_tag,
                account_id=account_id,
                start_unix=int(start_date.timestamp()),
                end_unix=int(end_date.timestamp()),
                status="pending",
                created_at=datetime.now().isoformat()
            )
            
            # Start backtest execution
            self._start_backtest_execution(job)
            
            # Save job
            self.jobs[job_id] = job
            self._save_jobs()
            
            logger.info(f"Created cutoff-based individual backtest job: {job_id}")
            logger.info(f"Backtest period: {(end_date - start_date).days} days")
            return job
            
        except Exception as e:
            logger.error(f"Failed to create cutoff-based individual backtest: {e}")
            raise

    def create_individual_backtest(self, 
                                 script_id: str,
                                 market_tag: str,
                                 account_id: str,
                                 start_date: datetime,
                                 end_date: datetime,
                                 job_name: str = None) -> BacktestJob:
        """Create an individual backtest job"""
        
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        # Generate job ID
        job_id = f"individual_{int(time.time())}_{script_id[:8]}"
        
        # Create lab for individual backtest
        try:
            # Parse market tag to create CloudMarket
            market_parts = market_tag.split('_')
            if len(market_parts) >= 3:
                exchange_code = market_parts[0]
                primary = market_parts[1]
                secondary = market_parts[2]
            else:
                raise ValueError(f"Invalid market tag format: {market_tag}")
            
            cloud_market = CloudMarket(
                category="",
                price_source=exchange_code,
                primary=primary,
                secondary=secondary
            )
            
            # Create lab request
            lab_name = job_name or f"Individual_{script_id}_{int(time.time())}"
            req = CreateLabRequest.with_generated_name(
                script_id=script_id,
                account_id=account_id,
                market=cloud_market,
                exchange_code=exchange_code,
                interval=1,
                default_price_data_style="CandleStick"
            )
            
            # Create lab
            lab = api.create_lab(self.executor, req)
            logger.info(f"Created lab {lab.lab_id} for individual backtest")
            
            # Create backtest job
            job = BacktestJob(
                job_id=job_id,
                job_type="individual",
                lab_id=lab.lab_id,
                script_id=script_id,
                market_tag=market_tag,
                account_id=account_id,
                start_unix=int(start_date.timestamp()),
                end_unix=int(end_date.timestamp()),
                status="pending",
                created_at=datetime.now().isoformat()
            )
            
            # Start backtest execution
            self._start_backtest_execution(job)
            
            # Save job
            self.jobs[job_id] = job
            self._save_jobs()
            
            logger.info(f"Created individual backtest job: {job_id}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to create individual backtest: {e}")
            raise
    
    def create_wfo_lab(self,
                      script_id: str,
                      market_tag: str,
                      account_id: str,
                      time_periods: List[Dict[str, Any]],
                      parameter_ranges: Dict[str, List[float]] = None,
                      wfo_name: str = None) -> WFOJob:
        """Create a WFO lab with multiple time periods"""
        
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        # Generate WFO ID
        wfo_id = f"wfo_{int(time.time())}_{script_id[:8]}"
        
        try:
            # Parse market tag to create CloudMarket
            market_parts = market_tag.split('_')
            if len(market_parts) >= 3:
                exchange_code = market_parts[0]
                primary = market_parts[1]
                secondary = market_parts[2]
            else:
                raise ValueError(f"Invalid market tag format: {market_tag}")
            
            cloud_market = CloudMarket(
                category="",
                price_source=exchange_code,
                primary=primary,
                secondary=secondary
            )
            
            # Create lab for WFO
            lab_name = wfo_name or f"WFO_{script_id}_{int(time.time())}"
            req = CreateLabRequest.with_generated_name(
                script_id=script_id,
                account_id=account_id,
                market=cloud_market,
                exchange_code=exchange_code,
                interval=1,
                default_price_data_style="CandleStick"
            )
            
            # Create lab
            lab = api.create_lab(self.executor, req)
            logger.info(f"Created lab {lab.lab_id} for WFO")
            
            # Apply parameter ranges if provided
            if parameter_ranges:
                self._apply_parameter_ranges(lab.lab_id, parameter_ranges)
            
            # Create WFO job
            wfo_job = WFOJob(
                wfo_id=wfo_id,
                base_script_id=script_id,
                base_market_tag=market_tag,
                base_account_id=account_id,
                time_periods=time_periods,
                parameter_ranges=parameter_ranges or {},
                status="pending",
                created_at=datetime.now().isoformat(),
                lab_jobs=[]
            )
            
            # Create individual lab jobs for each time period
            for i, period in enumerate(time_periods):
                job_id = f"{wfo_id}_period_{i}"
                
                job = BacktestJob(
                    job_id=job_id,
                    job_type="lab",
                    lab_id=lab.lab_id,
                    script_id=script_id,
                    market_tag=market_tag,
                    account_id=account_id,
                    start_unix=period['start_unix'],
                    end_unix=period['end_unix'],
                    status="pending",
                    created_at=datetime.now().isoformat()
                )
                
                wfo_job.lab_jobs.append(job)
                self.jobs[job_id] = job
            
            # Save jobs
            self.wfo_jobs[wfo_id] = wfo_job
            self._save_jobs()
            self._save_wfo_jobs()
            
            logger.info(f"Created WFO job: {wfo_id} with {len(time_periods)} periods")
            return wfo_job
            
        except Exception as e:
            logger.error(f"Failed to create WFO lab: {e}")
            raise
    
    def _apply_parameter_ranges(self, lab_id: str, parameter_ranges: Dict[str, List[float]]) -> None:
        """Apply parameter ranges to a lab"""
        try:
            # Get current lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Update parameters with ranges
            for param_key, param_values in parameter_ranges.items():
                # Find existing parameter or create new one
                param_found = False
                for param in lab_details.parameters:
                    if param.key == param_key:
                        param.optimization_values = param_values
                        param.is_optimized = True
                        param.is_optimization_selected = True
                        param_found = True
                        break
                
                if not param_found:
                    # Add new parameter
                    from ..parameters import LabParameter
                    new_param = LabParameter(
                        key=param_key,
                        optimization_values=param_values,
                        is_optimized=True,
                        is_optimization_selected=True
                    )
                    lab_details.parameters.append(new_param)
            
            # Update lab with new parameters
            api.update_lab_details(self.executor, lab_details)
            logger.info(f"Applied parameter ranges to lab {lab_id}")
            
        except Exception as e:
            logger.error(f"Failed to apply parameter ranges: {e}")
            raise
    
    def _discover_cutoff_simple(self, lab_id: str, market_tag: str) -> datetime:
        """Simplified cutoff discovery using binary search"""
        try:
            logger.info(f"Starting simplified cutoff discovery for {market_tag}")
            
            # Start with a reasonable range (2 years back)
            now = datetime.now()
            earliest_date = now - timedelta(days=730)  # 2 years
            latest_date = now - timedelta(days=1)      # Yesterday
            
            # Binary search for cutoff date
            max_attempts = 10
            attempts = 0
            
            while (latest_date - earliest_date).total_seconds() > (24 * 3600) and attempts < max_attempts:  # 1 day precision
                attempts += 1
                mid_date = earliest_date + (latest_date - earliest_date) / 2
                
                logger.info(f"Attempt {attempts}: Testing cutoff at {mid_date}")
                
                # Test if we can start a backtest from this date
                test_start_unix = int(mid_date.timestamp())
                test_end_unix = int((mid_date + timedelta(hours=1)).timestamp())
                
                try:
                    # Try to start a very short backtest to test if data is available
                    request = StartLabExecutionRequest(
                        lab_id=lab_id,
                        start_unix=test_start_unix,
                        end_unix=test_end_unix,
                        send_email=False
                    )
                    
                    result = api.start_lab_execution(self.executor, request)
                    
                    if result.get('Success', False):
                        # Data is available, cutoff is earlier
                        earliest_date = mid_date
                        logger.info(f"Data available at {mid_date}, moving cutoff earlier")
                    else:
                        # No data available, cutoff is later
                        latest_date = mid_date
                        logger.info(f"No data at {mid_date}, moving cutoff later")
                        
                except Exception as e:
                    # Assume no data available
                    latest_date = mid_date
                    logger.info(f"Error testing {mid_date}, assuming no data: {e}")
            
            # Return the latest date where data is available
            cutoff_date = earliest_date
            logger.info(f"Discovered cutoff date: {cutoff_date} (after {attempts} attempts)")
            
            return cutoff_date
            
        except Exception as e:
            logger.error(f"Error in cutoff discovery: {e}")
            # Fallback to a conservative date (1 year ago)
            return datetime.now() - timedelta(days=365)

    def _start_backtest_execution(self, job: BacktestJob) -> None:
        """Start backtest execution for a job"""
        try:
            request = StartLabExecutionRequest(
                lab_id=job.lab_id,
                start_unix=job.start_unix,
                end_unix=job.end_unix,
                send_email=False
            )
            
            result = api.start_lab_execution(self.executor, request)
            
            if result.get('Success', False):
                job.status = "running"
                logger.info(f"Started backtest execution for job {job.job_id}")
            else:
                job.status = "failed"
                job.error_message = result.get('Error', 'Unknown error')
                logger.error(f"Failed to start backtest for job {job.job_id}: {job.error_message}")
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"Failed to start backtest execution: {e}")
    
    def monitor_jobs(self) -> Dict[str, Any]:
        """Monitor all pending and running jobs"""
        if not self.executor:
            logger.warning("Not connected to API. Cannot monitor jobs.")
            return {"error": "Not connected to API"}
        
        monitoring_results = {
            "checked_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "still_running": 0,
            "new_results": []
        }
        
        for job_id, job in self.jobs.items():
            if job.status in ["pending", "running"]:
                monitoring_results["checked_jobs"] += 1
                
                try:
                    # Check lab status
                    lab_details = api.get_lab_details(self.executor, job.lab_id)
                    
                    if lab_details.status.value == 3:  # COMPLETED
                        job.status = "completed"
                        job.completed_at = datetime.now().isoformat()
                        
                        # Get backtest results
                        job.results = self._get_backtest_results(job.lab_id)
                        monitoring_results["completed_jobs"] += 1
                        monitoring_results["new_results"].append(job_id)
                        
                        logger.info(f"Job {job_id} completed successfully")
                        
                    elif lab_details.status.value == 4:  # CANCELLED
                        job.status = "failed"
                        job.error_message = "Lab was cancelled"
                        monitoring_results["failed_jobs"] += 1
                        
                    elif lab_details.status.value == 5:  # ERROR
                        job.status = "failed"
                        job.error_message = "Lab execution failed"
                        monitoring_results["failed_jobs"] += 1
                        
                    else:
                        monitoring_results["still_running"] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to check job {job_id}: {e}")
                    continue
        
        # Update WFO job statuses
        for wfo_id, wfo_job in self.wfo_jobs.items():
            if wfo_job.status in ["pending", "running"]:
                # Check if all lab jobs are completed
                all_completed = all(job.status == "completed" for job in wfo_job.lab_jobs)
                any_failed = any(job.status == "failed" for job in wfo_job.lab_jobs)
                
                if all_completed:
                    wfo_job.status = "completed"
                    wfo_job.completed_at = datetime.now().isoformat()
                    wfo_job.results = self._compile_wfo_results(wfo_job)
                    logger.info(f"WFO job {wfo_id} completed")
                elif any_failed:
                    wfo_job.status = "failed"
                    wfo_job.completed_at = datetime.now().isoformat()
                    logger.info(f"WFO job {wfo_id} failed")
        
        # Save updated jobs
        self._save_jobs()
        self._save_wfo_jobs()
        
        return monitoring_results
    
    def _get_backtest_results(self, lab_id: str) -> Dict[str, Any]:
        """Get backtest results for a lab"""
        try:
            # Get backtest results
            results = api.get_backtest_result_page(self.executor, lab_id, 0, 100)
            
            if results and results.get('I'):
                # Get the first (best) backtest result
                best_backtest = results['I'][0]
                
                return {
                    "backtest_id": best_backtest.get('ID', ''),
                    "roi_percentage": best_backtest.get('ROI', 0),
                    "win_rate": best_backtest.get('WR', 0),
                    "total_trades": best_backtest.get('TT', 0),
                    "max_drawdown": best_backtest.get('MD', 0),
                    "realized_profits": best_backtest.get('RP', 0),
                    "pc_value": best_backtest.get('PC', 0),
                    "generation_idx": best_backtest.get('GI', 0),
                    "population_idx": best_backtest.get('PI', 0)
                }
            else:
                return {"error": "No backtest results found"}
                
        except Exception as e:
            logger.error(f"Failed to get backtest results for lab {lab_id}: {e}")
            return {"error": str(e)}
    
    def _compile_wfo_results(self, wfo_job: WFOJob) -> Dict[str, Any]:
        """Compile results from all WFO periods"""
        results = {
            "periods": [],
            "summary": {
                "total_periods": len(wfo_job.lab_jobs),
                "completed_periods": 0,
                "failed_periods": 0,
                "average_roi": 0,
                "average_win_rate": 0,
                "average_drawdown": 0
            }
        }
        
        rois = []
        win_rates = []
        drawdowns = []
        
        for job in wfo_job.lab_jobs:
            if job.status == "completed" and job.results:
                period_result = {
                    "period": job.job_id,
                    "start_unix": job.start_unix,
                    "end_unix": job.end_unix,
                    "results": job.results
                }
                results["periods"].append(period_result)
                results["summary"]["completed_periods"] += 1
                
                rois.append(job.results.get("roi_percentage", 0))
                win_rates.append(job.results.get("win_rate", 0))
                drawdowns.append(job.results.get("max_drawdown", 0))
            else:
                results["summary"]["failed_periods"] += 1
        
        # Calculate averages
        if rois:
            results["summary"]["average_roi"] = sum(rois) / len(rois)
            results["summary"]["average_win_rate"] = sum(win_rates) / len(win_rates)
            results["summary"]["average_drawdown"] = sum(drawdowns) / len(drawdowns)
        
        return results
    
    def get_job_status(self, job_id: str) -> Optional[BacktestJob]:
        """Get status of a specific job"""
        return self.jobs.get(job_id)
    
    def get_wfo_status(self, wfo_id: str) -> Optional[WFOJob]:
        """Get status of a specific WFO job"""
        return self.wfo_jobs.get(wfo_id)
    
    def get_completed_jobs(self) -> List[BacktestJob]:
        """Get all completed jobs"""
        return [job for job in self.jobs.values() if job.status == "completed"]
    
    def get_pending_jobs(self) -> List[BacktestJob]:
        """Get all pending jobs"""
        return [job for job in self.jobs.values() if job.status == "pending"]
    
    def get_running_jobs(self) -> List[BacktestJob]:
        """Get all running jobs"""
        return [job for job in self.jobs.values() if job.status == "running"]
    
    def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """Clean up old completed jobs"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        # Clean up individual jobs
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if (job.status == "completed" and 
                job.completed_at and 
                datetime.fromisoformat(job.completed_at) < cutoff_date):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            cleaned_count += 1
        
        # Clean up WFO jobs
        wfo_to_remove = []
        for wfo_id, wfo_job in self.wfo_jobs.items():
            if (wfo_job.status == "completed" and 
                wfo_job.completed_at and 
                datetime.fromisoformat(wfo_job.completed_at) < cutoff_date):
                wfo_to_remove.append(wfo_id)
        
        for wfo_id in wfo_to_remove:
            del self.wfo_jobs[wfo_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            self._save_jobs()
            self._save_wfo_jobs()
            logger.info(f"Cleaned up {cleaned_count} old jobs")
        
        return cleaned_count
    
    def generate_status_report(self) -> str:
        """Generate a comprehensive status report"""
        report = []
        report.append("=" * 80)
        report.append("BACKTEST MANAGER STATUS REPORT")
        report.append("=" * 80)
        report.append(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Individual jobs summary
        total_jobs = len(self.jobs)
        pending_jobs = len(self.get_pending_jobs())
        running_jobs = len(self.get_running_jobs())
        completed_jobs = len(self.get_completed_jobs())
        failed_jobs = len([j for j in self.jobs.values() if j.status == "failed"])
        
        report.append("INDIVIDUAL JOBS SUMMARY:")
        report.append("-" * 40)
        report.append(f"Total Jobs: {total_jobs}")
        report.append(f"Pending: {pending_jobs}")
        report.append(f"Running: {running_jobs}")
        report.append(f"Completed: {completed_jobs}")
        report.append(f"Failed: {failed_jobs}")
        report.append("")
        
        # WFO jobs summary
        total_wfo = len(self.wfo_jobs)
        pending_wfo = len([w for w in self.wfo_jobs.values() if w.status == "pending"])
        running_wfo = len([w for w in self.wfo_jobs.values() if w.status == "running"])
        completed_wfo = len([w for w in self.wfo_jobs.values() if w.status == "completed"])
        failed_wfo = len([w for w in self.wfo_jobs.values() if w.status == "failed"])
        
        report.append("WFO JOBS SUMMARY:")
        report.append("-" * 40)
        report.append(f"Total WFO Jobs: {total_wfo}")
        report.append(f"Pending: {pending_wfo}")
        report.append(f"Running: {running_wfo}")
        report.append(f"Completed: {completed_wfo}")
        report.append(f"Failed: {failed_wfo}")
        report.append("")
        
        # Recent completed jobs
        recent_completed = sorted(
            [job for job in self.jobs.values() if job.status == "completed"],
            key=lambda x: x.completed_at or "",
            reverse=True
        )[:5]
        
        if recent_completed:
            report.append("RECENT COMPLETED JOBS:")
            report.append("-" * 40)
            for job in recent_completed:
                report.append(f"Job ID: {job.job_id}")
                report.append(f"  Type: {job.job_type}")
                report.append(f"  Lab ID: {job.lab_id}")
                report.append(f"  Completed: {job.completed_at}")
                if job.results:
                    report.append(f"  ROI: {job.results.get('roi_percentage', 'N/A')}%")
                    report.append(f"  Win Rate: {job.results.get('win_rate', 'N/A')}%")
                report.append("")
        
        return "\n".join(report)
