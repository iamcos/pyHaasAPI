# Lab Analysis and Automated Bot Deployment Script

A comprehensive Python script that analyzes HaasOnline trading labs, ranks backtest configurations by performance, and automatically deploys the top-performing strategies as bots on available simulation accounts.

## Features

### 📊 Comprehensive Financial Analysis
- **Multi-Metric Evaluation**: Analyzes profit, win rate, drawdown, Sharpe ratio, and trade volume
- **Composite Scoring**: Weighted algorithm combining multiple performance metrics
- **Risk Assessment**: Evaluates margin safety and position sizing
- **Performance Ranking**: Automatically ranks all configurations from best to worst

### 🤖 Automated Bot Deployment
- **Account Discovery**: Scans for available simulation accounts (pattern: `[Sim] 4AA-10k`)
- **Occupancy Detection**: Checks which accounts already have bots assigned
- **Smart Distribution**: Distributes bots across multiple accounts for risk diversification
- **Batch Processing**: Deploys top 20 configurations automatically

### 📋 Detailed Reporting
- **Comprehensive Reports**: Generates detailed analysis and deployment reports
- **Progress Tracking**: Real-time logging and status updates
- **Error Handling**: Robust error handling with detailed error reporting
- **Export Options**: Saves reports to timestamped files

## Prerequisites

### System Requirements
- Python 3.11+
- pyHaasAPI library installed
- Valid HaasOnline API credentials
- Available simulation accounts matching pattern `[Sim] 4AA-10k`

### Installation
```bash
# Ensure pyHaasAPI is installed
pip install -e .

# Make script executable
chmod +x lab_analysis_and_deployment.py
```

### Configuration
Create a `.env` file with your HaasOnline credentials:
```env
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your_email@domain.com
API_PASSWORD=your_password
```

## Usage

### Basic Usage
```bash
python lab_analysis_and_deployment.py <lab_id>
```

### Example
```bash
python lab_analysis_and_deployment.py 272bbb66-f2b3-4eae-8c32-714747dcb827
```

### Command Line Options
- **Lab ID**: Required parameter - the HaasOnline lab identifier to analyze

## How It Works

### 1. Analysis Phase
1. **Lab Loading**: Retrieves all backtests from the specified lab
2. **Metrics Extraction**: Extracts financial metrics from each backtest:
   - Total profit/loss
   - Number of trades (winning/losing)
   - Win rate percentage
   - Maximum drawdown
   - Sharpe ratio
   - Execution time
3. **Composite Scoring**: Calculates weighted performance score using:
   - Profit (30% weight)
   - Win rate (25% weight)
   - Risk-adjusted score (20% weight)
   - Sharpe ratio (15% weight)
   - Volume score (10% weight)

### 2. Account Discovery Phase
1. **Account Scanning**: Retrieves all available accounts
2. **Bot Occupancy Check**: Queries all existing bots to map account usage
3. **Free Account Identification**: Filters accounts matching pattern `[Sim] 4AA-10k` with no active bots

### 3. Deployment Phase
1. **Top Configuration Selection**: Selects top 20 performing configurations
2. **Round-Robin Distribution**: Distributes bots across available accounts
3. **Bot Creation**: Uses HaasOnline API to create bots from lab backtests
4. **Progress Tracking**: Monitors deployment success/failure

## Output

### Console Output
```
🚀 Lab Analysis and Automated Bot Deployment
==================================================

🔐 Authenticating with HaasOnline API...
✅ Authentication successful!

📊 Analyzing lab: 272bbb66-f2b3-4eae-8c32-714747dcb827
📋 Lab: My Trading Strategy | Market: BINANCE_BTC_USDT_
📊 Found 150 backtests to analyze
✅ Analysis complete - 150 backtests processed

🏦 Scanning for available accounts...
🤖 Found 5 occupied accounts
✅ Found 12 available accounts

🤖 Deploying top 20 configurations...
✅ Successfully deployed bot AutoDeploy_Strategy1_1234567890_abc123 to [Sim] 4AA-10k
✅ Successfully deployed bot AutoDeploy_Strategy2_1234567890_def456 to [Sim] 4AA-20k
...
```

