#!/usr/bin/env python3
"""
Print Scalper Bot Parameter Keys

Finds a lab using the scalper bot, fetches its parameters, and prints the full keys for
"Stop Loss (%)" and "Take Profit (%)" (including any prefixes).
"""
import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
# Credentials must be set in your .env file as HAAS_API_HOST, HAAS_API_PORT, HAAS_API_EMAIL, HAAS_API_PASSWORD
from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest

def main():
    executor = api.RequestsExecutor(
        host=os.getenv("HAAS_API_HOST"),
        port=int(os.getenv("HAAS_API_PORT")),
        state=api.Guest()
    ).authenticate(
        email=os.getenv("HAAS_API_EMAIL"),
        password=os.getenv("HAAS_API_PASSWORD")
    )
    
    # Find a scalper bot script
    scripts = api.get_scripts_by_name(executor, "Scalper Bot")
    if not scripts:
        print("❌ No scalper bot scripts found!")
        return
    scalper_script = scripts[0]
    print(f"✅ Found scalper bot script: {scalper_script.script_name} (ID: {scalper_script.script_id})")
    
    # Find a lab using this script
    labs = api.get_all_labs(executor)
    scalper_labs = [lab for lab in labs if lab.script_id == scalper_script.script_id]
    if not scalper_labs:
        print("❌ No labs found using the scalper bot script!")
        return
    lab = scalper_labs[0]
    print(f"✅ Found lab: {lab.name} (ID: {lab.lab_id})")
    
    # Fetch lab details and parameters
    lab_details = api.get_lab_details(executor, lab.lab_id)
    print(f"✅ Lab details fetched. Parameters:")
    for param in lab_details.parameters:
        # param is a dict with 'K' (key) and possibly 'N' (name)
        key = param.get('K', '')
        name = key.split('.')[-1] if '.' in key else key
        if "stop loss" in name.lower() or "take profit" in name.lower():
            print(f"  - Key: {key} | Name: {name} | Options: {param.get('O', [])}")
    print("---\nAll parameter keys:")
    for param in lab_details.parameters:
        print(f"  - {param.get('K', '')}")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 