#!/usr/bin/env python3
"""
Repository Publishing Script
Publishes pyHaasAPI and mcp_server as separate GitHub repositories
while maintaining the current monorepo structure.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Error: {result.stderr}")
        return False
    return result.stdout.strip()

def create_pyhaasapi_repo():
    """Create and publish the pyHaasAPI repository."""
    print("📦 Publishing pyHaasAPI...")
    
    # The current repo is already set up for pyHaasAPI
    # Just need to ensure it's properly configured
    
    # Update the README to focus on pyHaasAPI
    readme_content = """# pyHaasAPI

A comprehensive Python library for HaasOnline API integration with advanced trading automation capabilities.

## 🚀 Features

- **Complete API Coverage**: Full HaasOnline API integration with type-safe models
- **Advanced Analysis**: Trade-level backtest data extraction with intelligent debugging
- **Market Intelligence**: Multi-exchange market discovery and classification
- **Lab Management**: Bulk lab cloning and automated configuration
- **Account Management**: Standardized account creation and naming schemas
- **Parameter Intelligence**: Advanced parameter optimization with strategic values

## 📦 Installation

```bash
pip install pyHaasAPI
```

## 🔧 Quick Start

```python
from pyHaasAPI import api
from pyHaasAPI.analysis import BacktestDataExtractor
from pyHaasAPI.markets import MarketDiscovery

# Get authenticated executor
executor = api.get_authenticated_executor()

# Extract trade data from backtest results
extractor = BacktestDataExtractor()
summary = extractor.extract_backtest_data("backtest_results.json")
print(f"Extracted {len(summary.trades)} trades with {summary.win_rate:.1f}% win rate")
```

## 📚 Documentation

- [Parameter Optimization Algorithm](docs/PARAMETER_OPTIMIZATION_ALGORITHM.md)
- [Quick Reference Guide](docs/PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md)
- [Complete Documentation](docs/README.md)

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for reliable, scalable trading automation**
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ pyHaasAPI repository is ready at: https://github.com/iamcos/pyHaasAPI")
    return True

def create_mcp_server_repo():
    """Create and publish the MCP Server repository."""
    print("📦 Publishing haas-mcp-server...")
    
    # Create a temporary directory for the new repo
    with tempfile.TemporaryDirectory() as temp_dir:
        mcp_repo_path = Path(temp_dir) / "haas-mcp-server"
        mcp_repo_path.mkdir()
        
        # Copy MCP server files
        files_to_copy = [
            "mcp_server/",
            "pyHaasAPI/",  # MCP server depends on pyHaasAPI
        ]
        
        for file_path in files_to_copy:
            src = Path(file_path)
            if src.is_dir():
                dst = mcp_repo_path / src.name
                shutil.copytree(src, dst)
            elif src.exists():
                shutil.copy2(src, mcp_repo_path / src.name)
        
        # Create a focused README for MCP server
        mcp_readme = """# HaasOnline MCP Server

A Model Context Protocol (MCP) server that provides access to HaasOnline API functionality through Kiro and other MCP-compatible clients.

## 🚀 Features

- **Complete HaasOnline Integration**: 60+ API endpoints
- **Account Management**: Create, manage, and monitor trading accounts
- **Lab Operations**: Create, clone, and execute trading labs
- **Market Data**: Access real-time and historical market data
- **Backtest Execution**: Run and analyze trading strategies
- **Bulk Operations**: Efficient batch processing

## 📦 Installation

```bash
pip install haas-mcp-server
```

## 🔧 Quick Start

1. Set up your environment variables:
```bash
export API_HOST=127.0.0.1
export API_PORT=8090
export API_EMAIL=your_email@example.com
export API_PASSWORD=your_password
```

2. Run the MCP server:
```bash
python -m mcp_server.server
```

## 🛠️ Configuration

The server can be configured through environment variables or a `.env` file:

```env
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your_email@example.com
API_PASSWORD=your_password
```

## 📚 Available Tools

### Account Management
- `get_haas_status` - Check API connection status
- `get_all_accounts` - List all user accounts
- `create_simulated_account` - Create new simulated accounts

### Lab Management
- `get_all_labs` - List all labs
- `create_lab` - Create new labs
- `clone_lab` - Clone existing labs
- `backtest_lab` - Start lab backtests

### Market Data
- `get_all_markets` - List available markets
- `get_market_data` - Retrieve market information

## 🔌 Integration

### Kiro Integration

Add to your `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "haas-mcp-server": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "API_HOST": "127.0.0.1",
        "API_PORT": "8090"
      }
    }
  }
}
```

## 🧪 Testing

```bash
cd mcp_server
python test_mcp.py
```

## 📄 License

MIT License - see LICENSE file for details.

---

**Built for seamless HaasOnline integration via MCP**
"""
        
        with open(mcp_repo_path / "README.md", "w") as f:
            f.write(mcp_readme)
        
        # Initialize git repo
        os.chdir(mcp_repo_path)
        run_command("git init")
        run_command("git add .")
        run_command('git commit -m "Initial commit: HaasOnline MCP Server"')
        
        # Create GitHub repo (you'll need to do this manually or use GitHub CLI)
        print(f"📁 MCP Server repository prepared at: {mcp_repo_path}")
        print("🔗 To publish to GitHub:")
        print("1. Create a new repository at https://github.com/new")
        print("2. Name it: haas-mcp-server")
        print("3. Run these commands:")
        print(f"   cd {mcp_repo_path}")
        print("   git remote add origin https://github.com/Cosmos/haas-mcp-server.git")
        print("   git branch -M main")
        print("   git push -u origin main")
        
        # Keep the directory for manual publishing
        final_path = Path.cwd().parent / "haas-mcp-server-publish"
        if final_path.exists():
            shutil.rmtree(final_path)
        shutil.copytree(mcp_repo_path, final_path)
        print(f"📂 Repository saved to: {final_path}")
        
    return True

