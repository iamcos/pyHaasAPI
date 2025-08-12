
import requests
import json

url = "http://localhost:8000/setup_haas_accounts"
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, headers=headers, data=json.dumps({}))
    response.raise_for_status()  # Raise an exception for HTTP errors
    print(response.json())
except requests.exceptions.RequestException as e:
    print(f"Error sending request: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response content: {e.response.text}")
