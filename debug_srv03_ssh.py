
import asyncio
import os
import json
import subprocess

def test_ssh():
    print("Loading servers.json...")
    with open("servers.json") as f:
        data = json.load(f)
    
    config = data.get("srv03")
    if not config:
        print("srv03 not found in config")
        return

    print(f"Config for srv03: {config}")
    
    # Construct SSH command similar to ServerManager
    cmd = [
        "ssh",
        "-v", # Verbose for debugging
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "BatchMode=yes",
        "-o", f"ConnectTimeout={config.get('timeout', 10)}",
    ]
    
    key_path = config.get("ssh_key_path")
    if key_path:
        # Expand user
        key_path = os.path.expanduser(key_path)
        if os.path.exists(key_path):
             cmd.extend(["-i", key_path])
        else:
             print(f"Warning: Key path {key_path} does not exist")

    hostname = config.get("hostname")
    username = config.get("username")
    cmd.append(f"{username}@{hostname}")
    cmd.append("echo 'SSH Connection Successful'")
    
    print(f"\nRunning command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("\n--- STDOUT ---")
        print(result.stdout)
        print("\n--- STDERR ---")
        print(result.stderr)
        
        print(f"\nReturn Code: {result.returncode}")
    except Exception as e:
        print(f"Execution failed: {e}")

if __name__ == "__main__":
    test_ssh()
