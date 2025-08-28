# HaasOnline API Examples

This directory contains example scripts demonstrating how to use the HaasOnline API for various trading operations.

## Scripts

### setup_trading_accounts.py

**Purpose**: Complete setup script for creating standardized trading accounts.

**Features**:
- Creates 200 simulated trading accounts with naming scheme `4AA-10K-XXX`
- Funds each account with exactly 10,000 USDT
- Removes any unwanted cryptocurrencies to ensure clean accounts
- Comprehensive error handling and progress tracking
- Verification and cleanup of account balances

**Usage**:
```bash
# Make sure you have the virtual environment activated
source .venv/bin/activate

# Run the setup script
python examples/setup_trading_accounts.py
```

**Requirements**:
- HaasOnline API server running on `localhost:8090`
- Valid API credentials in `.env` file:
  ```
  API_HOST=127.0.0.1
  API_PORT=8090
  API_EMAIL=your_email@example.com
  API_PASSWORD=your_password
  ```
- pyHaasAPI library installed in virtual environment

**Output**:
- 200 accounts named `4AA-10K-001` through `4AA-10K-200`
- Each account contains exactly 10,000 USDT and no other cryptocurrencies
- Detailed progress reporting and error handling
- Final verification of account setup

## Environment Setup

Before running any examples, ensure you have:

1. **Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the project root with your HaasOnline API credentials.

4. **HaasOnline Server**:
   Ensure your HaasOnline server is running and accessible.

## API Channels Used

The setup script uses these HaasOnline API channels:
- `CREATE_SIMULATED_ACCOUNT` - Creates new simulated trading accounts
- `DEPOSIT_FUNDS` - Adds USDT to accounts
- `WITHDRAWAL_FUNDS` - Removes unwanted cryptocurrencies
- `GET_ALL_BALANCES` - Verifies account balances

## Error Handling

All scripts include comprehensive error handling for:
- API connection failures
- Authentication issues
- Account creation failures
- Funding operation failures
- Balance verification errors

## Support

For issues or questions:
1. Check the HaasOnline API documentation
2. Verify your API credentials and server status
3. Review the script output for specific error messages
4. Ensure all dependencies are properly installed