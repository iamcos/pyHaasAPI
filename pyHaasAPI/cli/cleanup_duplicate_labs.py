"""
CLI for cleaning up duplicate lab clones

This script identifies duplicate labs (same source lab, same coin) and removes
duplicates, keeping only the most recent one per coin.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .base import BaseCLI
from ..core.server_manager import ServerManager
from ..config.settings import Settings
from ..config.api_config import APIConfig
from ..exceptions import LabError
from ..core.logging import get_logger

logger = get_logger("cleanup_duplicate_labs")


class CleanupDuplicateLabsCLI(BaseCLI):
    """
    CLI for cleaning up duplicate lab clones
    
    Identifies labs with matching patterns and removes duplicates,
    keeping only the most recent one per coin.
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        self.server_manager: Optional[ServerManager] = None
    
    async def connect_to_serv3(self) -> bool:
        """Connect to serv3 using ServerManager"""
        try:
            self.logger.info("Connecting to serv3...")
            
            settings = Settings()
            self.server_manager = ServerManager(settings)
            
            if not await self.server_manager.ensure_srv03_tunnel():
                self.logger.error("Failed to establish SSH tunnel to serv3")
                return False
            
            if not await self.server_manager.preflight_check():
                self.logger.error("Preflight check failed - tunnel not available")
                return False
            
            server_config = self.server_manager.get_active_server_config()
            if not server_config:
                self.logger.error("No active server configuration")
                return False
            
            self.logger.info(f"Connected to serv3 on port {server_config.local_ports[0]}")
            
            from ..core.client import AsyncHaasClient
            from ..core.auth import AuthenticationManager
            
            api_config = APIConfig(
                host="127.0.0.1",
                port=server_config.local_ports[0],
                timeout=self.config.timeout
            )
            
            self.client = AsyncHaasClient(api_config)
            self.auth_manager = AuthenticationManager(self.client, api_config)
            
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                self.logger.error("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            await self.auth_manager.authenticate(email, password)
            await self._initialize_api_modules()
            
            self.logger.info("Successfully connected and authenticated to serv3")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to serv3: {e}")
            return False
    
    def extract_coin_from_name(self, lab_name: str) -> Optional[str]:
        """Extract coin symbol from lab name"""
        # Pattern: "0-  YATS bot - ETH- 01.12.2023 - XRP Clone"
        # Extract the coin before "Clone"
        match = re.search(r'-\s+([A-Z]+)\s+Clone$', lab_name)
        if match:
            return match.group(1)
        return None
    
    async def find_duplicate_labs(self, source_lab_pattern: str = "YATS bot") -> Dict[str, List[Any]]:
        """
        Find duplicate labs grouped by coin
        
        Args:
            source_lab_pattern: Pattern to match in lab names (e.g., "YATS bot")
            
        Returns:
            Dictionary mapping coin symbols to lists of lab records
        """
        try:
            self.logger.info("Fetching all labs...")
            labs = await self.lab_api.get_labs()
            
            # Group labs by coin
            labs_by_coin: Dict[str, List[Any]] = defaultdict(list)
            
            for lab in labs:
                lab_name = getattr(lab, 'name', '') or getattr(lab, 'lab_name', '')
                
                # Check if it matches our pattern and is a clone
                if source_lab_pattern in lab_name and "Clone" in lab_name:
                    coin = self.extract_coin_from_name(lab_name)
                    if coin:
                        # Get created timestamp
                        created_at = getattr(lab, 'created_at', None)
                        if created_at:
                            labs_by_coin[coin].append({
                                'lab': lab,
                                'lab_id': lab.lab_id,
                                'name': lab_name,
                                'created_at': created_at,
                                'timestamp': created_at.timestamp() if hasattr(created_at, 'timestamp') else 0
                            })
            
            # Sort by timestamp (newest first) for each coin
            for coin in labs_by_coin:
                labs_by_coin[coin].sort(key=lambda x: x['timestamp'], reverse=True)
            
            return labs_by_coin
            
        except Exception as e:
            self.logger.error(f"Failed to find duplicate labs: {e}")
            raise
    
    async def cleanup_duplicates(
        self,
        source_lab_pattern: str = "YATS bot",
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up duplicate labs, keeping only the most recent one per coin
        
        Args:
            source_lab_pattern: Pattern to match in lab names
            dry_run: If True, only report what would be deleted without actually deleting
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            labs_by_coin = await self.find_duplicate_labs(source_lab_pattern)
            
            results = {
                'coins_processed': 0,
                'labs_kept': 0,
                'labs_deleted': 0,
                'labs_to_delete': 0,
                'deletions': [],
                'errors': []
            }
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info("DUPLICATE LAB CLEANUP")
            self.logger.info(f"{'='*60}")
            
            for coin, coin_labs in sorted(labs_by_coin.items()):
                if len(coin_labs) <= 1:
                    continue  # No duplicates for this coin
                
                results['coins_processed'] += 1
                
                # Keep the most recent (first in sorted list)
                keep_lab = coin_labs[0]
                duplicates = coin_labs[1:]
                
                results['labs_kept'] += 1
                results['labs_to_delete'] += len(duplicates)
                
                self.logger.info(f"\n{coin}:")
                self.logger.info(f"  ✅ Keeping: {keep_lab['name']} ({keep_lab['lab_id'][:8]})")
                
                for dup in duplicates:
                    self.logger.info(f"  {'[DRY RUN] ' if dry_run else ''}🗑️  Deleting: {dup['name']} ({dup['lab_id'][:8]})")
                    
                    if not dry_run:
                        try:
                            success = await self.lab_api.delete_lab(dup['lab_id'])
                            if success:
                                results['labs_deleted'] += 1
                                results['deletions'].append({
                                    'coin': coin,
                                    'lab_id': dup['lab_id'],
                                    'name': dup['name']
                                })
                                self.logger.info(f"      ✅ Deleted successfully")
                            else:
                                results['errors'].append({
                                    'coin': coin,
                                    'lab_id': dup['lab_id'],
                                    'error': 'Delete returned False'
                                })
                                self.logger.warning(f"      ⚠️  Delete returned False")
                        except Exception as e:
                            results['errors'].append({
                                'coin': coin,
                                'lab_id': dup['lab_id'],
                                'error': str(e)
                            })
                            self.logger.error(f"      ❌ Failed to delete: {e}")
            
            # Summary
            self.logger.info(f"\n{'='*60}")
            self.logger.info("SUMMARY")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"Coins processed: {results['coins_processed']}")
            self.logger.info(f"Labs kept: {results['labs_kept']}")
            
            if dry_run:
                self.logger.info(f"Labs that would be deleted: {results['labs_to_delete']}")
                self.logger.info("\n⚠️  DRY RUN MODE - No labs were actually deleted")
                self.logger.info("Run with --execute to actually delete duplicates")
            else:
                self.logger.info(f"Labs deleted: {results['labs_deleted']}")
                if results['errors']:
                    self.logger.warning(f"Errors: {len(results['errors'])}")
            
            self.logger.info(f"{'='*60}\n")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup duplicates: {e}")
            raise
    
    async def run(
        self,
        source_lab_pattern: str = "YATS bot",
        dry_run: bool = True
    ) -> int:
        """
        Main execution method
        
        Args:
            source_lab_pattern: Pattern to match in lab names
            dry_run: If True, only report without deleting
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if not await self.connect_to_serv3():
                self.logger.error("Failed to connect to serv3")
                return 1
            
            results = await self.cleanup_duplicates(source_lab_pattern, dry_run)
            
            if results['errors'] and not dry_run:
                return 2  # Partial failure
            return 0
            
        except Exception as e:
            self.logger.error(f"Fatal error during cleanup: {e}")
            return 1
        finally:
            if self.server_manager:
                await self.server_manager.shutdown()


async def main(args: List[str]) -> int:
    """Entry point for the CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up duplicate lab clones on serv3"
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default="YATS bot",
        help='Pattern to match in lab names (default: "YATS bot")'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete duplicates (default: dry run)'
    )
    
    parsed_args = parser.parse_args(args)
    
    cli = CleanupDuplicateLabsCLI()
    return await cli.run(
        source_lab_pattern=parsed_args.pattern,
        dry_run=not parsed_args.execute
    )


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(exit_code)

