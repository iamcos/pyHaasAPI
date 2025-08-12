"""
⚠️ SECURITY WARNING ⚠️
DO NOT EXPOSE PRIVATE DATA IN SCRIPTS! USE .env FILE!!!

This script demonstrates synchronous executor functionality.
NEVER hardcode credentials - always use environment variables!
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
import random

from pyHaasAPI import api, lab
from pyHaasAPI.domain import BacktestPeriod
from pyHaasAPI.model import CreateLabRequest


def main():
    # ⚠️ SECURITY: Use environment variables, never hardcode credentials!
    executor = api.RequestsExecutor(host=settings.API_HOST, port=settings.API_PORT, state=api.Guest())

    markets = api.get_all_markets(executor)
    market = random.choice(markets)
    print(f"Got {len(markets)} and choosed {market}")

    # Authenticate to get access for the all endpoints
    executor = executor.authenticate(email=settings.API_EMAIL, password=settings.API_PASSWORD)

    accounts = api.get_accounts(executor)
    account = random.choice(accounts)
    print(f"Got {len(accounts)} and choosed {account}")

    # Get available scripts
    scripts = api.get_all_scripts(executor)
    script = random.choice(scripts)
    print(f"Got {len(scripts)} and choosed {script}")

    # Create lab
    lab_details = api.create_lab(
        executor,
        CreateLabRequest(
            script_id=script.script_id,
            name="My first lab",
            account_id=account.account_id,
            market=market.market,
            interval=0,
            default_price_data_style="CandleStick",
        ),
    )
    print(f"{lab_details=}")

    # Start lab backtesting & wait for result
    backtesting_result = lab.backtest(
        executor,
        lab_details.lab_id,
        BacktestPeriod(period_type=BacktestPeriod.Type.DAY, count=20),
    )
    print(f"{backtesting_result=}")


if __name__ == "__main__":
    # Place the main execution logic here
    pass
