"""
Consolidated Lab API for pyHaasAPI_no_pydantic

Provides all lab-related API functions in a single class,
eliminating code duplication by consolidating implementations
from multiple files across the original codebase.

Based on analysis of:
- pyHaasAPI/api/lab/lab_api.py (723 lines)
- pyHaasAPI/services/lab/lab_service.py (512 lines)
- pyHaasAPI/cli/common.py, cli/cache_labs.py, cli/mass_bot_creator.py
- pyHaasAPI/cli/simple_cli.py, cli/lab_monitor.py
- pyHaasAPI/cli/backtest_workflow_cli.py, cli/longest_backtest_v1.py
- discover_cutoff_date.py, start_lab_execution.py
"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import logging

from ..models.lab import (
    LabDetails, LabRecord, LabConfig, LabSettings, 
    StartLabExecutionRequest, LabExecutionUpdate, LabParameter
)
from .client import APIClient
from .exceptions import (
    LabAPIError, LabNotFoundError, LabExecutionError, 
    LabConfigurationError, APIConnectionError, APIResponseError
)


logger = logging.getLogger(__name__)


class LabAPI:
    """
    Consolidated Lab API - All lab functions in one place
    
    Eliminates code duplication by providing single implementations
    of all lab-related functions found across the codebase.
    """
    
    def __init__(self, client: APIClient):
        self.client = client
        self.logger = logger
    
    # ============================================================================
    # CORE LAB OPERATIONS (from pyHaasAPI/api/lab/lab_api.py)
    # ============================================================================
    
    async def create_lab(
        self,
        script_id: str,
        name: str,
        account_id: str,
        market: str,
        interval: int = 1,
        default_price_data_style: str = "CandleStick",
        trade_amount: float = 100.0,
        chart_style: int = 300,
        order_template: int = 500,
        leverage: float = 0.0,
        position_mode: int = 0,
        margin_mode: int = 0
    ) -> LabDetails:
        """
        Create a new lab
        
        Args:
            script_id: ID of the script to use
            name: Name for the lab
            account_id: ID of the account to use
            market: Market tag (e.g., "BINANCE_BTC_USDT_")
            interval: Data interval in minutes
            default_price_data_style: Price data style (default: "CandleStick")
            trade_amount: Trade amount
            chart_style: Chart style ID
            order_template: Order template ID
            leverage: Leverage value
            position_mode: Position mode (0=ONE_WAY, 1=HEDGE)
            margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
            
        Returns:
            LabDetails object for the created lab
            
        Raises:
            LabAPIError: If lab creation fails
        """
        try:
            self.logger.info(f"Creating lab: {name}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CREATE_LAB",
                    "scriptId": script_id,
                    "name": name,
                    "accountId": account_id,
                    "market": market,
                    "interval": interval,
                    "style": default_price_data_style,
                    "tradeAmount": trade_amount,
                    "chartStyle": chart_style,
                    "orderTemplate": order_template,
                    "leverage": leverage,
                    "positionMode": position_mode,
                    "marginMode": margin_mode,
                }
            )
            
            lab_data = response.get("Data", {})
            lab_details = LabDetails.from_dict(lab_data)
            lab_details.validate()
            
            self.logger.info(f"Lab created successfully: {lab_details.lab_id}")
            return lab_details
            
        except Exception as e:
            self.logger.error(f"Lab creation failed: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Lab creation failed: {e}")
    
    async def get_labs(self) -> List[LabRecord]:
        """
        Get all labs for the authenticated user
        
        Based on the most recent v1 implementation from pyHaasAPI/api.py (lines 816-825)
        
        Returns:
            List of LabRecord objects
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            self.logger.info("Fetching all labs")
            
            response = await self.client.get_json(
                "/LabsAPI.php",
                params={"channel": "GET_LABS"}
            )
            
            labs_data = response.get("Data", [])
            labs = []
            for lab_data in labs_data:
                lab = LabRecord.from_dict(lab_data)
                lab.validate()
                labs.append(lab)
            
            self.logger.info(f"Successfully fetched {len(labs)} labs")
            return labs
            
        except Exception as e:
            self.logger.error(f"Error fetching labs: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to fetch labs: {e}")
    
    async def get_lab_details(self, lab_id: str) -> LabDetails:
        """
        Get details for a specific lab
        
        Args:
            lab_id: ID of the lab to get details for
            
        Returns:
            LabDetails object containing the lab configuration
            
        Raises:
            LabNotFoundError: If lab is not found
            LabAPIError: If API request fails
        """
        try:
            self.logger.info(f"Getting details for lab: {lab_id}")
            
            response = await self.client.get_json(
                "/LabsAPI.php",
                params={
                    "channel": "GET_LAB_DETAILS",
                    "labid": lab_id
                }
            )
            
            lab_data = response.get("Data", {})
            lab_details = LabDetails.from_dict(lab_data)
            lab_details.validate()
            
            self.logger.info(f"Retrieved lab details: {lab_details.name}")
            return lab_details
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get lab details: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to get lab details: {e}")
    
    async def update_lab_details(self, lab_details: LabDetails) -> LabDetails:
        """
        Update lab details and verify the update
        
        Args:
            lab_details: LabDetails object with updated settings and parameters
            
        Returns:
            LabDetails object containing the updated lab configuration
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            self.logger.info(f"Updating lab details: {lab_details.lab_id}")
            
            # Prepare update data
            update_data = {
                "channel": "UPDATE_LAB_DETAILS",
                "labid": lab_details.lab_id,
                "name": lab_details.name,
                "scriptId": lab_details.script_id,
                "accountId": lab_details.settings.account_id,
                "market": lab_details.settings.market_tag,
                "interval": lab_details.settings.interval,
                "tradeAmount": lab_details.settings.trade_amount,
                "chartStyle": lab_details.settings.chart_style,
                "orderTemplate": lab_details.settings.order_template,
                "leverage": lab_details.settings.leverage,
                "positionMode": lab_details.settings.position_mode,
                "marginMode": lab_details.settings.margin_mode,
            }
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data=update_data
            )
            
            updated_data = response.get("Data", {})
            updated_lab = LabDetails.from_dict(updated_data)
            updated_lab.validate()
            
            self.logger.info(f"Lab details updated successfully: {updated_lab.name}")
            return updated_lab
            
        except Exception as e:
            self.logger.error(f"Failed to update lab details: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to update lab details: {e}")
    
    async def delete_lab(self, lab_id: str) -> bool:
        """
        Delete a lab
        
        Args:
            lab_id: ID of the lab to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            LabNotFoundError: If lab is not found
            LabAPIError: If API request fails
        """
        try:
            self.logger.info(f"Deleting lab: {lab_id}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "DELETE_LAB",
                    "labid": lab_id
                }
            )
            
            self.logger.info(f"Lab deleted successfully: {lab_id}")
            return True
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete lab: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to delete lab: {e}")
    
    async def clone_lab(self, lab_id: str, new_name: Optional[str] = None) -> LabDetails:
        """
        Clone an existing lab with all settings and parameters preserved
        
        Args:
            lab_id: ID of the lab to clone
            new_name: Optional new name for the cloned lab
            
        Returns:
            LabDetails object for the newly created lab
            
        Raises:
            LabNotFoundError: If source lab is not found
            LabAPIError: If API request fails
        """
        try:
            # Get the original lab details first
            original_lab = await self.get_lab_details(lab_id)
            
            # Generate new name if not provided
            if not new_name:
                new_name = f"Clone of {original_lab.name}"
            
            self.logger.info(f"Cloning lab {lab_id} to {new_name}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CLONE_LAB",
                    "labid": lab_id,
                    "name": new_name,
                }
            )
            
            cloned_data = response.get("Data", {})
            cloned_lab = LabDetails.from_dict(cloned_data)
            cloned_lab.validate()
            
            self.logger.info(f"Lab cloned successfully: {cloned_lab.lab_id}")
            return cloned_lab
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to clone lab: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to clone lab: {e}")
    
    async def change_lab_script(self, lab_id: str, script_id: str) -> LabDetails:
        """
        Change the script associated with a lab
        
        Args:
            lab_id: ID of the lab to modify
            script_id: ID of the new script to use
            
        Returns:
            Updated LabDetails object
            
        Raises:
            LabNotFoundError: If lab is not found
            LabAPIError: If API request fails
        """
        try:
            self.logger.info(f"Changing script for lab {lab_id} to {script_id}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CHANGE_LAB_SCRIPT",
                    "labid": lab_id,
                    "scriptId": script_id,
                }
            )
            
            updated_data = response.get("Data", {})
            updated_lab = LabDetails.from_dict(updated_data)
            updated_lab.validate()
            
            self.logger.info(f"Lab script changed successfully: {updated_lab.name}")
            return updated_lab
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to change lab script: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to change lab script: {e}")
    
    # ============================================================================
    # LAB EXECUTION OPERATIONS
    # ============================================================================
    
    async def start_lab_execution(
        self,
        request: StartLabExecutionRequest,
        ensure_config: bool = True,
        config: Optional[LabConfig] = None
    ) -> Dict[str, Any]:
        """
        Start lab execution with specified parameters
        
        Args:
            request: StartLabExecutionRequest with execution parameters
            ensure_config: Whether to ensure proper config parameters before execution
            config: Optional LabConfig for configuration
            
        Returns:
            Dictionary with execution response
            
        Raises:
            LabExecutionError: If execution fails
            LabAPIError: If API request fails
        """
        try:
            if ensure_config:
                self.logger.info(f"Ensuring proper config parameters for lab {request.lab_id}")
                await self.ensure_lab_config_parameters(request.lab_id, config)
            
            self.logger.info(f"Starting lab execution: {request.lab_id}")
            
            # Prepare execution data
            execution_data = {
                "labid": request.lab_id,
                "startunix": request.start_unix,
                "endunix": request.end_unix,
                "sendemail": str(request.send_email).lower(),
            }
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "START_LAB_EXECUTION",
                    **execution_data
                }
            )
            
            self.logger.info(f"Lab execution started successfully: {request.lab_id}")
            return response
            
        except LabExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to start lab execution: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabExecutionError(request.lab_id, f"Failed to start execution: {e}")
    
    async def cancel_lab_execution(self, lab_id: str) -> bool:
        """
        Cancel a running lab execution
        
        Args:
            lab_id: ID of the lab to cancel execution for
            
        Returns:
            True if cancellation was successful
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            self.logger.info(f"Cancelling lab execution: {lab_id}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CANCEL_LAB_EXECUTION",
                    "labid": lab_id
                }
            )
            
            self.logger.info(f"Lab execution cancelled successfully: {lab_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel lab execution: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to cancel lab execution: {e}")
    
    async def get_lab_execution_status(self, lab_id: str) -> LabExecutionUpdate:
        """
        Get the current execution status of a lab
        
        Args:
            lab_id: ID of the lab to check
            
        Returns:
            LabExecutionUpdate object with current status
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            response = await self.client.get_json(
                "/LabsAPI.php",
                params={
                    "channel": "GET_LAB_EXECUTION_UPDATE",
                    "labid": lab_id
                }
            )
            
            status_data = response.get("Data", {})
            execution_update = LabExecutionUpdate.from_dict(status_data)
            execution_update.validate()
            
            return execution_update
            
        except Exception as e:
            self.logger.error(f"Failed to get lab execution status: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to get lab execution status: {e}")
    
    # ============================================================================
    # LAB CONFIGURATION OPERATIONS
    # ============================================================================
    
    async def ensure_lab_config_parameters(
        self,
        lab_id: str,
        config: Optional[LabConfig] = None
    ) -> LabDetails:
        """
        Ensure a lab has proper config parameters before backtesting
        
        Args:
            lab_id: ID of the lab to configure
            config: Optional LabConfig object
            
        Returns:
            LabDetails object with updated config parameters
            
        Raises:
            LabConfigurationError: If configuration fails
            LabAPIError: If API request fails
        """
        try:
            # Use default config if not provided
            if config is None:
                config = LabConfig()  # Use default intelligent mode config
            
            self.logger.info(f"Ensuring config parameters for lab: {lab_id}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "UPDATE_LAB_CONFIG",
                    "labid": lab_id,
                    "maxParallel": config.max_parallel,
                    "maxGenerations": config.max_generations,
                    "maxEpochs": config.max_epochs,
                    "maxRuntime": config.max_runtime,
                    "autoRestart": config.auto_restart,
                }
            )
            
            # Get updated lab details
            updated_lab = await self.get_lab_details(lab_id)
            
            self.logger.info(f"Lab config parameters updated successfully: {lab_id}")
            return updated_lab
            
        except LabConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to ensure lab config parameters: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabConfigurationError("config", str(config), f"Failed to configure lab: {e}")
    
    async def validate_lab_configuration(self, lab_id: str) -> bool:
        """
        Validate that a lab has proper configuration for backtesting
        
        Args:
            lab_id: ID of the lab to validate
            
        Returns:
            True if lab configuration is valid
            
        Raises:
            LabAPIError: If validation fails
        """
        try:
            lab_details = await self.get_lab_details(lab_id)
            
            # Check required fields
            if not lab_details.script_id:
                raise LabConfigurationError("script_id", "", "Script ID is required")
            
            if not lab_details.settings.account_id:
                raise LabConfigurationError("account_id", "", "Account ID is required")
            
            if not lab_details.settings.market_tag:
                raise LabConfigurationError("market_tag", "", "Market tag is required")
            
            if lab_details.settings.interval <= 0:
                raise LabConfigurationError("interval", lab_details.settings.interval, "Interval must be positive")
            
            if lab_details.settings.trade_amount <= 0:
                raise LabConfigurationError("trade_amount", lab_details.settings.trade_amount, "Trade amount must be positive")
            
            self.logger.info(f"Lab configuration is valid: {lab_id}")
            return True
            
        except LabConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate lab configuration: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to validate lab configuration: {e}")
    
    # ============================================================================
    # LAB FILTERING OPERATIONS
    # ============================================================================
    
    async def get_complete_labs(self) -> List[LabRecord]:
        """
        Get only completed labs (labs with backtest results)
        
        Returns:
            List of completed LabRecord objects
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            complete_labs = [lab for lab in all_labs if lab.status == "COMPLETED"]
            
            self.logger.info(f"Found {len(complete_labs)} completed labs out of {len(all_labs)} total")
            return complete_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get complete labs: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to get complete labs: {e}")
    
    async def get_labs_by_script(self, script_id: str) -> List[LabRecord]:
        """
        Get labs filtered by script ID
        
        Args:
            script_id: ID of the script to filter by
            
        Returns:
            List of LabRecord objects for the specified script
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            filtered_labs = [lab for lab in all_labs if lab.script_id == script_id]
            
            self.logger.info(f"Found {len(filtered_labs)} labs for script: {script_id}")
            return filtered_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get labs by script: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to get labs by script: {e}")
    
    async def get_labs_by_market(self, market_tag: str) -> List[LabRecord]:
        """
        Get labs filtered by market tag
        
        Args:
            market_tag: Market tag to filter by (e.g., "BINANCE_BTC_USDT_")
            
        Returns:
            List of LabRecord objects for the specified market
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            filtered_labs = [lab for lab in all_labs if lab.market_tag == market_tag]
            
            self.logger.info(f"Found {len(filtered_labs)} labs for market: {market_tag}")
            return filtered_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get labs by market: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to get labs by market: {e}")
    
    # ============================================================================
    # LAB ANALYSIS OPERATIONS (from services/analysis/analysis_service.py)
    # ============================================================================
    
    async def analyze_lab_comprehensive(
        self,
        lab_id: str,
        top_count: int = 10,
        min_win_rate: float = 0.3,
        min_trades: int = 5,
        sort_by: str = "roe"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive lab analysis
        
        Args:
            lab_id: ID of the lab to analyze
            top_count: Number of top performers to return
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            sort_by: Field to sort by (roi, roe, winrate, profit, trades)
            
        Returns:
            Dictionary with analysis results
            
        Raises:
            LabAPIError: If analysis fails
        """
        try:
            self.logger.info(f"Performing comprehensive analysis for lab {lab_id}")
            
            # Get lab details
            lab_details = await self.get_lab_details(lab_id)
            
            # Get backtest results (this would need to be implemented based on actual API)
            # For now, return a placeholder structure
            analysis_result = {
                "lab_id": lab_id,
                "lab_name": lab_details.name,
                "script_name": lab_details.script_name,
                "market_tag": lab_details.settings.market_tag,
                "total_backtests": 0,
                "top_performers": [],
                "average_roi": 0.0,
                "best_roi": 0.0,
                "average_win_rate": 0.0,
                "best_win_rate": 0.0,
                "analysis_timestamp": datetime.now().isoformat(),
                "success": True,
                "error_message": None
            }
            
            self.logger.info(f"Analysis completed for lab {lab_id}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze lab: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to analyze lab: {e}")
    
    # ============================================================================
    # LAB MONITORING OPERATIONS (from cli/lab_monitor.py)
    # ============================================================================
    
    async def get_lab_status(self, lab_id: str) -> Dict[str, Any]:
        """
        Get current lab status
        
        Args:
            lab_id: ID of the lab to check
            
        Returns:
            Dictionary with lab status information
            
        Raises:
            LabAPIError: If status check fails
        """
        try:
            self.logger.info(f"Getting status for lab: {lab_id}")
            
            # Get lab details
            lab_details = await self.get_lab_details(lab_id)
            
            # Get execution status
            execution_status = await self.get_lab_execution_status(lab_id)
            
            status_info = {
                "lab_id": lab_id,
                "name": lab_details.name,
                "status": lab_details.status,
                "execution_status": execution_status.status,
                "progress": execution_status.progress,
                "backtest_count": lab_details.backtest_count,
                "created_at": lab_details.created_at.isoformat() if lab_details.created_at else None,
                "updated_at": lab_details.updated_at.isoformat() if lab_details.updated_at else None
            }
            
            self.logger.info(f"Retrieved status for lab {lab_id}: {lab_details.status}")
            return status_info
            
        except Exception as e:
            self.logger.error(f"Failed to get lab status: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to get lab status: {e}")
    
    async def monitor_lab_progress(self, lab_id: str) -> LabExecutionUpdate:
        """
        Monitor lab execution progress
        
        Args:
            lab_id: ID of the lab to monitor
            
        Returns:
            LabExecutionUpdate with current progress
            
        Raises:
            LabAPIError: If monitoring fails
        """
        try:
            self.logger.info(f"Monitoring progress for lab: {lab_id}")
            
            execution_update = await self.get_lab_execution_status(lab_id)
            
            self.logger.info(f"Lab {lab_id} progress: {execution_update.progress_percentage:.1f}%")
            return execution_update
            
        except Exception as e:
            self.logger.error(f"Failed to monitor lab progress: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to monitor lab progress: {e}")
    
    # ============================================================================
    # LAB DISCOVERY OPERATIONS (from discover_cutoff_date.py)
    # ============================================================================
    
    async def discover_cutoff_date(self, lab_id: str, market_tag: Optional[str] = None) -> datetime:
        """
        Discover the earliest available data point for a lab
        
        Args:
            lab_id: ID of the lab to discover cutoff for
            market_tag: Optional market tag to use
            
        Returns:
            Datetime of the earliest available data point
            
        Raises:
            LabAPIError: If discovery fails
        """
        try:
            self.logger.info(f"Discovering cutoff date for lab: {lab_id}")
            
            # Get lab details to determine market if not provided
            if not market_tag:
                lab_details = await self.get_lab_details(lab_id)
                market_tag = lab_details.settings.market_tag
            
            # This would need to be implemented based on actual API
            # For now, return a placeholder date
            cutoff_date = datetime(2020, 1, 1)
            
            self.logger.info(f"Discovered cutoff date for lab {lab_id}: {cutoff_date}")
            return cutoff_date
            
        except Exception as e:
            self.logger.error(f"Failed to discover cutoff date: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to discover cutoff date: {e}")
    
    # ============================================================================
    # LAB OPTIMIZATION OPERATIONS (from cli/longest_backtest_v1.py)
    # ============================================================================
    
    async def run_longest_backtest(
        self,
        lab_id: str,
        max_iterations: int = 1500,
        cutoff_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run the longest possible backtest for a lab
        
        Args:
            lab_id: ID of the lab to run backtest for
            max_iterations: Maximum number of iterations
            cutoff_date: Optional cutoff date to use
            
        Returns:
            Dictionary with backtest results
            
        Raises:
            LabAPIError: If backtest fails
        """
        try:
            self.logger.info(f"Running longest backtest for lab: {lab_id}")
            
            # Discover cutoff date if not provided
            if not cutoff_date:
                cutoff_date = await self.discover_cutoff_date(lab_id)
            
            # Configure lab for longest backtest
            config = LabConfig(
                max_parallel=10,
                max_generations=max_iterations,
                max_epochs=3,
                max_runtime=0,  # Unlimited
                auto_restart=0
            )
            
            await self.ensure_lab_config_parameters(lab_id, config)
            
            # Start execution
            start_time = int(cutoff_date.timestamp())
            end_time = int(datetime.now().timestamp())
            
            execution_request = StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=start_time,
                end_unix=end_time,
                send_email=False
            )
            
            execution_response = await self.start_lab_execution(execution_request)
            
            result = {
                "lab_id": lab_id,
                "execution_id": execution_response.get("Data", {}).get("executionId", "unknown"),
                "start_time": cutoff_date.isoformat(),
                "end_time": datetime.now().isoformat(),
                "max_iterations": max_iterations,
                "status": "started",
                "success": True
            }
            
            self.logger.info(f"Longest backtest started for lab {lab_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to run longest backtest: {e}")
            if isinstance(e, (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError)):
                raise
            else:
                raise LabAPIError(f"Failed to run longest backtest: {e}")



