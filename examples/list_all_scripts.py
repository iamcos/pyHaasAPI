#!/usr/bin/env python3
"""
Minimal example: List all script items and print their key fields
"""
from pyHaasAPI import api

def main():
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    scripts = api.get_all_scripts(executor)
    print(f"Found {len(scripts)} script items:")
    for script in scripts:
        print(f"ID: {script.script_id}, Name: {script.script_name}, Type: {script.script_type}, Folder: {script.folder_id}")

if __name__ == "__main__":
    main() 