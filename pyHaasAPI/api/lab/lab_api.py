"""
Lab API module for pyHaasAPI v2

Provides comprehensive lab management functionality including creation,
configuration, execution, and monitoring of trading labs.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import LabError, LabNotFoundError, LabExecutionError, LabConfigurationError
from ...core.logging import get_logger
from ...models.lab import LabDetails, LabRecord, LabConfig, StartLabExecutionRequest, LabExecutionUpdate


class LabAPI:
    """
    Lab API for managing trading labs
    
    Provides comprehensive lab management functionality including creation,
    configuration, execution, and monitoring of trading labs.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("lab_api")
    
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
            LabError: If lab creation fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
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
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Lab creation failed")
                raise LabError(message=f"Failed to create lab: {error_msg}")
            
            lab_data = response.get("Data", {})
            lab_details = LabDetails(**lab_data)
            
            self.logger.info(f"Lab created successfully: {lab_details.lab_id}")
            return lab_details
            
        except Exception as e:
            self.logger.error(f"Lab creation failed: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Lab creation failed: {e}")
    
    async def get_labs(self) -> List[LabRecord]:
        """
        Get all labs for the authenticated user
        
        Based on the most recent v1 implementation from pyHaasAPI/api.py (lines 816-825)
        
        Returns:
            List of LabRecord objects
            
        Raises:
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info("Fetching all labs")
            
            # Use the correct client method
            response = await self.client.get_json("Labs", params={"channel": "GET_LABS"})
            
            # Parse response data
            if not response.get("Success", False):
                raise LabError(message=f"API request failed: {response.get('Error', 'Unknown error')}")
            
            # Convert to LabRecord objects
            labs_data = response.get("Data", [])
            response = [LabRecord(**lab_data) for lab_data in labs_data]
            
            self.logger.info(f"Successfully fetched {len(response)} labs")
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching labs: {e}")
            raise LabError(message=f"Failed to fetch labs: {e}")
    
    async def get_lab_details(self, lab_id: str) -> LabDetails:
        """
        Get details for a specific lab
        
        Args:
            lab_id: ID of the lab to get details for
            
        Returns:
            LabDetails object containing the lab configuration
            
        Raises:
            LabNotFoundError: If lab is not found
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Getting details for lab: {lab_id}")
            
            response = await self.client.get_json(
                "/LabsAPI.php",
                params={
                    "channel": "GET_LAB_DETAILS",
                    "labid": lab_id
                }
            )
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to get lab details")
                if "not found" in error_msg.lower():
                    raise LabNotFoundError(lab_id)
                else:
                    raise LabError(message=f"Failed to get lab details: {error_msg}")
            
            lab_data = response.get("Data", {})
            lab_details = LabDetails(**lab_data)
            
            self.logger.info(f"Retrieved lab details: {lab_details.name}")
            return lab_details
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get lab details: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get lab details: {e}")
    
    async def update_lab_details(self, lab_details: LabDetails) -> LabDetails:
        """
        Update lab details and verify the update
        
        Args:
            lab_details: LabDetails object with updated settings and parameters
            
        Returns:
            LabDetails object containing the updated lab configuration
            
        Raises:
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
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
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to update lab details")
                raise LabError(message=f"Failed to update lab details: {error_msg}")
            
            updated_data = response.get("Data", {})
            updated_lab = LabDetails(**updated_data)
            
            self.logger.info(f"Lab details updated successfully: {updated_lab.name}")
            return updated_lab
            
        except Exception as e:
            self.logger.error(f"Failed to update lab details: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to update lab details: {e}")
    
    async def delete_lab(self, lab_id: str) -> bool:
        """
        Delete a lab
        
        Args:
            lab_id: ID of the lab to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            LabNotFoundError: If lab is not found
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Deleting lab: {lab_id}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "DELETE_LAB",
                    "labid": lab_id
                }
            )
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to delete lab")
                if "not found" in error_msg.lower():
                    raise LabNotFoundError(lab_id)
                else:
                    raise LabError(message=f"Failed to delete lab: {error_msg}")
            
            self.logger.info(f"Lab deleted successfully: {lab_id}")
            return True
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete lab: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to delete lab: {e}")
    
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
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
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
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to clone lab")
                raise LabError(message=f"Failed to clone lab: {error_msg}")
            
            cloned_data = response.get("Data", {})
            cloned_lab = LabDetails(**cloned_data)
            
            self.logger.info(f"Lab cloned successfully: {cloned_lab.lab_id}")
            return cloned_lab
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to clone lab: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to clone lab: {e}")
    
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
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Changing script for lab {lab_id} to {script_id}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CHANGE_LAB_SCRIPT",
                    "labid": lab_id,
                    "scriptId": script_id,
                }
            )
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to change lab script")
                if "not found" in error_msg.lower():
                    raise LabNotFoundError(lab_id)
                else:
                    raise LabError(message=f"Failed to change lab script: {error_msg}")
            
            updated_data = response.get("Data", {})
            updated_lab = LabDetails(**updated_data)
            
            self.logger.info(f"Lab script changed successfully: {updated_lab.name}")
            return updated_lab
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to change lab script: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to change lab script: {e}")
    
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
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
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
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to start lab execution")
                raise LabExecutionError(request.lab_id, error_msg)
            
            self.logger.info(f"Lab execution started successfully: {request.lab_id}")
            return response
            
        except LabExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to start lab execution: {e}")
            if isinstance(e, LabError):
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
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Cancelling lab execution: {lab_id}")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CANCEL_LAB_EXECUTION",
                    "labid": lab_id
                }
            )
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to cancel lab execution")
                raise LabError(message=f"Failed to cancel lab execution: {error_msg}")
            
            self.logger.info(f"Lab execution cancelled successfully: {lab_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel lab execution: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to cancel lab execution: {e}")
    
    async def get_lab_execution_status(self, lab_id: str) -> LabExecutionUpdate:
        """
        Get the current execution status of a lab
        
        Args:
            lab_id: ID of the lab to check
            
        Returns:
            LabExecutionUpdate object with current status
            
        Raises:
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            response = await self.client.get_json(
                "/LabsAPI.php",
                params={
                    "channel": "GET_LAB_EXECUTION_UPDATE",
                    "labid": lab_id
                }
            )
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to get lab execution status")
                raise LabError(message=f"Failed to get lab execution status: {error_msg}")
            
            status_data = response.get("Data", {})
            execution_update = LabExecutionUpdate(**status_data)
            
            return execution_update
            
        except Exception as e:
            self.logger.error(f"Failed to get lab execution status: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get lab execution status: {e}")
    
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
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
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
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Failed to update lab config")
                raise LabConfigurationError("max_parallel", config.max_parallel, error_msg)
            
            # Get updated lab details
            updated_lab = await self.get_lab_details(lab_id)
            
            self.logger.info(f"Lab config parameters updated successfully: {lab_id}")
            return updated_lab
            
        except LabConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to ensure lab config parameters: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabConfigurationError("config", str(config), f"Failed to configure lab: {e}")
    
    async def get_complete_labs(self) -> List[LabRecord]:
        """
        Get only completed labs (labs with backtest results)
        
        Returns:
            List of completed LabRecord objects
            
        Raises:
            LabError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            complete_labs = [lab for lab in all_labs if lab.status == "COMPLETED"]
            
            self.logger.info(f"Found {len(complete_labs)} completed labs out of {len(all_labs)} total")
            return complete_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get complete labs: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get complete labs: {e}")
    
    async def get_labs_by_script(self, script_id: str) -> List[LabRecord]:
        """
        Get labs filtered by script ID
        
        Args:
            script_id: ID of the script to filter by
            
        Returns:
            List of LabRecord objects for the specified script
            
        Raises:
            LabError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            filtered_labs = [lab for lab in all_labs if lab.script_id == script_id]
            
            self.logger.info(f"Found {len(filtered_labs)} labs for script: {script_id}")
            return filtered_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get labs by script: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get labs by script: {e}")
    
    async def get_labs_by_market(self, market_tag: str) -> List[LabRecord]:
        """
        Get labs filtered by market tag
        
        Args:
            market_tag: Market tag to filter by (e.g., "BINANCE_BTC_USDT_")
            
        Returns:
            List of LabRecord objects for the specified market
            
        Raises:
            LabError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            filtered_labs = [lab for lab in all_labs if lab.market_tag == market_tag]
            
            self.logger.info(f"Found {len(filtered_labs)} labs for market: {market_tag}")
            return filtered_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get labs by market: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get labs by market: {e}")
    
    async def validate_lab_configuration(self, lab_id: str) -> bool:
        """
        Validate that a lab has proper configuration for backtesting
        
        Args:
            lab_id: ID of the lab to validate
            
        Returns:
            True if lab configuration is valid
            
        Raises:
            LabError: If validation fails
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
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to validate lab configuration: {e}")
