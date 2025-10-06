import os, time
from dotenv import load_dotenv
from pyHaasAPI_v1 import api

load_dotenv()
HOST='127.0.0.1'
PORT=8091
MARKET='ETH_USDT_PERPETUAL'
MONTHS=36
POLL=5
TIMEOUT=900

haas_api = api.RequestsExecutor(host=HOST, port=PORT, state=api.Guest())
executor = haas_api.authenticate(os.getenv('API_EMAIL'), os.getenv('API_PASSWORD'))

# Trigger chart to register market
try:
    api.get_chart(executor, MARKET, interval=15, style=301)
except Exception:
    pass

# Wait for sync (Status == 3)
start=time.time()
while time.time()-start < TIMEOUT:
    try:
        status = api.get_history_status(executor)
        info = status.get(MARKET)
        if info and info.get('Status') == 3:
            break
    except Exception:
        pass
    time.sleep(POLL)

# Set history depth
try:
    api.set_history_depth(executor, MARKET, MONTHS)
except Exception:
    pass
print('done')
