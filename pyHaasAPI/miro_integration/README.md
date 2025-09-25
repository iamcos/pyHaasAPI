# pyHaasAPI Miro Integration 🚀

A comprehensive integration between pyHaasAPI and Miro boards for real-time lab monitoring, bot deployment, and automated reporting.

## 🌟 Features

### 🧪 **Lab Monitoring**
- Real-time lab progression tracking
- Performance metrics visualization
- Automated status updates
- Interactive lab management controls

### 🤖 **Bot Deployment Center**
- One-click bot creation from lab analysis
- Interactive deployment buttons
- Real-time bot status monitoring
- Performance tracking and alerts

### 📊 **Automated Reporting**
- Comprehensive lab analysis reports
- Bot performance summaries
- System status monitoring
- Scheduled report generation

### 🎛️ **Dashboard Management**
- Unified dashboard creation
- Multi-component monitoring
- Real-time updates coordination
- Status tracking and error handling

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file with your credentials:

```bash
# HaasOnline API
API_EMAIL=your_email@example.com
API_PASSWORD=your_password

# Miro API
MIRO_ACCESS_TOKEN=your_miro_access_token
MIRO_TEAM_ID=your_team_id  # Optional
```

### 2. Install Dependencies

```bash
# Install pyHaasAPI with Miro integration
pip install pyHaasAPI

# Or install from source
git clone https://github.com/your-repo/pyHaasAPI
cd pyHaasAPI
pip install -e .
```

### 3. Basic Usage

```python
from pyHaasAPI.miro_integration import DashboardManager, DashboardConfig
from pyHaasAPI.analysis import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI import api
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup HaasOnline API connection
haas_api = api.RequestsExecutor(host='127.0.0.1', port=8090, state=api.Guest())
executor = haas_api.authenticate(os.getenv('API_EMAIL'), os.getenv('API_PASSWORD'))

# Setup Miro client
from pyHaasAPI.miro_integration.client import MiroClient
miro_client = MiroClient(os.getenv('MIRO_ACCESS_TOKEN'))

# Initialize analyzer
cache_manager = UnifiedCacheManager()
analyzer = HaasAnalyzer(cache_manager)
analyzer.executor = executor

# Create comprehensive dashboard
dashboard_config = DashboardConfig(
    update_interval_minutes=15,
    enable_lab_monitoring=True,
    enable_bot_deployment=True,
    enable_automated_reporting=True
)

dashboard_manager = DashboardManager(miro_client, analyzer, dashboard_config)
dashboard = dashboard_manager.create_comprehensive_dashboard("My Trading Dashboard")

# Start monitoring
labs = analyzer.get_labs()
lab_ids = [getattr(lab, 'lab_id', '') for lab in labs[:5]]
dashboard_manager.start_comprehensive_monitoring(dashboard.id, lab_ids)
```

## 📋 CLI Usage

### Create Comprehensive Dashboard

```bash
# Create dashboard with all features
python -m pyHaasAPI.miro_integration.cli create-dashboard --start-monitoring

# Create dashboard with custom settings
python -m pyHaasAPI.miro_integration.cli create-dashboard \
  --dashboard-name "My Trading Dashboard" \
  --update-interval 10 \
  --start-monitoring
```

### Monitor Specific Labs

```bash
# Monitor specific labs
python -m pyHaasAPI.miro_integration.cli monitor-labs \
  --lab-ids "lab1,lab2,lab3" \
  --start-monitoring

# Monitor with custom settings
python -m pyHaasAPI.miro_integration.cli monitor-labs \
  --lab-ids "lab1,lab2" \
  --update-interval 5 \
  --max-labs 10 \
  --start-monitoring
```

### Deploy Bots

```bash
# Deploy bots from lab analysis
python -m pyHaasAPI.miro_integration.cli deploy-bots \
  --lab-ids "lab1,lab2" \
  --top-count 5 \
  --activate

# Deploy with custom settings
python -m pyHaasAPI.miro_integration.cli deploy-bots \
  --lab-ids "lab1" \
  --top-count 3 \
  --leverage 20.0 \
  --trade-amount 2000.0 \
  --activate
```

### Generate Reports

```bash
# Generate all reports
python -m pyHaasAPI.miro_integration.cli generate-reports --report-type all

# Generate specific reports
python -m pyHaasAPI.miro_integration.cli generate-reports \
  --report-type labs \
  --lab-ids "lab1,lab2" \
  --start-automated

# Generate with custom settings
python -m pyHaasAPI.miro_integration.cli generate-reports \
  --report-type all \
  --update-interval 2 \
  --include-charts \
  --include-recommendations \
  --start-automated
```

### List Boards

```bash
# List all available Miro boards
python -m pyHaasAPI.miro_integration.cli list-boards
```

## 🎯 Advanced Usage

### Lab Monitoring

