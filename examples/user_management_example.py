#!/usr/bin/env python3
"""
User Management Example
----------------------
Demonstrates user endpoints:
- App login
- Check token
- Logout
- Is device approved

Run with: python -m examples.user_management_example
"""
from config import settings
from pyHaasAPI import api

# NOTE: These endpoints may require specific server configuration or app credentials.

def main():
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # 2. App login (replace with real app_id/app_secret if needed)
    try:
        app_login_resp = api.app_login(executor, app_id="your_app_id", app_secret="your_app_secret")
        if isinstance(app_login_resp, dict):
            print(f"App login response: {app_login_resp}")
        else:
            print(f"App login result: {app_login_resp}")
    except Exception as e:
        print(f"App login error: {e}")

    # 3. Check token (replace with real token if needed)
    try:
        check_token_resp = api.check_token(executor, token="your_token")
        if isinstance(check_token_resp, dict):
            print(f"Check token response: {check_token_resp}")
        else:
            print(f"Check token result: {check_token_resp}")
    except Exception as e:
        print(f"Check token error: {e}")

    # 4. Is device approved (replace with real device_id if needed)
    try:
        device_approved_resp = api.is_device_approved(executor, device_id="your_device_id")
        if isinstance(device_approved_resp, dict):
            print(f"Is device approved response: {device_approved_resp}")
        else:
            print(f"Is device approved result: {device_approved_resp}")
    except Exception as e:
        print(f"Is device approved error: {e}")

    # 5. Logout
    try:
        logout_resp = api.logout(executor)
        if isinstance(logout_resp, dict):
            print(f"Logout response: {logout_resp}")
        else:
            print(f"Logout result: {logout_resp}")
    except Exception as e:
        print(f"Logout error: {e}")

if __name__ == "__main__":
    main() 