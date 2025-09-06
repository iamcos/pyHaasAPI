#!/usr/bin/env python3
"""
Create MCP Server Repository
This script creates a clean MCP server repository structure
"""

import os
import shutil
from pathlib import Path

def create_mcp_server_repo():
    """Create the MCP server repository structure."""
    
    # Create the repository directory
    repo_dir = Path("haas-mcp-server-repo")
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir()
    
    # Copy essential files
    files_to_copy = [
        ("mcp_server/server.py", "server.py"),
        ("mcp_server/requirements.txt", "requirements.txt"),
        ("mcp_server/setup.py", "setup.py"),
        ("mcp_server/pyproject.toml", "pyproject.toml"),
        ("mcp_server/LICENSE", "LICENSE"),
        ("mcp_server/.gitignore", ".gitignore"),
    ]
    
    for src, dst in files_to_copy:
        src_path = Path(src)
        if src_path.exists():
            shutil.copy2(src_path, repo_dir / dst)
    
    # Copy directories
    dirs_to_copy = [
        ("mcp_server/endpoints", "endpoints"),
        ("mcp_server/automation", "automation"),
        ("mcp_server/workflows", "workflows"),
        ("mcp_server/tests", "tests"),
    ]
    
    for src, dst in dirs_to_copy:
        src_path = Path(src)
        if src_path.exists():
            shutil.copytree(src_path, repo_dir / dst)
    
    # Create a focused README
    readme_content = """# HaasOnline MCP Server

A Model Context Protocol (MCP) server that provides access to HaasOnline API functionality.

## Features

- **Complete HaasOnline Integration**: 60+ API endpoints
- **Account Management**: Create and manage trading accounts
- **Lab Operations**: Create, clone, and execute trading labs
- **Market Data**: Access real-time and historical market data
- **Backtest Execution**: Run and analyze trading strategies

## Installation

```bash
pip install haas-mcp-server
```

## Quick Start

1. Set up environment variables:
```bash
export API_HOST=127.0.0.1
export API_PORT=8090
export API_EMAIL=your_email@example.com
export API_PASSWORD=your_password
```

2. Run the server:
```bash
python server.py
```

## Configuration

Configure via `.env` file or environment variables:

```env
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your_email@example.com
API_PASSWORD=your_password
```

## License

MIT License - see LICENSE file for details.

---

**Author: Cosmos**
"""
    
    with open(repo_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    # Create __init__.py
    with open(repo_dir / "__init__.py", "w") as f:
        f.write('"""HaasOnline MCP Server"""\n__version__ = "1.0.0"\n')
    
    print(f"✅ MCP Server repository created at: {repo_dir}")
    print("\n📋 To publish to GitHub:")
    print(f"1. cd {repo_dir}")
    print("2. git init")
    print("3. git add .")
    print('4. git commit -m "Initial commit"')
    print("5. Create repository at https://github.com/new (name: haas-mcp-server)")
    print("6. git remote add origin https://github.com/Cosmos/haas-mcp-server.git")
    print("7. git branch -M main")
    print("8. git push -u origin main")
    
    return repo_dir

if __name__ == "__main__":
    create_mcp_server_repo()