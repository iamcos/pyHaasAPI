#!/usr/bin/env python3
"""
Bot Deployment Example
======================

Example script demonstrating how to use the Bot Creation Engine
to deploy WFO recommendations as live trading bots.

This example shows:
- How to load WFO recommendations
- How to configure bot deployment
- How to deploy bots to accounts
- How to monitor deployment results
- How to handle rollbacks if needed

Usage:
    python examples/bot_deployment_example.py

Author: AI Assistant
Version: 1.0
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api
from lab_to_bot_automation.bot_creation_engine import BotCreationEngine, BotCreationConfig
from lab_to_bot_automation.account_manager import AccountManager, AccountConfig

def main():
    """Demonstrate bot deployment capabilities"""
    print("🚀 Bot Deployment Example")
    print("=" * 60)

    # Configuration for this example
    bot_config = BotCreationConfig(
        position_size_usdt=2000.0,  # 2,000 USDT position size
        leverage=1,  # 1x leverage for spot-like behavior
        activate_immediately=True,  # Activate bots after creation
        max_creation_attempts=3,  # Retry up to 3 times
        creation_delay=2.0,  # 2 second delay between deployments
        enable_position_sizing=True
    )

    account_config = AccountConfig(
        initial_balance=10000.0,
        creation_delay=1.0
    )

    print(f"📊 Deployment Configuration:")
    print(f"   • Position Size: {bot_config.position_size_usdt} USDT")
    print(f"   • Leverage: {bot_config.leverage}x")
    print(f"   • Auto-Activate: {bot_config.activate_immediately}")
    print(f"   • Account Balance: {account_config.initial_balance} USDT")
    print()

    # Connect to HaasOnline API
    try:
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            print("❌ Error: API_EMAIL and API_PASSWORD must be set in .env file")
            print("💡 This is just an example - set up your credentials to run actual deployment")
            show_example_output()
            return

        print(f"🔌 Connecting to HaasOnline API: {api_host}:{api_port}")

        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )

        # Authenticate
        haas_executor = haas_api.authenticate(api_email, api_password)
        print("✅ Successfully connected to HaasOnline API")

    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        print("💡 This is just an example - showing what the output would look like:")
        show_example_output()
        return

    # Initialize managers
    account_manager = AccountManager(haas_executor, account_config)
    bot_engine = BotCreationEngine(haas_executor, bot_config)

    print("\n🏗️  Step 1: Account Discovery...")
    try:
        accounts = account_manager.get_existing_accounts()
        print(f"   Found {len(accounts)} existing accounts")

        # Show a few examples
        available_accounts = [acc for acc in accounts if not acc.has_bot]
        print(f"   Available for bots: {len(available_accounts)}")

    except Exception as e:
        print(f"   ❌ Error discovering accounts: {e}")
        return

    # Ask for lab ID
    lab_id = input("\n🏗️  Enter Lab ID with backtests to deploy from: ").strip()
    if not lab_id:
        print("❌ No Lab ID provided")
        return

    print("\n🤖 Step 2: Load WFO Recommendations...")
    # In a real scenario, you would load recommendations from a WFO analysis
    # For this example, we'll create mock recommendations
    recommendations = create_mock_recommendations(lab_id)
    print(f"   Loaded {len(recommendations)} bot recommendations")

    # Show recommendations
    print("\n📋 Bot Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec.bot_name} (Score: {rec.recommendation_score:.1f})")

    # Confirm deployment
    response = input(f"\n⚠️  Deploy {len(recommendations)} bots? (y/N): ").strip().lower()
    if response != 'y':
        print("Deployment cancelled.")
        return

    print("\n🚀 Step 3: Deploying Bots...")
    print("=" * 60)

    # Get available accounts for deployment
    account_mapping = {acc.name: acc for acc in available_accounts}

    if len(account_mapping) < len(recommendations):
        print(f"❌ Not enough available accounts ({len(account_mapping)}) for {len(recommendations)} bots")
        return

    # Deploy bots
    report = bot_engine.deploy_bots_batch(recommendations, account_mapping)

    print("\n📊 Step 4: Deployment Results")
    print("=" * 60)

    # Show summary
    print(f"✅ Successful Deployments: {report.successful_deployments}")
    print(f"❌ Failed Deployments: {report.failed_deployments}")
    print(".1f"    print(".1f"    print("\n📋 Detailed Results:")

    for i, result in enumerate(report.deployment_results, 1):
        status_icon = "✅" if result.success else "❌"
        print(f"\n{i}. {status_icon} {result.bot_name}")
        print(f"   Account: {result.account_id}")
        print(f"   Position Size: {result.position_size_usdt} USDT")
        print(f"   Activation: {result.activation_status}")
        if not result.success:
            print(f"   Error: {result.error_message}")

    # Generate comprehensive report
    print("\n📄 Step 5: Generating Report...")
    report_content = report.get_deployment_summary()

    # Save report
    report_filename = f"bot_deployment_report_{lab_id}_{len(recommendations)}bots.txt"
    with open(report_filename, 'w') as f:
        f.write(report_content)

    print(f"✅ Detailed report saved to: {report_filename}")

    # Get final status
    status = bot_engine.get_deployment_status()
    print("
📈 Final Status:"    print(f"   Active Bots: {status['active_deployments']}")
    print(".1f"    print("\n🎉 BOT DEPLOYMENT COMPLETE!")
    print("=" * 60)

    # Offer rollback option
    if report.failed_deployments > 0:
        response = input("🔄 Rollback failed deployments? (y/N): ").strip().lower()
        if response == 'y':
            print("\n🔄 Rolling back failed deployments...")
            for result in report.deployment_results:
                if not result.success and result.bot_id:
                    bot_engine.rollback_deployment(result.bot_id)

    print("\n💡 Next Steps:")
    print("   • Monitor bot performance in HaasOnline interface")
    print("   • Adjust position sizes if needed")
    print("   • Review detailed deployment report")
    print("   • Consider running WFO analysis on new backtests")

def create_mock_recommendations(lab_id: str):
    """Create mock recommendations for demonstration"""
    # This would normally come from WFO analysis
    from lab_to_bot_automation.wfo_analyzer import BotRecommendation, WFOMetrics

    recommendations = []

    mock_strategies = [
        ("SuperTrend RSI Scalper", 127.45, 68.25, "ETH/USDT"),
        ("MACD Divergence Trader", 89.12, 62.18, "BTC/USDT"),
        ("Bollinger Squeeze Breakout", 156.78, 71.45, "ETH/USDT")
    ]

    for i, (name, roi, win_rate, market) in enumerate(mock_strategies):
        # Create mock WFO metrics
        metrics = WFOMetrics(
            backtest_id=f"mock_bt_{i+1}",
            lab_id=lab_id,
            script_name=name,
            account_id=f"mock_acc_{i+1}",
            market=market,
            total_trades=150 + i * 50,
            winning_trades=int((150 + i * 50) * win_rate / 100),
            losing_trades=0,  # Will be calculated
            win_rate=win_rate,
            total_profit=10000 + i * 5000,
            total_profit_usd=10000 + i * 5000,
            roi_percentage=roi,
            profit_factor=2.0 + i * 0.3,
            max_drawdown=1500 + i * 500,
            max_drawdown_percentage=12.0 + i * 3,
            sharpe_ratio=2.0 + i * 0.2,
            overall_score=85.0 + i * 5,
            wfo_score=8.0 + i * 0.3
        )

        # Calculate derived fields
        metrics.losing_trades = metrics.total_trades - metrics.winning_trades

        # Create recommendation
        recommendation = BotRecommendation(
            backtest=metrics,
            recommendation_score=metrics.overall_score * (metrics.wfo_score + 1) / 2,
            diversity_score=0.8 + i * 0.1,
            bot_name=f"{name} +{int(roi)}% pop/gen",
            reasoning=[
                ".2f",
                ".2f",
                ".2f",
                ".2f"
            ],
            risk_assessment="Low Risk" if metrics.max_drawdown_percentage < 20 else "Medium Risk",
            position_size_usdt=2000.0
        )

        recommendations.append(recommendation)

    return recommendations

def show_example_output():
    """Show example deployment output when API is not available"""
    print("\n📊 EXAMPLE BOT DEPLOYMENT OUTPUT:")
    print("=" * 60)
    print("""
