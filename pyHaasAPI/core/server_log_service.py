"""
Server Log Service for pyHaasAPI v2

Provides functionality to view and export Haas Trade Server (HTS) logs
from remote servers using SSH and screen sesssion monitoring.
"""

import re
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from .server_manager import ServerManager
from .logging import get_logger
from ..config.settings import settings

logger = get_logger("server_log_service")

class ServerLogService:
    """
    Service for managing and fetching logs from remote Haas servers.
    """

    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager

    async def list_screen_sessions(self, server_name: str, sudo_user: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List active screen sessions for a specific user on a remote server.
        
        Args:
            server_name: The name of the server (srv01, srv02, etc.)
            sudo_user: The user who owns the screen sessions (defaults to settings.sudo_user).
            
        Returns:
            A list of dictionaries containing session info (id, name, date, status).
        """
        user = sudo_user or settings.sudo_user
        # Command to list screens
        cmd = f"sudo -n -u {user} screen -ls"
        
        success, stdout, stderr = await self.server_manager.execute_remote_command(server_name, cmd)
        
        if not success:
            # If sudo needs a password, this might fail with -n
            # We'll need to handle password-based sudo in ServerManager if necessary
            logger.error(f"Failed to list screen sessions on {server_name}: {stderr}")
            return []

        sessions = []
        # Example output line: 7519.pts-2.srv03	(01.11.2025 18:25:02)	(Detached)
        # Regex to match session ID and details
        pattern = re.compile(r'^\s*(\d+)\.([^\s]+)\s+\(([^)]+)\)\s+\(([^)]+)\)')
        
        for line in stdout.splitlines():
            match = pattern.match(line)
            if match:
                sessions.append({
                    "id": match.group(1),
                    "name": match.group(2),
                    "date": match.group(3),
                    "status": match.group(4)
                })
        
        return sessions

    async def get_screen_snapshot(self, server_name: str, session_id: str, sudo_user: Optional[str] = None) -> str:
        """
        Get a snapshot of the current screen session output.
        Uses 'screen -X hardcopy' to capture the screen buffer.
        """
        user = sudo_user or settings.sudo_user
        tmp_file = f"/tmp/screen_shot_{session_id}.txt"
        
        # 1. Clear any old snapshot
        await self.server_manager.execute_remote_command(server_name, f"rm -f {tmp_file}")
        
        # 2. Tell screen to write its buffer to a file
        # We need to run this as the sudo_user
        copy_cmd = f"sudo -n -u {user} screen -S {session_id} -X hardcopy {tmp_file}"
        success, _, stderr = await self.server_manager.execute_remote_command(server_name, copy_cmd)
        
        if not success:
            logger.error(f"Failed to capture screen snapshot for {session_id} on {server_name}: {stderr}")
            return f"Error capturing screen: {stderr}"

        # 3. Read the file content
        read_cmd = f"sudo -n -u {user} cat {tmp_file}"
        success, stdout, stderr = await self.server_manager.execute_remote_command(server_name, read_cmd)
        
        # 4. Cleanup
        await self.server_manager.execute_remote_command(server_name, f"rm -f {tmp_file}")

        if success:
            return stdout
        return f"Error reading snapshot: {stderr}"

    async def export_filtered_logs(
        self, 
        server_name: str, 
        output_path: str, 
        sudo_user: Optional[str] = None,
        levels: List[str] = ["ERROR", "WARNING"]
    ) -> Tuple[bool, str]:
        """
        Find HTS log files on the remote server, filter for specific levels,
        and download the result to a local file.
        """
        user = sudo_user or settings.sudo_user
        # Heuristic to find HTS log files: look for logs with HTS or Haas in content
        find_cmd = f"sudo -n -u {user} find /home/{user} -name '*.log' -type f | xargs grep -lE 'Haas|HTS|TradeServer'"
        success, stdout, stderr = await self.server_manager.execute_remote_command(server_name, find_cmd)
        
        if not success or not stdout.strip():
            return False, f"Could not find HTS log files on {server_name}: {stderr or 'None found'}"

        log_files = stdout.splitlines()
        
        # Create a combined filter command
        # Example levels filter: "ERROR|WARNING"
        filter_pattern = "|".join(levels)
        
        local_logs = []
        for log_file in log_files:
            filter_cmd = f"sudo -n -u {user} grep -E '{filter_pattern}' {log_file} | tail -n 1000"
            success, stdout, _ = await self.server_manager.execute_remote_command(server_name, filter_cmd)
            if success and stdout.strip():
                local_logs.append(f"--- LOGS FROM {log_file} ---")
                local_logs.append(stdout)
                local_logs.append("\n")

        if not local_logs:
            return True, f"No logs matching {levels} found on {server_name}."

        try:
            with open(output_path, "w") as f:
                f.write("\n".join(local_logs))
            return True, f"Logs exported to {output_path}"
        except Exception as e:
            return False, f"Failed to write local log file: {e}"
