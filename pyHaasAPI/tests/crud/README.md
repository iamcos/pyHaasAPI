# CRUD Testing Framework

Comprehensive CRUD testing framework for pyHaasAPI v2 with field mapping validation, error handling robustness, and cleanup discipline.

## Overview

This testing framework provides comprehensive CRUD (Create, Read, Update, Delete) testing for all pyHaasAPI v2 entities with a focus on:

- **Field Mapping Validation**: Prevents the 50% of runtime errors caused by improper field mapping
- **Error Handling Robustness**: Comprehensive error handling and recovery testing
- **Manager Integration**: Testing of BacktestingManager, BotVerificationManager, and FinetuningManager
- **Cleanup Discipline**: Ensures proper resource cleanup and no leaks
- **v2-Only Runtime**: Enforces v2-only runtime with guards against v1 usage

## Test Structure

```
pyHaasAPI/tests/crud/
├── conftest.py              # Pytest configuration and fixtures
├── helpers.py                # Test utilities and helpers
├── test_lab_crud.py          # Lab CRUD tests
├── test_bot_crud.py          # Bot CRUD tests
├── test_account_crud.py      # Account CRUD tests
├── test_field_mapping_resilience.py  # Field mapping resilience tests
├── test_error_handling_robustness.py # Error handling robustness tests
├── test_manager_integration.py       # Manager integration tests
├── run_crud_tests.py         # Test runner script
├── test_report.py            # Test report generator
└── README.md                 # This file
```

## Key Features

### 1. Field Mapping Validation

Prevents the 50% of runtime errors caused by improper field mapping on API response objects:

- **Safe Field Access**: Uses `getattr()` and `hasattr()` instead of `.get()`
- **Field Validation**: Validates critical fields with proper error handling
- **Resilience Testing**: Tests with missing optional fields
- **No .get() Regressions**: Ensures no `.get()` usage on API objects

### 2. Error Handling Robustness

Comprehensive error handling and recovery testing:

- **Error Message Context**: Ensures error messages include actionable context
- **Retry Mechanisms**: Tests retry logic for transient failures
- **Rate Limit Handling**: Tests rate limit backoff and recovery
- **Error Hierarchy**: Validates proper exception inheritance
- **Graceful Degradation**: Tests system behavior under partial failures

### 3. Manager Integration

Testing of v2-only manager classes:

- **BacktestingManager**: Longest backtest execution and monitoring
- **BotVerificationManager**: Bot configuration verification
- **FinetuningManager**: Lab parameter optimization
- **Error Recovery**: Manager error handling and recovery
- **Performance Metrics**: Manager performance monitoring

### 4. Cleanup Discipline

Ensures proper resource cleanup and no leaks:

- **Session Finalizer**: Automatic cleanup of created resources
- **Tunnel Management**: Proper SSH tunnel cleanup
- **Process Cleanup**: Kills hanging Python processes
- **Resource Tracking**: Registry of created resources for cleanup

## Test Categories

### Lab CRUD Tests (`test_lab_crud.py`)

- **Create**: Lab creation with proper field mapping
- **Read**: Lab details retrieval with safe field access
- **Update**: Lab parameter updates with validation
- **Delete**: Safe lab deletion with job cancellation
- **Edge Cases**: Non-existent labs, invalid parameters
- **Field Mapping**: Safe field access for all lab fields

### Bot CRUD Tests (`test_bot_crud.py`)

- **Create**: Bot creation from lab with proper configuration
- **Read**: Bot details retrieval with field validation
- **Update**: Bot parameter editing with validation
- **Control**: Activation, deactivation, pause, resume workflows
- **Delete**: Safe bot deletion with order cancellation
- **Edge Cases**: Non-existent bots, invalid parameters

### Account CRUD Tests (`test_account_crud.py`)

- **Read**: Account listing and details retrieval
- **Balance**: Account balance and wallet data validation
- **Margin Settings**: Margin configuration management
- **Position/Margin Modes**: Mode setting and validation
- **Leverage**: Leverage setting and validation
- **Field Mapping**: Safe field access for account data

### Field Mapping Resilience Tests (`test_field_mapping_resilience.py`)

- **Lab Field Mapping**: Tests all possible lab fields
- **Bot Field Mapping**: Tests all possible bot fields
- **Account Field Mapping**: Tests all possible account fields
- **Market Field Mapping**: Tests market data fields
- **Backtest Field Mapping**: Tests backtest data fields
- **Script Field Mapping**: Tests script data fields
- **Order Field Mapping**: Tests order data fields
- **No .get() Regressions**: Ensures no `.get()` usage

