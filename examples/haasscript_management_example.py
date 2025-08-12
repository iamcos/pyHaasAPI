#!/usr/bin/env python3
"""
HaasScript Management Example
----------------------------
Demonstrates HaasScript management:
- List scripts
- Get script details
- Add script
- Edit script
- Delete script
- Move script to folder

Run with: python -m examples.haasscript_management_example
"""
from config import settings
from pyHaasAPI import api
import time

def main():
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # 1. List all scripts
    scripts = api.get_all_scripts(executor)
    print("All scripts:")
    for script in scripts:
        print(f"  {script.script_id}: {script.script_name}")

    # 2. Add a new script
    new_script = api.add_script(executor, script_name="TestScript", script_content="// code", description="Test")
    print(f"Script created: {new_script.script_id}")
    time.sleep(2)

    # 3. Get script details
    script = api.get_script_item(executor, new_script.script_id)
    print(f"Script details: {script}")

    # 4. Edit script
    try:
        edited_script = api.edit_script(
            executor,
            script_id=new_script.script_id,
            name="TestScriptEdited",
            description="Updated",
            script="// new code",
        )
        if isinstance(edited_script, dict):
            print("WARNING: Partial or invalid response from edit_script:")
            print(edited_script)
        else:
            print(f"Script updated: {edited_script.script_id}")
    except Exception as e:
        print(f"Edit script error: {e}")
    time.sleep(2)

    # 5. Move script to folder (create folder if needed)
    folders = api.get_all_script_folders(executor)
    folder_id = folders[0].folder_id if folders else api.create_script_folder(executor, "TestFolder").folder_id
    moved = api.move_script_to_folder(executor, new_script.script_id, folder_id)
    print(f"Script moved to folder {folder_id}: {moved}")
    time.sleep(2)

    # 6. Delete the script
    api.delete_script(executor, new_script.script_id)
    print(f"Script deleted: {new_script.script_id}")

if __name__ == "__main__":
    main() 