🏆 BOT DEPLOYMENT RESULTS:

1. ✅ SuperTrend RSI Scalper +127% pop/gen
   Account: [Sim] 4AA-10k
   Position Size: 2000 USDT
   Activation: activated

2. ✅ MACD Divergence Trader +89% pop/gen
   Account: [Sim] 4AB-10k
   Position Size: 2000 USDT
   Activation: activated

3. ✅ Bollinger Squeeze Breakout +156% pop/gen
   Account: [Sim] 4AC-10k
   Position Size: 2000 USDT
   Activation: activated

📈 DEPLOYMENT SUMMARY:
   ✅ Successful Deployments: 3
   ❌ Failed Deployments: 0
   🎯 Success Rate: 100.0%
   📊 Active Bots: 3

🎉 BOT DEPLOYMENT COMPLETE!
📄 Detailed report saved to: bot_deployment_report_LAB123_3bots.txt
""")

    print("💡 Key Features Demonstrated:")
    print("   • Automated bot creation from lab backtests")
    print("   • Position size configuration (2,000 USDT)")
    print("   • Account assignment and management")
    print("   • Bot activation and status monitoring")
    print("   • Comprehensive error handling")
    print("   • Detailed deployment reporting")
    print("   • Rollback capabilities for failed deployments")

if __name__ == "__main__":
    main()

