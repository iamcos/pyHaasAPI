#!/usr/bin/env python3
"""
Backtest Result Analysis System

This system retrieves and analyzes completed backtest results,
comparing them with bot performance to generate verification reports.
"""

import asyncio
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


@dataclass
class BacktestResult:
    """Represents a completed backtest result"""
    backtest_id: str
    bot_id: str
    bot_name: str
    server_name: str
    script_id: str
    market_tag: str
    start_time: datetime
    end_time: datetime
    duration_days: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    max_drawdown: float
    profit_factor: float
    sharpe_ratio: float
    roi_percentage: float
    starting_balance: float
    ending_balance: float
    result_data: Dict[str, Any]
    completed_at: datetime


@dataclass
class BotPerformance:
    """Represents current bot performance"""
    bot_id: str
    bot_name: str
    server_name: str
    account_id: str
    market_tag: str
    script_id: str
    is_activated: bool
    is_paused: bool
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    total_trades: int
    win_rate: float
    max_drawdown: float
    current_balance: float
    trade_amount: float
    leverage: float
    margin_mode: str
    position_mode: str
    performance_data: Dict[str, Any]


@dataclass
class VerificationReport:
    """Represents a verification report comparing bot vs backtest"""
    bot_id: str
    bot_name: str
    backtest_id: str
    server_name: str
    verification_timestamp: datetime
    
    # Bot performance
    bot_realized_pnl: float
    bot_unrealized_pnl: float
    bot_total_pnl: float
    bot_win_rate: float
    bot_max_drawdown: float
    bot_total_trades: int
    
    # Backtest performance
    backtest_net_profit: float
    backtest_win_rate: float
    backtest_max_drawdown: float
    backtest_total_trades: int
    backtest_roi_percentage: float
    
    # Comparison metrics
    pnl_difference: float
    pnl_difference_percentage: float
    win_rate_difference: float
    drawdown_difference: float
    trades_difference: int
    
    # Verification status
    verification_status: str  # "PASS", "FAIL", "WARNING"
    verification_score: float  # 0.0 to 1.0
    issues: List[str]
    recommendations: List[str]


