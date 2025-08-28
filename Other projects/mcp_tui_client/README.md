# MCP TUI Client

A comprehensive Terminal User Interface (TUI) for the HaasOnline MCP Server, providing full-featured trading bot and lab management capabilities through an intuitive, modular, and high-performance terminal interface.

## 🚀 Features

### 📊 **Dashboard**
- Real-time system status and connectivity monitoring
- Quick actions and navigation shortcuts
- Active bots and running labs overview
- Performance charts and market overview
- Recent alerts and notifications

### 🤖 **Bot Management**
- Comprehensive bot list with status indicators
- Detailed bot performance metrics and charts
- Bot lifecycle operations (start, stop, pause, resume)
- Batch operations for managing multiple bots
- Real-time P&L tracking and trade history

### 🧪 **Lab Management**
- Advanced backtesting laboratory interface
- Intelligent backtesting with history validation
- Parameter optimization with progress tracking
- Lab cloning and bulk operations
- Comprehensive backtest results analysis

### 📝 **Script Editor**
- HaasScript editor with syntax highlighting
- Real-time validation and error checking
- Script compilation and testing tools
- Script organization with folders and search
- Template library and code snippets

### 🔄 **Workflow Designer**
- Node-based workflow system for modular trading operations
- Visual workflow canvas with drag-and-drop interface
- Pre-built nodes for labs, bots, analysis, and market data
- Workflow execution with real-time progress tracking
- Workflow templates and sharing capabilities

### 📈 **Market Data**
- Real-time market data visualization with ASCII charts
- Order book visualization and trade history
- Multi-market monitoring and comparison
- Technical indicators and market statistics
- Price alerts and notifications

### 📊 **Analytics**
- Advanced performance analytics and reporting
- Portfolio analysis with risk metrics
- Strategy comparison and benchmarking
- Equity curve visualization
- Risk analysis and correlation matrices

### ⚙️ **Settings**
- MCP server connection configuration
- UI preferences and theme customization
- Logging and data management settings
- Security and credential management
- Backup and restore functionality

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- Terminal with Unicode support
- Access to HaasOnline MCP Server

### Install Dependencies
```bash
pip install textual aiohttp rich pydantic keyring python-dotenv
```

### Quick Start
```bash
# Run the demo (with mock data)
python demo_tui_client.py

# Run with real MCP server
python mcp_tui_client/run.py
```

## 🎮 Usage

### Navigation
- **F1**: Dashboard - System overview and quick actions
- **F2**: Bot Management - Trading bot operations
- **F3**: Lab Management - Backtesting and optimization
- **F4**: Script Editor - HaasScript development
- **F5**: Workflow Designer - Node-based workflows
- **F6**: Market Data - Real-time market information
- **F7**: Analytics - Performance analysis and reporting
- **F8**: Settings - Configuration and preferences

### Global Shortcuts
- **Ctrl+Q**: Quit application
- **Ctrl+R**: Refresh current view
- **Ctrl+H**: Show help
- **Tab/Shift+Tab**: Navigate between panels
- **Enter**: Activate selected item
- **Esc**: Cancel or go back

## 🔧 Configuration

### MCP Server Settings
The TUI client connects to your HaasOnline MCP server. Default configuration:
- Host: `localhost`
- Port: `3002`
- Timeout: `30 seconds`
- Retry attempts: `3`

### Configuration File
Settings are stored in `~/.mcp-tui/config.json`:
```json
{
  "mcp": {
    "host": "localhost",
    "port": 3002,
    "timeout": 30,
    "retry_attempts": 3,
    "use_ssl": false
  },
  "ui": {
    "theme": "dark",
    "auto_refresh_interval": 5,
    "show_help_on_startup": true
  }
}
```

## 🏗 Architecture

