"""
Bulk Operations for Lab and Bot Management
Handles bulk execution, monitoring, and management operations.
"""

import logging
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BulkOperationResult:
    """Result of a bulk operation"""
    operation_id: str
    total_items: int
    successful_items: int
    failed_items: int
    results: Dict[str, Any]
    failures: Dict[str, str]
    status: OperationStatus
    start_time: float
    end_time: Optional[float] = None


class BulkLabExecutor:
    """Handles bulk lab execution operations"""
    
    def __init__(self, haas_executor):
        self.haas_executor = haas_executor
        self.active_operations = {}
        
    def start_multiple_labs(self, lab_ids: List[str], start_unix: int, end_unix: int,
                          send_email: bool = False, operation_id: Optional[str] = None) -> BulkOperationResult:
        """
        Start execution on multiple labs with the same time period
        
        Args:
            lab_ids: List of lab IDs to start
            start_unix: Start timestamp for backtest
            end_unix: End timestamp for backtest
            send_email: Whether to send email notifications
            operation_id: Optional operation ID for tracking
            
        Returns:
            BulkOperationResult with execution results
        """
        from pyHaasAPI import api
        
        if not operation_id:
            operation_id = f"bulk_start_{int(time.time())}"
        
        operation = BulkOperationResult(
            operation_id=operation_id,
            total_items=len(lab_ids),
            successful_items=0,
            failed_items=0,
            results={},
            failures={},
            status=OperationStatus.RUNNING,
            start_time=time.time()
        )
        
        self.active_operations[operation_id] = operation
        
        print(f"🚀 Starting execution on {len(lab_ids)} labs (Operation: {operation_id})")
        
        for i, lab_id in enumerate(lab_ids, 1):
            print(f"[{i}/{len(lab_ids)}] Starting lab {lab_id}...")
            
            try:
                req = api.StartLabExecutionRequest(
                    lab_id=lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=send_email
                )
                
                result = api.start_lab_execution(self.haas_executor, req)
                operation.results[lab_id] = result
                operation.successful_items += 1
                print(f"  ✅ Started successfully")
                
            except Exception as e:
                error_msg = str(e)
                operation.failures[lab_id] = error_msg
                operation.failed_items += 1
                print(f"  ❌ Failed: {error_msg}")
        
        operation.status = OperationStatus.COMPLETED
        operation.end_time = time.time()
        
        print(f"✅ Bulk operation completed: {operation.successful_items} started, {operation.failed_items} failed")
        
        return operation
    
    def cancel_multiple_labs(self, lab_ids: List[str], operation_id: Optional[str] = None) -> BulkOperationResult:
        """
        Cancel execution on multiple labs
        
        Args:
            lab_ids: List of lab IDs to cancel
            operation_id: Optional operation ID for tracking
            
        Returns:
            BulkOperationResult with cancellation results
        """
        from pyHaasAPI import api
        
        if not operation_id:
            operation_id = f"bulk_cancel_{int(time.time())}"
        
        operation = BulkOperationResult(
            operation_id=operation_id,
            total_items=len(lab_ids),
            successful_items=0,
            failed_items=0,
            results={},
            failures={},
            status=OperationStatus.RUNNING,
            start_time=time.time()
        )
        
        self.active_operations[operation_id] = operation
        
        print(f"🛑 Cancelling execution on {len(lab_ids)} labs (Operation: {operation_id})")
        
        for i, lab_id in enumerate(lab_ids, 1):
            print(f"[{i}/{len(lab_ids)}] Cancelling lab {lab_id}...")
            
            try:
                result = api.cancel_lab_execution(self.haas_executor, lab_id)
                operation.results[lab_id] = result
                operation.successful_items += 1
                print(f"  ✅ Cancelled successfully")
                
            except Exception as e:
                error_msg = str(e)
                operation.failures[lab_id] = error_msg
                operation.failed_items += 1
                print(f"  ❌ Failed: {error_msg}")
        
        operation.status = OperationStatus.COMPLETED
        operation.end_time = time.time()
        
        print(f"✅ Bulk cancellation completed: {operation.successful_items} cancelled, {operation.failed_items} failed")
        
        return operation
    
    def get_operation_status(self, operation_id: str) -> Optional[BulkOperationResult]:
        """Get the status of a bulk operation"""
        return self.active_operations.get(operation_id)
    
    def list_active_operations(self) -> List[str]:
        """List all active operation IDs"""
        return list(self.active_operations.keys())


