"""
Script API module for pyHaasAPI v2

Provides comprehensive script management functionality including script creation,
editing, testing, and management of HaasScript trading scripts.
"""

import asyncio
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import ScriptError, ScriptNotFoundError, ScriptCreationError, ScriptConfigurationError
from ...core.logging import get_logger
from ...core.field_utils import (
    safe_get_field, safe_get_nested_field, safe_get_dict_field,
    safe_get_success_flag, log_field_mapping_issues
)
from ...models.script import ScriptRecord, ScriptItem, ScriptParameter


class ScriptAPI:
    """
    Script API for managing HaasScript trading scripts
    
    Provides comprehensive script management functionality including script creation,
    editing, testing, and management of HaasScript trading scripts.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("script_api")
    
    async def get_all_scripts(self) -> List[ScriptItem]:
        """
        Get all scripts for the authenticated user
        
        Based on the most recent v1 implementation from pyHaasAPI/api.py (lines 432-446)
        
        Returns:
            List of ScriptItem objects
            
        Raises:
            ScriptError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving all scripts")
            
            # Use canonical endpoint; resolver in client will normalize
            try:
                response = await self.client.get_json(
                    endpoint="HaasScript",
                    params={
                        "channel": "GET_ALL_SCRIPT_ITEMS",
                        "userid": self.auth_manager.user_id,
                        "interfacekey": self.auth_manager.interface_key,
                    }
                )
            except Exception:
                response = await self.client.get_json(
                    endpoint="HaasScript",
                    params={
                        "channel": "GET_ALL_SCRIPT_ITEMS",
                        "userid": self.auth_manager.user_id,
                        "interfacekey": self.auth_manager.interface_key,
                    }
                )
            
            # Parse response data using safe field access
            success = safe_get_success_flag(response)
            if not success:
                error_msg = safe_get_field(response, 'Error', 'Unknown error')
                raise ScriptError(message=f"API request failed: {error_msg}")
            
            # Convert to ScriptItem objects with safe mapping
            scripts_data = safe_get_field(response, 'Data', [])
            mapped_scripts: List[ScriptItem] = []
            for item in scripts_data:
                try:
                    # Safe field access for script ID
                    script_id = ""
                    for key in ['ScriptId', 'ID', 'Id', 'script_id']:
                        if hasattr(item, key):
                            script_id = str(getattr(item, key, ""))
                            break
                        elif isinstance(item, dict) and key in item:
                            script_id = str(item[key])
                            break
                    
                    # Safe field access for name
                    name = ""
                    for key in ['Name', 'N', 'name']:
                        if hasattr(item, key):
                            name = str(getattr(item, key, ""))
                            break
                        elif isinstance(item, dict) and key in item:
                            name = str(item[key])
                            break
                    
                    # Safe field access for description
                    description = ""
                    for key in ['Description', 'D', 'description']:
                        if hasattr(item, key):
                            description = str(getattr(item, key, ""))
                            break
                        elif isinstance(item, dict) and key in item:
                            description = str(item[key])
                            break
                    
                    # Safe field access for source code
                    source_code = ""
                    for key in ['Source', 'SourceCode', 'source_code']:
                        if hasattr(item, key):
                            source_code = str(getattr(item, key, ""))
                            break
                        elif isinstance(item, dict) and key in item:
                            source_code = str(item[key])
                            break
                    
                    # Safe field access for version
                    version = ""
                    for key in ['Version', 'version']:
                        if hasattr(item, key):
                            version = str(getattr(item, key, ""))
                            break
                        elif isinstance(item, dict) and key in item:
                            version = str(item[key])
                            break
                    
                    # Safe field access for author
                    author = ""
                    for key in ['Author', 'author']:
                        if hasattr(item, key):
                            author = str(getattr(item, key, ""))
                            break
                        elif isinstance(item, dict) and key in item:
                            author = str(item[key])
                            break
                    
                    # Safe field access for dependencies
                    dependencies = []
                    for key in ['Dependencies', 'dependencies']:
                        if hasattr(item, key):
                            dependencies = getattr(item, key, [])
                            break
                        elif isinstance(item, dict) and key in item:
                            dependencies = item[key]
                            break
                    
                    # Safe field access for parameters
                    parameters = []
                    for key in ['Parameters', 'parameters']:
                        if hasattr(item, key):
                            parameters = getattr(item, key, [])
                            break
                        elif isinstance(item, dict) and key in item:
                            parameters = item[key]
                            break
                    
                    # Safe field access for is_published
                    is_published = False
                    for key in ['IsPublished', 'is_published']:
                        if hasattr(item, key):
                            is_published = bool(getattr(item, key, False))
                            break
                        elif isinstance(item, dict) and key in item:
                            is_published = bool(item[key])
                            break
                    
                    mapped_scripts.append(
                        ScriptItem(
                            script_id=script_id,
                            name=name,
                            description=description,
                            source_code=source_code,
                            version=version,
                            author=author,
                            dependencies=dependencies,
                            parameters=parameters,
                            created_at=datetime.now().isoformat(),
                            updated_at=datetime.now().isoformat(),
                            is_published=is_published,
                        )
                    )
                except Exception as map_err:
                    self.logger.warning(f"Failed to map script item, skipping: {map_err}")
                    continue
            response = mapped_scripts
            
            self.logger.debug(f"Retrieved {len(response)} scripts")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve scripts: {e}")
            raise ScriptError(f"Failed to retrieve scripts: {e}") from e
    
    async def get_script_record(self, script_id: str) -> ScriptRecord:
        """
        Get the full script record including compile logs and all fields
        
        Args:
            script_id: ID of the script to retrieve
            
        Returns:
            ScriptRecord object with complete script information
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving script record: {script_id}")
            
            response = await self.client.get_json(
                endpoint="HaasScript",
                params={
                    "channel": "GET_SCRIPT_RECORD",
                    "scriptid": script_id,
                    "interfacekey": self.auth_manager.interface_key,
                    "userid": self.auth_manager.user_id,
                }
            )
            
            script_record = ScriptRecord.model_validate(response)
            self.logger.debug(f"Retrieved script record: {script_id}")
            return script_record
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve script record {script_id}: {e}")
            raise ScriptNotFoundError(f"Script not found: {script_id}") from e
    
    async def get_script_item(self, script_id: str) -> ScriptItem:
        """
        Get detailed information about a specific script
        
        Args:
            script_id: ID of the script to get details for
            
        Returns:
            ScriptItem object with complete script information
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving script item: {script_id}")
            
            response = await self.client.get_json(
                endpoint="HaasScript",
                params={
                    "channel": "GET_SCRIPT_ITEM",
                    "scriptid": script_id,
                    "interfacekey": self.auth_manager.interface_key,
                    "userid": self.auth_manager.user_id,
                }
            )
            
            script_item = ScriptItem.model_validate(response)
            self.logger.debug(f"Retrieved script item: {script_id}")
            return script_item
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve script item {script_id}: {e}")
            raise ScriptNotFoundError(f"Script not found: {script_id}") from e
    
    async def get_scripts_by_name(
        self,
        name_pattern: str,
        case_sensitive: bool = False
    ) -> List[ScriptItem]:
        """
        Get scripts that match the given name pattern
        
        Args:
            name_pattern: String pattern to match in script names
            case_sensitive: Whether to perform case-sensitive matching (default: False)
            
        Returns:
            List of ScriptItem objects matching the pattern
            
        Raises:
            ScriptError: If retrieval fails
        """
        try:
            self.logger.debug(f"Searching scripts by name pattern: {name_pattern}")
            
            all_scripts = await self.get_all_scripts()
            
            if case_sensitive:
                matching_scripts = [
                    script for script in all_scripts 
                    if name_pattern in script.script_name
                ]
            else:
                matching_scripts = [
                    script for script in all_scripts 
                    if name_pattern.lower() in script.script_name.lower()
                ]
            
            self.logger.debug(f"Found {len(matching_scripts)} scripts matching pattern: {name_pattern}")
            return matching_scripts
            
        except Exception as e:
            self.logger.error(f"Failed to search scripts by name pattern {name_pattern}: {e}")
            raise ScriptError(f"Failed to search scripts by name: {e}") from e
    
    async def add_script(
        self,
        script_name: str,
        script_content: str,
        description: str = "",
        script_type: int = 0
    ) -> ScriptItem:
        """
        Upload a new script to the HaasOnline server
        
        Args:
            script_name: Name for the new script
            script_content: The script source code
            description: Description of the script (optional)
            script_type: Type of script (default: 0 for HaasScript)
            
        Returns:
            ScriptItem object for the newly created script
            
        Raises:
            ScriptCreationError: If script creation fails
        """
        try:
            self.logger.info(f"Creating new script: {script_name}")
            
            response = await self.client.post_json(
                endpoint="HaasScript",
                data={
                    "channel": "ADD_SCRIPT",
                    "name": script_name,
                    "script": script_content,
                    "description": description,
                    "type": script_type,
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            script_item = ScriptItem.model_validate(response)
            self.logger.info(f"Successfully created script: {script_item.script_id}")
            return script_item
            
        except Exception as e:
            self.logger.error(f"Failed to create script {script_name}: {e}")
            raise ScriptCreationError(f"Failed to create script: {e}") from e
    
    async def edit_script(
        self,
        script_id: str,
        script_name: Optional[str] = None,
        script_content: Optional[str] = None,
        description: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> ScriptItem:
        """
        Edit an existing script
        
        Args:
            script_id: ID of the script to edit
            script_name: New name for the script (optional)
            script_content: New script content (optional)
            description: Description for the script (optional)
            settings: Optional dictionary of script settings to update
            
        Returns:
            Updated ScriptItem object
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If editing fails
        """
        try:
            self.logger.info(f"Editing script: {script_id}")
            
            params = {
                "channel": "EDIT_SCRIPT",
                "scriptid": script_id,
                "description": description,
            }
            
            if script_name is not None:
                params["name"] = script_name
            if script_content is not None:
                params["script"] = script_content
            if settings is not None:
                params["settings"] = json.dumps(settings)
            
            params["userid"] = self.auth_manager.user_id
            params["interfacekey"] = self.auth_manager.interface_key
            response = await self.client.post_json(
                endpoint="HaasScript",
                data=params
            )
            
            # Handle different response types
            if isinstance(response, dict) and "script_id" in response:
                script_item = ScriptItem.model_validate(response)
            else:
                # If response is not a full script item, fetch the updated script
                script_item = await self.get_script_item(script_id)
            
            self.logger.info(f"Successfully edited script: {script_id}")
            return script_item
            
        except Exception as e:
            self.logger.error(f"Failed to edit script {script_id}: {e}")
            raise ScriptError(f"Failed to edit script: {e}") from e
    
    async def edit_script_sourcecode(
        self,
        script_id: str,
        sourcecode: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the source code and settings of a script
        
        Args:
            script_id: ID of the script to edit
            sourcecode: The new source code for the script
            settings: Dictionary containing script settings
            
        Returns:
            Dictionary containing the result of the compilation
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If editing fails
        """
        try:
            self.logger.info(f"Editing script source code: {script_id}")
            
            response = await self.client.post_json(
                endpoint="HaasScript",
                data={
                    "channel": "EDIT_SCRIPT_SOURCECODE",
                    "scriptid": script_id,
                    "sourcecode": sourcecode,
                    "settings": json.dumps(settings),
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            self.logger.info(f"Successfully edited script source code: {script_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to edit script source code {script_id}: {e}")
            raise ScriptError(f"Failed to edit script source code: {e}") from e
    
    async def delete_script(self, script_id: str) -> bool:
        """
        Delete a script
        
        Args:
            script_id: ID of the script to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If deletion fails
        """
        try:
            self.logger.info(f"Deleting script: {script_id}")
            
            response = await self.client.post_json(
                endpoint="HaasScript",
                data={
                    "channel": "DELETE_SCRIPT",
                    "scriptid": script_id,
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            success = response if isinstance(response, bool) else safe_get_field(response, "success", False)
            if success:
                self.logger.info(f"Successfully deleted script: {script_id}")
            else:
                self.logger.warning(f"Failed to delete script: {script_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete script {script_id}: {e}")
            raise ScriptError(f"Failed to delete script: {e}") from e
    
    async def publish_script(self, script_id: str) -> bool:
        """
        Publish a script to make it public
        
        Args:
            script_id: ID of the script to publish
            
        Returns:
            True if publication was successful
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If publication fails
        """
        try:
            self.logger.info(f"Publishing script: {script_id}")
            
            response = await self.client.post_json(
                endpoint="HaasScript",
                data={
                    "channel": "PUBLISH_SCRIPT",
                    "scriptid": script_id,
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            success = response if isinstance(response, bool) else safe_get_field(response, "success", False)
            if success:
                self.logger.info(f"Successfully published script: {script_id}")
            else:
                self.logger.warning(f"Failed to publish script: {script_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to publish script {script_id}: {e}")
            raise ScriptError(f"Failed to publish script: {e}") from e
    
    async def get_haasscript_commands(self) -> List[Dict[str, Any]]:
        """
        Get all available HaasScript commands and their descriptions
        
        Returns:
            List of dictionaries containing all HaasScript commands and their details
            
        Raises:
            ScriptError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving HaasScript commands")
            
            response = await self.client.get_json(
                endpoint="HaasScript",
                params={
                    "channel": "GET_COMMANDS",
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            self.logger.debug(f"Retrieved {len(response)} HaasScript commands")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve HaasScript commands: {e}")
            raise ScriptError(f"Failed to retrieve HaasScript commands: {e}") from e
    
    async def execute_debug_test(
        self,
        script_id: str,
        script_type: int,
        settings: Dict[str, Any]
    ) -> List[str]:
        """
        Execute a debug test for a given script
        
        Args:
            script_id: ID of the script to debug
            script_type: Type of the script (e.g., 0 for trading script)
            settings: Dictionary containing the bot's settings for the debug test
            
        Returns:
            List of strings representing the debug log output
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If debug test fails
        """
        try:
            self.logger.info(f"Executing debug test for script: {script_id}")
            
            response = await self.client.post_json(
                endpoint="Backtest",
                data={
                    "channel": "EXECUTE_DEBUGTEST",
                    "scriptid": script_id,
                    "scripttype": script_type,
                    "settings": json.dumps(settings),
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            self.logger.info(f"Successfully executed debug test for script: {script_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to execute debug test for script {script_id}: {e}")
            raise ScriptError(f"Failed to execute debug test: {e}") from e
    
    async def execute_quicktest(
        self,
        backtest_id: str,
        script_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a quicktest for a given script
        
        Args:
            backtest_id: ID of the backtest
            script_id: ID of the script to quicktest
            settings: Dictionary containing the bot's settings for the quicktest
            
        Returns:
            Dictionary containing the result of the quicktest
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If quicktest fails
        """
        try:
            self.logger.info(f"Executing quicktest for script: {script_id}")
            
            response = await self.client.post_json(
                endpoint="Backtest",
                data={
                    "channel": "EXECUTE_QUICKTEST",
                    "backtestid": backtest_id,
                    "scriptid": script_id,
                    "settings": json.dumps(settings),
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            self.logger.info(f"Successfully executed quicktest for script: {script_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to execute quicktest for script {script_id}: {e}")
            raise ScriptError(f"Failed to execute quicktest: {e}") from e
    
    # Additional utility methods
    
    async def get_scripts_by_type(self, script_type: int) -> List[ScriptItem]:
        """
        Get scripts filtered by type
        
        Args:
            script_type: Script type to filter by
            
        Returns:
            List of ScriptItem objects with the specified type
        """
        all_scripts = await self.get_all_scripts()
        return [script for script in all_scripts if script.script_type == script_type]
    
    async def get_public_scripts(self) -> List[ScriptItem]:
        """
        Get all public scripts
        
        Returns:
            List of public ScriptItem objects
        """
        all_scripts = await self.get_all_scripts()
        return [script for script in all_scripts if getattr(script, 'is_public', False)]
    
    async def get_script_parameters(self, script_id: str) -> List[ScriptParameter]:
        """
        Get parameters for a specific script
        
        Args:
            script_id: ID of the script
            
        Returns:
            List of ScriptParameter objects
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If retrieval fails
        """
        try:
            script_item = await self.get_script_item(script_id)
            return getattr(script_item, 'parameters', [])
            
        except Exception as e:
            self.logger.error(f"Failed to get parameters for script {script_id}: {e}")
            raise ScriptError(f"Failed to get script parameters: {e}") from e
    
    async def validate_script(self, script_content: str) -> Dict[str, Any]:
        """
        Validate script syntax and structure
        
        Args:
            script_content: The script source code to validate
            
        Returns:
            Dictionary containing validation results
            
        Raises:
            ScriptError: If validation fails
        """
        try:
            self.logger.debug("Validating script syntax")
            
            # This would typically involve calling a validation endpoint
            # For now, we'll do basic validation
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Basic validation checks
            if not script_content.strip():
                validation_result["valid"] = False
                validation_result["errors"].append("Script content is empty")
            
            if "function main()" not in script_content:
                validation_result["warnings"].append("Script may be missing main() function")
            
            self.logger.debug(f"Script validation completed: {validation_result['valid']}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate script: {e}")
            raise ScriptError(f"Failed to validate script: {e}") from e
    
    async def get_script_statistics(self, script_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a script
        
        Args:
            script_id: ID of the script
            
        Returns:
            Dictionary containing script statistics
            
        Raises:
            ScriptNotFoundError: If script is not found
            ScriptError: If retrieval fails
        """
        try:
            self.logger.debug(f"Getting statistics for script: {script_id}")
            
            # This would typically involve calling a statistics endpoint
            # For now, we'll return basic information
            script_item = await self.get_script_item(script_id)
            
            statistics = {
                "script_id": script_id,
                "script_name": script_item.script_name,
                "created_at": getattr(script_item, 'created_at', None),
                "last_modified": getattr(script_item, 'last_modified', None),
                "usage_count": getattr(script_item, 'usage_count', 0),
                "is_public": getattr(script_item, 'is_public', False),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.debug(f"Retrieved statistics for script: {script_id}")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics for script {script_id}: {e}")
            raise ScriptError(f"Failed to get script statistics: {e}") from e
