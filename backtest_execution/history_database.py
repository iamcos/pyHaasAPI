"""
Database management for backtesting history intelligence.

This module provides persistent storage for cutoff date records using
JSON-based storage with backup functionality and concurrent access support.
"""

import json
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

try:
    from .history_intelligence_models import CutoffRecord
except ImportError:
    from history_intelligence_models import CutoffRecord


class HistoryDatabase:
    """
    JSON-based database for storing and managing cutoff date records.
    
    Provides thread-safe operations for storing, retrieving, and managing
    cutoff date information with automatic backup functionality.
    """
    
    def __init__(self, db_path: str = "data/history_cutoffs.json"):
        """
        Initialize the history database.
        
        Args:
            db_path: Path to the JSON database file
        """
        self.db_path = Path(db_path)
        self.backup_dir = self.db_path.parent / "backups"
        self._lock = threading.RLock()
        self._data_cache: Optional[Dict[str, Any]] = None
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database file if it doesn't exist
        if not self.db_path.exists():
            self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize an empty database file with proper structure."""
        initial_data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "cutoffs": {}
        }
        
        with open(self.db_path, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    @contextmanager
    def _database_lock(self):
        """Context manager for thread-safe database operations."""
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()
    
    def _load_data(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load data from the database file with caching.
        
        Args:
            force_reload: Force reload from disk even if cached
            
        Returns:
            Dictionary containing the database data
        """
        if self._data_cache is None or force_reload:
            try:
                with open(self.db_path, 'r') as f:
                    self._data_cache = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                # If file is corrupted or missing, try to restore from backup
                if self._restore_from_backup():
                    with open(self.db_path, 'r') as f:
                        self._data_cache = json.load(f)
                else:
                    # If no backup available, initialize new database
                    self._initialize_database()
                    self._data_cache = self._load_data(force_reload=True)
        
        return self._data_cache
    
    def _save_data(self, data: Dict[str, Any]) -> bool:
        """
        Save data to the database file with backup.
        
        Args:
            data: Data to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Create backup before saving
            self._create_backup()
            
            # Update timestamp
            data["last_updated"] = datetime.now().isoformat()
            
            # Write to temporary file first, then move to avoid corruption
            temp_path = self.db_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic move
            shutil.move(str(temp_path), str(self.db_path))
            
            # Update cache
            self._data_cache = data
            
            return True
            
        except Exception as e:
            # Clean up temporary file if it exists
            temp_path = self.db_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            
            print(f"Error saving database: {e}")
            return False
    
    def _create_backup(self) -> bool:
        """
        Create a timestamped backup of the current database.
        
        Returns:
            True if backup was successful, False otherwise
        """
        try:
            if not self.db_path.exists():
                return True  # Nothing to backup
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"history_cutoffs_backup_{timestamp}.json"
            
            shutil.copy2(str(self.db_path), str(backup_path))
            
            # Clean up old backups (keep last 10)
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 10) -> None:
        """
        Remove old backup files, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backup files to keep
        """
        try:
            backup_files = list(self.backup_dir.glob("history_cutoffs_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for backup_file in backup_files[keep_count:]:
                backup_file.unlink()
                
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
    
    def _restore_from_backup(self) -> bool:
        """
        Restore database from the most recent backup.
        
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            backup_files = list(self.backup_dir.glob("history_cutoffs_backup_*.json"))
            if not backup_files:
                return False
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            # Restore from backup
            shutil.copy2(str(latest_backup), str(self.db_path))
            
            print(f"Database restored from backup: {latest_backup.name}")
            return True
            
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def store_cutoff(self, market_tag: str, cutoff_date: datetime, 
                    discovery_metadata: Dict[str, Any]) -> bool:
        """
        Store a cutoff date record in the database.
        
        Args:
            market_tag: Market identifier (e.g., "BINANCEFUTURES_BTC_USDT_PERPETUAL")
            cutoff_date: The discovered cutoff date
            discovery_metadata: Metadata about the discovery process
            
        Returns:
            True if storage was successful, False otherwise
        """
        with self._database_lock():
            try:
                data = self._load_data()
                
                # Parse market tag to extract components
                parts = market_tag.split('_')
                if len(parts) >= 3:
                    exchange = parts[0]
                    primary_asset = parts[1]
                    secondary_asset = parts[2]
                else:
                    # Fallback parsing
                    exchange = "UNKNOWN"
                    primary_asset = "UNKNOWN"
                    secondary_asset = "UNKNOWN"
                
                # Create cutoff record
                record = CutoffRecord(
                    market_tag=market_tag,
                    cutoff_date=cutoff_date,
                    discovery_date=datetime.now(),
                    precision_hours=discovery_metadata.get('final_precision_hours', 24),
                    exchange=exchange,
                    primary_asset=primary_asset,
                    secondary_asset=secondary_asset,
                    discovery_metadata=discovery_metadata
                )
                
                # Store in database (cutoff dates are immutable - only add if not exists)
                if market_tag not in data["cutoffs"]:
                    data["cutoffs"][market_tag] = record.to_dict()
                    return self._save_data(data)
                else:
                    # Record already exists - cutoff dates are immutable
                    return True
                    
            except Exception as e:
                print(f"Error storing cutoff: {e}")
                return False
    
    def get_cutoff(self, market_tag: str) -> Optional[CutoffRecord]:
        """
        Retrieve a cutoff record for a specific market.
        
        Args:
            market_tag: Market identifier
            
        Returns:
            CutoffRecord if found, None otherwise
        """
        with self._database_lock():
            try:
                data = self._load_data()
                cutoff_data = data["cutoffs"].get(market_tag)
                
                if cutoff_data:
                    return CutoffRecord.from_dict(cutoff_data)
                
                return None
                
            except Exception as e:
                print(f"Error retrieving cutoff: {e}")
                return None
    
    def get_all_cutoffs(self) -> Dict[str, CutoffRecord]:
        """
        Retrieve all cutoff records from the database.
        
        Returns:
            Dictionary mapping market tags to CutoffRecord objects
        """
        with self._database_lock():
            try:
                data = self._load_data()
                result = {}
                
                for market_tag, cutoff_data in data["cutoffs"].items():
                    result[market_tag] = CutoffRecord.from_dict(cutoff_data)
                
                return result
                
            except Exception as e:
                print(f"Error retrieving all cutoffs: {e}")
                return {}
    
    def export_cutoffs(self, format: str = "json") -> str:
        """
        Export cutoff data in the specified format.
        
        Args:
            format: Export format ("json" or "csv")
            
        Returns:
            Exported data as string
        """
        with self._database_lock():
            try:
                data = self._load_data()
                
                if format.lower() == "json":
                    return json.dumps(data, indent=2)
                elif format.lower() == "csv":
                    # Convert to CSV format
                    lines = ["market_tag,cutoff_date,discovery_date,precision_hours,exchange,primary_asset,secondary_asset"]
                    
                    for market_tag, cutoff_data in data["cutoffs"].items():
                        record = CutoffRecord.from_dict(cutoff_data)
                        lines.append(f"{record.market_tag},{record.cutoff_date.isoformat()},"
                                   f"{record.discovery_date.isoformat()},{record.precision_hours},"
                                   f"{record.exchange},{record.primary_asset},{record.secondary_asset}")
                    
                    return "\n".join(lines)
                else:
                    raise ValueError(f"Unsupported export format: {format}")
                    
            except Exception as e:
                print(f"Error exporting cutoffs: {e}")
                return ""
    
    def import_cutoffs(self, data: str, format: str = "json") -> bool:
        """
        Import cutoff data from the specified format.
        
        Args:
            data: Data to import as string
            format: Import format ("json" or "csv")
            
        Returns:
            True if import was successful, False otherwise
        """
        with self._database_lock():
            try:
                current_data = self._load_data()
                
                if format.lower() == "json":
                    import_data = json.loads(data)
                    
                    # Merge cutoffs (don't overwrite existing ones)
                    for market_tag, cutoff_data in import_data.get("cutoffs", {}).items():
                        if market_tag not in current_data["cutoffs"]:
                            current_data["cutoffs"][market_tag] = cutoff_data
                
                elif format.lower() == "csv":
                    lines = data.strip().split('\n')
                    if len(lines) < 2:  # Header + at least one data line
                        return False
                    
                    # Skip header
                    for line in lines[1:]:
                        parts = line.split(',')
                        if len(parts) >= 7:
                            market_tag = parts[0]
                            
                            # Only import if not already exists
                            if market_tag not in current_data["cutoffs"]:
                                record = CutoffRecord(
                                    market_tag=market_tag,
                                    cutoff_date=datetime.fromisoformat(parts[1]),
                                    discovery_date=datetime.fromisoformat(parts[2]),
                                    precision_hours=int(parts[3]),
                                    exchange=parts[4],
                                    primary_asset=parts[5],
                                    secondary_asset=parts[6],
                                    discovery_metadata={}
                                )
                                current_data["cutoffs"][market_tag] = record.to_dict()
                
                else:
                    raise ValueError(f"Unsupported import format: {format}")
                
                return self._save_data(current_data)
                
            except Exception as e:
                print(f"Error importing cutoffs: {e}")
                return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the database.
        
        Returns:
            Dictionary containing database statistics
        """
        with self._database_lock():
            try:
                data = self._load_data()
                
                stats = {
                    "version": data.get("version", "unknown"),
                    "created": data.get("created", "unknown"),
                    "last_updated": data.get("last_updated", "unknown"),
                    "total_cutoffs": len(data.get("cutoffs", {})),
                    "file_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
                    "backup_count": len(list(self.backup_dir.glob("history_cutoffs_backup_*.json")))
                }
                
                # Exchange breakdown
                exchanges = {}
                for cutoff_data in data.get("cutoffs", {}).values():
                    exchange = cutoff_data.get("exchange", "unknown")
                    exchanges[exchange] = exchanges.get(exchange, 0) + 1
                
                stats["exchanges"] = exchanges
                
                return stats
                
            except Exception as e:
                print(f"Error getting database stats: {e}")
                return {}
    
    def validate_database_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of the database.
        
        Returns:
            Dictionary containing validation results
        """
        with self._database_lock():
            try:
                data = self._load_data()
                
                validation_result = {
                    "is_valid": True,
                    "errors": [],
                    "warnings": []
                }
                
                # Check required fields
                required_fields = ["version", "cutoffs"]
                for field in required_fields:
                    if field not in data:
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(f"Missing required field: {field}")
                
                # Validate cutoff records
                for market_tag, cutoff_data in data.get("cutoffs", {}).items():
                    try:
                        # Try to create CutoffRecord from data
                        CutoffRecord.from_dict(cutoff_data)
                    except Exception as e:
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(f"Invalid cutoff record for {market_tag}: {e}")
                
                return validation_result
                
            except Exception as e:
                return {
                    "is_valid": False,
                    "errors": [f"Database validation failed: {e}"],
                    "warnings": []
                }