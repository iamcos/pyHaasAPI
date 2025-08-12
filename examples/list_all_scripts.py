#!/usr/bin/env python3
"""
Minimal example: List all script items and print their key fields
"""
import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
# Credentials must be set in your .env file as HAAS_API_HOST, HAAS_API_PORT, HAAS_API_EMAIL, HAAS_API_PASSWORD
from pyHaasAPI import api

def main():
    executor = api.RequestsExecutor(
        host=os.getenv("HAAS_API_HOST"),
        port=int(os.getenv("HAAS_API_PORT")),
        state=api.Guest()
    ).authenticate(
        email=os.getenv("HAAS_API_EMAIL"),
        password=os.getenv("HAAS_API_PASSWORD")
    )
    scripts = api.get_all_scripts(executor)
    print(f"Found {len(scripts)} script items:")
    for script in scripts:
        print(f"ID: {script.script_id}, Name: {script.script_name}, Type: {script.script_type}, Folder: {script.folder_id}")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 