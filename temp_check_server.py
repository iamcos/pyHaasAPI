
import requests

try:
    response = requests.get("http://localhost:8000/get_all_scripts")
    response.raise_for_status()
    print("Server is online and responding.")
    print(response.json())
except requests.exceptions.RequestException as e:
    print(f"Server is offline or not responding: {e}")
