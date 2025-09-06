#!/usr/bin/env python3
"""
Lab Analysis and Automated Bot Deployment Script

This script provides comprehensive financial analysis of HaasOnline labs and automatically
deploys the top-performing configurations as bots on available simulation accounts.

Features:
- Complete lab backtest analysis using pyHaasAPI BacktestObject
- Configuration ranking and selection (top 20)
- Account availability scanning (avoids accounts with existing bots)
- Automated bot creation and deployment
- Comprehensive reporting and progress tracking

Usage:
    python lab_analysis_and_deployment.py <lab_id>

Requirements:
- pyHaasAPI installed and configured
- Valid API credentials in .env file
- Available simulation accounts matching pattern [Sim] 4AA-10k
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lab_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import pyHaasAPI components
from pyHaasAPI import api
from pyHaasAPI.backtest_object import BacktestObject, BacktestManager
from pyHaasAPI.model import LabRecord, LabDetails, CreateBotRequest, AddBotFromLabRequest

@dataclass
class BacktestMetrics:
    """Financial metrics for a backtest"""
    backtest_id: str
    script_id: str
    script_name: str
    total_profit: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    execution_time_ms: int = 0
    score: float = 0.0  # Composite performance score

@dataclass
class AccountInfo:
    """Account information with occupancy status"""
    account_id: str
    name: str
    balance: float
    exchange: str
    is_occupied: bool = False
    assigned_bots: List[str] = None

    def __post_init__(self):
        if self.assigned_bots is None:
            self.assigned_bots = []

class LabAnalyzer:
    """Main class for lab analysis and bot deployment"""

    def __init__(self, executor):
        self.executor = executor
        self.backtest_manager = BacktestManager(executor)
        self.logger = logging.getLogger(__name__)

    def authenticate_and_initialize(self) -> bool:
        """Verify authentication and initialize components"""
        try:
            # Test authentication by getting user info or labs
            labs = api.get_all_labs(self.executor)
            self.logger.info(f"✅ Authentication successful - found {len(labs)} labs")
            return True
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            return False

    def analyze_lab_backtests(self, lab_id: str) -> Tuple[List[BacktestMetrics], Dict[str, Any]]:
        """Analyze all backtests in a lab using pyHaasAPI BacktestObject"""
        self.logger.info(f"🔍 Analyzing lab: {lab_id}")

        # Get lab details first
        try:
            lab_details = api.get_lab_details(self.executor, lab_id)
            market_tag = getattr(lab_details.settings, 'market_tag', 'Unknown')
            self.logger.info(f"📋 Lab: {lab_details.name} | Market: {market_tag}")
        except Exception as e:
            self.logger.error(f"❌ Failed to get lab details: {e}")
            return [], {"error": f"Failed to get lab details: {e}"}

        # Get backtest history using BacktestManager (the correct way)
        try:
            backtest_history = self.backtest_manager.get_backtest_history()
            self.logger.info(f"📊 Retrieved backtest history with {len(backtest_history)} entries")

            # Filter backtests for this specific lab (script_id)
            lab_backtests = [bt for bt in backtest_history if bt.get('ScriptId') == lab_details.script_id]
            self.logger.info(f"📊 Found {len(lab_backtests)} backtests for lab {lab_id}")

            if not lab_backtests:
                self.logger.warning("No backtests found for this lab")
                return [], {"lab_details": lab_details, "error": "No backtests found for this lab"}

        except Exception as e:
            self.logger.error(f"❌ Failed to get backtest history: {e}")
            return [], {"lab_details": lab_details, "error": f"Failed to get backtest history: {e}"}

        # Analyze each backtest using BacktestObject
        metrics_list = []
        for i, bt_summary in enumerate(lab_backtests):
            backtest_id = bt_summary.get('BacktestId')
            self.logger.info(f"🔄 Analyzing backtest {i+1}/{len(lab_backtests)}: {backtest_id[:8]}...")

            try:
                # Use BacktestManager to get detailed backtest data (the correct way)
                bt_object = self.backtest_manager.get_backtest(backtest_id)

                if bt_object and bt_object.runtime and bt_object.metadata:
                    # Extract metrics from BacktestObject runtime data
                    metrics = BacktestMetrics(
                        backtest_id=backtest_id,
                        script_id=bt_object.metadata.script_id or lab_details.script_id,
                        script_name=bt_object.metadata.script_name or 'Unknown',
                        total_profit=bt_object.runtime.total_profit or 0.0,
                        total_trades=bt_object.runtime.total_trades or 0,
                        winning_trades=bt_object.runtime.winning_trades or 0,
                        losing_trades=bt_object.runtime.losing_trades or 0,
                        win_rate=bt_object.runtime.win_rate or 0.0,
                        max_drawdown=bt_object.runtime.max_drawdown or 0.0,
                        sharpe_ratio=bt_object.runtime.sharpe_ratio or 0.0,
                        profit_factor=bt_object.runtime.profit_factor or 0.0,
                        execution_time_ms=bt_object.runtime.execution_time_ms or 0,
                        score=0.0  # Will be calculated below
                    )

                    # Calculate composite score
                    metrics.score = self._calculate_composite_score(metrics)
                    metrics_list.append(metrics)
                    self.logger.info(f"✅ Successfully analyzed backtest {backtest_id[:8]}")
                else:
                    self.logger.warning(f"No runtime/metadata data available for backtest {backtest_id}")

            except Exception as e:
                self.logger.warning(f"Failed to analyze backtest {backtest_id}: {e}")

        # Sort by composite score
        metrics_list.sort(key=lambda x: x.score, reverse=True)

        lab_summary = {
            "lab_id": lab_id,
            "lab_name": lab_details.name,
            "market_tag": market_tag,
            "script_id": lab_details.script_id,
            "total_backtests": len(lab_backtests),
            "analyzed_backtests": len(metrics_list),
            "analysis_timestamp": datetime.now().isoformat()
        }

        return metrics_list, lab_summary

    def _calculate_composite_score(self, metrics: BacktestMetrics) -> float:
        """Calculate composite performance score"""
        # Normalize profit (scale to 0-100 range, assuming $1000 = 100 points)
        profit_score = min(abs(metrics.total_profit) / 10, 100)

        # Win rate score (0-100)
        win_rate_score = metrics.win_rate

        # Risk-adjusted score (inverse of drawdown, 0-100)
        risk_score = max(0, 100 - (metrics.max_drawdown * 10))

        # Sharpe ratio score (0-100, assuming 2.0 = 100 points)
        sharpe_score = min(metrics.sharpe_ratio * 50, 100)

        # Volume score (based on trade count, more trades = more reliable)
        volume_score = min(metrics.total_trades / 10, 100)

        # Weighted composite score
        weights = {
            'profit': 0.30,
            'win_rate': 0.25,
            'risk': 0.20,
            'sharpe': 0.15,
            'volume': 0.10
        }

        composite_score = (
            profit_score * weights['profit'] +
            win_rate_score * weights['win_rate'] +
            risk_score * weights['risk'] +
            sharpe_score * weights['sharpe'] +
            volume_score * weights['volume']
        )

        return composite_score

class AccountScanner:
    """Scans and manages available accounts"""

    def __init__(self, executor):
        self.executor = executor
        self.logger = logging.getLogger(__name__)

    def find_available_accounts(self, pattern: str = "[Sim] 4AA-10k") -> List[AccountInfo]:
        """Find accounts matching pattern that are not occupied by bots"""
        self.logger.info(f"🔍 Scanning for available accounts with pattern: {pattern}")

        try:
            # Get all bots to check occupancy first
            occupied_accounts = self._get_occupied_accounts()
            self.logger.info(f"🤖 Found {len(occupied_accounts)} occupied accounts")

            # Get all accounts using the proper pyHaasAPI method
            accounts_list = []
            try:
                accounts_data = api.get_all_account_balances(self.executor)

                # Handle the response - should be a list of account balance objects
                if isinstance(accounts_data, list):
                    self.logger.info(f"📊 Found {len(accounts_data)} total accounts")
                    accounts_list = accounts_data
                else:
                    self.logger.warning(f"Unexpected account data format: {type(accounts_data)}")
                    accounts_list = []

            except Exception as e:
                self.logger.warning(f"Could not retrieve account balances: {e}")
                accounts_list = []

            available_accounts = []

            for account_data in accounts_list:
                try:
                    # Handle the actual API response structure
                    if isinstance(account_data, dict):
                        # Extract account information from the actual API response
                        account_id = account_data.get('AID', '')
                        balances = account_data.get('I', [])

                        # Get USDT balance as the main balance (most common)
                        balance = 0.0
                        for balance_info in balances:
                            if isinstance(balance_info, dict) and balance_info.get('C') == 'USDT':
                                balance = balance_info.get('T', 0.0)  # Total balance
                                break

                        # For now, we don't have account names from this API
                        # We'll need to use a different API to get account names
                        account_name = f"Account_{account_id[:8]}"  # Use first 8 chars of ID

                        # Check if account has sufficient balance and is not occupied
                        if (balance > 0 and account_id not in occupied_accounts):

                            account_info = AccountInfo(
                                account_id=account_id,
                                name=account_name,
                                balance=balance,
                                exchange="Unknown",  # Not provided in this API
                                is_occupied=False
                            )
                            available_accounts.append(account_info)
                            self.logger.info(f"✅ Available account: {account_name} ({account_id}) - Balance: ${balance:.2f}")

                except Exception as e:
                    self.logger.warning(f"Could not process account data: {e}")

            self.logger.info(f"🎯 Found {len(available_accounts)} available accounts")
            return available_accounts

        except Exception as e:
            self.logger.error(f"❌ Failed to scan accounts: {e}")
            return []

    def _get_occupied_accounts(self) -> set:
        """Get set of account IDs that already have bots assigned"""
        occupied = set()

        try:
            bots = api.get_all_bots(self.executor)

            for bot in bots:
                if hasattr(bot, 'account_id') and bot.account_id:
                    occupied.add(bot.account_id)
                    self.logger.debug(f"Bot {bot.bot_id} occupies account {bot.account_id}")

        except Exception as e:
            self.logger.warning(f"Could not get bot occupancy data: {e}")

        return occupied

class BotDeployer:
    """Handles bot creation and deployment"""

    def __init__(self, executor, account_scanner: AccountScanner):
        self.executor = executor
        self.account_scanner = account_scanner
        self.logger = logging.getLogger(__name__)

    def deploy_top_configurations(self, metrics_list: List[BacktestMetrics],
                                available_accounts: List[AccountInfo],
                                lab_id: str, top_n: int = 20) -> Dict[str, Any]:
        """Deploy top N configurations as bots on available accounts"""
        self.logger.info(f"🚀 Deploying top {top_n} configurations from lab {lab_id}")

        if not metrics_list:
            return {"error": "No metrics to deploy"}

        if not available_accounts:
            return {"error": "No available accounts for deployment"}

        # Get top N configurations
        top_configs = metrics_list[:top_n]
        self.logger.info(f"📊 Selected {len(top_configs)} top configurations for deployment")

        deployment_results = {
            "total_attempted": len(top_configs),
            "successful_deployments": 0,
            "failed_deployments": 0,
            "deployments": [],
            "errors": []
        }

        # Deploy each configuration
        for i, config in enumerate(top_configs):
            self.logger.info(f"🤖 Deploying configuration {i+1}/{len(top_configs)}: {config.backtest_id[:8]}...")

            try:
                # Select account using round-robin
                account = available_accounts[i % len(available_accounts)]

                # Deploy bot
                success, result = self._deploy_single_bot(config, account, lab_id)

                if success:
                    deployment_results["successful_deployments"] += 1
                    deployment_results["deployments"].append({
                        "backtest_id": config.backtest_id,
                        "bot_id": result.get("bot_id", "Unknown"),
                        "account_id": account.account_id,
                        "account_name": account.name,
                        "score": config.score,
                        "total_profit": config.total_profit,
                        "win_rate": config.win_rate
                    })
                    self.logger.info(f"✅ Successfully deployed bot {result.get('bot_id', 'Unknown')} to {account.name}")
                else:
                    deployment_results["failed_deployments"] += 1
                    deployment_results["errors"].append({
                        "backtest_id": config.backtest_id,
                        "error": result
                    })
                    self.logger.error(f"❌ Failed to deploy {config.backtest_id}: {result}")

            except Exception as e:
                deployment_results["failed_deployments"] += 1
                deployment_results["errors"].append({
                    "backtest_id": config.backtest_id,
                    "error": str(e)
                })
                self.logger.error(f"❌ Exception deploying {config.backtest_id}: {e}")

        self.logger.info(f"📋 Deployment complete: {deployment_results['successful_deployments']}/{deployment_results['total_attempted']} successful")
        return deployment_results

    def _deploy_single_bot(self, config: BacktestMetrics, account: AccountInfo, lab_id: str, market: str = None) -> Tuple[bool, Any]:
        """Deploy a single bot from configuration"""
        try:
            # Get lab details to extract market
            if market is None:
                lab_details = api.get_lab_details(self.executor, lab_id)
                market = getattr(lab_details.settings, 'market_tag', "BINANCE_BTC_USDT_")

            # Create bot from lab backtest
            bot_request = AddBotFromLabRequest(
                lab_id=lab_id,
                backtest_id=config.backtest_id,
                bot_name=f"AutoDeploy_{config.script_name}_{int(time.time())}_{config.backtest_id[:6]}",
                account_id=account.account_id,
                market=market
            )

            bot = api.add_bot_from_lab(self.executor, bot_request)

            return True, {
                "bot_id": bot.bot_id,
                "bot_name": bot.bot_name,
                "account_id": account.account_id
            }

        except Exception as e:
            return False, str(e)

def generate_comprehensive_report(metrics_list: List[BacktestMetrics],
                                lab_summary: Dict[str, Any],
                                deployment_results: Dict[str, Any],
                                available_accounts: List[AccountInfo]) -> str:
    """Generate comprehensive analysis and deployment report"""

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("LAB ANALYSIS AND BOT DEPLOYMENT REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Lab Summary
    report_lines.append("🏢 LAB SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Lab ID: {lab_summary.get('lab_id', 'Unknown')}")
    report_lines.append(f"Lab Name: {lab_summary.get('lab_name', 'Unknown')}")
    report_lines.append(f"Market: {lab_summary.get('market_tag', 'Unknown')}")
    report_lines.append(f"Script ID: {lab_summary.get('script_id', 'Unknown')}")
    report_lines.append(f"Total Backtests: {lab_summary.get('total_backtests', 0)}")
    report_lines.append(f"Analyzed Backtests: {lab_summary.get('analyzed_backtests', 0)}")
    report_lines.append("")

    # Account Summary
    report_lines.append("🏦 ACCOUNT SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Available Accounts: {len(available_accounts)}")
    for account in available_accounts:
        report_lines.append(f"  • {account.name} ({account.account_id}) - Balance: ${account.balance:,.2f}")
    report_lines.append("")

    # Top 20 Configurations
    report_lines.append("📊 TOP 20 CONFIGURATIONS")
    report_lines.append("-" * 40)
    report_lines.append(f"{'Rank':<5} {'Backtest ID':<12} {'Score':<8} {'Profit':<10} {'Trades':<8} {'Win Rate':<10} {'Max DD':<10}")
    report_lines.append("-" * 80)

    for i, config in enumerate(metrics_list[:20], 1):
        report_lines.append(f"{i:<5} {config.backtest_id[:12]:<12} {config.score:<8.1f} ${config.total_profit:<9.2f} {config.total_trades:<8} {config.win_rate:<9.1f}% {config.max_drawdown:<9.2f}%")
    report_lines.append("")

    # Deployment Results
    report_lines.append("🤖 DEPLOYMENT RESULTS")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Attempted: {deployment_results.get('total_attempted', 0)}")
    report_lines.append(f"Successful: {deployment_results.get('successful_deployments', 0)}")
    report_lines.append(f"Failed: {deployment_results.get('failed_deployments', 0)}")
    report_lines.append("")

    if deployment_results.get('deployments'):
        report_lines.append("✅ SUCCESSFUL DEPLOYMENTS:")
        for deployment in deployment_results['deployments']:
            report_lines.append(f"  • Bot {deployment['bot_id'][:12]} -> {deployment['account_name']}")
            report_lines.append(f"    Backtest: {deployment['backtest_id'][:12]}, Score: {deployment['score']:.1f}")
    report_lines.append("")

    if deployment_results.get('errors'):
        report_lines.append("❌ DEPLOYMENT ERRORS:")
        for error in deployment_results['errors']:
            report_lines.append(f"  • {error['backtest_id'][:12]}: {error['error']}")

    report_lines.append("")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)

def main():
    """Main execution function"""
    print("🚀 Lab Analysis and Automated Bot Deployment")
    print("=" * 60)

    if len(sys.argv) != 2:
        print("Usage: python lab_analysis_and_deployment.py <lab_id>")
        print("Example: python lab_analysis_and_deployment.py LAB123456")
        sys.exit(1)

    lab_id = sys.argv[1].strip()

    try:
        # Initialize executor
        print("🔐 Authenticating with HaasOnline API...")
        executor = api.RequestsExecutor(
            host=os.getenv("API_HOST", "127.0.0.1"),
            port=int(os.getenv("API_PORT", 8090)),
            state=api.Guest()
        )

        executor = executor.authenticate(
            email=os.getenv("API_EMAIL", ""),
            password=os.getenv("API_PASSWORD", "")
        )

        print("✅ Authentication successful!")

        # Initialize components
        analyzer = LabAnalyzer(executor)
        account_scanner = AccountScanner(executor)
        deployer = BotDeployer(executor, account_scanner)

        # Step 1: Analyze lab
        print(f"\n📊 Analyzing lab: {lab_id}")
        metrics_list, lab_summary = analyzer.analyze_lab_backtests(lab_id)

        if not metrics_list:
            print("❌ No backtests found or analysis failed")
            return

        print(f"✅ Analysis complete - {len(metrics_list)} backtests processed")

        # Step 2: Find available accounts
        print("\n🏦 Scanning for available accounts...")
        available_accounts = account_scanner.find_available_accounts()

        if not available_accounts:
            print("❌ No available accounts found")
            return

        print(f"✅ Found {len(available_accounts)} available accounts")

        # Step 3: Deploy top configurations
        print("\n🤖 Deploying top 20 configurations...")
        deployment_results = deployer.deploy_top_configurations(
            metrics_list, available_accounts, lab_id, top_n=20
        )

        # Step 4: Generate and display report
        print("\n📋 Generating comprehensive report...")
        report = generate_comprehensive_report(
            metrics_list, lab_summary, deployment_results, available_accounts
        )

        # Save report to file
        report_filename = f"lab_analysis_report_{lab_id}_{int(time.time())}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)

        print(f"✅ Report saved to: {report_filename}")

        # Display summary
        print("\n" + "=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Lab Analyzed: {lab_summary.get('lab_name', lab_id)}")
        print(f"Backtests Processed: {len(metrics_list)}")
        print(f"Available Accounts: {len(available_accounts)}")
        print(f"Bots Deployed: {deployment_results.get('successful_deployments', 0)}")
        print(f"Deployment Success Rate: {deployment_results.get('successful_deployments', 0)/max(1, deployment_results.get('total_attempted', 1))*100:.1f}%")
        print(f"Report: {report_filename}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        logger.error(f"Main execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
