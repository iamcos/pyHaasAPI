"""
CLI Interface for Miro Integration

Provides command-line interface for Miro integration features:
- Dashboard creation and management
- Lab monitoring setup
- Bot deployment automation
- Report generation
"""

import argparse
import logging
import sys
from typing import List, Optional
from datetime import datetime

from .client import MiroClient
from .dashboard_manager import DashboardManager, DashboardConfig
from .lab_monitor import LabMonitorConfig
from .bot_deployment import BotDeploymentConfig
from .report_generator import ReportConfig
from ..analysis import HaasAnalyzer, UnifiedCacheManager
from .. import api
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_haas_connection():
    """Setup HaasOnline API connection"""
    try:
        # Create API connection
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        
        # Authenticate
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        
        return executor
        
    except Exception as e:
        logger.error(f"Failed to connect to HaasOnline API: {e}")
        return None


def setup_miro_client():
    """Setup Miro API client"""
    try:
        access_token = os.getenv('MIRO_ACCESS_TOKEN')
        team_id = os.getenv('MIRO_TEAM_ID')
        
        if not access_token:
            logger.error("MIRO_ACCESS_TOKEN environment variable not set")
            return None
        
        return MiroClient(access_token, team_id)
        
    except Exception as e:
        logger.error(f"Failed to setup Miro client: {e}")
        return None


def create_dashboard(args):
    """Create a comprehensive Miro dashboard"""
    try:
        # Setup connections
        executor = setup_haas_connection()
        if not executor:
            return False
        
        miro_client = setup_miro_client()
        if not miro_client:
            return False
        
        # Initialize analyzer
        cache_manager = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache_manager)
        analyzer.executor = executor
        
        # Create dashboard manager
        dashboard_config = DashboardConfig(
            update_interval_minutes=args.update_interval,
            enable_lab_monitoring=args.enable_lab_monitoring,
            enable_bot_deployment=args.enable_bot_deployment,
            enable_automated_reporting=args.enable_reporting
        )
        
        dashboard_manager = DashboardManager(miro_client, analyzer, dashboard_config)
        
        # Create dashboard
        dashboard = dashboard_manager.create_comprehensive_dashboard(args.dashboard_name)
        if not dashboard:
            logger.error("Failed to create dashboard")
            return False
        
        logger.info(f"✅ Created dashboard: {dashboard.name} (ID: {dashboard.id})")
        logger.info(f"🔗 Dashboard URL: https://miro.com/app/board/{dashboard.id}")
        
        # Start monitoring if requested
        if args.start_monitoring:
            # Get labs to monitor
            labs = analyzer.get_labs()
            lab_ids = [getattr(lab, 'lab_id', '') for lab in labs if hasattr(lab, 'lab_id')]
            
            if lab_ids:
                dashboard_manager.start_comprehensive_monitoring(dashboard.id, lab_ids)
                logger.info(f"🚀 Started comprehensive monitoring for {len(lab_ids)} labs")
            else:
                logger.warning("No labs found to monitor")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create dashboard: {e}")
        return False


def monitor_labs(args):
    """Monitor specific labs on Miro board"""
    try:
        # Setup connections
        executor = setup_haas_connection()
        if not executor:
            return False
        
        miro_client = setup_miro_client()
        if not miro_client:
            return False
        
        # Initialize analyzer
        cache_manager = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache_manager)
        analyzer.executor = executor
        
        # Create lab monitor
        lab_config = LabMonitorConfig(
            update_interval_minutes=args.update_interval,
            max_labs_per_board=args.max_labs
        )
        
        from .lab_monitor import LabMonitor
        lab_monitor = LabMonitor(miro_client, analyzer, lab_config)
        
        # Create monitoring board
        board = lab_monitor.create_lab_monitoring_board(args.board_name)
        if not board:
            logger.error("Failed to create lab monitoring board")
            return False
        
        logger.info(f"✅ Created lab monitoring board: {board.name} (ID: {board.id})")
        
        # Add labs to monitoring
        for lab_id in args.lab_ids:
            success = lab_monitor.add_lab_to_monitoring(lab_id, board.id)
            if success:
                logger.info(f"✅ Added lab {lab_id} to monitoring")
            else:
                logger.warning(f"⚠️ Failed to add lab {lab_id} to monitoring")
        
        # Start monitoring
        if args.start_monitoring:
            logger.info("🚀 Starting lab monitoring...")
            lab_monitor.start_monitoring(board.id)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to monitor labs: {e}")
        return False


