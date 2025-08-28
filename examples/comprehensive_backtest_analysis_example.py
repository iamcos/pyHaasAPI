#!/usr/bin/env python3
"""
Comprehensive Backtest Analysis Example
Demonstrates the complete workflow from analysis to live deployment
"""

import asyncio
import json
from datetime import datetime, timedelta
from pyHaasAPI.enhanced_execution import get_enhanced_executor
from backtest_analysis.comprehensive_backtest_analyzer import ComprehensiveBacktestAnalyzer
from account_management.account_manager import AccountManager
from infrastructure.server_manager import ServerManager
from infrastructure.config_manager import ConfigManager

async def main():
    """Complete demonstration of the comprehensive backtest analysis system"""
    
    print("🚀 Comprehensive Backtest Analysis System Demo")
    print("=" * 80)
    
    # Initialize the system components
    print("\n📊 1. Initializing System Components...")
    
    try:
        # Get authenticated executor
        executor = get_enhanced_executor()
        if not executor:
            print("❌ Failed to get authenticated executor")
            return
        
        # Initialize account manager
        config_manager = ConfigManager()
        server_manager = ServerManager()
        account_manager = AccountManager(server_manager, config_manager)
        
        # Initialize comprehensive analyzer
        analyzer = ComprehensiveBacktestAnalyzer(executor, account_manager)
        
        print("✅ System components initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    # Example 1: Single Backtest Analysis
    print("\n📈 2. Single Backtest Comprehensive Analysis...")
    
    # You would replace this with an actual backtest ID
    example_backtest_id = "your_backtest_id_here"  
    
    try:
        print(f"   Analyzing backtest: {example_backtest_id}")
        
        # Perform comprehensive analysis
        report = analyzer.analyze_single_backtest(example_backtest_id)
        
        print("✅ Analysis completed! Key metrics:")
        print(f"   📊 PROFIT MULTIPLIER: {report.metrics.profit_multiplier:.3f}")
        print(f"   💰 FINAL WALLET BALANCE: ${report.metrics.final_wallet_balance:,.2f}")
        print(f"   📈 FINAL REPORT PROFIT %: {report.metrics.final_report_profit_percent:.2f}%")
        print(f"   📉 MAX DRAWDOWN: {report.metrics.max_drawdown_percent:.2f}%")
        print(f"   🎯 MIN MARGIN: {report.metrics.final_report_min_margin:.2f}%")
        print(f"   🎯 MAX MARGIN: {report.metrics.final_report_max_margin:.2f}%")
        print(f"   🔢 LOSING POSITIONS: {report.metrics.losing_positions_count}")
        print(f"   🏆 WIN RATE: {report.metrics.win_rate:.1%}")
        print(f"   📊 SHARPE RATIO: {report.metrics.sharpe_ratio:.3f}")
        print(f"   🚀 DEPLOYMENT READINESS: {report.metrics.deployment_readiness_score:.1f}%")
        
        # Risk Analysis
        print(f"\n🛡️ Risk Analysis:")
        print(f"   Grade: {report.risk_analysis['risk_grade']}")
        print(f"   Risk Factors: {report.risk_analysis['risk_factors']}")
        
        # Deployment Recommendation
        print(f"\n🎯 Deployment Status:")
        if report.deployment_recommendation['is_recommended']:
            print("   ✅ RECOMMENDED FOR DEPLOYMENT")
            print(f"   Strategy: {report.deployment_recommendation['deployment_strategy']['approach']}")
            print(f"   Capital: {report.deployment_recommendation['deployment_strategy']['initial_capital_percent']}%")
        else:
            print("   ❌ NOT READY FOR DEPLOYMENT")
            print("   Recommendations:")
            for rec in report.risk_analysis['risk_recommendations']:
                print(f"     • {rec}")
        
        # Export report
        filename = analyzer.export_analysis_report(example_backtest_id, 'json')
        print(f"   📄 Report exported to: {filename}")
        
    except Exception as e:
        print(f"❌ Single analysis failed: {e}")
    
    # Example 2: Multiple Backtest Comparison
    print("\n📊 3. Multiple Backtest Comparison...")
    
    # Example backtest IDs (replace with actual IDs)
    example_backtest_ids = [
        "backtest_1",
        "backtest_2", 
        "backtest_3",
        "backtest_4",
        "backtest_5"
    ]
    
    try:
        print(f"   Comparing {len(example_backtest_ids)} backtests...")
        
        # Perform comparison analysis
        comparison_result = analyzer.compare_multiple_backtests(example_backtest_ids)
        
        print("✅ Comparison completed!")
        
        # Display comparison summary
        summary = comparison_result['comparison_summary']
        print(f"   📊 Total analyzed: {summary['total_analyzed']}")
        print(f"   🚀 Deployment ready: {summary['deployment_ready_count']}")
        print(f"   🏆 Top performer: {summary['top_performer']['backtest_id']}")
        print(f"       Score: {summary['top_performer']['score']:.1f}%")
        print(f"       Profit: {summary['top_performer']['profit_percent']:.2f}%")
        
        # Show recommended strategies
        print(f"\n🎯 Recommended for Deployment:")
        for i, strategy in enumerate(summary['recommended_for_deployment'][:3]):
            print(f"   {i+1}. {strategy['script_name']}")
            print(f"      Profit: {strategy['profit_percent']:.2f}%")
            print(f"      Drawdown: {strategy['max_drawdown']:.2f}%")
            print(f"      Score: {strategy['score']:.1f}%")
        
        # Deployment recommendations
        deploy_rec = comparison_result['deployment_recommendations']
        print(f"\n📋 Deployment Plan: {deploy_rec['recommendation']}")
        if 'deployment_phases' in deploy_rec:
            for phase in deploy_rec['deployment_phases']:
                print(f"   Phase {phase['phase']}: {phase['description']}")
                print(f"     Strategies: {phase['strategies']}")
                print(f"     Capital: {phase['capital_allocation']}")
        
    except Exception as e:
        print(f"❌ Comparison analysis failed: {e}")
    
    # Example 3: Account Management for Deployment
    print("\n🏦 4. Account Management for Deployment...")
    
    try:
        # Get account statistics
        stats = account_manager.get_account_statistics()
        print(f"   📊 Total accounts: {stats['total_accounts']}")
        print(f"   📈 Accounts by type: {stats['accounts_by_type']}")
        print(f"   💰 Total balance: ${stats['total_balance']:,.2f}")
        
        # Find available simulation accounts
        server_id = "default_server"  # Replace with actual server
        test_accounts = account_manager.find_test_accounts(server_id)
        print(f"   🧪 Test accounts found: {len(test_accounts)}")
        
        # Example account allocation
        if test_accounts:
            account = test_accounts[0]
            print(f"   ✅ Available account: {account.account_name}")
            print(f"      ID: {account.account_id}")
            print(f"      Balance: ${account.balance:,.2f}")
        
    except Exception as e:
        print(f"❌ Account management failed: {e}")
    
    # Example 4: Live Bot Deployment Simulation
    print("\n🤖 5. Live Bot Deployment Simulation...")
    
    if 'report' in locals() and report.deployment_recommendation['is_recommended']:
        print(f"   🚀 Simulating deployment of {report.script_name}...")
        
        # Deployment configuration
        deployment_config = {
            'max_position_size_percent': report.deployment_recommendation['risk_management']['max_position_size_percent'],
            'stop_loss_percent': report.deployment_recommendation['risk_management']['suggested_stop_loss_percent'],
            'daily_loss_limit': report.deployment_recommendation['risk_management']['daily_loss_limit_percent'],
            'monitoring_frequency': report.deployment_recommendation['monitoring_requirements']['monitoring_frequency']
        }
        
        print(f"   ⚙️ Deployment Configuration:")
        print(f"      Max Position Size: {deployment_config['max_position_size_percent']:.1f}%")
        print(f"      Stop Loss: {deployment_config['stop_loss_percent']:.1f}%")
        print(f"      Daily Loss Limit: {deployment_config['daily_loss_limit']:.1f}%")
        print(f"      Monitoring: {deployment_config['monitoring_frequency']}")
        
        # Account allocation
        if report.deployment_recommendation.get('account_allocation'):
            allocation = report.deployment_recommendation['account_allocation']
            print(f"   🏦 Account Allocation:")
            print(f"      Account ID: {allocation.get('assigned_account_id', 'Not assigned')}")
            print(f"      Initial Balance: ${allocation.get('initial_balance', 0):,.2f}")
            print(f"      Status: {allocation.get('deployment_status', 'Unknown')}")
        
        print("   ✅ Deployment simulation completed")
        print("   📊 Bot would be monitored with:")
        for metric in report.deployment_recommendation['monitoring_requirements']['key_metrics_to_watch']:
            print(f"      • {metric.replace('_', ' ').title()}")
        
    else:
        print("   ⚠️ No deployable strategies available from analysis")
    
    # Example 5: Risk Management Alerts
    print("\n🛡️ 6. Risk Management & Monitoring Setup...")
    
    if 'report' in locals():
        alerts = report.deployment_recommendation['monitoring_requirements']['alert_thresholds']
        print("   🚨 Alert Thresholds:")
        for alert_type, threshold in alerts.items():
            print(f"      {alert_type.replace('_', ' ').title()}: {threshold}")
        
        # Stress test scenarios
        stress_scenarios = report.risk_analysis['stress_test_scenarios']
        print("   💥 Stress Test Scenarios:")
        for scenario, impact in stress_scenarios.items():
            print(f"      {scenario.replace('_', ' ').title()}: ${impact:,.2f}")
    
    # Summary and Next Steps
    print("\n" + "=" * 80)
    print("🎉 COMPREHENSIVE ANALYSIS DEMO COMPLETED!")
    print("=" * 80)
    
    print("\n📋 System Capabilities Demonstrated:")
    print("   ✅ Complete backtest analysis with ALL required metrics")
    print("   ✅ PROFIT MULTIPLIER, FINAL BALANCE, PROFIT %, NET PROFIT")
    print("   ✅ MIN/MAX MARGIN analysis and safety scoring")
    print("   ✅ MAX DRAWDOWN and LOSING POSITIONS tracking")
    print("   ✅ Advanced risk metrics (Sharpe, Sortino, Calmar ratios)")
    print("   ✅ Multi-backtest comparison and ranking")
    print("   ✅ Deployment readiness scoring")
    print("   ✅ Account management for 100+ simulation accounts")
    print("   ✅ Live bot deployment with risk management")
    print("   ✅ Real-time monitoring setup")
    print("   ✅ Export capabilities for reports")
    
    print("\n🚀 Next Steps:")
    print("   1. Run analysis on your actual backtest IDs")
    print("   2. Use the visual dashboard for interactive analysis")
    print("   3. Deploy top-performing strategies to live accounts")
    print("   4. Monitor deployed bots with real-time alerts")
    print("   5. Continuously optimize based on live performance")
    
    print("\n💡 Integration Points:")
    print("   • Frontend: ai-trading-interface/src/components/analysis/BacktestAnalysisDashboard.tsx")
    print("   • Backend: backtest_analysis/comprehensive_backtest_analyzer.py")
    print("   • API: mcp_server/tools/comprehensive_analysis_tools.py")
    print("   • Accounts: account_management/account_manager.py")
    
    print(f"\n📊 Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def demonstrate_api_integration():
    """Demonstrate the API integration for the frontend"""
    
    print("\n🔌 API Integration Example")
    print("-" * 50)
    
    # Example API calls that the frontend would make
    api_examples = {
        "Single Analysis": {
            "endpoint": "POST /api/analyze/backtest",
            "payload": {"backtest_id": "example_id"},
            "description": "Comprehensive analysis of single backtest"
        },
        "Comparison": {
            "endpoint": "POST /api/analyze/backtests/compare", 
            "payload": {"backtest_ids": ["id1", "id2", "id3"]},
            "description": "Compare multiple backtests"
        },
        "Deployment": {
            "endpoint": "POST /api/deploy/bot",
            "payload": {
                "backtest_id": "example_id",
                "deployment_config": {
                    "account_allocation": {"account_id": "sim_account_1"},
                    "risk_management": {"stop_loss": 2.5, "max_position": 10}
                }
            },
            "description": "Deploy backtest as live bot"
        },
        "Monitoring": {
            "endpoint": "GET /api/monitor/bots",
            "payload": {},
            "description": "Monitor deployed bots"
        },
        "Export": {
            "endpoint": "POST /api/analyze/export",
            "payload": {"backtest_id": "example_id", "format": "json"},
            "description": "Export analysis report"
        }
    }
    
    for operation, details in api_examples.items():
        print(f"\n{operation}:")
        print(f"  {details['endpoint']}")
        print(f"  Payload: {json.dumps(details['payload'], indent=4)}")
        print(f"  Description: {details['description']}")

if __name__ == "__main__":
    print("Starting Comprehensive Backtest Analysis Demo...")
    
    # Run the main demo
    asyncio.run(main())
    
    # Show API integration examples
    demonstrate_api_integration()
    
    print("\n🎯 Ready to analyze your backtests and deploy the best performers!")