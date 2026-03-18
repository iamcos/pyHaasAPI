"""
Log CLI for pyHaasAPI v2
"""

import os
import sys
import asyncio
from typing import List, Optional
from .base import BaseCLI
from ..core.server_log_service import ServerLogService
from ..core.server_manager import ServerManager
from ..config.settings import settings

class LogCLI(BaseCLI):
    """
    CLI for managing and viewing remote HTS logs.
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        self.server_manager = ServerManager(settings)
        self.log_service = ServerLogService(self.server_manager)

    async def connect(self) -> bool:
        """
        Override connect to bypass the strict tunnel preflight check,
        as logging operations use direct SSH commands.
        """
        # We don't need full API connection for log operations
        self.logger.info("LogCLI: Bypassing API tunnel preflight check.")
        return True

    async def run(self, args: List[str]) -> int:
        if not args:
            self.print_help()
            return 0

        action = args[0]
        remaining = args[1:]

        if action == 'list':
            return await self.list_sessions(remaining)
        elif action == 'export':
            return await self.export_logs(remaining)
        else:
            print(f"Unknown log action: {action}")
            self.print_help()
            return 1

    async def list_sessions(self, args: List[str]) -> int:
        import argparse
        parser = argparse.ArgumentParser(prog='pyhaas log list')
        parser.add_argument('--server', required=True, help='Server name (srv01, srv02, srv03)')
        parser.add_argument('--user', help='Sudo user (defaults to settings.sudo_user)')
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 1

        print(f"Fetching screen sessions from {parsed_args.server}...")
        sessions = await self.log_service.list_screen_sessions(parsed_args.server, parsed_args.user)
        
        if not sessions:
            print(f"No active screen sessions found for {parsed_args.user} on {parsed_args.server}.")
            return 0

        print(f"\nActive screen sessions for {parsed_args.user}:")
        print(f"{'ID':<10} {'NAME':<20} {'DATE':<25} {'STATUS':<15}")
        print("-" * 70)
        for s in sessions:
            print(f"{s['id']:<10} {s['name']:<20} {s['date']:<25} {s['status']:<15}")
        
        return 0

    async def export_logs(self, args: List[str]) -> int:
        import argparse
        parser = argparse.ArgumentParser(prog='pyhaas log export')
        parser.add_argument('--server', required=True, help='Server name')
        parser.add_argument('--output', required=True, help='Local output file path')
        parser.add_argument('--user', help='Sudo user (defaults to settings.sudo_user)')
        parser.add_argument('--levels', default='ERROR,WARNING', help='Comma-separated log levels')
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 1

        levels = [lvl.strip().upper() for lvl in parsed_args.levels.split(',')]
        print(f"Exporting filtered logs from {parsed_args.server} to {parsed_args.output}...")
        
        success, msg = await self.log_service.export_filtered_logs(
            parsed_args.server, 
            parsed_args.output, 
            parsed_args.user, 
            levels
        )
        
        if success:
            print(f"✅ {msg}")
            return 0
        else:
            print(f"❌ {msg}")
            return 1

    def print_help(self):
        print("Usage: pyhaas log <action> [options]")
        print("\nActions:")
        print("  list    List active screen sessions")
        print("  export  Export and filter logs to a local file")
        print("\nExamples:")
        print("  pyhaas log list --server srv03")
        print("  pyhaas log export --server srv03 --output srv03_errors.log --levels ERROR")
