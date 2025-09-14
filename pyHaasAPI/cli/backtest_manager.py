#!/usr/bin/env python3
"""
Backtest Manager CLI Tool

This tool provides comprehensive backtest management including:
- Creating individual backtests for pre-bot validation
- Creating WFO labs with multiple time periods
- Monitoring job execution status
- Managing backtest results
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI.analysis.backtest_manager import BacktestManager
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_individual_backtest_with_cutoff(script_id: str, market_tag: str, account_id: str, 
                                          job_name: str = None):
    """Create an individual backtest using cutoff discovery for maximum period"""
    
    logger.info(f"Creating cutoff-based individual backtest for script {script_id}")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    backtest_manager = BacktestManager(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        logger.error("Failed to connect to HaasOnline API")
        return False
    
    # Connect backtest manager
    backtest_manager.connect(analyzer.executor)
    
    try:
        # Create individual backtest with cutoff discovery
        job = backtest_manager.create_individual_backtest_with_cutoff(
            script_id=script_id,
            market_tag=market_tag,
            account_id=account_id,
            job_name=job_name
        )
        
        logger.info(f"Created cutoff-based individual backtest job: {job.job_id}")
        logger.info(f"Lab ID: {job.lab_id}")
        logger.info(f"Backtest period: {(datetime.fromtimestamp(job.end_unix) - datetime.fromtimestamp(job.start_unix)).days} days")
        logger.info(f"Status: {job.status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating cutoff-based individual backtest: {e}")
        return False


def create_individual_backtest(script_id: str, market_tag: str, account_id: str, 
                             hours: int = 24, job_name: str = None):
    """Create an individual backtest for pre-bot validation"""
    
    logger.info(f"Creating individual backtest for script {script_id}")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    backtest_manager = BacktestManager(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        logger.error("Failed to connect to HaasOnline API")
        return False
    
    # Connect backtest manager
    backtest_manager.connect(analyzer.executor)
    
    try:
        # Calculate time range
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        
        # Create individual backtest
        job = backtest_manager.create_individual_backtest(
            script_id=script_id,
            market_tag=market_tag,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            job_name=job_name
        )
        
        logger.info(f"Created individual backtest job: {job.job_id}")
        logger.info(f"Lab ID: {job.lab_id}")
        logger.info(f"Time range: {start_date} to {end_date}")
        logger.info(f"Status: {job.status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating individual backtest: {e}")
        return False


def create_wfo_lab(script_id: str, market_tag: str, account_id: str,
                  training_days: int = 90, testing_days: int = 30, 
                  num_periods: int = 4, wfo_name: str = None):
    """Create a WFO lab with multiple time periods"""
    
    logger.info(f"Creating WFO lab for script {script_id}")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    backtest_manager = BacktestManager(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        logger.error("Failed to connect to HaasOnline API")
        return False
    
    # Connect backtest manager
    backtest_manager.connect(analyzer.executor)
    
    try:
        # Generate time periods
        time_periods = []
        end_date = datetime.now()
        
        for i in range(num_periods):
            # Calculate period dates
            period_end = end_date - timedelta(days=i * (training_days + testing_days))
            period_start = period_end - timedelta(days=training_days + testing_days)
            testing_start = period_end - timedelta(days=testing_days)
            
            # Training period
            training_period = {
                "period_type": "training",
                "start_unix": int(period_start.timestamp()),
                "end_unix": int(testing_start.timestamp()),
                "start_date": period_start.isoformat(),
                "end_date": testing_start.isoformat()
            }
            
            # Testing period
            testing_period = {
                "period_type": "testing", 
                "start_unix": int(testing_start.timestamp()),
                "end_unix": int(period_end.timestamp()),
                "start_date": testing_start.isoformat(),
                "end_date": period_end.isoformat()
            }
            
            time_periods.extend([training_period, testing_period])
        
        # Create WFO lab
        wfo_job = backtest_manager.create_wfo_lab(
            script_id=script_id,
            market_tag=market_tag,
            account_id=account_id,
            time_periods=time_periods,
            wfo_name=wfo_name
        )
        
        logger.info(f"Created WFO job: {wfo_job.wfo_id}")
        logger.info(f"Lab ID: {wfo_job.lab_jobs[0].lab_id if wfo_job.lab_jobs else 'N/A'}")
        logger.info(f"Time periods: {len(time_periods)}")
        logger.info(f"Status: {wfo_job.status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating WFO lab: {e}")
        return False


def monitor_jobs():
    """Monitor all pending and running jobs"""
    
    logger.info("Monitoring backtest jobs...")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    backtest_manager = BacktestManager(cache_manager)
    
    try:
        # Monitor jobs
        results = backtest_manager.monitor_jobs()
        
        if "error" in results:
            logger.error(f"Monitoring failed: {results['error']}")
            return False
        
        logger.info("Monitoring results:")
        logger.info(f"  Checked jobs: {results['checked_jobs']}")
        logger.info(f"  Completed jobs: {results['completed_jobs']}")
        logger.info(f"  Failed jobs: {results['failed_jobs']}")
        logger.info(f"  Still running: {results['still_running']}")
        
        if results['new_results']:
            logger.info(f"  New completed jobs: {', '.join(results['new_results'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error monitoring jobs: {e}")
        return False


def show_status():
    """Show comprehensive status report"""
    
    logger.info("Generating status report...")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    backtest_manager = BacktestManager(cache_manager)
    
    try:
        # Generate status report
        report = backtest_manager.generate_status_report()
        print(report)
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating status report: {e}")
        return False


def cleanup_old_jobs(days_old: int = 7):
    """Clean up old completed jobs"""
    
    logger.info(f"Cleaning up jobs older than {days_old} days...")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    backtest_manager = BacktestManager(cache_manager)
    
    try:
        # Clean up old jobs
        cleaned_count = backtest_manager.cleanup_old_jobs(days_old)
        
        logger.info(f"Cleaned up {cleaned_count} old jobs")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {e}")
        return False


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Backtest Manager CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create individual backtest for pre-bot validation (fixed hours)
  python -m pyHaasAPI.cli.backtest_manager create-individual --script-id script123 --market-tag BINANCE_BTC_USDT_ --account-id acc123 --hours 48
  
  # Create individual backtest with cutoff discovery (maximum possible period)
  python -m pyHaasAPI.cli.backtest_manager create-individual-cutoff --script-id script123 --market-tag BINANCE_BTC_USDT_ --account-id acc123
  
  # Create WFO lab with 4 periods
  python -m pyHaasAPI.cli.backtest_manager create-wfo --script-id script123 --market-tag BINANCE_BTC_USDT_ --account-id acc123 --training-days 90 --testing-days 30 --num-periods 4
  
  # Monitor all jobs
  python -m pyHaasAPI.cli.backtest_manager monitor
  
  # Show status report
  python -m pyHaasAPI.cli.backtest_manager status
  
  # Clean up old jobs
  python -m pyHaasAPI.cli.backtest_manager cleanup --days 7
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create individual backtest command
    individual_parser = subparsers.add_parser('create-individual', help='Create individual backtest')
    individual_parser.add_argument('--script-id', required=True, help='Script ID to backtest')
    individual_parser.add_argument('--market-tag', required=True, help='Market tag (e.g., BINANCE_BTC_USDT_)')
    individual_parser.add_argument('--account-id', required=True, help='Account ID to use')
    individual_parser.add_argument('--hours', type=int, default=24, help='Hours to backtest (default: 24)')
    individual_parser.add_argument('--job-name', help='Custom job name')
    
    # Create individual backtest with cutoff command
    cutoff_parser = subparsers.add_parser('create-individual-cutoff', help='Create individual backtest using cutoff discovery for maximum period')
    cutoff_parser.add_argument('--script-id', required=True, help='Script ID to backtest')
    cutoff_parser.add_argument('--market-tag', required=True, help='Market tag (e.g., BINANCE_BTC_USDT_)')
    cutoff_parser.add_argument('--account-id', required=True, help='Account ID to use')
    cutoff_parser.add_argument('--job-name', help='Custom job name')
    
    # Create WFO lab command
    wfo_parser = subparsers.add_parser('create-wfo', help='Create WFO lab')
    wfo_parser.add_argument('--script-id', required=True, help='Script ID to backtest')
    wfo_parser.add_argument('--market-tag', required=True, help='Market tag (e.g., BINANCE_BTC_USDT_)')
    wfo_parser.add_argument('--account-id', required=True, help='Account ID to use')
    wfo_parser.add_argument('--training-days', type=int, default=90, help='Training period in days (default: 90)')
    wfo_parser.add_argument('--testing-days', type=int, default=30, help='Testing period in days (default: 30)')
    wfo_parser.add_argument('--num-periods', type=int, default=4, help='Number of periods (default: 4)')
    wfo_parser.add_argument('--wfo-name', help='Custom WFO name')
    
    # Monitor jobs command
    subparsers.add_parser('monitor', help='Monitor all pending and running jobs')
    
    # Status command
    subparsers.add_parser('status', help='Show comprehensive status report')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old completed jobs')
    cleanup_parser.add_argument('--days', type=int, default=7, help='Days old threshold (default: 7)')
    
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not args.command:
        parser.error("No command specified")
    
    # Run command
    try:
        if args.command == 'create-individual':
            success = create_individual_backtest(
                script_id=args.script_id,
                market_tag=args.market_tag,
                account_id=args.account_id,
                hours=args.hours,
                job_name=args.job_name
            )
        elif args.command == 'create-individual-cutoff':
            success = create_individual_backtest_with_cutoff(
                script_id=args.script_id,
                market_tag=args.market_tag,
                account_id=args.account_id,
                job_name=args.job_name
            )
        elif args.command == 'create-wfo':
            success = create_wfo_lab(
                script_id=args.script_id,
                market_tag=args.market_tag,
                account_id=args.account_id,
                training_days=args.training_days,
                testing_days=args.testing_days,
                num_periods=args.num_periods,
                wfo_name=args.wfo_name
            )
        elif args.command == 'monitor':
            success = monitor_jobs()
        elif args.command == 'status':
            success = show_status()
        elif args.command == 'cleanup':
            success = cleanup_old_jobs(args.days)
        else:
            parser.error(f"Unknown command: {args.command}")
        
        if success:
            logger.info("Command completed successfully")
            sys.exit(0)
        else:
            logger.error("Command failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Command interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
