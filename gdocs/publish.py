#!/usr/bin/env python3
"""
Simple CLI wrapper for Google Sheets publishing functionality.
Uses the pyHaasAPI Google Sheets service.
"""

import sys
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyHaasAPI.services.google_sheets_service import GoogleSheetsService, MultiServerDataCollector


async def publish_data(sheet_id: str, credentials_path: str = "gdocs/google_credentials.json"):
    """Publish pyHaasAPI data to Google Sheets."""
    
    server_configs = {
        "srv01": {"host": "127.0.0.1", "port": 8090},
        "srv02": {"host": "127.0.0.1", "port": 8091},
        "srv03": {"host": "127.0.0.1", "port": 8092}
    }
    
    sheets_service = GoogleSheetsService(credentials_path, sheet_id)
    data_collector = MultiServerDataCollector()
    
    print(f"Collecting data from {len(server_configs)} servers...")
    all_data = await data_collector.collect_all_server_data(server_configs)
    
    print(f"Publishing data to Google Sheets...")
    for server_name, data in all_data.items():
        await sheets_service.publish_server_data(server_name, data)
    
    await sheets_service.publish_summary(all_data)
    print(f"Done. Published data for {len(all_data)} servers")


def main():
    parser = argparse.ArgumentParser(description="Publish pyHaasAPI data to Google Sheets")
    parser.add_argument("--sheet-id", required=True, help="Google Sheets document ID")
    parser.add_argument("--credentials", default="gdocs/google_credentials.json", help="Path to Google credentials JSON")
    
    args = parser.parse_args()
    
    asyncio.run(publish_data(args.sheet_id, args.credentials))


if __name__ == "__main__":
    main()



