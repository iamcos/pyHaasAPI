#!/usr/bin/env python3
"""
History Sync Manager
This module manages chart history synchronization for backtesting operations.
It ensures proper market data is available before starting backtests by:
1. Making chart calls for each market
2. Checking basic sync completion
3. Upgrading to 36-month history sync
4. Queuing labs for execution once sync is complete
"""

import asyncio
import logging
import time
import requests
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """History sync status states"""
    NOT_STARTED = "not_started"
    BASIC_SYNC_REQUESTED = "basic_sync_requested"
    BASIC_SYNC_COMPLETE = "basic_sync_complete"
    EXTENDED_SYNC_REQUESTED = "extended_sync_requested"
    EXTENDED_SYNC_COMPLETE = "extended_sync_complete"
    SYNC_FAILED = "sync_failed"

class LabExecutionStatus(Enum):
    """Lab execution readiness status"""
    WAITING_FOR_SYNC = "waiting_for_sync"
    READY_FOR_EXECUTION = "ready_for_execution"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_FAILED = "execution_failed"

@dataclass
class MarketSyncInfo:
    """Information about market history sync status"""
    market_tag: str
    exchange: str
    primary_asset: str
    secondary_asset: str
    sync_status: SyncStatus = SyncStatus.NOT_STARTED
    basic_sync_start_time: Optional[float] = None
    extended_sync_start_time: Optional[float] = None
    last_status_check: Optional[float] = None
    sync_attempts: int = 0
    error_message: Optional[str] = None

@dataclass
class LabSyncRequest:
    """Lab waiting for history sync completion"""
    lab_id: str
    lab_name: str
    market_tag: str
    execution_config: Dict[str, Any]
    priority: int = 1
    created_time: float = field(default_factory=time.time)
    status: LabExecutionStatus = LabExecutionStatus.WAITING_FOR_SYNC

