"""
Log API module for pyHaasAPI v2

Provides programmatic access to remote HTS logs and screen sessions.
Embedded into the core API structure, disabled by default via config.
"""

from typing import List, Dict, Optional, Tuple, Any
from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...core.server_log_service import ServerLogService
from ...core.server_manager import ServerManager
from ...core.logging import get_logger

class LogAPI:
    """
    API for managing and viewing remote HTS logs.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("log_api")
        
        # LogAPI relies on ServerManager which is usually held by the application/CLI
        # For direct API usage, we initialize a standalone ServerManager if not provided
        from ...config.settings import settings
        self.server_manager = ServerManager(settings)
        self.log_service = ServerLogService(self.server_manager)

    async def get_sessions(self, server_name: str, sudo_user: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get active screen sessions on a remote server.
        """
        if not self.client.config.enable_remote_logging:
            self.logger.warning("Remote logging is disabled in config.")
            return []
        return await self.log_service.list_screen_sessions(server_name, sudo_user)

    async def get_session_snapshot(self, server_name: str, session_id: str, sudo_user: Optional[str] = None) -> str:
        """
        Get a snapshot of a specific screen session's output.
        """
        if not self.client.config.enable_remote_logging:
            return "Remote logging is disabled in config."
        return await self.log_service.get_screen_snapshot(server_name, session_id, sudo_user)

    async def export_logs(
        self, 
        server_name: str, 
        output_path: str, 
        sudo_user: Optional[str] = None,
        levels: List[str] = ["ERROR", "WARNING"]
    ) -> Tuple[bool, str]:
        """
        Export filtered remote logs to a local file.
        """
        if not self.client.config.enable_remote_logging:
            return False, "Remote logging is disabled in config."
        return await self.log_service.export_filtered_logs(server_name, output_path, sudo_user, levels)
