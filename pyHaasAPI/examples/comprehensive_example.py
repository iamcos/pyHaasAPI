"""
Comprehensive Example for pyHaasAPI v2

This example demonstrates the complete functionality of pyHaasAPI v2 including:
- Lab analysis and management
- Bot creation and management
- Data dumping and reporting
- Testing data management
- Walk Forward Optimization
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List

from pyHaasAPI_v2 import (
    AsyncHaasClient,
    AuthenticationManager,
    Settings,
    LabService,
    BotService,
    AnalysisService,
    ReportingService,
    DataDumper,
    TestDataManager,
    ReportType,
    ReportFormat,
    ReportConfig,
    DumpConfig,
    DumpFormat,
    TestConfig,
    TestEntity
)
from pyHaasAPI_v2.exceptions import HaasAPIError


async def main():
    """Main example function"""
    print("🚀 pyHaasAPI v2 Comprehensive Example")
    print("=" * 50)
    
    try:
        # Initialize client and authentication
        print("\n1. Initializing Client and Authentication...")
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        auth_manager = AuthenticationManager(client)
        
        # Authenticate (you'll need to set these environment variables)
        email = os.getenv("API_EMAIL", "your_email@example.com")
        password = os.getenv("API_PASSWORD", "your_password")
        
        await auth_manager.authenticate(email, password)
        print("✅ Authentication successful")
        
        # Initialize services
        print("\n2. Initializing Services...")
        from pyHaasAPI_v2.api.lab import LabAPI
        from pyHaasAPI_v2.api.bot import BotAPI
        from pyHaasAPI_v2.api.account import AccountAPI
        from pyHaasAPI_v2.api.script import ScriptAPI
        from pyHaasAPI_v2.api.market import MarketAPI
        from pyHaasAPI_v2.api.backtest import BacktestAPI
        from pyHaasAPI_v2.api.order import OrderAPI
        
        # Initialize API modules
        lab_api = LabAPI(client, auth_manager)
        bot_api = BotAPI(client, auth_manager)
        account_api = AccountAPI(client, auth_manager)
        script_api = ScriptAPI(client, auth_manager)
        market_api = MarketAPI(client, auth_manager)
        backtest_api = BacktestAPI(client, auth_manager)
        order_api = OrderAPI(client, auth_manager)
        
        # Initialize services
        lab_service = LabService(lab_api, backtest_api, script_api, account_api)
        bot_service = BotService(bot_api, account_api, lab_api, backtest_api)
        analysis_service = AnalysisService(lab_api, bot_api, backtest_api, account_api)
        reporting_service = ReportingService()
        data_dumper = DataDumper(lab_api, bot_api, account_api, script_api, market_api, backtest_api, order_api)
        test_manager = TestDataManager(lab_api, bot_api, account_api, script_api, market_api, backtest_api)
        
        print("✅ Services initialized")
        
        # Example 1: List and analyze labs
        print("\n3. Lab Analysis Example...")
        await demonstrate_lab_analysis(lab_api, analysis_service)
        
        # Example 2: Bot recommendations and creation
        print("\n4. Bot Management Example...")
        await demonstrate_bot_management(analysis_service, bot_service)
        
        # Example 3: Data dumping
        print("\n5. Data Dumping Example...")
        await demonstrate_data_dumping(data_dumper)
        
        # Example 4: Reporting
        print("\n6. Reporting Example...")
        await demonstrate_reporting(analysis_service, reporting_service)
        
        # Example 5: Testing data management
        print("\n7. Testing Data Management Example...")
        await demonstrate_testing_data_management(test_manager)
        
        # Example 6: Walk Forward Optimization
        print("\n8. Walk Forward Optimization Example...")
        await demonstrate_wfo_analysis(analysis_service)
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


async def demonstrate_lab_analysis(lab_api, analysis_service):
    """Demonstrate lab analysis functionality"""
    try:
        # Get all labs
        labs = await lab_api.get_labs()
        print(f"Found {len(labs)} labs")
        
        if not labs:
            print("No labs found. Creating a test lab...")
            return
        
        # Analyze the first lab
        lab = labs[0]
        print(f"Analyzing lab: {lab.name} (ID: {lab.lab_id})")
        
        # Perform comprehensive analysis
        analysis_result = await analysis_service.analyze_lab_comprehensive(
            lab_id=lab.lab_id,
            top_count=5,
            min_roi=10.0,
            min_win_rate=30.0,
            min_trades=5
        )
        
        print(f"Analysis Results:")
        print(f"  Total Backtests: {analysis_result.total_backtests}")
        print(f"  Analyzed Backtests: {analysis_result.analyzed_backtests}")
        print(f"  Average ROI: {analysis_result.average_roi:.1f}%")
        print(f"  Best ROI: {analysis_result.best_roi:.1f}%")
        print(f"  Average Win Rate: {analysis_result.average_win_rate:.1f}%")
        print(f"  Total Trades: {analysis_result.total_trades}")
        
        if analysis_result.recommendations:
            print(f"  Recommendations:")
            for i, rec in enumerate(analysis_result.recommendations, 1):
                print(f"    {i}. {rec}")
        
        print("✅ Lab analysis completed")
        
    except Exception as e:
        print(f"❌ Lab analysis failed: {e}")


async def demonstrate_bot_management(analysis_service, bot_service):
    """Demonstrate bot management functionality"""
    try:
        # Get labs for bot recommendations
        from pyHaasAPI_v2.api.lab import LabAPI
        from pyHaasAPI_v2.core.client import AsyncHaasClient
        from pyHaasAPI_v2.core.auth import AuthenticationManager
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        auth_manager = AuthenticationManager(client)
        await auth_manager.authenticate(os.getenv("API_EMAIL", "your_email@example.com"), 
                                      os.getenv("API_PASSWORD", "your_password"))
        
        lab_api = LabAPI(client, auth_manager)
        labs = await lab_api.get_labs()
        
        if not labs:
            print("No labs available for bot recommendations")
            return
        
        lab = labs[0]
        print(f"Generating bot recommendations for lab: {lab.name}")
        
        # Generate bot recommendations
        recommendations = await analysis_service.generate_bot_recommendations(
            lab_id=lab.lab_id,
            max_recommendations=3,
            min_confidence=0.7
        )
        
        if not recommendations:
            print("No bot recommendations generated")
            return
        
        print(f"Generated {len(recommendations)} bot recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec.formatted_bot_name}")
            print(f"     ROI: {rec.roi_percentage:.1f}%")
            print(f"     Win Rate: {rec.win_rate:.1f}%")
            print(f"     Confidence: {rec.confidence_score:.2f}")
            print(f"     Reason: {rec.recommendation_reason}")
        
        # Note: We won't actually create bots in this example to avoid cluttering the system
        print("✅ Bot recommendations generated (not creating actual bots)")
        
    except Exception as e:
        print(f"❌ Bot management failed: {e}")


async def demonstrate_data_dumping(data_dumper):
    """Demonstrate data dumping functionality"""
    try:
        print("Dumping lab data to JSON...")
        
        # Configure dump
        dump_config = DumpConfig(
            format=DumpFormat.JSON,
            output_directory="example_dumps",
            include_metadata=True,
            pretty_print=True,
            max_records=10  # Limit for example
        )
        
        # Dump labs data
        dump_path = await data_dumper.dump_labs_data(dump_config)
        print(f"Labs data dumped to: {dump_path}")
        
        # Dump bots data
        dump_path = await data_dumper.dump_bots_data(dump_config)
        print(f"Bots data dumped to: {dump_path}")
        
        print("✅ Data dumping completed")
        
    except Exception as e:
        print(f"❌ Data dumping failed: {e}")


async def demonstrate_reporting(analysis_service, reporting_service):
    """Demonstrate reporting functionality"""
    try:
        # Get a lab for reporting
        from pyHaasAPI_v2.api.lab import LabAPI
        from pyHaasAPI_v2.core.client import AsyncHaasClient
        from pyHaasAPI_v2.core.auth import AuthenticationManager
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        auth_manager = AuthenticationManager(client)
        await auth_manager.authenticate(os.getenv("API_EMAIL", "your_email@example.com"), 
                                      os.getenv("API_PASSWORD", "your_password"))
        
        lab_api = LabAPI(client, auth_manager)
        labs = await lab_api.get_labs()
        
        if not labs:
            print("No labs available for reporting")
            return
        
        lab = labs[0]
        print(f"Generating reports for lab: {lab.name}")
        
        # Analyze lab
        analysis_result = await analysis_service.analyze_lab_comprehensive(lab.lab_id)
        
        # Generate different report formats
        report_configs = [
            ReportConfig(ReportType.ANALYSIS, ReportFormat.JSON),
            ReportConfig(ReportType.ANALYSIS, ReportFormat.MARKDOWN),
            ReportConfig(ReportType.ANALYSIS, ReportFormat.CSV)
        ]
        
        for config in report_configs:
            report_path = await reporting_service.generate_analysis_report(
                [analysis_result], config
            )
            print(f"Generated {config.format.value} report: {report_path}")
        
        print("✅ Reporting completed")
        
    except Exception as e:
        print(f"❌ Reporting failed: {e}")


async def demonstrate_testing_data_management(test_manager):
    """Demonstrate testing data management functionality"""
    try:
        print("Creating test data...")
        
        # Create test configuration
        test_config = TestConfig(
            entity_type=TestEntity.LAB,
            count=2,
            prefix="EXAMPLE_TEST",
            cleanup_after=True,
            cleanup_delay_hours=1  # Clean up after 1 hour for example
        )
        
        # Create test labs
        test_labs = await test_manager.create_test_labs(test_config)
        print(f"Created {len(test_labs)} test labs")
        
        for lab in test_labs:
            print(f"  Test Lab: {lab.name} (ID: {lab.lab_id})")
        
        # Show created entities
        entities = test_manager.get_created_entities()
        print(f"Total created entities: {len(entities)}")
        
        entity_counts = test_manager.get_entity_count_by_type()
        for entity_type, count in entity_counts.items():
            print(f"  {entity_type}: {count}")
        
        print("✅ Testing data management completed")
        
    except Exception as e:
        print(f"❌ Testing data management failed: {e}")


async def demonstrate_wfo_analysis(analysis_service):
    """Demonstrate Walk Forward Optimization analysis"""
    try:
        # Get a lab for WFO analysis
        from pyHaasAPI_v2.api.lab import LabAPI
        from pyHaasAPI_v2.core.client import AsyncHaasClient
        from pyHaasAPI_v2.core.auth import AuthenticationManager
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        auth_manager = AuthenticationManager(client)
        await auth_manager.authenticate(os.getenv("API_EMAIL", "your_email@example.com"), 
                                      os.getenv("API_PASSWORD", "your_password"))
        
        lab_api = LabAPI(client, auth_manager)
        labs = await lab_api.get_labs()
        
        if not labs:
            print("No labs available for WFO analysis")
            return
        
        lab = labs[0]
        print(f"Performing WFO analysis for lab: {lab.name}")
        
        # Perform WFO analysis
        wfo_result = await analysis_service.perform_walk_forward_optimization(
            lab_id=lab.lab_id,
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now(),
            training_days=180,
            testing_days=60,
            step_days=30
        )
        
        print(f"WFO Analysis Results:")
        print(f"  Total Periods: {wfo_result.total_periods}")
        print(f"  Successful Periods: {wfo_result.successful_periods}")
        print(f"  Failed Periods: {wfo_result.failed_periods}")
        print(f"  Average Period ROI: {wfo_result.average_period_roi:.1f}%")
        print(f"  Best Period ROI: {wfo_result.best_period_roi:.1f}%")
        print(f"  Worst Period ROI: {wfo_result.worst_period_roi:.1f}%")
        print(f"  Stability Score: {wfo_result.stability_score:.2f}")
        print(f"  Out-of-Sample Performance: {wfo_result.out_of_sample_performance:.1f}%")
        
        if wfo_result.recommendations:
            print(f"  Recommendations:")
            for i, rec in enumerate(wfo_result.recommendations, 1):
                print(f"    {i}. {rec}")
        
        print("✅ WFO analysis completed")
        
    except Exception as e:
        print(f"❌ WFO analysis failed: {e}")


if __name__ == "__main__":
    # Set up environment variables for authentication
    # You can also set these in your shell:
    # export API_EMAIL="your_email@example.com"
    # export API_PASSWORD="your_password"
    
    if not os.getenv("API_EMAIL") or not os.getenv("API_PASSWORD"):
        print("⚠️  Please set API_EMAIL and API_PASSWORD environment variables")
        print("   export API_EMAIL='your_email@example.com'")
        print("   export API_PASSWORD='your_password'")
        print("\n   Or modify the script to include your credentials directly")
    
    # Run the example
    asyncio.run(main())