def deploy_bots(args):
    """Deploy bots from lab analysis"""
    try:
        # Setup connections
        executor = setup_haas_connection()
        if not executor:
            return False
        
        miro_client = setup_miro_client()
        if not miro_client:
            return False
        
        # Initialize analyzer
        cache_manager = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache_manager)
        analyzer.executor = executor
        
        # Create bot deployment center
        bot_config = BotDeploymentConfig(
            default_leverage=args.leverage,
            default_trade_amount_usdt=args.trade_amount,
            auto_activate=args.activate,
            max_bots_per_lab=args.max_bots
        )
        
        from .bot_deployment import BotDeploymentCenter
        bot_deployment = BotDeploymentCenter(miro_client, analyzer, bot_config)
        
        # Create deployment board
        board = bot_deployment.create_bot_deployment_board(args.board_name)
        if not board:
            logger.error("Failed to create bot deployment board")
            return False
        
        logger.info(f"✅ Created bot deployment board: {board.name} (ID: {board.id})")
        
        # Deploy bots from labs
        total_bots_created = 0
        for lab_id in args.lab_ids:
            logger.info(f"🤖 Creating bots from lab {lab_id}...")
            bot_results = bot_deployment.create_bots_from_lab_analysis(
                lab_id, board.id, args.top_count, args.activate
            )
            
            successful_bots = [bot for bot in bot_results if bot.success]
            total_bots_created += len(successful_bots)
            
            logger.info(f"✅ Created {len(successful_bots)} bots from lab {lab_id}")
        
        logger.info(f"🎉 Total bots created: {total_bots_created}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to deploy bots: {e}")
        return False


def generate_reports(args):
    """Generate automated reports"""
    try:
        # Setup connections
        executor = setup_haas_connection()
        if not executor:
            return False
        
        miro_client = setup_miro_client()
        if not miro_client:
            return False
        
        # Initialize analyzer
        cache_manager = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache_manager)
        analyzer.executor = executor
        
        # Create report generator
        report_config = ReportConfig(
            update_interval_hours=args.update_interval,
            include_performance_charts=args.include_charts,
            include_recommendations=args.include_recommendations
        )
        
        from .report_generator import ReportGenerator
        report_generator = ReportGenerator(miro_client, analyzer, report_config)
        
        # Create reporting board
        board = report_generator.create_reporting_board(args.board_name)
        if not board:
            logger.error("Failed to create reporting board")
            return False
        
        logger.info(f"✅ Created reporting board: {board.name} (ID: {board.id})")
        
        # Generate reports
        if args.report_type == "all":
            reports = report_generator.generate_comprehensive_report(board.id)
            logger.info(f"📊 Generated {len(reports)} comprehensive reports")
        elif args.report_type == "labs":
            report = report_generator.generate_lab_analysis_report(board.id, args.lab_ids)
            if report:
                logger.info(f"📊 Generated lab analysis report: {report.report_id}")
        elif args.report_type == "bots":
            report = report_generator.generate_bot_performance_report(board.id, args.bot_ids)
            if report:
                logger.info(f"📊 Generated bot performance report: {report.report_id}")
        elif args.report_type == "system":
            report = report_generator.generate_system_status_report(board.id)
            if report:
                logger.info(f"📊 Generated system status report: {report.report_id}")
        
        # Start automated reporting if requested
        if args.start_automated:
            logger.info("🚀 Starting automated reporting...")
            report_generator.start_automated_reporting(board.id)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate reports: {e}")
        return False


