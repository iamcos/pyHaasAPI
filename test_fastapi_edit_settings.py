import requests
import json
import urllib.parse
import time

# --- Configuration (Update these with your actual values) ---
BASE_URL = "http://127.0.0.1:8000/BotAPI.php"
BOT_ID = "6dcbbe90f464401e807dbae2bca5b279"
SCRIPT_ID = "d840bbc48dbb59b8660e96795dab8797"
USER_ID = "your_user_id"
INTERFACE_KEY = "your_interface_key"

# --- EDIT_SETTINGS Payload ---
# This is the 'settings' JSON object from your curl command, with some values changed for testing
edit_settings_payload_data = {
    "botId": BOT_ID,
    "botName": "BOT2_UPDATED", # Changed bot name
    "accountId": "642b0a4e-fbab-4581-b881-09c06cb7cd2d",
    "marketTag": "BINANCE_BTC_MXN_",
    "leverage": 0,
    "positionMode": 0,
    "interval": 10,
    "chartStyle": 302,
    "tradeAmount": 0.06, # Changed trade amount
    "orderTemplate": 501,
    "scriptParameters": {
        "11-11-15-20.Length of RSI/MFI": 20, # Changed from 15
        "12-12-13-18.Multiplier": 2, # Changed from 1
        "13-13-18-23.Draw RSI?": False, # Changed from true
        "14-14-18-23.Draw MFI?": True, # Changed from false
        "15-15-21-26.Highlight OS/OB?": True # Changed from false
    }
}

# Convert the settings payload to a JSON string
settings_json_string = json.dumps(edit_settings_payload_data)

# --- EDIT_SETTINGS Request ---
edit_settings_data = {
    "botid": BOT_ID,
    "scriptid": SCRIPT_ID,
    "settings": settings_json_string,
    "interfacekey": INTERFACE_KEY,
    "userid": USER_ID
}

# Manually encode the data for x-www-form-urlencoded
encoded_edit_settings_data = urllib.parse.urlencode(edit_settings_data)

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,pl;q=0.6,de;q=0.5,fr;q=0.4',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'http://127.0.0.1:8090',
    'Referer': f'http://127.0.0.1:8090/Bots/{BOT_ID}/Settings',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"' ,
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"'
}

print("\n--- Sending EDIT_SETTINGS request ---")
try:
    edit_settings_response = requests.post(f"{BASE_URL}?channel=EDIT_SETTINGS", data=encoded_edit_settings_data, headers=headers)
    edit_settings_response.raise_for_status() # Raise an exception for HTTP errors
    print("EDIT_SETTINGS Response:", edit_settings_response.json())
except requests.exceptions.RequestException as e:
    print(f"Error sending EDIT_SETTINGS request: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print("Response content:", e.response.text)
    exit()

# --- GET_RUNTIME Request (to verify changes) ---
get_runtime_data = {
    "botid": BOT_ID,
    "interfacekey": INTERFACE_KEY,
    "userid": USER_ID
}

encoded_get_runtime_data = urllib.parse.urlencode(get_runtime_data)

# Give the server a moment to process the settings change
time.sleep(1)

print("\n--- Sending GET_RUNTIME request to verify changes ---")
try:
    get_runtime_response = requests.post(f"{BASE_URL}?channel=GET_RUNTIME", data=encoded_get_runtime_data, headers=headers)
    get_runtime_response.raise_for_status() # Raise an exception for HTTP errors
    runtime_data = get_runtime_response.json()
    print("GET_RUNTIME Response:", runtime_data)

    # Verify changes
    if runtime_data.get("Success"):
        data = runtime_data.get("Data", {})
        h_data = data.get("H", {})
        input_fields = data.get("InputFields", {})

        print("\n--- Verification ---")
        # Verify bot name
        if h_data.get("BN") == edit_settings_payload_data["botName"]:
            print(f"✅ Bot Name updated successfully to: {h_data.get('BN')}")
        else:
            print(f"❌ Bot Name not updated. Expected '{edit_settings_payload_data["botName"]}', got '{h_data.get("BN")}")

        # Verify trade amount
        if h_data.get("TA") == edit_settings_payload_data["tradeAmount"]:
            print(f"✅ Trade Amount updated successfully to: {h_data.get("TA")}")
        else:
            print(f"❌ Trade Amount not updated. Expected '{edit_settings_payload_data["tradeAmount"]}', got '{h_data.get("TA")}")

        # Verify script parameters
        print("\n--- Script Parameter Verification ---")
        for key, expected_value in edit_settings_payload_data["scriptParameters"].items():
            # The API returns boolean values as lowercase strings, so convert expected_value for comparison
            if isinstance(expected_value, bool):
                expected_value_str = str(expected_value).lower()
            else:
                expected_value_str = str(expected_value)

            actual_value = input_fields.get(key, {}).get("V")
            if actual_value == expected_value_str:
                print(f"✅ Parameter '{key}' updated successfully. Value: {actual_value}")
            else:
                print(f"❌ Parameter '{key}' not updated. Expected '{expected_value_str}', got '{actual_value}'")
    else:
        print("❌ GET_RUNTIME request was not successful.")

except requests.exceptions.RequestException as e:
    print(f"Error sending GET_RUNTIME request: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print("Response content:", e.response.text)
