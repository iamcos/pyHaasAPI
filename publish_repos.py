#!/usr/bin/env python3
"""
Script to publish individual projects to separate GitHub repositories.
This handles the monorepo → separate repos publishing workflow.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from typing import List, Optional
import tempfile

class RepoPublisher:
    def __init__(self):
        self.root = Path(__file__).parent
        self.projects = {
            'pyhaasapi': {
                'source_dir': self.root / 'pyHaasAPI',
                'repo_url': 'https://github.com/Cosmos/pyHaasAPI.git',
                'include_files': [
                    'pyHaasAPI/',
                    'examples/',
                    'tests/',
                    'docs/',
                    'pyproject.toml',
                    'README.md',
                    'LICENSE',
                    '.gitignore'
                ]
            },
            'mcp-server': {
                'source_dir': self.root / 'mcp_server',
                'repo_url': 'https://github.com/Cosmos/haas-mcp-server.git',
                'include_files': [
                    'mcp_server/',
                    'automation/',
                    'endpoints/',
                    'tests/',
                    'workflows/',
                    'pyproject.toml',
                    'README.md',
                    'LICENSE',
                    'requirements.txt',
                    'setup.py',
                    '.gitignore'
                ]
            }
        }
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(cmd)}")
        if cwd:
            print(f"In directory: {cwd}")
        
        return subprocess.run(
            cmd, 
            cwd=cwd or self.root,
            capture_output=capture_output,
            text=True
        )
    
    def create_project_readme(self, project: str, temp_dir: Path):
        """Create a project-specific README."""
        if project == 'pyhaasapi':
            readme_content = """# pyHaasAPI

Python library for HaasOnline API integration with advanced trading automation capabilities.

## Features

- **Complete API Coverage**: Full HaasOnline API integration with type-safe models
- **Advanced Analysis**: Trade-level backtest data extraction with intelligent debugging
- **Market Intelligence**: Multi-exchange market discovery and classification
- **Lab Management**: Bulk lab cloning and automated configuration
- **Account Management**: Standardized account creation and naming schemas
- **Parameter Intelligence**: Advanced parameter optimization with strategic values

## Installation

```bash
pip install pyHaasAPI
```

## Quick Start

```python
from pyHaasAPI import api
from pyHaasAPI.analysis import BacktestDataExtractor

# Get authenticated executor
executor = api.get_authenticated_executor()

# Extract trade data from backtest results
extractor = BacktestDataExtractor()
summary = extractor.extract_backtest_data("backtest_results.json")
print(f"Extracted {len(summary.trades)} trades with {summary.win_rate:.1f}% win rate")
```

## Documentation

