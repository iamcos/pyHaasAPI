"""
Core data models for the Backtesting History Intelligence system.

This module defines the dataclasses used throughout the history intelligence
system for representing cutoff records, validation results, and other core
data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class CutoffRecord:
    """
    Represents a discovered cutoff date record for a trading pair.
    
    This record contains all information about when historical data
    becomes available for a specific market, along with metadata
    about how the cutoff was discovered.
    """
    market_tag: str
    cutoff_date: datetime
    discovery_date: datetime
    precision_hours: int
    exchange: str
    primary_asset: str
    secondary_asset: str
    discovery_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for JSON serialization."""
        return {
            'market_tag': self.market_tag,
            'cutoff_date': self.cutoff_date.isoformat(),
            'discovery_date': self.discovery_date.isoformat(),
            'precision_hours': self.precision_hours,
            'exchange': self.exchange,
            'primary_asset': self.primary_asset,
            'secondary_asset': self.secondary_asset,
            'discovery_metadata': self.discovery_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CutoffRecord':
        """Create a CutoffRecord from a dictionary."""
        return cls(
            market_tag=data['market_tag'],
            cutoff_date=datetime.fromisoformat(data['cutoff_date']),
            discovery_date=datetime.fromisoformat(data['discovery_date']),
            precision_hours=data['precision_hours'],
            exchange=data['exchange'],
            primary_asset=data['primary_asset'],
            secondary_asset=data['secondary_asset'],
            discovery_metadata=data.get('discovery_metadata', {})
        )


@dataclass
class ValidationResult:
    """
    Result of validating a backtest period against known cutoff dates.
    
    Contains information about whether the requested period is valid
    and any adjustments that need to be made.
    """
    is_valid: bool
    adjusted_start_date: Optional[datetime] = None
    cutoff_date: Optional[datetime] = None
    message: str = ""
    requires_sync: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            'is_valid': self.is_valid,
            'adjusted_start_date': self.adjusted_start_date.isoformat() if self.adjusted_start_date else None,
            'cutoff_date': self.cutoff_date.isoformat() if self.cutoff_date else None,
            'message': self.message,
            'requires_sync': self.requires_sync
        }


@dataclass
class CutoffResult:
    """
    Result of a cutoff date discovery operation.
    
    Contains the discovered cutoff date along with metadata about
    the discovery process performance and accuracy.
    """
    success: bool
    cutoff_date: Optional[datetime] = None
    precision_achieved: int = 0
    discovery_time_seconds: float = 0.0
    tests_performed: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            'success': self.success,
            'cutoff_date': self.cutoff_date.isoformat() if self.cutoff_date else None,
            'precision_achieved': self.precision_achieved,
            'discovery_time_seconds': self.discovery_time_seconds,
            'tests_performed': self.tests_performed,
            'error_message': self.error_message
        }


@dataclass
class HistoryResult:
    """
    Result of checking and ensuring sufficient history for backtesting.
    
    Contains information about history availability and any sync
    operations that were performed or are required.
    """
    sufficient_history: bool
    sync_required: bool = False
    sync_completed: bool = False
    estimated_wait_time: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            'sufficient_history': self.sufficient_history,
            'sync_required': self.sync_required,
            'sync_completed': self.sync_completed,
            'estimated_wait_time': self.estimated_wait_time,
            'error_message': self.error_message
        }


@dataclass
class SyncStatusResult:
    """
    Result of checking history synchronization status for a market.
    
    Contains detailed information about the current sync state
    and any ongoing synchronization operations.
    """
    is_synced: bool
    sync_in_progress: bool = False
    last_sync_date: Optional[datetime] = None
    available_history_months: int = 0
    sync_progress_percent: float = 0.0
    estimated_completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            'is_synced': self.is_synced,
            'sync_in_progress': self.sync_in_progress,
            'last_sync_date': self.last_sync_date.isoformat() if self.last_sync_date else None,
            'available_history_months': self.available_history_months,
            'sync_progress_percent': self.sync_progress_percent,
            'estimated_completion_time': self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            'error_message': self.error_message
        }