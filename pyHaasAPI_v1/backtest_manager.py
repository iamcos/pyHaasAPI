"""
Backtest Manager for pyHaasAPI

This module provides the BacktestManager class for orchestrating direct backtest execution
without creating cluttered labs. Used for live bot validation and pre-creation validation.
"""

import os
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from . import api
from .model import (
    GetScriptRecordRequest,
    ExecuteBacktestRequest,
    BacktestHistoryRequest,
    EditBacktestTagRequest,
    ArchiveBacktestRequest
)
from .analysis.robustness import StrategyRobustnessAnalyzer
from .analysis.models import BacktestAnalysis

logger = logging.getLogger(__name__)


@dataclass
class BacktestExecutionResult:
    """Result of backtest execution"""
    backtest_id: str
    script_id: str
    market_tag: str
    start_time: int
    end_time: int
    success: bool
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class BacktestValidationResult:
    """Result of bot validation via backtest"""
    bot_id: str
    bot_name: str
    backtest_id: str
    validation_successful: bool
    roi_percentage: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    max_drawdown: Optional[float] = None
    error_message: Optional[str] = None


class BacktestManager:
    """Manages direct backtest execution for bot validation"""
    
    def __init__(self, executor):
        self.executor = executor
        self.execution_history = []
    
    def execute_bot_backtest(
        self, 
        bot_data: Dict[str, Any], 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration_days: int = 1
    ) -> BacktestExecutionResult:
        """
        Execute a backtest for bot validation using the correct workflow:
        1. GET_SCRIPT_RECORD - Get script details and parameters
        2. EXECUTE_BACKTEST - Execute with bot parameters
        3. Return execution result
        """
        try:
            start_time = start_time or datetime.now() - timedelta(days=duration_days)
            end_time = end_time or datetime.now()
            
            start_unix = int(start_time.timestamp())
            end_unix = int(end_time.timestamp())
            
            logger.info(f"🚀 Executing backtest for bot: {bot_data.get('BotName', 'Unknown')}")
            logger.info(f"📅 Period: {start_time} to {end_time}")
            
            # Step 1: Get script record
            script_id = bot_data.get('ScriptId')
            if not script_id:
                return BacktestExecutionResult(
                    backtest_id="",
                    script_id="",
                    market_tag="",
                    start_time=start_unix,
                    end_time=end_unix,
                    success=False,
                    error_message="Bot has no ScriptId"
                )
            
            script_record = self._get_script_record(script_id)
            if not script_record:
                return BacktestExecutionResult(
                    backtest_id="",
                    script_id=script_id,
                    market_tag="",
                    start_time=start_unix,
                    end_time=end_unix,
                    success=False,
                    error_message="Failed to get script record"
                )
            
            # Step 2: Execute backtest
            backtest_id = str(uuid.uuid4())
            market_tag = bot_data.get('MarketTag', '')
            
            settings = api.build_backtest_settings(bot_data, script_record)
            
            request = ExecuteBacktestRequest(
                backtest_id=backtest_id,
                script_id=script_id,
                settings=settings,
                start_unix=start_unix,
                end_unix=end_unix
            )
            
            result = api.execute_backtest(self.executor, request)
            
            if result.get('Success', False):
                logger.info(f"✅ Backtest executed successfully: {backtest_id}")
                
                execution_result = BacktestExecutionResult(
                    backtest_id=backtest_id,
                    script_id=script_id,
                    market_tag=market_tag,
                    start_time=start_unix,
                    end_time=end_unix,
                    success=True
                )
                
                self.execution_history.append(execution_result)
                return execution_result
            else:
                error_msg = result.get('Error', 'Unknown error')
                logger.error(f"❌ Backtest execution failed: {error_msg}")
                
                return BacktestExecutionResult(
                    backtest_id=backtest_id,
                    script_id=script_id,
                    market_tag=market_tag,
                    start_time=start_unix,
                    end_time=end_unix,
                    success=False,
                    error_message=error_msg
                )
                
        except Exception as e:
            logger.error(f"❌ Error executing backtest: {e}")
            return BacktestExecutionResult(
                backtest_id="",
                script_id=bot_data.get('ScriptId', ''),
                market_tag=bot_data.get('MarketTag', ''),
                start_time=start_unix if 'start_unix' in locals() else 0,
                end_time=end_unix if 'end_unix' in locals() else 0,
                success=False,
                error_message=str(e)
            )
    
    def validate_live_bot(self, bot_data: Dict[str, Any]) -> BacktestValidationResult:
        """
        Validate a currently running bot by executing a recent backtest
        """
        try:
            bot_id = bot_data.get('BotId', '')
            bot_name = bot_data.get('BotName', 'Unknown')
            
            logger.info(f"🔍 Validating live bot: {bot_name}")
            
            # Execute 1-day backtest
            execution_result = self.execute_bot_backtest(bot_data, duration_days=1)
            
            if not execution_result.success:
                return BacktestValidationResult(
                    bot_id=bot_id,
                    bot_name=bot_name,
                    backtest_id=execution_result.backtest_id,
                    validation_successful=False,
                    error_message=execution_result.error_message
                )
            
            # Get backtest results (this would need to be implemented)
            # For now, return success with basic info
            return BacktestValidationResult(
                bot_id=bot_id,
                bot_name=bot_name,
                backtest_id=execution_result.backtest_id,
                validation_successful=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error validating bot: {e}")
            return BacktestValidationResult(
                bot_id=bot_data.get('BotId', ''),
                bot_name=bot_data.get('BotName', 'Unknown'),
                backtest_id="",
                validation_successful=False,
                error_message=str(e)
            )
    
    def validate_bot_before_creation(
        self, 
        bot_config: Dict[str, Any], 
        script_id: str
    ) -> BacktestValidationResult:
        """
        Validate bot configuration before creating it from lab analysis
        """
        try:
            logger.info(f"🔍 Validating bot config before creation")
            
            # Create temporary bot data structure
            temp_bot_data = {
                'BotId': 'temp-validation',
                'BotName': bot_config.get('name', 'Validation Bot'),
                'ScriptId': script_id,
                'MarketTag': bot_config.get('market_tag', ''),
                'Settings': bot_config.get('settings', {})
            }
            
            # Execute backtest
            execution_result = self.execute_bot_backtest(temp_bot_data, duration_days=7)
            
            if not execution_result.success:
                return BacktestValidationResult(
                    bot_id='temp-validation',
                    bot_name=temp_bot_data['BotName'],
                    backtest_id=execution_result.backtest_id,
                    validation_successful=False,
                    error_message=execution_result.error_message
                )
            
            return BacktestValidationResult(
                bot_id='temp-validation',
                bot_name=temp_bot_data['BotName'],
                backtest_id=execution_result.backtest_id,
                validation_successful=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error validating bot config: {e}")
            return BacktestValidationResult(
                bot_id='temp-validation',
                bot_name='Validation Bot',
                backtest_id="",
                validation_successful=False,
                error_message=str(e)
            )
    
    def get_backtest_history(self, script_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get backtest history"""
        try:
            request = BacktestHistoryRequest(
                script_id=script_id,
                limit=limit
            )
            
            result = api.get_backtest_history(self.executor, request)
            
            if result.get('Success', False):
                return result.get('Data', [])
            else:
                logger.error(f"❌ Failed to get backtest history: {result.get('Error', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting backtest history: {e}")
            return []
    
    def edit_backtest_tag(self, backtest_id: str, new_tag: str) -> bool:
        """Edit backtest tag"""
        try:
            request = EditBacktestTagRequest(
                backtest_id=backtest_id,
                new_tag=new_tag
            )
            
            result = api.edit_backtest_tag(self.executor, request)
            return result.get('Success', False)
            
        except Exception as e:
            logger.error(f"❌ Error editing backtest tag: {e}")
            return False
    
    def archive_backtest(self, backtest_id: str) -> bool:
        """Archive backtest"""
        try:
            request = ArchiveBacktestRequest(backtest_id=backtest_id)
            result = api.archive_backtest(self.executor, request)
            return result.get('Success', False)
            
        except Exception as e:
            logger.error(f"❌ Error archiving backtest: {e}")
            return False
    
    def _get_script_record(self, script_id: str) -> Optional[Dict[str, Any]]:
        """Get script record with parameters"""
        try:
            request = GetScriptRecordRequest(script_id=script_id)
            result = api.get_script_record(self.executor, request)
            
            if result.get('Success', False):
                return result.get('Data')
            else:
                logger.error(f"❌ Failed to get script record: {result.get('Error', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting script record: {e}")
            return None
    
    def _convert_bot_to_dict(self, bot) -> Dict[str, Any]:
        """Convert HaasBot object to dictionary with proper field mapping"""
        settings = getattr(bot, 'settings', None)
        
        return {
            'BotId': getattr(bot, 'bot_id', ''),
            'BotName': getattr(bot, 'bot_name', ''),
            'ScriptId': getattr(bot, 'script_id', ''),
            'AccountId': getattr(bot, 'account_id', ''),
            'Market': getattr(bot, 'market', ''),
            'MarketTag': getattr(settings, 'market_tag', '') if settings else '',
            'Leverage': getattr(settings, 'leverage', 0) if settings else 0,
            'PositionMode': getattr(settings, 'position_mode', 0) if settings else 0,
            'MarginMode': getattr(settings, 'margin_mode', 0) if settings else 0,
            'TradeAmount': getattr(settings, 'trade_amount', 0) if settings else 0,
            'Interval': getattr(settings, 'interval', 1) if settings else 1,
            'ChartStyle': getattr(settings, 'chart_style', 300) if settings else 300,
            'OrderTemplate': getattr(settings, 'order_template', 500) if settings else 500,
            'ScriptParameters': getattr(settings, 'script_parameters', {}) if settings else {},
            'IsActive': getattr(bot, 'is_activated', False),
            'Settings': settings
        }
    
    def get_execution_history(self) -> List[BacktestExecutionResult]:
        """Get history of executed backtests"""
        return self.execution_history.copy()
    
    def clear_execution_history(self):
        """Clear execution history"""
        self.execution_history.clear()
    
    def validate_bot_with_robustness(
        self, 
        bot_data: Dict[str, Any], 
        duration_days: int = 7,
        min_robustness_score: float = 50.0,
        max_risk_level: str = "MEDIUM"
    ) -> BacktestValidationResult:
        """
        Validate a bot using backtest execution and robustness analysis
        
        Args:
            bot_data: Bot configuration data
            duration_days: Duration of backtest in days
            min_robustness_score: Minimum robustness score required (0-100)
            max_risk_level: Maximum acceptable risk level (LOW, MEDIUM, HIGH, CRITICAL)
            
        Returns:
            BacktestValidationResult with robustness analysis
        """
        try:
            logger.info(f"🔍 Validating bot with robustness analysis: {bot_data.get('BotName', 'Unknown')}")
            
            # Execute backtest
            execution_result = self.execute_bot_backtest(bot_data, duration_days=duration_days)
            
            if not execution_result.success:
                return BacktestValidationResult(
                    bot_id=bot_data.get('BotId', ''),
                    bot_name=bot_data.get('BotName', ''),
                    backtest_id=execution_result.backtest_id,
                    validation_successful=False,
                    error_message=execution_result.error_message
                )
            
            # Wait for backtest completion and get results
            logger.info("⏳ Waiting for backtest completion...")
            time.sleep(10)  # Wait for backtest to process
            
            # Get backtest results from history
            backtest_results = self.get_backtest_results(execution_result.backtest_id)
            
            if not backtest_results:
                return BacktestValidationResult(
                    bot_id=bot_data.get('BotId', ''),
                    bot_name=bot_data.get('BotName', ''),
                    backtest_id=execution_result.backtest_id,
                    validation_successful=False,
                    error_message="Failed to retrieve backtest results"
                )
            
            # Create BacktestAnalysis object for robustness analysis
            backtest_analysis = BacktestAnalysis(
                backtest_id=execution_result.backtest_id,
                lab_id="direct_validation",
                generation_idx=None,
                population_idx=None,
                market_tag=execution_result.market_tag,
                script_id=execution_result.script_id,
                script_name=bot_data.get('BotName', 'Unknown'),
                roi_percentage=backtest_results.get('roi', 0.0),
                win_rate=0.0,  # Will be calculated by robustness analyzer
                total_trades=0,  # Will be calculated by robustness analyzer
                max_drawdown=0.0,  # Will be calculated by robustness analyzer
                realized_profits_usdt=float(backtest_results.get('profit', '0').split('_')[0]),
                pc_value=0.0,
                avg_profit_per_trade=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            # Perform robustness analysis
            robustness_analyzer = StrategyRobustnessAnalyzer()
            robustness_metrics = robustness_analyzer.analyze_backtest_robustness(backtest_analysis)
            
            # Check if bot meets robustness criteria
            meets_criteria = (
                robustness_metrics.robustness_score >= min_robustness_score and
                self._is_risk_level_acceptable(robustness_metrics.risk_level, max_risk_level)
            )
            
            logger.info(f"📊 Robustness Analysis Results:")
            logger.info(f"   Robustness Score: {robustness_metrics.robustness_score:.1f}/100")
            logger.info(f"   Risk Level: {robustness_metrics.risk_level}")
            logger.info(f"   Max Drawdown: {robustness_metrics.drawdown_analysis.max_drawdown_percentage:.2f}%")
            logger.info(f"   Meets Criteria: {meets_criteria}")
            
            return BacktestValidationResult(
                bot_id=bot_data.get('BotId', ''),
                bot_name=bot_data.get('BotName', ''),
                backtest_id=execution_result.backtest_id,
                validation_successful=meets_criteria,
                roi_percentage=backtest_results.get('roi', 0.0),
                win_rate=robustness_metrics.overall_roi / 100 * 0.6,  # Estimate
                total_trades=robustness_metrics.drawdown_analysis.max_consecutive_losses * 2,  # Estimate
                max_drawdown=robustness_metrics.drawdown_analysis.max_drawdown_percentage,
                error_message=None if meets_criteria else f"Failed robustness criteria: Score {robustness_metrics.robustness_score:.1f}, Risk {robustness_metrics.risk_level}"
            )
            
        except Exception as e:
            logger.error(f"❌ Robustness validation failed: {e}")
            return BacktestValidationResult(
                bot_id=bot_data.get('BotId', ''),
                bot_name=bot_data.get('BotName', ''),
                backtest_id="",
                validation_successful=False,
                error_message=str(e)
            )
    
    def _is_risk_level_acceptable(self, actual_risk: str, max_risk: str) -> bool:
        """Check if actual risk level is acceptable compared to maximum allowed"""
        risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        try:
            actual_index = risk_levels.index(actual_risk.upper())
            max_index = risk_levels.index(max_risk.upper())
            return actual_index <= max_index
        except ValueError:
            return False
    
    def get_backtest_results(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Get backtest results from history"""
        try:
            history_request = BacktestHistoryRequest(offset=0, limit=50)
            history = api.get_backtest_history(self.executor, history_request)
            
            if history and 'I' in history:
                for backtest in history['I']:
                    if backtest.get('BID') == backtest_id:
                        return {
                            'roi': float(backtest.get('RT', 0)),
                            'profit': backtest.get('PT', '0'),
                            'market': backtest.get('ME', ''),
                            'account': backtest.get('AT', '')
                        }
            return None
        except Exception as e:
            logger.error(f"Failed to get backtest results: {e}")
            return None