### Report Files
The script generates timestamped report files:
- `lab_analysis_report_<lab_id>_<timestamp>.txt`

Report includes:
- Lab summary and metadata
- Account availability status
- Top 20 configuration rankings
- Deployment results with bot assignments
- Error logs and troubleshooting information

## Account Management

### Account Pattern Matching
The script looks for accounts with names containing `[Sim] 4AA-10k` pattern:
- `[Sim] 4AA-10k`
- `[Sim] 4AA-20k`
- `[Sim] 4AA-50k`
- etc.

### Occupancy Detection
Before deployment, the script:
1. Retrieves all existing bots
2. Maps which accounts each bot is assigned to
3. Filters out occupied accounts
4. Only deploys to completely free accounts

### Distribution Strategy
- **Round-Robin**: Distributes bots evenly across available accounts
- **Load Balancing**: Prevents overloading single accounts
- **Risk Diversification**: Spreads risk across multiple accounts

## Financial Metrics Explained

### Composite Score Calculation
```python
weights = {
    'profit': 0.30,      # 30% - Raw profitability
    'win_rate': 0.25,    # 25% - Consistency
    'risk': 0.20,        # 20% - Risk-adjusted returns
    'sharpe': 0.15,      # 15% - Risk-adjusted performance
    'volume': 0.10       # 10% - Sample size reliability
}
```

### Risk-Adjusted Scoring
- **Profit Score**: Normalized to 0-100 scale (higher profit = higher score)
- **Win Rate Score**: Direct percentage (0-100)
- **Risk Score**: Inverse of drawdown (100 - drawdown%)
- **Sharpe Score**: Risk-adjusted return measure (0-100)
- **Volume Score**: Based on trade count (more trades = higher reliability)

## Error Handling

### Common Issues and Solutions

#### Authentication Errors
```
❌ Authentication failed: Invalid credentials
```
**Solution**: Check your `.env` file credentials

#### No Available Accounts
```
❌ No available accounts found
```
**Solution**: Ensure you have accounts matching `[Sim] 4AA-10k` pattern with no active bots

#### Lab Not Found
```
❌ Failed to analyze lab: Lab not found
```
**Solution**: Verify the lab ID is correct and you have access to it

#### API Rate Limiting
```
❌ Failed to deploy: Rate limit exceeded
```
**Solution**: Wait a few minutes and try again, or reduce batch size

## Troubleshooting

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Account Check
Check account availability manually:
```python
from pyHaasAPI import api

executor = api.RequestsExecutor(host="127.0.0.1", port=8090, state=api.Guest())
executor = executor.authenticate(email="your_email", password="your_password")

# Check accounts
accounts = api.get_all_account_balances(executor)
bots = api.get_all_bots(executor)

print(f"Total accounts: {len(accounts)}")
print(f"Total bots: {len(bots)}")
```

### Log Files
- **Main Log**: `lab_analysis.log` - Contains all script execution details
- **Report Files**: `lab_analysis_report_*.txt` - Detailed analysis reports

## Advanced Usage

### Custom Scoring Weights
Modify the `LabAnalyzer._calculate_composite_score()` method to adjust metric weights based on your preferences.

### Account Filtering
Modify the `AccountScanner.find_available_accounts()` method to use different account patterns or filtering criteria.

### Batch Size Control
Adjust the `top_n` parameter in `BotDeployer.deploy_top_configurations()` to deploy more or fewer configurations.

## Security Notes

- Credentials are stored in `.env` file (not committed to version control)
- API calls are made over HTTPS when possible
- No sensitive data is logged in report files
- Script validates account ownership before deployment

## Support

For issues or questions:
1. Check the log files for detailed error information
2. Verify your API credentials and account permissions
3. Ensure your HaasOnline instance is running and accessible
4. Check that you have sufficient account permissions for bot creation

## Changelog

### Version 1.0.0
- Initial release with comprehensive lab analysis
- Automated bot deployment with account management
- Detailed reporting and progress tracking
- Robust error handling and logging
