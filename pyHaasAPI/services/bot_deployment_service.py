"""
Bot Deployment Service for pyHaasAPI v2

Orchestrates automated bot deployment for labs without bots, including:
- Finding top N backtests per lab (zero drawdown only)
- Assigning unused BINANCEFUTURES USDT accounts
- Creating bots with proper naming
- Running verification backtests
- Building comprehensive tracking notes
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import asdict

from ..core.logging import get_logger
from ..api.bot.bot_api import BotAPI
from ..api.account.account_api import AccountAPI
from ..api.backtest.backtest_api import BacktestAPI
from ..api.lab.lab_api import LabAPI
from ..services.analysis.cached_analysis_service import (
    CachedAnalysisService,
    CachedBacktestPerformance
)
from ..services.bot_naming_service import BotNamingService, BotNamingContext
from ..services.longest_backtest_service import LongestBacktestService
from ..models.account import AccountRecord


logger = get_logger("bot_deployment_service")


class BotDeploymentService:
    """
    Service for deploying bots to labs without bots
    
    Creates top N bots per lab with individual accounts, proper naming,
    verification backtests, and comprehensive tracking notes.
    """
    
    def __init__(
        self,
        bot_api: BotAPI,
        account_api: AccountAPI,
        backtest_api: BacktestAPI,
        lab_api: LabAPI,
        cached_analysis_service: CachedAnalysisService,
        longest_backtest_service: LongestBacktestService,
        bot_naming_service: Optional[BotNamingService] = None
    ):
        self.bot_api = bot_api
        self.account_api = account_api
        self.backtest_api = backtest_api
        self.lab_api = lab_api
        self.cached_analysis = cached_analysis_service
        self.longest_backtest_service = longest_backtest_service
        self.bot_naming_service = bot_naming_service or BotNamingService()
        self.logger = get_logger("bot_deployment_service")
        
        # Track used accounts to avoid conflicts during batch deployment
        self._assigned_accounts: set = set()
    
    async def deploy_bots_for_labs_without_bots(
        self,
        labs_without_bots: List[Dict[str, Any]],
        bots_per_lab: int = 5,
        trade_amount_usdt: float = 2000.0,
        leverage: int = 20,
        min_win_rate: float = 0.55,  # Standardized: 55%+ win rate
        max_drawdown: float = 0.0,   # Standardized: Zero drawdown only
        verify_with_backtest: bool = True,
        verification_days: int = 7   # 7-day verification backtest
    ) -> Dict[str, Any]:
        """
        Deploy top N bots for all labs without bots
        
        Args:
            labs_without_bots: List of lab records without bots
            bots_per_lab: Number of bots to create per lab (default: 5)
            trade_amount_usdt: Trade amount in USDT (default: 2000)
            leverage: Leverage to use (default: 20)
            min_win_rate: Minimum win rate filter (default: 0.55 for 55%+)
            max_drawdown: Maximum drawdown (default: 0.0 for zero drawdown only)
            verify_with_backtest: Run verification backtest (default: True)
            verification_days: Days to run verification backtest (default: 7)
            
        Returns:
            Deployment results with success/failure counts and details
            
        CRITICAL: Lab metrics are NOT reliable - always calculate from raw trade data
        """
        self.logger.info(f"Starting bot deployment for {len(labs_without_bots)} labs")
        self.logger.info(f"Creating {bots_per_lab} bots per lab ({len(labs_without_bots) * bots_per_lab} total)")
        
        results = {
            "labs_processed": 0,
            "bots_created": 0,
            "bots_failed": 0,
            "accounts_assigned": 0,
            "verifications_completed": 0,
            "verifications_failed": 0,
            "lab_results": []
        }
        
        for lab in labs_without_bots:
            lab_id = lab.get("lab_id") or lab.get("id")
            lab_name = lab.get("lab_name") or lab.get("name")
            
            self.logger.info(f"Processing lab: {lab_name} ({lab_id[:8]}...)")
            
            lab_result = await self._deploy_bots_for_single_lab(
                lab_id=lab_id,
                lab_name=lab_name,
                lab_data=lab,
                bots_per_lab=bots_per_lab,
                trade_amount_usdt=trade_amount_usdt,
                leverage=leverage,
                min_win_rate=min_win_rate,
                max_drawdown=max_drawdown,
                verify_with_backtest=verify_with_backtest,
                verification_days=verification_days
            )
            
            results["labs_processed"] += 1
            results["bots_created"] += lab_result["bots_created"]
            results["bots_failed"] += lab_result["bots_failed"]
            results["accounts_assigned"] += lab_result["accounts_assigned"]
            results["verifications_completed"] += lab_result["verifications_completed"]
            results["verifications_failed"] += lab_result["verifications_failed"]
            results["lab_results"].append(lab_result)
        
        self.logger.info(f"Deployment complete: {results['bots_created']} bots created, {results['bots_failed']} failed")
        return results
    
    async def _deploy_bots_for_single_lab(
        self,
        lab_id: str,
        lab_name: str,
        lab_data: Dict[str, Any],
        bots_per_lab: int,
        trade_amount_usdt: float,
        leverage: int,
        min_win_rate: float,
        max_drawdown: float,
        verify_with_backtest: bool,
        verification_days: int
    ) -> Dict[str, Any]:
        """Deploy bots for a single lab"""
        result = {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "bots_created": 0,
            "bots_failed": 0,
            "accounts_assigned": 0,
            "verifications_completed": 0,
            "verifications_failed": 0,
            "bots": []
        }
        
        try:
            # Find top N backtests for this lab
            top_backtests = await self._find_top_backtests_for_lab(
                lab_id=lab_id,
                count=bots_per_lab,
                min_win_rate=min_win_rate,
                max_drawdown=max_drawdown
            )
            
            if not top_backtests:
                self.logger.warning(f"No suitable backtests found for lab {lab_name}")
                result["error"] = "No suitable backtests found"
                return result
            
            self.logger.info(f"Found {len(top_backtests)} suitable backtests for {lab_name}")
            
            # Deploy bot for each backtest
            for i, backtest in enumerate(top_backtests, 1):
                bot_result = await self._deploy_single_bot(
                    lab_id=lab_id,
                    lab_name=lab_name,
                    lab_data=lab_data,
                    backtest=backtest,
                    bot_index=i,
                    trade_amount_usdt=trade_amount_usdt,
                    leverage=leverage,
                    verify_with_backtest=verify_with_backtest,
                    verification_days=verification_days
                )
                
                if bot_result["success"]:
                    result["bots_created"] += 1
                    result["accounts_assigned"] += 1
                    if bot_result.get("verification_completed"):
                        result["verifications_completed"] += 1
                else:
                    result["bots_failed"] += 1
                    if bot_result.get("verification_failed"):
                        result["verifications_failed"] += 1
                
                result["bots"].append(bot_result)
        
        except Exception as e:
            self.logger.error(f"Failed to deploy bots for lab {lab_name}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _deploy_single_bot(
        self,
        lab_id: str,
        lab_name: str,
        lab_data: Dict[str, Any],
        backtest: CachedBacktestPerformance,
        bot_index: int,
        trade_amount_usdt: float,
        leverage: int,
        verify_with_backtest: bool,
        verification_days: int
    ) -> Dict[str, Any]:
        """Deploy a single bot"""
        result = {
            "success": False,
            "bot_id": None,
            "bot_name": None,
            "account_id": None,
            "backtest_id": backtest.backtest_id,
            "verification_completed": False,
            "verification_failed": False,
            "error": None
        }
        
        try:
            # Assign unused account
            account = await self._assign_unused_account(exchange="BINANCEFUTURES")
            if not account:
                result["error"] = "No unused accounts available"
                return result
            
            result["account_id"] = getattr(account, 'account_id', None)
            self.logger.info(f"Assigned account {result['account_id'][:8]}... for bot {bot_index}")
            
            # Generate bot name
            naming_context = BotNamingContext(
                server=lab_data.get("server", "srv03"),
                script_name=backtest.script_name,
                market_tag=backtest.market_tag,
                roi_percentage=backtest.roi_percentage,
                win_rate=backtest.win_rate,
                max_drawdown=backtest.max_drawdown,
                total_trades=backtest.total_trades,
                profit_factor=backtest.profit_factor,
                sharpe_ratio=backtest.sharpe_ratio
            )
            bot_name = self.bot_naming_service.generate_bot_name(
                naming_context,
                strategy="server-specific"
            )
            result["bot_name"] = bot_name
            
            # Create bot from lab
            bot_details = await self.bot_api.create_bot_from_lab(
                lab_id=lab_id,
                backtest_id=backtest.backtest_id,
                bot_name=bot_name,
                account_id=result["account_id"],
                market=backtest.market_tag,
                leverage=leverage
            )
            
            result["bot_id"] = getattr(bot_details, 'bot_id', None)
            result["success"] = True
            self.logger.info(f"Created bot {bot_name} ({result['bot_id'][:8]}...)")
            
            # Run verification backtest if requested
            verification_result = None
            if verify_with_backtest:
                try:
                    verification_result = await self._execute_verification_backtest(
                        bot_id=result["bot_id"],
                        bot_data=asdict(bot_details) if hasattr(bot_details, '__dict__') else {},
                        lab_id=lab_id,
                        use_longest_backtest=True
                    )
                    result["verification_completed"] = True
                    self.logger.info(f"Verification backtest completed for {bot_name}")
                except Exception as e:
                    self.logger.error(f"Verification backtest failed for {bot_name}: {e}")
                    result["verification_failed"] = True
                    verification_result = {"error": str(e), "status": "failed"}
            
            # Build and update bot notes
            notes = self._build_bot_notes(
                bot_id=result["bot_id"],
                lab_id=lab_id,
                lab_name=lab_name,
                lab_data=lab_data,
                account_id=result["account_id"],
                account_starting_balance=10000.0,
                lab_backtest=backtest,
                verification_result=verification_result
            )
            
            await self._update_bot_notes(result["bot_id"], notes)
            self.logger.info(f"Updated notes for {bot_name}")
        
        except Exception as e:
            self.logger.error(f"Failed to deploy bot for {lab_name} backtest {backtest.backtest_id[:8]}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _find_top_backtests_for_lab(
        self,
        lab_id: str,
        count: int = 5,
        min_win_rate: float = 0.3,
        max_drawdown: float = 0.0
    ) -> List[CachedBacktestPerformance]:
        """
        Find top N best performing backtests for lab from cache
        
        CRITICAL: Strict zero drawdown filter (max_drawdown = 0.0)
        """
        try:
            # Analyze lab from cache
            analysis = await self.cached_analysis.analyze_lab_from_cache(
                lab_id=lab_id,
                top_count=count * 2,  # Get extra in case some fail filters
                min_win_rate=min_win_rate,
                min_trades=5,
                max_drawdown=max_drawdown,
                sort_by="roe"
            )
            
            if not analysis.success or not analysis.top_performers:
                return []
            
            # Return top N performers
            return analysis.top_performers[:count]
        
        except Exception as e:
            self.logger.error(f"Failed to find backtests for lab {lab_id}: {e}")
            return []
    
    async def _assign_unused_account(
        self,
        exchange: str = "BINANCEFUTURES"
    ) -> Optional[AccountRecord]:
        """
        Assign an existing unused BINANCEFUTURES USDT account
        
        Account already has 10,000 USDT balance, other currencies at zero
        Tracks assigned accounts to avoid conflicts during batch deployment
        """
        try:
            # Get all accounts for exchange
            accounts = await self.account_api.get_accounts(exchange=exchange)
            
            if not accounts:
                self.logger.error(f"No accounts available for {exchange}")
                return None
            
            # Find unused account (not in assigned set)
            for account in accounts:
                account_id = getattr(account, 'account_id', None)
                if account_id and account_id not in self._assigned_accounts:
                    # Mark as assigned
                    self._assigned_accounts.add(account_id)
                    self.logger.info(f"Assigned unused account: {account_id[:8]}...")
                    return account
            
            self.logger.warning(f"No unused accounts available for {exchange}")
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to assign account: {e}")
            return None
    
    async def _execute_verification_backtest(
        self,
        bot_id: str,
        bot_data: Dict[str, Any],
        lab_id: str,
        use_longest_backtest: bool = True
    ) -> Dict[str, Any]:
        """
        Run individual backtest to verify bot configuration
        
        Uses longest possible backtest algorithm:
        1. Start with 36 months -> step down until RUNNING
        2. Step UP by weeks until QUEUED
        3. Fine-tune by adding days until QUEUED
        
        CRITICAL: Calculate all metrics from raw trade data, not lab data
        Verification backtests expire in 48 hours - cache raw data immediately
        """
        try:
            # Determine backtest period
            if use_longest_backtest:
                # Use longest backtest algorithm from LongestBacktestService
                self.logger.info(f"Finding longest backtest period for lab {lab_id}")
                start_unix, end_unix, period_name, success = await self.longest_backtest_service.find_longest_working_period(lab_id)
                
                if not success or start_unix is None or end_unix is None:
                    self.logger.warning(f"Longest backtest failed for lab {lab_id}, using fallback (2 years)")
                    # Fallback to 2 years
                    end_time = datetime.now()
                    start_time = end_time - timedelta(days=730)
                    duration_days = 730
                else:
                    start_time = datetime.fromtimestamp(start_unix)
                    end_time = datetime.fromtimestamp(end_unix)
                    duration_days = (end_time - start_time).days
                    self.logger.info(f"Using longest period: {period_name} ({duration_days} days)")
            else:
                # Fallback to fixed duration
                end_time = datetime.now()
                start_time = end_time - timedelta(days=730)
                duration_days = 730
            
            # Execute backtest with calculated period
            self.logger.info(f"Executing bot backtest for {duration_days} days")
            backtest_result = await self.backtest_api.execute_bot_backtest(
                bot_data=bot_data,
                start_time=start_time,
                end_time=end_time
            )
            
            backtest_id = getattr(backtest_result, 'backtest_id', None)
            executed_at = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(hours=48)).isoformat()
            
            # Cache raw backtest data immediately (expires in 48 hours)
            cache_path = await self._cache_verification_backtest(
                bot_id=bot_id,
                backtest_id=backtest_id,
                backtest_result=backtest_result
            )
            
            # Calculate metrics from raw trade data
            metrics = self._calculate_metrics_from_trades(backtest_result)
            
            return {
                "backtest_id": backtest_id,
                "executed_at": executed_at,
                "expires_at": expires_at,
                "duration_days": duration_days,
                "start_date": start_time.isoformat(),
                "end_date": end_time.isoformat(),
                "roe": metrics["roe"],
                "win_rate": metrics["win_rate"],
                "total_trades": metrics["total_trades"],
                "max_drawdown": metrics["max_drawdown"],
                "profit_factor": metrics["profit_factor"],
                "realized_profit": metrics["realized_profit"],
                "largest_win": metrics["largest_win"],
                "largest_loss": metrics["largest_loss"],
                "consecutive_wins": metrics["consecutive_wins"],
                "status": "viable" if metrics["max_drawdown"] == 0.0 else "rejected",
                "raw_data_cached": True,
                "cache_path": str(cache_path),
                "notes": "Initial verification - " + ("passed zero drawdown test" if metrics["max_drawdown"] == 0.0 else "FAILED zero drawdown test")
            }
        
        except Exception as e:
            self.logger.error(f"Failed to execute verification backtest for bot {bot_id}: {e}")
            raise
    
    async def _cache_verification_backtest(
        self,
        bot_id: str,
        backtest_id: str,
        backtest_result: Any
    ) -> Path:
        """Cache verification backtest raw data (expires in 48 hours)"""
        cache_dir = Path("unified_cache") / "verification_backtests"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cache_file = cache_dir / f"bot_{bot_id[:8]}_{timestamp}.json"
        
        # Convert backtest result to dict for JSON serialization
        if hasattr(backtest_result, '__dict__'):
            data = backtest_result.__dict__
        elif hasattr(backtest_result, 'model_dump'):
            data = backtest_result.model_dump()
        else:
            data = dict(backtest_result)
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Cached verification backtest to {cache_file}")
        return cache_file
    
    def _calculate_metrics_from_trades(
        self,
        backtest_result: Any
    ) -> Dict[str, Any]:
        """
        Calculate all metrics from raw trade data
        
        CRITICAL: Never trust lab metrics - always calculate from trades
        ROE = realized_profit / starting_balance * 100
        """
        # Extract trade data
        trades = getattr(backtest_result, 'trades', [])
        starting_balance = getattr(backtest_result, 'starting_balance', 10000.0)
        
        if not trades:
            return {
                "roe": 0.0,
                "win_rate": 0.0,
                "total_trades": 0,
                "max_drawdown": 0.0,
                "profit_factor": 0.0,
                "realized_profit": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "consecutive_wins": 0
            }
        
        # Calculate metrics
        winning_trades = [t for t in trades if getattr(t, 'profit', 0) > 0]
        losing_trades = [t for t in trades if getattr(t, 'profit', 0) < 0]
        
        total_profit = sum(getattr(t, 'profit', 0) for t in winning_trades)
        total_loss = abs(sum(getattr(t, 'profit', 0) for t in losing_trades))
        realized_profit = total_profit - total_loss
        
        roe = (realized_profit / starting_balance) * 100 if starting_balance > 0 else 0.0
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0.0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0
        
        largest_win = max((getattr(t, 'profit', 0) for t in winning_trades), default=0.0)
        largest_loss = abs(min((getattr(t, 'profit', 0) for t in losing_trades), default=0.0))
        
        # Calculate consecutive wins
        consecutive_wins = 0
        max_consecutive_wins = 0
        for trade in trades:
            if getattr(trade, 'profit', 0) > 0:
                consecutive_wins += 1
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_wins = 0
        
        # Calculate max drawdown
        balance = starting_balance
        peak_balance = starting_balance
        max_drawdown = 0.0
        
        for trade in trades:
            balance += getattr(trade, 'profit', 0)
            peak_balance = max(peak_balance, balance)
            drawdown = ((peak_balance - balance) / peak_balance) if peak_balance > 0 else 0.0
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "roe": round(roe, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": len(trades),
            "max_drawdown": round(max_drawdown, 4),
            "profit_factor": round(profit_factor, 2),
            "realized_profit": round(realized_profit, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "consecutive_wins": max_consecutive_wins
        }
    
    def _build_bot_notes(
        self,
        bot_id: str,
        lab_id: str,
        lab_name: str,
        lab_data: Dict[str, Any],
        account_id: str,
        account_starting_balance: float,
        lab_backtest: CachedBacktestPerformance,
        verification_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build comprehensive JSON notes for bot tracking with size safety check
        
        CRITICAL: Lab metrics marked as unreliable - for reference only
        """
        notes = {
            "bot_id": bot_id,
            "lab_id": lab_id,
            "lab_name": lab_name,
            "created_at": datetime.now().isoformat(),
            "account_id": account_id,
            "account_starting_balance": account_starting_balance,
            "lab_statistics": {
                "note": "Lab metrics NOT reliable - for reference only",
                "source_backtest_id": lab_backtest.backtest_id,
                "lab_roi": lab_backtest.roi_percentage,
                "lab_win_rate": lab_backtest.win_rate,
                "lab_total_trades": lab_backtest.total_trades,
                "lab_max_drawdown": lab_backtest.max_drawdown,
                "lab_profit_factor": lab_backtest.profit_factor,
                "lab_sharpe_ratio": lab_backtest.sharpe_ratio
            },
            "verification_backtests": [verification_result] if verification_result else [],
            "viability_assessment": {
                "last_updated": datetime.now().isoformat(),
                "status": "pending" if not verification_result else verification_result.get("status", "pending"),
                "roe_avg": verification_result.get("roe", 0.0) if verification_result else 0.0,
                "zero_drawdown_maintained": verification_result.get("max_drawdown", 0.0) == 0.0 if verification_result else False,
                "backtests_analyzed": 1 if verification_result else 0,
                "recommendation": "PENDING - Awaiting verification" if not verification_result else verification_result.get("notes", ""),
                "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
            }
        }
        
        # Serialize with readable format
        json_str = json.dumps(notes, indent=2)
        
        # Size check (50KB limit for safety)
        if len(json_str) > 50000:
            self.logger.warning(f"Bot notes too large: {len(json_str)} bytes, truncating verification backtests")
            # Keep only last 5 verification backtests to reduce size
            notes["verification_backtests"] = notes["verification_backtests"][-5:]
            json_str = json.dumps(notes, indent=2)
            self.logger.info(f"Bot notes truncated to {len(json_str)} bytes")
        
        return json_str
    
    async def _update_bot_notes(
        self,
        bot_id: str,
        notes: str
    ) -> bool:
        """Update bot notes via API"""
        try:
            await self.bot_api.change_bot_notes(bot_id=bot_id, notes=notes)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update notes for bot {bot_id}: {e}")
            return False

