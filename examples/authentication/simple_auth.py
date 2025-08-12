
import os
import sys
import random
from dotenv import load_dotenv
from pyHaasAPI.api import RequestsExecutor, HaasApiError, Guest

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Get API credentials from environment variables
ip = os.getenv("HAAS_IP")
port = os.getenv("HAAS_PORT")
email = os.getenv("HAAS_EMAIL")
password = os.getenv("HAAS_PASSWORD")

if not all([ip, port, email, password]):
    print("Error: Missing one or more required environment variables (HAAS_IP, HAAS_PORT, HAAS_EMAIL, HAAS_PASSWORD)")
    sys.exit(1)

try:
    executor = RequestsExecutor(host=ip, port=port, state=Guest())
    interface_key = "".join(f"{random.randint(0, 100)}" for _ in range(10))
    resp = executor._execute_inner(
        "User",
        response_type=dict,
        query_params={
            "channel": "LOGIN_WITH_ONE_TIME_CODE",
            "email": email,
            "pincode": 123456,
            "interfaceKey": interface_key,
        },
    )
    if not resp.success:
        raise HaasApiError(resp.error or "Failed to login")
    print("Authentication successful!")
except HaasApiError as e:
    print(f"Authentication failed: {e}")