```python
from pyHaasAPI.miro_integration import LabMonitor, LabMonitorConfig

# Configure lab monitoring
lab_config = LabMonitorConfig(
    update_interval_minutes=5,
    max_labs_per_board=20,
    include_performance_charts=True,
    auto_create_bots=False
)

# Create lab monitor
lab_monitor = LabMonitor(miro_client, analyzer, lab_config)

# Create monitoring board
board = lab_monitor.create_lab_monitoring_board("Lab Monitoring")

# Add labs to monitoring
lab_monitor.add_lab_to_monitoring("lab_id_1", board.id)
lab_monitor.add_lab_to_monitoring("lab_id_2", board.id)

# Start monitoring
lab_monitor.start_monitoring(board.id)
```

### Bot Deployment

```python
from pyHaasAPI.miro_integration import BotDeploymentCenter, BotDeploymentConfig

# Configure bot deployment
bot_config = BotDeploymentConfig(
    default_leverage=20.0,
    default_trade_amount_usdt=2000.0,
    position_mode=1,  # HEDGE
    margin_mode=0,    # CROSS
    auto_activate=False,
    max_bots_per_lab=5
)

# Create bot deployment center
bot_deployment = BotDeploymentCenter(miro_client, analyzer, bot_config)

# Create deployment board
board = bot_deployment.create_bot_deployment_board("Bot Deployment")

# Deploy bots from lab analysis
bot_results = bot_deployment.create_bots_from_lab_analysis(
    "lab_id", board.id, top_count=5, activate=True
)

# Update bot performance
for bot_id in bot_deployment.deployed_bots.keys():
    bot_deployment.update_bot_performance(bot_id, board.id)
```

### Automated Reporting

```python
from pyHaasAPI.miro_integration import ReportGenerator, ReportConfig

# Configure reporting
report_config = ReportConfig(
    update_interval_hours=6,
    include_performance_charts=True,
    include_recommendations=True,
    max_labs_per_report=50,
    report_format="comprehensive"
)

# Create report generator
report_generator = ReportGenerator(miro_client, analyzer, report_config)

# Create reporting board
board = report_generator.create_reporting_board("Automated Reports")

# Generate comprehensive report
reports = report_generator.generate_comprehensive_report(board.id)

# Start automated reporting
report_generator.start_automated_reporting(board.id)
```

## 🔧 Configuration

### Dashboard Configuration

```python
dashboard_config = DashboardConfig(
    update_interval_minutes=15,           # Update frequency
    enable_lab_monitoring=True,           # Enable lab monitoring
    enable_bot_deployment=True,           # Enable bot deployment
    enable_automated_reporting=True,      # Enable automated reporting
    lab_monitoring_config=LabMonitorConfig(
        update_interval_minutes=10,
        max_labs_per_board=20,
        include_performance_charts=True,
        auto_create_bots=False
    ),
    bot_deployment_config=BotDeploymentConfig(
        default_leverage=20.0,
        default_trade_amount_usdt=2000.0,
        position_mode=1,
        margin_mode=0,
        auto_activate=False,
        max_bots_per_lab=5
    ),
    report_config=ReportConfig(
        update_interval_hours=6,
        include_performance_charts=True,
        include_recommendations=True,
        max_labs_per_report=50
    )
)
```

## 🎨 Miro Board Layouts

### Comprehensive Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│                🚀 pyHaasAPI Comprehensive Dashboard         │
├─────────────────────────────────────────────────────────────┤
│ 🧭 Quick Navigation    │ 🧪 Lab Monitoring │ 🤖 Bot Deployment │
│ • Analyze All Labs     │ 🟢 Active: 5      │ 🟢 Running: 12    │
│ • Mass Bot Creator     │ 🟡 Paused: 2      │ 🟡 Paused: 3      │
│ • Generate Reports     │ 🔴 Failed: 0      │ 🔴 Failed: 1      │
│ • System Status        │ ✅ Completed: 8   │ ⚪ Created: 5      │
│ • Refresh All          │                   │                   │
├─────────────────────────────────────────────────────────────┤
│ 📊 Automated Reports   │ ⚙️ System Overview                 │
│ 📈 Lab Analysis: Ready │ 🔗 API: Connected                  │
│ 🤖 Bot Performance: ✅ │ 💾 Cache: Active                   │
│ ⚙️ System Status: ✅   │ 📊 Database: Healthy               │
│ 🔄 Next Update: 14:30  │ 🔄 Services: Running               │
└─────────────────────────────────────────────────────────────┘
```

### Lab Monitoring Board Layout

```
┌─────────────────────────────────────────────────────────────┐
│                🧪 Lab Monitoring Dashboard                  │
├─────────────────────────────────────────────────────────────┤
│ 📊 Status Legend: 🟢 Running │ 🟡 Paused │ 🔴 Failed │ ✅ Completed │
├─────────────────────────────────────────────────────────────┤
│ 🧪 Active Labs                                              │
│ ┌─────────────────┐ ┌─────────────────┐                    │
│ │ 🟢 Lab 1        │ │ 🟢 Lab 2        │                    │
│ │ Progress: 75%   │ │ Progress: 90%   │                    │
│ │ Backtests: 150/200 │ Backtests: 180/200 │                │
│ │ ROI: 85.2%      │ │ ROI: 92.1%      │                    │
│ │ [📊 Analyze]    │ │ [📊 Analyze]    │                    │
│ │ [🤖 Create Bots]│ │ [🤖 Create Bots]│                    │
│ │ [👁️ Details]    │ │ [👁️ Details]    │                    │
│ └─────────────────┘ └─────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Bot Deployment Board Layout

