"""
Lab API module for pyHaasAPI v2

Handles all lab-related API operations with async support and proper error handling.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import LabError, LabNotFoundError, LabExecutionError
from ...core.logging import get_logger

# Optional model imports
try:
    from ...models.lab import LabDetails, LabRecord, LabConfig, LabSettings
except ImportError:
    LabDetails = None
    LabRecord = None
    LabConfig = None
    LabSettings = None


class LabAPI:
    """API client for lab operations"""
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("lab_api")
    
    async def create_lab(
        self,
        name: str,
        script_id: str,
        market_tag: str,
        account_id: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new lab
        
        Args:
            name: Lab name
            script_id: Script ID to use
            market_tag: Market to test on
            account_id: Account ID to use
            start_date: Start date for backtesting
            end_date: End date for backtesting
            **kwargs: Additional lab parameters
            
        Returns:
            Lab creation response
            
        Raises:
            ValidationError: If input validation fails
            APIError: If API call fails
        """
        # Validate inputs
        if not name or not script_id or not market_tag:
            raise ValidationError("Name, script_id, and market_tag are required")
        
        if start_date >= end_date:
            raise ValidationError("Start date must be before end date")
        
        # Prepare request data
        request_data = {
            "name": name,
            "script_id": script_id,
            "market_tag": market_tag,
            "account_id": account_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            **kwargs
        }
        
        try:
            response = await self.client.post("/api/labs", json=request_data)
            return response.json()
        except Exception as e:
            raise APIError(f"Failed to create lab: {e}")
    
    async def get_labs(self, status: Optional[str] = None) -> List[Any]:
        """
        Get all labs, optionally filtered by status
        
        Args:
            status: Optional status filter (not currently used)
            
        Returns:
            List of LabRecord objects
            
        Raises:
            LabError: If API call fails
        """
        try:
            self.logger.info("Getting all labs")
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            # Use LabsAPI.php endpoint with GET_LABS channel
            response = await self.client.post_json(
                endpoint="/LabsAPI.php",
                params={"channel": "GET_LABS"},
                data={
                    "userid": session.user_id,
                    "interfacekey": session.interface_key
                }
            )
            
            # Parse response - API returns {"Success": true, "Data": [...]}
            if isinstance(response, dict):
                if response.get("Success"):
                    data = response.get("Data", [])
                    if isinstance(data, list):
                        # Convert to LabRecord objects if models are available
                        if LabRecord:
                            try:
                                return [LabRecord.model_validate(item) if isinstance(item, dict) else item for item in data]
                            except Exception:
                                pass
                        # Fallback to raw dicts if models fail or unavailable
                        return data if isinstance(data, list) else []
                    return []
                else:
                    error_msg = response.get("Error", "Unknown error")
                    raise LabError(f"API returned error: {error_msg}")
            
            return []
            
        except LabError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get labs: {e}")
            raise LabError(f"Failed to get labs: {e}") from e
    
    async def get_lab_details(self, lab_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific lab
        
        Args:
            lab_id: Lab ID
            
        Returns:
            Lab details
            
        Raises:
            ValidationError: If lab_id is invalid
            APIError: If API call fails
        """
        if not lab_id:
            raise ValidationError("Lab ID is required")
        
        try:
            response = await self.client.get(f"/api/labs/{lab_id}")
            return response.json()
        except Exception as e:
            raise APIError(f"Failed to get lab details for {lab_id}: {e}")
    
    async def update_lab_details(
        self, 
        lab_id: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update lab details
        
        Args:
            lab_id: Lab ID
            updates: Dictionary of updates
            
        Returns:
            Updated lab data
            
        Raises:
            ValidationError: If inputs are invalid
            APIError: If API call fails
        """
        if not lab_id:
            raise ValidationError("Lab ID is required")
        
        if not updates:
            raise ValidationError("Updates dictionary cannot be empty")
        
        try:
            response = await self.client.put(f"/api/labs/{lab_id}", json=updates)
            return response.json()
        except Exception as e:
            raise APIError(f"Failed to update lab {lab_id}: {e}")
    
    async def delete_lab(self, lab_id: str) -> bool:
        """
        Delete a lab
        
        Args:
            lab_id: Lab ID
            
        Returns:
            True if successful
            
        Raises:
            ValidationError: If lab_id is invalid
            APIError: If API call fails
        """
        if not lab_id:
            raise ValidationError("Lab ID is required")
        
        try:
            response = await self.client.delete(f"/api/labs/{lab_id}")
            return response.status_code == 200
        except Exception as e:
            raise APIError(f"Failed to delete lab {lab_id}: {e}")
    
    async def clone_lab(
        self, 
        source_lab_id: str, 
        new_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Clone an existing lab
        
        Args:
            source_lab_id: Source lab ID
            new_name: Name for the new lab
            **kwargs: Additional parameters for the new lab
            
        Returns:
            New lab data
            
        Raises:
            ValidationError: If inputs are invalid
            APIError: If API call fails
        """
        if not source_lab_id or not new_name:
            raise ValidationError("Source lab ID and new name are required")
        
        try:
            request_data = {
                "source_lab_id": source_lab_id,
                "new_name": new_name,
                **kwargs
            }
            response = await self.client.post("/api/labs/clone", json=request_data)
            return response.json()
        except Exception as e:
            raise APIError(f"Failed to clone lab {source_lab_id}: {e}")
    
    async def change_lab_script(
        self, 
        lab_id: str, 
        script_id: str
    ) -> Dict[str, Any]:
        """
        Change the script used by a lab
        
        Args:
            lab_id: Lab ID
            script_id: New script ID
            
        Returns:
            Updated lab data
            
        Raises:
            ValidationError: If inputs are invalid
            APIError: If API call fails
        """
        if not lab_id or not script_id:
            raise ValidationError("Lab ID and script ID are required")
        
        try:
            request_data = {"script_id": script_id}
            response = await self.client.put(f"/api/labs/{lab_id}/script", json=request_data)
            return response.json()
        except Exception as e:
            raise APIError(f"Failed to change script for lab {lab_id}: {e}")
    
    async def start_lab_execution(self, lab_id: str) -> Dict[str, Any]:
        """
        Start lab execution/backtesting
        
        Args:
            lab_id: Lab ID
            
        Returns:
            Execution response
            
        Raises:
            ValidationError: If lab_id is invalid
            APIError: If API call fails
        """
        if not lab_id:
            raise ValidationError("Lab ID is required")
        
        try:
            response = await self.client.post(f"/api/labs/{lab_id}/start")
            return response.json()
        except Exception as e:
            raise APIError(f"Failed to start lab execution for {lab_id}: {e}")
    
    async def cancel_lab_execution(self, lab_id: str) -> bool:
        """
        Cancel lab execution
        
        Args:
            lab_id: Lab ID
            
        Returns:
            True if successful
            
        Raises:
            ValidationError: If lab_id is invalid
            APIError: If API call fails
        """
        if not lab_id:
            raise ValidationError("Lab ID is required")
        
        try:
            response = await self.client.post(f"/api/labs/{lab_id}/cancel")
            return response.status_code == 200
        except Exception as e:
            raise APIError(f"Failed to cancel lab execution for {lab_id}: {e}")
    
    async def get_lab_execution_status(self, lab_id: str) -> Dict[str, Any]:
        """
        Get lab execution status
        
        Args:
            lab_id: Lab ID
            
        Returns:
            Execution status
            
        Raises:
            ValidationError: If lab_id is invalid
            APIError: If API call fails
        """
        if not lab_id:
            raise ValidationError("Lab ID is required")
        
        try:
            response = await self.client.get(f"/api/labs/{lab_id}/status")
            return response.json()
        except Exception as e:
            raise APIError(f"Failed to get execution status for lab {lab_id}: {e}")
    
    async def get_complete_labs(self) -> List[Dict[str, Any]]:
        """
        Get all completed labs
        
        Returns:
            List of completed labs
            
        Raises:
            APIError: If API call fails
        """
        try:
            from ...models.enumerations import UserLabStatus
            labs = await self.get_labs()
            # Filter by completed status - handle both string and int status values
            completed_status = str(UserLabStatus.COMPLETED.value)
            return [lab for lab in labs if str(lab.get("status", "")) == completed_status]
        except Exception as e:
            raise APIError(f"Failed to get complete labs: {e}")
    
    async def get_labs_by_script(self, script_id: str) -> List[Dict[str, Any]]:
        """
        Get all labs using a specific script
        
        Args:
            script_id: Script ID
            
        Returns:
            List of labs using the script
            
        Raises:
            ValidationError: If script_id is invalid
            APIError: If API call fails
        """
        if not script_id:
            raise ValidationError("Script ID is required")
        
        try:
            labs = await self.get_labs()
            return [lab for lab in labs if lab.get("script_id") == script_id]
        except Exception as e:
            raise APIError(f"Failed to get labs for script {script_id}: {e}")
    
    async def get_labs_by_market(self, market_tag: str) -> List[Dict[str, Any]]:
        """
        Get all labs for a specific market
        
        Args:
            market_tag: Market tag
            
        Returns:
            List of labs for the market
            
        Raises:
            ValidationError: If market_tag is invalid
            APIError: If API call fails
        """
        if not market_tag:
            raise ValidationError("Market tag is required")
        
        try:
            labs = await self.get_labs()
            return [lab for lab in labs if lab.get("market_tag") == market_tag]
        except Exception as e:
            raise APIError(f"Failed to get labs for market {market_tag}: {e}")