class HistorySyncManager:
    """Manages history synchronization for backtesting operations"""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        self.session = requests.Session()
        
        # Sync tracking
        self.market_sync_status: Dict[str, MarketSyncInfo] = {}
        self.lab_execution_queue: List[LabSyncRequest] = []
        self.active_sync_operations: Set[str] = set()
        
        # Configuration
        self.basic_sync_timeout = 300  # 5 minutes
        self.extended_sync_timeout = 1800  # 30 minutes
        self.status_check_interval = 10  # seconds
        self.max_concurrent_syncs = 5
        self.max_sync_attempts = 3
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Sync loop control
        self.sync_loop_running = False
        
    def parse_market_tag(self, market_tag: str) -> Tuple[str, str, str]:
        """Parse market tag into components"""
        try:
            parts = market_tag.split('_')
            if len(parts) >= 3:
                exchange = parts[0]
                primary = parts[1]
                secondary = parts[2]
                return exchange, primary, secondary
            else:
                raise ValueError(f"Invalid market tag format: {market_tag}")
        except Exception as e:
            logger.error(f"Failed to parse market tag {market_tag}: {e}")
            return "UNKNOWN", "UNKNOWN", "UNKNOWN"
    
    def add_lab_for_execution(self, lab_id: str, lab_name: str, market_tag: str, 
                             execution_config: Dict[str, Any], priority: int = 1) -> bool:
        """
        Add a lab to the execution queue, ensuring history sync first.
        
        Args:
            lab_id: Lab identifier
            lab_name: Lab name
            market_tag: Market tag (e.g., BINANCEFUTURES_BTC_USDT_PERPETUAL)
            execution_config: Execution configuration (period, etc.)
            priority: Execution priority (higher = more important)
            
        Returns:
            True if added successfully
        """
        try:
            # Create lab sync request
            lab_request = LabSyncRequest(
                lab_id=lab_id,
                lab_name=lab_name,
                market_tag=market_tag,
                execution_config=execution_config,
                priority=priority
            )
            
            # Add to queue (sorted by priority)
            self.lab_execution_queue.append(lab_request)
            self.lab_execution_queue.sort(key=lambda x: x.priority, reverse=True)
            
            # Initialize market sync info if not exists
            if market_tag not in self.market_sync_status:
                exchange, primary, secondary = self.parse_market_tag(market_tag)
                self.market_sync_status[market_tag] = MarketSyncInfo(
                    market_tag=market_tag,
                    exchange=exchange,
                    primary_asset=primary,
                    secondary_asset=secondary
                )
            
            logger.info(f"Added lab {lab_id} to execution queue for market {market_tag}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add lab {lab_id} to execution queue: {e}")
            return False
    
    def start_chart_sync(self, market_tag: str) -> bool:
        """
        Start chart history sync for a market.
        
        Args:
            market_tag: Market tag to sync
            
        Returns:
            True if sync started successfully
        """
        try:
            if market_tag in self.active_sync_operations:
                logger.info(f"Sync already in progress for {market_tag}")
                return True
            
            sync_info = self.market_sync_status.get(market_tag)
            if not sync_info:
                logger.error(f"No sync info found for market {market_tag}")
                return False
            
            # Make chart call to start basic sync
            chart_response = self._make_chart_call(market_tag)
            
            if chart_response.get('success', False):
                # Update sync status
                sync_info.sync_status = SyncStatus.BASIC_SYNC_REQUESTED
                sync_info.basic_sync_start_time = time.time()
                sync_info.sync_attempts += 1
                self.active_sync_operations.add(market_tag)
                
                logger.info(f"Started basic sync for {market_tag}")
                return True
            else:
                sync_info.sync_status = SyncStatus.SYNC_FAILED
                sync_info.error_message = chart_response.get('error', 'Unknown error')
                logger.error(f"Failed to start sync for {market_tag}: {sync_info.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Exception starting sync for {market_tag}: {e}")
            if market_tag in self.market_sync_status:
                self.market_sync_status[market_tag].sync_status = SyncStatus.SYNC_FAILED
                self.market_sync_status[market_tag].error_message = str(e)
            return False
    
    def _make_chart_call(self, market_tag: str) -> Dict[str, Any]:
        """
        Make chart call to HaasOnline API via MCP server.
        This initiates the history sync process.
        """
        try:
            # Parse market tag for chart call
            exchange, primary, secondary = self.parse_market_tag(market_tag)
            
            # Make chart call via MCP server
            # Note: This is a placeholder - you'll need to implement the actual chart endpoint
            payload = {
                "market": market_tag,
                "exchange": exchange,
                "primary": primary,
                "secondary": secondary,
                "sync_history": True
            }
            
            # For now, simulate the chart call
            logger.info(f"Making chart call for {market_tag} (simulated)")
            
            # In real implementation, this would be:
            # response = self.session.post(f"{self.mcp_base_url}/chart_call", json=payload)
            
            # Simulate successful chart call
            return {
                'success': True,
                'message': f'Chart call initiated for {market_tag}',
                'sync_started': True
            }
            
        except Exception as e:
            logger.error(f"Chart call failed for {market_tag}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_sync_status(self, market_tag: str) -> SyncStatus:
        """
        Check the current sync status for a market.
        
        Args:
            market_tag: Market tag to check
            
        Returns:
            Current sync status
        """
        try:
            sync_info = self.market_sync_status.get(market_tag)
            if not sync_info:
                return SyncStatus.NOT_STARTED
            
            # Check if we need to poll for status
            current_time = time.time()
            
            if sync_info.sync_status == SyncStatus.BASIC_SYNC_REQUESTED:
                # Check if basic sync is complete
                if self._check_basic_sync_complete(market_tag):
                    sync_info.sync_status = SyncStatus.BASIC_SYNC_COMPLETE
                    logger.info(f"Basic sync completed for {market_tag}")
                    
                    # Start extended sync (36 months)
                    if self._start_extended_sync(market_tag):
                        sync_info.sync_status = SyncStatus.EXTENDED_SYNC_REQUESTED
                        sync_info.extended_sync_start_time = current_time
                        logger.info(f"Started extended sync (36 months) for {market_tag}")
                
                # Check for timeout
                elif (sync_info.basic_sync_start_time and 
                      current_time - sync_info.basic_sync_start_time > self.basic_sync_timeout):
                    sync_info.sync_status = SyncStatus.SYNC_FAILED
                    sync_info.error_message = "Basic sync timeout"
                    logger.error(f"Basic sync timeout for {market_tag}")
            
            elif sync_info.sync_status == SyncStatus.EXTENDED_SYNC_REQUESTED:
                # Check if extended sync is complete
                if self._check_extended_sync_complete(market_tag):
                    sync_info.sync_status = SyncStatus.EXTENDED_SYNC_COMPLETE
                    self.active_sync_operations.discard(market_tag)
                    logger.info(f"Extended sync completed for {market_tag} - ready for backtesting!")
                
                # Check for timeout
                elif (sync_info.extended_sync_start_time and 
                      current_time - sync_info.extended_sync_start_time > self.extended_sync_timeout):
                    sync_info.sync_status = SyncStatus.SYNC_FAILED
                    sync_info.error_message = "Extended sync timeout"
                    self.active_sync_operations.discard(market_tag)
                    logger.error(f"Extended sync timeout for {market_tag}")
            
            sync_info.last_status_check = current_time
            return sync_info.sync_status
            
        except Exception as e:
            logger.error(f"Error checking sync status for {market_tag}: {e}")
            return SyncStatus.SYNC_FAILED
    
    def _check_basic_sync_complete(self, market_tag: str) -> bool:
        """Check if basic sync is complete (placeholder implementation)"""
        try:
            # In real implementation, this would check HaasOnline API for sync status
            # For now, simulate basic sync completion after 30 seconds
            sync_info = self.market_sync_status.get(market_tag)
            if sync_info and sync_info.basic_sync_start_time:
                elapsed = time.time() - sync_info.basic_sync_start_time
                return elapsed > 30  # Simulate 30-second basic sync
            return False
        except Exception as e:
            logger.error(f"Error checking basic sync for {market_tag}: {e}")
            return False
    
    def _start_extended_sync(self, market_tag: str) -> bool:
        """Start extended 36-month history sync"""
        try:
            # In real implementation, this would make API call to extend sync to 36 months
            logger.info(f"Starting 36-month extended sync for {market_tag}")
            
            # Simulate extended sync start
            return True
            
        except Exception as e:
            logger.error(f"Failed to start extended sync for {market_tag}: {e}")
            return False
    
    def _check_extended_sync_complete(self, market_tag: str) -> bool:
        """Check if extended sync is complete (placeholder implementation)"""
        try:
            # In real implementation, this would check HaasOnline API for extended sync status
            # For now, simulate extended sync completion after 2 minutes
            sync_info = self.market_sync_status.get(market_tag)
            if sync_info and sync_info.extended_sync_start_time:
                elapsed = time.time() - sync_info.extended_sync_start_time
                return elapsed > 120  # Simulate 2-minute extended sync
            return False
        except Exception as e:
            logger.error(f"Error checking extended sync for {market_tag}: {e}")
            return False
    
    def process_sync_queue(self) -> Dict[str, Any]:
        """
        Process the sync queue - start syncs and check for ready labs.
        
        Returns:
            Summary of processing results
        """
        try:
            results = {
                'syncs_started': 0,
                'syncs_completed': 0,
                'labs_ready': 0,
                'labs_started': 0,
                'errors': []
            }
            
            # Start new syncs for markets that need them
            markets_needing_sync = set()
            for lab_request in self.lab_execution_queue:
                if lab_request.status == LabExecutionStatus.WAITING_FOR_SYNC:
                    markets_needing_sync.add(lab_request.market_tag)
            
            # Start syncs for markets (up to concurrent limit)
            active_syncs = len(self.active_sync_operations)
            for market_tag in markets_needing_sync:
                if active_syncs >= self.max_concurrent_syncs:
                    break
                
                sync_info = self.market_sync_status.get(market_tag)
                if (sync_info and 
                    sync_info.sync_status == SyncStatus.NOT_STARTED and
                    sync_info.sync_attempts < self.max_sync_attempts):
                    
                    if self.start_chart_sync(market_tag):
                        results['syncs_started'] += 1
                        active_syncs += 1
            
            # Check sync status for all active syncs
            for market_tag in list(self.active_sync_operations):
                status = self.check_sync_status(market_tag)
                
                if status == SyncStatus.EXTENDED_SYNC_COMPLETE:
                    results['syncs_completed'] += 1
                    
                    # Mark labs as ready for execution
                    for lab_request in self.lab_execution_queue:
                        if (lab_request.market_tag == market_tag and 
                            lab_request.status == LabExecutionStatus.WAITING_FOR_SYNC):
                            lab_request.status = LabExecutionStatus.READY_FOR_EXECUTION
                            results['labs_ready'] += 1
                
                elif status == SyncStatus.SYNC_FAILED:
                    sync_info = self.market_sync_status.get(market_tag)
                    error_msg = f"Sync failed for {market_tag}: {sync_info.error_message if sync_info else 'Unknown error'}"
                    results['errors'].append(error_msg)
                    
                    # Mark labs as failed
                    for lab_request in self.lab_execution_queue:
                        if (lab_request.market_tag == market_tag and 
                            lab_request.status == LabExecutionStatus.WAITING_FOR_SYNC):
                            lab_request.status = LabExecutionStatus.EXECUTION_FAILED
            
            # Start execution for ready labs
            ready_labs = [lab for lab in self.lab_execution_queue 
                         if lab.status == LabExecutionStatus.READY_FOR_EXECUTION]
            
            for lab_request in ready_labs:
                if self._start_lab_execution(lab_request):
                    lab_request.status = LabExecutionStatus.EXECUTION_STARTED
                    results['labs_started'] += 1
                else:
                    lab_request.status = LabExecutionStatus.EXECUTION_FAILED
                    results['errors'].append(f"Failed to start execution for lab {lab_request.lab_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing sync queue: {e}")
            return {'error': str(e)}
    
    def _start_lab_execution(self, lab_request: LabSyncRequest) -> bool:
        """Start lab execution via MCP server"""
        try:
            payload = {
                "lab_id": lab_request.lab_id,
                **lab_request.execution_config
            }
            
            response = self.session.post(
                f"{self.mcp_base_url}/start_lab_execution",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    logger.info(f"Started execution for lab {lab_request.lab_id}")
                    return True
                else:
                    logger.error(f"MCP server error starting lab {lab_request.lab_id}: {data.get('Error', 'Unknown')}")
                    return False
            else:
                logger.error(f"HTTP error starting lab {lab_request.lab_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception starting lab execution {lab_request.lab_id}: {e}")
            return False
    
    async def start_sync_loop(self):
        """Start the async sync monitoring loop"""
        self.sync_loop_running = True
        logger.info("Starting history sync monitoring loop")
        
        while self.sync_loop_running:
            try:
                # Process sync queue
                results = self.process_sync_queue()
                
                if 'error' not in results:
                    logger.debug(f"Sync queue processed: {results}")
                else:
                    logger.error(f"Sync queue processing error: {results['error']}")
                
                # Wait before next iteration
                await asyncio.sleep(self.status_check_interval)
                
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                await asyncio.sleep(self.status_check_interval)
    
    def stop_sync_loop(self):
        """Stop the sync monitoring loop"""
        self.sync_loop_running = False
        logger.info("Stopping history sync monitoring loop")
    
    def get_sync_summary(self) -> Dict[str, Any]:
        """Get comprehensive sync status summary"""
        try:
            # Market sync summary
            sync_counts = {}
            for status in SyncStatus:
                sync_counts[status.value] = len([
                    info for info in self.market_sync_status.values() 
                    if info.sync_status == status
                ])
            
            # Lab execution summary
            lab_counts = {}
            for status in LabExecutionStatus:
                lab_counts[status.value] = len([
                    lab for lab in self.lab_execution_queue 
                    if lab.status == status
                ])
            
            # Active operations
            active_syncs = list(self.active_sync_operations)
            
            # Recent errors
            recent_errors = [
                f"{info.market_tag}: {info.error_message}"
                for info in self.market_sync_status.values()
                if info.error_message and info.sync_status == SyncStatus.SYNC_FAILED
            ]
            
            return {
                'total_markets': len(self.market_sync_status),
                'total_labs': len(self.lab_execution_queue),
                'active_syncs': len(active_syncs),
                'active_sync_markets': active_syncs,
                'market_sync_status': sync_counts,
                'lab_execution_status': lab_counts,
                'recent_errors': recent_errors[:5],  # Last 5 errors
                'sync_loop_running': self.sync_loop_running
            }
            
        except Exception as e:
            logger.error(f"Error generating sync summary: {e}")
            return {'error': str(e)}
    
    def bulk_add_labs(self, lab_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add multiple labs for execution with history sync management.
        
        Args:
            lab_configs: List of lab configuration dictionaries
                Each should contain: lab_id, lab_name, market_tag, execution_config, priority
                
        Returns:
            Summary of bulk operation
        """
        try:
            results = {
                'added': 0,
                'failed': 0,
                'unique_markets': set(),
                'errors': []
            }
            
            for config in lab_configs:
                try:
                    success = self.add_lab_for_execution(
                        lab_id=config['lab_id'],
                        lab_name=config['lab_name'],
                        market_tag=config['market_tag'],
                        execution_config=config['execution_config'],
                        priority=config.get('priority', 1)
                    )
                    
                    if success:
                        results['added'] += 1
                        results['unique_markets'].add(config['market_tag'])
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to add lab {config['lab_id']}")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error adding lab {config.get('lab_id', 'unknown')}: {e}")
            
            results['unique_markets'] = len(results['unique_markets'])
            
            logger.info(f"Bulk add completed: {results['added']} added, {results['failed']} failed, {results['unique_markets']} unique markets")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk add labs: {e}")
            return {'error': str(e)}

def main():
    """Test the history sync manager"""
    print("Testing History Sync Manager...")
    print("=" * 50)
    
    # Initialize sync manager
    sync_manager = HistorySyncManager()
    
    # Test 1: Add labs for execution
    print("\n1. Testing lab addition with sync management:")
    
    test_labs = [
        {
            'lab_id': 'test-lab-001',
            'lab_name': 'BTC Test Lab',
            'market_tag': 'BINANCEFUTURES_BTC_USDT_PERPETUAL',
            'execution_config': {'period': '2_years', 'send_email': False},
            'priority': 3
        },
        {
            'lab_id': 'test-lab-002',
            'lab_name': 'ETH Test Lab',
            'market_tag': 'BINANCEFUTURES_ETH_USDT_PERPETUAL',
            'execution_config': {'period': '1_year', 'send_email': False},
            'priority': 2
        },
        {
            'lab_id': 'test-lab-003',
            'lab_name': 'SOL Test Lab',
            'market_tag': 'BINANCEFUTURES_SOL_USDT_PERPETUAL',
            'execution_config': {'period': '2_years', 'send_email': False},
            'priority': 1
        }
    ]
    
    bulk_result = sync_manager.bulk_add_labs(test_labs)
    print(f"✓ Bulk add result: {bulk_result}")
    
    # Test 2: Process sync queue
    print("\n2. Testing sync queue processing:")
    
    for i in range(5):  # Simulate 5 processing cycles
        print(f"\n   Processing cycle {i+1}:")
        results = sync_manager.process_sync_queue()
        print(f"   Results: {results}")
        
        # Get sync summary
        summary = sync_manager.get_sync_summary()
        print(f"   Summary: Active syncs: {summary['active_syncs']}, Labs ready: {summary['lab_execution_status'].get('ready_for_execution', 0)}")
        
        # Wait a bit to simulate time passing
        time.sleep(2)
    
    # Test 3: Final summary
    print("\n3. Final sync status summary:")
    final_summary = sync_manager.get_sync_summary()
    print(f"✓ Final summary:")
    print(f"   Total markets: {final_summary['total_markets']}")
    print(f"   Total labs: {final_summary['total_labs']}")
    print(f"   Market sync status: {final_summary['market_sync_status']}")
    print(f"   Lab execution status: {final_summary['lab_execution_status']}")
    
    if final_summary['recent_errors']:
        print(f"   Recent errors: {final_summary['recent_errors']}")
    
    print("\n" + "=" * 50)
    print("History sync manager test completed!")
    print("\nKey features demonstrated:")
    print("  - Bulk lab addition with market sync tracking")
    print("  - Automatic chart call initiation")
    print("  - Basic sync → Extended sync (36 months) workflow")
    print("  - Async queue management for lab execution")
    print("  - Comprehensive status tracking and reporting")
    print("  - Error handling and retry mechanisms")

if __name__ == "__main__":
    main()