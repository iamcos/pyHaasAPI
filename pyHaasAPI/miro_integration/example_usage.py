"""
Example Usage of Miro Integration

Demonstrates how to use the Miro integration features:
- Creating comprehensive dashboards
- Monitoring lab progression
- Deploying bots with interactive controls
- Generating automated reports
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

from .client import MiroClient
from .dashboard_manager import DashboardManager, DashboardConfig
from .lab_monitor import LabMonitorConfig
from .bot_deployment import BotDeploymentConfig
from .report_generator import ReportConfig
from ..analysis import HaasAnalyzer, UnifiedCacheManager
from .. import api

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_connections():
    """Setup all required connections"""
    try:
        # Setup HaasOnline API connection
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        
        # Setup Miro client
        miro_client = MiroClient(
            access_token=os.getenv('MIRO_ACCESS_TOKEN'),
            team_id=os.getenv('MIRO_TEAM_ID')
        )
        
        # Initialize analyzer
        cache_manager = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache_manager)
        analyzer.executor = executor
        
        return executor, miro_client, analyzer
        
    except Exception as e:
        logger.error(f"Failed to setup connections: {e}")
        return None, None, None


def example_comprehensive_dashboard():
    """Example: Create a comprehensive dashboard with all features"""
    logger.info("🚀 Creating comprehensive dashboard...")
    
    # Setup connections
    executor, miro_client, analyzer = setup_connections()
    if not all([executor, miro_client, analyzer]):
        return False
    
    try:
        # Configure dashboard
        dashboard_config = DashboardConfig(
            update_interval_minutes=10,
            enable_lab_monitoring=True,
            enable_bot_deployment=True,
            enable_automated_reporting=True
        )
        
        # Create dashboard manager
        dashboard_manager = DashboardManager(miro_client, analyzer, dashboard_config)
        
        # Create comprehensive dashboard
        dashboard = dashboard_manager.create_comprehensive_dashboard("pyHaasAPI Demo Dashboard")
        if not dashboard:
            logger.error("Failed to create dashboard")
            return False
        
        logger.info(f"✅ Created dashboard: {dashboard.name}")
        logger.info(f"🔗 Dashboard URL: https://miro.com/app/board/{dashboard.id}")
        
        # Get labs to monitor
        labs = analyzer.get_labs()
        lab_ids = [getattr(lab, 'lab_id', '') for lab in labs[:5] if hasattr(lab, 'lab_id')]  # Monitor first 5 labs
        
        if lab_ids:
            # Start comprehensive monitoring
            dashboard_manager.start_comprehensive_monitoring(dashboard.id, lab_ids)
            logger.info(f"🚀 Started monitoring for {len(lab_ids)} labs")
            
            # Wait a bit to see initial updates
            logger.info("⏳ Waiting for initial updates...")
            time.sleep(30)
            
            # Create some bots from the best performing lab
            if len(lab_ids) > 0:
                logger.info(f"🤖 Creating bots from lab {lab_ids[0]}...")
                bot_results = dashboard_manager.create_bots_from_lab(
                    dashboard.id, lab_ids[0], top_count=3, activate=False
                )
                logger.info(f"✅ Created {len(bot_results)} bots")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create comprehensive dashboard: {e}")
        return False


def example_lab_monitoring():
    """Example: Set up lab monitoring with real-time updates"""
    logger.info("🧪 Setting up lab monitoring...")
    
    # Setup connections
    executor, miro_client, analyzer = setup_connections()
    if not all([executor, miro_client, analyzer]):
        return False
    
    try:
        from .lab_monitor import LabMonitor
        
        # Configure lab monitoring
        lab_config = LabMonitorConfig(
            update_interval_minutes=5,
            max_labs_per_board=10,
            include_performance_charts=True,
            auto_create_bots=False
        )
        
        # Create lab monitor
        lab_monitor = LabMonitor(miro_client, analyzer, lab_config)
        
        # Create monitoring board
        board = lab_monitor.create_lab_monitoring_board("Lab Monitoring Demo")
        if not board:
            logger.error("Failed to create lab monitoring board")
            return False
        
        logger.info(f"✅ Created lab monitoring board: {board.name}")
        
        # Get labs to monitor
        labs = analyzer.get_labs()
        lab_ids = [getattr(lab, 'lab_id', '') for lab in labs[:3] if hasattr(lab, 'lab_id')]  # Monitor first 3 labs
        
        # Add labs to monitoring
        for lab_id in lab_ids:
            success = lab_monitor.add_lab_to_monitoring(lab_id, board.id)
            if success:
                logger.info(f"✅ Added lab {lab_id} to monitoring")
            else:
                logger.warning(f"⚠️ Failed to add lab {lab_id} to monitoring")
        
        # Start monitoring (this will run continuously)
        logger.info("🚀 Starting lab monitoring...")
        logger.info("Press Ctrl+C to stop monitoring")
        
        try:
            lab_monitor.start_monitoring(board.id)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup lab monitoring: {e}")
        return False


def example_bot_deployment():
    """Example: Deploy bots with interactive Miro controls"""
    logger.info("🤖 Setting up bot deployment...")
    
    # Setup connections
    executor, miro_client, analyzer = setup_connections()
    if not all([executor, miro_client, analyzer]):
        return False
    
    try:
        from .bot_deployment import BotDeploymentCenter
        
        # Configure bot deployment
        bot_config = BotDeploymentConfig(
            default_leverage=20.0,
            default_trade_amount_usdt=2000.0,
            position_mode=1,  # HEDGE
            margin_mode=0,    # CROSS
            auto_activate=False,
            max_bots_per_lab=5
        )
        
        # Create bot deployment center
        bot_deployment = BotDeploymentCenter(miro_client, analyzer, bot_config)
        
        # Create deployment board
        board = bot_deployment.create_bot_deployment_board("Bot Deployment Demo")
        if not board:
            logger.error("Failed to create bot deployment board")
            return False
        
        logger.info(f"✅ Created bot deployment board: {board.name}")
        
        # Get labs for bot creation
        labs = analyzer.get_labs()
        lab_ids = [getattr(lab, 'lab_id', '') for lab in labs[:2] if hasattr(lab, 'lab_id')]  # Use first 2 labs
        
        # Deploy bots from labs
        total_bots_created = 0
        for lab_id in lab_ids:
            logger.info(f"🤖 Creating bots from lab {lab_id}...")
            bot_results = bot_deployment.create_bots_from_lab_analysis(
                lab_id, board.id, top_count=3, activate=False
            )
            
            successful_bots = [bot for bot in bot_results if bot.success]
            total_bots_created += len(successful_bots)
            
            logger.info(f"✅ Created {len(successful_bots)} bots from lab {lab_id}")
            
            # Show bot details
            for bot in successful_bots:
                logger.info(f"  🤖 {bot.bot_name} (ID: {bot.bot_id[:8]})")
        
        logger.info(f"🎉 Total bots created: {total_bots_created}")
        
        # Update bot performance (simulate)
        logger.info("📊 Updating bot performance data...")
        for bot_id in bot_deployment.deployed_bots.keys():
            bot_deployment.update_bot_performance(bot_id, board.id)
            time.sleep(1)  # Rate limiting
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup bot deployment: {e}")
        return False


def example_automated_reporting():
    """Example: Generate automated reports"""
    logger.info("📊 Setting up automated reporting...")
    
    # Setup connections
    executor, miro_client, analyzer = setup_connections()
    if not all([executor, miro_client, analyzer]):
        return False
    
    try:
        from .report_generator import ReportGenerator
        
        # Configure reporting
        report_config = ReportConfig(
            update_interval_hours=1,
            include_performance_charts=True,
            include_recommendations=True,
            max_labs_per_report=20,
            report_format="comprehensive"
        )
        
        # Create report generator
        report_generator = ReportGenerator(miro_client, analyzer, report_config)
        
        # Create reporting board
        board = report_generator.create_reporting_board("Automated Reports Demo")
        if not board:
            logger.error("Failed to create reporting board")
            return False
        
        logger.info(f"✅ Created reporting board: {board.name}")
        
        # Generate comprehensive report
        logger.info("📊 Generating comprehensive report...")
        reports = report_generator.generate_comprehensive_report(board.id)
        
        logger.info(f"✅ Generated {len(reports)} reports:")
        for report_type, report in reports.items():
            logger.info(f"  📋 {report_type}: {report.report_id}")
            logger.info(f"     Summary: {report.summary[:100]}...")
            logger.info(f"     Recommendations: {len(report.recommendations)} items")
        
        # Start automated reporting (this will run continuously)
        logger.info("🚀 Starting automated reporting...")
        logger.info("Press Ctrl+C to stop automated reporting")
        
        try:
            report_generator.start_automated_reporting(board.id)
        except KeyboardInterrupt:
            logger.info("Automated reporting stopped by user")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup automated reporting: {e}")
        return False


def example_webhook_integration():
    """Example: Set up webhook integration for real-time updates"""
    logger.info("🔗 Setting up webhook integration...")
    
    # Setup connections
    executor, miro_client, analyzer = setup_connections()
    if not all([executor, miro_client, analyzer]):
        return False
    
    try:
        # Create a board for webhook testing
        board = miro_client.create_board("Webhook Integration Demo")
        if not board:
            logger.error("Failed to create webhook board")
            return False
        
        logger.info(f"✅ Created webhook board: {board.name}")
        
        # Create webhook (you'll need to set up a webhook endpoint)
        webhook_url = "https://your-webhook-endpoint.com/miro-webhook"
        webhook_id = miro_client.create_webhook(
            board.id, 
            webhook_url,
            events=["board:updated", "item:created", "item:updated"]
        )
        
        if webhook_id:
            logger.info(f"✅ Created webhook: {webhook_id}")
            logger.info(f"🔗 Webhook URL: {webhook_url}")
        else:
            logger.warning("⚠️ Failed to create webhook")
        
        # Create some test items to trigger webhooks
        logger.info("📝 Creating test items...")
        
        # Create a text item
        text_id = miro_client.create_text_item(
            board.id,
            "Test Text Item",
            x=0, y=0,
            width=200, height=100
        )
        
        # Create a card item
        card_id = miro_client.create_card_item(
            board.id,
            "Test Card",
            "This is a test card for webhook integration",
            x=250, y=0,
            width=300, height=200
        )
        
        # Create a button
        button_id = miro_client.create_shape_item(
            board.id,
            "round_rectangle",
            x=0, y=150,
            width=200, height=50,
            content="Test Button",
            style={
                "backgroundColor": "#007ACC",
                "color": "#FFFFFF",
                "fontSize": 14,
                "fontWeight": "bold"
            }
        )
        
        logger.info(f"✅ Created test items:")
        logger.info(f"  📝 Text: {text_id}")
        logger.info(f"  🃏 Card: {card_id}")
        logger.info(f"  🔘 Button: {button_id}")
        
        # Clean up webhook
        if webhook_id:
            miro_client.delete_webhook(webhook_id)
            logger.info("🧹 Cleaned up webhook")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup webhook integration: {e}")
        return False


def main():
    """Main example runner"""
    print("🚀 pyHaasAPI Miro Integration Examples")
    print("=" * 50)
    
    examples = [
        ("Comprehensive Dashboard", example_comprehensive_dashboard),
        ("Lab Monitoring", example_lab_monitoring),
        ("Bot Deployment", example_bot_deployment),
        ("Automated Reporting", example_automated_reporting),
        ("Webhook Integration", example_webhook_integration)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n0. Run all examples")
    print("q. Quit")
    
    while True:
        try:
            choice = input("\nSelect an example (0-{} or q): ".format(len(examples))).strip().lower()
            
            if choice == 'q':
                print("👋 Goodbye!")
                break
            elif choice == '0':
                # Run all examples
                for name, example_func in examples:
                    print(f"\n{'='*20} {name} {'='*20}")
                    try:
                        example_func()
                    except Exception as e:
                        logger.error(f"Example '{name}' failed: {e}")
                    print(f"{'='*50}")
                break
            else:
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(examples):
                        name, example_func = examples[choice_num - 1]
                        print(f"\n{'='*20} {name} {'='*20}")
                        example_func()
                        print(f"{'='*50}")
                        break
                    else:
                        print("❌ Invalid choice. Please try again.")
                except ValueError:
                    print("❌ Invalid input. Please try again.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            break


if __name__ == '__main__':
    main()
