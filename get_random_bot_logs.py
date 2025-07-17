#!/usr/bin/env python3
"""
Random Bot Log Viewer

This script connects to your HaasOnline API, gets all running bots,
randomly selects one, and displays comprehensive log/runtime information.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from pyHaasAPI import api
from config import settings

# Authenticate
executor = api.RequestsExecutor(
    host=settings.API_HOST,
    port=settings.API_PORT,
    state=api.Guest()
).authenticate(
    email=settings.API_EMAIL,
    password=settings.API_PASSWORD
)

print("\n=== ACCOUNTS ===")
accounts = api.get_accounts(executor)
for acc in accounts:
    print(acc)

print("\n=== LABS ===")
labs = api.get_all_labs(executor)
for lab in labs:
    print(lab)

print("\n=== BOTS ===")
bots = api.get_all_bots(executor)
for bot in bots:
    print(bot)