```
┌─────────────────────────────────────────────────────────────┐
│                🤖 Bot Deployment Center                     │
├─────────────────────────────────────────────────────────────┤
│ 🎛️ Deployment Controls                                      │
│ [🚀 Mass Bot Creator] [📊 Analyze All Labs] [⚙️ Manage Bots] │
├─────────────────────────────────────────────────────────────┤
│ 🤖 Deployed Bots                                            │
│ ┌─────────────────┐ ┌─────────────────┐                    │
│ │ 🟢 Bot 1        │ │ 🟢 Bot 2        │                    │
│ │ Market: BTC_USDT│ │ Market: ETH_USDT│                    │
│ │ Account: 4AA-10k│ │ Account: 4AB-10k│                    │
│ │ ROI: 12.5%      │ │ ROI: 8.3%       │                    │
│ │ [▶️ Activate]   │ │ [▶️ Activate]   │                    │
│ │ [⏸️ Pause]      │ │ [⏸️ Pause]      │                    │
│ │ [⏹️ Stop]       │ │ [⏹️ Stop]       │                    │
│ │ [📊 Stats]      │ │ [📊 Stats]      │                    │
│ └─────────────────┘ └─────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## 🔗 Webhook Integration

### Setting Up Webhooks

```python
# Create webhook for real-time updates
webhook_id = miro_client.create_webhook(
    board_id="your_board_id",
    webhook_url="https://your-endpoint.com/miro-webhook",
    events=["board:updated", "item:created", "item:updated", "item:deleted"]
)

# Handle webhook events
def handle_webhook_event(event_data):
    event_type = event_data.get("eventType")
    board_id = event_data.get("boardId")
    
    if event_type == "item:created":
        # Handle new item creation
        item_id = event_data.get("itemId")
        # Update your system accordingly
    elif event_type == "item:updated":
        # Handle item updates
        item_id = event_data.get("itemId")
        # Refresh data or trigger actions
```

## 📊 Report Types

### Lab Analysis Report

- **Total Labs Analyzed**: Number of labs processed
- **Total Backtests**: Total backtests across all labs
- **Analysis Success Rate**: Percentage of successful analyses
- **Top Performing Labs**: Best performing labs by ROI
- **Recommendations**: Actionable insights and suggestions

### Bot Performance Report

- **Total Bots**: Number of deployed bots
- **Active Bots**: Currently running bots
- **Average ROI**: Mean ROI across all bots
- **Top Performing Bots**: Best performing bots
- **Performance Trends**: Historical performance data

### System Status Report

- **API Status**: HaasOnline API connection status
- **System Health**: Overall system health indicators
- **Resource Usage**: Memory, CPU, and storage usage
- **Error Counts**: Number of errors and warnings
- **Service Status**: Status of all integrated services

## 🚨 Error Handling

### Common Issues and Solutions

1. **Authentication Errors**
   ```python
   # Check environment variables
   if not os.getenv('API_EMAIL') or not os.getenv('API_PASSWORD'):
       raise ValueError("HaasOnline credentials not found")
   
   if not os.getenv('MIRO_ACCESS_TOKEN'):
       raise ValueError("Miro access token not found")
   ```

2. **API Rate Limits**
   ```python
   # The integration includes built-in rate limiting
   # If you encounter rate limits, increase delays:
   lab_config = LabMonitorConfig(update_interval_minutes=30)  # Slower updates
   ```

3. **Board Creation Failures**
   ```python
   # Check Miro permissions and team access
   boards = miro_client.get_boards()
   if not boards:
       raise ValueError("No accessible Miro boards found")
   ```

## 🔒 Security Considerations

1. **API Keys**: Store all API keys in environment variables
2. **Webhook Security**: Implement proper authentication for webhook endpoints
3. **Data Privacy**: Ensure sensitive trading data is handled securely
4. **Access Control**: Limit Miro board access to authorized users only

## 📈 Performance Optimization

1. **Caching**: Use the built-in cache manager for better performance
2. **Batch Operations**: Process multiple items in batches
3. **Rate Limiting**: Respect API rate limits with appropriate delays
4. **Error Recovery**: Implement retry logic for failed operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the example usage files

---

**Happy Trading! 🚀📊🤖**
