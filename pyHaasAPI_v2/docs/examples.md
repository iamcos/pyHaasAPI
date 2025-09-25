# Examples

This document provides comprehensive examples for using pyHaasAPI v2 in various scenarios.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Service Layer Examples](#service-layer-examples)
- [CLI Examples](#cli-examples)
- [Advanced Examples](#advanced-examples)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Testing Examples](#testing-examples)

## Basic Usage

### Simple Client Setup

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager

async def main():
    # Create client and authenticate
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    
    # Authenticate
    await auth_manager.authenticate()
    
    # Use the client
    labs = await client.get_labs()
    print(f"Found {len(labs)} labs")

# Run the async function
asyncio.run(main())
```

### Using API Modules Directly

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.api import LabAPI, BotAPI

async def main():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create API instances
    lab_api = LabAPI(client)
    bot_api = BotAPI(client)
    
    # Get labs
    labs = await lab_api.get_labs()
    print(f"Found {len(labs)} labs")
    
    # Get bots
    bots = await bot_api.get_all_bots()
    print(f"Found {len(bots)} bots")

asyncio.run(main())
```

### Type-Safe Operations

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.core.type_validation import TypeValidator
from pyHaasAPI_v2.core.type_definitions import LabID, BotID

async def main():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Type validation
    validator = TypeValidator()
    
    # Validate lab ID
    lab_id: LabID = "lab_123"
    result = validator.validate_type(lab_id, LabID)
    if result.is_valid:
        print(f"Valid lab ID: {result.validated_value}")
    
    # Validate bot ID
    bot_id: BotID = "bot_456"
    result = validator.validate_type(bot_id, BotID)
    if result.is_valid:
        print(f"Valid bot ID: {result.validated_value}")

asyncio.run(main())
```

## Service Layer Examples

### Lab Management

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import LabService

async def main():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create lab service
    lab_service = LabService(client, auth_manager)
    
    # Create a new lab
    result = await lab_service.create_lab(
        name="Test Lab",
        script_id="script_123",
        description="A test lab for development"
    )
    
    if result.success:
        lab_id = result.data["lab_id"]
        print(f"Created lab: {lab_id}")
        
        # Execute the lab
        execution_result = await lab_service.execute_lab(lab_id)
        if execution_result.success:
            print("Lab execution started")
            
            # Monitor lab status
            status_result = await lab_service.get_lab_status(lab_id)
            if status_result.success:
                print(f"Lab status: {status_result.data['status']}")

asyncio.run(main())
```

### Bot Management

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import BotService

async def main():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create bot service
    bot_service = BotService(client, auth_manager)
    
    # Create a bot
    result = await bot_service.create_bot(
        name="Test Bot",
        account_id="account_123",
        market_tag="BTC_USDT_PERPETUAL",
        leverage=20,
        margin_mode="cross",
        position_mode="hedge"
    )
    
    if result.success:
        bot_id = result.data["bot_id"]
        print(f"Created bot: {bot_id}")
        
        # Activate the bot
        activation_result = await bot_service.activate_bot(bot_id)
        if activation_result.success:
            print("Bot activated")
            
            # Monitor bot performance
            performance_result = await bot_service.get_bot_performance(bot_id)
            if performance_result.success:
                print(f"Bot performance: {performance_result.data}")

asyncio.run(main())
```

### Analysis and Reporting

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import AnalysisService, ReportingService

async def main():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create services
    analysis_service = AnalysisService(client, auth_manager)
    reporting_service = ReportingService()
    
    # Analyze a lab
    analysis_result = await analysis_service.analyze_lab_comprehensive(
        lab_id="lab_123",
        top_count=10
    )
    
    if analysis_result.success:
        print(f"Lab analysis completed: {analysis_result.data['lab_name']}")
        print(f"Total backtests: {analysis_result.data['total_backtests']}")
        print(f"Average ROI: {analysis_result.data['average_roi']}%")
        print(f"Best ROI: {analysis_result.data['best_roi']}%")
        
        # Generate report
        report_result = await reporting_service.generate_analysis_report(
            data=[analysis_result.data],
            report_type="lab_analysis",
            format="csv"
        )
        
        if report_result.success:
            print(f"Report generated: {report_result.report_path}")

asyncio.run(main())
```

### Mass Bot Creation

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import BotService, AnalysisService

async def main():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create services
    bot_service = BotService(client, auth_manager)
    analysis_service = AnalysisService(client, auth_manager)
    
    # Analyze multiple labs
    lab_ids = ["lab_123", "lab_456", "lab_789"]
    
    for lab_id in lab_ids:
        # Analyze lab
        analysis_result = await analysis_service.analyze_lab_comprehensive(
            lab_id=lab_id,
            top_count=5
        )
        
        if analysis_result.success:
            print(f"Analyzed lab {lab_id}: {analysis_result.data['lab_name']}")
            
            # Create bots from top performers
            bot_result = await bot_service.create_bots_from_lab(
                lab_id=lab_id,
                count=3,
                activate=True
            )
            
            if bot_result.success:
                print(f"Created {len(bot_result.data)} bots from lab {lab_id}")

asyncio.run(main())
```

## CLI Examples

### Basic Lab Operations

```bash
# List all labs
python -m pyHaasAPI_v2.cli lab list

# Create a new lab
python -m pyHaasAPI_v2.cli lab create --name "Test Lab" --script-id "script_123"

# Analyze a lab
python -m pyHaasAPI_v2.cli lab analyze --lab-id "lab_123" --top-count 5

# Execute a lab
python -m pyHaasAPI_v2.cli lab execute --lab-id "lab_123"

# Get lab status
python -m pyHaasAPI_v2.cli lab status --lab-id "lab_123"
```

### Bot Management

```bash
# List all bots
python -m pyHaasAPI_v2.cli bot list

# Create bots from lab
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_123" --count 3 --activate

# Activate specific bots
python -m pyHaasAPI_v2.cli bot activate --bot-ids "bot1,bot2,bot3"

# Deactivate all bots
python -m pyHaasAPI_v2.cli bot deactivate --all

# Pause bots
python -m pyHaasAPI_v2.cli bot pause --bot-ids "bot1,bot2"

# Resume bots
python -m pyHaasAPI_v2.cli bot resume --bot-ids "bot1,bot2"
```

### Analysis and Reporting

```bash
# Analyze all labs
python -m pyHaasAPI_v2.cli analysis labs --generate-reports

# Analyze specific lab
python -m pyHaasAPI_v2.cli analysis labs --lab-id "lab_123" --top-count 10

# Walk Forward Optimization
python -m pyHaasAPI_v2.cli analysis wfo --lab-id "lab_123" --start-date "2022-01-01" --end-date "2023-12-31"

# Generate performance report
python -m pyHaasAPI_v2.cli analysis performance --generate-reports

# Export data to CSV
python -m pyHaasAPI_v2.cli lab list --output-format csv --output-file labs.csv
```

### Batch Operations

```bash
# Analyze multiple labs with filters
python -m pyHaasAPI_v2.cli analysis labs --min-roi 100 --min-winrate 0.6 --generate-reports

# Create bots from multiple labs
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_123" --count 5
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_456" --count 3

# Activate all bots
python -m pyHaasAPI_v2.cli bot activate --all

# Export all data
python -m pyHaasAPI_v2.cli lab list --output-format csv --output-file all_labs.csv
python -m pyHaasAPI_v2.cli bot list --output-format csv --output-file all_bots.csv
python -m pyHaasAPI_v2.cli account list --output-format csv --output-file all_accounts.csv
```

## Advanced Examples

### Custom Analysis Pipeline

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import AnalysisService, BotService
from pyHaasAPI_v2.core.async_utils import AsyncBatchProcessor

async def custom_analysis_pipeline():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create services
    analysis_service = AnalysisService(client, auth_manager)
    bot_service = BotService(client, auth_manager)
    
    # Batch processor for concurrent operations
    batch_processor = AsyncBatchProcessor(batch_size=5, max_concurrent=3)
    
    # Lab IDs to analyze
    lab_ids = ["lab_123", "lab_456", "lab_789", "lab_101", "lab_202"]
    
    # Define analysis function
    async def analyze_lab(lab_id):
        result = await analysis_service.analyze_lab_comprehensive(
            lab_id=lab_id,
            top_count=5
        )
        return lab_id, result
    
    # Process labs in batches
    results = await batch_processor.process_batches(lab_ids, analyze_lab)
    
    # Filter successful analyses
    successful_analyses = []
    for lab_id, result in results:
        if result.success and result.data['average_roi'] > 100:
            successful_analyses.append((lab_id, result.data))
    
    print(f"Found {len(successful_analyses)} labs with ROI > 100%")
    
    # Create bots from successful analyses
    for lab_id, data in successful_analyses:
        bot_result = await bot_service.create_bots_from_lab(
            lab_id=lab_id,
            count=3,
            activate=True
        )
        
        if bot_result.success:
            print(f"Created {len(bot_result.data)} bots from lab {lab_id}")

asyncio.run(custom_analysis_pipeline())
```

### Performance Monitoring

```python
import asyncio
import time
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import BotService
from pyHaasAPI_v2.core.async_utils import AsyncRateLimiter

async def performance_monitoring():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create services
    bot_service = BotService(client, auth_manager)
    
    # Rate limiter for API calls
    rate_limiter = AsyncRateLimiter(max_requests=100, time_window=60.0)
    
    # Monitor bots
    bot_ids = ["bot_123", "bot_456", "bot_789"]
    
    while True:
        start_time = time.time()
        
        # Rate limit API calls
        await rate_limiter.acquire()
        
        # Get bot performance
        for bot_id in bot_ids:
            performance = await bot_service.get_bot_performance(bot_id)
            if performance.success:
                data = performance.data
                print(f"Bot {bot_id}: ROI={data.get('roi', 0):.2f}%, "
                      f"Win Rate={data.get('win_rate', 0):.2f}%, "
                      f"Trades={data.get('total_trades', 0)}")
        
        # Wait for next monitoring cycle
        elapsed = time.time() - start_time
        await asyncio.sleep(max(0, 60 - elapsed))  # Monitor every minute

# Run monitoring (uncomment to use)
# asyncio.run(performance_monitoring())
```

### Data Export and Analysis

```python
import asyncio
import json
import csv
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.tools import DataDumper
from pyHaasAPI_v2.services import AnalysisService

async def data_export_and_analysis():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create services
    data_dumper = DataDumper(client)
    analysis_service = AnalysisService(client, auth_manager)
    
    # Export all data
    print("Exporting data...")
    
    # Export labs
    labs_result = await data_dumper.dump_labs("json", "exports")
    if labs_result.success:
        print(f"Exported labs: {labs_result.files}")
    
    # Export bots
    bots_result = await data_dumper.dump_bots("json", "exports")
    if bots_result.success:
        print(f"Exported bots: {bots_result.files}")
    
    # Export accounts
    accounts_result = await data_dumper.dump_accounts("json", "exports")
    if accounts_result.success:
        print(f"Exported accounts: {accounts_result.files}")
    
    # Analyze exported data
    print("Analyzing exported data...")
    
    # Load and analyze labs
    with open("exports/labs.json", "r") as f:
        labs_data = json.load(f)
    
    print(f"Total labs: {len(labs_data)}")
    
    # Analyze each lab
    for lab in labs_data:
        lab_id = lab["lab_id"]
        analysis_result = await analysis_service.analyze_lab_comprehensive(
            lab_id=lab_id,
            top_count=5
        )
        
        if analysis_result.success:
            data = analysis_result.data
            print(f"Lab {lab_id}: {data['lab_name']}, "
                  f"ROI: {data['average_roi']:.2f}%, "
                  f"Backtests: {data['total_backtests']}")

asyncio.run(data_export_and_analysis())
```

## Error Handling

### Comprehensive Error Handling

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.exceptions import (
    HaasAPIError, AuthenticationError, APIError, 
    ValidationError, RateLimitError, TimeoutError
)

async def robust_operations():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    
    try:
        # Authenticate
        await auth_manager.authenticate()
        print("Authentication successful")
        
        # Perform operations
        labs = await client.get_labs()
        print(f"Retrieved {len(labs)} labs")
        
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("Please check your credentials")
        
    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        print("Please wait before making more requests")
        
    except TimeoutError as e:
        print(f"Request timeout: {e}")
        print("Please check your connection")
        
    except APIError as e:
        print(f"API error: {e}")
        print("Please check the API endpoint and parameters")
        
    except ValidationError as e:
        print(f"Validation error: {e}")
        print("Please check your input data")
        
    except HaasAPIError as e:
        print(f"General API error: {e}")
        print("Please check the error details")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Please contact support")

asyncio.run(robust_operations())
```

### Retry Logic

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.core.async_utils import AsyncRetryHandler
from pyHaasAPI_v2.exceptions import APIError

async def retry_operations():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    
    # Retry handler
    retry_handler = AsyncRetryHandler(max_retries=3, base_delay=1.0)
    
    # Define operation with retry
    async def get_labs_with_retry():
        await auth_manager.authenticate()
        return await client.get_labs()
    
    try:
        # Execute with retry
        labs = await retry_handler.execute_with_retry(get_labs_with_retry)
        print(f"Retrieved {len(labs)} labs after retries")
        
    except Exception as e:
        print(f"Operation failed after retries: {e}")

asyncio.run(retry_operations())
```

## Performance Optimization

### Concurrent Operations

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import AnalysisService

async def concurrent_analysis():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create service
    analysis_service = AnalysisService(client, auth_manager)
    
    # Lab IDs to analyze concurrently
    lab_ids = ["lab_123", "lab_456", "lab_789", "lab_101", "lab_202"]
    
    # Define analysis function
    async def analyze_lab(lab_id):
        return await analysis_service.analyze_lab_comprehensive(
            lab_id=lab_id,
            top_count=5
        )
    
    # Run analyses concurrently
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[analyze_lab(lab_id) for lab_id in lab_ids])
    end_time = asyncio.get_event_loop().time()
    
    # Process results
    successful_analyses = [r for r in results if r.success]
    print(f"Completed {len(successful_analyses)}/{len(lab_ids)} analyses in {end_time - start_time:.2f}s")
    
    # Print results
    for i, result in enumerate(successful_analyses):
        data = result.data
        print(f"Lab {lab_ids[i]}: {data['lab_name']}, "
              f"ROI: {data['average_roi']:.2f}%, "
              f"Backtests: {data['total_backtests']}")

asyncio.run(concurrent_analysis())
```

### Caching and Rate Limiting

```python
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.core.async_client import AsyncHaasClientWrapper, AsyncClientConfig
from pyHaasAPI_v2.core.async_utils import AsyncRateLimiter

async def optimized_operations():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="your_email@example.com",
        password="your_password"
    )
    await auth_manager.authenticate()
    
    # Create optimized client wrapper
    config = AsyncClientConfig(
        cache_ttl=300.0,  # 5 minutes cache
        enable_caching=True,
        enable_rate_limiting=True,
        max_concurrent_requests=10
    )
    
    wrapper = AsyncHaasClientWrapper(client, auth_manager, config)
    
    # Rate limiter for additional control
    rate_limiter = AsyncRateLimiter(max_requests=100, time_window=60.0)
    
    # Perform operations with caching and rate limiting
    for i in range(10):
        await rate_limiter.acquire()
        
        # This will use cache if available
        labs = await wrapper.execute_request(client.get_labs)
        print(f"Request {i+1}: Retrieved {len(labs)} labs")
        
        # Small delay to respect rate limits
        await asyncio.sleep(0.1)

asyncio.run(optimized_operations())
```

## Testing Examples

### Unit Testing

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import LabService

@pytest.mark.async
async def test_lab_service():
    # Mock dependencies
    mock_client = AsyncMock()
    mock_auth_manager = AsyncMock()
    
    # Create service
    lab_service = LabService(mock_client, mock_auth_manager)
    
    # Mock API response
    mock_client.get_labs.return_value = [
        {"lab_id": "test_lab_123", "name": "Test Lab"}
    ]
    
    # Test service method
    labs = await lab_service.get_all_labs()
    
    # Assertions
    assert len(labs) == 1
    assert labs[0]["lab_id"] == "test_lab_123"
    assert labs[0]["name"] == "Test Lab"
    
    # Verify mock was called
    mock_client.get_labs.assert_called_once()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_lab_service())
```

### Integration Testing

```python
import pytest
import asyncio
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import LabService, BotService

@pytest.mark.async
@pytest.mark.integration
async def test_lab_to_bot_workflow():
    # Setup (use real client for integration tests)
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="test@example.com",
        password="test_password"
    )
    
    try:
        # Authenticate
        await auth_manager.authenticate()
        
        # Create services
        lab_service = LabService(client, auth_manager)
        bot_service = BotService(client, auth_manager)
        
        # Create test lab
        lab_result = await lab_service.create_lab(
            name="Integration Test Lab",
            script_id="test_script_123"
        )
        
        assert lab_result.success
        lab_id = lab_result.data["lab_id"]
        
        # Create bot from lab
        bot_result = await bot_service.create_bot(
            name="Integration Test Bot",
            account_id="test_account_123",
            market_tag="BTC_USDT_PERPETUAL"
        )
        
        assert bot_result.success
        bot_id = bot_result.data["bot_id"]
        
        # Cleanup
        await bot_service.delete_bot(bot_id)
        await lab_service.delete_lab(lab_id)
        
    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_lab_to_bot_workflow())
```

### Performance Testing

```python
import pytest
import asyncio
import time
from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager
from pyHaasAPI_v2.services import AnalysisService

@pytest.mark.async
@pytest.mark.performance
async def test_analysis_performance():
    # Setup
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(
        email="test@example.com",
        password="test_password"
    )
    await auth_manager.authenticate()
    
    # Create service
    analysis_service = AnalysisService(client, auth_manager)
    
    # Test lab ID
    lab_id = "test_lab_123"
    
    # Measure performance
    start_time = time.time()
    
    result = await analysis_service.analyze_lab_comprehensive(
        lab_id=lab_id,
        top_count=10
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Assertions
    assert result.success
    assert execution_time < 5.0  # Should complete within 5 seconds
    
    print(f"Analysis completed in {execution_time:.2f}s")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_analysis_performance())
```

---

These examples demonstrate various ways to use pyHaasAPI v2 for different scenarios. For more specific use cases or advanced patterns, refer to the [API Reference](api_reference.md) and [CLI Reference](cli_reference.md) documents.
