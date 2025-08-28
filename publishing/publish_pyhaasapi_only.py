#!/usr/bin/env python3
"""
Selective Publishing Script for pyHaasAPI
Publishes only the core pyHaasAPI library to GitHub while keeping local monorepo intact.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

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

def create_clean_pyhaasapi_repo():
    """Create a clean pyHaasAPI repository with only essential files."""
    
    # Files and directories to include in the published repository
    files_to_include = [
        "pyHaasAPI/",           # Core library
        "docs/",                # Documentation
        "examples/",            # Usage examples  
        "experiments/",         # Experimental features
        "tests/",               # Test suite
        "pyproject.toml",       # Package configuration
        "README.md",            # Main documentation
        "LICENSE",              # MIT License
        ".gitignore",           # Git ignore rules
        "rules.cursor",         # Development rules
        "RUNNING_TESTS.cursor", # Testing guidelines
    ]
    
    # Create temp directory for clean repository (using project temp folder)
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    clean_repo_path = temp_dir / "pyhaasapi-clean"
    
    # Clean up any existing temp repo
    if clean_repo_path.exists():
        shutil.rmtree(clean_repo_path)
    
    clean_repo_path.mkdir()
        
    print("📦 Creating clean pyHaasAPI repository...")
    
    # Copy essential files and directories
    for item in files_to_include:
        src_path = Path(item)
        dst_path = clean_repo_path / item
        
        if src_path.exists():
            if src_path.is_dir():
                print(f"📁 Copying directory: {item}")
                shutil.copytree(src_path, dst_path)
            else:
                print(f"📄 Copying file: {item}")
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
        else:
            print(f"⚠️  Item not found (skipping): {item}")
    
    # Initialize git repository
    os.chdir(clean_repo_path)
    run_command("git init")
    run_command("git add .")
    
    # Get commit message
    commit_message = input("\n📝 Enter commit message for pyHaasAPI update: ").strip()
    if not commit_message:
        commit_message = "Update pyHaasAPI library"
    
    run_command(f'git commit -m "{commit_message}"')
    
    # Add remote and push
    run_command("git remote add origin https://github.com/iamcos/pyHaasAPI.git")
    run_command("git branch -M master")
    
    print("\n🚀 Pushing clean pyHaasAPI to GitHub...")
    success, output = run_command("git push --force origin master")
    
    if success:
        print("✅ pyHaasAPI successfully published to GitHub!")
        print("🔗 Repository: https://github.com/iamcos/pyHaasAPI")
        
        print("\n📋 Published structure:")
        print("├── pyHaasAPI/          # Core library")
        print("├── docs/               # Documentation") 
        print("├── examples/           # Usage examples")
        print("├── experiments/        # Experimental features")
        print("├── tests/              # Test suite")
        print("├── pyproject.toml      # Package configuration")
        print("├── README.md           # Main documentation")
        print("├── LICENSE             # MIT License")
        print("├── .gitignore          # Git ignore rules")
        print("├── rules.cursor        # Development rules")
        print("└── RUNNING_TESTS.cursor # Testing guidelines")
        
    else:
        print("❌ Failed to push to GitHub")
        return False
    
    # Clean up temp directory
    print("🧹 Cleaning up temporary files...")
    os.chdir("..")  # Go back to project root
    if clean_repo_path.exists():
        shutil.rmtree(clean_repo_path)
        print("✅ Temporary files cleaned up")
    
    return True

def main():
    """Main publishing workflow."""
    print("🚀 Selective pyHaasAPI Publishing")
    print("=" * 50)
    print("This will publish ONLY the core pyHaasAPI library to GitHub.")
    print("Your local monorepo will remain completely untouched.")
    print()
    
    # Verify we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Not in the root directory of the project")
        print("Please run this script from the pyHaasAPI root directory")
        return False
    
    # Confirm with user
    confirm = input("🔍 Proceed with selective publishing? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Publishing cancelled")
        return False
    
    # Create and publish clean repository
    success = create_clean_pyhaasapi_repo()
    
    if success:
        print("\n🎉 Publishing completed successfully!")
        print("📍 Your local files are completely unchanged")
        print("📍 Only essential pyHaasAPI files were published to GitHub")
    else:
        print("\n❌ Publishing failed")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Publishing cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)