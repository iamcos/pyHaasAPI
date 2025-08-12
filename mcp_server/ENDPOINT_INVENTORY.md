# 📋 MCP Server Complete Endpoint Inventory

## 🎯 **Period Presets Explanation**
The period presets automatically calculate backtest timestamps:
- **`"1_year"`** → 365 days from current time
- **`"2_years"`** → 730 days from current time  
- **`"3_years"`** → 1095 days from current time
- **`"custom"`** → Use provided `custom_start_unix` and `custom_end_unix`

## 📊 **All Available Endpoints (60+ endpoints)**

### 🏠 **Core System**
- `GET /` - Root endpoint, server status
- `GET /status` - Authentication and connection status

### 🧪 **Lab Management (Enhanced)**
#### **Basic Lab Operations**
- `POST /create_lab` - Create new lab
- `POST /clone_lab` - Simple 1:1 lab cloning
- `GET /get_all_labs` - List all labs
- `DELETE /delete_lab/{lab_id}` - Delete specific lab
- `DELETE /labs/delete_all_except/{lab_name_to_keep}` - Bulk delete labs

#### **Lab Execution (NEW Enhanced)**
- `POST /backtest_lab` - Basic backtest (manual timestamps)
- `POST /start_lab_execution` - **🆕 Enhanced with period presets**
- `POST /start_multiple_labs` - **🆕 Bulk execution on multiple labs**
- `POST /cancel_lab_execution` - **🆕 Cancel running lab execution**
- `POST /get_backtest_results` - Get backtest results

#### **Advanced Lab Automation (NEW)**
- `POST /clone_lab_to_markets` - **🆕 Clone lab to multiple markets**
- `POST /clone_and_execute_labs` - **🆕 Ultimate automation: clone + execute**

### 🤖 **Bot Management**
#### **Bot Creation & Control**
- `POST /create_trade_bot_from_lab` - Create bot from lab results
- `POST /create_simple_bot` - Create simple trading bot
- `POST /activate_bot/{bot_id}` - Activate bot
- `POST /deactivate_bot/{bot_id}` - Deactivate bot
- `GET /get_all_trade_bots` - List all bots
- `GET /get_bot/{bot_id}` - Get specific bot details
- `DELETE /delete_trade_bot/{bot_id}` - Delete bot

#### **Bot Configuration**
- `POST /change_bot_script/{bot_id}/{script_id}` - Change bot script
- `POST /edit_bot_settings` - Edit bot settings
- `POST /edit_bot_parameter` - Edit bot parameters
- `GET /get_bot_script_parameters/{bot_id}` - Get bot script parameters

### 💰 **Account Management**
#### **Account Operations**
- `POST /create_simulated_account` - Create simulated account
- `DELETE /delete_simulated_account/{account_id}` - Delete account
- `GET /get_all_accounts` - List all accounts
- `GET /get_accounts` - Alternative account listing
- `GET /get_account_data/{account_id}` - Get account details
- `POST /setup_haas_accounts` - Setup HaasOnline accounts

#### **Funds Management**
- `POST /deposit_funds` - Deposit funds to account
- `POST /withdraw_funds` - Withdraw funds from account
- `GET /get_account_balance/{account_id}` - Get specific account balance
- `POST /get_account_balance` - Get account balance (POST version)
- `GET /get_all_account_balances` - Get all account balances

### 📈 **Market Data**
- `GET /get_all_markets` - List all available markets
- `POST /get_market_price` - Get current market price
- `POST /get_orderbook` - Get market order book

### 📝 **Script Management**
- `POST /add_script` - Add new HaasScript
- `GET /get_all_scripts` - List all scripts
- `GET /get_script_record/{script_id}` - Get script details
- `POST /edit_script_sourcecode` - Edit script source code
- `GET /is_script_execution/{script_id}` - Check if script is executing
- `GET /get_haasscript_commands` - Get available HaasScript commands

### 🔧 **Configuration & Testing**
- `GET /get_lab_config/{lab_id}` - Get lab configuration
- `POST /update_lab_config` - Update lab configuration
- `POST /execute_debug_test` - Execute debug test

### 📊 **Performance Monitoring**
- `GET /get_bot_logbook/{bot_id}` - Get bot trading log
- `GET /get_all_completed_orders` - Get all completed orders

### 🧠 **AI/ML Features**
- `POST /get_embedding` - Generate text embeddings

## 🆕 **New Enhanced Endpoints Details**

### **1. Enhanced Lab Execution**
```json
POST /start_lab_execution
{
  "lab_id": "abc123",
  "period": "2_years",        // 🆕 Period preset
  "send_email": false
}
```

### **2. Bulk Lab Execution**
```json
POST /start_multiple_labs
{
  "lab_ids": ["lab1", "lab2", "lab3"],
  "period": "1_year",         // 🆕 Period preset
  "send_email": false
}
```

### **3. Advanced Lab Cloning**
```json
POST /clone_lab_to_markets
{
  "source_lab_id": "abc123",
  "targets": [
    {"asset": "BTC", "exchange": "BINANCEFUTURES"},
    {"asset": "ETH", "exchange": "BINANCEFUTURES"}
  ],
  "lab_name_template": "{strategy} - {primary} - {suffix}"
}
```

### **4. Ultimate Automation**
```json
POST /clone_and_execute_labs
{
  "source_lab_id": "abc123",
  "targets": [{"asset": "BTC"}, {"asset": "ETH"}],
  "backtest_period": "2_years",  // 🆕 Period preset
  "auto_start": true
}
```

## 🎯 **Endpoint Categories Summary**

| Category | Count | Key Features |
|----------|-------|--------------|
| **Lab Management** | 12 | Period presets, bulk operations, advanced cloning |
| **Bot Management** | 10 | Full lifecycle management, configuration |
| **Account Management** | 10 | Account creation, funds management |
| **Market Data** | 3 | Real-time prices, order books |
| **Script Management** | 6 | HaasScript development tools |
| **Configuration** | 3 | Lab/bot configuration management |
| **Monitoring** | 2 | Performance tracking |
| **AI/ML** | 1 | Text embeddings |
| **System** | 2 | Status and health checks |

**Total: 49+ Endpoints**

## 🚀 **Key Automation Workflows**

### **Complete Lab Automation**
1. `POST /clone_lab_to_markets` - Clone to multiple assets
2. `POST /start_multiple_labs` - Start all with period presets
3. `GET /get_backtest_results` - Monitor results
4. `POST /create_trade_bot_from_lab` - Deploy best performers

### **Bot Management Workflow**
1. `POST /create_simple_bot` - Create bot
2. `POST /edit_bot_settings` - Configure settings
3. `POST /activate_bot/{bot_id}` - Start trading
4. `GET /get_bot_logbook/{bot_id}` - Monitor performance

### **Account Setup Workflow**
1. `POST /create_simulated_account` - Create account
2. `POST /deposit_funds` - Add funds
3. `GET /get_account_balance/{account_id}` - Verify balance

## 💡 **Period Presets vs Manual Timestamps**

### **Before (Manual)**
```json
{
  "lab_id": "abc123",
  "start_unix": 1691417668,    // Manual calculation needed
  "end_unix": 1754489668,      // Manual calculation needed
  "send_email": false
}
```

### **After (Period Presets)**
```json
{
  "lab_id": "abc123",
  "period": "2_years",         // 🎯 Automatic calculation
  "send_email": false
}
```

The period presets eliminate the need for manual timestamp calculations and make backtesting much more user-friendly!