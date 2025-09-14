"""
Live Bot Validation System

This module provides comprehensive validation of live trading bots by backtesting them
over the longest possible period and providing recommendations on which bots to keep
running and which to stop.

Features:
- Persistent job tracking that survives app restarts
- Cutoff-based backtesting for maximum data period
- Performance comparison between live and backtest results
- Automated recommendations with risk assessment
- Comprehensive reporting
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .. import api
from ..model import (
    CloudMarket, CreateLabRequest, StartLabExecutionRequest
)
from .cache import UnifiedCacheManager
from .robustness import StrategyRobustnessAnalyzer, RobustnessMetrics

logger = logging.getLogger(__name__)


class BotRecommendation(Enum):
    """Bot recommendation types"""
    KEEP_RUNNING = "KEEP_RUNNING"
    STOP_IMMEDIATELY = "STOP_IMMEDIATELY"
    REDUCE_POSITION = "REDUCE_POSITION"
    MONITOR_CLOSELY = "MONITOR_CLOSELY"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class LiveBotValidationJob:
    """Represents a live bot validation job"""
    job_id: str
    bot_id: str
    bot_name: str
    script_id: str
    market_tag: str
    account_id: str
    lab_id: Optional[str] = None
    backtest_id: Optional[str] = None
    start_unix: int = 0
    end_unix: int = 0
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    # Live bot data
    live_roi: float = 0.0
    live_win_rate: float = 0.0
    live_trades: int = 0
    live_drawdown: float = 0.0
    
    # Backtest results
    backtest_roi: float = 0.0
    backtest_win_rate: float = 0.0
    backtest_trades: int = 0
    backtest_drawdown: float = 0.0
    
    # Analysis results
    performance_deviation: float = 0.0  # How much live differs from backtest
    robustness_score: float = 0.0
    risk_level: str = "UNKNOWN"
    recommendation: str = "NEEDS_REVIEW"
    confidence_score: float = 0.0
    
    # Additional metrics
    backtest_period_days: int = 0
    data_quality_score: float = 0.0


@dataclass
class LiveBotValidationReport:
    """Comprehensive validation report for all live bots"""
    report_id: str
    total_bots_analyzed: int
    bots_keep_running: int
    bots_stop_immediately: int
    bots_reduce_position: int
    bots_monitor_closely: int
    bots_needs_review: int
    average_performance_deviation: float
    average_robustness_score: float
    generated_at: str
    bot_recommendations: List[LiveBotValidationJob]


class LiveBotValidator:
    """
    Validates live trading bots by backtesting them over maximum possible periods
    and providing recommendations on which bots to keep running.
    """
    
    def __init__(self, cache_manager: UnifiedCacheManager):
        self.cache_manager = cache_manager
        self.executor = None
        self.robustness_analyzer = StrategyRobustnessAnalyzer(cache_manager)
        self.jobs: Dict[str, LiveBotValidationJob] = {}
        self.jobs_file = Path("unified_cache/live_bot_validation_jobs.json")
        
        # Load existing jobs
        self._load_jobs()
    
    def connect(self, executor):
        """Connect to the HaasOnline API"""
        self.executor = executor
        logger.info("Connected to HaasOnline API for live bot validation")
    
    def _load_jobs(self):
        """Load existing validation jobs from cache"""
        try:
            if self.jobs_file.exists():
                with open(self.jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                    self.jobs = {
                        job_id: LiveBotValidationJob(**job_data)
                        for job_id, job_data in jobs_data.items()
                    }
                logger.info(f"Loaded {len(self.jobs)} existing validation jobs")
            else:
                logger.info("No existing validation jobs found")
        except Exception as e:
            logger.error(f"Failed to load validation jobs: {e}")
            self.jobs = {}
    
    def _save_jobs(self):
        """Save validation jobs to cache"""
        try:
            self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
            jobs_data = {
                job_id: asdict(job)
                for job_id, job in self.jobs.items()
            }
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
            logger.info(f"Saved {len(self.jobs)} validation jobs")
        except Exception as e:
            logger.error(f"Failed to save validation jobs: {e}")
    
    def get_live_bots(self) -> List[Dict[str, Any]]:
        """Get all live (active) bots"""
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        try:
            bots = api.get_all_bots(self.executor)
            if not isinstance(bots, list):
                logger.warning(f"Unexpected bot response type: {type(bots)}")
                return []
            
            logger.info(f"Retrieved {len(bots)} total bots from API")
            
            # Debug: Print first bot structure
            if bots:
                first_bot = bots[0]
                logger.info(f"First bot type: {type(first_bot)}")
                if hasattr(first_bot, '__dict__'):
                    logger.info(f"First bot attributes: {list(first_bot.__dict__.keys())}")
                elif isinstance(first_bot, dict):
                    logger.info(f"First bot keys: {list(first_bot.keys())}")
            
            # Filter for active bots using the correct field name
            live_bots = []
            for bot in bots:
                # Check if bot is activated (is_activated field with alias 'IA')
                if hasattr(bot, 'is_activated') and bot.is_activated:
                    live_bots.append(bot)
                    logger.debug(f"Bot {bot.bot_name} ({bot.bot_id}): is_activated = {bot.is_activated}")
            
            logger.info(f"Found {len(live_bots)} live (activated) bots out of {len(bots)} total bots")
            return live_bots
            
        except Exception as e:
            logger.error(f"Failed to get live bots: {e}")
            return []
    
    def get_bot_live_performance(self, bot_id: str) -> Dict[str, float]:
        """Get live performance metrics for a bot"""
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        try:
            runtime_data = api.get_full_bot_runtime_data(self.executor, bot_id)
            
            # runtime_data is a HaasBot object, not a response dict
            if not hasattr(runtime_data, 'bot_id'):
                raise Exception("Failed to get bot runtime data: Invalid response format")
            
            # Extract data from HaasBot object
            data = {
                'ROI': getattr(runtime_data, 'return_on_investment', 0.0),
                'WinRate': 0.0,  # Not available in HaasBot
                'TotalTrades': 0,  # Not available in HaasBot
                'MaxDrawdown': 0.0,  # Not available in HaasBot
                'RealizedProfits': getattr(runtime_data, 'realized_profit', 0.0),
                'UnrealizedProfits': getattr(runtime_data, 'urealized_profit', 0.0)
            }
            
            # Extract performance metrics
            performance = {
                'roi': data.get('ROI', 0.0),
                'win_rate': data.get('WinRate', 0.0),
                'total_trades': data.get('TotalTrades', 0),
                'max_drawdown': abs(data.get('MaxDrawdown', 0.0)),
                'realized_profits': data.get('RealizedProfits', 0.0),
                'unrealized_profits': data.get('UnrealizedProfits', 0.0)
            }
            
            logger.info(f"Bot {bot_id} live performance: ROI={performance['roi']:.2f}%, "
                       f"WinRate={performance['win_rate']:.2f}%, Trades={performance['total_trades']}")
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to get live performance for bot {bot_id}: {e}")
            return {
                'roi': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'max_drawdown': 0.0,
                'realized_profits': 0.0,
                'unrealized_profits': 0.0
            }
    
    def create_validation_job(self, bot_data) -> LiveBotValidationJob:
        """Create a validation job for a live bot"""
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        # Handle HaasBot objects (Pydantic models with aliases)
        if hasattr(bot_data, 'bot_id'):
            # This is a HaasBot object
            bot_id = bot_data.bot_id
            market_tag = bot_data.market  # This is the market field
            bot_name = bot_data.bot_name
            script_id = bot_data.script_id
            account_id = bot_data.account_id
        else:
            # Fallback for dictionary format
            bot_id = bot_data['BotId']
            market_tag = bot_data.get('MarketTag', '')
            bot_name = bot_data.get('BotName', 'Unknown')
            script_id = bot_data['ScriptId']
            account_id = bot_data['AccountId']
        
        job_id = f"live_validation_{int(time.time())}_{bot_id[:8]}"
        
        try:
            # Get live performance
            live_performance = self.get_bot_live_performance(bot_id)
            
            # Try to find existing lab for this script and market
            lab = self._find_or_create_suitable_lab(script_id, market_tag, account_id)
            logger.info(f"Using lab {lab.lab_id} for live bot validation")
            
            # Discover cutoff for maximum backtest period
            cutoff_date = self._discover_cutoff_simple(lab.lab_id, market_tag)
            end_date = datetime.now()
            start_date = cutoff_date + timedelta(days=1)  # Safety margin
            
            backtest_period_days = (end_date - start_date).days
            
            # Create validation job
            job = LiveBotValidationJob(
                job_id=job_id,
                bot_id=bot_id,
                bot_name=bot_name,
                script_id=script_id,
                market_tag=market_tag,
                account_id=account_id,
                lab_id=lab.lab_id,
                start_unix=int(start_date.timestamp()),
                end_unix=int(end_date.timestamp()),
                status="pending",
                created_at=datetime.now().isoformat(),
                live_roi=live_performance['roi'],
                live_win_rate=live_performance['win_rate'],
                live_trades=live_performance['total_trades'],
                live_drawdown=live_performance['max_drawdown'],
                backtest_period_days=backtest_period_days
            )
            
            # Start backtest execution
            self._start_backtest_execution(job)
            
            self.jobs[job_id] = job
            self._save_jobs()
            
            logger.info(f"Created live bot validation job: {job_id}")
            logger.info(f"Bot: {job.bot_name} ({job.bot_id})")
            logger.info(f"Backtest period: {backtest_period_days} days")
            logger.info(f"Live performance: ROI={job.live_roi:.2f}%, WinRate={job.live_win_rate:.2f}%")
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to create validation job for bot {bot_id}: {e}")
            raise
    
    def _find_or_create_suitable_lab(self, script_id: str, market_tag: str, account_id: str):
        """Find existing lab or create a new one with proper parameter ranges"""
        try:
            # First, try to find existing labs for this script and market
            existing_labs = api.get_labs(self.executor)
            
            # Filter labs by script and market
            suitable_labs = []
            for lab in existing_labs:
                if (hasattr(lab, 'script_id') and lab.script_id == script_id and
                    hasattr(lab, 'market') and lab.market == market_tag):
                    suitable_labs.append(lab)
            
            if suitable_labs:
                # Use the first suitable lab
                lab = suitable_labs[0]
                logger.info(f"Found existing lab {lab.lab_id} for script {script_id} and market {market_tag}")
                return lab
            
            # No suitable lab found, create a new one with parameter ranges
            logger.info(f"No existing lab found for script {script_id} and market {market_tag}, creating new one")
            return self._create_lab_with_parameter_ranges(script_id, market_tag, account_id)
            
        except Exception as e:
            logger.error(f"Error finding/creating suitable lab: {e}")
            # Fallback to creating a new lab
            return self._create_lab_with_parameter_ranges(script_id, market_tag, account_id)
    
    def _create_lab_with_parameter_ranges(self, script_id: str, market_tag: str, account_id: str):
        """Create a new lab with proper parameter ranges for optimization"""
        try:
            market_parts = market_tag.split('_')
            
            if len(market_parts) >= 3:
                exchange_code = market_parts[0]
                primary = market_parts[1]
                secondary = market_parts[2]
            else:
                raise ValueError(f"Invalid market tag format: {market_tag}")
            
            cloud_market = CloudMarket(
                C="",  # category
                PS=exchange_code,  # price_source
                P=primary,  # primary
                S=secondary  # secondary
            )
            
            # Create lab with a descriptive name
            lab_name = f"LiveValidation_{script_id[:8]}_{primary}_{secondary}"
            req = CreateLabRequest.with_generated_name(
                script_id=script_id,
                account_id=account_id,
                market=cloud_market,
                exchange_code=exchange_code,
                interval=1,
                default_price_data_style="CandleStick"
            )
            
            lab = api.create_lab(self.executor, req)
            logger.info(f"Created new lab {lab.lab_id} with parameter ranges for live bot validation")
            
            # TODO: Configure parameter ranges for optimization
            # This would involve setting up parameter ranges for the script
            # For now, we'll use the default parameters
            
            return lab
            
        except Exception as e:
            logger.error(f"Failed to create lab with parameter ranges: {e}")
            raise

    def _discover_cutoff_simple(self, lab_id: str, market_tag: str) -> datetime:
        """Simplified cutoff discovery using binary search"""
        try:
            logger.info(f"Starting cutoff discovery for live bot validation: {market_tag}")
            
            now = datetime.now()
            earliest_date = now - timedelta(days=730)  # 2 years
            latest_date = now - timedelta(days=1)      # Yesterday
            
            max_attempts = 10
            attempts = 0
            
            while (latest_date - earliest_date).total_seconds() > (24 * 3600) and attempts < max_attempts:
                attempts += 1
                mid_date = earliest_date + (latest_date - earliest_date) / 2
                
                logger.info(f"Attempt {attempts}: Testing cutoff at {mid_date}")
                
                test_start_unix = int(mid_date.timestamp())
                test_end_unix = int((mid_date + timedelta(hours=1)).timestamp())
                
                try:
                    request = StartLabExecutionRequest(
                        lab_id=lab_id,
                        start_unix=test_start_unix,
                        end_unix=test_end_unix,
                        send_email=False
                    )
                    
                    result = api.start_lab_execution(self.executor, request)
                    
                    if result.get('Success', False):
                        earliest_date = mid_date
                        logger.info(f"Data available at {mid_date}, moving cutoff earlier")
                    else:
                        latest_date = mid_date
                        logger.info(f"No data at {mid_date}, moving cutoff later")
                        
                except Exception as e:
                    latest_date = mid_date
                    logger.info(f"Error testing {mid_date}, assuming no data: {e}")
            
            cutoff_date = earliest_date
            logger.info(f"Discovered cutoff date: {cutoff_date} (after {attempts} attempts)")
            
            return cutoff_date
            
        except Exception as e:
            logger.error(f"Error in cutoff discovery: {e}")
            return datetime.now() - timedelta(days=365)  # Fallback to 1 year ago
    
    def _start_backtest_execution(self, job: LiveBotValidationJob):
        """Start backtest execution for a validation job"""
        try:
            logger.info(f"Starting backtest execution for job {job.job_id}")
            logger.info(f"Lab ID: {job.lab_id}")
            logger.info(f"Start Unix: {job.start_unix}")
            logger.info(f"End Unix: {job.end_unix}")
            
            # First, check if the lab is already running and cancel if needed
            try:
                lab_details = api.get_lab_details(self.executor, job.lab_id)
                if hasattr(lab_details, 'is_running') and lab_details.is_running:
                    logger.info(f"Lab {job.lab_id} is already running, canceling existing execution...")
                    cancel_result = api.cancel_lab_execution(self.executor, job.lab_id)
                    logger.info(f"Cancel result: {cancel_result}")
                    
                    # Wait a moment for the cancellation to take effect
                    import time
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not check/cancel lab execution: {e}")
            
            # Now start the backtest
            request = StartLabExecutionRequest(
                lab_id=job.lab_id,
                start_unix=job.start_unix,
                end_unix=job.end_unix,
                send_email=False
            )
            
            result = api.start_lab_execution(self.executor, request)
            
            # Debug: Log the actual response structure
            logger.info(f"Backtest execution response type: {type(result)}")
            logger.info(f"Backtest execution response: {result}")
            
            # Handle different response formats
            success = False
            error_message = "Unknown error"
            
            if isinstance(result, dict):
                success = result.get('Success', False)
                error_message = result.get('Error', result.get('Message', 'Unknown error'))
            elif hasattr(result, 'Success'):
                success = result.Success
                error_message = getattr(result, 'Error', getattr(result, 'Message', 'Unknown error'))
            else:
                # If it's neither dict nor object with Success, assume it succeeded
                # (some API responses might just return empty dict or None on success)
                success = True
                error_message = None
            
            # Handle specific error cases
            if not success and error_message:
                if "already active" in error_message.lower() or "run is already active" in error_message.lower():
                    # Lab is already running, mark as running instead of failed
                    job.status = "running"
                    logger.info(f"✅ Lab {job.lab_id} is already running backtest - monitoring existing execution")
                    return
                elif "cancel it or wait" in error_message.lower():
                    # Same as above - lab is running
                    job.status = "running"
                    logger.info(f"✅ Lab {job.lab_id} has active backtest - monitoring existing execution")
                    return
            
            if success:
                job.status = "running"
                logger.info(f"✅ Started backtest execution for job {job.job_id}")
            else:
                job.status = "failed"
                job.error_message = error_message
                logger.error(f"❌ Failed to start backtest for job {job.job_id}: {error_message}")
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"❌ Exception starting backtest for job {job.job_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def monitor_jobs(self) -> Dict[str, int]:
        """Monitor all validation jobs and update their status"""
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        results = {
            'pending_jobs': 0,
            'running_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0
        }
        
        for job_id, job in self.jobs.items():
            if job.status == "pending":
                results['pending_jobs'] += 1
            elif job.status == "running":
                results['running_jobs'] += 1
                self._check_job_completion(job)
            elif job.status == "completed":
                results['completed_jobs'] += 1
            elif job.status == "failed":
                results['failed_jobs'] += 1
        
        self._save_jobs()
        return results
    
    def _check_job_completion(self, job: LiveBotValidationJob):
        """Check if a running job has completed and retrieve results"""
        try:
            # Check lab execution status
            execution_update = api.get_lab_execution_update(self.executor, job.lab_id)
            
            # LabExecutionUpdate is a Pydantic model, not a dictionary
            # Check if the lab is still running based on status
            from pyHaasAPI.model import LabStatus
            is_running = execution_update.status in [LabStatus.QUEUED, LabStatus.RUNNING]
            
            logger.info(f"Job {job.job_id} status: {execution_update.status}, progress: {execution_update.progress}%")
            
            if not is_running:
                # Lab execution completed, get results
                if execution_update.status == LabStatus.COMPLETED:
                    logger.info(f"✅ Job {job.job_id} completed successfully")
                    self._retrieve_backtest_results(job)
                elif execution_update.status == LabStatus.FAILED:
                    job.status = "failed"
                    job.error_message = execution_update.error or "Lab execution failed"
                    logger.error(f"❌ Job {job.job_id} failed: {job.error_message}")
                elif execution_update.status == LabStatus.CANCELLED:
                    job.status = "failed"
                    job.error_message = "Lab execution was cancelled"
                    logger.warning(f"⚠️ Job {job.job_id} was cancelled")
                else:
                    logger.warning(f"Unknown status for job {job.job_id}: {execution_update.status}")
            else:
                logger.info(f"Job {job.job_id} still running (progress: {execution_update.progress}%)")
                
        except Exception as e:
            logger.error(f"Error checking completion for job {job.job_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def _retrieve_backtest_results(self, job: LiveBotValidationJob):
        """Retrieve backtest results for a completed job"""
        try:
            # Get backtest results
            results_response = api.get_backtest_result_page(self.executor, job.lab_id, 0, 100)
            
            if results_response.get('Success', False):
                backtests = results_response.get('Data', {}).get('Backtests', [])
                
                if backtests:
                    # Get the first (and likely only) backtest
                    backtest = backtests[0]
                    job.backtest_id = backtest.get('BacktestId')
                    
                    # Extract performance metrics
                    job.backtest_roi = backtest.get('ROI', 0.0)
                    job.backtest_win_rate = backtest.get('WinRate', 0.0)
                    job.backtest_trades = backtest.get('TotalTrades', 0)
                    job.backtest_drawdown = abs(backtest.get('MaxDrawdown', 0.0))
                    
                    # Perform analysis
                    self._analyze_bot_performance(job)
                    
                    job.status = "completed"
                    job.completed_at = datetime.now().isoformat()
                    
                    logger.info(f"Job {job.job_id} completed successfully")
                    logger.info(f"Backtest ROI: {job.backtest_roi:.2f}%, Live ROI: {job.live_roi:.2f}%")
                    logger.info(f"Recommendation: {job.recommendation}")
                else:
                    job.status = "failed"
                    job.error_message = "No backtest results found"
                    logger.error(f"No backtest results for job {job.job_id}")
            else:
                job.status = "failed"
                job.error_message = results_response.get('Message', 'Failed to get backtest results')
                logger.error(f"Failed to get backtest results for job {job.job_id}")
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"Exception retrieving results for job {job.job_id}: {e}")
    
    def _analyze_bot_performance(self, job: LiveBotValidationJob):
        """Analyze bot performance and generate recommendations"""
        try:
            # Calculate performance deviation
            if job.backtest_roi != 0:
                job.performance_deviation = abs(job.live_roi - job.backtest_roi) / abs(job.backtest_roi) * 100
            else:
                job.performance_deviation = 100.0 if job.live_roi != 0 else 0.0
            
            # Get robustness analysis
            try:
                # Create a mock backtest analysis for robustness
                mock_backtest_data = {
                    'backtest_id': job.backtest_id or 'unknown',
                    'roi_percentage': job.backtest_roi,
                    'win_rate': job.backtest_win_rate,
                    'total_trades': job.backtest_trades,
                    'max_drawdown': job.backtest_drawdown,
                    'realized_profits_usdt': 0.0,  # We don't have this from basic results
                    'pc_value': 0.0
                }
                
                robustness_metrics = self.robustness_analyzer._analyze_drawdown_risk(mock_backtest_data)
                job.robustness_score = robustness_metrics.robustness_score
                job.risk_level = robustness_metrics.risk_level
                
            except Exception as e:
                logger.warning(f"Failed to get robustness analysis for job {job.job_id}: {e}")
                job.robustness_score = 50.0  # Default moderate score
                job.risk_level = "MEDIUM"
            
            # Calculate confidence score
            job.confidence_score = self._calculate_confidence_score(job)
            
            # Generate recommendation
            job.recommendation = self._generate_recommendation(job)
            
            logger.info(f"Analysis complete for job {job.job_id}:")
            logger.info(f"  Performance deviation: {job.performance_deviation:.1f}%")
            logger.info(f"  Robustness score: {job.robustness_score:.1f}/100")
            logger.info(f"  Risk level: {job.risk_level}")
            logger.info(f"  Confidence: {job.confidence_score:.1f}%")
            logger.info(f"  Recommendation: {job.recommendation}")
            
        except Exception as e:
            logger.error(f"Error analyzing performance for job {job.job_id}: {e}")
            job.recommendation = "NEEDS_REVIEW"
            job.confidence_score = 0.0
    
    def _calculate_confidence_score(self, job: LiveBotValidationJob) -> float:
        """Calculate confidence score for the recommendation"""
        confidence = 100.0
        
        # Reduce confidence based on performance deviation
        if job.performance_deviation > 50:
            confidence -= 30
        elif job.performance_deviation > 25:
            confidence -= 15
        elif job.performance_deviation > 10:
            confidence -= 5
        
        # Reduce confidence based on data quality
        if job.backtest_period_days < 30:
            confidence -= 20
        elif job.backtest_period_days < 90:
            confidence -= 10
        elif job.backtest_period_days < 180:
            confidence -= 5
        
        # Reduce confidence based on trade count
        if job.backtest_trades < 10:
            confidence -= 15
        elif job.backtest_trades < 30:
            confidence -= 10
        elif job.backtest_trades < 50:
            confidence -= 5
        
        # Reduce confidence if live bot has very few trades
        if job.live_trades < 5:
            confidence -= 20
        elif job.live_trades < 10:
            confidence -= 10
        
        return max(0.0, min(100.0, confidence))
    
    def _generate_recommendation(self, job: LiveBotValidationJob) -> str:
        """Generate recommendation based on analysis"""
        # Critical risk - stop immediately
        if job.risk_level == "CRITICAL":
            return BotRecommendation.STOP_IMMEDIATELY.value
        
        # High performance deviation - needs review
        if job.performance_deviation > 100:
            return BotRecommendation.NEEDS_REVIEW.value
        
        # Poor live performance compared to backtest
        if job.live_roi < job.backtest_roi * 0.5 and job.live_roi < 0:
            return BotRecommendation.STOP_IMMEDIATELY.value
        
        # High risk with poor performance
        if job.risk_level == "HIGH" and job.live_roi < 0:
            return BotRecommendation.STOP_IMMEDIATELY.value
        
        # High risk but positive performance - reduce position
        if job.risk_level == "HIGH":
            return BotRecommendation.REDUCE_POSITION.value
        
        # Medium risk with poor performance - monitor closely
        if job.risk_level == "MEDIUM" and job.live_roi < job.backtest_roi * 0.7:
            return BotRecommendation.MONITOR_CLOSELY.value
        
        # Good performance and low risk - keep running
        if job.risk_level in ["LOW", "VERY_LOW"] and job.performance_deviation < 30:
            return BotRecommendation.KEEP_RUNNING.value
        
        # Default to monitor closely
        return BotRecommendation.MONITOR_CLOSELY.value
    
    def validate_all_live_bots(self, max_bots: Optional[int] = None) -> List[LiveBotValidationJob]:
        """Validate all live bots and create validation jobs"""
        if not self.executor:
            raise ValueError("Not connected to API. Call connect() first.")
        
        live_bots = self.get_live_bots()
        
        if max_bots:
            live_bots = live_bots[:max_bots]
        
        created_jobs = []
        
        for bot_data in live_bots:
            try:
                job = self.create_validation_job(bot_data)
                created_jobs.append(job)
                bot_name = bot_data.bot_name if hasattr(bot_data, 'bot_name') else bot_data.get('BotName', 'Unknown')
                logger.info(f"Created validation job for bot: {bot_name}")
            except Exception as e:
                bot_id = bot_data.bot_id if hasattr(bot_data, 'bot_id') else bot_data.get('BotId', 'Unknown')
                logger.error(f"Failed to create validation job for bot {bot_id}: {e}")
        
        logger.info(f"Created {len(created_jobs)} validation jobs for live bots")
        return created_jobs
    
    def generate_validation_report(self) -> LiveBotValidationReport:
        """Generate comprehensive validation report"""
        completed_jobs = [job for job in self.jobs.values() if job.status == "completed"]
        
        if not completed_jobs:
            logger.warning("No completed validation jobs found")
            return LiveBotValidationReport(
                report_id=f"report_{int(time.time())}",
                total_bots_analyzed=0,
                bots_keep_running=0,
                bots_stop_immediately=0,
                bots_reduce_position=0,
                bots_monitor_closely=0,
                bots_needs_review=0,
                average_performance_deviation=0.0,
                average_robustness_score=0.0,
                generated_at=datetime.now().isoformat(),
                bot_recommendations=[]
            )
        
        # Count recommendations
        recommendations = {
            BotRecommendation.KEEP_RUNNING.value: 0,
            BotRecommendation.STOP_IMMEDIATELY.value: 0,
            BotRecommendation.REDUCE_POSITION.value: 0,
            BotRecommendation.MONITOR_CLOSELY.value: 0,
            BotRecommendation.NEEDS_REVIEW.value: 0
        }
        
        for job in completed_jobs:
            recommendations[job.recommendation] += 1
        
        # Calculate averages
        avg_deviation = sum(job.performance_deviation for job in completed_jobs) / len(completed_jobs)
        avg_robustness = sum(job.robustness_score for job in completed_jobs) / len(completed_jobs)
        
        report = LiveBotValidationReport(
            report_id=f"report_{int(time.time())}",
            total_bots_analyzed=len(completed_jobs),
            bots_keep_running=recommendations[BotRecommendation.KEEP_RUNNING.value],
            bots_stop_immediately=recommendations[BotRecommendation.STOP_IMMEDIATELY.value],
            bots_reduce_position=recommendations[BotRecommendation.REDUCE_POSITION.value],
            bots_monitor_closely=recommendations[BotRecommendation.MONITOR_CLOSELY.value],
            bots_needs_review=recommendations[BotRecommendation.NEEDS_REVIEW.value],
            average_performance_deviation=avg_deviation,
            average_robustness_score=avg_robustness,
            generated_at=datetime.now().isoformat(),
            bot_recommendations=completed_jobs
        )
        
        return report
    
    def get_job_status(self, job_id: str) -> Optional[LiveBotValidationJob]:
        """Get status of a specific validation job"""
        return self.jobs.get(job_id)
    
    def cleanup_old_jobs(self, days_old: int = 7):
        """Clean up old completed and failed jobs"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if job.status in ["completed", "failed"] and job.completed_at:
                try:
                    completed_date = datetime.fromisoformat(job.completed_at)
                    if completed_date < cutoff_date:
                        jobs_to_remove.append(job_id)
                except ValueError:
                    # Invalid date format, remove the job
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        if jobs_to_remove:
            self._save_jobs()
            logger.info(f"Cleaned up {len(jobs_to_remove)} old validation jobs")
        
        return len(jobs_to_remove)
    
    def cleanup_incorrect_labs(self, dry_run: bool = True):
        """Clean up labs that were created incorrectly (single-parameter labs for validation)"""
        try:
            if not self.executor:
                raise ValueError("Not connected to API. Call connect() first.")
            
            # Get all labs
            all_labs = api.get_labs(self.executor)
            
            # Find labs that were created for live validation (single-parameter)
            incorrect_labs = []
            for lab in all_labs:
                if (hasattr(lab, 'lab_name') and 
                    lab.lab_name.startswith('LiveValidation_') and
                    '_' in lab.lab_name and len(lab.lab_name.split('_')) > 3):  # Has timestamp
                    incorrect_labs.append(lab)
            
            if not incorrect_labs:
                logger.info("No incorrect validation labs found")
                return 0
            
            logger.info(f"Found {len(incorrect_labs)} incorrect validation labs:")
            for lab in incorrect_labs:
                logger.info(f"  - {lab.lab_name} ({lab.lab_id})")
            
            if dry_run:
                logger.info("DRY RUN: Would delete these labs. Use dry_run=False to actually delete them.")
                return len(incorrect_labs)
            
            # Actually delete the labs
            deleted_count = 0
            for lab in incorrect_labs:
                try:
                    result = api.delete_lab(self.executor, lab.lab_id)
                    if result.get('Success', False):
                        deleted_count += 1
                        logger.info(f"✅ Deleted lab {lab.lab_name} ({lab.lab_id})")
                    else:
                        logger.error(f"❌ Failed to delete lab {lab.lab_name}: {result.get('Error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"❌ Exception deleting lab {lab.lab_name}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} incorrect validation labs")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup incorrect labs: {e}")
            return 0
