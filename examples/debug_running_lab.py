import requests
from utils.auth.authenticator import authenticator

# Authenticate
success = authenticator.authenticate()
if not success:
    print("❌ Authentication failed")
    exit(1)
executor = authenticator.get_executor()

# Get dynamic values for the single lab
lab_id = 'a98740a6-0f37-4e16-b833-7df22279ce59'
start_unix = 1752498600
end_unix = 1753103400
interface_key = getattr(executor.state, 'interface_key', None)
user_id = getattr(executor.state, 'user_id', None)

url = "http://127.0.0.1:8090/LabsAPI.php?channel=START_LAB_EXECUTION"
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,pl;q=0.6,de;q=0.5,fr;q=0.4',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'http://127.0.0.1:8090',
    'Referer': f'http://127.0.0.1:8090/Labs/{lab_id}',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}
data = f"labid={lab_id}&startunix={start_unix}&endunix={end_unix}&sendemail=false&interfacekey={interface_key}&userid={user_id}"

print("\nSending minimal curl-matching POST with dynamic keys...")
resp = requests.post(url, headers=headers, data=data)
print(f"Status code: {resp.status_code}")
print(f"Response: {resp.text}") 