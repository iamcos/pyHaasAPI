
import os
import sys
from config import settings
from pyHaasAPI import api

SCRIPT_DUMP_DIR = "/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/haasscripts_dump"

def main():
    # Authenticate
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # Check if authentication was successful by verifying the executor's state
    if isinstance(executor.state, api.Guest):
        print("Authentication failed. Please check your .env settings.")
        sys.exit(1)

    try:
        scripts = api.get_all_scripts(executor)
        for script_item in scripts:
            # Get the full script record to access script_components
            script_record = api.get_script_record(executor, script_item.script_id)
            if script_record and script_record.script_components:
                sanitized_script_name = "".join(c if c.isalnum() or c in (' ', '.', '-') else '_' for c in script_item.script_name)
                filename = os.path.join(SCRIPT_DUMP_DIR, f"{sanitized_script_name}.hss")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(script_record.script_components)
                print(f"Saved script: {script_item.script_name} to {filename}")
            else:
                print(f"Could not retrieve content for script: {script_item.script_name}")
    except api.HaasApiError as e:
        print(f"API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

    print("\nAll HaasScripts have been processed.")

if __name__ == "__main__":
    main()
