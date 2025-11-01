"""
Script to delete labs by name pattern from srv03

Usage:
    python -m pyHaasAPI.cli.delete_labs_by_pattern
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.core.logging import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("delete_labs_by_pattern")


async def delete_labs_by_pattern(pattern: str, server_name: str = "srv03") -> int:
    """
    Delete labs matching the name pattern from the specified server.
    
    Args:
        pattern: Name pattern to match (e.g., "0- YATS bot - ETH- 01.12.2023")
        server_name: Server name (default: srv03)
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Ensure SSH tunnel to srv03
        logger.info(f"Connecting to {server_name}...")
        settings = Settings()
        server_manager = ServerManager(settings)
        
        # Connect to srv03
        connected = await server_manager.connect_server(server_name)
        if not connected:
            logger.error(f"Failed to connect to {server_name}")
            return 1
        
        # Preflight check
        preflight_ok = await server_manager.preflight_check()
        if not preflight_ok:
            logger.error("Tunnel preflight failed")
            return 1
        
        logger.info(f"Successfully connected to {server_name}")
        
        # Get credentials
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            logger.error("API_EMAIL and API_PASSWORD environment variables are required")
            return 1
        
        # Create API client and authenticate
        api_config = APIConfig(
            timeout=30.0,
            email=email,
            password=password
        )
        
        client = AsyncHaasClient(api_config)
        auth_manager = AuthenticationManager(client, api_config)
        
        logger.info("Authenticating...")
        await auth_manager.authenticate()
        logger.info("Authentication successful")
        
        # Create LabAPI
        lab_api = LabAPI(client, auth_manager)
        
        # Get all labs
        logger.info("Fetching all labs...")
        labs = await lab_api.get_labs()
        logger.info(f"Found {len(labs)} total labs")
        
        # Filter labs by name pattern
        # Match labs that start with "0-" and contain the pattern
        matching_labs = [
            lab for lab in labs 
            if lab.name.strip().startswith("0-") and pattern in lab.name
        ]
        logger.info(f"Found {len(matching_labs)} labs matching pattern (starting with '0-' and containing '{pattern}')")
        
        if not matching_labs:
            logger.info("No labs found matching the pattern")
            return 0
        
        # Display labs to be deleted
        logger.info("\nLabs to be deleted:")
        for lab in matching_labs:
            logger.info(f"  - {lab.name} (ID: {lab.lab_id})")
        
        # Delete labs
        deleted_count = 0
        failed_count = 0
        
        logger.info(f"\nDeleting {len(matching_labs)} labs...")
        for lab in matching_labs:
            try:
                logger.info(f"Deleting lab: {lab.name} ({lab.lab_id})...")
                success = await lab_api.delete_lab(lab.lab_id)
                if success:
                    logger.info(f"  ✅ Successfully deleted: {lab.name}")
                    deleted_count += 1
                else:
                    logger.error(f"  ❌ Failed to delete: {lab.name}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"  ❌ Error deleting {lab.name}: {e}")
                failed_count += 1
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Deletion Summary:")
        logger.info(f"  Total matching labs: {len(matching_labs)}")
        logger.info(f"  Successfully deleted: {deleted_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"{'='*60}")
        
        # Disconnect from server
        await server_manager.disconnect_server(server_name)
        
        # Cleanup client session
        if client:
            await client.close()
        
        return 0 if failed_count == 0 else 1
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def main():
    """Main entry point"""
    # Pattern to match labs - all labs starting with "0- YATS bot - ETH- 01.12.2023"
    # Note: Lab names may have variable spacing, so we'll match any lab that contains this substring
    pattern = "YATS bot - ETH- 01.12.2023"
    
    exit_code = await delete_labs_by_pattern(pattern, server_name="srv03")
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())

