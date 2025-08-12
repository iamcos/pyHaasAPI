# pyHaasAPI Example Scripts

This directory contains runnable example scripts demonstrating all major features and workflows of the pyHaasAPI client for HaasOnline.

## Table of Contents

- [lab_lifecycle_example.py](#lab_lifecycle_examplepy)
- [bot_lifecycle_example.py](#bot_lifecycle_examplepy)
- [account_management_example.py](#account_management_examplepy)
- [haasscript_management_example.py](#haasscript_management_examplepy)
- [price_market_example.py](#price_market_examplepy)
- [user_management_example.py](#user_management_examplepy)
- [utility_advanced_example.py](#utility_advanced_examplepy)

## Usage

All scripts are runnable as modules:

```bash
python -m examples.<script_name>
```

Ensure your `config/settings.py` is set up with valid API credentials and server details.

## Example Scripts

### lab_lifecycle_example.py
Demonstrates the full lifecycle of a lab: create, clone, update parameters, backtest, and delete.

### bot_lifecycle_example.py
Shows how to create, activate, monitor, pause, resume, deactivate, and delete a bot.

### account_management_example.py
Covers listing, filtering, adding, renaming, and deleting accounts (including simulated accounts).

### haasscript_management_example.py
Demonstrates HaasScript management: list, get, add, edit, delete, and move scripts to folders.

### price_market_example.py
Shows how to list markets, get prices, order books, trades, chart data, and manage history depth.

### user_management_example.py
Covers user endpoints: app login, check token, logout, and device approval status.

### utility_advanced_example.py
Demonstrates advanced utilities: ensuring market history readiness, error handling, and bulk lab creation.

## Best Practices

- Review each script for required arguments and replace placeholder values (e.g., `your_script_id`, `your_account_id`) with real values from your environment.
- Handle API errors gracefully and check for readiness (e.g., market history) before running workflows.
- Use these scripts as templates for your own automation and integration tasks. 