### Error Handling Robustness Tests (`test_error_handling_robustness.py`)

- **Error Message Context**: Tests error message quality
- **Retry Mechanisms**: Tests retry logic for transient errors
- **Rate Limit Handling**: Tests rate limit backoff
- **Network Error Recovery**: Tests network error handling
- **Validation Error Handling**: Tests input validation
- **Authentication Error Handling**: Tests auth error handling
- **Configuration Error Handling**: Tests config error handling
- **Error Hierarchy**: Tests exception inheritance
- **Concurrent Error Handling**: Tests error handling under load

### Manager Integration Tests (`test_manager_integration.py`)

- **BacktestingManager**: Smoke tests for longest backtest execution
- **BotVerificationManager**: Bot configuration verification tests
- **FinetuningManager**: Lab parameter optimization tests
- **Error Handling**: Manager error handling and recovery
- **Retry Mechanisms**: Manager retry logic testing
- **Progress Tracking**: Manager progress monitoring
- **Configuration Validation**: Manager configuration testing
- **Resource Cleanup**: Manager resource management
- **Concurrent Operations**: Manager concurrent operation testing
- **Performance Metrics**: Manager performance monitoring

## Usage

### Running Tests

#### 1. Manual Test Execution

```bash
# Setup environment
source .venv/bin/activate

# Kill existing processes
timeout 30 pkill -f python || true

# Setup SSH tunnel
ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv03 &

# Run tests
timeout 300 bash -lc 'source .venv/bin/activate && python -m pytest -v pyHaasAPI/tests/crud/'
```

#### 2. Using Test Runner

```bash
# Run comprehensive CRUD tests
python pyHaasAPI/tests/crud/run_crud_tests.py
```

#### 3. Individual Test Categories

```bash
# Run specific test categories
python -m pytest pyHaasAPI/tests/crud/test_lab_crud.py -v
python -m pytest pyHaasAPI/tests/crud/test_bot_crud.py -v
python -m pytest pyHaasAPI/tests/crud/test_account_crud.py -v
python -m pytest pyHaasAPI/tests/crud/test_field_mapping_resilience.py -v
python -m pytest pyHaasAPI/tests/crud/test_error_handling_robustness.py -v
python -m pytest pyHaasAPI/tests/crud/test_manager_integration.py -v
```

### Test Configuration

#### Environment Variables

```bash
# Required environment variables
API_EMAIL=your_email@example.com
API_PASSWORD=your_password

# Optional configuration
API_HOST=127.0.0.1
API_PORT=8090
API_TIMEOUT=30.0
```

#### Pytest Markers

```bash
# Run specific test categories
pytest -m crud                    # All CRUD tests
pytest -m field_mapping          # Field mapping tests
pytest -m error_handling         # Error handling tests
pytest -m manager_integration    # Manager integration tests
pytest -m srv03                # srv03 server tests
```

### Test Report Generation

```bash
# Generate comprehensive test report
python pyHaasAPI/tests/crud/test_report.py

# Generate report from specific test results
python pyHaasAPI/tests/crud/test_report.py test_results.json
```

## Test Fixtures

### Session-Scoped Fixtures

- **`srv03_tunnel`**: Ensures SSH tunnel to srv03 is active
- **`auth_context`**: Provides authenticated API context
- **`cleanup_registry`**: Tracks created resources for cleanup
- **`teardown_cleanup`**: Automatic cleanup of created resources

### Function-Scoped Fixtures

- **`apis`**: Provides initialized API modules
- **`test_timeout`**: Provides timeout protection for individual tests

## Helper Functions

### Field Mapping Helpers

- **`assert_safe_field()`**: Safe field access with type validation
- **`assert_lab_details_integrity()`**: Lab details validation
- **`assert_bot_details_integrity()`**: Bot details validation
- **`assert_account_data_integrity()`**: Account data validation

### Retry and Timeout Helpers

- **`retry_async()`**: Retry mechanism with exponential backoff
- **`await_idle_lab()`**: Wait for lab to become idle
- **`with_alarm()`**: Timeout wrapper for long operations

### Test Data Helpers