### Project Structure
```
mcp_tui_client/
├── __init__.py          # Package initialization
├── app.py               # Main application entry point
├── styles.css           # TUI styling and themes
├── requirements.txt     # Python dependencies
├── run.py              # Application launcher
├── services/           # Business logic and API integration
│   ├── __init__.py
│   ├── config.py       # Configuration management
│   └── mcp_client.py   # MCP server communication
├── ui/                 # User interface components
│   ├── __init__.py
│   ├── dashboard.py    # Dashboard view
│   ├── bots.py         # Bot management interface
│   ├── labs.py         # Lab management interface
│   ├── scripts.py      # Script editor interface
│   ├── workflows.py    # Workflow designer interface
│   ├── markets.py      # Market data interface
│   ├── analytics.py    # Analytics interface
│   └── settings.py     # Settings interface
├── nodes/              # Workflow node system
│   └── __init__.py
└── utils/              # Utility functions
    ├── __init__.py
    └── logging.py      # Logging utilities
```

### Key Components

#### **MCPClientService**
Handles all communication with the HaasOnline MCP server:
- Connection management with retry logic
- Tool execution with error handling
- Real-time data streaming
- Batch operations for efficiency

#### **UI Views**
Modular interface components built with Textual:
- Responsive layout with automatic resizing
- Real-time data updates
- Interactive tables and charts
- Context-sensitive actions

#### **Configuration Service**
Manages application settings and user preferences:
- Secure credential storage
- Theme and UI customization
- Logging configuration
- Backup and restore

## 🔌 MCP Integration

The TUI client integrates with all 97+ MCP server endpoints:

### System & Status (3 endpoints)
- `get_haas_status` - Server health monitoring
- Connection status tracking
- System diagnostics

### Account Management (14 endpoints)
- `get_all_accounts` - Account listing
- `get_account_balance` - Balance information
- `deposit_funds` / `withdraw_funds` - Fund management
- Account statistics and performance

### Bot Management (8 endpoints)
- `get_all_bots` - Bot listing
- `get_bot_details` - Detailed bot information
- `activate_bot` / `deactivate_bot` - Bot control
- `pause_bot` / `resume_bot` - Bot state management

### Lab Management (16 endpoints)
- `get_all_labs` - Lab listing
- `create_lab` / `clone_lab` - Lab creation
- `execute_backtest_intelligent` - Smart backtesting
- Parameter optimization and results analysis

### Script Management (18 endpoints)
- `get_all_scripts` - Script listing
- `add_script` / `edit_script` - Script management
- `save_script` - Script validation and compilation
- Script organization and sharing

### Market Data (9 endpoints)
- `get_all_markets` - Market discovery
- `get_market_snapshot` - Real-time prices
- Order book and trade history
- Cross-market analysis

## 🎨 Customization

### Themes
The TUI supports custom themes through CSS:
- Dark theme (default)
- Light theme
- Custom color schemes
- Panel layout customization

### Keyboard Shortcuts
All shortcuts are customizable through the settings interface.

### Workflow Nodes
The node-based workflow system is extensible:
- Custom node types
- Node parameter validation
- Workflow templates
- Import/export functionality

## 🐛 Troubleshooting

### Common Issues

**Connection Failed**
- Verify MCP server is running
- Check host/port configuration
- Ensure firewall allows connections

**Import Errors**
- Install all required dependencies
- Check Python version (3.8+)
- Verify virtual environment activation

**Display Issues**
- Ensure terminal supports Unicode
- Try different terminal applications
- Check terminal size (minimum 80x24)

### Logging
Logs are stored in `~/.mcp-tui/logs/app.log`:
```bash
# View recent logs
tail -f ~/.mcp-tui/logs/app.log

# Debug mode
export LOG_LEVEL=DEBUG
python mcp_tui_client/run.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd mcp-tui-client

# Install development dependencies
pip install -r requirements.txt
pip install pytest black mypy

# Run tests
pytest

# Format code
black mcp_tui_client/

# Type checking
mypy mcp_tui_client/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Textual](https://textual.textualize.io/) - Modern TUI framework
- [Rich](https://rich.readthedocs.io/) - Rich text and beautiful formatting
- [HaasOnline](https://www.haasonline.com/) - Advanced trading platform
- Model Context Protocol (MCP) - Standardized AI integration

---

**Happy Trading! 🚀📈**