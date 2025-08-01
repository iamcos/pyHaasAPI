import os
from dotenv import load_dotenv
from pyHaasAPI import api
from config import settings

load_dotenv()

def main():
    print("🔍 Checking API server connectivity and authentication...")
    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        )
        print(f"✅ Server reachable at {settings.API_HOST}:{settings.API_PORT}")
    except Exception as e:
        print(f"❌ Could not connect to server: {e}")
        return
    try:
        auth_executor = executor.authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

if __name__ == "__main__":
    main() 