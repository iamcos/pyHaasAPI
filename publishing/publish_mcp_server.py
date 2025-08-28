#!/usr/bin/env python3
"""
Publish MCP Server to Private GitHub Repository

This script publishes the MCP server to the private haas_mcp_server repository.
The server is not available on PyPI and must be installed from source.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

def publish_mcp_server():
    """Publish MCP server to private GitHub repository."""
    
    print("🚀 Publishing HaasOnline MCP Server to Private Repository")
    print("=" * 60)
    
    # Repository configuration
    repo_url = "https://github.com/iamcos/haas_mcp_server.git"
    repo_name = "haas_mcp_server"
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        repo_path = temp_path / repo_name
        
        print(f"📁 Working in temporary directory: {temp_path}")
        
        # Clone or create repository
        try:
            print(f"📥 Cloning repository from {repo_url}")
            subprocess.run([
                "git", "clone", repo_url, str(repo_path)
            ], check=True, cwd=temp_path)
        except subprocess.CalledProcessError:
            print("📝 Repository doesn't exist yet, creating new one...")
            repo_path.mkdir()
            subprocess.run(["git", "init"], check=True, cwd=repo_path)
            subprocess.run([
                "git", "remote", "add", "origin", repo_url
            ], check=True, cwd=repo_path)
        
        # Clear existing content (except .git)
        for item in repo_path.iterdir():
            if item.name != ".git":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        # Copy MCP server files
        print("📋 Copying MCP server files...")
        
        # Essential files to copy
        files_to_copy = [
            ("mcp_server/server.py", "server.py"),
            ("mcp_server/pyproject.toml", "pyproject.toml"),
            ("mcp_server/LICENSE", "LICENSE"),
            ("mcp_server/.gitignore", ".gitignore"),
        ]
        
        # Copy files
        for src, dst in files_to_copy:
            src_path = Path(src)
            if src_path.exists():
                print(f"  📄 {src} → {dst}")
                shutil.copy2(src_path, repo_path / dst)
            else:
                print(f"  ⚠️  Missing: {src}")
        
        # Create requirements.txt if it doesn't exist
        requirements_path = repo_path / "requirements.txt"
        if not requirements_path.exists():
            print("  📄 Creating requirements.txt")
            requirements_content = """mcp>=1.0.0
python-dotenv>=1.0.0
requests>=2.25.0
pydantic>=2.0.0
"""
            requirements_path.write_text(requirements_content)
        
        # Create comprehensive README
        print("  📄 Creating README.md")
        readme_content = """# HaasOnline MCP Server

**Private Repository** - Model Context Protocol server for HaasOnline API integration.

## 🎯 **Overview**

This MCP server exposes **65 HaasOnline API endpoints** as MCP tools, enabling AI models to interact directly with HaasOnline trading platform through natural language.

## ✨ **Key Features**

- **🔄 AI Script Editing** - Real-time validation and compilation feedback
- **⚙️ Server Management** - Complete automation pipelines  
- **📊 Data Visualization** - Generate charts and analytics
- **🤖 Bot Management** - Full lifecycle automation
- **🎯 Fine-tuning** - Single backtest executions for optimization
- **📈 Smart Backtesting** - Automatic history cutoff detection

## 📦 **Installation**

**Install from source** (not available on PyPI):

```bash
# Install pyHaasAPI dependency first
pip install git+https://github.com/iamcos/pyHaasAPI.git

# Install MCP server
pip install git+https://github.com/iamcos/haas_mcp_server.git
```

## ⚙️ **Configuration**

1. **Environment Setup**:
```bash
# .env file
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL_LOCAL=your_email@example.com
API_PASSWORD_LOCAL=your_password
```

2. **MCP Client Configuration**:
```json
{
  "mcpServers": {
    "haas-api": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "API_HOST": "127.0.0.1",
        "API_PORT": "8090"
      }
    }
  }
}
```

## 🚀 **Usage**

### **Start Server**
```bash
python server.py
```