See the [full documentation](https://github.com/Cosmos/pyHaasAPI/tree/main/docs) for detailed usage examples.

## License

MIT License - see LICENSE file for details.
"""
        elif project == 'mcp-server':
            readme_content = """# HaasOnline MCP Server

Model Context Protocol (MCP) server that provides access to HaasOnline API functionality through Kiro and other MCP-compatible clients.

## Features

- **60+ API Endpoints**: Complete HaasOnline API coverage
- **Account Management**: Create and manage simulated accounts
- **Lab Operations**: Create, clone, delete, and backtest labs
- **Market Data**: Access to 12,398+ real markets
- **Bulk Operations**: Automated lab creation and execution

## Installation

```bash
pip install haas-mcp-server
```

## Usage

1. Set up your environment variables:
   ```bash
   API_HOST=127.0.0.1
   API_PORT=8090
   API_EMAIL=your_email@example.com
   API_PASSWORD=your_password
   ```

2. Start the server:
   ```bash
   haas-mcp-server
   ```

3. Configure in your MCP client (e.g., Kiro):
   ```json
   {
     "mcpServers": {
       "haas-mcp-server": {
         "command": "haas-mcp-server",
         "args": []
       }
     }
   }
   ```

## Documentation

See the [full documentation](https://github.com/Cosmos/haas-mcp-server/blob/main/README.md) for detailed setup and usage.

## License

MIT License - see LICENSE file for details.
"""
        
        readme_path = temp_dir / 'README.md'
        readme_path.write_text(readme_content)
        print(f"Created project-specific README for {project}")
    
    def prepare_project_files(self, project: str, temp_dir: Path):
        """Prepare files for a specific project in a temporary directory."""
        if project not in self.projects:
            raise ValueError(f"Unknown project: {project}")
        
        config = self.projects[project]
        source_dir = config['source_dir']
        
        print(f"Preparing files for {project}...")
        
        # Copy project-specific files
        for file_pattern in config['include_files']:
            source_path = source_dir / file_pattern
            dest_path = temp_dir / file_pattern
            
            if source_path.exists():
                if source_path.is_dir():
                    print(f"Copying directory: {source_path} -> {dest_path}")
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                else:
                    print(f"Copying file: {source_path} -> {dest_path}")
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
            else:
                print(f"Warning: {source_path} does not exist, skipping")
        
        # Copy shared files from root
        shared_files = ['LICENSE']
        for shared_file in shared_files:
            source_path = self.root / shared_file
            if source_path.exists():
                dest_path = temp_dir / shared_file
                print(f"Copying shared file: {source_path} -> {dest_path}")
                shutil.copy2(source_path, dest_path)
        
        # Create project-specific README
        self.create_project_readme(project, temp_dir)
        
        # Create .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv/
venv/
ENV/
env/

# IDE and editors
.DS_Store
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
logs/
results/
data/
*.log
*.json

# Temporary files
*.tmp
*.temp
"""
        gitignore_path = temp_dir / '.gitignore'
        gitignore_path.write_text(gitignore_content)
    
    def publish_to_github(self, project: str, create_repo: bool = False):
        """Publish a project to its GitHub repository."""
        if project not in self.projects:
            raise ValueError(f"Unknown project: {project}")
        
        config = self.projects[project]
        repo_url = config['repo_url']
        
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            
            # Prepare project files
            self.prepare_project_files(project, temp_dir)
            
            # Initialize git repo
            print(f"Initializing git repository for {project}...")
            self.run_command(['git', 'init'], temp_dir)
            self.run_command(['git', 'add', '.'], temp_dir)
            self.run_command(['git', 'commit', '-m', f'Initial commit for {project}'], temp_dir)
            
            # Add remote and push
            print(f"Adding remote and pushing to {repo_url}...")
            self.run_command(['git', 'remote', 'add', 'origin', repo_url], temp_dir)
            
            # Try to push to main branch
            result = self.run_command(['git', 'push', '-u', 'origin', 'main'], temp_dir)
            if result.returncode != 0:
                # Try master branch if main fails
                print("Failed to push to main, trying master...")
                self.run_command(['git', 'branch', '-M', 'master'], temp_dir)
                result = self.run_command(['git', 'push', '-u', 'origin', 'master'], temp_dir)
            
            if result.returncode == 0:
                print(f"✅ Successfully published {project} to {repo_url}")
            else:
                print(f"❌ Failed to publish {project}")
                return False
        
        return True
    
    def create_github_repo(self, project: str):
        """Create a GitHub repository using GitHub CLI."""
        if project not in self.projects:
            raise ValueError(f"Unknown project: {project}")
        
        config = self.projects[project]
        repo_name = config['repo_url'].split('/')[-1].replace('.git', '')
        
        # Check if gh CLI is available
        result = self.run_command(['which', 'gh'], capture_output=True)
        if result.returncode != 0:
            print("GitHub CLI (gh) not found. Please install it or create the repository manually.")
            print(f"Repository URL: {config['repo_url']}")
            return False
        
        # Create the repository
        print(f"Creating GitHub repository: {repo_name}")
        result = self.run_command([
            'gh', 'repo', 'create', repo_name,
            '--public',
            '--description', f'{project} - Trading automation project'
        ], capture_output=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully created repository: {repo_name}")
            return True
        else:
            print(f"❌ Failed to create repository: {result.stderr}")
            return False

def main():
    publisher = RepoPublisher()
    
    if len(sys.argv) < 2:
        print("Usage: python publish_repos.py <command> [project]")
        print("\nCommands:")
        print("  create <project>      - Create GitHub repository")
        print("  publish <project>     - Publish project to GitHub")
        print("  publish-all           - Publish all projects")
        print("\nProjects: pyhaasapi, mcp-server")
        return 1
    
    command = sys.argv[1]
    
    if command == 'create':
        if len(sys.argv) < 3:
            print("Error: create command requires a project name")
            return 1
        
        project = sys.argv[2]
        return 0 if publisher.create_github_repo(project) else 1
    
    elif command == 'publish':
        if len(sys.argv) < 3:
            print("Error: publish command requires a project name")
            return 1
        
        project = sys.argv[2]
        return 0 if publisher.publish_to_github(project) else 1
    
    elif command == 'publish-all':
        success = True
        for project in publisher.projects.keys():
            print(f"\n{'='*50}")
            print(f"Publishing {project}...")
            print(f"{'='*50}")
            
            if not publisher.publish_to_github(project):
                success = False
        
        return 0 if success else 1
    
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == '__main__':
    sys.exit(main())