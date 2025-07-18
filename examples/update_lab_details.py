import os
from dotenv import load_dotenv
load_dotenv()
import random

from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest


def main():
    API_HOST = os.environ.get("API_HOST", "127.0.0.1")
    API_PORT = int(os.environ.get("API_PORT", 8090))
    API_EMAIL = os.environ.get("API_EMAIL")
    API_PASSWORD = os.environ.get("API_PASSWORD")

    if not all([API_HOST, API_PORT, API_EMAIL, API_PASSWORD]):
        print("Missing one or more required environment variables: API_HOST, API_PORT, API_EMAIL, API_PASSWORD")
        print("Please create a .env file with these values.")
        return

    executor = api.RequestsExecutor(host=API_HOST, port=API_PORT, state=api.Guest())

    markets = api.get_all_markets(executor)
    market = random.choice(markets)
    print(f"Got {len(markets)} and choosed {market}")

    # Authenticate to get access for the all endpoints
    executor = executor.authenticate(
        email=API_EMAIL, password=API_PASSWORD
    )

    accounts = api.get_accounts(executor)
    account = random.choice(accounts)
    print(f"Got {len(accounts)} and choosed {account}")

    # Get available scripts
    scripts = api.get_all_scripts(executor)
    script = next(
        script
        for script in scripts
        if script.script_name == "Haasonline Original - Scalper Bot"
    )
    print(f"Got {len(scripts)} and choosed {script}")

    # Create lab
    lab_details = api.create_lab(
        executor,
        CreateLabRequest(
            script_id=script.script_id,
            name="My first lab",
            account_id=account.account_id,
            market=f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_",
            interval=0,
            default_price_data_style="CandleStick",
        ),
    )
    print(f"{lab_details=}")
    lab_details.parameters[0]['O'] = [1, 2, 3, 4, 5]
    api.update_lab_details(executor, lab_details)


if __name__ == "__main__":
    main()
