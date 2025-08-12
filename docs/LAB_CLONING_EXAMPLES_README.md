# Lab Cloning Examples

This directory contains example scripts that demonstrate how to create labs, clone them, and apply parameter ranges using the pyHaasAPI library.

## Scripts Overview

### 1. `simple_lab_cloning_example.py`
A straightforward example that demonstrates the core functionality:
- Creates a lab for Binance BTC/USDT market with scalper bot script
- Clones the lab twice
- Applies parameter ranges (1 to 10, step 0.5) to the second clone
- Saves the configuration to a JSON file

### 2. `example_lab_cloning_with_ranges.py`
A comprehensive example with advanced features:
- More robust error handling
- Intelligent parameter detection
- Detailed logging and progress tracking
- Flexible parameter range application
- Better resource discovery

## Prerequisites

1. **pyHaasAPI Library**: Make sure you have the pyHaasAPI library installed
2. **HaasOnline API**: Ensure the HaasOnline API is running on localhost:8090
3. **Valid Credentials**: You need valid HaasOnline credentials

## Configuration

Both scripts use environment variables for configuration. You can set them in your environment or modify the defaults in the scripts:

```bash
export HAAS_API_HOST="127.0.0.1"
export HAAS_API_PORT="8090"
export HAAS_API_EMAIL="your-email@example.com"
export HAAS_API_PASSWORD="your-password"
```

## Usage

### Running the Simple Example

```bash
python simple_lab_cloning_example.py
```

### Running the Comprehensive Example

```bash
python example_lab_cloning_with_ranges.py
```

## What the Scripts Do

### Step-by-Step Process

1. **Authentication**: Connect to the HaasOnline API using provided credentials
2. **Resource Discovery**: 
   - Find a scalper bot script
   - Locate Binance BTC/USDT market
   - Get available accounts
3. **Lab Creation**: Create an initial lab with the scalper bot on BTC/USDT
4. **Lab Cloning**: Clone the original lab twice
5. **Parameter Range Application**: Apply parameter ranges (1.0 to 10.0, step 0.5) to the second clone
6. **Configuration Saving**: Save the final lab configuration to a JSON file

### Parameter Range Details

The scripts generate parameter values from 1.0 to 10.0 with a step of 0.5:
```
[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
```

These ranges are applied to suitable parameters in the scalper bot script, such as:
- Stop Loss parameters
- Take Profit parameters
- Threshold values
- Delay settings

## Output Files

After running the scripts, you'll get:
- **Lab Configuration JSON**: Contains the lab details, parameter ranges, and settings
- **Console Output**: Detailed progress information and summary

Example output file: `lab_config_<lab_id>.json`

## Expected Output

```
🚀 Simple Lab Cloning Example
========================================
🔐 Authenticating...
✅ Authenticated

🔍 Finding scalper script...
✅ Found: Haasonline Original - Scalper Bot

🔍 Finding Binance BTC/USDT market...
✅ Found: BINANCE_BTC_USDT

🔍 Finding account...
✅ Using: My Binance Account

🚀 Creating initial lab...
✅ Created: Example_Lab_1703123456 (ID: abc123...)

📋 Cloning lab...
✅ Cloned: Clone_1_Example_Lab_1703123456 (ID: def456...)

📋 Cloning again...
✅ Cloned: Clone_2_Example_Lab_1703123456 (ID: ghi789...)

🔧 Applying parameter ranges...
📊 Generated 19 values: ['1.0', '1.5', '2.0', '2.5', '3.0']...['8.5', '9.0', '9.5', '10.0']
  ✅ Applied range to: .Stop Loss
  ✅ Applied range to: .Take Profit
✅ Lab updated successfully

💾 Saving configuration...
✅ Configuration saved to lab_config_ghi789.json

📋 SUMMARY
====================
Original lab: abc123...
Clone 1: def456...
Clone 2 (with ranges): ghi789...
Parameters updated: 2
Range values: 19

🎉 Example completed successfully!
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your credentials
   - Ensure HaasOnline API is running
   - Verify host and port settings

2. **No Scalper Bot Found**
   - Make sure you have scalper bot scripts in your HaasOnline account
   - The script looks for various scalper bot names

3. **No Binance BTC/USDT Market**
   - Ensure you have access to Binance markets
   - Check if the market is available in your HaasOnline setup

4. **No Accounts Available**
   - Make sure you have configured accounts in HaasOnline
   - Check account permissions and status

### Debug Mode

For more detailed output, you can modify the scripts to include debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Functions Used

The scripts demonstrate the following pyHaasAPI functions:

- `api.RequestsExecutor.authenticate()` - Authentication
- `api.get_scripts_by_name()` - Find scripts
- `api.get_all_markets()` - Get available markets
- `api.get_accounts()` - Get user accounts
- `api.create_lab()` - Create new lab
- `api.clone_lab()` - Clone existing lab
- `api.get_lab_details()` - Get lab configuration
- `api.update_lab_details()` - Update lab parameters

## Customization

You can easily customize these scripts for your needs:

- **Different Markets**: Change the market search criteria
- **Different Scripts**: Modify the script search patterns
- **Different Parameter Ranges**: Adjust the range start, end, and step values
- **Different Parameters**: Modify the parameter detection logic

## Next Steps

After running these examples, you can:

1. **Run Backtests**: Start lab execution to test the parameter ranges
2. **Analyze Results**: Get backtest results and find optimal parameters
3. **Deploy Bots**: Create bots from the best backtest configurations
4. **Scale Up**: Apply similar patterns to multiple markets or scripts

## Support

For issues with the pyHaasAPI library or these examples, please refer to the main pyHaasAPI documentation or create an issue in the repository. 