def list_boards(args):
    """List available Miro boards"""
    try:
        miro_client = setup_miro_client()
        if not miro_client:
            return False
        
        boards = miro_client.get_boards()
        
        if not boards:
            logger.info("No boards found")
            return True
        
        logger.info(f"📋 Found {len(boards)} boards:")
        for board in boards:
            logger.info(f"  • {board.name} (ID: {board.id})")
            if board.description:
                logger.info(f"    Description: {board.description}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to list boards: {e}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="pyHaasAPI Miro Integration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create comprehensive dashboard
  python -m pyHaasAPI.miro_integration.cli create-dashboard --start-monitoring
  
  # Monitor specific labs
  python -m pyHaasAPI.miro_integration.cli monitor-labs --lab-ids lab1,lab2 --start-monitoring
  
  # Deploy bots from labs
  python -m pyHaasAPI.miro_integration.cli deploy-bots --lab-ids lab1,lab2 --activate
  
  # Generate reports
  python -m pyHaasAPI.miro_integration.cli generate-reports --report-type all
  
  # List available boards
  python -m pyHaasAPI.miro_integration.cli list-boards
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create dashboard command
    create_parser = subparsers.add_parser('create-dashboard', help='Create comprehensive dashboard')
    create_parser.add_argument('--dashboard-name', help='Dashboard name')
    create_parser.add_argument('--update-interval', type=int, default=15, help='Update interval in minutes')
    create_parser.add_argument('--enable-lab-monitoring', action='store_true', default=True, help='Enable lab monitoring')
    create_parser.add_argument('--enable-bot-deployment', action='store_true', default=True, help='Enable bot deployment')
    create_parser.add_argument('--enable-reporting', action='store_true', default=True, help='Enable automated reporting')
    create_parser.add_argument('--start-monitoring', action='store_true', help='Start monitoring immediately')
    
    # Monitor labs command
    monitor_parser = subparsers.add_parser('monitor-labs', help='Monitor specific labs')
    monitor_parser.add_argument('--lab-ids', required=True, help='Comma-separated lab IDs')
    monitor_parser.add_argument('--board-name', help='Board name')
    monitor_parser.add_argument('--update-interval', type=int, default=15, help='Update interval in minutes')
    monitor_parser.add_argument('--max-labs', type=int, default=20, help='Maximum labs per board')
    monitor_parser.add_argument('--start-monitoring', action='store_true', help='Start monitoring immediately')
    
    # Deploy bots command
    deploy_parser = subparsers.add_parser('deploy-bots', help='Deploy bots from lab analysis')
    deploy_parser.add_argument('--lab-ids', required=True, help='Comma-separated lab IDs')
    deploy_parser.add_argument('--board-name', help='Board name')
    deploy_parser.add_argument('--top-count', type=int, default=5, help='Number of top backtests to use')
    deploy_parser.add_argument('--leverage', type=float, default=20.0, help='Default leverage')
    deploy_parser.add_argument('--trade-amount', type=float, default=2000.0, help='Default trade amount in USDT')
    deploy_parser.add_argument('--max-bots', type=int, default=5, help='Maximum bots per lab')
    deploy_parser.add_argument('--activate', action='store_true', help='Activate bots immediately')
    
    # Generate reports command
    reports_parser = subparsers.add_parser('generate-reports', help='Generate automated reports')
    reports_parser.add_argument('--report-type', choices=['all', 'labs', 'bots', 'system'], default='all', help='Report type')
    reports_parser.add_argument('--board-name', help='Board name')
    reports_parser.add_argument('--lab-ids', help='Comma-separated lab IDs (for lab reports)')
    reports_parser.add_argument('--bot-ids', help='Comma-separated bot IDs (for bot reports)')
    reports_parser.add_argument('--update-interval', type=int, default=6, help='Update interval in hours')
    reports_parser.add_argument('--include-charts', action='store_true', default=True, help='Include performance charts')
    reports_parser.add_argument('--include-recommendations', action='store_true', default=True, help='Include recommendations')
    reports_parser.add_argument('--start-automated', action='store_true', help='Start automated reporting')
    
    # List boards command
    list_parser = subparsers.add_parser('list-boards', help='List available Miro boards')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    success = False
    
    if args.command == 'create-dashboard':
        success = create_dashboard(args)
    elif args.command == 'monitor-labs':
        # Parse lab IDs
        args.lab_ids = [lab_id.strip() for lab_id in args.lab_ids.split(',')]
        success = monitor_labs(args)
    elif args.command == 'deploy-bots':
        # Parse lab IDs
        args.lab_ids = [lab_id.strip() for lab_id in args.lab_ids.split(',')]
        success = deploy_bots(args)
    elif args.command == 'generate-reports':
        # Parse optional IDs
        if args.lab_ids:
            args.lab_ids = [lab_id.strip() for lab_id in args.lab_ids.split(',')]
        if args.bot_ids:
            args.bot_ids = [bot_id.strip() for bot_id in args.bot_ids.split(',')]
        success = generate_reports(args)
    elif args.command == 'list-boards':
        success = list_boards(args)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
