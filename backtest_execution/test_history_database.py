"""
Unit tests for history database operations.

Tests the HistoryDatabase class including concurrent access, backup functionality,
and data integrity operations.
"""

import pytest
import json
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open

from backtest_execution.history_database import HistoryDatabase
from backtest_execution.history_intelligence_models import CutoffRecord


class TestHistoryDatabase:
    """Test cases for HistoryDatabase class."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test_history_cutoffs.json"
    
    @pytest.fixture
    def sample_cutoff_data(self):
        """Sample cutoff data for testing."""
        return {
            "tests_performed": 10,
            "discovery_time_seconds": 45.2,
            "initial_range_days": 1000,
            "final_precision_hours": 24
        }
    
    def test_database_initialization(self, temp_db_path):
        """Test database initialization creates proper structure."""
        db = HistoryDatabase(str(temp_db_path))
        
        # Check that database file was created
        assert temp_db_path.exists()
        
        # Check that backup directory was created
        backup_dir = temp_db_path.parent / "backups"
        assert backup_dir.exists()
        
        # Check initial database structure
        with open(temp_db_path, 'r') as f:
            data = json.load(f)
        
        assert "version" in data
        assert "created" in data
        assert "last_updated" in data
        assert "cutoffs" in data
        assert data["cutoffs"] == {}
    
    def test_store_cutoff_success(self, temp_db_path, sample_cutoff_data):
        """Test successful cutoff storage."""
        db = HistoryDatabase(str(temp_db_path))
        
        cutoff_date = datetime(2020, 1, 1, 12, 0, 0)
        market_tag = "BINANCEFUTURES_BTC_USDT_PERPETUAL"
        
        result = db.store_cutoff(market_tag, cutoff_date, sample_cutoff_data)
        
        assert result is True
        
        # Verify data was stored
        stored_record = db.get_cutoff(market_tag)
        assert stored_record is not None
        assert stored_record.market_tag == market_tag
        assert stored_record.cutoff_date == cutoff_date
        assert stored_record.exchange == "BINANCEFUTURES"
        assert stored_record.primary_asset == "BTC"
        assert stored_record.secondary_asset == "USDT"
        assert stored_record.discovery_metadata == sample_cutoff_data
    
    def test_store_cutoff_immutable(self, temp_db_path, sample_cutoff_data):
        """Test that cutoff dates are immutable (cannot be overwritten)."""
        db = HistoryDatabase(str(temp_db_path))
        
        market_tag = "TEST_BTC_USDT"
        original_date = datetime(2020, 1, 1)
        new_date = datetime(2020, 2, 1)
        
        # Store original cutoff
        result1 = db.store_cutoff(market_tag, original_date, sample_cutoff_data)
        assert result1 is True
        
        # Try to store different cutoff for same market
        result2 = db.store_cutoff(market_tag, new_date, {"different": "data"})
        assert result2 is True  # Should succeed but not overwrite
        
        # Verify original data is preserved
        stored_record = db.get_cutoff(market_tag)
        assert stored_record.cutoff_date == original_date
        assert stored_record.discovery_metadata == sample_cutoff_data
    
    def test_get_cutoff_not_found(self, temp_db_path):
        """Test retrieving non-existent cutoff."""
        db = HistoryDatabase(str(temp_db_path))
        
        result = db.get_cutoff("NONEXISTENT_MARKET")
        assert result is None
    
    def test_get_all_cutoffs(self, temp_db_path, sample_cutoff_data):
        """Test retrieving all cutoffs."""
        db = HistoryDatabase(str(temp_db_path))
        
        # Store multiple cutoffs
        markets = [
            ("BINANCE_BTC_USDT", datetime(2020, 1, 1)),
            ("BINANCE_ETH_USDT", datetime(2020, 2, 1)),
            ("BINANCE_ADA_USDT", datetime(2020, 3, 1))
        ]
        
        for market_tag, cutoff_date in markets:
            db.store_cutoff(market_tag, cutoff_date, sample_cutoff_data)
        
        all_cutoffs = db.get_all_cutoffs()
        
        assert len(all_cutoffs) == 3
        for market_tag, cutoff_date in markets:
            assert market_tag in all_cutoffs
            assert all_cutoffs[market_tag].cutoff_date == cutoff_date
    
    def test_export_cutoffs_json(self, temp_db_path, sample_cutoff_data):
        """Test exporting cutoffs in JSON format."""
        db = HistoryDatabase(str(temp_db_path))
        
        market_tag = "TEST_BTC_USDT"
        cutoff_date = datetime(2020, 1, 1)
        db.store_cutoff(market_tag, cutoff_date, sample_cutoff_data)
        
        exported_data = db.export_cutoffs("json")
        
        # Verify it's valid JSON
        parsed_data = json.loads(exported_data)
        assert "cutoffs" in parsed_data
        assert market_tag in parsed_data["cutoffs"]
    
    def test_export_cutoffs_csv(self, temp_db_path, sample_cutoff_data):
        """Test exporting cutoffs in CSV format."""
        db = HistoryDatabase(str(temp_db_path))
        
        market_tag = "TEST_BTC_USDT"
        cutoff_date = datetime(2020, 1, 1)
        db.store_cutoff(market_tag, cutoff_date, sample_cutoff_data)
        
        exported_data = db.export_cutoffs("csv")
        
        lines = exported_data.strip().split('\n')
        assert len(lines) == 2  # Header + 1 data line
        assert lines[0] == "market_tag,cutoff_date,discovery_date,precision_hours,exchange,primary_asset,secondary_asset"
        assert lines[1].startswith(f"{market_tag},{cutoff_date.isoformat()}")
    
    def test_import_cutoffs_json(self, temp_db_path):
        """Test importing cutoffs from JSON format."""
        db = HistoryDatabase(str(temp_db_path))
        
        import_data = {
            "version": "1.0",
            "cutoffs": {
                "IMPORT_BTC_USDT": {
                    "market_tag": "IMPORT_BTC_USDT",
                    "cutoff_date": "2020-01-01T00:00:00",
                    "discovery_date": "2025-01-08T10:00:00",
                    "precision_hours": 24,
                    "exchange": "IMPORT",
                    "primary_asset": "BTC",
                    "secondary_asset": "USDT",
                    "discovery_metadata": {}
                }
            }
        }
        
        result = db.import_cutoffs(json.dumps(import_data), "json")
        assert result is True
        
        # Verify imported data
        imported_record = db.get_cutoff("IMPORT_BTC_USDT")
        assert imported_record is not None
        assert imported_record.market_tag == "IMPORT_BTC_USDT"
        assert imported_record.cutoff_date == datetime(2020, 1, 1)
    
    def test_import_cutoffs_csv(self, temp_db_path):
        """Test importing cutoffs from CSV format."""
        db = HistoryDatabase(str(temp_db_path))
        
        csv_data = """market_tag,cutoff_date,discovery_date,precision_hours,exchange,primary_asset,secondary_asset
