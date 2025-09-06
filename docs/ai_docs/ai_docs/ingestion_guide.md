# Data Ingestion Guide for pyHaasAPI

This guide outlines the process for ingesting new HaasScript scripts and datasets into the `pyHaasAPI` project, ensuring they are properly managed and accessible.

## Ingesting New HaasScript Scripts

To add new HaasScript scripts to the server, you should use the `add_script` function available in the `pyHaasAPI.api` module. This function allows you to upload script content directly to the HaasOnline Trade Server.

**Function Signature:**

```python
api.add_script(
    executor,
    script_name: str,
    script_content: str,
    description: str = "",
    script_type: int = 0 # 0 = trading script, other types may exist
)
```

**Example Usage:**

```python
from config import settings
from pyHaasAPI import api

# Authenticate (assuming executor is already set up as per authentication guide)
executor = api.RequestsExecutor(
    host=settings.API_HOST,
    port=settings.API_PORT,
    state=api.Guest()
).authenticate(
    email=settings.API_EMAIL,
    password=settings.API_PASSWORD
)

script_name = "MyNewTradingScript"
script_content = """
// HaasScript
function main() {
  Print("Hello from my new script!");
}
"""
description = "A newly added example trading script."
script_type = 0 # Trading script

try:
    new_script = api.add_script(executor, script_name, script_content, description, script_type)
    print(f"Successfully added script: {new_script.script_name} with ID: {new_script.script_id}")
except api.HaasApiError as e:
    print(f"Error adding script: {e}")
```

**Best Practices for Scripts:**

*   **Descriptive Names:** Use clear and descriptive `script_name` values.
*   **Version Control:** Always keep your script source code under version control (e.g., Git) in the project's `haasscripts_dump/` directory or a similar designated location.
*   **Testing:** Thoroughly test new scripts in a lab environment before deploying them to live bots.

## Ingesting New Datasets

For datasets (e.g., historical price data, custom indicators, or other relevant data files), the ingestion process typically involves placing them in a designated project directory and ensuring they can be accessed by your scripts or analysis tools.

**Recommended Location:**

Place new datasets in the `data/` directory within the project root. Organize them into subdirectories as appropriate (e.g., `data/historical_prices/BINANCE/BTC_USDT/`).

**Example Data Structure:**

```
pyHaasAPI/
├── data/
│   ├── historical_prices/
│   │   ├── BINANCE/
│   │   │   └── BTC_USDT_1h.csv
│   │   └── COINBASE/
│   │       └── ETH_USD_4h.json
│   └── custom_indicators/
│       └── my_indicator_data.json
└── ...
```

**Accessing Datasets from Python:**

When writing Python code to interact with these datasets, use relative paths from the project root or construct absolute paths using `os.path.join` and the project's root directory.

```python
import os
import pandas as pd

project_root = os.path.dirname(os.path.abspath(__file__)) # Adjust if script is not in root
data_file_path = os.path.join(project_root, 'data', 'historical_prices', 'BINANCE', 'BTC_USDT_1h.csv')

try:
    df = pd.read_csv(data_file_path)
    print(f"Successfully loaded data from {data_file_path}")
    print(df.head())
except FileNotFoundError:
    print(f"Error: Data file not found at {data_file_path}")
except Exception as e:
    print(f"An error occurred while loading data: {e}")
```

**Integrating with `haasscript_rag` (for metadata/embeddings):**

If you have metadata about your datasets (e.g., descriptions, sources, or derived insights), you can ingest this information into the `haasscript_rag` server. This allows for semantic search and retrieval of information about your data, rather than the raw data itself.

**Example Metadata Ingestion (Conceptual):**

```python
import requests
import json

rag_server_url = "http://localhost:5001/memory"
project_name = "pyHaasAPI"

metadata_entry = {
    "project_name": project_name,
    "memory": "Dataset: BINANCE_BTC_USDT_1h.csv. Contains 1-hour candlestick data for BTC/USDT from Binance, used for backtesting scalping strategies. Data range: 2023-01-01 to 2023-12-31."
}

try:
    response = requests.post(rag_server_url, json=metadata_entry)
    response.raise_for_status()
    print(f"Metadata ingested successfully: {response.json()}")
except requests.exceptions.RequestException as e:
    print(f"Error ingesting metadata to RAG server: {e}")
```

By following these guidelines, you can effectively manage and integrate new HaasScript scripts and datasets within the `pyHaasAPI` project.