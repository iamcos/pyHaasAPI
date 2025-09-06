#!/usr/bin/env python3
"""
Repository Setup Validation Script
Validates that the dual-repository setup is correctly configured.
"""

import os
import subprocess
from pathlib import Path

def check_command(cmd, description):
    """Check if a command runs successfully."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description}")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Exception: {e}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    if Path(dirpath).is_dir():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

def validate_git_remotes():
    """Validate git remote configurations."""
    print("\n🔗 Validating Git Remotes...")
    
    # Check main repository remote
    success = check_command(
        "git remote get-url origin",
        "Main repository remote configured"
    )
    
    # Check MCP server repository remote
    if Path("haas-mcp-server-repo").exists():
        success &= check_command(
            "git remote get-url origin",
            "MCP server repository remote configured",
        )
    
    return success

def validate_file_structure():
    """Validate required file structure."""
    print("\n📁 Validating File Structure...")
    
    success = True
    
    # Core files
    success &= check_file_exists("pyproject.toml", "Main pyproject.toml exists")
    success &= check_file_exists("LICENSE", "LICENSE file exists")
    success &= check_file_exists("README.md", "README.md exists")
    
    # Core directories
    success &= check_directory_exists("pyHaasAPI", "pyHaasAPI directory exists")
    success &= check_directory_exists("mcp_server", "mcp_server directory exists")
    
    # Management scripts
    success &= check_file_exists("create_mcp_repo.py", "MCP repo creation script exists")
    success &= check_file_exists("update_repositories.py", "Repository update script exists")
    success &= check_file_exists("INTERNAL_REPOSITORY_MANAGEMENT.md", "Internal documentation exists")
    success &= check_file_exists("AI_ASSISTANT_QUICK_REFERENCE.md", "AI assistant reference exists")
    
    # MCP server files
    success &= check_file_exists("mcp_server/server.py", "MCP server main file exists")
    success &= check_file_exists("mcp_server/pyproject.toml", "MCP server pyproject.toml exists")
    success &= check_file_exists("mcp_server/requirements.txt", "MCP server requirements.txt exists")
    
    return success

def validate_python_environment():
    """Validate Python environment."""
    print("\n🐍 Validating Python Environment...")
    
    success = True
    success &= check_command("python --version", "Python is available")
    success &= check_command("git --version", "Git is available")
    
    return success

def validate_repository_status():
    """Validate repository status."""
    print("\n📊 Validating Repository Status...")
    
    success = True
    
    # Check if we're in a git repository
    success &= check_command("git status", "Main repository git status")
    
    # Check MCP server staging repository
    if Path("haas-mcp-server-repo").exists():
        original_dir = os.getcwd()
        try:
            os.chdir("haas-mcp-server-repo")
            success &= check_command("git status", "MCP server staging git status")
        finally:
            os.chdir(original_dir)
    
    return success

def main():
    """Run all validation checks."""
    print("🔍 Repository Setup Validation")
    print("=" * 50)
    
    all_success = True
    
    # Run validation checks
    all_success &= validate_python_environment()
    all_success &= validate_file_structure()
    all_success &= validate_repository_status()
    all_success &= validate_git_remotes()
    
    print("\n" + "=" * 50)
    
    if all_success:
        print("🎉 All validation checks passed!")
        print("✅ Repository setup is correctly configured")
        print("\n📚 Available commands:")
        print("  • python update_repositories.py  - Update both repositories")
        print("  • python create_mcp_repo.py      - Regenerate MCP staging")
        print("  • python validate_setup.py       - Run this validation again")
        print("\n📖 Documentation:")
        print("  • INTERNAL_REPOSITORY_MANAGEMENT.md - Full management guide")
        print("  • AI_ASSISTANT_QUICK_REFERENCE.md   - Quick reference for AI")
    else:
        print("❌ Some validation checks failed!")
        print("🔧 Please fix the issues above before proceeding")
        print("\n📋 Common fixes:")
        print("  • Ensure you're in the project root directory")
        print("  • Run 'python create_mcp_repo.py' to create MCP staging")
        print("  • Check git remote configurations")
    
    return all_success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)