IMPORT_ETH_USDT,2020-02-01T00:00:00,2025-01-08T10:00:00,24,IMPORT,ETH,USDT"""
        
        result = db.import_cutoffs(csv_data, "csv")
        assert result is True
        
        # Verify imported data
        imported_record = db.get_cutoff("IMPORT_ETH_USDT")
        assert imported_record is not None
        assert imported_record.market_tag == "IMPORT_ETH_USDT"
        assert imported_record.cutoff_date == datetime(2020, 2, 1)
    
    def test_backup_creation(self, temp_db_path, sample_cutoff_data):
        """Test backup creation functionality."""
        db = HistoryDatabase(str(temp_db_path))
        
        # Store some initial data
        db.store_cutoff("INITIAL_BTC_USDT", datetime(2020, 1, 1), sample_cutoff_data)
        
        # Store more data to trigger backup creation
        db.store_cutoff("TEST_BTC_USDT", datetime(2020, 1, 2), sample_cutoff_data)
        
        # Check that backup was created
        backup_dir = temp_db_path.parent / "backups"
        backup_files = list(backup_dir.glob("history_cutoffs_backup_*.json"))
        
        assert len(backup_files) >= 1
        
        # Verify backup content (backup contains state before the last write)
        with open(backup_files[-1], 'r') as f:
            backup_data = json.load(f)
        
        assert "cutoffs" in backup_data
        # The backup should contain the initial data
        assert "INITIAL_BTC_USDT" in backup_data["cutoffs"]
    
    def test_database_stats(self, temp_db_path, sample_cutoff_data):
        """Test database statistics functionality."""
        db = HistoryDatabase(str(temp_db_path))
        
        # Store some test data
        markets = [
            ("BINANCE_BTC_USDT", "BINANCE"),
            ("BINANCE_ETH_USDT", "BINANCE"),
            ("COINBASE_BTC_USD", "COINBASE")
        ]
        
        for market_tag, exchange in markets:
            # Modify market tag to include exchange info
            full_market_tag = f"{exchange}_{market_tag.split('_', 1)[1]}"
            db.store_cutoff(full_market_tag, datetime(2020, 1, 1), sample_cutoff_data)
        
        stats = db.get_database_stats()
        
        assert "version" in stats
        assert "total_cutoffs" in stats
        assert stats["total_cutoffs"] == 3
        assert "exchanges" in stats
        assert "file_size_bytes" in stats
        assert stats["file_size_bytes"] > 0
    
    def test_database_validation(self, temp_db_path, sample_cutoff_data):
        """Test database integrity validation."""
        db = HistoryDatabase(str(temp_db_path))
        
        # Store valid data
        db.store_cutoff("VALID_BTC_USDT", datetime(2020, 1, 1), sample_cutoff_data)
        
        validation_result = db.validate_database_integrity()
        
        assert validation_result["is_valid"] is True
        assert len(validation_result["errors"]) == 0
    
    def test_concurrent_access(self, temp_db_path, sample_cutoff_data):
        """Test concurrent database access."""
        db = HistoryDatabase(str(temp_db_path))
        
        results = []
        errors = []
        
        def store_cutoff_worker(worker_id):
            try:
                market_tag = f"CONCURRENT_TEST_{worker_id}"
                cutoff_date = datetime(2020, 1, worker_id + 1)  # Add 1 to avoid day 0
                result = db.store_cutoff(market_tag, cutoff_date, sample_cutoff_data)
                results.append((worker_id, result))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        def read_cutoff_worker(worker_id):
            try:
                # Try to read existing data
                all_cutoffs = db.get_all_cutoffs()
                results.append((f"read_{worker_id}", len(all_cutoffs)))
            except Exception as e:
                errors.append((f"read_{worker_id}", str(e)))
        
        # Create multiple threads for concurrent access
        threads = []
        
        # Writer threads
        for i in range(5):
            thread = threading.Thread(target=store_cutoff_worker, args=(i,))
            threads.append(thread)
        
        # Reader threads
        for i in range(3):
            thread = threading.Thread(target=read_cutoff_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        
        # Verify all writes succeeded
        write_results = [r for r in results if isinstance(r[0], int)]
        assert len(write_results) == 5
        assert all(result[1] is True for result in write_results)
        
        # Verify final state
        final_cutoffs = db.get_all_cutoffs()
        assert len(final_cutoffs) == 5
    
    def test_corruption_recovery(self, temp_db_path):
        """Test recovery from corrupted database file."""
        # Create database and store some data
        db = HistoryDatabase(str(temp_db_path))
        db.store_cutoff("TEST_BTC_USDT", datetime(2020, 1, 1), {"test": "data"})
        
        # Corrupt the database file
        with open(temp_db_path, 'w') as f:
            f.write("invalid json content")
        
        # Clear cache to force reload
        db._data_cache = None
        
        # Try to access data - should trigger recovery
        cutoffs = db.get_all_cutoffs()
        
        # Should either recover from backup or initialize new database
        assert isinstance(cutoffs, dict)
    
    def test_missing_database_file(self, temp_db_path):
        """Test handling of missing database file."""
        # Don't create the database file
        temp_db_path.unlink(missing_ok=True)
        
        db = HistoryDatabase(str(temp_db_path))
        
        # Should initialize new database
        assert temp_db_path.exists()
        
        # Should be able to store data
        result = db.store_cutoff("TEST_BTC_USDT", datetime(2020, 1, 1), {"test": "data"})
        assert result is True
    
    def test_file_permission_error(self, temp_db_path):
        """Test handling of file permission errors."""
        # Create database first
        db = HistoryDatabase(str(temp_db_path))
        
        # Make the parent directory read-only to simulate permission error
        parent_dir = temp_db_path.parent
        original_mode = parent_dir.stat().st_mode
        parent_dir.chmod(0o444)
        
        try:
            # Should handle permission error gracefully
            result = db.store_cutoff("TEST_BTC_USDT", datetime(2020, 1, 1), {"test": "data"})
            assert result is False
        finally:
            # Restore permissions for cleanup
            parent_dir.chmod(original_mode)
    
    def test_market_tag_parsing(self, temp_db_path, sample_cutoff_data):
        """Test parsing of different market tag formats."""
        db = HistoryDatabase(str(temp_db_path))
        
        test_cases = [
            ("BINANCEFUTURES_BTC_USDT_PERPETUAL", "BINANCEFUTURES", "BTC", "USDT"),
            ("COINBASE_ETH_USD", "COINBASE", "ETH", "USD"),
            ("INVALID_FORMAT", "UNKNOWN", "UNKNOWN", "UNKNOWN"),
            ("", "UNKNOWN", "UNKNOWN", "UNKNOWN")
        ]
        
        for market_tag, expected_exchange, expected_primary, expected_secondary in test_cases:
            db.store_cutoff(market_tag, datetime(2020, 1, 1), sample_cutoff_data)
            
            record = db.get_cutoff(market_tag)
            assert record is not None
            assert record.exchange == expected_exchange
            assert record.primary_asset == expected_primary
            assert record.secondary_asset == expected_secondary
    
    def test_backup_cleanup(self, temp_db_path, sample_cutoff_data):
        """Test automatic cleanup of old backup files."""
        db = HistoryDatabase(str(temp_db_path))
        
        # Create multiple backups by storing data multiple times
        for i in range(15):  # More than the default keep_count of 10
            db.store_cutoff(f"TEST_BTC_USDT_{i}", datetime(2020, 1, 1), sample_cutoff_data)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        backup_dir = temp_db_path.parent / "backups"
        backup_files = list(backup_dir.glob("history_cutoffs_backup_*.json"))
        
        # Should keep only the most recent backups (default is 10)
        assert len(backup_files) <= 10