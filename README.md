# Haaslib - HaasOnline Trading API Client

**Your Organization**

**2024**

## Overview

Haaslib is a Python client library for interacting with the HaasOnline Trading Server API. It provides a type-safe interface for managing trading bots, labs, backtests, and market data.

## Features

- Full type safety with Pydantic models
- Comprehensive API coverage
- Support for both authenticated and unauthenticated endpoints
- Lab management and backtesting capabilities
- Market data access
- Bot creation and management
- Account management

## Installation

```bash
pip install haaslib
```

## Quick Start

```python
from haaslib.api import RequestsExecutor, Guest
from haaslib import api

# Create guest executor
executor = RequestsExecutor(
    host="127.0.0.1",
    port=8090,
    state=Guest()
)

# Authenticate
auth_executor = executor.authenticate(
    email="your_email@example.com",
    password="your_password"
)

# Get markets
markets = api.get_all_markets(auth_executor)
```

## Documentation

The documentation is organized into the following sections:

- [Authentication](docs/authentication.md)
- [Lab Management](docs/labs.md)


## Development

**Prerequisites**

- Python 3.11+
- Poetry (recommended)

**Setting Up Development Environment**

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/haaslib.git
   cd haaslib
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Create `.env` file:
   ```
   HAAS_API_HOST=127.0.0.1
   HAAS_API_PORT=8090
   HAAS_API_EMAIL="your_email@example.com"
   HAAS_API_PASSWORD="your_password"
   ```

**Running Tests**

```bash
poetry run pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.
