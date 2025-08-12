"""
Integration tests for the History Intelligence system.

Tests the complete workflow of storing, retrieving, and managing
cutoff date records in realistic scenarios.
"""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

try:
    from .history_intelligence_models import CutoffRecord, ValidationResult, CutoffResult
    from .history_database import HistoryDatabase
except ImportError:
    from history_intelligence_models import CutoffRecord, ValidationResult, CutoffResult
    from history_database import HistoryDatabase


class TestHistoryIntelligenceIntegration:
    """Integration tests for the complete history intelligence system."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "integration_test.json"
            yield HistoryDatabase(str(db_path))
    
    def test_complete_cutoff_discovery_workflow(self, temp_db):
        """Test the complete workflow of cutoff discovery and storage."""
        # Simulate a cutoff discovery process
        market_tag = "BINANCEFUTURES_BTC_USDT_PERPETUAL"
        discovered_cutoff = datetime(2020, 1, 15, 8, 0, 0)
        
        # Create discovery metadata
        discovery_metadata = {
            "tests_performed": 12,
            "discovery_time_seconds": 45.7,
            "initial_range_days": 1000,
            "final_precision_hours": 24,
            "binary_search_iterations": 8,
            "api_calls_made": 24
        }
        
        # Store the cutoff
        success = temp_db.store_cutoff(market_tag, discovered_cutoff, discovery_metadata)
        assert success is True
        
        # Retrieve and verify
        stored_record = temp_db.get_cutoff(market_tag)
        assert stored_record is not None
        assert stored_record.market_tag == market_tag
        assert stored_record.cutoff_date == discovered_cutoff
        assert stored_record.exchange == "BINANCEFUTURES"
        assert stored_record.primary_asset == "BTC"
        assert stored_record.secondary_asset == "USDT"
        assert stored_record.discovery_metadata == discovery_metadata
    
    def test_multiple_exchange_cutoffs(self, temp_db):
        """Test storing cutoffs for multiple exchanges and markets."""
        test_data = [
            ("BINANCEFUTURES_BTC_USDT_PERPETUAL", datetime(2020, 1, 15), "BINANCEFUTURES", "BTC", "USDT"),
            ("COINBASE_ETH_USD", datetime(2019, 12, 1), "COINBASE", "ETH", "USD"),
            ("KRAKEN_ADA_EUR", datetime(2020, 3, 10), "KRAKEN", "ADA", "EUR"),
            ("BINANCE_DOT_USDT", datetime(2020, 8, 19), "BINANCE", "DOT", "USDT"),
            ("BITFINEX_XRP_USD", datetime(2019, 6, 15), "BITFINEX", "XRP", "USD")
        ]
        
        # Store all cutoffs
        for market_tag, cutoff_date, exchange, primary, secondary in test_data:
            metadata = {"test_data": True, "exchange": exchange}
            success = temp_db.store_cutoff(market_tag, cutoff_date, metadata)
            assert success is True
        
        # Verify all were stored correctly
        all_cutoffs = temp_db.get_all_cutoffs()
        assert len(all_cutoffs) == len(test_data)
        
        for market_tag, cutoff_date, exchange, primary, secondary in test_data:
            record = all_cutoffs[market_tag]
            assert record.cutoff_date == cutoff_date
            assert record.exchange == exchange
            assert record.primary_asset == primary
            assert record.secondary_asset == secondary
    
    def test_validation_workflow(self, temp_db):
        """Test a realistic validation workflow."""
        # Store some cutoff data
        market_tag = "BINANCEFUTURES_ETH_USDT_PERPETUAL"
        cutoff_date = datetime(2020, 2, 10, 12, 0, 0)
        
        temp_db.store_cutoff(market_tag, cutoff_date, {"precision_hours": 24})
        
        # Simulate validation scenarios
        test_scenarios = [
            # Valid period (after cutoff)
            (datetime(2020, 3, 1), datetime(2020, 4, 1), True, None),
            # Invalid period (before cutoff)
            (datetime(2020, 1, 1), datetime(2020, 3, 1), False, datetime(2020, 2, 11)),
            # Partially invalid period
            (datetime(2020, 2, 5), datetime(2020, 3, 1), False, datetime(2020, 2, 11)),
        ]
        
        for start_date, end_date, expected_valid, expected_adjustment in test_scenarios:
            # Get stored cutoff
            stored_record = temp_db.get_cutoff(market_tag)
            assert stored_record is not None
            
            # Simulate validation logic
            if start_date < stored_record.cutoff_date:
                # Invalid - need adjustment
                adjusted_start = stored_record.cutoff_date + timedelta(days=1)
                validation_result = ValidationResult(
                    is_valid=False,
                    adjusted_start_date=adjusted_start,
                    cutoff_date=stored_record.cutoff_date,
                    message=f"Start date adjusted from {start_date} to {adjusted_start}",
                    requires_sync=True
                )
            else:
                # Valid period
                validation_result = ValidationResult(
                    is_valid=True,
                    message="Period is valid for backtesting"
                )
            
            assert validation_result.is_valid == expected_valid
            if expected_adjustment:
                assert validation_result.adjusted_start_date is not None
                assert validation_result.adjusted_start_date >= stored_record.cutoff_date
    
    def test_export_import_workflow(self, temp_db):
        """Test the complete export/import workflow."""
        # Store some test data
        test_markets = [
            ("BINANCE_BTC_USDT", datetime(2020, 1, 1)),
            ("COINBASE_ETH_USD", datetime(2019, 12, 15)),
            ("KRAKEN_ADA_EUR", datetime(2020, 3, 20))
        ]
        
        for market_tag, cutoff_date in test_markets:
            temp_db.store_cutoff(market_tag, cutoff_date, {"exported": True})
        
        # Export data
        json_export = temp_db.export_cutoffs("json")
        csv_export = temp_db.export_cutoffs("csv")
        
        # Verify exports contain data
        assert len(json_export) > 100  # Should be substantial JSON
        assert len(csv_export.split('\n')) == len(test_markets) + 1  # Header + data rows
        
        # Create new database and import
        with tempfile.TemporaryDirectory() as temp_dir:
            import_db_path = Path(temp_dir) / "import_test.json"
            import_db = HistoryDatabase(str(import_db_path))
            
            # Import JSON data
            import_success = import_db.import_cutoffs(json_export, "json")
            assert import_success is True
            
            # Verify imported data
            imported_cutoffs = import_db.get_all_cutoffs()
            assert len(imported_cutoffs) == len(test_markets)
            
            for market_tag, cutoff_date in test_markets:
                imported_record = imported_cutoffs[market_tag]
                assert imported_record.cutoff_date == cutoff_date
                assert imported_record.discovery_metadata.get("exported") is True
    
    def test_database_statistics_and_validation(self, temp_db):
        """Test database statistics and validation in a realistic scenario."""
        # Store diverse data
        exchanges = ["BINANCE", "COINBASE", "KRAKEN", "BITFINEX"]
        assets = ["BTC", "ETH", "ADA", "DOT", "XRP"]
        
        stored_count = 0
        for i, exchange in enumerate(exchanges):
            for j, asset in enumerate(assets[:3]):  # Limit combinations
                market_tag = f"{exchange}_{asset}_USDT"
                cutoff_date = datetime(2020, 1, 1) + timedelta(days=i*10 + j*5)
                
                success = temp_db.store_cutoff(market_tag, cutoff_date, {
                    "exchange": exchange,
                    "asset": asset,
                    "test_id": stored_count
                })
                
                if success:
                    stored_count += 1
        
        # Get statistics
        stats = temp_db.get_database_stats()
        
        assert stats["total_cutoffs"] == stored_count
        assert len(stats["exchanges"]) == len(exchanges)
        assert stats["file_size_bytes"] > 0
        assert stats["backup_count"] >= 0
        
        # Validate database integrity
        validation = temp_db.validate_database_integrity()
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
    
    def test_realistic_market_tag_parsing(self, temp_db):
        """Test parsing of realistic market tag formats."""
        realistic_market_tags = [
            ("BINANCEFUTURES_BTC_USDT_PERPETUAL", "BINANCEFUTURES", "BTC", "USDT"),
            ("COINBASE_ETH_USD", "COINBASE", "ETH", "USD"),
            ("KRAKEN_ADA_EUR", "KRAKEN", "ADA", "EUR"),
            ("BITFINEX_XRP_USD", "BITFINEX", "XRP", "USD"),
            ("BINANCE_DOT_USDT", "BINANCE", "DOT", "USDT"),
            ("HUOBI_LINK_USDT", "HUOBI", "LINK", "USDT"),
            ("OKEX_UNI_USDT", "OKEX", "UNI", "USDT"),
        ]
        
        for market_tag, expected_exchange, expected_primary, expected_secondary in realistic_market_tags:
            cutoff_date = datetime(2020, 1, 1)
            
            success = temp_db.store_cutoff(market_tag, cutoff_date, {"test": "parsing"})
            assert success is True
            
            record = temp_db.get_cutoff(market_tag)
            assert record is not None
            assert record.exchange == expected_exchange
            assert record.primary_asset == expected_primary
            assert record.secondary_asset == expected_secondary
    
    def test_performance_with_many_records(self, temp_db):
        """Test performance with a larger number of records."""
        import time
        
        # Store many records
        num_records = 100
        start_time = time.time()
        
        for i in range(num_records):
            market_tag = f"PERF_TEST_{i:03d}_BTC_USDT"
            cutoff_date = datetime(2020, 1, 1) + timedelta(days=i)
            
            success = temp_db.store_cutoff(market_tag, cutoff_date, {
                "performance_test": True,
                "record_id": i
            })
            assert success is True
        
        store_time = time.time() - start_time
        
        # Retrieve all records
        start_time = time.time()
        all_cutoffs = temp_db.get_all_cutoffs()
        retrieve_time = time.time() - start_time
        
        assert len(all_cutoffs) == num_records
        
        # Performance should be reasonable (less than 1 second each)
        assert store_time < 10.0, f"Storing {num_records} records took {store_time:.2f}s"
        assert retrieve_time < 1.0, f"Retrieving {num_records} records took {retrieve_time:.2f}s"
        
        # Test individual retrieval performance
        start_time = time.time()
        for i in range(0, num_records, 10):  # Sample every 10th record
            market_tag = f"PERF_TEST_{i:03d}_BTC_USDT"
            record = temp_db.get_cutoff(market_tag)
            assert record is not None
        
        individual_retrieve_time = time.time() - start_time
        assert individual_retrieve_time < 1.0, f"Individual retrievals took {individual_retrieve_time:.2f}s"