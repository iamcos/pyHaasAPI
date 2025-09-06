#!/usr/bin/env python3
"""
Test Comprehensive Lab Analysis - Limited Scope

This test script:
1. Fetches 1 completed lab
2. Gets 10 top performing backtests that beat buy & hold
3. Creates 1 bot from the best performer
4. Tests the new bot naming convention

This is a scaled-down test of the full comprehensive system.
"""

import os
import sys
import csv
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor, get_full_backtest_runtime_data
from pyHaasAPI.model import GetBacktestResultRequest, AddBotFromLabRequest
from pyHaasAPI.model import LabStatus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestBacktestAnalysis:
    """Analysis result for a single backtest (test version)"""
    backtest_id: str
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    pc_value: float
    script_name: str
    market_tag: str
    generation_idx: Optional[int]
    population_idx: Optional[int]
    beats_buy_hold: bool

@dataclass
class TestBotResult:
    """Result of creating a test bot"""
    lab_id: str
    lab_name: str
    backtest_id: str
    account_id: str
    bot_id: str
    bot_name: str
    roi: float
    win_rate: float
    generation_idx: Optional[int]
    population_idx: Optional[int]
    creation_time: str
    status: str

class TestLabAnalyzer:
    """Test analyzer for one lab with limited scope"""
    
    def __init__(self, executor: RequestsExecutor):
        self.executor = executor
        self.test_results = {}
        
    def get_one_completed_lab(self) -> Optional[Dict[str, Any]]:
        """Get one completed lab for testing"""
        print("🔍 Fetching one completed lab for testing...")
        
        try:
            labs = api.get_all_labs(self.executor)
            print(f"✅ Found {len(labs)} total labs")
            
            # Find first completed lab
            for lab in labs:
                lab_status = getattr(lab, 'status', None)
                if lab_status == LabStatus.COMPLETED:
                    lab_dict = {
                        'lab_id': getattr(lab, 'lab_id', ''),
                        'name': getattr(lab, 'name', f"Lab {getattr(lab, 'lab_id', '')[:8]}"),
                        'script_id': getattr(lab, 'script_id', ''),
                        'account_id': getattr(lab, 'account_id', ''),
                        'status': str(lab_status),
                        'completed_backtests': getattr(lab, 'completed_backtests', 0)
                    }
                    print(f"✅ Using lab: {lab_dict['name']} (ID: {lab_dict['lab_id'][:8]}...) - {lab_dict['completed_backtests']} backtests")
                    return lab_dict
            
            print("❌ No completed labs found")
            return None
            
        except Exception as e:
            print(f"❌ Failed to fetch labs: {e}")
            raise
    
    def establish_buy_hold_baseline(self, lab_id: str) -> float:
        """Establish buy & hold baseline by analyzing top ROI backtests"""
        print(f"📊 Establishing buy & hold baseline for lab {lab_id[:8]}...")
        
        try:
            # Fetch first page of backtests to find highest ROI
            request = GetBacktestResultRequest(
                lab_id=lab_id,
                next_page_id=0,
                page_lenght=20  # Start with 20 to find baseline
            )
            
            response = api.get_backtest_result(self.executor, request)
            
            if not response or not response.items:
                raise ValueError(f"No backtests found for lab {lab_id}")
            
            print(f"   Analyzing {len(response.items)} backtests for baseline...")
            
            # Analyze each backtest to get ROI
            roi_values = []
            for backtest in response.items:
                try:
                    # Get runtime data for ROI calculation
                    runtime_data = get_full_backtest_runtime_data(self.executor, lab_id, backtest.backtest_id)
                    
                    if runtime_data and runtime_data.Reports:
                        # Get first report
                        report_key = list(runtime_data.Reports.keys())[0]
                        report_data = runtime_data.Reports[report_key]
                        
                        if hasattr(report_data, 'PR') and hasattr(report_data.PR, 'ROI'):
                            roi = float(report_data.PR.ROI)
                            roi_values.append(roi)
                            
                except Exception as e:
                    print(f"      ⚠️  Error analyzing backtest {backtest.backtest_id[:8]}: {e}")
                    continue
            
            if not roi_values:
                raise ValueError(f"Unable to extract ROI from any backtest in lab {lab_id}")
            
            # Use highest ROI as buy & hold baseline
            buy_hold_baseline = max(roi_values)
            print(f"   ✅ Buy & Hold Baseline: {buy_hold_baseline:.2f}%")
            
            return buy_hold_baseline
            
        except Exception as e:
            print(f"❌ Failed to establish buy & hold baseline: {e}")
            raise
    
    def fetch_top_10_backtests(self, lab_id: str, buy_hold_baseline: float) -> List[Any]:
        """Fetch top 10 backtests that beat the buy & hold baseline"""
        print(f"🎯 Fetching top 10 backtests above {buy_hold_baseline:.2f}% ROI...")
        
        try:
            all_backtests = []
            next_page_id = 0
            page_size = 50
            
            while len(all_backtests) < 10:
                # Fetch batch
                request = GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=next_page_id,
                    page_lenght=page_size
                )
                
                response = api.get_backtest_result(self.executor, request)
                
                if not response or not response.items:
                    break
                
                # Quick ROI check for this batch
                profitable_batch = []
                for backtest in response.items:
                    try:
                        # Quick analysis just for ROI
                        runtime_data = get_full_backtest_runtime_data(self.executor, lab_id, backtest.backtest_id)
                        
                        if runtime_data and runtime_data.Reports:
                            report_key = list(runtime_data.Reports.keys())[0]
                            report_data = runtime_data.Reports[report_key]
                            
                            if hasattr(report_data, 'PR') and hasattr(report_data.PR, 'ROI'):
                                roi = float(report_data.PR.ROI)
                                if roi > buy_hold_baseline:
                                    profitable_batch.append(backtest)
                                    
                    except Exception as e:
                        continue
                
                all_backtests.extend(profitable_batch)
                print(f"      Batch: {len(response.items)} backtests, {len(profitable_batch)} profitable")
                
                # Check if we have enough
                if len(all_backtests) >= 10:
                    break
                
                # Check if we should continue (if batch was full)
                if len(response.items) < page_size:
                    break
                
                # Get next page ID for pagination
                next_page_id = response.next_page_id
                if not next_page_id:
                    break
            
            print(f"   ✅ Found {len(all_backtests)} profitable backtests above threshold")
            return all_backtests[:10]  # Return max 10
            
        except Exception as e:
            print(f"❌ Failed to fetch profitable backtests: {e}")
            raise
    
    def analyze_backtest(self, backtest: Any, lab_id: str) -> Optional[TestBacktestAnalysis]:
        """Analyze a single backtest and return analysis"""
        try:
            backtest_id = backtest.backtest_id
            runtime_data = get_full_backtest_runtime_data(self.executor, lab_id, backtest_id)
            
            if not runtime_data or not runtime_data.Reports:
                return None
            
            # Get first report
            report_key = list(runtime_data.Reports.keys())[0]
            report_data = runtime_data.Reports[report_key]
            
            # Extract performance data
            roi_percentage = 0.0
            win_rate = 0.0
            total_trades = 0
            max_drawdown = 0.0
            pc_value = 0.0
            
            # Extract from PR (Performance Report)
            if hasattr(report_data, 'PR'):
                pr_data = report_data.PR
                roi_percentage = float(getattr(pr_data, 'ROI', 0))
                max_drawdown = float(getattr(pr_data, 'RM', 0))
                pc_value = float(getattr(pr_data, 'PC', 0))
            
            # Extract from P (Performance)
            if hasattr(report_data, 'P'):
                p_data = report_data.P
                total_trades = int(getattr(p_data, 'C', 0))
                winning_trades = int(getattr(p_data, 'W', 0))
                win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0
            
            # Extract script and market info
            script_name = getattr(runtime_data, 'ScriptName', 'Unknown')
            market_tag = getattr(runtime_data, 'M', 'Unknown')
            
            # Extract generation and population indices
            generation_idx = None
            population_idx = None
            
            # Try to get from backtest object attributes
            if hasattr(backtest, 'generation_idx'):
                try:
                    generation_idx = int(backtest.generation_idx)
                except (ValueError, TypeError):
                    pass
            
            if hasattr(backtest, 'population_idx'):
                try:
                    population_idx = int(backtest.population_idx)
                except (ValueError, TypeError):
                    pass
            
            # If not found in attributes, try to get from parameters
            if generation_idx is None and hasattr(backtest, 'parameters'):
                parameters = backtest.parameters
                if parameters:
                    generation_idx = parameters.get('generation_idx')
                    if generation_idx:
                        try:
                            generation_idx = int(generation_idx)
                        except (ValueError, TypeError):
                            generation_idx = None
            
            if population_idx is None and hasattr(backtest, 'parameters'):
                parameters = backtest.parameters
                if parameters:
                    population_idx = parameters.get('population_idx')
                    if population_idx:
                        try:
                            population_idx = int(population_idx)
                        except (ValueError, TypeError):
                            population_idx = None
            
            # Determine if beats buy & hold
            beats_buy_hold = roi_percentage > pc_value
            
            return TestBacktestAnalysis(
                backtest_id=backtest_id,
                roi_percentage=roi_percentage,
                win_rate=win_rate,
                total_trades=total_trades,
                max_drawdown=max_drawdown,
                pc_value=pc_value,
                script_name=script_name,
                market_tag=market_tag,
                generation_idx=generation_idx,
                population_idx=population_idx,
                beats_buy_hold=beats_buy_hold
            )
            
        except Exception as e:
            logger.error(f"Error analyzing backtest {getattr(backtest, 'backtest_id', 'unknown')}: {e}")
            return None
    
    def get_available_accounts(self) -> List[Dict[str, Any]]:
        """Get available accounts for bot creation"""
        try:
            accounts = api.get_all_accounts(self.executor)
            bots = api.get_all_bots(self.executor)
            
            # Find which accounts are used by bots
            used_accounts = set()
            for bot in bots:
                if hasattr(bot, 'AccountId') and bot.AccountId:
                    used_accounts.add(bot.AccountId)
            
            # Find available accounts (not used by bots)
            available_accounts = []
            for account in accounts:
                if account['AID'] not in used_accounts:
                    available_accounts.append(account)
            
            print(f"✅ Found {len(available_accounts)} available accounts")
            return available_accounts
            
        except Exception as e:
            logger.error(f"Error getting available accounts: {e}")
            return []
    
    def create_test_bot(self, lab_id: str, backtest: TestBacktestAnalysis, 
                        account_id: str, lab_name: str) -> Optional[TestBotResult]:
        """Create a test bot from a backtest"""
        try:
            # Create bot name with lab name + ROI + pop/gen info
            pop_gen_info = ""
            
            # Use the extracted generation and population indices
            if backtest.generation_idx is not None and backtest.population_idx is not None:
                pop_gen_info = f"_G{backtest.generation_idx}_P{backtest.population_idx}"
            elif backtest.generation_idx is not None:
                pop_gen_info = f"_G{backtest.generation_idx}"
            elif backtest.population_idx is not None:
                pop_gen_info = f"_P{backtest.population_idx}"
            
            # Format ROI for display (2 decimal places)
            roi_display = f"{backtest.roi_percentage:.2f}"
            
            # Create descriptive bot name
            bot_name = f"{lab_name}_ROI{roi_display}{pop_gen_info}"
            
            # Clean up bot name (remove special characters that might cause issues)
            bot_name = "".join(c for c in bot_name if c.isalnum() or c in "._-")
            
            print(f"🤖 Creating bot with name: {bot_name}")
            
            # Get lab details for market info
            lab_details = api.get_lab_details(self.executor, lab_id)
            market = getattr(lab_details.settings, 'market_tag', 'BINANCE_BTC_USDT_')
            
            # Create bot request
            bot_request = AddBotFromLabRequest(
                lab_id=lab_id,
                backtest_id=backtest.backtest_id,
                bot_name=bot_name,
                account_id=account_id,
                market=market,
                leverage=0
            )
            
            # Create bot
            bot = api.add_bot_from_lab(self.executor, bot_request)
            
            return TestBotResult(
                lab_id=lab_id,
                lab_name=lab_name,
                backtest_id=backtest.backtest_id,
                account_id=account_id,
                bot_id=bot.bot_id,
                bot_name=bot_name,
                roi=backtest.roi_percentage,
                win_rate=backtest.win_rate,
                generation_idx=backtest.generation_idx,
                population_idx=backtest.population_idx,
                creation_time=datetime.now().isoformat(),
                status="created"
            )
            
        except Exception as e:
            logger.error(f"Error creating bot from backtest {backtest.backtest_id}: {e}")
            return None
    
    def run_test_analysis(self) -> Dict[str, Any]:
        """Run the test analysis with limited scope"""
        
        print("🧪 Starting Test Lab Analysis - Limited Scope")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 1. Get one completed lab
            lab = self.get_one_completed_lab()
            
            if not lab:
                print("❌ No completed labs found for testing")
                return {"error": "No completed labs found"}
            
            lab_id = lab['lab_id']
            lab_name = lab['name']
            
            print(f"\n🎯 Testing with lab: {lab_name}")
            print(f"   ID: {lab_id[:8]}...")
            print("=" * 60)
            
            # 2. Establish buy & hold baseline
            buy_hold_baseline = self.establish_buy_hold_baseline(lab_id)
            
            # 3. Fetch top 10 profitable backtests
            profitable_backtests = self.fetch_top_10_backtests(lab_id, buy_hold_baseline)
            
            if not profitable_backtests:
                raise ValueError(f"No backtests found above {buy_hold_baseline:.2f}% ROI")
            
            # 4. Analyze all profitable backtests
            print(f"🔍 Analyzing {len(profitable_backtests)} profitable backtests...")
            analyses = []
            
            for i, backtest in enumerate(profitable_backtests):
                print(f"      Analyzing {i+1}/{len(profitable_backtests)}: {backtest.backtest_id[:8]}...")
                
                analysis = self.analyze_backtest(backtest, lab_id)
                if analysis:
                    analyses.append(analysis)
                    print(f"         ✅ ROI: {analysis.roi_percentage:.2f}%, Win Rate: {analysis.win_rate:.1%}")
            
            print(f"   ✅ Successfully analyzed {len(analyses)} backtests")
            
            # 5. Select best performer for bot creation
            if analyses:
                # Sort by ROI and select the best one
                analyses.sort(key=lambda x: x.roi_percentage, reverse=True)
                best_backtest = analyses[0]
                
                print(f"\n🏆 Best performer selected:")
                print(f"   Backtest ID: {best_backtest.backtest_id[:8]}...")
                print(f"   ROI: {best_backtest.roi_percentage:.2f}%")
                print(f"   Win Rate: {best_backtest.win_rate:.1%}")
                print(f"   Trades: {best_backtest.total_trades}")
                print(f"   Generation: {best_backtest.generation_idx or 'N/A'}")
                print(f"   Population: {best_backtest.population_idx or 'N/A'}")
                
                # 6. Create one bot from the best performer
                print(f"\n🤖 Creating bot from best performer...")
                
                available_accounts = self.get_available_accounts()
                
                if not available_accounts:
                    raise ValueError("No available accounts for bot creation")
                
                # Use first available account
                account = available_accounts[0]
                account_id = account['AID']
                
                bot_result = self.create_test_bot(lab_id, best_backtest, account_id, lab_name)
                
                if bot_result:
                    print(f"✅ Bot created successfully!")
                    print(f"   Bot ID: {bot_result.bot_id}")
                    print(f"   Bot Name: {bot_result.bot_name}")
                    print(f"   Account: {account_id}")
                    
                    # Store results
                    self.test_results = {
                        "lab": lab,
                        "buy_hold_baseline": buy_hold_baseline,
                        "total_backtests_analyzed": len(profitable_backtests),
                        "profitable_backtests": len(analyses),
                        "best_backtest": {
                            "backtest_id": best_backtest.backtest_id,
                            "roi": best_backtest.roi_percentage,
                            "win_rate": best_backtest.win_rate,
                            "generation": best_backtest.generation_idx,
                            "population": best_backtest.population_idx
                        },
                        "bot_created": {
                            "bot_id": bot_result.bot_id,
                            "bot_name": bot_result.bot_name,
                            "account_id": bot_result.account_id
                        },
                        "processing_time": time.time() - start_time
                    }
                    
                    return self.test_results
                else:
                    raise ValueError("Failed to create bot")
            else:
                raise ValueError("No backtests were successfully analyzed")
            
        except Exception as e:
            print(f"❌ Error during test analysis: {e}")
            
            self.test_results = {
                "error": str(e),
                "processing_time": time.time() - start_time
            }
            
            return self.test_results
    
    def save_test_report(self, output_dir: str = None):
        """Save test results to a simple report"""
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"test_lab_analysis_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save test results as JSON
        results_file = os.path.join(output_dir, "test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Save simple summary text
        summary_file = os.path.join(output_dir, "test_summary.txt")
        with open(summary_file, 'w') as f:
            f.write("TEST LAB ANALYSIS SUMMARY\n")
            f.write("=" * 30 + "\n\n")
            
            if "error" in self.test_results:
                f.write(f"❌ Test failed with error: {self.test_results['error']}\n")
            else:
                f.write(f"✅ Test completed successfully!\n\n")
                f.write(f"Lab: {self.test_results['lab']['name']}\n")
                f.write(f"Buy & Hold Baseline: {self.test_results['buy_hold_baseline']:.2f}%\n")
                f.write(f"Total Backtests Analyzed: {self.test_results['total_backtests_analyzed']}\n")
                f.write(f"Profitable Backtests: {self.test_results['profitable_backtests']}\n\n")
                
                f.write("Best Backtest:\n")
                f.write(f"  ID: {self.test_results['best_backtest']['backtest_id'][:8]}...\n")
                f.write(f"  ROI: {self.test_results['best_backtest']['roi']:.2f}%\n")
                f.write(f"  Win Rate: {self.test_results['best_backtest']['win_rate']:.1%}\n")
                f.write(f"  Generation: {self.test_results['best_backtest']['generation'] or 'N/A'}\n")
                f.write(f"  Population: {self.test_results['best_backtest']['population'] or 'N/A'}\n\n")
                
                f.write("Bot Created:\n")
                f.write(f"  ID: {self.test_results['bot_created']['bot_id']}\n")
                f.write(f"  Name: {self.test_results['bot_created']['bot_name']}\n")
                f.write(f"  Account: {self.test_results['bot_created']['account_id']}\n\n")
                
                f.write(f"Processing Time: {self.test_results['processing_time']:.2f} seconds\n")
            
            f.write(f"\nReports saved to:\n")
            f.write(f"  • Test Results: {results_file}\n")
            f.write(f"  • Summary: {summary_file}\n")
        
        print(f"\n📊 Test report saved to: {output_dir}")
        print(f"Files: test_results.json, test_summary.txt")
        
        return output_dir

def main():
    """Main execution function for testing"""
    
    print("🧪 Initializing Test Lab Analyzer...")
    
    # Initialize API connection
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        print("❌ Error: API_EMAIL and API_PASSWORD must be set in .env file")
        return 1

    print(f"🔌 Connecting to HaasOnline API: {api_host}:{api_port}")

    try:
        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )

        # Authenticate
        executor = haas_api.authenticate(api_email, api_password)
        print("✅ Successfully connected to HaasOnline API")
        
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return 1
    
    # Create test analyzer and run
    analyzer = TestLabAnalyzer(executor)
    
    try:
        print("\n🚀 Running test analysis...")
        results = analyzer.run_test_analysis()
        
        if "error" not in results:
            print(f"\n🎉 Test completed successfully!")
            print(f"🤖 Bot created: {results['bot_created']['bot_name']}")
            
            # Save test report
            output_dir = analyzer.save_test_report()
            print(f"📁 Test report saved to: {output_dir}")
            
        else:
            print(f"\n❌ Test failed: {results['error']}")
            return 1
        
    except Exception as e:
        print(f"❌ Error during test execution: {e}")
        return 1
    
    print(f"\n🧪 Test Lab Analysis completed!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

