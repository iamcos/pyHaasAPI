"""
Unit tests for history intelligence data models.

Tests the core dataclasses and their serialization/deserialization methods.
"""

import pytest
from datetime import datetime
from backtest_execution.history_intelligence_models import (
    CutoffRecord, ValidationResult, CutoffResult, HistoryResult, SyncStatusResult
)


class TestCutoffRecord:
    """Test cases for CutoffRecord dataclass."""
    
    def test_cutoff_record_creation(self):
        """Test basic CutoffRecord creation."""
        cutoff_date = datetime(2020, 1, 1, 12, 0, 0)
        discovery_date = datetime(2025, 1, 8, 10, 30, 0)
        metadata = {"tests_performed": 10, "discovery_time": 45.2}
        
        record = CutoffRecord(
            market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
            cutoff_date=cutoff_date,
            discovery_date=discovery_date,
            precision_hours=24,
            exchange="BINANCEFUTURES",
            primary_asset="BTC",
            secondary_asset="USDT",
            discovery_metadata=metadata
        )
        
        assert record.market_tag == "BINANCEFUTURES_BTC_USDT_PERPETUAL"
        assert record.cutoff_date == cutoff_date
        assert record.discovery_date == discovery_date
        assert record.precision_hours == 24
        assert record.exchange == "BINANCEFUTURES"
        assert record.primary_asset == "BTC"
        assert record.secondary_asset == "USDT"
        assert record.discovery_metadata == metadata
    
    def test_cutoff_record_to_dict(self):
        """Test CutoffRecord serialization to dictionary."""
        cutoff_date = datetime(2020, 1, 1, 12, 0, 0)
        discovery_date = datetime(2025, 1, 8, 10, 30, 0)
        metadata = {"tests_performed": 10}
        
        record = CutoffRecord(
            market_tag="TEST_BTC_USDT",
            cutoff_date=cutoff_date,
            discovery_date=discovery_date,
            precision_hours=12,
            exchange="TEST",
            primary_asset="BTC",
            secondary_asset="USDT",
            discovery_metadata=metadata
        )
        
        result = record.to_dict()
        
        assert result["market_tag"] == "TEST_BTC_USDT"
        assert result["cutoff_date"] == cutoff_date.isoformat()
        assert result["discovery_date"] == discovery_date.isoformat()
        assert result["precision_hours"] == 12
        assert result["exchange"] == "TEST"
        assert result["primary_asset"] == "BTC"
        assert result["secondary_asset"] == "USDT"
        assert result["discovery_metadata"] == metadata
    
    def test_cutoff_record_from_dict(self):
        """Test CutoffRecord deserialization from dictionary."""
        cutoff_date = datetime(2020, 1, 1, 12, 0, 0)
        discovery_date = datetime(2025, 1, 8, 10, 30, 0)
        metadata = {"tests_performed": 10}
        
        data = {
            "market_tag": "TEST_BTC_USDT",
            "cutoff_date": cutoff_date.isoformat(),
            "discovery_date": discovery_date.isoformat(),
            "precision_hours": 12,
            "exchange": "TEST",
            "primary_asset": "BTC",
            "secondary_asset": "USDT",
            "discovery_metadata": metadata
        }
        
        record = CutoffRecord.from_dict(data)
        
        assert record.market_tag == "TEST_BTC_USDT"
        assert record.cutoff_date == cutoff_date
        assert record.discovery_date == discovery_date
        assert record.precision_hours == 12
        assert record.exchange == "TEST"
        assert record.primary_asset == "BTC"
        assert record.secondary_asset == "USDT"
        assert record.discovery_metadata == metadata
    
    def test_cutoff_record_roundtrip(self):
        """Test CutoffRecord serialization roundtrip."""
        original = CutoffRecord(
            market_tag="ROUNDTRIP_TEST",
            cutoff_date=datetime(2019, 6, 15, 8, 30, 45),
            discovery_date=datetime(2025, 1, 8, 14, 22, 10),
            precision_hours=6,
            exchange="TESTEX",
            primary_asset="ETH",
            secondary_asset="BTC",
            discovery_metadata={"test": "value", "number": 42}
        )
        
        # Serialize and deserialize
        data = original.to_dict()
        restored = CutoffRecord.from_dict(data)
        
        assert restored.market_tag == original.market_tag
        assert restored.cutoff_date == original.cutoff_date
        assert restored.discovery_date == original.discovery_date
        assert restored.precision_hours == original.precision_hours
        assert restored.exchange == original.exchange
        assert restored.primary_asset == original.primary_asset
        assert restored.secondary_asset == original.secondary_asset
        assert restored.discovery_metadata == original.discovery_metadata


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""
    
    def test_validation_result_valid(self):
        """Test ValidationResult for valid period."""
        result = ValidationResult(
            is_valid=True,
            message="Period is valid"
        )
        
        assert result.is_valid is True
        assert result.adjusted_start_date is None
        assert result.cutoff_date is None
        assert result.message == "Period is valid"
        assert result.requires_sync is False
    
    def test_validation_result_invalid_with_adjustment(self):
        """Test ValidationResult for invalid period with adjustment."""
        cutoff_date = datetime(2020, 1, 1)
        adjusted_date = datetime(2020, 1, 2)
        
        result = ValidationResult(
            is_valid=False,
            adjusted_start_date=adjusted_date,
            cutoff_date=cutoff_date,
            message="Start date adjusted to available history",
            requires_sync=True
        )
        
        assert result.is_valid is False
        assert result.adjusted_start_date == adjusted_date
        assert result.cutoff_date == cutoff_date
        assert result.message == "Start date adjusted to available history"
        assert result.requires_sync is True
    
    def test_validation_result_to_dict(self):
        """Test ValidationResult serialization."""
        cutoff_date = datetime(2020, 1, 1)
        adjusted_date = datetime(2020, 1, 2)
        
        result = ValidationResult(
            is_valid=False,
            adjusted_start_date=adjusted_date,
            cutoff_date=cutoff_date,
            message="Test message",
            requires_sync=True
        )
        
        data = result.to_dict()
        
        assert data["is_valid"] is False
        assert data["adjusted_start_date"] == adjusted_date.isoformat()
        assert data["cutoff_date"] == cutoff_date.isoformat()
        assert data["message"] == "Test message"
        assert data["requires_sync"] is True


