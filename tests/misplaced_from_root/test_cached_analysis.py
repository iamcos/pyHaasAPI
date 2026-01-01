#!/usr/bin/env python3
"""
Test script for cached analysis service
"""
import asyncio
import os
from pathlib import Path
from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService

async def test_cached_analysis():
    """Test the cached analysis service"""
    try:
        # Set up cache directory
        cache_dir = Path("/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/unified_cache")
        
        # Create service
        service = CachedAnalysisService(cache_dir)
        
        # Get cache statistics
        print("📊 Cache Statistics:")
        stats = service.get_cache_statistics()
        print(f"  Total backtest files: {stats.get('total_backtest_files', 0)}")
        print(f"  Unique labs: {stats.get('unique_labs', 0)}")
        print(f"  Cache directory: {stats.get('cache_directory', 'N/A')}")
        
        # Test with a specific lab
        test_lab_id = "058c6c5a-549a-4828-9169-a79b0a317229"  # From the file listing
        
        print(f"\n🔍 Testing analysis for lab: {test_lab_id[:8]}...")
        
        # Analyze this lab with relaxed filters
        result = await service.analyze_lab_from_cache(
            lab_id=test_lab_id,
            lab_name="Test Lab",
            script_name="Simple RSING VWAP Strategy",
            market_tag="BINANCEFUTURES_SOL_USDT_PERPETUAL",
            top_count=5,
            min_win_rate=0.0,  # Relaxed filter
            min_trades=1,      # Relaxed filter
            sort_by="roi"
        )
        
        print(f"\n📈 Analysis Results:")
        print(f"  Success: {result.success}")
        print(f"  Total backtests: {result.total_backtests}")
        print(f"  Average ROI: {result.average_roi:.2f}%")
        print(f"  Best ROI: {result.best_roi:.2f}%")
        print(f"  Average Win Rate: {result.average_win_rate:.2f}%")
        print(f"  Best Win Rate: {result.best_win_rate:.2f}%")
        
        if result.top_performers:
            print(f"\n🏆 Top Performers:")
            for i, perf in enumerate(result.top_performers[:3], 1):
                print(f"  {i}. ROI: {perf.roi_percentage:.2f}%, Win Rate: {perf.win_rate:.2f}%, Trades: {perf.total_trades}")
        else:
            print(f"\n🔍 Debug: Let's check what data we're getting...")
            # Load one file manually to debug
            cached_files = service.get_cached_backtest_files_for_lab(test_lab_id)
            if cached_files:
                data = service.load_backtest_from_file(cached_files[0])
                if data:
                    performance = service.extract_performance_from_cached_data(data, cached_files[0])
                    if performance:
                        print(f"  Sample performance: ROI={performance.roi_percentage:.2f}%, Win Rate={performance.win_rate:.2f}%, Trades={performance.total_trades}")
                    else:
                        print(f"  Failed to extract performance from sample file")
        
        if not result.success:
            print(f"  Error: {result.error_message}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cached_analysis())
