#!/usr/bin/env python3
"""
Main runner for the Comprehensive Backtest Analysis System
This is your primary entry point to run the analysis
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print system banner"""
    print("🚀 Comprehensive Backtest Analysis System")
    print("=" * 60)
    print("📊 Analyzes backtests with ALL required metrics")
    print("🎯 Deploys best performers to live accounts")
    print("🛡️ Advanced risk management and monitoring")
    print("=" * 60)

def get_user_choice():
    """Get user's choice for what to run"""
    print("\n🎯 What would you like to do?")
    print("1. 📊 Analyze a single backtest")
    print("2. 📈 Compare multiple backtests")
    print("3. 🏦 Check available accounts") 
    print("4. 🤖 View deployed bots status")
    print("5. 📋 Run full system demo")
    print("6. 🔧 Start MCP server")
    print("7. 🌐 Start React dashboard")
    print("0. ❌ Exit")
    
    try:
        choice = int(input("\nEnter your choice (0-7): "))
        return choice
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return get_user_choice()

async def analyze_single_backtest():
    """Analyze a single backtest"""
    print("\n📊 Single Backtest Analysis")
    print("-" * 40)
    
    try:
        # Import the analyzer
        from pyHaasAPI.enhanced_execution import get_enhanced_executor
        from backtest_analysis.comprehensive_backtest_analyzer import ComprehensiveBacktestAnalyzer
        from account_management.account_manager import AccountManager
        from infrastructure.server_manager import ServerManager
        from infrastructure.config_manager import ConfigManager
        
        # Get backtest ID from user
        backtest_id = input("Enter backtest ID: ").strip()
        if not backtest_id:
            print("❌ Backtest ID is required")
            return
        
        print(f"\n🔄 Analyzing backtest: {backtest_id}")
        
        # Initialize system
        executor = get_enhanced_executor()
        if not executor:
            print("❌ Failed to get authenticated executor")
            print("💡 Check your API credentials in .env file")
            return
        
        # Initialize components
        config_manager = ConfigManager()
        server_manager = ServerManager()
        account_manager = AccountManager(server_manager, config_manager)
        analyzer = ComprehensiveBacktestAnalyzer(executor, account_manager)
        
        # Perform analysis
        report = analyzer.analyze_single_backtest(backtest_id)
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 ANALYSIS RESULTS")
        print("=" * 60)
        
        print(f"\n💰 CORE METRICS:")
        print(f"   PROFIT MULTIPLIER: {report.metrics.profit_multiplier:.3f}")
        print(f"   FINAL WALLET BALANCE: ${report.metrics.final_wallet_balance:,.2f}")
        print(f"   FINAL REPORT PROFIT %: {report.metrics.final_report_profit_percent:.2f}%")
        print(f"   FINAL REPORT NET BOT PROFIT: ${report.metrics.final_report_net_bot_profit:.2f}")
        
        print(f"\n📊 MARGIN ANALYSIS:")
        print(f"   FINAL REPORT MIN MARGIN: {report.metrics.final_report_min_margin:.2f}%")
        print(f"   FINAL REPORT MAX MARGIN: {report.metrics.final_report_max_margin:.2f}%")
        print(f"   MARGIN SAFETY SCORE: {report.metrics.margin_safety_score:.1f}/100")
        
        print(f"\n⚠️  RISK METRICS:")
        print(f"   MAX DRAWDOWN: {report.metrics.max_drawdown_percent:.2f}%")
        print(f"   LOSING POSITIONS: {report.metrics.losing_positions_count}")
        print(f"   WIN RATE: {report.metrics.win_rate:.1%}")
        print(f"   SHARPE RATIO: {report.metrics.sharpe_ratio:.3f}")
        
        print(f"\n🎯 DEPLOYMENT ASSESSMENT:")
        print(f"   READINESS SCORE: {report.metrics.deployment_readiness_score:.1f}%")
        print(f"   RISK GRADE: {report.risk_analysis['risk_grade']}")
        
        if report.deployment_recommendation['is_recommended']:
            print("   STATUS: ✅ RECOMMENDED FOR DEPLOYMENT")
            if report.deployment_recommendation.get('account_allocation'):
                allocation = report.deployment_recommendation['account_allocation']
                print(f"   ACCOUNT: {allocation.get('assigned_account_id', 'Not assigned')}")
        else:
            print("   STATUS: ❌ NOT READY FOR DEPLOYMENT")
            print("   RECOMMENDATIONS:")
            for rec in report.risk_analysis['risk_recommendations'][:3]:
                print(f"     • {rec}")
        
        # Export option
        export = input("\n💾 Export detailed report? (y/n): ").lower().strip()
        if export == 'y':
            filename = analyzer.export_analysis_report(backtest_id, 'json')
            print(f"✅ Report exported to: {filename}")
        
        print("\n✅ Analysis completed!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("💡 Check your backtest ID and API connection")

async def compare_multiple_backtests():
    """Compare multiple backtests"""
    print("\n📈 Multiple Backtest Comparison")
    print("-" * 40)
    
    try:
        # Get backtest IDs
        print("Enter backtest IDs (comma-separated):")
        ids_input = input("IDs: ").strip()
        if not ids_input:
            print("❌ Backtest IDs are required")
            return
        
        backtest_ids = [id.strip() for id in ids_input.split(',')]
        print(f"\n🔄 Comparing {len(backtest_ids)} backtests...")
        
        # Initialize and run comparison
        from pyHaasAPI.enhanced_execution import get_enhanced_executor
        from backtest_analysis.comprehensive_backtest_analyzer import ComprehensiveBacktestAnalyzer
        from account_management.account_manager import AccountManager
        from infrastructure.server_manager import ServerManager
        from infrastructure.config_manager import ConfigManager
        
        executor = get_enhanced_executor()
        config_manager = ConfigManager()
        server_manager = ServerManager()
        account_manager = AccountManager(server_manager, config_manager)
        analyzer = ComprehensiveBacktestAnalyzer(executor, account_manager)
        
        comparison_result = analyzer.compare_multiple_backtests(backtest_ids)
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 COMPARISON RESULTS")
        print("=" * 60)
        
        summary = comparison_result['comparison_summary']
        print(f"\n📊 SUMMARY:")
        print(f"   Total analyzed: {summary['total_analyzed']}")
        print(f"   Deployment ready: {summary['deployment_ready_count']}")
        print(f"   Top performer: {summary['top_performer']['backtest_id']}")
        print(f"     Score: {summary['top_performer']['score']:.1f}%")
        print(f"     Profit: {summary['top_performer']['profit_percent']:.2f}%")
        
        print(f"\n🏆 TOP 3 PERFORMERS:")
        for i, strategy in enumerate(summary['recommended_for_deployment'][:3], 1):
            print(f"   {i}. {strategy['script_name']}")
            print(f"      Profit: {strategy['profit_percent']:.2f}%")
            print(f"      Drawdown: {strategy['max_drawdown']:.2f}%")
            print(f"      Score: {strategy['score']:.1f}%")
        
        # Deployment recommendations
        deploy_rec = comparison_result['deployment_recommendations']
        print(f"\n🚀 DEPLOYMENT PLAN: {deploy_rec['recommendation']}")
        if 'deployment_phases' in deploy_rec:
            for phase in deploy_rec['deployment_phases']:
                print(f"   Phase {phase['phase']}: {phase['description']}")
                print(f"     Strategies: {phase['strategies']}")
                print(f"     Capital: {phase['capital_allocation']}")
        
        print("\n✅ Comparison completed!")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")

async def check_available_accounts():
    """Check available simulation accounts"""
    print("\n🏦 Available Accounts Check")
    print("-" * 40)
    
    try:
        from account_management.account_manager import AccountManager
        from infrastructure.server_manager import ServerManager
        from infrastructure.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        server_manager = ServerManager()
        account_manager = AccountManager(server_manager, config_manager)
        
        # Get account statistics
        stats = account_manager.get_account_statistics()
        
        print(f"\n📊 ACCOUNT SUMMARY:")
        print(f"   Total accounts: {stats['total_accounts']}")
        print(f"   Total balance: ${stats['total_balance']:,.2f}")
        print(f"   Average balance: ${stats['average_balance']:,.2f}")
        
        print(f"\n📈 BY TYPE:")
        for acc_type, count in stats['accounts_by_type'].items():
            print(f"   {acc_type.title()}: {count}")
        
        print(f"\n🔄 BY STATUS:")
        for status, count in stats['accounts_by_status'].items():
            print(f"   {status.title()}: {count}")
        
        # Show server breakdown
        print(f"\n🖥️  BY SERVER:")
        for server_id, server_stats in stats['accounts_by_server'].items():
            print(f"   {server_id}: {server_stats['total']} accounts")
            print(f"     Balance: ${server_stats['total_balance']:,.2f}")
        
        print("\n✅ Account check completed!")
        
    except Exception as e:
        print(f"❌ Account check failed: {e}")

async def view_deployed_bots():
    """View status of deployed bots"""
    print("\n🤖 Deployed Bots Status")
    print("-" * 40)
    
    try:
        # This would integrate with actual bot monitoring
        print("📊 Bot monitoring system integration needed")
        print("💡 This would show:")
        print("   • Active bot count")
        print("   • Performance summary")
        print("   • Alert status")
        print("   • Account utilization")
        
        print("\n🔧 Integration points:")
        print("   • HaasOnline API bot management")
        print("   • Real-time performance tracking")
        print("   • Risk threshold monitoring")
        
    except Exception as e:
        print(f"❌ Bot status check failed: {e}")

async def run_full_demo():
    """Run the full system demonstration"""
    print("\n📋 Full System Demo")
    print("-" * 40)
    
    try:
        from examples.comprehensive_backtest_analysis_example import main as demo_main
        await demo_main()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Check if example file exists and dependencies are installed")

def start_mcp_server():
    """Start the MCP server"""
    print("\n🔧 Starting MCP Server")
    print("-" * 40)
    
    try:
        import subprocess
        
        print("🚀 Starting MCP server...")
        print("💡 This will start the server for API integration")
        
        # Start the MCP server
        cmd = [sys.executable, "mcp_server/server.py"]
        print(f"Running: {' '.join(cmd)}")
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        print("💡 Check if mcp_server/server.py exists")

def start_react_dashboard():
    """Start the React dashboard"""
    print("\n🌐 Starting React Dashboard")
    print("-" * 40)
    
    try:
        import subprocess
        import os
        
        dashboard_dir = "ai-trading-interface"
        if not os.path.exists(dashboard_dir):
            print(f"❌ Dashboard directory not found: {dashboard_dir}")
            return
        
        print("🚀 Starting React development server...")
        print("💡 This will open the visual dashboard")
        
        # Change to dashboard directory and start
        os.chdir(dashboard_dir)
        
        # Install dependencies if needed
        if not os.path.exists("node_modules"):
            print("📦 Installing dependencies...")
            subprocess.run(["npm", "install"])
        
        # Start development server
        subprocess.run(["npm", "run", "dev"])
        
    except Exception as e:
        print(f"❌ Failed to start React dashboard: {e}")
        print("💡 Make sure Node.js and npm are installed")

async def main():
    """Main application loop"""
    print_banner()
    
    while True:
        choice = get_user_choice()
        
        if choice == 0:
            print("\n👋 Goodbye!")
            break
        elif choice == 1:
            await analyze_single_backtest()
        elif choice == 2:
            await compare_multiple_backtests()
        elif choice == 3:
            await check_available_accounts()
        elif choice == 4:
            await view_deployed_bots()
        elif choice == 5:
            await run_full_demo()
        elif choice == 6:
            start_mcp_server()
        elif choice == 7:
            start_react_dashboard()
        else:
            print("❌ Invalid choice. Please try again.")
        
        if choice != 0:
            input("\n⏸️  Press Enter to continue...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Run setup_analysis_system.py first to check your setup")