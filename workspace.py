#!/usr/bin/env python3
"""
Workspace management script for the trading automation monorepo.
Provides easy commands to build, test, and publish individual projects.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional

class WorkspaceManager:
    def __init__(self):
        self.root = Path(__file__).parent
        self.projects = {
            'pyhaasapi': self.root / 'pyHaasAPI',
            'mcp-server': self.root / 'mcp_server',
        }
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> int:
        """Run a command and return the exit code."""
        print(f"Running: {' '.join(cmd)}")
        if cwd:
            print(f"In directory: {cwd}")
        
        result = subprocess.run(cmd, cwd=cwd or self.root)
        return result.returncode
    
    def install_deps(self, project: Optional[str] = None):
        """Install dependencies for a project or all projects."""
        if project:
            if project not in self.projects:
                print(f"Unknown project: {project}")
                return 1
            
            print(f"Installing dependencies for {project}...")
            return self.run_command(['poetry', 'install'], self.projects[project])
        else:
            print("Installing dependencies for all projects...")
            # Install root workspace dependencies first
            result = self.run_command(['poetry', 'install'])
            if result != 0:
                return result
            
            # Then install each project's dependencies
            for proj_name, proj_path in self.projects.items():
                print(f"\nInstalling {proj_name} dependencies...")
                result = self.run_command(['poetry', 'install'], proj_path)
                if result != 0:
                    return result
            return 0
    
    def build(self, project: str):
        """Build a specific project."""
        if project not in self.projects:
            print(f"Unknown project: {project}")
            return 1
        
        print(f"Building {project}...")
        return self.run_command(['poetry', 'build'], self.projects[project])
    
    def test(self, project: Optional[str] = None):
        """Run tests for a project or all projects."""
        if project:
            if project not in self.projects:
                print(f"Unknown project: {project}")
                return 1
            
            print(f"Running tests for {project}...")
            return self.run_command(['poetry', 'run', 'pytest'], self.projects[project])
        else:
            print("Running tests for all projects...")
            for proj_name, proj_path in self.projects.items():
                print(f"\nTesting {proj_name}...")
                result = self.run_command(['poetry', 'run', 'pytest'], proj_path)
                if result != 0:
                    print(f"Tests failed for {proj_name}")
                    return result
            return 0
    
    def publish(self, project: str, repository: str = "pypi"):
        """Publish a project to PyPI or another repository."""
        if project not in self.projects:
            print(f"Unknown project: {project}")
            return 1
        
        # Build first
        result = self.build(project)
        if result != 0:
            print(f"Build failed for {project}")
            return result
        
        # Then publish
        print(f"Publishing {project} to {repository}...")
        cmd = ['poetry', 'publish']
        if repository != "pypi":
            cmd.extend(['-r', repository])
        
        return self.run_command(cmd, self.projects[project])
    
    def clean(self, project: Optional[str] = None):
        """Clean build artifacts."""
        if project:
            if project not in self.projects:
                print(f"Unknown project: {project}")
                return 1
            
            proj_path = self.projects[project]
            print(f"Cleaning {project}...")
            
            # Remove common build artifacts
            for pattern in ['dist', 'build', '*.egg-info', '__pycache__']:
                for path in proj_path.rglob(pattern):
                    if path.is_dir():
                        print(f"Removing directory: {path}")
                        subprocess.run(['rm', '-rf', str(path)])
                    elif path.is_file():
                        print(f"Removing file: {path}")
                        path.unlink()
        else:
            print("Cleaning all projects...")
            for proj_name in self.projects:
                self.clean(proj_name)
        
        return 0
    
    def status(self):
        """Show status of all projects."""
        print("Workspace Status:")
        print("=" * 50)
        
        for proj_name, proj_path in self.projects.items():
            print(f"\n{proj_name.upper()}:")
            print(f"  Path: {proj_path}")
            print(f"  Exists: {proj_path.exists()}")
            
            pyproject = proj_path / 'pyproject.toml'
            if pyproject.exists():
                print(f"  Has pyproject.toml: ✓")
                # Try to get version
                try:
                    result = subprocess.run(
                        ['poetry', 'version'], 
                        cwd=proj_path, 
                        capture_output=True, 
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"  Version: {result.stdout.strip()}")
                except:
                    print(f"  Version: Unable to determine")
            else:
                print(f"  Has pyproject.toml: ✗")

def main():
    manager = WorkspaceManager()
    
    if len(sys.argv) < 2:
        print("Usage: python workspace.py <command> [options]")
        print("\nCommands:")
        print("  install [project]     - Install dependencies")
        print("  build <project>       - Build a project")
        print("  test [project]        - Run tests")
        print("  publish <project>     - Publish to PyPI")
        print("  clean [project]       - Clean build artifacts")
        print("  status                - Show workspace status")
        print("\nProjects: pyhaasapi, mcp-server")
        return 1
    
    command = sys.argv[1]
    
    if command == 'install':
        project = sys.argv[2] if len(sys.argv) > 2 else None
        return manager.install_deps(project)
    
    elif command == 'build':
        if len(sys.argv) < 3:
            print("Error: build command requires a project name")
            return 1
        return manager.build(sys.argv[2])
    
    elif command == 'test':
        project = sys.argv[2] if len(sys.argv) > 2 else None
        return manager.test(project)
    
    elif command == 'publish':
        if len(sys.argv) < 3:
            print("Error: publish command requires a project name")
            return 1
        repository = sys.argv[3] if len(sys.argv) > 3 else "pypi"
        return manager.publish(sys.argv[2], repository)
    
    elif command == 'clean':
        project = sys.argv[2] if len(sys.argv) > 2 else None
        return manager.clean(project)
    
    elif command == 'status':
        return manager.status()
    
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == '__main__':
    sys.exit(main())