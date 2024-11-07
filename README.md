# Haaslib: A Python Library for Interacting with the HaasOnline API

Haaslib is a Python library designed to simplify interaction with the HaasOnline API.  It provides a robust and efficient way to manage labs, bots, scripts, and other resources within the HaasOnline ecosystem.

## Key Features

* **Simplified API Interaction:** Haaslib abstracts away the complexities of the HaasOnline API, providing a clean and intuitive Pythonic interface.
* **Robust Error Handling:** The library incorporates comprehensive error handling, including custom exceptions for common API errors and detailed logging for debugging.
* **Type Safety:** Leveraging Pydantic models, Haaslib ensures type safety for all API requests and responses, reducing the risk of runtime errors.
* **Efficient Resource Management:** The library includes tools for efficient management of resources, including labs, bots, and scripts, with built-in mechanisms for cleanup and resource tracking.
* **Comprehensive Testing:** Haaslib is thoroughly tested to ensure reliability and stability. Testing covers authentication, market data retrieval, bot management, script management, account management, and lab management, including creating, deleting, updating labs, retrieving lab details, and managing lab executions.  Testing guidelines emphasize successful authentication paths, efficient resource management, and robust error handling.
* **Lab Parameter Handling:**  Provides robust tools for parsing, updating, and managing lab parameters, including handling various parameter types (numeric, string, etc.) and ensuring type safety.

## Usage

This library is designed to be used with Python 3.

### Installation

Since Haaslib is not yet on PyPI, you need to install it from source. You can clone the repository and install it using pip:

1. **Clone the repository:** `git clone <repository_url>`
2. **Navigate to the directory:** `cd haaslib`
3. **Install using pip:** `pip install .`


### Configuration

Before using Haaslib, you need to configure your environment variables with your HaasOnline API credentials.  These are typically stored in a `.env` file (see `.env.example` for an example).  You'll need to replace the placeholder values with your actual credentials.  The required environment variables are:

* `HAAS_API_EMAIL`: Your HaasOnline API email address.
* `HAAS_API_PASSWORD`: Your HaasOnline API password.
* `HAAS_API_HOST`: The host address of your HaasOnline API (default: localhost).
* `HAAS_API_PORT`: The port number of your HaasOnline API (default: 8090).


You can set these variables in your shell's environment or in a `.env` file.  Make sure the `.env` file is in the same directory as your script.

### Basic Usage Example (Illustrative)

This is a simplified example to illustrate the basic usage. Refer to the detailed documentation and examples for more comprehensive usage scenarios.

```python
from haaslib import HaasClient

# Initialize the client
client = HaasClient()

# Authenticate (this will use your environment variables)
client.authenticate()

# Perform API calls (replace with actual API calls)
try:
    response = client.get_user_labs()
    print(response)
except Exception as e:
    print(f"An error occurred: {e}")

```

### Lab Parameter Management Example

Haaslib simplifies lab parameter management.  You can easily parse raw parameters into structured objects, update parameter values, and handle different parameter types.

```python
from haaslib.lab import update_lab_parameter_ranges
from haaslib.parameters import ScriptParameters

# ... (Obtain lab details using HaasClient) ...

# Parse parameters
script_params = ScriptParameters.from_api_response(lab_details.parameters)

# Update parameters (example: randomize parameters)
updated_details = update_lab_parameter_ranges(executor, lab_id, randomize=True)

# Access updated parameters
updated_params = ScriptParameters.from_api_response(updated_details.parameters)
```

## API Interaction Guidelines

* **Authentication:** Secure authentication is handled through environment variables (`HAAS_API_EMAIL`, `HAAS_API_PASSWORD`, `HAAS_API_HOST`, `HAAS_API_PORT`) to protect sensitive credentials.
* **Channel Names:** Use the official channel names from the HaasOnline API documentation.
* **Error Handling:** Always check the API response success flag and handle errors appropriately. Haaslib provides custom exceptions to help with this.
* **Rate Limiting:** Be mindful of API rate limits (e.g., 60 requests per minute). Implement exponential backoff if necessary.

## Project Structure

The project is structured to promote maintainability and scalability. Key components include:

* `haaslib/`: Contains the core library code.
* `examples/`: Provides example scripts demonstrating the library's usage. These are a great starting point for learning how to use the library.
* `docs/`: Contains documentation for the library.
* `tests/`: Contains unit and integration tests.

## Contributing

Contributions are welcome! Please refer to the contribution guidelines for more information.

## License

[Specify License]
