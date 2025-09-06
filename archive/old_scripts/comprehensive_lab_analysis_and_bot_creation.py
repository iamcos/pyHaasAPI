#!/usr/bin/env python3
"""
Comprehensive Lab Analysis and Bot Creation System

This script:
1. Fetches ALL completed labs from the server
2. For each lab, establishes buy & hold baseline by analyzing top ROI backtests
3. Fetches up to 50 distinct backtests per lab that beat the buy & hold baseline
4. Creates 5 bots for each lab using the top performing backtests
5. Caches all data for future analysis

The end result: Complete analysis of all completed labs with automated bot creation
"""

import os
import sys
import csv
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
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
class LabAnalysisResult:
    """Result of analyzing a single lab"""
    lab_id: str
    lab_name: str
    status: str
    buy_hold_baseline: float
    total_backtests_analyzed: int
    profitable_backtests: int
    selected_backtests: int
    bots_created: int
    processing_time: float
    error_message: Optional[str] = None

@dataclass
class BacktestAnalysis:
    """Analysis result for a single backtest"""
    backtest_id: str
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    pc_value: float
    realized_profits_usdt: float
    fees_usdt: float
    script_name: str
    market_tag: str
    parameters: Dict[str, Any]
    generation_idx: Optional[int]
    population_idx: Optional[int]
    beats_buy_hold: bool

@dataclass
class BotCreationResult:
    """Result of creating a bot"""
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