class TestCutoffResult:
    """Test cases for CutoffResult dataclass."""
    
    def test_cutoff_result_success(self):
        """Test successful CutoffResult."""
        cutoff_date = datetime(2020, 1, 1)
        
        result = CutoffResult(
            success=True,
            cutoff_date=cutoff_date,
            precision_achieved=24,
            discovery_time_seconds=45.2,
            tests_performed=8
        )
        
        assert result.success is True
        assert result.cutoff_date == cutoff_date
        assert result.precision_achieved == 24
        assert result.discovery_time_seconds == 45.2
        assert result.tests_performed == 8
        assert result.error_message is None
    
    def test_cutoff_result_failure(self):
        """Test failed CutoffResult."""
        result = CutoffResult(
            success=False,
            error_message="Discovery failed due to API timeout"
        )
        
        assert result.success is False
        assert result.cutoff_date is None
        assert result.precision_achieved == 0
        assert result.discovery_time_seconds == 0.0
        assert result.tests_performed == 0
        assert result.error_message == "Discovery failed due to API timeout"
    
    def test_cutoff_result_to_dict(self):
        """Test CutoffResult serialization."""
        cutoff_date = datetime(2020, 1, 1)
        
        result = CutoffResult(
            success=True,
            cutoff_date=cutoff_date,
            precision_achieved=12,
            discovery_time_seconds=30.5,
            tests_performed=6,
            error_message=None
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["cutoff_date"] == cutoff_date.isoformat()
        assert data["precision_achieved"] == 12
        assert data["discovery_time_seconds"] == 30.5
        assert data["tests_performed"] == 6
        assert data["error_message"] is None


class TestHistoryResult:
    """Test cases for HistoryResult dataclass."""
    
    def test_history_result_sufficient(self):
        """Test HistoryResult with sufficient history."""
        result = HistoryResult(
            sufficient_history=True
        )
        
        assert result.sufficient_history is True
        assert result.sync_required is False
        assert result.sync_completed is False
        assert result.estimated_wait_time == 0
        assert result.error_message is None
    
    def test_history_result_sync_required(self):
        """Test HistoryResult requiring sync."""
        result = HistoryResult(
            sufficient_history=False,
            sync_required=True,
            sync_completed=True,
            estimated_wait_time=300
        )
        
        assert result.sufficient_history is False
        assert result.sync_required is True
        assert result.sync_completed is True
        assert result.estimated_wait_time == 300
        assert result.error_message is None
    
    def test_history_result_to_dict(self):
        """Test HistoryResult serialization."""
        result = HistoryResult(
            sufficient_history=False,
            sync_required=True,
            sync_completed=False,
            estimated_wait_time=600,
            error_message="Sync timeout"
        )
        
        data = result.to_dict()
        
        assert data["sufficient_history"] is False
        assert data["sync_required"] is True
        assert data["sync_completed"] is False
        assert data["estimated_wait_time"] == 600
        assert data["error_message"] == "Sync timeout"


class TestSyncStatusResult:
    """Test cases for SyncStatusResult dataclass."""
    
    def test_sync_status_result_synced(self):
        """Test SyncStatusResult for synced market."""
        last_sync = datetime(2025, 1, 8, 10, 0, 0)
        
        result = SyncStatusResult(
            is_synced=True,
            last_sync_date=last_sync,
            available_history_months=36
        )
        
        assert result.is_synced is True
        assert result.sync_in_progress is False
        assert result.last_sync_date == last_sync
        assert result.available_history_months == 36
        assert result.sync_progress_percent == 0.0
        assert result.estimated_completion_time is None
        assert result.error_message is None
    
    def test_sync_status_result_in_progress(self):
        """Test SyncStatusResult for sync in progress."""
        completion_time = datetime(2025, 1, 8, 11, 0, 0)
        
        result = SyncStatusResult(
            is_synced=False,
            sync_in_progress=True,
            sync_progress_percent=65.5,
            estimated_completion_time=completion_time
        )
        
        assert result.is_synced is False
        assert result.sync_in_progress is True
        assert result.sync_progress_percent == 65.5
        assert result.estimated_completion_time == completion_time
    
    def test_sync_status_result_to_dict(self):
        """Test SyncStatusResult serialization."""
        last_sync = datetime(2025, 1, 8, 10, 0, 0)
        completion_time = datetime(2025, 1, 8, 11, 0, 0)
        
        result = SyncStatusResult(
            is_synced=False,
            sync_in_progress=True,
            last_sync_date=last_sync,
            available_history_months=24,
            sync_progress_percent=75.0,
            estimated_completion_time=completion_time,
            error_message=None
        )
        
        data = result.to_dict()
        
        assert data["is_synced"] is False
        assert data["sync_in_progress"] is True
        assert data["last_sync_date"] == last_sync.isoformat()
        assert data["available_history_months"] == 24
        assert data["sync_progress_percent"] == 75.0
        assert data["estimated_completion_time"] == completion_time.isoformat()
        assert data["error_message"] is None