### **Available Tools** (65 total)
- **Script Management**: `save_script`, `validate_script`, `share_script`
- **Lab Operations**: `create_lab`, `clone_lab`, `backtest_lab`
- **Bot Management**: `create_bot`, `activate_bot`, `deactivate_bot`
- **Market Data**: `get_market_price`, `get_order_book`, `get_last_trades`
- **Account Management**: `get_accounts`, `get_balance`, `deposit_funds`
- **Backtesting**: `execute_backtest`, `get_backtest_results`, `cancel_backtest`

## 🎭 **Interaction Paradigms**

**1. Direct Chat** - Natural language commands to your HaasOnline server

**2. AI-Enhanced Development** - Comprehensive documentation enables effortless coding workflows for complex server interactions

**3. Universal Strategy Conversion** - Convert anything (PineScript, Python, descriptions, TradingView ideas, scientific papers) into HaasScript strategies

## 🔧 **Requirements**

- **Python 3.8+**
- **HaasOnline Community License** or higher
- **MCP-compatible client** (Kiro, Cursor, etc.)
- **pyHaasAPI library** (dependency)

## 🤝 **Access**

This is a **private repository** for early adopters and supporters who see the benefit of automating complex trading workflows involving intricate backtesting scenarios and fine-tuning.

## 📄 **License**

Dual licensed under MIT and Apache 2.0.

---

**For access requests and support, contact the maintainers directly.**
"""
        
        readme_path = repo_path / "README.md"
        readme_path.write_text(readme_content)
        
        # Create setup.py for installation
        print("  📄 Creating setup.py")
        setup_content = '''#!/usr/bin/env python3
"""
Setup script for HaasOnline MCP Server
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="haas-mcp-server",
    version="1.0.0",
    author="HaasOnline MCP Team",
    description="Model Context Protocol server for HaasOnline API integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["server"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=1.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.25.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "haas-mcp-server=server:main",
        ],
    },
)
'''
        setup_path = repo_path / "setup.py"
        setup_path.write_text(setup_content)
        
        # Git operations
        print("\n🔄 Preparing Git commit...")
        
        # Configure git if needed
        try:
            subprocess.run(["git", "config", "user.name"], 
                         check=True, capture_output=True, cwd=repo_path)
        except subprocess.CalledProcessError:
            subprocess.run(["git", "config", "user.name", "MCP Publisher"], 
                         check=True, cwd=repo_path)
            subprocess.run(["git", "config", "user.email", "mcp@haasonline.com"], 
                         check=True, cwd=repo_path)
        
        # Add all files
        subprocess.run(["git", "add", "."], check=True, cwd=repo_path)
        
        # Check if there are changes to commit
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, cwd=repo_path)
        
        if result.stdout.strip():
            # Get commit message
            commit_message = input("\n💬 Enter commit message (or press Enter for default): ").strip()
            if not commit_message:
                commit_message = "Update MCP server with latest functionality"
            
            # Commit changes
            subprocess.run(["git", "commit", "-m", commit_message], 
                         check=True, cwd=repo_path)
            
            # Push to repository
            print(f"📤 Pushing to {repo_url}")
            try:
                subprocess.run(["git", "push", "origin", "main"], 
                             check=True, cwd=repo_path)
                print("✅ Successfully pushed to GitHub!")
            except subprocess.CalledProcessError:
                try:
                    # Try master branch if main doesn't exist
                    subprocess.run(["git", "push", "origin", "master"], 
                                 check=True, cwd=repo_path)
                    print("✅ Successfully pushed to GitHub!")
                except subprocess.CalledProcessError:
                    # First push
                    subprocess.run(["git", "branch", "-M", "main"], 
                                 check=True, cwd=repo_path)
                    subprocess.run(["git", "push", "-u", "origin", "main"], 
                                 check=True, cwd=repo_path)
                    print("✅ Successfully created and pushed to GitHub!")
        else:
            print("📝 No changes to commit - repository is up to date")
    
    print("\n🎉 MCP Server publishing completed!")
    print(f"\n📋 Installation instructions:")
    print(f"pip install git+{repo_url}")

if __name__ == "__main__":
    publish_mcp_server()