"""
Demonstration of the backtest execution and monitoring system.

This example shows how to:
1. Configure and execute backtests
2. Monitor execution progress in real-time
3. Manage backtest lifecycle (archive, delete, cleanup)
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from ..backtest_manager import BacktestManager
from ..models import BacktestConfig, PositionMode
from ..config import ConfigManager
from ..api_client import HaasOnlineClient
from ..backtest_manager.execution_monitor import MonitoringEventType


class BacktestExecutionDemo:
    """Demonstration of backtest execution and monitoring capabilities."""
    
    def __init__(self):
        """Initialize the demo with configuration."""
        # Initialize configuration (in real usage, load from config files)
        self.config_manager = ConfigManager()
        
        # Initialize API client (in real usage, use actual credentials)
        self.api_client = HaasOnlineClient(self.config_manager.haasonline)
        
        # Initialize backtest manager
        self.backtest_manager = BacktestManager(self.config_manager, self.api_client)
        
        # Register event callbacks for monitoring
        self._setup_monitoring_callbacks()
        
        print("🚀 Backtest Execution Demo initialized")
    
    def _setup_monitoring_callbacks(self):
        """Setup monitoring event callbacks."""
        
        def on_execution_started(execution):
            print(f"✅ Execution started: {execution.backtest_id}")
            print(f"   Script: {execution.script_id}")
            print(f"   Market: {execution.config.market_tag}")
        
        def on_execution_completed(execution):
            print(f"🎉 Execution completed: {execution.backtest_id}")
            print(f"   Duration: {execution.duration}")
            print(f"   Final status: {execution.status.status.value}")
        
        def on_execution_failed(execution):
            print(f"❌ Execution failed: {execution.backtest_id}")
            print(f"   Error: {execution.error_message}")
        
        def on_execution_progress(execution):
            print(f"📊 Progress update: {execution.backtest_id}")
            print(f"   Progress: {execution.status.progress_percentage:.1f}%")
            print(f"   Phase: {execution.status.current_phase}")
        
        # Register callbacks
        self.backtest_manager.register_monitoring_callback(
            MonitoringEventType.EXECUTION_STARTED, on_execution_started
        )
        self.backtest_manager.register_monitoring_callback(
            MonitoringEventType.EXECUTION_COMPLETED, on_execution_completed
        )
        self.backtest_manager.register_monitoring_callback(
            MonitoringEventType.EXECUTION_FAILED, on_execution_failed
        )
        self.backtest_manager.register_monitoring_callback(
            MonitoringEventType.EXECUTION_PROGRESS, on_execution_progress
        )
    
    def create_sample_backtest_config(self, script_id: str, market: str = "BTCUSDT") -> BacktestConfig:
        """Create a sample backtest configuration."""
        return BacktestConfig(
            script_id=script_id,
            account_id="demo_account_123",
            market_tag=market,
            start_time=int((datetime.now() - timedelta(days=30)).timestamp()),
            end_time=int((datetime.now() - timedelta(days=1)).timestamp()),
            interval=60,  # 1-hour candles
            execution_amount=1000.0,
            script_parameters={
                "fast_ma_period": 12,
                "slow_ma_period": 26,
                "signal_period": 9,
                "risk_percentage": 2.0
            },
            leverage=1,
            position_mode=PositionMode.LONG_ONLY,
            slippage=0.1,
            commission=0.1
        )
    
    def demo_basic_execution(self):
        """Demonstrate basic backtest execution."""
        print("\n" + "="*60)
        print("🔥 DEMO: Basic Backtest Execution")
        print("="*60)
        
        # Create backtest configuration
        config = self.create_sample_backtest_config("macd_strategy_v1")
        
        try:
            # Execute backtest
            print("📋 Executing backtest...")
            execution = self.backtest_manager.execute_backtest(config)
            
            print(f"✅ Backtest queued successfully!")
            print(f"   Backtest ID: {execution.backtest_id}")
            print(f"   Status: {execution.status.status.value}")
            print(f"   Estimated completion: {execution.status.estimated_completion}")
            
            return execution.backtest_id
            
        except Exception as e:
            print(f"❌ Failed to execute backtest: {e}")
            return None
    
    def demo_execution_monitoring(self, backtest_id: str):
        """Demonstrate execution monitoring."""
        print("\n" + "="*60)
        print("📊 DEMO: Execution Monitoring")
        print("="*60)
        
        print(f"🔍 Monitoring backtest: {backtest_id}")
        
        # Monitor for a few iterations
        for i in range(5):
            try:
                # Get current status
                status = self.backtest_manager.monitor_execution(backtest_id)
                
                print(f"\n📈 Status Update #{i+1}:")
                print(f"   Status: {status.status.value}")
                print(f"   Progress: {status.progress_percentage:.1f}%")
                print(f"   Phase: {status.current_phase}")
                print(f"   CPU Usage: {status.resource_usage.cpu_percent:.1f}%")
                print(f"   Memory Usage: {status.resource_usage.memory_mb:.1f} MB")
                
                if status.estimated_completion:
                    remaining = status.estimated_completion - datetime.now()
                    print(f"   Estimated remaining: {remaining}")
                
                # Break if completed
                if status.is_complete or status.has_failed:
                    print(f"🏁 Execution finished with status: {status.status.value}")
                    break
                
                # Wait before next check
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Error monitoring execution: {e}")
                break
    
    def demo_dashboard_data(self):
        """Demonstrate dashboard data retrieval."""
        print("\n" + "="*60)
        print("📊 DEMO: Dashboard Data")
        print("="*60)
        
        try:
            # Get dashboard data
            dashboard_data = self.backtest_manager.get_dashboard_data()
            
            print("📋 Dashboard Summary:")
            summary = dashboard_data.get("summary", {})
            print(f"   Total executions: {summary.get('total_executions', 0)}")
            print(f"   Running: {summary.get('running', 0)}")
            print(f"   Completed: {summary.get('completed', 0)}")
            print(f"   Failed: {summary.get('failed', 0)}")
            
            # Show recent events
            recent_events = dashboard_data.get("recent_events", [])
            if recent_events:
                print(f"\n📝 Recent Events ({len(recent_events)}):")
                for event in recent_events[-3:]:  # Show last 3 events
                    print(f"   {event.timestamp.strftime('%H:%M:%S')} - {event.event_type.value}")
                    print(f"     {event.message}")
            
            # Show queue status
            queue_status = self.backtest_manager.get_queue_status()
            print(f"\n🔄 Queue Status:")
            print(f"   Active executions: {queue_status['active_executions']}")
            print(f"   Queued executions: {queue_status['queued_executions']}")
            print(f"   Max concurrent: {queue_status['max_concurrent']}")
            
        except Exception as e:
            print(f"❌ Error retrieving dashboard data: {e}")
    
    def demo_lifecycle_management(self):
        """Demonstrate backtest lifecycle management."""
        print("\n" + "="*60)
        print("🔄 DEMO: Lifecycle Management")
        print("="*60)
        
        # Get execution history
        print("📚 Execution History:")
        try:
            history = self.backtest_manager.get_execution_history(limit=5)
            print(f"   Found {len(history)} historical executions")
            
            for summary in history:
                print(f"   - {summary.backtest_id}: {summary.status} ({summary.market_tag})")
                print(f"     Created: {summary.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        except Exception as e:
            print(f"❌ Error retrieving history: {e}")
        
        # Show retention status
        print("\n🗄️ Retention Status:")
        try:
            retention_status = self.backtest_manager.get_backtest_retention_status()
            
            print(f"   Total executions: {retention_status['total_executions']}")
            print(f"   Completed executions: {retention_status['completed_executions']}")
            print(f"   Old executions needing cleanup: {retention_status['old_executions_needing_cleanup']}")
            print(f"   Estimated storage: {retention_status['estimated_storage_mb']} MB")
            print(f"   Cleanup recommended: {retention_status['cleanup_recommended']}")
            
        except Exception as e:
            print(f"❌ Error retrieving retention status: {e}")
        
        # Demonstrate bulk operations
        print("\n🧹 Bulk Operations:")
        try:
            # Bulk archive completed backtests
            archive_result = self.backtest_manager.bulk_archive_completed(older_than_hours=48)
            print(f"   Bulk archive result: {archive_result}")
            
            # Cleanup old executions
            cleanup_result = self.backtest_manager.cleanup_completed_executions(
                max_age_hours=72, 
                archive_before_delete=True
            )
            print(f"   Cleanup result: {cleanup_result}")
            
        except Exception as e:
            print(f"❌ Error in bulk operations: {e}")
    
    def demo_concurrent_executions(self):
        """Demonstrate concurrent execution management."""
        print("\n" + "="*60)
        print("🚀 DEMO: Concurrent Executions")
        print("="*60)
        
        backtest_ids = []
        
        # Start multiple backtests
        markets = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        for i, market in enumerate(markets):
            try:
                config = self.create_sample_backtest_config(f"strategy_{i+1}", market)
                execution = self.backtest_manager.execute_backtest(config)
                backtest_ids.append(execution.backtest_id)
                
                print(f"✅ Started backtest {i+1}: {execution.backtest_id} ({market})")
                
            except Exception as e:
                print(f"❌ Failed to start backtest {i+1}: {e}")
        
        # Monitor all executions
        print(f"\n📊 Monitoring {len(backtest_ids)} concurrent executions...")
        
        for _ in range(3):  # Monitor for 3 iterations
            print(f"\n--- Status Check ---")
            
            for backtest_id in backtest_ids:
                try:
                    progress = self.backtest_manager.get_execution_progress(backtest_id)
                    if progress:
                        execution = progress["execution"]
                        progress_info = progress["progress"]
                        
                        print(f"   {backtest_id[:8]}... - {execution.status.progress_percentage:.1f}% - {execution.status.current_phase}")
                
                except Exception as e:
                    print(f"   {backtest_id[:8]}... - Error: {e}")
            
            time.sleep(15)  # Wait between checks
        
        return backtest_ids
    
    def run_full_demo(self):
        """Run the complete demonstration."""
        print("🎬 Starting Backtest Execution and Monitoring Demo")
        print("="*80)
        
        try:
            # Demo 1: Basic execution
            backtest_id = self.demo_basic_execution()
            
            if backtest_id:
                # Demo 2: Monitoring
                self.demo_execution_monitoring(backtest_id)
            
            # Demo 3: Dashboard data
            self.demo_dashboard_data()
            
            # Demo 4: Lifecycle management
            self.demo_lifecycle_management()
            
            # Demo 5: Concurrent executions
            concurrent_ids = self.demo_concurrent_executions()
            
            print("\n" + "="*80)
            print("🎉 Demo completed successfully!")
            print("="*80)
            
            return {
                "single_backtest_id": backtest_id,
                "concurrent_backtest_ids": concurrent_ids
            }
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            return None
        
        finally:
            # Cleanup
            print("\n🧹 Cleaning up...")
            self.backtest_manager.stop_monitoring()
            print("✅ Cleanup completed")


def main():
    """Main function to run the demo."""
    demo = BacktestExecutionDemo()
    
    try:
        results = demo.run_full_demo()
        
        if results:
            print(f"\n📋 Demo Results:")
            print(f"   Single backtest: {results.get('single_backtest_id', 'None')}")
            print(f"   Concurrent backtests: {len(results.get('concurrent_backtest_ids', []))}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo crashed: {e}")
    finally:
        print("\n👋 Demo finished")


if __name__ == "__main__":
    main()