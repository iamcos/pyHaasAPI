#!/usr/bin/env python3
"""
Minimal demo: Create a folder and move a script into it
"""
from pyHaasAPI import api
import random

def main():
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="garrypotterr@gmail.com",
        password="IQYTCQJIQYTCQJ"
    )

    # 1. Create a new folder
    folder_name = f"DemoFolder_{random.randint(1000, 9999)}"
    folder = api.create_script_folder(executor, folder_name)
    print(f"Created folder: {folder.name} (ID: {folder.folder_id})")

    # 2. Get all scripts and pick one at random
    scripts = api.get_all_scripts(executor)
    if not scripts:
        print("No scripts available to move!")
        return
    script = random.choice(scripts)
    print(f"Moving script: {script.script_name} (ID: {script.script_id}) to folder {folder.folder_id}")

    # 3. Move the script to the new folder
    try:
        response = executor.execute(
            endpoint="HaasScript",
            response_type=object,  # Accept any type for Data
            query_params={
                "channel": "MOVE_SCRIPT_TO_FOLDER",
                "scriptid": script.script_id,
                "folderid": folder.folder_id,
                "interfacekey": executor.state.interface_key,
                "userid": executor.state.user_id,
            }
        )
        print("Move response:", response)
        if isinstance(response, dict) and response.get("Success"):
            if response.get("Data") is True:
                print("Move successful!")
            else:
                print("Move failed (API returned Data: false). This script may not be movable.")
        elif isinstance(response, dict):
            print(f"Move failed! Error: {response.get('Error')}")
        else:
            print(f"Unexpected response: {response}")
    except Exception as e:
        print(f"Exception during move: {e}")

if __name__ == "__main__":
    main() 