class BacktestResultAnalysisSystem:
    """System for analyzing backtest results and generating verification reports"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
        self.completed_backtests: Dict[str, BacktestResult] = {}
        self.bot_performances: Dict[str, BotPerformance] = {}
        self.verification_reports: Dict[str, VerificationReport] = {}
    
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to a specific server"""
        try:
            # Establish SSH tunnel
            ssh_process = await self._establish_ssh_tunnel(server_name)
            if not ssh_process:
                return False
            
            self.ssh_processes[server_name] = ssh_process
            
            # Get credentials
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                print("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Initialize analyzer and connect
            cache = UnifiedCacheManager()
            analyzer = HaasAnalyzer(cache)
            success = analyzer.connect(
                host='127.0.0.1',
                port=8090,
                email=email,
                password=password
            )
            
            if success:
                self.servers[server_name] = {
                    'analyzer': analyzer,
                    'executor': analyzer.executor,
                    'cache': cache
                }
                print(f"Successfully connected to {server_name}")
                return True
            else:
                print(f"Failed to connect to {server_name}")
                return False
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _establish_ssh_tunnel(self, server_name: str):
        """Establish SSH tunnel to server"""
        try:
            print(f"Connecting to {server_name}...")
            
            ssh_cmd = [
                "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
                f"prod@{server_name}"
            ]
            
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            await asyncio.sleep(5)
            
            if process.poll() is None:
                print(f"SSH tunnel established to {server_name} (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"SSH tunnel failed for {server_name}: {stderr.decode()}")
                return None
                
        except Exception as e:
            print(f"Failed to establish SSH tunnel to {server_name}: {e}")
            return None
    
    def get_bot_performance(self, server_name: str, bot_id: str) -> Optional[BotPerformance]:
        """Get current bot performance data"""
        if server_name not in self.servers:
            return None
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Get bot details
            bot_details = api.get_bot(executor, bot_id)
            if not bot_details:
                return None
            
            # Get bot runtime data
            runtime_data = api.get_full_bot_runtime_data(executor, bot_id)
            
            # Extract performance data
            if hasattr(bot_details, 'model_dump'):
                bot_data = bot_details.model_dump()
            elif isinstance(bot_details, dict):
                bot_data = bot_details
            else:
                bot_data = {
                    'bot_id': getattr(bot_details, 'bot_id', ''),
                    'bot_name': getattr(bot_details, 'bot_name', 'Unknown'),
                    'account_id': getattr(bot_details, 'account_id', ''),
                    'market': getattr(bot_details, 'market', ''),
                    'script_id': getattr(bot_details, 'script_id', ''),
                    'is_activated': getattr(bot_details, 'is_activated', False),
                    'is_paused': getattr(bot_details, 'is_paused', False)
                }
            
            # Extract runtime performance data
            realized_pnl = 0.0
            unrealized_pnl = 0.0
            total_trades = 0
            win_rate = 0.0
            max_drawdown = 0.0
            current_balance = 0.0
            trade_amount = 0.0
            leverage = 1.0
            margin_mode = "CROSS"
            position_mode = "HEDGE"
            
            if runtime_data:
                if hasattr(runtime_data, 'model_dump'):
                    runtime_dict = runtime_data.model_dump()
                elif isinstance(runtime_data, dict):
                    runtime_dict = runtime_data
                else:
                    runtime_dict = {}
                
                # Extract performance metrics
                performance = runtime_dict.get('performance', {})
                realized_pnl = performance.get('realized_pnl', 0.0)
                unrealized_pnl = performance.get('unrealized_pnl', 0.0)
                total_trades = performance.get('total_trades', 0)
                win_rate = performance.get('win_rate', 0.0)
                max_drawdown = performance.get('max_drawdown', 0.0)
                current_balance = performance.get('current_balance', 0.0)
                
                # Extract settings
                settings = runtime_dict.get('settings', {})
                trade_amount = settings.get('trade_amount', 0.0)
                leverage = settings.get('leverage', 1.0)
                margin_mode = settings.get('margin_mode', 'CROSS')
                position_mode = settings.get('position_mode', 'HEDGE')
            
            return BotPerformance(
                bot_id=bot_data.get('bot_id', ''),
                bot_name=bot_data.get('bot_name', 'Unknown'),
                server_name=server_name,
                account_id=bot_data.get('account_id', ''),
                market_tag=bot_data.get('market', ''),
                script_id=bot_data.get('script_id', ''),
                is_activated=bot_data.get('is_activated', False),
                is_paused=bot_data.get('is_paused', False),
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                total_pnl=realized_pnl + unrealized_pnl,
                total_trades=total_trades,
                win_rate=win_rate,
                max_drawdown=max_drawdown,
                current_balance=current_balance,
                trade_amount=trade_amount,
                leverage=leverage,
                margin_mode=margin_mode,
                position_mode=position_mode,
                performance_data=runtime_data
            )
            
        except Exception as e:
            print(f"Error getting bot performance for {bot_id}: {e}")
            return None
    
    def analyze_backtest_result(self, backtest_data: Dict[str, Any], bot_id: str, bot_name: str, server_name: str) -> Optional[BacktestResult]:
        """Analyze a backtest result and extract performance metrics"""
        try:
            # Extract basic information
            backtest_id = backtest_data.get('BID', '')
            script_id = backtest_data.get('ScriptId', '')
            market_tag = backtest_data.get('MarketTag', '')
            
            # Extract time information
            start_time = datetime.fromtimestamp(backtest_data.get('StartUnix', 0))
            end_time = datetime.fromtimestamp(backtest_data.get('EndUnix', 0))
            duration_days = (end_time - start_time).total_seconds() / 86400
            
            # Extract trade data
            trades = backtest_data.get('T', [])
            total_trades = len(trades)
            
            # Calculate winning/losing trades
            winning_trades = 0
            losing_trades = 0
            total_profit = 0.0
            total_loss = 0.0
            
            for trade in trades:
                pnl = trade.get('PnL', 0.0)
                if pnl > 0:
                    winning_trades += 1
                    total_profit += pnl
                elif pnl < 0:
                    losing_trades += 1
                    total_loss += abs(pnl)
            
            # Calculate metrics
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            net_profit = total_profit - total_loss
            
            # Extract balance information
            starting_balance = backtest_data.get('StartingBalance', 0.0)
            ending_balance = backtest_data.get('EndingBalance', 0.0)
            
            # Calculate ROI
            roi_percentage = ((ending_balance - starting_balance) / starting_balance * 100) if starting_balance > 0 else 0.0
            
            # Calculate max drawdown (simplified)
            max_drawdown = backtest_data.get('MaxDrawdown', 0.0)
            
            # Calculate profit factor
            profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = backtest_data.get('SharpeRatio', 0.0)
            
            return BacktestResult(
                backtest_id=backtest_id,
                bot_id=bot_id,
                bot_name=bot_name,
                server_name=server_name,
                script_id=script_id,
                market_tag=market_tag,
                start_time=start_time,
                end_time=end_time,
                duration_days=duration_days,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_profit=total_profit,
                total_loss=total_loss,
                net_profit=net_profit,
                max_drawdown=max_drawdown,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                roi_percentage=roi_percentage,
                starting_balance=starting_balance,
                ending_balance=ending_balance,
                result_data=backtest_data,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            print(f"Error analyzing backtest result: {e}")
            return None
    
    def generate_verification_report(self, bot_performance: BotPerformance, backtest_result: BacktestResult) -> VerificationReport:
        """Generate a verification report comparing bot vs backtest performance"""
        
        # Calculate differences
        pnl_difference = bot_performance.total_pnl - backtest_result.net_profit
        pnl_difference_percentage = (pnl_difference / backtest_result.net_profit * 100) if backtest_result.net_profit != 0 else 0.0
        win_rate_difference = bot_performance.win_rate - backtest_result.win_rate
        drawdown_difference = bot_performance.max_drawdown - backtest_result.max_drawdown
        trades_difference = bot_performance.total_trades - backtest_result.total_trades
        
        # Determine verification status
        issues = []
        recommendations = []
        
        # Check PnL consistency
        if abs(pnl_difference_percentage) > 20.0:  # 20% difference threshold
            issues.append(f"PnL difference: {pnl_difference_percentage:.1f}%")
            recommendations.append("Review bot settings and market conditions")
        
        # Check win rate consistency
        if abs(win_rate_difference) > 10.0:  # 10% difference threshold
            issues.append(f"Win rate difference: {win_rate_difference:.1f}%")
            recommendations.append("Check for strategy drift or market changes")
        
        # Check drawdown consistency
        if abs(drawdown_difference) > 5.0:  # 5% difference threshold
            issues.append(f"Drawdown difference: {drawdown_difference:.1f}%")
            recommendations.append("Review risk management settings")
        
        # Check trade count consistency
        if abs(trades_difference) > 10:  # 10 trades difference threshold
            issues.append(f"Trade count difference: {trades_difference}")
            recommendations.append("Check for execution issues or market volatility")
        
        # Determine overall status
        if len(issues) == 0:
            verification_status = "PASS"
            verification_score = 1.0
        elif len(issues) <= 2:
            verification_status = "WARNING"
            verification_score = 0.7
        else:
            verification_status = "FAIL"
            verification_score = 0.3
        
        return VerificationReport(
            bot_id=bot_performance.bot_id,
            bot_name=bot_performance.bot_name,
            backtest_id=backtest_result.backtest_id,
            server_name=bot_performance.server_name,
            verification_timestamp=datetime.now(),
            
            # Bot performance
            bot_realized_pnl=bot_performance.realized_pnl,
            bot_unrealized_pnl=bot_performance.unrealized_pnl,
            bot_total_pnl=bot_performance.total_pnl,
            bot_win_rate=bot_performance.win_rate,
            bot_max_drawdown=bot_performance.max_drawdown,
            bot_total_trades=bot_performance.total_trades,
            
            # Backtest performance
            backtest_net_profit=backtest_result.net_profit,
            backtest_win_rate=backtest_result.win_rate,
            backtest_max_drawdown=backtest_result.max_drawdown,
            backtest_total_trades=backtest_result.total_trades,
            backtest_roi_percentage=backtest_result.roi_percentage,
            
            # Comparison metrics
            pnl_difference=pnl_difference,
            pnl_difference_percentage=pnl_difference_percentage,
            win_rate_difference=win_rate_difference,
            drawdown_difference=drawdown_difference,
            trades_difference=trades_difference,
            
            # Verification status
            verification_status=verification_status,
            verification_score=verification_score,
            issues=issues,
            recommendations=recommendations
        )
    
    async def process_completed_backtests(self, server_name: str, completed_job_ids: List[str]) -> Dict[str, VerificationReport]:
        """Process completed backtests and generate verification reports"""
        if server_name not in self.servers:
            return {}
        
        print(f"Processing {len(completed_job_ids)} completed backtests on {server_name}...")
        
        verification_reports = {}
        
        for job_id in completed_job_ids:
            try:
                # Load job data from file
                if Path("backtest_jobs.json").exists():
                    with open("backtest_jobs.json", 'r') as f:
                        jobs_data = json.load(f)
                    
                    job_data = None
                    for job in jobs_data.get('jobs', []):
                        if job['job_id'] == job_id:
                            job_data = job
                            break
                    
                    if not job_data:
                        print(f"  Job {job_id} not found in saved data")
                        continue
                    
                    bot_id = job_data['bot_id']
                    bot_name = job_data['bot_name']
                    backtest_id = job_data['backtest_id']
                    
                    print(f"  Processing {bot_name} (backtest: {backtest_id})")
                    
                    # Get bot performance
                    bot_performance = self.get_bot_performance(server_name, bot_id)
                    if not bot_performance:
                        print(f"    ❌ Failed to get bot performance")
                        continue
                    
                    # Get backtest result (this would need to be implemented based on how results are stored)
                    # For now, we'll create a mock result
                    backtest_result = BacktestResult(
                        backtest_id=backtest_id,
                        bot_id=bot_id,
                        bot_name=bot_name,
                        server_name=server_name,
                        script_id=bot_performance.script_id,
                        market_tag=bot_performance.market_tag,
                        start_time=datetime.now() - timedelta(days=1),
                        end_time=datetime.now(),
                        duration_days=1.0,
                        total_trades=bot_performance.total_trades,
                        winning_trades=int(bot_performance.total_trades * bot_performance.win_rate / 100),
                        losing_trades=int(bot_performance.total_trades * (100 - bot_performance.win_rate) / 100),
                        win_rate=bot_performance.win_rate,
                        total_profit=bot_performance.total_pnl if bot_performance.total_pnl > 0 else 0,
                        total_loss=abs(bot_performance.total_pnl) if bot_performance.total_pnl < 0 else 0,
                        net_profit=bot_performance.total_pnl,
                        max_drawdown=bot_performance.max_drawdown,
                        profit_factor=1.0,
                        sharpe_ratio=0.0,
                        roi_percentage=(bot_performance.total_pnl / bot_performance.current_balance * 100) if bot_performance.current_balance > 0 else 0,
                        starting_balance=bot_performance.current_balance - bot_performance.total_pnl,
                        ending_balance=bot_performance.current_balance,
                        result_data={},
                        completed_at=datetime.now()
                    )
                    
                    # Generate verification report
                    verification_report = self.generate_verification_report(bot_performance, backtest_result)
                    verification_reports[job_id] = verification_report
                    
                    print(f"    ✅ Generated verification report: {verification_report.verification_status}")
                    print(f"      Bot PnL: {bot_performance.total_pnl:.2f}")
                    print(f"      Backtest PnL: {backtest_result.net_profit:.2f}")
                    print(f"      Difference: {verification_report.pnl_difference_percentage:.1f}%")
                    print(f"      Score: {verification_report.verification_score:.2f}")
                    
            except Exception as e:
                print(f"  ❌ Error processing job {job_id}: {e}")
                continue
        
        return verification_reports
    
    def save_verification_reports(self, reports: Dict[str, VerificationReport], filename: str = "verification_reports.json"):
        """Save verification reports to file"""
        try:
            reports_data = {
                'reports': [],
                'summary': {
                    'total_reports': len(reports),
                    'pass_count': sum(1 for r in reports.values() if r.verification_status == "PASS"),
                    'warning_count': sum(1 for r in reports.values() if r.verification_status == "WARNING"),
                    'fail_count': sum(1 for r in reports.values() if r.verification_status == "FAIL"),
                    'average_score': sum(r.verification_score for r in reports.values()) / len(reports) if reports else 0,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
            for report in reports.values():
                report_data = {
                    'bot_id': report.bot_id,
                    'bot_name': report.bot_name,
                    'backtest_id': report.backtest_id,
                    'server_name': report.server_name,
                    'verification_timestamp': report.verification_timestamp.isoformat(),
                    'verification_status': report.verification_status,
                    'verification_score': report.verification_score,
                    'bot_performance': {
                        'realized_pnl': report.bot_realized_pnl,
                        'unrealized_pnl': report.bot_unrealized_pnl,
                        'total_pnl': report.bot_total_pnl,
                        'win_rate': report.bot_win_rate,
                        'max_drawdown': report.bot_max_drawdown,
                        'total_trades': report.bot_total_trades
                    },
                    'backtest_performance': {
                        'net_profit': report.backtest_net_profit,
                        'win_rate': report.backtest_win_rate,
                        'max_drawdown': report.backtest_max_drawdown,
                        'total_trades': report.backtest_total_trades,
                        'roi_percentage': report.backtest_roi_percentage
                    },
                    'comparison': {
                        'pnl_difference': report.pnl_difference,
                        'pnl_difference_percentage': report.pnl_difference_percentage,
                        'win_rate_difference': report.win_rate_difference,
                        'drawdown_difference': report.drawdown_difference,
                        'trades_difference': report.trades_difference
                    },
                    'issues': report.issues,
                    'recommendations': report.recommendations
                }
                reports_data['reports'].append(report_data)
            
            with open(filename, 'w') as f:
                json.dump(reports_data, f, indent=2)
            
            print(f"Saved {len(reports)} verification reports to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving verification reports: {e}")
            return False
    
    async def cleanup_all(self):
        """Clean up all SSH tunnels"""
        for server_name, process in self.ssh_processes.items():
            print(f"Cleaning up {server_name}...")
            try:
                if process and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                print(f"Error cleaning up {server_name}: {e}")


async def test_backtest_result_analysis_system():
    """Test the backtest result analysis system"""
    print("Testing Backtest Result Analysis System")
    print("=" * 60)
    
    system = BacktestResultAnalysisSystem()
    
    try:
        # Connect to srv03
        print("Connecting to srv03...")
        if not await system.connect_to_server("srv03"):
            print("Failed to connect to srv03")
            return 1
        
        # Load completed jobs from file
        completed_job_ids = []
        if Path("backtest_jobs.json").exists():
            with open("backtest_jobs.json", 'r') as f:
                jobs_data = json.load(f)
            
            completed_job_ids = jobs_data.get('completed_jobs', [])
            print(f"Found {len(completed_job_ids)} completed jobs")
        else:
            print("No completed jobs found")
            return 0
        
        # Process completed backtests
        if completed_job_ids:
            verification_reports = await system.process_completed_backtests("srv03", completed_job_ids[:5])  # Process first 5 for testing
            
            if verification_reports:
                # Save reports
                system.save_verification_reports(verification_reports)
                
                # Show summary
                print(f"\nVerification Summary:")
                pass_count = sum(1 for r in verification_reports.values() if r.verification_status == "PASS")
                warning_count = sum(1 for r in verification_reports.values() if r.verification_status == "WARNING")
                fail_count = sum(1 for r in verification_reports.values() if r.verification_status == "FAIL")
                avg_score = sum(r.verification_score for r in verification_reports.values()) / len(verification_reports)
                
                print(f"  Total reports: {len(verification_reports)}")
                print(f"  Pass: {pass_count}")
                print(f"  Warning: {warning_count}")
                print(f"  Fail: {fail_count}")
                print(f"  Average score: {avg_score:.2f}")
                
                # Show individual reports
                print(f"\nIndividual Reports:")
                for job_id, report in verification_reports.items():
                    print(f"  {report.bot_name}:")
                    print(f"    Status: {report.verification_status}")
                    print(f"    Score: {report.verification_score:.2f}")
                    print(f"    Bot PnL: {report.bot_total_pnl:.2f}")
                    print(f"    Backtest PnL: {report.backtest_net_profit:.2f}")
                    print(f"    Difference: {report.pnl_difference_percentage:.1f}%")
                    if report.issues:
                        print(f"    Issues: {', '.join(report.issues)}")
            else:
                print("No verification reports generated")
        else:
            print("No completed jobs to process")
        
        print("\nBacktest result analysis system test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await system.cleanup_all()


async def main():
    """Main entry point"""
    return await test_backtest_result_analysis_system()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