class BulkLabManager:
    """Handles bulk lab management operations"""
    
    def __init__(self, haas_executor):
        self.haas_executor = haas_executor
        
    def delete_labs_by_pattern(self, name_pattern: str, exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Delete labs matching a name pattern
        
        Args:
            name_pattern: Pattern to match lab names (simple string contains)
            exclude_patterns: Patterns to exclude from deletion
            
        Returns:
            Dictionary with deletion results
        """
        from pyHaasAPI import api
        
        exclude_patterns = exclude_patterns or []
        
        try:
            all_labs = api.get_all_labs(self.haas_executor)
            
            # Filter labs to delete
            labs_to_delete = []
            for lab in all_labs:
                # Check if lab name contains the pattern
                if name_pattern.lower() in lab.name.lower():
                    # Check if it should be excluded
                    should_exclude = any(
                        exclude_pattern.lower() in lab.name.lower()
                        for exclude_pattern in exclude_patterns
                    )
                    if not should_exclude:
                        labs_to_delete.append(lab)
            
            print(f"🗑️  Found {len(labs_to_delete)} labs matching pattern '{name_pattern}'")
            
            deleted_count = 0
            failed_deletions = {}
            
            for lab in labs_to_delete:
                try:
                    api.delete_lab(self.haas_executor, lab.lab_id)
                    deleted_count += 1
                    print(f"  ✅ Deleted: {lab.name}")
                except Exception as e:
                    failed_deletions[lab.name] = str(e)
                    print(f"  ❌ Failed to delete {lab.name}: {e}")
            
            return {
                "total_found": len(labs_to_delete),
                "deleted_count": deleted_count,
                "failed_count": len(failed_deletions),
                "failures": failed_deletions
            }
            
        except Exception as e:
            logging.error(f"Error in bulk lab deletion: {e}")
            return {"error": str(e)}
    
    def get_labs_by_status(self, status_filter: Optional[str] = None) -> Dict[str, List[Any]]:
        """
        Get labs grouped by their execution status
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            Dictionary with labs grouped by status
        """
        from pyHaasAPI import api
        
        try:
            all_labs = api.get_all_labs(self.haas_executor)
            
            status_groups = {
                "running": [],
                "completed": [],
                "idle": [],
                "error": []
            }
            
            for lab in all_labs:
                # TODO: Implement status detection logic
                # This would involve checking lab execution status
                # For now, we'll put all labs in "idle"
                status_groups["idle"].append(lab)
            
            if status_filter:
                return {status_filter: status_groups.get(status_filter, [])}
            
            return status_groups
            
        except Exception as e:
            logging.error(f"Error getting labs by status: {e}")
            return {"error": str(e)}


class BulkBotManager:
    """Handles bulk bot management operations"""
    
    def __init__(self, haas_executor):
        self.haas_executor = haas_executor
        
    def activate_multiple_bots(self, bot_ids: List[str]) -> Dict[str, Any]:
        """
        Activate multiple bots
        
        Args:
            bot_ids: List of bot IDs to activate
            
        Returns:
            Dictionary with activation results
        """
        from pyHaasAPI import api
        
        results = {}
        failures = {}
        
        print(f"🤖 Activating {len(bot_ids)} bots...")
        
        for i, bot_id in enumerate(bot_ids, 1):
            print(f"[{i}/{len(bot_ids)}] Activating bot {bot_id}...")
            
            try:
                bot = api.activate_bot(self.haas_executor, bot_id)
                results[bot_id] = {
                    "bot_id": bot.bot_id,
                    "is_activated": bot.is_activated
                }
                print(f"  ✅ Activated successfully")
                
            except Exception as e:
                failures[bot_id] = str(e)
                print(f"  ❌ Failed: {e}")
        
        return {
            "activated_count": len(results),
            "failed_count": len(failures),
            "results": results,
            "failures": failures
        }
    
    def deactivate_multiple_bots(self, bot_ids: List[str]) -> Dict[str, Any]:
        """
        Deactivate multiple bots
        
        Args:
            bot_ids: List of bot IDs to deactivate
            
        Returns:
            Dictionary with deactivation results
        """
        from pyHaasAPI import api
        
        results = {}
        failures = {}
        
        print(f"🛑 Deactivating {len(bot_ids)} bots...")
        
        for i, bot_id in enumerate(bot_ids, 1):
            print(f"[{i}/{len(bot_ids)}] Deactivating bot {bot_id}...")
            
            try:
                bot = api.deactivate_bot(self.haas_executor, bot_id)
                results[bot_id] = {
                    "bot_id": bot.bot_id,
                    "is_activated": bot.is_activated
                }
                print(f"  ✅ Deactivated successfully")
                
            except Exception as e:
                failures[bot_id] = str(e)
                print(f"  ❌ Failed: {e}")
        
        return {
            "deactivated_count": len(results),
            "failed_count": len(failures),
            "results": results,
            "failures": failures
        }


def calculate_operation_duration(operation: BulkOperationResult) -> float:
    """Calculate the duration of a bulk operation in seconds"""
    if operation.end_time:
        return operation.end_time - operation.start_time
    else:
        return time.time() - operation.start_time


def format_operation_summary(operation: BulkOperationResult) -> str:
    """Format a bulk operation result into a readable summary"""
    duration = calculate_operation_duration(operation)
    
    summary = f"""
Bulk Operation Summary
======================
Operation ID: {operation.operation_id}
Status: {operation.status.value}
Duration: {duration:.2f} seconds

Results:
- Total Items: {operation.total_items}
- Successful: {operation.successful_items}
- Failed: {operation.failed_items}
- Success Rate: {(operation.successful_items / operation.total_items * 100):.1f}%
"""
    
    if operation.failures:
        summary += f"\nFailures:\n"
        for item_id, error in operation.failures.items():
            summary += f"- {item_id}: {error}\n"
    
    return summary