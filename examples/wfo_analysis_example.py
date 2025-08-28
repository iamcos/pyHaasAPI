#!/usr/bin/env python3
"""
WFO Analysis Example
====================

Example script demonstrating how to use the Walk Forward Optimization (WFO) Analyzer
for comprehensive backtest analysis and bot recommendation generation.

This example shows:
- How to configure WFO analysis parameters
- How to analyze a lab's backtests
- How to generate diverse bot recommendations
- How to view detailed WFO reports

Usage:
    python examples/wfo_analysis_example.py

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
from lab_to_bot_automation.wfo_analyzer import WFOAnalyzer, WFOConfig

def main():
    """Demonstrate WFO Analysis capabilities"""
    print("🚀 Walk Forward Optimization (WFO) Analysis Example")
    print("=" * 70)

    # Configuration for this example
    wfo_config = WFOConfig(
        max_bots_per_lab=5,  # Generate 5 bot recommendations
        min_overall_score=60.0,  # Lower threshold for example
        min_win_rate=35.0,
        max_drawdown_pct=35.0,
        min_trades=3,  # Lower for example purposes
        min_roi_pct=5.0,
        min_sharpe_ratio=0.3,

        # Diversity filtering settings
        roi_similarity_threshold=0.08,  # ±8% ROI
        trade_count_similarity_threshold=0.15,  # ±15% trade count
        win_rate_similarity_threshold=0.10,  # ±10% win rate

        # Scoring weights
        profitability_weight=0.35,
        win_rate_weight=0.20,
        roi_weight=0.20,
        risk_weight=0.15,
        consistency_weight=0.10
    )

    print(f"📊 WFO Configuration:")
    print(f"   • Max Bots: {wfo_config.max_bots_per_lab}")
    print(f"   • Min Score: {wfo_config.min_overall_score}")
    print(f"   • Min Trades: {wfo_config.min_trades}")
    print(f"   • Max Drawdown: {wfo_config.max_drawdown_pct}%")
    print(f"   • ROI Similarity: ±{wfo_config.roi_similarity_threshold:.1%}")
    print(f"   • Trade Count Similarity: ±{wfo_config.trade_count_similarity_threshold:.1%}")
    print()

    # Connect to HaasOnline API
    try:
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            print("❌ Error: API_EMAIL and API_PASSWORD must be set in .env file")
            print("💡 This is just an example - set up your credentials to run actual analysis")
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

    # Ask for lab ID
    lab_id = input("\n🏗️  Enter Lab ID to analyze: ").strip()
    if not lab_id:
        print("❌ No Lab ID provided")
        return

    # Create WFO Analyzer
    analyzer = WFOAnalyzer(haas_executor, wfo_config)

    print(f"\n🔬 Starting WFO Analysis for Lab: {lab_id}")
    print("=" * 70)

    # Step 1: Analyze all backtests in the lab
    print("📊 Step 1: Analyzing backtests...")
    metrics_list = analyzer.analyze_lab_backtests(lab_id, max_backtests=50)

    if not metrics_list:
        print("❌ No backtests found or analysis failed")
        return

    print(f"✅ Analyzed {len(metrics_list)} backtests")

    # Step 2: Generate bot recommendations
    print("\n🤖 Step 2: Generating bot recommendations...")
    recommendations = analyzer.generate_bot_recommendations(lab_id)

    if not recommendations:
        print("❌ No bot recommendations generated")
        return

    print(f"✅ Generated {len(recommendations)} diverse bot recommendations")

    # Step 3: Display results
    print("\n📋 Step 3: WFO Analysis Results")
    print("=" * 70)

    # Show top recommendations
    print("🏆 TOP BOT RECOMMENDATIONS:")
    print("-" * 40)

    for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
        print(f"\n{i}. {rec.bot_name}")
        print(".1f"        print(".2f"        print(".2f"        print(".2f"        print(".2f"        print(".2f"        print(f"   🎪 Risk: {rec.risk_assessment}")
        print(f"   💰 Position Size: {rec.position_size_usdt} USDT")

    # Step 4: Generate detailed report
    print("\n📄 Step 4: Generating detailed WFO report...")
    report = analyzer.generate_wfo_report(recommendations)

    # Save report to file
    report_filename = f"wfo_analysis_report_{lab_id}_{analyzer.config.max_bots_per_lab}bots.txt"
    with open(report_filename, 'w') as f:
        f.write(report)

    print(f"✅ Detailed report saved to: {report_filename}")

    # Show summary
    print("\n🎉 WFO ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"📊 Analyzed: {len(metrics_list)} backtests")
    print(f"🤖 Recommended: {len(recommendations)} diverse bots")
    print(f"📄 Report: {report_filename}")

    # Show next steps
    print("\n🚀 Next Steps:")
    print("   • Review the detailed report for comprehensive analysis")
    print("   • Use the account manager to create accounts for these bots")
    print("   • Deploy recommended bots with the bot creation engine")
    print("   • Monitor performance and adjust position sizes as needed")

def show_example_output():
    """Show example output when API is not available"""
    print("\n📊 EXAMPLE WFO ANALYSIS OUTPUT:")
    print("=" * 70)
    print("""
🏆 TOP BOT RECOMMENDATIONS:

1. SuperTrend RSI Scalper +127% pop/gen
   📊 Recommendation Score: 87.3/100
   🎯 WFO Score: 8.42/10
   💰 ROI: 127.45%
   🎲 Win Rate: 68.25%
   📈 Profit Factor: 2.34
   ⚠️  Max Drawdown: 12.45%
   📊 Sharpe Ratio: 2.18
   🔄 Total Trades: 247
   🎪 Risk: Low Risk
   💰 Position Size: 2000 USDT

2. MACD Divergence Trader +89% pop/gen
   📊 Recommendation Score: 82.1/100
   🎯 WFO Score: 7.89/10
   💰 ROI: 89.12%
   🎲 Win Rate: 62.18%
   📈 Profit Factor: 1.98
   ⚠️  Max Drawdown: 18.92%
   📊 Sharpe Ratio: 1.87
   🔄 Total Trades: 189
   🎪 Risk: Medium Risk
   💰 Position Size: 2000 USDT

3. Bollinger Squeeze Breakout +156% pop/gen
   📊 Recommendation Score: 91.7/100
   🎯 WFO Score: 8.76/10
   💰 ROI: 156.78%
   🎲 Win Rate: 71.45%
   📈 Profit Factor: 2.67
   ⚠️  Max Drawdown: 15.23%
   📊 Sharpe Ratio: 2.45
   🔄 Total Trades: 312
   🎪 Risk: Low Risk
   💰 Position Size: 2000 USDT

🎉 WFO ANALYSIS COMPLETE!
📊 Analyzed: 47 backtests
🤖 Recommended: 5 diverse bots
📄 Report: wfo_analysis_report_LAB123_5bots.txt
""")

    print("💡 Key Features Demonstrated:")
    print("   • Diversity filtering removed similar strategies")
    print("   • WFO scoring evaluated stability, consistency, robustness")
    print("   • Risk assessment categorized strategies by drawdown")
    print("   • Position sizing set to 2000 USDT per strategy")
    print("   • Comprehensive analysis with detailed reasoning")

if __name__ == "__main__":
    main()

