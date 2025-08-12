#!/usr/bin/env python3
"""
Demo script for the History Intelligence system.

This script demonstrates the core functionality of the data models
and database operations for the backtesting history intelligence system.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from history_intelligence_models import (
    CutoffRecord, ValidationResult, CutoffResult, HistoryResult, SyncStatusResult
)
from history_database import HistoryDatabase


def demo_data_models():
    """Demonstrate the data models functionality."""
    print("=== Data Models Demo ===")
    
    # Create a cutoff record
    cutoff_record = CutoffRecord(
        market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
        cutoff_date=datetime(2020, 1, 15, 8, 0, 0),
        discovery_date=datetime.now(),
        precision_hours=24,
        exchange="BINANCEFUTURES",
        primary_asset="BTC",
        secondary_asset="USDT",
        discovery_metadata={
            "tests_performed": 12,
            "discovery_time_seconds": 45.7,
            "initial_range_days": 1000,
            "final_precision_hours": 24
        }
    )
    
    print(f"Created cutoff record for {cutoff_record.market_tag}")
    print(f"Cutoff date: {cutoff_record.cutoff_date}")
    print(f"Exchange: {cutoff_record.exchange}")
    print(f"Assets: {cutoff_record.primary_asset}/{cutoff_record.secondary_asset}")
    
    # Test serialization
    record_dict = cutoff_record.to_dict()
    restored_record = CutoffRecord.from_dict(record_dict)
    
    print(f"Serialization test: {'PASSED' if restored_record.market_tag == cutoff_record.market_tag else 'FAILED'}")
    
    # Create validation result
    validation_result = ValidationResult(
        is_valid=False,
        adjusted_start_date=datetime(2020, 1, 16),
        cutoff_date=datetime(2020, 1, 15),
        message="Start date adjusted to available history",
        requires_sync=True
    )
    
    print(f"Validation result: {'Valid' if validation_result.is_valid else 'Invalid'}")
    print(f"Message: {validation_result.message}")
    
    # Create cutoff discovery result
    cutoff_result = CutoffResult(
        success=True,
        cutoff_date=datetime(2020, 1, 15),
        precision_achieved=24,
        discovery_time_seconds=45.7,
        tests_performed=12
    )
    
    print(f"Discovery result: {'Success' if cutoff_result.success else 'Failed'}")
    print(f"Tests performed: {cutoff_result.tests_performed}")
    print(f"Discovery time: {cutoff_result.discovery_time_seconds:.1f}s")
    
    print()


def demo_database_operations():
    """Demonstrate database operations."""
    print("=== Database Operations Demo ===")
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "demo_history_cutoffs.json"
        db = HistoryDatabase(str(db_path))
        
        print(f"Created database at: {db_path}")
        
        # Store some cutoff records
        markets_data = [
            ("BINANCEFUTURES_BTC_USDT_PERPETUAL", datetime(2020, 1, 15), {"tests": 12, "time": 45.7}),
            ("BINANCEFUTURES_ETH_USDT_PERPETUAL", datetime(2020, 2, 10), {"tests": 8, "time": 32.1}),
            ("COINBASE_BTC_USD", datetime(2019, 12, 1), {"tests": 15, "time": 67.3}),
            ("BINANCE_ADA_USDT", datetime(2020, 3, 5), {"tests": 10, "time": 28.9})
        ]
        
        print(f"Storing {len(markets_data)} cutoff records...")
        
        for market_tag, cutoff_date, metadata in markets_data:
            success = db.store_cutoff(market_tag, cutoff_date, metadata)
            print(f"  {market_tag}: {'✓' if success else '✗'}")
        
        # Retrieve records
        print("\nRetrieving stored records:")
        all_cutoffs = db.get_all_cutoffs()
        
        for market_tag, record in all_cutoffs.items():
            print(f"  {market_tag}: {record.cutoff_date} ({record.exchange})")
        
        # Test specific retrieval
        btc_record = db.get_cutoff("BINANCEFUTURES_BTC_USDT_PERPETUAL")
        if btc_record:
            print(f"\nBTC record details:")
            print(f"  Cutoff: {btc_record.cutoff_date}")
            print(f"  Discovery: {btc_record.discovery_date}")
            print(f"  Precision: {btc_record.precision_hours}h")
            print(f"  Metadata: {btc_record.discovery_metadata}")
        
        # Test export functionality
        print("\nTesting export functionality:")
        json_export = db.export_cutoffs("json")
        csv_export = db.export_cutoffs("csv")
        
        print(f"  JSON export: {len(json_export)} characters")
        print(f"  CSV export: {len(csv_export.split(chr(10)))} lines")
        
        # Database statistics
        stats = db.get_database_stats()
        print(f"\nDatabase statistics:")
        print(f"  Total cutoffs: {stats['total_cutoffs']}")
        print(f"  File size: {stats['file_size_bytes']} bytes")
        print(f"  Exchanges: {list(stats['exchanges'].keys())}")
        print(f"  Backup count: {stats['backup_count']}")
        
        # Validation
        validation = db.validate_database_integrity()
        print(f"  Database valid: {'✓' if validation['is_valid'] else '✗'}")
        
        print()


def demo_concurrent_operations():
    """Demonstrate concurrent database operations."""
    print("=== Concurrent Operations Demo ===")
    
    import threading
    import time
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "concurrent_demo.json"
        db = HistoryDatabase(str(db_path))
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                market_tag = f"CONCURRENT_TEST_{worker_id}"
                cutoff_date = datetime(2020, 1, 1) + timedelta(days=worker_id)
                metadata = {"worker_id": worker_id, "timestamp": time.time()}
                
                # Simulate some processing time
                time.sleep(0.1)
                
                success = db.store_cutoff(market_tag, cutoff_date, metadata)
                results.append((worker_id, success))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create and start multiple threads
        threads = []
        num_workers = 5
        
        print(f"Starting {num_workers} concurrent workers...")
        
        for i in range(num_workers):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print(f"Completed: {len(results)} successful, {len(errors)} errors")
        
        # Verify final state
        final_cutoffs = db.get_all_cutoffs()
        print(f"Final database contains {len(final_cutoffs)} records")
        
        for market_tag, record in final_cutoffs.items():
            worker_id = record.discovery_metadata.get("worker_id", "unknown")
            print(f"  {market_tag}: Worker {worker_id}")
        
        print()


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("=== Error Handling Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "error_demo.json"
        db = HistoryDatabase(str(db_path))
        
        # Test non-existent record retrieval
        missing_record = db.get_cutoff("NONEXISTENT_MARKET")
        print(f"Non-existent record: {'None' if missing_record is None else 'Found'}")
        
        # Test immutable cutoff behavior
        market_tag = "IMMUTABLE_TEST"
        original_date = datetime(2020, 1, 1)
        new_date = datetime(2020, 2, 1)
        
        # Store original
        success1 = db.store_cutoff(market_tag, original_date, {"version": 1})
        print(f"Original store: {'✓' if success1 else '✗'}")
        
        # Try to overwrite
        success2 = db.store_cutoff(market_tag, new_date, {"version": 2})
        print(f"Overwrite attempt: {'✓' if success2 else '✗'}")
        
        # Verify original is preserved
        stored_record = db.get_cutoff(market_tag)
        if stored_record:
            preserved = stored_record.cutoff_date == original_date
            print(f"Original preserved: {'✓' if preserved else '✗'}")
            print(f"  Stored date: {stored_record.cutoff_date}")
            print(f"  Metadata version: {stored_record.discovery_metadata.get('version')}")
        
        print()


def main():
    """Run all demos."""
    print("History Intelligence System Demo")
    print("=" * 40)
    print()
    
    demo_data_models()
    demo_database_operations()
    demo_concurrent_operations()
    demo_error_handling()
    
    print("Demo completed successfully! ✓")


if __name__ == "__main__":
    main()