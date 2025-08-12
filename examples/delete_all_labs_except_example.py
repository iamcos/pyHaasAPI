"""
⚠️ SECURITY WARNING ⚠️
DO NOT EXPOSE PRIVATE DATA IN SCRIPTS! USE .env FILE!!!

This script demonstrates lab deletion functionality, skipping the "Example" lab.
NEVER hardcode credentials - always use environment variables!
"""

import os
from config import settings
from dotenv import load_dotenv
from pyHaasAPI import api

def main():
    # ⚠️ SECURITY: Use environment variables, never hardcode credentials!
    load_dotenv()
    executor = api.RequestsExecutor(host=settings.API_HOST, port=settings.API_PORT, state=api.Guest())
    executor = executor.authenticate(email=settings.API_EMAIL, password=settings.API_PASSWORD)

    while True:
        all_labs = api.get_all_labs(executor)
        labs_to_delete = [lab for lab in all_labs if lab.name != "Example"]

        if not labs_to_delete:
            print("No more labs to delete.")
            break

        print(f"Found {len(labs_to_delete)} labs to delete.")

        for lab in labs_to_delete:
            print(f"Deleting lab: {lab.name} ({lab.lab_id})")
            try:
                api.delete_lab(executor, lab.lab_id)
            except Exception as e:
                print(f"Could not delete lab {lab.name}: {e}")

    print("Finished deleting labs.")


if __name__ == "__main__":
    main()
