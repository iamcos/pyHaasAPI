#!/usr/bin/env python3
"""
Simple publishing launcher
Runs the selective pyHaasAPI publishing script from the publishing folder.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the publishing script."""
    script_path = Path("publishing/publish_pyhaasapi_only.py")
    
    if not script_path.exists():
        print("❌ Publishing script not found!")
        print("Expected: publishing/publish_pyhaasapi_only.py")
        return False
    
    print("🚀 Launching pyHaasAPI selective publishing...")
    print("=" * 50)
    
    # Run the publishing script
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running publishing script: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)