- **`generate_test_resource_name()`**: Standardized test resource naming
- **`create_test_lab_config()`**: Test lab configuration
- **`create_test_bot_config()`**: Test bot configuration
- **`log_field_mapping_warnings()`**: Field mapping debugging

## Test Naming Conventions

### Resource Naming

- **Labs**: `TEST v2 CRUD <YYYYMMDD-HHMMSS>`
- **Bots**: `TEST v2 CRUD Bot <n> <YYYYMMDD-HHMMSS>`
- **Accounts**: Use existing accounts (no creation)

### Test Naming

- **Lab Tests**: `test_lab_<operation>_<scenario>`
- **Bot Tests**: `test_bot_<operation>_<scenario>`
- **Account Tests**: `test_account_<operation>_<scenario>`
- **Field Mapping Tests**: `test_<entity>_field_mapping_<scenario>`
- **Error Handling Tests**: `test_<scenario>_error_handling`
- **Manager Tests**: `test_<manager>_<operation>_<scenario>`

## Error Handling

### Expected Errors

- **`LabNotFoundError`**: Non-existent lab operations
- **`BotNotFoundError`**: Non-existent bot operations
- **`AccountNotFoundError`**: Non-existent account operations
- **`ValidationError`**: Invalid input parameters
- **`LabConfigurationError`**: Invalid lab configuration
- **`BotConfigurationError`**: Invalid bot configuration

### Error Recovery

- **Retry Mechanisms**: Automatic retry for transient failures
- **Graceful Degradation**: System continues with partial failures
- **Resource Cleanup**: Proper cleanup even on errors
- **Error Context**: Detailed error messages with recovery suggestions

## Performance Considerations

### Timeouts

- **Test Timeout**: 5 minutes per test (configurable)
- **Operation Timeout**: 30 seconds per operation
- **Tunnel Timeout**: 30 seconds for tunnel establishment
- **Cleanup Timeout**: 30 seconds for resource cleanup

### Resource Management

- **Connection Pooling**: Efficient HTTP connection management
- **Rate Limiting**: Respects API rate limits
- **Memory Management**: Proper cleanup of large datasets
- **Process Management**: Kills hanging processes

## Troubleshooting

### Common Issues

1. **SSH Tunnel Issues**
   ```bash
   # Check tunnel status
   nc -zv 127.0.0.1 8090
   
   # Restart tunnel
   pkill -f 'ssh.*srv03'
   ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv03 &
   ```

2. **Authentication Issues**
   ```bash
   # Check credentials
   echo $API_EMAIL
   echo $API_PASSWORD
   
   # Verify .env file
   cat .env
   ```

3. **Field Mapping Issues**
   ```bash
   # Check for .get() usage
   grep -r "\.get(" pyHaasAPI/tests/crud/
   
   # Verify safe field access
   grep -r "assert_safe_field" pyHaasAPI/tests/crud/
   ```

4. **Cleanup Issues**
   ```bash
   # Kill all Python processes
   pkill -f python
   
   # Check for hanging processes
   ps aux | grep python
   ```

### Debug Mode

```bash
# Run with debug output
python -m pytest pyHaasAPI/tests/crud/ -v -s --tb=short

# Run specific test with debug
python -m pytest pyHaasAPI/tests/crud/test_lab_crud.py::TestLabCRUD::test_lab_create_success -v -s
```

## Contributing

### Adding New Tests

1. **Follow Naming Conventions**: Use descriptive test names
2. **Use Helper Functions**: Leverage existing helper functions
3. **Add Field Mapping**: Include field mapping validation
4. **Test Error Cases**: Include error handling tests
5. **Cleanup Resources**: Ensure proper resource cleanup

### Test Structure

```python
@pytest.mark.crud
@pytest.mark.srv03
class TestNewFeature:
    """Test new feature functionality"""
    
    async def test_new_feature_success(self, apis, cleanup_registry, test_session_id):
        """Test successful new feature operation"""
        # Test implementation
        pass
    
    async def test_new_feature_error_handling(self, apis):
        """Test new feature error handling"""
        # Error handling test
        pass
```

### Field Mapping Guidelines

```python
# Always use safe field access
value = assert_safe_field(obj, 'field_name', str, required=True)

# Never use .get() on API objects
# ❌ WRONG
value = obj.get('field_name', default)

# ✅ CORRECT
value = assert_safe_field(obj, 'field_name', str, required=False)
```

## License

This testing framework is part of the pyHaasAPI project and follows the same license terms.
