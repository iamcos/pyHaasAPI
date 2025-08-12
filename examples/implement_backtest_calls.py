from config import settings
from pyHaasAPI import api

def main():
    # Authenticate
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    
    # Your test code here
    scripts = api.get_all_scripts(executor)
    print(f"Found {len(scripts)} scripts")

if __name__ == "__main__":
    main()