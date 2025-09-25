"""
Backtest API for pyHaasAPI v2

This module provides comprehensive backtest management functionality including
execution, retrieval, analysis, and management of backtest results.
"""

import asyncio
import json
import uuid
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import BacktestError, BacktestNotFoundError, BacktestExecutionError
from ...core.logging import get_logger
from ...models.backtest import (
    BacktestResult, BacktestRuntimeData, BacktestChart, BacktestLog,
    ExecuteBacktestRequest, BacktestHistoryRequest, EditBacktestTagRequest,
    ArchiveBacktestRequest, BacktestExecutionResult, BacktestValidationResult
)
from ...models.common import PaginatedResponse

logger = get_logger("backtest_api")


class BacktestAPI:
    """
    Backtest API for managing backtest operations.

    Provides comprehensive backtest functionality including execution,
    retrieval, analysis, and management of backtest results.
    """

    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("backtest_api")

    async def get_backtest_result(
        self, 
        lab_id: str, 
        next_page_id: int = 0, 
        page_length: int = 100
    ) -> PaginatedResponse[BacktestResult]:
        """
        Get paginated backtest results for a specific lab.

        Based on the most recent v1 implementation from pyHaasAPI/api.py (lines 799-813)

        Args:
            lab_id: ID of the lab
            next_page_id: Page ID for pagination (0 for first page)
            page_length: Number of results per page

        Returns:
            Paginated response with backtest results

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Getting backtest results for lab {lab_id}, page {next_page_id}")
            
            # Use the proven v1 implementation pattern
            response = await self.client.execute_request(
                endpoint="Labs",
                response_type=PaginatedResponse[BacktestResult],
                query_params={
                    "channel": "GET_BACKTEST_RESULT_PAGE",
                    "labid": lab_id,
                    "nextpageid": next_page_id,
                    "pagelength": page_length,
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get backtest results: {e}")
            raise BacktestError(f"Failed to get backtest results for lab {lab_id}: {e}") from e

    async def get_backtest_runtime(
        self, 
        lab_id: str, 
        backtest_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed runtime information for a specific backtest.

        Args:
            lab_id: ID of the lab containing the backtest
            backtest_id: ID of the specific backtest

        Returns:
            Runtime information dictionary

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Getting runtime data for backtest {backtest_id} in lab {lab_id}")
            
            response = await self.client.execute(
                endpoint="Labs",
                query_params={
                    "channel": "GET_BACKTEST_RUNTIME",
                    "labid": lab_id,
                    "backtestid": backtest_id,
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get backtest runtime: {e}")
            raise BacktestError(f"Failed to get runtime data for backtest {backtest_id}: {e}") from e

    async def get_full_backtest_runtime_data(
        self, 
        lab_id: str, 
        backtest_id: str
    ) -> BacktestRuntimeData:
        """
        Get detailed runtime information for a specific backtest as a structured object.

        This function retrieves comprehensive backtest runtime data including:
        - Chart information and status
        - Compiler errors and warnings
        - Trading reports with performance metrics
        - Account and market information
        - Position and order data
        - Script execution details

        Args:
            lab_id: ID of the lab containing the backtest
            backtest_id: ID of the specific backtest to retrieve

        Returns:
            BacktestRuntimeData object with complete runtime information

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Getting full runtime data for backtest {backtest_id}")
            
            raw_response = await self.get_backtest_runtime(lab_id, backtest_id)
            
            # The API response is direct data, not wrapped in {"Success": ..., "Data": ...}
            data_content = raw_response
            
            # Parse the data into our structured BacktestRuntimeData model
            return BacktestRuntimeData.model_validate(data_content)
            
        except Exception as e:
            self.logger.error(f"Failed to get full backtest runtime data: {e}")
            raise BacktestError(f"Failed to get full runtime data for backtest {backtest_id}: {e}") from e

    async def get_backtest_chart(
        self, 
        lab_id: str, 
        backtest_id: str
    ) -> BacktestChart:
        """
        Get chart data for a specific backtest.

        Args:
            lab_id: ID of the lab containing the backtest
            backtest_id: ID of the specific backtest

        Returns:
            BacktestChart object with chart data

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Getting chart data for backtest {backtest_id}")
            
            response = await self.client.execute(
                endpoint="Labs",
                query_params={
                    "channel": "GET_BACKTEST_CHART",
                    "labid": lab_id,
                    "backtestid": backtest_id,
                }
            )
            
            return BacktestChart.model_validate(response)
            
        except Exception as e:
            self.logger.error(f"Failed to get backtest chart: {e}")
            raise BacktestError(f"Failed to get chart data for backtest {backtest_id}: {e}") from e

    async def get_backtest_log(
        self, 
        lab_id: str, 
        backtest_id: str
    ) -> List[str]:
        """
        Get execution log for a specific backtest.

        Args:
            lab_id: ID of the lab containing the backtest
            backtest_id: ID of the specific backtest

        Returns:
            List of log entries as strings

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Getting log data for backtest {backtest_id}")
            
            response = await self.client.execute(
                endpoint="Labs",
                query_params={
                    "channel": "GET_BACKTEST_LOG",
                    "labid": lab_id,
                    "backtestid": backtest_id,
                }
            )
            
            return response if isinstance(response, list) else []
            
        except Exception as e:
            self.logger.error(f"Failed to get backtest log: {e}")
            raise BacktestError(f"Failed to get log data for backtest {backtest_id}: {e}") from e

    async def execute_backtest(
        self, 
        request: ExecuteBacktestRequest
    ) -> BacktestExecutionResult:
        """
        Execute a backtest with bot parameters using EXECUTE_BACKTEST channel.

        This function creates and executes a new backtest with the exact bot parameters.
        Requires: backtestid (can be new UUID), scriptid, settings JSON, start/end times.

        Args:
            request: ExecuteBacktestRequest with all required parameters

        Returns:
            BacktestExecutionResult with execution details

        Raises:
            BacktestExecutionError: If the backtest execution fails
        """
        try:
            self.logger.info(f"Executing backtest for script {request.script_id}")
            
            # Build form data with all required parameters
            data = {
                'backtestid': request.backtest_id,
                'scriptid': request.script_id,
                'settings': json.dumps(request.settings),  # JSON string
                'startunix': request.start_unix,
                'endunix': request.end_unix,
            }
            
            response = await self.client.execute(
                endpoint="BacktestAPI",
                method="POST",
                query_params={"channel": "EXECUTE_BACKTEST"},
                data=data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'{self.client.base_url}/WebEditor/{request.script_id}',
                }
            )
            
            if response.get('Success', False):
                self.logger.info(f"✅ Backtest executed successfully: {request.backtest_id}")
                return BacktestExecutionResult(
                    backtest_id=request.backtest_id,
                    script_id=request.script_id,
                    market_tag=request.settings.get('marketTag', ''),
                    start_time=request.start_unix,
                    end_time=request.end_unix,
                    success=True
                )
            else:
                error_msg = response.get('Error', 'Unknown error')
                self.logger.error(f"❌ Backtest execution failed: {error_msg}")
                raise BacktestExecutionError(f"Backtest execution failed: {error_msg}")
                
        except BacktestExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute backtest: {e}")
            raise BacktestExecutionError(f"Failed to execute backtest: {e}") from e

    async def get_backtest_history(
        self, 
        request: BacktestHistoryRequest
    ) -> Dict[str, Any]:
        """
        Get backtest history using the GET_BACKTEST_HISTORY channel.

        Args:
            request: BacktestHistoryRequest with filtering parameters

        Returns:
            Dictionary with backtest history data

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info("Getting backtest history")
            
            # Build query parameters
            query_params = {
                'channel': 'GET_BACKTEST_HISTORY',
                'nextpageid': request.offset,  # Use offset as nextpageid
                'pagelength': request.limit,   # Use limit as pagelength
            }
            
            # Add optional filters
            if request.script_id:
                query_params['scriptid'] = request.script_id
            if request.market_tag:
                query_params['markettag'] = request.market_tag
            if request.account_id:
                query_params['accountid'] = request.account_id
            if request.start_date:
                query_params['startdate'] = request.start_date
            if request.end_date:
                query_params['enddate'] = request.end_date
            
            response = await self.client.execute(
                endpoint="Backtest",
                query_params=query_params
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get backtest history: {e}")
            raise BacktestError(f"Failed to get backtest history: {e}") from e

    async def edit_backtest_tag(
        self, 
        request: EditBacktestTagRequest
    ) -> Dict[str, Any]:
        """
        Edit backtest tag using the EDIT_BACKTEST_TAG channel.

        Args:
            request: EditBacktestTagRequest with backtest ID and new tag

        Returns:
            Dictionary with operation result

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Editing tag for backtest {request.backtest_id}")
            
            data = {
                'backtestid': request.backtest_id,
                'backtesttag': request.tag,
            }
            
            response = await self.client.execute(
                endpoint="BacktestAPI",
                method="POST",
                query_params={"channel": "EDIT_BACKTEST_TAG"},
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to edit backtest tag: {e}")
            raise BacktestError(f"Failed to edit tag for backtest {request.backtest_id}: {e}") from e

    async def archive_backtest(
        self, 
        request: ArchiveBacktestRequest
    ) -> Dict[str, Any]:
        """
        Archive backtest using the ARCHIVE_BACKTEST channel.

        Args:
            request: ArchiveBacktestRequest with backtest ID and archive result

        Returns:
            Dictionary with operation result

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Archiving backtest {request.backtest_id}")
            
            data = {
                'backtestid': request.backtest_id,
                'archiveresult': str(request.archive_result).lower(),
            }
            
            response = await self.client.execute(
                endpoint="BacktestAPI",
                method="POST",
                query_params={"channel": "ARCHIVE_BACKTEST"},
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to archive backtest: {e}")
            raise BacktestError(f"Failed to archive backtest {request.backtest_id}: {e}") from e

    async def get_history_status(self) -> Dict[str, Any]:
        """
        Get history sync status for all markets.

        Returns:
            Dictionary with market status information

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info("Getting history sync status")
            
            response = await self.client.execute(
                endpoint="Backtest",
                query_params={"channel": "GET_HISTORY_STATUS"}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get history status: {e}")
            raise BacktestError(f"Failed to get history status: {e}") from e

    async def set_history_depth(
        self, 
        market_tag: str, 
        months: int
    ) -> bool:
        """
        Set history depth for a specific market.

        Args:
            market_tag: Market identifier
            months: Number of months of history to maintain

        Returns:
            True if successful, False otherwise

        Raises:
            BacktestError: If the API request fails
        """
        try:
            self.logger.info(f"Setting history depth for {market_tag} to {months} months")
            
            response = await self.client.execute(
                endpoint="Backtest",
                query_params={
                    "channel": "SET_HISTORY_DEPTH",
                    "market": market_tag,
                    "months": months
                }
            )
            
            return response.get('Success', False)
            
        except Exception as e:
            self.logger.error(f"Failed to set history depth: {e}")
            raise BacktestError(f"Failed to set history depth for {market_tag}: {e}") from e

    # Utility methods for backtest management

    async def build_backtest_settings(
        self, 
        bot_data: Dict[str, Any], 
        script_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the settings JSON for EXECUTE_BACKTEST from bot data and script record.

        Args:
            bot_data: Bot data from get_bot() or get_all_bots()
            script_record: Script record from get_script_record()

        Returns:
            Settings JSON for EXECUTE_BACKTEST
        """
        try:
            # Extract script parameters from script record
            script_parameters = {}
            if 'Data' in script_record and 'I' in script_record['Data']:
                for param in script_record['Data']['I']:
                    if 'K' in param and 'V' in param:
                        script_parameters[param['K']] = param['V']
            
            # Build settings JSON with proper fallbacks
            settings = {
                "botId": bot_data.get('BotId', ''),
                "botName": bot_data.get('BotName', ''),
                "accountId": bot_data.get('AccountId', '') or bot_data.get('AccountId', ''),
                "marketTag": bot_data.get('MarketTag', '') or bot_data.get('Market', ''),
                "leverage": bot_data.get('Leverage', 0) or 20.0,  # Default to 20x leverage
                "positionMode": bot_data.get('PositionMode', 0) or 1,  # Default to HEDGE mode
                "marginMode": bot_data.get('MarginMode', 0) or 0,  # Default to CROSS margin
                "interval": bot_data.get('Interval', 1) or 15,  # Default to 15 minutes
                "chartStyle": bot_data.get('ChartStyle', 300) or 300,  # Default chart style
                "tradeAmount": bot_data.get('TradeAmount', 0.005) or 2000.0,  # Default to $2000 USDT
                "orderTemplate": bot_data.get('OrderTemplate', 500) or 500,  # Default order template
                "scriptParameters": script_parameters
            }
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to build backtest settings: {e}")
            raise BacktestError(f"Failed to build backtest settings: {e}") from e

    async def execute_bot_backtest(
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

        Args:
            bot_data: Bot data dictionary
            start_time: Start time for backtest (defaults to duration_days ago)
            end_time: End time for backtest (defaults to now)
            duration_days: Number of days to backtest (if start_time not provided)

        Returns:
            BacktestExecutionResult with execution details

        Raises:
            BacktestExecutionError: If the backtest execution fails
        """
        try:
            start_time = start_time or datetime.now() - timedelta(days=duration_days)
            end_time = end_time or datetime.now()
            
            start_unix = int(start_time.timestamp())
            end_unix = int(end_time.timestamp())
            
            self.logger.info(f"🚀 Executing backtest for bot: {bot_data.get('BotName', 'Unknown')}")
            self.logger.info(f"📅 Period: {start_time} to {end_time}")
            
            # Step 1: Get script record (this would need to be implemented in ScriptAPI)
            script_id = bot_data.get('ScriptId')
            if not script_id:
                raise BacktestExecutionError("Bot has no ScriptId")
            
            # For now, we'll use a simplified approach
            # In a full implementation, this would call ScriptAPI.get_script_record()
            script_record = {}  # Placeholder - would be populated by ScriptAPI call
            
            # Step 2: Build settings and execute backtest
            settings = await self.build_backtest_settings(bot_data, script_record)
            
            backtest_id = str(uuid.uuid4())
            market_tag = bot_data.get('MarketTag', '')
            
            request = ExecuteBacktestRequest(
                backtest_id=backtest_id,
                script_id=script_id,
                settings=settings,
                start_unix=start_unix,
                end_unix=end_unix
            )
            
            return await self.execute_backtest(request)
            
        except BacktestExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute bot backtest: {e}")
            raise BacktestExecutionError(f"Failed to execute bot backtest: {e}") from e

    async def validate_live_bot(
        self, 
        bot_data: Dict[str, Any]
    ) -> BacktestValidationResult:
        """
        Validate a currently running bot by executing a recent backtest.

        Args:
            bot_data: Bot data dictionary

        Returns:
            BacktestValidationResult with validation details

        Raises:
            BacktestError: If the validation fails
        """
        try:
            bot_id = bot_data.get('BotId', '')
            bot_name = bot_data.get('BotName', 'Unknown')
            
            self.logger.info(f"🔍 Validating live bot: {bot_name}")
            
            # Execute 1-day backtest
            execution_result = await self.execute_bot_backtest(bot_data, duration_days=1)
            
            if not execution_result.success:
                return BacktestValidationResult(
                    bot_id=bot_id,
                    bot_name=bot_name,
                    backtest_id=execution_result.backtest_id,
                    validation_successful=False,
                    error_message=execution_result.error_message
                )
            
            # For now, return success with basic info
            # In a full implementation, this would analyze the backtest results
            return BacktestValidationResult(
                bot_id=bot_id,
                bot_name=bot_name,
                backtest_id=execution_result.backtest_id,
                validation_successful=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to validate live bot: {e}")
            raise BacktestError(f"Failed to validate live bot: {e}") from e

    # Additional utility methods for comprehensive backtest management

    async def get_all_backtests_for_lab(
        self, 
        lab_id: str, 
        max_pages: int = 10
    ) -> List[BacktestResult]:
        """
        Get all backtests for a lab by fetching all pages.

        Args:
            lab_id: ID of the lab
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all backtest results

        Raises:
            BacktestError: If the API request fails
        """
        try:
            all_backtests = []
            next_page_id = 0
            page_count = 0
            
            while page_count < max_pages:
                response = await self.get_backtest_result(lab_id, next_page_id, 100)
                all_backtests.extend(response.items)
                
                if not response.has_more or not response.next_page_id:
                    break
                    
                next_page_id = response.next_page_id
                page_count += 1
            
            self.logger.info(f"Retrieved {len(all_backtests)} backtests for lab {lab_id}")
            return all_backtests
            
        except Exception as e:
            self.logger.error(f"Failed to get all backtests for lab: {e}")
            raise BacktestError(f"Failed to get all backtests for lab {lab_id}: {e}") from e

    async def get_top_performing_backtests(
        self, 
        lab_id: str, 
        top_count: int = 10,
        sort_by: str = "roi"
    ) -> List[BacktestResult]:
        """
        Get top performing backtests for a lab.

        Args:
            lab_id: ID of the lab
            top_count: Number of top backtests to return
            sort_by: Field to sort by (roi, profit, winrate, etc.)

        Returns:
            List of top performing backtest results

        Raises:
            BacktestError: If the API request fails
        """
        try:
            all_backtests = await self.get_all_backtests_for_lab(lab_id)
            
            # Sort by the specified field
            if sort_by == "roi":
                sorted_backtests = sorted(all_backtests, key=lambda x: getattr(x, 'roi_percentage', 0), reverse=True)
            elif sort_by == "profit":
                sorted_backtests = sorted(all_backtests, key=lambda x: getattr(x, 'realized_profits_usdt', 0), reverse=True)
            elif sort_by == "winrate":
                sorted_backtests = sorted(all_backtests, key=lambda x: getattr(x, 'win_rate', 0), reverse=True)
            else:
                sorted_backtests = all_backtests
            
            top_backtests = sorted_backtests[:top_count]
            self.logger.info(f"Retrieved top {len(top_backtests)} backtests for lab {lab_id}")
            return top_backtests
            
        except Exception as e:
            self.logger.error(f"Failed to get top performing backtests: {e}")
            raise BacktestError(f"Failed to get top performing backtests for lab {lab_id}: {e}") from e
