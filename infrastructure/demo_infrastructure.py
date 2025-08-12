#!/usr/bin/env python3
"""
Infrastructure System Demo

This script demonstrates the core infrastructure components working together.
"""

import os
import json
import time
import tempfile
from server_manager import ServerManager
from config_manager import ConfigManager
from error_handler import GracefulErrorHandler, ErrorCategory, retry_on_error, RetryConfig

def demo_config_management():
    """Demonstrate configuration management"""
    print("=== Configuration Management Demo ===")
    
    # Create configuration manager
    config_manager = ConfigManager()
    
    print("✓ Created default configuration")
    print(f"  - Default lab max population: {config_manager.get_lab_config().max_population}")
    print(f"  - Default account balance: {config_manager.get_account_settings().initial_balance}")
    print(f"  - Number of servers: {len(config_manager.get_all_server_configs())}")
    
    # Update configuration
    config_manager.update_lab_config(max_population=75, max_generations=150)
    config_manager.update_account_settings(initial_balance=15000.0)
    
    print("✓ Updated configuration")
    print(f"  - New lab max population: {config_manager.get_lab_config().max_population}")
    print(f"  - New account balance: {config_manager.get_account_settings().initial_balance}")
    
    # Validate configuration
    issues = config_manager.validate_config()
    if issues:
        print(f"⚠ Configuration issues found: {issues}")
    else:
        print("✓ Configuration is valid")
    
    # Save configuration
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.close()
    
    config_manager.save_config(temp_file.name)
    print(f"✓ Configuration saved to {temp_file.name}")
    
    # Load configuration
    config_manager2 = ConfigManager(temp_file.name)
    print("✓ Configuration loaded successfully")
    print(f"  - Loaded lab max population: {config_manager2.get_lab_config().max_population}")
    
    # Cleanup
    os.unlink(temp_file.name)
    print()

def demo_error_handling():
    """Demonstrate error handling and retry mechanisms"""
    print("=== Error Handling Demo ===")
    
    # Create error handler
    handler = GracefulErrorHandler()
    
    # Register fallback handler
    def connection_fallback(error, context):
        return f"Fallback: Using cached data from {context.get('operation', 'unknown')}"
    
    handler.register_fallback_handler(ErrorCategory.CONNECTION, connection_fallback)
    print("✓ Registered connection error fallback handler")
    
    # Simulate connection error
    try:
        raise ConnectionError("Server unreachable")
    except Exception as e:
        result = handler.handle_error(e, {'operation': 'fetch_data'})
        print(f"✓ Handled connection error gracefully: {result}")
    
    # Demonstrate retry decorator
    attempt_count = 0
    
    @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.1))
    def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count < 3:
            raise ConnectionError(f"Simulated failure {attempt_count}")
        
        return f"Success after {attempt_count} attempts"
    
    print("✓ Testing retry decorator...")
    try:
        result = flaky_operation()
        print(f"✓ Retry successful: {result}")
    except Exception as e:
        print(f"✗ Retry failed: {e}")
    
    # Get error statistics
    stats = handler.error_tracker.get_error_statistics()
    print(f"✓ Error statistics: {stats['total_errors']} total errors recorded")
    print()

def demo_server_management():
    """Demonstrate server management (without actual connections)"""
    print("=== Server Management Demo ===")
    
    # Create test configuration
    test_config = {
        "servers": {
            "demo_srv01": {
                "host": "demo-server-01",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 50,
                "max_concurrent_tasks": 5,
                "role": "backtest",
                "ssh_user": "demo"
            },
            "demo_srv02": {
                "host": "demo-server-02",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 30,
                "max_concurrent_tasks": 3,
                "role": "development",
                "ssh_user": "demo"
            }
        }
    }
    
    # Save test configuration
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(test_config, temp_file)
    temp_file.close()
    
    try:
        # Create server manager
        server_manager = ServerManager(temp_file.name)
        print(f"✓ Loaded server configuration with {len(server_manager.server_configs)} servers")
        
        # Generate status report
        report = server_manager.get_server_status_report()
        print("✓ Generated server status report:")
        print(f"  - Total servers: {report['total_servers']}")
        print(f"  - Server IDs: {list(report['servers'].keys())}")
        
        # Test connection simulation (will fail gracefully)
        print("✓ Testing connection simulation...")
        try:
            # This will fail since we don't have real servers
            server_manager.connect_to_server("demo_srv01")
        except Exception as e:
            print(f"  - Expected connection failure (no real servers): {type(e).__name__}")
        
        # Test API request simulation
        print("✓ Testing API request simulation...")
        result = server_manager.execute_api_request("demo_srv01", "/api/test")
        if result is None:
            print("  - Expected API failure (no real servers)")
        
    finally:
        # Cleanup
        os.unlink(temp_file.name)
    
    print()

def demo_integration():
    """Demonstrate integration between components"""
    print("=== Integration Demo ===")
    
    # Create integrated system
    config_manager = ConfigManager()
    error_handler = GracefulErrorHandler()
    
    # Register error handlers for different scenarios
    def config_fallback(error, context):
        return "Using default configuration"
    
    def server_fallback(error, context):
        return "Using local processing mode"
    
    error_handler.register_fallback_handler(ErrorCategory.CONFIGURATION, config_fallback)
    error_handler.register_fallback_handler(ErrorCategory.CONNECTION, server_fallback)
    
    print("✓ Integrated system components")
    print("✓ Registered fallback handlers for different error types")
    
    # Simulate system operations with error handling
    operations = [
        ("load_config", lambda: config_manager.get_lab_config()),
        ("connect_server", lambda: (_ for _ in ()).throw(ConnectionError("Server down"))),
        ("process_data", lambda: "Data processed successfully")
    ]
    
    results = []
    for op_name, operation in operations:
        try:
            result = operation()
            results.append(f"✓ {op_name}: {result}")
        except Exception as e:
            fallback_result = error_handler.handle_error(e, {'operation': op_name})
            results.append(f"⚠ {op_name}: {fallback_result} (fallback)")
    
    print("✓ System operations completed:")
    for result in results:
        print(f"  - {result}")
    
    print()

def main():
    """Run infrastructure demo"""
    print("Infrastructure System Demonstration")
    print("=" * 50)
    print()
    
    try:
        demo_config_management()
        demo_error_handling()
        demo_server_management()
        demo_integration()
        
        print("=" * 50)
        print("✓ All infrastructure components demonstrated successfully!")
        print()
        print("Key Features Demonstrated:")
        print("  - Configuration management with validation and persistence")
        print("  - Error classification and graceful handling")
        print("  - Retry mechanisms with exponential backoff")
        print("  - Server connection management framework")
        print("  - Integrated error recovery workflows")
        print()
        print("The infrastructure is ready for:")
        print("  - Multi-server SSH tunnel management")
        print("  - Distributed lab backtesting coordination")
        print("  - Robust error handling and recovery")
        print("  - Flexible configuration management")
        
    except Exception as e:
        print(f"✗ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()