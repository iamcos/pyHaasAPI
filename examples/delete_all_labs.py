"""
⚠️ SECURITY WARNING ⚠️
DO NOT EXPOSE PRIVATE DATA IN SCRIPTS! USE .env FILE!!!

This script demonstrates lab deletion functionality.
NEVER hardcode credentials - always use environment variables!
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
from pyHaasAPI import api


def main():
    # ⚠️ SECURITY: Use environment variables, never hardcode credentials!
    executor = api.RequestsExecutor(host=settings.API_HOST, port=settings.API_PORT, state=api.Guest())
    executor = executor.authenticate(email=settings.API_EMAIL, password=settings.API_PASSWORD)

    all_labs = api.get_all_labs(executor)
    print(f"Deleting {len(all_labs)} labs")

    for lab in all_labs:
        api.delete_lab(executor, lab.lab_id)

    print("All labs deleted")


if __name__ == "__main__":
    # Place the main execution logic here
    pass
