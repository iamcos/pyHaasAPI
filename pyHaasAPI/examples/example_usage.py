#!/usr/bin/env python3
"""
Example usage of the integrated pyHaasAPI analysis functionality

This script demonstrates how to use the new integrated analysis classes
from the pyHaasAPI library for comprehensive lab analysis and bot creation.
"""

import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import (
    HaasAnalyzer, 
    UnifiedCacheManager, 
    BacktestAnalysis, 
    BotCreationResult, 
    LabAnalysisResult
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def example_comprehensive_analysis():
    """Example of comprehensive lab analysis using the integrated API"""
    print("🚀 Example: Comprehensive Lab Analysis")
    print("=" * 50)
    
    # Create cache manager and analyzer
    cache_manager = UnifiedCacheManager("example_cache")
    analyzer = HaasAnalyzer(cache_manager)
    
    # Connect to API
    print("📡 Connecting to HaasOnline API...")
    if not analyzer.connect():
        print("❌ Failed to connect to API")
        return
    
    print("✅ Connected successfully!")
    
    # Example lab ID (replace with actual lab ID)
    lab_id = "e4616b35-8065-4095-966b-546de68fd493"
    
    try:
        # Analyze lab
        print(f"🔍 Analyzing lab {lab_id[:8]}...")
        result = analyzer.analyze_lab(lab_id, top_count=3)
        
        print(f"📊 Analysis Results:")
        print(f"  Lab: {result.lab_name}")
        print(f"  Total Backtests: {result.total_backtests}")
        print(f"  Analyzed: {result.analyzed_backtests}")
        print(f"  Processing Time: {result.processing_time:.2f}s")
        
        # Display top backtests
        print(f"\n🏆 Top {len(result.top_backtests)} Backtests:")
        for i, backtest in enumerate(result.top_backtests, 1):
            print(f"  {i}. {backtest.backtest_id[:8]}")
            print(f"     ROI: {backtest.roi_percentage:.2f}%")
            print(f"     Win Rate: {backtest.win_rate:.1%}")
            print(f"     Trades: {backtest.total_trades}")
            print(f"     Market: {backtest.market_tag}")
            print()
        
        # Save report
        report_path = cache_manager.save_analysis_report(result)
        print(f"📄 Report saved: {report_path}")
        
        # Create bots from top backtests
        print(f"\n🤖 Creating bots from top backtests...")
        bots_created = analyzer.create_bots_from_analysis(result, create_count=2)
        
        successful_bots = [bot for bot in bots_created if bot.success]
        print(f"✅ Successfully created {len(successful_bots)} bots:")
        
        for bot in successful_bots:
            print(f"  🤖 {bot.bot_name}")
            print(f"     ID: {bot.bot_id[:8]}")
            print(f"     Market: {bot.market_tag}")
            print(f"     Leverage: {bot.leverage}x")
            print(f"     Margin Mode: {bot.margin_mode}")
            print(f"     Position Mode: {bot.position_mode}")
            print()
        
        return result
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None


def example_individual_backtest_analysis():
    """Example of analyzing individual backtests"""
    print("\n🔍 Example: Individual Backtest Analysis")
    print("=" * 50)
    
    # Create analyzer
    analyzer = HaasAnalyzer()
    
    # Connect to API
    if not analyzer.connect():
        print("❌ Failed to connect to API")
        return
    
    try:
        from pyHaasAPI import api
        
        # Get a lab and its backtests
        lab_id = "e4616b35-8065-4095-966b-546de68fd493"
        labs = api.get_all_labs(analyzer.executor)
        lab = next((l for l in labs if l.lab_id == lab_id), None)
        
        if not lab:
            print(f"❌ Lab {lab_id} not found")
            return
        
        print(f"📊 Lab: {lab.name}")
        
        # Get backtests
        from pyHaasAPI.model import GetBacktestResultRequest
        request = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=5  # Just get first 5 for example
        )
        
        response = api.get_backtest_result(analyzer.executor, request)
        if not response or not hasattr(response, 'items'):
            print("❌ No backtests found")
            return
        
        # Analyze first backtest
        if response.items:
            backtest = response.items[0]
            print(f"🔍 Analyzing backtest {backtest.backtest_id[:8]}...")
            
            analysis = analyzer.analyze_backtest(lab_id, backtest)
            if analysis:
                print(f"✅ Analysis complete:")
                print(f"  ROI: {analysis.roi_percentage:.2f}%")
                print(f"  Win Rate: {analysis.win_rate:.1%}")
                print(f"  Trades: {analysis.total_trades}")
                print(f"  Max Drawdown: {analysis.max_drawdown:.2f}%")
                print(f"  Realized Profits: ${analysis.realized_profits_usdt:.2f}")
                print(f"  Market: {analysis.market_tag}")
                print(f"  Script: {analysis.script_name}")
        
    except Exception as e:
        print(f"❌ Error during individual analysis: {e}")


def example_cache_usage():
    """Example of using the cache system"""
    print("\n💾 Example: Cache System Usage")
    print("=" * 50)
    
    # Create cache manager
    cache_manager = UnifiedCacheManager("example_cache")
    
    # Example data to cache
    example_data = {
        "backtest_id": "example-123",
        "roi_percentage": 15.5,
        "win_rate": 0.65,
        "total_trades": 42,
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    # Cache data
    lab_id = "example-lab"
    backtest_id = "example-123"
    
    print(f"💾 Caching data for {backtest_id}...")
    cache_manager.cache_backtest_data(lab_id, backtest_id, example_data)
    
    # Load cached data
    print(f"📁 Loading cached data...")
    cached_data = cache_manager.load_backtest_cache(lab_id, backtest_id)
    
    if cached_data:
        print(f"✅ Cached data loaded:")
        print(f"  ROI: {cached_data['roi_percentage']}%")
        print(f"  Win Rate: {cached_data['win_rate']:.1%}")
        print(f"  Trades: {cached_data['total_trades']}")
    else:
        print("❌ No cached data found")


def main():
    """Main example function"""
    print("🎯 pyHaasAPI Integrated Analysis Examples")
    print("=" * 60)
    
    # Check if environment variables are set
    if not os.getenv('API_EMAIL') or not os.getenv('API_PASSWORD'):
        print("⚠️  Warning: API_EMAIL and API_PASSWORD not set in environment")
        print("   Set these in your .env file to run the examples")
        print()
    
    # Run examples
    try:
        # Example 1: Cache usage (doesn't require API connection)
        example_cache_usage()
        
        # Example 2: Individual backtest analysis (requires API connection)
        if os.getenv('API_EMAIL') and os.getenv('API_PASSWORD'):
            example_individual_backtest_analysis()
            
            # Example 3: Comprehensive analysis (requires API connection)
            example_comprehensive_analysis()
        else:
            print("\n⚠️  Skipping API examples - credentials not configured")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
    
    print("\n✅ Examples completed!")


if __name__ == '__main__':
    main()
