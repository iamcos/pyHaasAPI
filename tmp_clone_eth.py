import os, json
from dotenv import load_dotenv
from pyHaasAPI_v1 import api

load_dotenv()

HOST='127.0.0.1'
PORT=8091
BASE_LAB_ID='af83cbf2-eb30-47bc-b6f4-324d9050c8f2'

haas_api = api.RequestsExecutor(host=HOST, port=PORT, state=api.Guest())
executor = haas_api.authenticate(os.getenv('API_EMAIL'), os.getenv('API_PASSWORD'))

# Clone lab
orig = api.get_lab_details(executor, BASE_LAB_ID)
orig_name = getattr(orig, 'name', getattr(orig, 'lab_name', 'Lab'))
new_name = f"{orig_name} ETH Clone"
cloned = api.clone_lab(executor, BASE_LAB_ID, new_name=new_name)

# Configure cloned lab for ETH and standard settings
lab = api.get_lab_details(executor, cloned.lab_id)
settings = getattr(lab, 'settings', None)
if settings is not None:
    try:
        settings.trade_amount = 2000.0
        settings.leverage = 20.0
        settings.position_mode = 1  # HEDGE
        settings.margin_mode = 0    # CROSS
        if hasattr(settings, 'market_tag'):
            settings.market_tag = 'ETH_USDT_PERPETUAL'
        elif hasattr(lab, 'market'):
            lab.market = 'ETH_USDT_PERPETUAL'
    except Exception as e:
        print(f"Failed to set settings: {e}")

# Persist settings
api.update_lab_details(executor, lab)

# Verify
verified = api.get_lab_details(executor, cloned.lab_id)
vs = getattr(verified, 'settings', object())
result = {
    'new_lab_id': cloned.lab_id,
    'name': getattr(verified, 'name', getattr(verified, 'lab_name', '')),
    'trade_amount': getattr(vs, 'trade_amount', None),
    'leverage': getattr(vs, 'leverage', None),
    'position_mode': getattr(vs, 'position_mode', None),
    'margin_mode': getattr(vs, 'margin_mode', None),
    'market_tag': getattr(vs, 'market_tag', getattr(verified, 'market', None)),
}

print(json.dumps(result))
with open('tmp_new_lab_id.txt','w') as f:
    f.write(cloned.lab_id)
