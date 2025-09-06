#!/usr/bin/env python3
"""
Repository Update Script
Automated script for updating both pyHaasAPI and haas-mcp-server repositories.
FOR AI ASSISTANTS: Use this script to safely update repositories.
"""

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"❌ Error running command: {cmd}")
        print(f"Error: {result.stderr}")
        return False, result.stderr
    
    if result.stdout.strip():
        print(f"✅ Output: {result.stdout.strip()}")
    
    return True, result.stdout.strip()

def check_git_status():
    """Check if there are uncommitted changes."""
    success, output = run_command("git status --porcelain")
    if not success:
        return False
    
    if output.strip():
        print("⚠️  Warning: Uncommitted changes detected:")
        print(output)
        response = input("Continue anyway? (y/N): ")
        return response.lower() == 'y'
    
    return True

def update_pyhaasapi(commit_message):
    """Update the pyHaasAPI repository."""
    print("\n📦 Updating pyHaasAPI repository...")
    
    # Add all changes
    success, _ = run_command("git add .")
    if not success:
        return False
    
    # Commit changes
    success, _ = run_command(f'git commit -m "{commit_message}"')
    if not success:
        print("ℹ️  No changes to commit for pyHaasAPI")
        return True
    
    # Push to master branch
    success, _ = run_command("git push origin master")
    if not success:
        return False
    
    print("✅ pyHaasAPI repository updated successfully!")
    return True

def update_mcp_server(commit_message):
    """Update the haas-mcp-server repository."""
    print("\n📦 Updating haas-mcp-server repository...")
    
    # Check if mcp_server directory exists
    if not Path("mcp_server").exists():
        print("❌ mcp_server directory not found!")
        return False
    
    # Regenerate the staging repository
    print("🔄 Regenerating MCP server staging repository...")
    success, _ = run_command("python create_mcp_repo.py")
    if not success:
        return False
    
    # Navigate to staging directory
    staging_dir = "haas-mcp-server-repo"
    if not Path(staging_dir).exists():
        print(f"❌ Staging directory {staging_dir} not found!")
        return False
    
    # Check for changes in staging
    success, output = run_command("git status --porcelain", cwd=staging_dir)
    if not success:
        return False
    
    if not output.strip():
        print("ℹ️  No changes to commit for MCP server")
        return True
    
    # Add changes
    success, _ = run_command("git add .", cwd=staging_dir)
    if not success:
        return False
    
    # Commit changes
    success, _ = run_command(f'git commit -m "{commit_message}"', cwd=staging_dir)
    if not success:
        return False
    
    # Push to main branch
    success, _ = run_command("git push origin main", cwd=staging_dir)
    if not success:
        return False
    
    print("✅ haas-mcp-server repository updated successfully!")
    return True

def get_commit_message():
    """Get commit message from user."""
    print("\n📝 Enter commit message details:")
    
    # Get commit type
    commit_types = ["Update", "Fix", "Add", "Remove", "Refactor", "Docs", "Config"]
    print("Available commit types:")
    for i, ctype in enumerate(commit_types, 1):
        print(f"  {i}. {ctype}")
    
    while True:
        try:
            choice = int(input("Select commit type (1-7): "))
            if 1 <= choice <= 7:
                commit_type = commit_types[choice - 1]
                break
            else:
                print("Please enter a number between 1 and 7")
        except ValueError:
            print("Please enter a valid number")
    
    # Get brief description
    brief = input("Brief description: ").strip()
    if not brief:
        brief = "Repository updates"
    
    # Get detailed changes
    print("\nEnter detailed changes (one per line, empty line to finish):")
    changes = []
    while True:
        change = input("- ").strip()
        if not change:
            break
        changes.append(f"- {change}")
    
    # Build commit message
    commit_message = f"{commit_type}: {brief}"
    if changes:
        commit_message += "\n\n" + "\n".join(changes)
    
    return commit_message

def main():
    """Main update workflow."""
    print("🚀 Repository Update Script")
    print("=" * 50)
    
    # Verify we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Not in the root directory of the project")
        print("Please run this script from the pyHaasAPI root directory")
        return False
    
    # Check git status
    if not check_git_status():
        print("❌ Aborting due to uncommitted changes")
        return False
    
    # Get commit message
    commit_message = get_commit_message()
    
    print(f"\n📋 Commit message preview:")
    print("-" * 30)
    print(commit_message)
    print("-" * 30)
    
    confirm = input("\nProceed with updates? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Update cancelled")
        return False
    
    # Update repositories
    success = True
    
    # Ask which repositories to update
    print("\nWhich repositories should be updated?")
    update_pyhaas = input("Update pyHaasAPI? (Y/n): ").lower() != 'n'
    update_mcp = input("Update haas-mcp-server? (Y/n): ").lower() != 'n'
    
    if update_pyhaas:
        success &= update_pyhaasapi(commit_message)
    
    if update_mcp:
        success &= update_mcp_server(commit_message)
    
    if success:
        print("\n🎉 All repository updates completed successfully!")
        print(f"📅 Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show repository URLs
        print("\n🔗 Repository URLs:")
        if update_pyhaas:
            print("  • pyHaasAPI: https://github.com/iamcos/pyHaasAPI")
        if update_mcp:
            print("  • haas-mcp-server: https://github.com/iamcos/haas-mcp-server")
    else:
        print("\n❌ Some updates failed. Please check the errors above.")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)