"""
Centralized report generation functionality.
Extracts common report formatting logic from duplicated CLI files.
"""

from typing import Dict, List, Any, Optional
from pyHaasAPI.core.logging import get_logger


class ReportManager:
    """Centralized report generation"""
    
    def __init__(self):
        self.logger = get_logger("report_manager")

    def print_analysis_report(self, lab_results: Dict[str, Any]):
        """Unified analysis report formatting"""
        try:
            if "error" in lab_results:
                print(f"❌ Analysis Error: {lab_results['error']}")
                return
            
            print("\n" + "="*80)
            print("📊 LAB ANALYSIS REPORT")
            print("="*80)
            
            # Summary
            total_labs = lab_results.get("total_labs", 0)
            analyzed_labs = lab_results.get("analyzed_labs", 0)
            total_filtered = lab_results.get("total_filtered_backtests", 0)
            analysis_summary = lab_results.get("analysis_summary", {})
            
            print(f"📈 Total Labs: {total_labs}")
            print(f"✅ Analyzed Labs: {analyzed_labs}")
            print(f"🎯 Zero Drawdown Backtests: {total_filtered}")
            print(f"📊 Min Winrate: {analysis_summary.get('min_winrate', 'N/A')}%")
            print(f"🔢 Sort By: {analysis_summary.get('sort_by', 'N/A')}")
            print("-"*80)
            
            # Lab results
            lab_results_data = lab_results.get("lab_results", {})
            for lab_id, lab_result in lab_results_data.items():
                if "error" in lab_result:
                    print(f"❌ Lab {lab_id}: {lab_result['error']}")
                    continue
                
                lab_name = lab_result.get("lab_name", f"Lab {lab_id}")
                total_backtests = lab_result.get("total_backtests", 0)
                filtered_backtests = lab_result.get("filtered_backtests", 0)
                
                print(f"\n🏷️  {lab_name} (ID: {lab_id})")
                print(f"   📊 Total Backtests: {total_backtests}")
                print(f"   ✅ Zero Drawdown: {filtered_backtests}")
                
                # Show top backtests
                zero_drawdown_backtests = lab_result.get("zero_drawdown_backtests", [])
                if zero_drawdown_backtests:
                    print(f"   🏆 Top Backtests:")
                    for i, bt in enumerate(zero_drawdown_backtests[:3]):  # Show top 3
                        script_name = getattr(bt, 'script_name', 'Unknown')
                        roi = getattr(bt, 'roi_percentage', 0)
                        win_rate = getattr(bt, 'win_rate', 0) * 100
                        print(f"      {i+1}. {script_name} - ROI: {roi:.1f}%, Win Rate: {win_rate:.0f}%")
            
            print("\n" + "="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing analysis report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_bot_creation_report(self, created_bots: List[Dict[str, Any]]):
        """Unified bot creation report formatting"""
        try:
            if not created_bots:
                print("❌ No bots were created")
                return
            
            successful_bots = [bot for bot in created_bots if bot.get("success", False)]
            failed_bots = [bot for bot in created_bots if not bot.get("success", False)]
            
            print("\n" + "="*80)
            print("🤖 BOT CREATION REPORT")
            print("="*80)
            print(f"✅ Successfully Created: {len(successful_bots)}")
            print(f"❌ Failed: {len(failed_bots)}")
            print("-"*80)
            
            # Successful bots
            if successful_bots:
                print("\n🎉 SUCCESSFULLY CREATED BOTS:")
                for bot in successful_bots:
                    bot_id = bot.get("bot_id", "Unknown")
                    bot_name = bot.get("bot_name", "Unknown")
                    lab_name = bot.get("lab_name", "Unknown")
                    script_name = bot.get("script_name", "Unknown")
                    roi = bot.get("roi_percentage", 0)
                    win_rate = bot.get("win_rate", 0) * 100
                    
                    print(f"   🤖 {bot_name}")
                    print(f"      ID: {bot_id}")
                    print(f"      Lab: {lab_name}")
                    print(f"      Script: {script_name}")
                    print(f"      ROI: {roi:.1f}%, Win Rate: {win_rate:.0f}%")
                    print()
            
            # Failed bots
            if failed_bots:
                print("\n❌ FAILED BOT CREATIONS:")
                for bot in failed_bots:
                    bot_name = bot.get("bot_name", "Unknown")
                    error = bot.get("error", "Unknown error")
                    backtest_id = bot.get("backtest_id", "Unknown")
                    
                    print(f"   ❌ {bot_name}")
                    print(f"      Backtest ID: {backtest_id}")
                    print(f"      Error: {error}")
                    print()
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing bot creation report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_summary_report(self, analysis_results: Dict[str, Any], bot_results: List[Dict[str, Any]]):
        """Print combined analysis and bot creation summary"""
        try:
            print("\n" + "="*80)
            print("📋 COMPREHENSIVE SUMMARY REPORT")
            print("="*80)
            
            # Analysis summary
            if "error" not in analysis_results:
                total_labs = analysis_results.get("total_labs", 0)
                analyzed_labs = analysis_results.get("analyzed_labs", 0)
                total_filtered = analysis_results.get("total_filtered_backtests", 0)
                
                print(f"📊 Analysis Results:")
                print(f"   Total Labs: {total_labs}")
                print(f"   Analyzed Labs: {analyzed_labs}")
                print(f"   Zero Drawdown Backtests: {total_filtered}")
            else:
                print(f"❌ Analysis Error: {analysis_results['error']}")
            
            # Bot creation summary
            successful_bots = [bot for bot in bot_results if bot.get("success", False)]
            failed_bots = [bot for bot in bot_results if not bot.get("success", False)]
            
            print(f"\n🤖 Bot Creation Results:")
            print(f"   Successfully Created: {len(successful_bots)}")
            print(f"   Failed: {len(failed_bots)}")
            
            print("\n" + "="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing summary report: {e}")
            print(f"❌ Error generating summary report: {e}")





