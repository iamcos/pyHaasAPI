# Testing Guide for pyHaasAPI

## Quick Start

```python
#!/usr/bin/env python3
from config import settings
from pyHaasAPI import api

def main():
    # Authenticate
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    
    # Your test code here
    scripts = api.get_all_scripts(executor)
    print(f"Found {len(scripts)} scripts")

if __name__ == "__main__":
    main()
```

## Test File Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # API integration tests
└── performance/    # Performance tests

examples/           # Quick tests and demos
```

## Running Tests

```bash
# Run specific test file
python tests/test_account_functions.py

# Run as module
python -m tests.integration.test_account_management

# Run from project root
PYTHONPATH=. python tests/quick_account_test.py
```

## Test Patterns

### Basic Test Template
```python
from config import settings
from pyHaasAPI import api

def test_function():
    # Setup
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    
    # Test
    try:
        result = api.some_function(executor)
        print(f"✅ Test passed: {result}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_function()
```

### Error Handling
```python
try:
    result = api.some_function(executor)
except api.HaasApiError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. Always use `config/settings.py` for credentials
2. Run tests from project root
3. Handle API errors gracefully
4. Use descriptive test names
5. Clean up test data when possible 