class ComprehensiveLabAnalyzer:
    """Comprehensive analyzer for all completed labs with bot creation"""
    
    def __init__(self, executor: RequestsExecutor):
        self.executor = executor
        self.lab_results = []
        self.all_backtest_analyses = []
        self.all_bot_results = []
        self.cache_dir = "comprehensive_lab_cache"
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_completed_labs(self) -> List[Dict[str, Any]]:
        """Get all completed labs from the account"""
        print("🔍 Fetching all labs from your account...")
        
        try:
            labs = api.get_all_labs(self.executor)
            print(f"✅ Found {len(labs)} total labs")
            
            # Filter for completed labs
            completed_labs = []
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
                    completed_labs.append(lab_dict)
                    print(f"   🧪 {lab_dict['name']} (ID: {lab_dict['lab_id'][:8]}...) - {lab_dict['completed_backtests']} backtests")
            
            print(f"✅ Found {len(completed_labs)} completed labs")
            return completed_labs
            
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
                page_lenght=50  # Start with 50 to find baseline
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
    
    def fetch_profitable_backtests(self, lab_id: str, buy_hold_baseline: float, 
                                 max_backtests: int = 50) -> List[Any]:
        """Fetch backtests that beat the buy & hold baseline"""
        print(f"🎯 Fetching backtests above {buy_hold_baseline:.2f}% ROI (max {max_backtests})...")
        
        try:
            all_backtests = []
            next_page_id = 0
            page_size = 100
            
            while len(all_backtests) < max_backtests:
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
                if len(all_backtests) >= max_backtests:
                    break
                
                # Check if we should continue (if batch was full)
                if len(response.items) < page_size:
                    break
                
                # Get next page ID for pagination
                next_page_id = response.next_page_id
                if not next_page_id:
                    break
            
            print(f"   ✅ Found {len(all_backtests)} profitable backtests above threshold")
            return all_backtests[:max_backtests]
            
        except Exception as e:
            print(f"❌ Failed to fetch profitable backtests: {e}")
            raise
    
    def analyze_backtest(self, backtest: Any, lab_id: str) -> Optional[BacktestAnalysis]:
        """Analyze a single backtest and return comprehensive analysis"""
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
            sharpe_ratio = 0.0
            profit_factor = 0.0
            pc_value = 0.0
            realized_profits_usdt = 0.0
            fees_usdt = 0.0
            
            # Extract from PR (Performance Report)
            if hasattr(report_data, 'PR'):
                pr_data = report_data.PR
                roi_percentage = float(getattr(pr_data, 'ROI', 0))
                realized_profits_usdt = float(getattr(pr_data, 'RP', 0))
                max_drawdown = float(getattr(pr_data, 'RM', 0))
                pc_value = float(getattr(pr_data, 'PC', 0))
            
            # Extract from P (Performance)
            if hasattr(report_data, 'P'):
                p_data = report_data.P
                total_trades = int(getattr(p_data, 'C', 0))
                winning_trades = int(getattr(p_data, 'W', 0))
                win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0
            
            # Extract from T (Technical)
            if hasattr(report_data, 'T'):
                t_data = report_data.T
                sharpe_ratio = float(getattr(t_data, 'SHR', 0))
                profit_factor = float(getattr(t_data, 'PF', 0))
            
            # Extract from F (Fees)
            if hasattr(report_data, 'F'):
                f_data = report_data.F
                fees_usdt = float(getattr(f_data, 'TFC', 0))
            
            # Extract script and market info
            script_name = getattr(runtime_data, 'ScriptName', 'Unknown')
            market_tag = getattr(runtime_data, 'M', 'Unknown')
            
            # Extract parameters
            parameters = {}
            if hasattr(backtest, 'parameters'):
                parameters = backtest.parameters
            
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
            if generation_idx is None and parameters:
                generation_idx = parameters.get('generation_idx')
                if generation_idx:
                    try:
                        generation_idx = int(generation_idx)
                    except (ValueError, TypeError):
                        generation_idx = None
            
            if population_idx is None and parameters:
                population_idx = parameters.get('population_idx')
                if population_idx:
                    try:
                        population_idx = int(population_idx)
                    except (ValueError, TypeError):
                        population_idx = None
            
            # Determine if beats buy & hold
            beats_buy_hold = roi_percentage > pc_value
            
            return BacktestAnalysis(
                backtest_id=backtest_id,
                roi_percentage=roi_percentage,
                win_rate=win_rate,
                total_trades=total_trades,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                profit_factor=profit_factor,
                pc_value=pc_value,
                realized_profits_usdt=realized_profits_usdt,
                fees_usdt=fees_usdt,
                script_name=script_name,
                market_tag=market_tag,
                parameters=parameters,
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
    
    def create_bot_from_backtest(self, lab_id: str, backtest: BacktestAnalysis, 
                                account_id: str, lab_name: str) -> Optional[BotCreationResult]:
        """Create a bot from a backtest"""
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
            
            return BotCreationResult(
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
    
    def analyze_single_lab(self, lab: Dict[str, Any], max_backtests: int = 50, 
                          bots_per_lab: int = 5) -> LabAnalysisResult:
        """Analyze a single lab and create bots"""
        
        lab_id = lab['lab_id']
        lab_name = lab['name']
        start_time = time.time()
        
        print(f"\n🎯 Analyzing Lab: {lab_name}")
        print(f"   ID: {lab_id[:8]}...")
        print("=" * 60)
        
        try:
            # 1. Establish buy & hold baseline
            buy_hold_baseline = self.establish_buy_hold_baseline(lab_id)
            
            # 2. Fetch profitable backtests above threshold
            profitable_backtests = self.fetch_profitable_backtests(lab_id, buy_hold_baseline, max_backtests)
            
            if not profitable_backtests:
                raise ValueError(f"No backtests found above {buy_hold_baseline:.2f}% ROI")
            
            # 3. Analyze all profitable backtests
            print(f"🔍 Analyzing {len(profitable_backtests)} profitable backtests...")
            analyses = []
            
            for i, backtest in enumerate(profitable_backtests):
                print(f"      Analyzing {i+1}/{len(profitable_backtests)}: {backtest.backtest_id[:8]}...")
                
                analysis = self.analyze_backtest(backtest, lab_id)
                if analysis:
                    analyses.append(analysis)
            
            print(f"   ✅ Successfully analyzed {len(analyses)} backtests")
            
            # 4. Select top performers for bot creation
            # Sort by ROI and select top ones
            analyses.sort(key=lambda x: x.roi_percentage, reverse=True)
            selected_analyses = analyses[:bots_per_lab]
            
            print(f"🎯 Selected top {len(selected_analyses)} backtests for bot creation")
            
            # 5. Create bots
            created_bots = []
            available_accounts = self.get_available_accounts()
            
            if not available_accounts:
                raise ValueError("No available accounts for bot creation")
            
            for i, analysis in enumerate(selected_analyses):
                print(f"🤖 Creating bot {i+1}/{len(selected_analyses)} from {analysis.backtest_id[:8]}...")
                
                # Get account (round-robin assignment)
                account = available_accounts[i % len(available_accounts)]
                account_id = account['AID']
                
                bot_result = self.create_bot_from_backtest(lab_id, analysis, account_id, lab_name)
                if bot_result:
                    created_bots.append(bot_result)
                    self.all_bot_results.append(bot_result)
                    print(f"   ✅ Bot created: {bot_result.bot_id}")
                else:
                    print(f"   ❌ Failed to create bot")
            
            # 6. Create lab summary
            processing_time = time.time() - start_time
            
            lab_result = LabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_name,
                status="completed",
                buy_hold_baseline=buy_hold_baseline,
                total_backtests_analyzed=len(profitable_backtests),
                profitable_backtests=len(analyses),
                selected_backtests=len(selected_analyses),
                bots_created=len(created_bots),
                processing_time=processing_time
            )
            
            # Store analyses
            self.all_backtest_analyses.extend(analyses)
            
            return lab_result
            
        except Exception as e:
            print(f"   ❌ Error analyzing lab {lab_name}: {e}")
            
            processing_time = time.time() - start_time
            
            lab_result = LabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_name,
                status="error",
                buy_hold_baseline=0.0,
                total_backtests_analyzed=0,
                profitable_backtests=0,
                selected_backtests=0,
                bots_created=0,
                processing_time=processing_time,
                error_message=str(e)
            )
            
            return lab_result
    
    def save_comprehensive_report(self, output_dir: str = None):
        """Save comprehensive report of all analysis and bot creation"""
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(self.cache_dir, f"comprehensive_analysis_{timestamp}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Lab Analysis Summary CSV
        lab_summary_csv = os.path.join(output_dir, "lab_analysis_summary.csv")
        
        lab_fieldnames = [
            'lab_id', 'lab_name', 'status', 'buy_hold_baseline', 
            'total_backtests_analyzed', 'profitable_backtests', 
            'selected_backtests', 'bots_created', 'processing_time', 'error_message'
        ]
        
        with open(lab_summary_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=lab_fieldnames)
            writer.writeheader()
            
            for result in self.lab_results:
                row = {
                    'lab_id': result.lab_id,
                    'lab_name': result.lab_name,
                    'status': result.status,
                    'buy_hold_baseline': f"{result.buy_hold_baseline:.2f}",
                    'total_backtests_analyzed': result.total_backtests_analyzed,
                    'profitable_backtests': result.profitable_backtests,
                    'selected_backtests': result.selected_backtests,
                    'bots_created': result.bots_created,
                    'processing_time': f"{result.processing_time:.2f}",
                    'error_message': result.error_message or ''
                }
                writer.writerow(row)
        
        # 2. All Backtest Analyses CSV
        backtest_csv = os.path.join(output_dir, "all_backtest_analyses.csv")
        
        backtest_fieldnames = [
            'backtest_id', 'roi_percentage', 'win_rate', 'total_trades',
            'max_drawdown', 'sharpe_ratio', 'profit_factor', 'pc_value',
            'realized_profits_usdt', 'fees_usdt', 'script_name', 'market_tag',
            'generation_idx', 'population_idx', 'beats_buy_hold'
        ]
        
        with open(backtest_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=backtest_fieldnames)
            writer.writeheader()
            
            for analysis in self.all_backtest_analyses:
                row = {
                    'backtest_id': analysis.backtest_id,
                    'roi_percentage': f"{analysis.roi_percentage:.2f}",
                    'win_rate': f"{analysis.win_rate:.4f}",
                    'total_trades': analysis.total_trades,
                    'max_drawdown': f"{analysis.max_drawdown:.2f}",
                    'sharpe_ratio': f"{analysis.sharpe_ratio:.4f}",
                    'profit_factor': f"{analysis.profit_factor:.4f}",
                    'pc_value': f"{analysis.pc_value:.2f}",
                    'realized_profits_usdt': f"{analysis.realized_profits_usdt:.2f}",
                    'fees_usdt': f"{analysis.fees_usdt:.2f}",
                    'script_name': analysis.script_name,
                    'market_tag': analysis.market_tag,
                    'generation_idx': analysis.generation_idx or '',
                    'population_idx': analysis.population_idx or '',
                    'beats_buy_hold': analysis.beats_buy_hold
                }
                writer.writerow(row)
        
        # 3. All Bot Creation Results CSV
        bot_csv = os.path.join(output_dir, "all_bot_creation_results.csv")
        
        bot_fieldnames = [
            'lab_id', 'lab_name', 'backtest_id', 'account_id', 'bot_id',
            'bot_name', 'roi', 'win_rate', 'generation_idx', 'population_idx', 'creation_time', 'status'
        ]
        
        with open(bot_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=bot_fieldnames)
            writer.writeheader()
            
            for bot in self.all_bot_results:
                row = {
                    'lab_id': bot.lab_id,
                    'lab_name': bot.lab_name,
                    'backtest_id': bot.backtest_id,
                    'account_id': bot.account_id,
                    'bot_id': bot.bot_id,
                    'bot_name': bot.bot_name,
                    'roi': f"{bot.roi:.2f}",
                    'win_rate': f"{bot.win_rate:.4f}",
                    'generation_idx': bot.generation_idx or '',
                    'population_idx': bot.population_idx or '',
                    'creation_time': bot.creation_time,
                    'status': bot.status
                }
                writer.writerow(row)
        
        # 4. Master Summary JSON
        summary_json = os.path.join(output_dir, "comprehensive_analysis_summary.json")
        
        summary = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_labs_processed": len(self.lab_results),
            "successful_labs": len([r for r in self.lab_results if r.status == "completed"]),
            "failed_labs": len([r for r in self.lab_results if r.status == "error"]),
            "total_backtests_analyzed": len(self.all_backtest_analyses),
            "total_bots_created": len(self.all_bot_results),
            "lab_summaries": [vars(result) for result in self.lab_results],
            "backtest_analyses": [vars(analysis) for analysis in self.all_backtest_analyses],
            "bot_results": [vars(bot) for bot in self.all_bot_results]
        }
        
        with open(summary_json, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # 5. Master Summary Text
        summary_txt = os.path.join(output_dir, "comprehensive_analysis_summary.txt")
        
        with open(summary_txt, 'w') as f:
            f.write("COMPREHENSIVE LAB ANALYSIS AND BOT CREATION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total labs processed: {len(self.lab_results)}\n")
            f.write(f"Successfully processed: {len([r for r in self.lab_results if r.status == 'completed'])}\n")
            f.write(f"Failed labs: {len([r for r in self.lab_results if r.status == 'error'])}\n\n")
            
            f.write(f"Total backtests analyzed: {len(self.all_backtest_analyses)}\n")
            f.write(f"Total bots created: {len(self.all_bot_results)}\n\n")
            
            f.write("LAB SUMMARIES:\n")
            f.write("-" * 20 + "\n")
            
            for result in self.lab_results:
                status_icon = "✅" if result.status == "completed" else "❌"
                f.write(f"{status_icon} {result.lab_name} (ID: {result.lab_id[:8]}...)\n")
                f.write(f"   Buy & Hold Baseline: {result.buy_hold_baseline:.2f}%\n")
                f.write(f"   Profitable Backtests: {result.profitable_backtests}\n")
                f.write(f"   Selected for Bots: {result.selected_backtests}\n")
                f.write(f"   Bots Created: {result.bots_created}\n")
                f.write(f"   Processing Time: {result.processing_time:.2f}s\n")
                if result.error_message:
                    f.write(f"   Error: {result.error_message}\n")
                f.write("\n")
            
            f.write(f"Reports saved to:\n")
            f.write(f"  • Lab Summaries: {lab_summary_csv}\n")
            f.write(f"  • All Backtest Analyses: {backtest_csv}\n")
            f.write(f"  • All Bot Results: {bot_csv}\n")
            f.write(f"  • Summary JSON: {summary_json}\n")
            f.write(f"  • Summary Text: {summary_txt}\n\n")
            
            f.write("BOT NAMING CONVENTION:\n")
            f.write("-" * 25 + "\n")
            f.write("Format: LabName_ROI{value}_G{generation}_P{population}\n")
            f.write("Example: MyLab_ROI15.67_G3_P12\n")
            f.write("This shows the lab name, ROI percentage, generation index, and population index.\n")
        
        print(f"\n📊 Comprehensive report saved to: {output_dir}")
        print(f"Files: lab_analysis_summary.csv, all_backtest_analyses.csv, all_bot_creation_results.csv, summary.json, summary.txt")
        
        return output_dir
    
    def run_comprehensive_analysis(self, max_backtests_per_lab: int = 50, 
                                 bots_per_lab: int = 5) -> str:
        """Run comprehensive analysis of all completed labs"""
        
        print("🚀 Starting Comprehensive Lab Analysis and Bot Creation")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            # 1. Get all completed labs
            completed_labs = self.get_completed_labs()
            
            if not completed_labs:
                print("❌ No completed labs found")
                return ""
            
            print(f"\n🎯 Processing {len(completed_labs)} completed labs...")
            
            # 2. Analyze each lab
            for i, lab in enumerate(completed_labs):
                print(f"\n📊 Lab {i+1}/{len(completed_labs)}")
                
                try:
                    lab_result = self.analyze_single_lab(
                        lab, 
                        max_backtests=max_backtests_per_lab,
                        bots_per_lab=bots_per_lab
                    )
                    
                    self.lab_results.append(lab_result)
                    
                    # Print lab summary
                    if lab_result.status == "completed":
                        print(f"✅ Lab completed: {lab_result.bots_created} bots created")
                    else:
                        print(f"❌ Lab failed: {lab_result.error_message}")
                        
                except Exception as e:
                    print(f"❌ Critical error processing lab {lab['name']}: {e}")
                    
                    # Create error result
                    error_result = LabAnalysisResult(
                        lab_id=lab['lab_id'],
                        lab_name=lab['name'],
                        status="critical_error",
                        buy_hold_baseline=0.0,
                        total_backtests_analyzed=0,
                        profitable_backtests=0,
                        selected_backtests=0,
                        bots_created=0,
                        processing_time=0.0,
                        error_message=str(e)
                    )
                    
                    self.lab_results.append(error_result)
            
            # 3. Save comprehensive report
            total_time = time.time() - start_time
            
            print(f"\n📊 Analysis completed in {total_time:.2f} seconds")
            print(f"📁 Saving comprehensive report...")
            
            output_dir = self.save_comprehensive_report()
            
            # 4. Print final summary
            print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETED!")
            print(f"=" * 50)
            print(f"Total labs processed: {len(self.lab_results)}")
            print(f"Successfully processed: {len([r for r in self.lab_results if r.status == 'completed'])}")
            print(f"Total backtests analyzed: {len(self.all_backtest_analyses)}")
            print(f"Total bots created: {len(self.all_bot_results)}")
            print(f"Output directory: {output_dir}")
            
            return output_dir
            
        except Exception as e:
            print(f"❌ Critical error during comprehensive analysis: {e}")
            raise

def main():
    """Main execution function"""
    
    # Configuration
    max_backtests_per_lab = 50
    bots_per_lab = 5
    
    print("🔧 Initializing Comprehensive Lab Analyzer...")
    
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
    
    # Create analyzer and run
    analyzer = ComprehensiveLabAnalyzer(executor)
    
    try:
        output_dir = analyzer.run_comprehensive_analysis(
            max_backtests_per_lab=max_backtests_per_lab,
            bots_per_lab=bots_per_lab
        )
        
        print(f"\n🎯 Comprehensive analysis completed successfully!")
        print(f"📁 Check the output directory: {output_dir}")
        
    except Exception as e:
        print(f"❌ Error during comprehensive analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