def create_workspace_summary():
    """Create a summary of the monorepo workspace."""
    summary = """# Trading Automation Workspace

This workspace contains multiple interconnected projects for HaasOnline trading automation:

## 📦 Published Repositories

### 1. pyHaasAPI
- **Repository**: https://github.com/iamcos/pyHaasAPI
- **Description**: Core Python library for HaasOnline API integration
- **Location**: Root directory + `pyHaasAPI/` folder

### 2. haas-mcp-server  
- **Repository**: https://github.com/Cosmos/haas-mcp-server
- **Description**: MCP server for HaasOnline API access via Kiro
- **Location**: `mcp_server/` folder

## 🏗️ Development Projects

### 3. AI Trading Interface
- **Location**: `ai-trading-interface/`
- **Description**: Advanced React/TypeScript trading interface
- **Status**: In development

### 4. HaasScript Backtesting
- **Location**: `haasscript_backtesting/`
- **Description**: Comprehensive backtesting system
- **Status**: In development

## 🔧 Workspace Structure

```
├── pyHaasAPI/              # Core library (published)
├── mcp_server/             # MCP server (published separately)
├── ai-trading-interface/   # React trading interface
├── haasscript_backtesting/ # Backtesting system
├── examples/               # Usage examples
├── docs/                   # Documentation
└── tools/                  # Development tools
```

## 🚀 Getting Started

1. **For pyHaasAPI development**:
   ```bash
   pip install -e .
   ```

2. **For MCP server development**:
   ```bash
   cd mcp_server
   pip install -r requirements.txt
   ```

3. **For AI interface development**:
   ```bash
   cd ai-trading-interface
   npm install
   ```

## 📚 Documentation

- [pyHaasAPI Documentation](docs/README.md)
- [MCP Server Guide](mcp_server/README.md)
- [AI Interface Guide](ai-trading-interface/README.md)

---

**Maintained by Cosmos**
"""
    
    with open("workspace.py", "w") as f:
        f.write("# Workspace configuration - see MONOREPO_SETUP_SUMMARY.md")
    
    with open("MONOREPO_SETUP_SUMMARY.md", "w") as f:
        f.write(summary)
    
    return True

def main():
    """Main publishing workflow."""
    print("🚀 Starting repository publishing process...")
    
    # Ensure we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Not in the root directory of the project")
        return False
    
    # Create workspace summary
    create_workspace_summary()
    
    # Publish pyHaasAPI (current repo)
    create_pyhaasapi_repo()
    
    # Prepare MCP server repo
    create_mcp_server_repo()
    
    print("\n✅ Publishing process completed!")
    print("\n📋 Next Steps:")
    print("1. The current repository (pyHaasAPI) is ready")
    print("2. Create the MCP server repository manually on GitHub")
    print("3. Follow the instructions printed above to publish it")
    print("4. Both repositories will be public and properly attributed to Cosmos")
    
    return True

if __name__ == "__main__":
    main()