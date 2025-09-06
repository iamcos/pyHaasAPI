# Backtesting Lab Analysis Dashboard

A comprehensive, interactive web dashboard for analyzing backtesting labs and their financial performance. Built with Dash and Plotly, seamlessly integrated with pyHaasAPI.

## 🚀 Features

### Core Functionality
- **Lab Selection & Management**: Browse and select from all your HaasOnline labs
- **Real-time Authentication**: Secure connection to your HaasOnline instance
- **Dynamic Data Loading**: Progress indicators and loading states for large datasets
- **Comprehensive Financial Analysis**: Detailed metrics and performance analysis

### Financial Analytics
- **Profit/Loss Analysis**: Cumulative and individual profit tracking
- **Equity Curve Visualization**: Portfolio value over time
- **Drawdown Analysis**: Risk assessment with visual drawdown charts
- **Trade Distribution**: Win/loss ratios and profit distributions
- **Advanced Metrics**: Sharpe ratio, profit factor, maximum drawdown

### Interactive Features
- **Tabbed Interface**: Organized analysis sections
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Dynamic chart generation and data processing
- **Sorting & Filtering**: Interactive data tables with search capabilities

### Bot Management
- **Create Bot**: Deploy successful backtests as live trading bots
- **Finetune**: Clone labs for parameter optimization
- **Performance Tracking**: Monitor bot creation status

## 📋 Prerequisites

- Python 3.8+
- Virtual environment (`.venv` already set up)
- HaasOnline API access credentials
- MCP server running (if using advanced features)

## 🛠️ Installation

1. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install dash dash-bootstrap-components plotly pandas numpy
   ```

## 🚀 Usage

### Running the Dashboard

1. **Start the dashboard:**
   ```bash
   python dash_backtest_analyzer.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:8050`

3. **Authenticate:**
   - Enter your HaasOnline API credentials
   - Specify host and port (default: 127.0.0.1:8090)
   - Click "Connect"

### Using the Dashboard

#### 1. Lab Selection
- Use the dropdown to select a lab from your HaasOnline instance
- View lab details including script name, market, and configuration
- Click "Refresh Labs" to reload the lab list

#### 2. Financial Analysis
- **Profit/Loss Tab**: View cumulative profit and individual backtest performance
- **Equity Curve Tab**: Track portfolio value changes over time
- **Drawdown Tab**: Analyze risk with drawdown visualization
- **Trades Analysis Tab**: Review win/loss distributions and trade profitability

#### 3. Bot Management
- **Create Bot**: Automatically creates a bot from the best-performing backtest
- **Finetune**: Clones the selected lab for parameter optimization

#### 4. Data Export
- Export detailed analysis data (feature ready for implementation)
- Download charts and performance reports

## 📊 Dashboard Structure

```
BacktestDashboard/
├── Authentication Section
│   ├── API Host/Port configuration
│   ├── Email/Password fields
│   └── Connection status
├── Lab Selection Section
│   ├── Lab dropdown with script names
│   ├── Quick action buttons (Create Bot, Finetune)
│   └── Lab information display
├── Analysis Section
│   ├── Summary metrics cards
│   ├── Interactive chart tabs
│   └── Detailed backtest table
└── Extended Analysis Modal
    ├── Advanced financial metrics
    ├── Performance breakdown
    └── Export functionality
```

## 🔧 Configuration

### API Settings
- **Host**: Your HaasOnline API host (default: 127.0.0.1)
- **Port**: API port (default: 8090)
- **Credentials**: Your HaasOnline email and password

### Dashboard Settings
- **Port**: Web server port (default: 8050)
- **Debug Mode**: Enabled for development
- **Hot Reload**: Automatic code changes detection

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_dashboard.py
```

This will test:
- Import functionality
- Data processing capabilities
- Chart generation (without display)

## 🏗️ Architecture

### Technology Stack
- **Backend**: Python with Dash framework
- **Frontend**: HTML/CSS/JS with Bootstrap components
- **Visualization**: Plotly for interactive charts
- **Data Processing**: Pandas and NumPy for analysis
- **API Integration**: pyHaasAPI for HaasOnline connectivity

### Data Flow
1. **Authentication**: Secure login to HaasOnline API
2. **Data Retrieval**: Fetch labs and backtest results
3. **Processing**: Calculate financial metrics and prepare charts
4. **Visualization**: Render interactive charts and tables
5. **Interaction**: Handle user inputs and update displays

### Key Components
- `BacktestDashboard`: Main application class
- `authenticate_user()`: API authentication
- `create_metrics_cards()`: Financial metrics display
- Chart generation callbacks for each analysis tab
- Bot creation and lab finetuning functions

## 🔍 API Integration

The dashboard integrates with the following pyHaasAPI functions:

- `get_all_labs()`: Retrieve available labs
- `get_backtest_result()`: Get backtest data for a lab
- `add_bot_from_lab()`: Create bot from successful backtest
- `clone_lab()`: Clone lab for finetuning
- `get_backtest_runtime()`: Retrieve detailed backtest metrics

## 📈 Financial Metrics

### Basic Metrics
- Total Profit: Sum of all backtest profits
- Total Trades: Aggregate trade count
- Win Rate: Percentage of profitable trades
- Number of Backtests: Total backtests in lab

### Advanced Metrics
- Sharpe Ratio: Risk-adjusted return measure
- Profit Factor: Ratio of winning to losing trades
- Maximum Drawdown: Largest peak-to-trough decline
- Average Profit per Trade: Mean trade profitability

## 🎨 Customization

### Styling
- Bootstrap-based responsive design
- Professional color scheme
- Interactive hover effects
- Loading animations

### Chart Customization
- Plotly chart themes and colors
- Custom axis formatting
- Interactive legends and tooltips
- Responsive chart sizing

## 🚨 Error Handling

- Authentication error handling
- API timeout management
- Data validation and error messages
- Graceful degradation for missing data

## 🔄 Future Enhancements

- **Data Export**: CSV/Excel export functionality
- **Real-time Updates**: Live data streaming
- **Advanced Analytics**: Machine learning insights
- **Multi-lab Comparison**: Side-by-side analysis
- **Performance Alerts**: Automated notifications

## 📝 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify API credentials
   - Check host and port settings
   - Ensure HaasOnline is running

2. **No Labs Found**
   - Check lab permissions
   - Verify API connectivity
   - Refresh lab list

3. **Charts Not Loading**
   - Check data availability
   - Verify backtest results exist
   - Check browser console for errors

### Debug Mode

Run with debug logging:
```bash
python -c "import logging; logging.basicConfig(level=logging.DEBUG); from dash_backtest_analyzer import main; main()"
```

## 📄 License

This dashboard is part of the pyHaasAPI project. See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please:
1. Test your changes with `test_dashboard.py`
2. Follow the existing code style
3. Update documentation as needed
4. Create comprehensive commit messages

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test suite
3. Review the pyHaasAPI documentation
4. Check HaasOnline API documentation

---

**Built with ❤️ for the HaasOnline trading community**
