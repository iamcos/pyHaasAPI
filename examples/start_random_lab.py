import random
from utils.auth.authenticator import authenticator
from pyHaasAPI import api
from pyHaasAPI.model import StartLabExecutionRequest
from datetime import datetime

# Authenticate
success = authenticator.authenticate()
if not success:
    print("❌ Authentication failed")
    exit(1)
executor = authenticator.get_executor()

# Get all labs
labs = api.get_all_labs(executor)

# Find labs that are not running or queued
not_running_labs = []
for lab in labs:
    try:
        status = api.get_lab_execution_update(executor, lab.lab_id)
        enum_status = getattr(status, 'status', None)
        # Not running or queued
        if not (hasattr(enum_status, 'name') and enum_status.name in ("RUNNING", "QUEUED")) and enum_status not in (1, 2):
            not_running_labs.append(lab)
    except Exception:
        # If status can't be fetched, consider it not running
        not_running_labs.append(lab)

if not not_running_labs:
    print("No labs available that are not running or queued.")
    exit(0)

# Pick a random lab
lab = random.choice(not_running_labs)
print(f"Selected lab: {lab.name} (ID: {lab.lab_id})")

# Fetch full lab details to get settings
lab_details = api.get_lab_details(executor, lab.lab_id)
market_tag = getattr(lab_details.settings, 'market_tag', None)
if not market_tag:
    print("Lab has no market_tag, cannot sync market.")
    exit(1)
print(f"Ensuring market {market_tag} is synced...")
api.get_chart(executor, market_tag, interval=15, style=301)

# Start backtest for the lab (last 30 days)
end_unix = int(datetime.now().timestamp())
start_unix = end_unix - 30*24*60*60
print(f"Starting backtest for lab {lab.lab_id}...")
req = StartLabExecutionRequest(
    lab_id=lab.lab_id,
    start_unix=start_unix,
    end_unix=end_unix,
    send_email=False
)
result = api.start_lab_execution(executor, req)
print("Backtest start result:")
print(result) 