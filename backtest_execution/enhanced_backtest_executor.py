#!/usr/bin/env python3
"""
Enhanced Backtest Executor with History Sync Management
This module provides an enhanced backtest execution system that properly handles
history synchronization before starting backtests, ensuring reliable execution.
"""

import asyncio
import logging
import time
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json

from history_sync_manager import HistorySyncManager, LabSyncRequest, SyncStatus
from lab_configuration.lab_configurator import LabConfiguration, LabConfigurator

logger = logging.getLogger(__name__)

@dataclass
class EnhancedExecutionRequest:
    """Enhanced execution request with sync management"""
    lab_id: str
    lab_name: str
    lab_configuration: LabConfiguration
    execution_config: Dict[str, Any]
    priority: int = 1
    requires_sync: bool = True
    created_time: float = None
    
    def __post_init__(self):
        if self.created_time is None:
            self.created_time = time.time()

class EnhancedBacktestExecutor:
    """Enhanced backtest executor with history sync management"""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        self.session = requests.Session()
        
        # Initialize history sync manager
        self.sync_manager = HistorySyncManager(mcp_base_url)
        
        # Initialize lab configurator for MCP integration
        self.lab_configurator = LabConfigurator()
        
        # Execution tracking
        self.execution_requests: Dict[str, EnhancedExecutionRequest] = {}
        self.completed_executions: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.max_concurrent_lab_creations = 10
        self.lab_creation_delay = 0.5  # seconds between lab creations
        
        # Thread pool for concurrent operations
        self.executor_pool = ThreadPoolExecutor(max_workers=15)
        
        # Control flags
        self.sync_loop_task = None
        self.is_running = False
    
    async def start_enhanced_execution_system(self):
        """Start the enhanced execution system with sync management"""
        if self.is_running:
            logger.warning("Enhanced execution system is already running")
            return
        
        self.is_running = True
        logger.info("Starting enhanced backtest execution system with history sync")
        
        # Start the sync manager loop
        self.sync_loop_task = asyncio.create_task(self.sync_manager.start_sync_loop())
        
        logger.info("Enhanced execution system started successfully")
    
    async def stop_enhanced_execution_system(self):
        """Stop the enhanced execution system"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping enhanced backtest execution system")
        
        # Stop sync manager
        self.sync_manager.stop_sync_loop()
        
        # Cancel sync loop task
        if self.sync_loop_task:
            self.sync_loop_task.cancel()
            try:
                await self.sync_loop_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Enhanced execution system stopped")
    
    def submit_lab_for_execution(self, lab_configuration: LabConfiguration, 
                                execution_config: Dict[str, Any], priority: int = 1) -> str:
        """
        Submit a lab for execution with automatic history sync management.
        
        Args:
            lab_configuration: Lab configuration
            execution_config: Execution configuration (period, send_email, etc.)
            priority: Execution priority
            
        Returns:
            Request ID for tracking
        """
        try:
            request_id = f"req_{lab_configuration.lab_id}_{int(time.time())}"
            
            # Create enhanced execution request
            request = EnhancedExecutionRequest(
                lab_id=lab_configuration.lab_id,
                lab_name=lab_configuration.lab_name,
                lab_configuration=lab_configuration,
                execution_config=execution_config,
                priority=priority
            )
            
            # Store request
            self.execution_requests[request_id] = request
            
            # Add to sync manager for history sync and execution
            success = self.sync_manager.add_lab_for_execution(
                lab_id=lab_configuration.lab_id,
                lab_name=lab_configuration.lab_name,
                market_tag=lab_configuration.market_config.market_tag,
                execution_config=execution_config,
                priority=priority
            )
            
            if success:
                logger.info(f"Submitted lab {lab_configuration.lab_id} for execution with sync management")
                return request_id
            else:
                logger.error(f"Failed to submit lab {lab_configuration.lab_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting lab for execution: {e}")
            return None
    
    def bulk_create_and_execute_labs(self, source_lab_id: str, target_assets: List[str], 
                                   execution_config: Dict[str, Any], priority: int = 1) -> Dict[str, Any]:
        """
        Create multiple labs from a source and execute them with proper sync management.
        
        This implements the workflow you described:
        1. Create labs for each asset
        2. Make chart calls (don't wait for results)
        3. Check basic sync completion
        4. Upgrade to 36-month sync
        5. Start backtest once sync is complete
        
        Args:
            source_lab_id: Source lab to clone from
            target_assets: List of assets to create labs for
            execution_config: Execution configuration
            priority: Execution priority
            
        Returns:
            Summary of bulk operation
        """
        try:
            logger.info(f"Starting bulk create and execute for {len(target_assets)} assets from lab {source_lab_id}")
            
            results = {
                'total_assets': len(target_assets),
                'labs_created': 0,
                'labs_queued_for_sync': 0,
                'sync_operations_started': 0,
                'failed_operations': 0,
                'created_labs': [],
                'errors': []
            }
            
            # Step 1: Clone lab to multiple markets via MCP server
            clone_payload = {
                "source_lab_id": source_lab_id,
                "targets": [{"asset": asset, "exchange": "BINANCEFUTURES"} for asset in target_assets],
                "lab_name_template": "Auto Strategy - {primary} - {suffix}"
            }
            
            clone_response = self.session.post(
                f"{self.mcp_base_url}/clone_lab_to_markets",
                json=clone_payload
            )
            
            if clone_response.status_code == 200:
                clone_data = clone_response.json()
                if clone_data.get("Success"):
                    created_labs = clone_data["Data"]["labs"]
                    results['labs_created'] = len(created_labs)
                    results['created_labs'] = list(created_labs.keys())
                    
                    logger.info(f"Successfully created {len(created_labs)} labs")
                    
                    # Step 2: Add all created labs to sync manager
                    lab_configs = []
                    for lab_id, lab_info in created_labs.items():
                        # Determine market tag from lab info
                        target_info = lab_info.get("target", {})
                        asset = target_info.get("asset", "UNKNOWN")
                        exchange = target_info.get("exchange", "BINANCEFUTURES")
                        quote = target_info.get("quote_asset", "USDT")
                        contract = target_info.get("contract_type", "PERPETUAL")
                        
                        market_tag = f"{exchange}_{asset}_{quote}_{contract}"
                        
                        lab_configs.append({
                            'lab_id': lab_id,
                            'lab_name': lab_info.get("lab_name", f"Auto Strategy - {asset}"),
                            'market_tag': market_tag,
                            'execution_config': execution_config,
                            'priority': priority
                        })
                    
                    # Step 3: Bulk add to sync manager (this starts chart calls automatically)
                    sync_results = self.sync_manager.bulk_add_labs(lab_configs)
                    results['labs_queued_for_sync'] = sync_results.get('added', 0)
                    results['failed_operations'] = sync_results.get('failed', 0)
                    
                    if sync_results.get('errors'):
                        results['errors'].extend(sync_results['errors'])
                    
                    logger.info(f"Added {results['labs_queued_for_sync']} labs to sync queue")
                    
                else:
                    error_msg = f"MCP server error cloning labs: {clone_data.get('Error', 'Unknown error')}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            else:
                error_msg = f"HTTP error cloning labs: {clone_response.status_code}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
            
            # The sync manager will now handle:
            # - Chart calls for each market (automatic)
            # - Basic sync monitoring
            # - Extended sync (36 months) once basic sync completes
            # - Lab execution once extended sync completes
            
            logger.info(f"Bulk operation completed: {results}")
            return results
            
        except Exception as e:
            error_msg = f"Error in bulk create and execute: {e}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'total_assets': len(target_assets),
                'labs_created': 0,
                'labs_queued_for_sync': 0,
                'failed_operations': len(target_assets)
            }
    
    def create_single_lab_with_sync(self, script_id: str, account_id: str, market_tag: str,
                                  lab_name: str, execution_config: Dict[str, Any], 
                                  priority: int = 1) -> Dict[str, Any]:
        """
        Create a single lab and add it to sync management.
        
        Args:
            script_id: Script ID to use
            account_id: Account ID to use
            market_tag: Market tag (e.g., BINANCEFUTURES_BTC_USDT_PERPETUAL)
            lab_name: Name for the lab
            execution_config: Execution configuration
            priority: Execution priority
            
        Returns:
            Operation result
        """
        try:
            # Parse market tag for lab creation
            parts = market_tag.split('_')
            if len(parts) >= 3:
                exchange = parts[0]
                primary = parts[1]
                secondary = parts[2]
            else:
                return {'error': f'Invalid market tag format: {market_tag}'}
            
            # Create lab via MCP server
            create_payload = {
                "script_id": script_id,
                "account_id": account_id,
                "market_category": "PERPETUAL" if "PERPETUAL" in market_tag else "SPOT",
                "market_price_source": exchange,
                "market_primary": primary,
                "market_secondary": secondary,
                "exchange_code": exchange,
                "interval": 15,
                "default_price_data_style": "CandleStick"
            }
            
            create_response = self.session.post(
                f"{self.mcp_base_url}/create_lab",
                json=create_payload
            )
            
            if create_response.status_code == 200:
                create_data = create_response.json()
                lab_id = create_data.get("lab_id")
                
                if lab_id:
                    # Add to sync manager
                    success = self.sync_manager.add_lab_for_execution(
                        lab_id=lab_id,
                        lab_name=lab_name,
                        market_tag=market_tag,
                        execution_config=execution_config,
                        priority=priority
                    )
                    
                    if success:
                        return {
                            'success': True,
                            'lab_id': lab_id,
                            'lab_name': lab_name,
                            'market_tag': market_tag,
                            'message': 'Lab created and queued for sync'
                        }
                    else:
                        return {'error': 'Failed to add lab to sync queue'}
                else:
                    return {'error': 'No lab ID returned from MCP server'}
            else:
                return {'error': f'HTTP error creating lab: {create_response.status_code}'}
                
        except Exception as e:
            return {'error': f'Exception creating lab: {e}'}
    
    def get_execution_status(self, request_id: str = None, lab_id: str = None) -> Dict[str, Any]:
        """
        Get execution status for a request or lab.
        
        Args:
            request_id: Request ID to check
            lab_id: Lab ID to check
            
        Returns:
            Status information
        """
        try:
            if request_id and request_id in self.execution_requests:
                request = self.execution_requests[request_id]
                lab_id = request.lab_id
            
            if not lab_id:
                return {'error': 'No lab ID provided or found'}
            
            # Check sync manager for lab status
            for lab_request in self.sync_manager.lab_execution_queue:
                if lab_request.lab_id == lab_id:
                    market_sync_info = self.sync_manager.market_sync_status.get(lab_request.market_tag)
                    
                    return {
                        'lab_id': lab_id,
                        'lab_name': lab_request.lab_name,
                        'market_tag': lab_request.market_tag,
                        'lab_status': lab_request.status.value,
                        'sync_status': market_sync_info.sync_status.value if market_sync_info else 'unknown',
                        'priority': lab_request.priority,
                        'created_time': lab_request.created_time
                    }
            
            # Check if completed
            if lab_id in self.completed_executions:
                return {
                    'lab_id': lab_id,
                    'status': 'completed',
                    'result': self.completed_executions[lab_id]
                }
            
            return {'error': f'Lab {lab_id} not found in execution system'}
            
        except Exception as e:
            return {'error': f'Error getting execution status: {e}'}
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the enhanced execution system"""
        try:
            # Get sync manager summary
            sync_summary = self.sync_manager.get_sync_summary()
            
            # Get execution request summary
            request_summary = {
                'total_requests': len(self.execution_requests),
                'completed_executions': len(self.completed_executions)
            }
            
            # Combine summaries
            return {
                'system_running': self.is_running,
                'sync_manager': sync_summary,
                'execution_requests': request_summary,
                'mcp_base_url': self.mcp_base_url
            }
            
        except Exception as e:
            return {'error': f'Error getting comprehensive status: {e}'}
    
    def monitor_and_report_progress(self) -> Dict[str, Any]:
        """Monitor and report progress of all operations"""
        try:
            status = self.get_comprehensive_status()
            
            # Format for easy reading
            report = {
                'timestamp': time.time(),
                'system_status': 'running' if status['system_running'] else 'stopped',
                'sync_operations': {
                    'total_markets': status['sync_manager']['total_markets'],
                    'active_syncs': status['sync_manager']['active_syncs'],
                    'completed_syncs': status['sync_manager']['market_sync_status'].get('extended_sync_complete', 0)
                },
                'lab_operations': {
                    'total_labs': status['sync_manager']['total_labs'],
                    'waiting_for_sync': status['sync_manager']['lab_execution_status'].get('waiting_for_sync', 0),
                    'ready_for_execution': status['sync_manager']['lab_execution_status'].get('ready_for_execution', 0),
                    'execution_started': status['sync_manager']['lab_execution_status'].get('execution_started', 0)
                },
                'recent_errors': status['sync_manager'].get('recent_errors', [])
            }
            
            return report
            
        except Exception as e:
            return {'error': f'Error monitoring progress: {e}'}

async def main():
    """Test the enhanced backtest executor"""
    print("Testing Enhanced Backtest Executor with History Sync...")
    print("=" * 60)
    
    # Initialize enhanced executor
    executor = EnhancedBacktestExecutor()
    
    try:
        # Start the enhanced system
        print("\n1. Starting enhanced execution system...")
        await executor.start_enhanced_execution_system()
        print("✓ Enhanced execution system started")
        
        # Test bulk create and execute
        print("\n2. Testing bulk create and execute with sync management...")
        
        # Use a real lab ID from your system
        source_lab_id = "7e39fd98-ad7c-4753-8802-c19b2ab11c31"  # Example_BTC_USDT_3mnth
        target_assets = ["BTC", "ETH", "SOL"]
        execution_config = {
            "period": "2_years",
            "send_email": False
        }
        
        bulk_result = executor.bulk_create_and_execute_labs(
            source_lab_id=source_lab_id,
            target_assets=target_assets,
            execution_config=execution_config,
            priority=2
        )
        
        print(f"✓ Bulk operation result: {bulk_result}")
        
        # Monitor progress for a while
        print("\n3. Monitoring progress...")
        
        for i in range(10):  # Monitor for 10 cycles
            await asyncio.sleep(3)  # Wait 3 seconds between checks
            
            progress = executor.monitor_and_report_progress()
            print(f"\n   Progress Report {i+1}:")
            print(f"   System: {progress.get('system_status', 'unknown')}")
            print(f"   Active syncs: {progress.get('sync_operations', {}).get('active_syncs', 0)}")
            print(f"   Labs waiting for sync: {progress.get('lab_operations', {}).get('waiting_for_sync', 0)}")
            print(f"   Labs ready for execution: {progress.get('lab_operations', {}).get('ready_for_execution', 0)}")
            print(f"   Labs executing: {progress.get('lab_operations', {}).get('execution_started', 0)}")
            
            if progress.get('recent_errors'):
                print(f"   Recent errors: {progress['recent_errors'][:2]}")
        
        # Final status
        print("\n4. Final comprehensive status:")
        final_status = executor.get_comprehensive_status()
        print(f"✓ Final status: {final_status}")
        
    finally:
        # Stop the system
        print("\n5. Stopping enhanced execution system...")
        await executor.stop_enhanced_execution_system()
        print("✓ Enhanced execution system stopped")
    
    print("\n" + "=" * 60)
    print("Enhanced backtest executor test completed!")
    print("\nKey features demonstrated:")
    print("  - Bulk lab creation with automatic sync management")
    print("  - Chart call initiation (simulated)")
    print("  - Basic sync → Extended sync (36 months) workflow")
    print("  - Async queue management for lab execution")
    print("  - Comprehensive progress monitoring")
    print("  - Integration with MCP server for real operations")

if __name__ == "__main__":
    asyncio.run(main())