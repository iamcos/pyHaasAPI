import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from pyHaasAPI import api
from pyHaasAPI.model import UserAccount, AccountData, CloudMarket, LabDetails, HaasScriptSettings, HaasBot
from pyHaasAPI.parameters import LabConfig
from sentence_transformers import SentenceTransformer
import time
import random

# Fixture to create a TestClient for testing FastAPI endpoints
@pytest.fixture(scope="module")
def client():
    import os
    os.environ["API_EMAIL"] = ""
    os.environ["API_PASSWORD"] = ""
    from tools.mcp_server.main import app # Import app locally within the fixture
    with TestClient(app=app) as client:
        yield client

@pytest.fixture(scope="module")
def setup_test_environment(client):
    # Dynamically get an account ID
    accounts_response = client.get("/get_accounts")
    assert accounts_response.status_code == 200
    accounts = accounts_response.json()["Data"]
    assert len(accounts) > 0, "No accounts found on the HaasOnline server. Please ensure at least one account exists."
    base_account_id = accounts[0]["AID"] # Use the first available account

    # Dynamically create a script for testing
    script_name = f"TestScript_{int(time.time())}"
    script_content = """// HaasScript
// Version 1.0.0
// Description: A simple test script

function main() {
    // Your script logic here
}
"""
    add_script_payload = {
        "script_name": script_name,
        "script_content": script_content
    }
    create_script_response = client.post("/add_script", json=add_script_payload)
    assert create_script_response.status_code == 200
    assert create_script_response.json()["Success"] == True
    base_script_id = create_script_response.json()["Data"]["script_id"]

    created_script_ids = [base_script_id]
    created_lab_ids = []
    created_bot_ids = []

    yield {
        "client": client,
        "account_id": base_account_id,
        "script_id": base_script_id,
        "created_lab_ids": created_lab_ids,
        "created_bot_ids": created_bot_ids,
        "created_script_ids": created_script_ids
    }

    # Teardown: Clean up created labs, bots, and scripts
    print("\nCleaning up test environment...")
    for bot_id in created_bot_ids:
        try:
            print(f"Deleting bot: {bot_id}")
            client.delete(f"/delete_trade_bot/{bot_id}")
        except Exception as e:
            print(f"Error deleting bot {bot_id}: {e}")
    for lab_id in created_lab_ids:
        try:
            print(f"Deleting lab: {lab_id}")
            client.delete(f"/delete_lab/{lab_id}")
        except Exception as e:
            print(f"Error deleting lab {lab_id}: {e}")
    for script_id in created_script_ids:
        try:
            print(f"Deleting script: {script_id}")
            client.delete(f"/delete_script/{script_id}")
        except Exception as e:
            print(f"Error deleting script {script_id}: {e}")
    print("Test environment cleanup complete.")


# Test /status endpoint
def test_get_status(setup_test_environment):
    client = setup_test_environment["client"]
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "authenticated", "haas_api_connected": True}

# Test /get_accounts endpoint
def test_get_accounts(setup_test_environment):
    client = setup_test_environment["client"]
    response = client.get("/get_accounts")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert isinstance(response.json()["Data"], list)
    assert len(response.json()["Data"]) > 0
    assert "AID" in response.json()["Data"][0]

# Test /get_account_data/{account_id} endpoint
def test_get_account_data(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    response = client.get(f"/get_account_data/{account_id}")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "account_id" in response.json()["Data"]

# Test /get_all_markets endpoint
def test_get_all_markets(setup_test_environment):
    client = setup_test_environment["client"]
    response = client.get("/get_all_markets")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert isinstance(response.json()["Data"], list)
    assert len(response.json()["Data"]) > 0
    assert "P" in response.json()["Data"][0]

# Test /get_market_price endpoint
def test_get_market_price(setup_test_environment):
    client = setup_test_environment["client"]
    # This test requires a valid market from your live server
    market_string = "BINANCE_BTC_USDT_" 
    response = client.post("/get_market_price", json={
        "market": market_string
    })
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "Data" in response.json()
    assert "C" in response.json()["Data"]

# Test /get_orderbook endpoint
def test_get_orderbook(setup_test_environment):
    client = setup_test_environment["client"]
    # This test requires a valid market from your live server
    market_string = "BINANCE_BTC_USDT_"
    response = client.post("/get_orderbook", json={
        "market": market_string,
        "depth": 5
    })
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "Data" in response.json()
    assert "Ask" in response.json()["Data"]
    assert "Bid" in response.json()["Data"]

# Test /get_account_balance endpoint
def test_get_account_balance(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    response = client.post("/get_account_balance", json={
        "account_id": account_id
    })
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "Data" in response.json()
    assert "AID" in response.json()["Data"]

# Test /get_all_account_balances endpoint
def test_get_all_account_balances(setup_test_environment):
    client = setup_test_environment["client"]
    response = client.get("/get_all_account_balances")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert isinstance(response.json()["Data"], list)
    assert len(response.json()["Data"]) > 0
    assert "AID" in response.json()["Data"][0]

# Test /create_lab endpoint
def test_create_lab(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]

    lab_name = f"TestLab_{int(time.time())}"

    payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    response = client.post("/create_lab", json=payload)
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert "lab_id" in response.json()["Data"]
    created_lab_ids.append(response.json()["Data"]["lab_id"]) # Store lab_id for cleanup

# Test /get_embedding endpoint
def test_get_embedding(setup_test_environment):
    client = setup_test_environment["client"]
    payload = {"text": "test sentence"}
    response = client.post("/get_embedding", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 384
    assert all(isinstance(x, float) for x in response.json())

    payload_empty = {"text": ""}
    response_empty = client.post("/get_embedding", json=payload_empty)
    assert response_empty.status_code == 200
    assert isinstance(response_empty.json(), list)
    assert len(response_empty.json()) == 384
    assert all(x == 0.0 for x in response_empty.json())

# Test /backtest_lab endpoint
def test_backtest_lab(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]

    # First, create a lab to backtest
    lab_name = f"BacktestLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    payload = {
        "lab_id": lab_id,
        "start_unix": 1672531200,  # Example: Jan 1, 2023, 00:00:00 UTC
        "end_unix": 1675209600,    # Example: Feb 1, 2023, 00:00:00 UTC
        "send_email": False
    }
    response = client.post("/backtest_lab", json=payload)
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert "result" in response.json()["Data"]

    # Optional: Wait for backtest to complete (polling)
    # This part is for a more robust test, but can be skipped for basic functionality check
    # print(f"Waiting for backtest {lab_id} to complete...")
    # for _ in range(60): # Poll for up to 60 seconds
    #     status_response = client.get(f"/get_lab_config/{lab_id}")
    #     if status_response.status_code == 200 and status_response.json().get("S") == 3: # LabStatus.COMPLETED
    #         print(f"Backtest {lab_id} completed.")
    #         break
    #     time.sleep(1)
    # else:
    #     print(f"Backtest {lab_id} did not complete in time.")


# Test /get_backtest_results endpoint
def test_get_backtest_results(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]

    # Create a lab and run a backtest to get a backtest_id
    lab_name = f"ResultsLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    backtest_payload = {
        "lab_id": lab_id,
        "start_unix": 1672531200,
        "end_unix": 1675209600,
        "send_email": False
    }
    backtest_response = client.post("/backtest_lab", json=backtest_payload)
    assert backtest_response.status_code == 200

    # Poll for backtest completion and get backtest_id
    backtest_id = None
    for _ in range(120): # Poll for up to 120 seconds
        status_response = client.get(f"/get_lab_config/{lab_id}")
        if status_response.status_code == 200:
            lab_details = status_response.json()
            if lab_details.get("CB", 0) > 0: # Check if completed backtests count is greater than 0
                # In a real scenario, you might need more sophisticated logic to find the specific backtest_id
                # For now, we'll assume the first backtest result is the one we just ran
                get_backtest_results_payload = {
                    "lab_id": lab_id,
                    "next_page_id": -1,
                    "page_length": 1
                }
                backtest_results_response = client.post("/get_backtest_results", json=get_backtest_results_payload)
                if backtest_results_response.status_code == 200 and backtest_results_response.json()["Data"]["I"]:
                    backtest_id = backtest_results_response.json()["Data"]["I"][0]["BID"]
                    print(f"Backtest {lab_id} completed. Backtest ID: {backtest_id}")
                    break
        time.sleep(1)
    assert backtest_id is not None, f"Backtest {lab_id} did not complete in time or backtest_id not found."

    payload = {
        "lab_id": lab_id,
        "next_page_id": -1,
        "page_length": 10
    }
    response = client.post("/get_backtest_results", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()["Success"] == True
    assert "Data" in response.json()
    assert "I" in response.json()["Data"]
    assert isinstance(response.json()["Data"]["I"], list)

# Test /delete_lab/{lab_id} endpoint
def test_delete_lab(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]

    # Create a lab to delete
    lab_name = f"LabToDelete_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id) # Add to list for cleanup in case of test failure

    response = client.delete(f"/delete_lab/{lab_id}")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert f"Lab {lab_id} deleted successfully" in response.json()["message"]
    created_lab_ids.remove(lab_id) # Remove from list if successfully deleted

# Test /create_trade_bot_from_lab endpoint
def test_create_trade_bot_from_lab(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]
    created_bot_ids = setup_test_environment["created_bot_ids"]

    # Create a lab and run a backtest to get a backtest_id
    lab_name = f"BotLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    backtest_payload = {
        "lab_id": lab_id,
        "start_unix": 1672531200,
        "end_unix": 1675209600,
        "send_email": False
    }
    backtest_response = client.post("/backtest_lab", json=backtest_payload)
    assert backtest_response.status_code == 200

    # Poll for backtest completion and get backtest_id
    backtest_id = None
    for _ in range(120): # Poll for up to 120 seconds
        status_response = client.get(f"/get_lab_config/{lab_id}")
        if status_response.status_code == 200:
            lab_details = status_response.json()
            if lab_details.get("CB", 0) > 0: # Check if completed backtests count is greater than 0
                get_backtest_results_payload = {
                    "lab_id": lab_id,
                    "next_page_id": -1,
                    "page_length": 1
                }
                backtest_results_response = client.post("/get_backtest_results", json=get_backtest_results_payload)
                if backtest_results_response.status_code == 200 and backtest_results_response.json()["Data"]["I"]:
                    backtest_id = backtest_results_response.json()["Data"]["I"][0]["BID"]
                    print(f"Backtest {lab_id} completed. Backtest ID: {backtest_id}")
                    break
        time.sleep(1)
    assert backtest_id is not None, f"Backtest {lab_id} did not complete in time or backtest_id not found."

    bot_name = f"TestBot_{int(time.time())}"

    payload = {
        "lab_id": lab_id,
        "backtest_id": backtest_id,
        "bot_name": bot_name,
        "account_id": account_id,
        "market": "BINANCE_BTC_USDT_",
        "leverage": 0
    }
    response = client.post("/create_trade_bot_from_lab", json=payload)
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert "bot_id" in response.json()["Data"]
    created_bot_ids.append(response.json()["Data"]["bot_id"])

# Test /clone_lab endpoint
def test_clone_lab(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]

    # Create a lab to clone
    original_lab_name = f"OriginalLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    original_lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(original_lab_id)

    cloned_lab_name = f"ClonedLab_{int(time.time())}"
    payload = {
        "lab_id": original_lab_id,
        "new_name": cloned_lab_name
    }
    response = client.post("/clone_lab", json=payload)
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert "lab_id" in response.json()["Data"]
    created_lab_ids.append(response.json()["Data"]["lab_id"])

# Test /activate_bot/{bot_id} endpoint
def test_activate_bot(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]
    created_bot_ids = setup_test_environment["created_bot_ids"]

    # Create a lab and bot to activate
    lab_name = f"ActivateBotLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    backtest_payload = {
        "lab_id": lab_id,
        "start_unix": 1672531200,
        "end_unix": 1675209600,
        "send_email": False
    }
    backtest_response = client.post("/backtest_lab", json=backtest_payload)
    assert backtest_response.status_code == 200

    # Poll for backtest completion and get backtest_id
    backtest_id = None
    for _ in range(120): # Poll for up to 120 seconds
        status_response = client.get(f"/get_lab_config/{lab_id}")
        if status_response.status_code == 200:
            lab_details = status_response.json()
            if lab_details.get("CB", 0) > 0: # Check if completed backtests count is greater than 0
                get_backtest_results_payload = {
                    "lab_id": lab_id,
                    "next_page_id": -1,
                    "page_length": 1
                }
                backtest_results_response = client.post("/get_backtest_results", json=get_backtest_results_payload)
                if backtest_results_response.status_code == 200 and backtest_results_response.json()["Data"]["I"]:
                    backtest_id = backtest_results_response.json()["Data"]["I"][0]["BID"]
                    print(f"Backtest {lab_id} completed. Backtest ID: {backtest_id}")
                    break
        time.sleep(1)
    assert backtest_id is not None, f"Backtest {lab_id} did not complete in time or backtest_id not found."

    bot_name = f"ActivateBot_{int(time.time())}"
    create_bot_payload = {
        "lab_id": lab_id,
        "backtest_id": backtest_id,
        "bot_name": bot_name,
        "account_id": account_id,
        "market": "BINANCE_BTC_USDT_",
        "leverage": 0
    }
    create_bot_response = client.post("/create_trade_bot_from_lab", json=create_bot_payload)
    assert create_bot_response.status_code == 200
    bot_id = create_bot_response.json()["bot_id"]
    created_bot_ids.append(bot_id)

    response = client.post(f"/activate_bot/{bot_id}")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert response.json()["Data"]["is_activated"] == True

# Test /deactivate_bot/{bot_id} endpoint
def test_deactivate_bot(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]
    created_bot_ids = setup_test_environment["created_bot_ids"]

    # Create a lab and bot to deactivate
    lab_name = f"DeactivateBotLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    backtest_payload = {
        "lab_id": lab_id,
        "start_unix": 1672531200,
        "end_unix": 1675209600,
        "send_email": False
    }
    backtest_response = client.post("/backtest_lab", json=backtest_payload)
    assert backtest_response.status_code == 200

    # Poll for backtest completion and get backtest_id
    backtest_id = None
    for _ in range(120): # Poll for up to 120 seconds
        status_response = client.get(f"/get_lab_config/{lab_id}")
        if status_response.status_code == 200:
            lab_details = status_response.json()
            if lab_details.get("CB", 0) > 0: # Check if completed backtests count is greater than 0
                get_backtest_results_payload = {
                    "lab_id": lab_id,
                    "next_page_id": -1,
                    "page_length": 1
                }
                backtest_results_response = client.post("/get_backtest_results", json=get_backtest_results_payload)
                if backtest_results_response.status_code == 200 and backtest_results_response.json()["Data"]["I"]:
                    backtest_id = backtest_results_response.json()["Data"]["I"][0]["BID"]
                    print(f"Backtest {lab_id} completed. Backtest ID: {backtest_id}")
                    break
        time.sleep(1)
    assert backtest_id is not None, f"Backtest {lab_id} did not complete in time or backtest_id not found."

    bot_name = f"DeactivateBot_{int(time.time())}"
    create_bot_payload = {
        "lab_id": lab_id,
        "backtest_id": backtest_id,
        "bot_name": bot_name,
        "account_id": account_id,
        "market": "BINANCE_BTC_USDT_",
        "leverage": 0
    }
    create_bot_response = client.post("/create_trade_bot_from_lab", json=create_bot_payload)
    assert create_bot_response.status_code == 200
    bot_id = create_bot_response.json()["bot_id"]
    created_bot_ids.append(bot_id)

    # Activate the bot first to ensure it can be deactivated
    activate_response = client.post(f"/activate_bot/{bot_id}")
    assert activate_response.status_code == 200

    response = client.post(f"/deactivate_bot/{bot_id}")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert response.json()["Data"]["is_activated"] == False

# Test /get_all_trade_bots endpoint
def test_get_all_trade_bots(setup_test_environment):
    client = setup_test_environment["client"]
    response = client.get("/get_all_trade_bots")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert isinstance(response.json()["Data"], list)
    assert len(response.json()["Data"]) > 0
    assert "ID" in response.json()["Data"][0]

# Test /delete_trade_bot/{bot_id} endpoint
def test_delete_trade_bot(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]
    created_bot_ids = setup_test_environment["created_bot_ids"]

    # Create a lab and bot to delete
    lab_name = f"DeleteBotLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    backtest_payload = {
        "lab_id": lab_id,
        "start_unix": 1672531200,
        "end_unix": 1675209600,
        "send_email": False
    }
    backtest_response = client.post("/backtest_lab", json=backtest_payload)
    assert backtest_response.status_code == 200

    # Poll for backtest completion and get backtest_id
    backtest_id = None
    for _ in range(120): # Poll for up to 120 seconds
        status_response = client.get(f"/get_lab_config/{lab_id}")
        if status_response.status_code == 200:
            lab_details = status_response.json()
            if lab_details.get("CB", 0) > 0: # Check if completed backtests count is greater than 0
                get_backtest_results_payload = {
                    "lab_id": lab_id,
                    "next_page_id": -1,
                    "page_length": 1
                }
                backtest_results_response = client.post("/get_backtest_results", json=get_backtest_results_payload)
                if backtest_results_response.status_code == 200 and backtest_results_response.json()["Data"]["I"]:
                    backtest_id = backtest_results_response.json()["Data"]["I"][0]["BID"]
                    print(f"Backtest {lab_id} completed. Backtest ID: {backtest_id}")
                    break
        time.sleep(1)
    assert backtest_id is not None, f"Backtest {lab_id} did not complete in time or backtest_id not found."

    bot_name = f"DeleteBot_{int(time.time())}"
    create_bot_payload = {
        "lab_id": lab_id,
        "backtest_id": backtest_id,
        "bot_name": bot_name,
        "account_id": account_id,
        "market": "BINANCE_BTC_USDT_",
        "leverage": 0
    }
    create_bot_response = client.post("/create_trade_bot_from_lab", json=create_bot_payload)
    assert create_bot_response.status_code == 200
    bot_id = create_bot_response.json()["bot_id"]
    created_bot_ids.append(bot_id) # Add to list for cleanup in case of test failure

    response = client.delete(f"/delete_trade_bot/{bot_id}")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert f"Bot {bot_id} deleted successfully" in response.json()["message"]
    created_bot_ids.remove(bot_id) # Remove from list if successfully deleted

# Test /get_lab_config/{lab_id} endpoint
def test_get_lab_config(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]

    # Create a lab to get its config
    lab_name = f"ConfigLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    response = client.get(f"/get_lab_config/{lab_id}")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "Data" in response.json()
    assert "LID" in response.json()["Data"]
    assert response.json()["Data"]["LID"] == lab_id

# Test /update_lab_config endpoint
def test_update_lab_config(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]

    # Create a lab to update
    lab_name = f"UpdateLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    # Get the current lab details
    current_lab_details_response = client.get(f"/get_lab_config/{lab_id}")
    assert current_lab_details_response.status_code == 200
    current_lab_details = current_lab_details_response.json()

    # Modify a setting (example: change the name)
    updated_lab_name = f"UpdatedLab_{int(time.time())}"
    current_lab_details["N"] = updated_lab_name

    payload = {"lab_details": current_lab_details}
    response = client.post("/update_lab_config", json=payload)
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "Data" in response.json()
    assert response.json()["Data"]["N"] == updated_lab_name

# Test /edit_bot_parameter endpoint
def test_edit_bot_parameter(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]
    created_bot_ids = setup_test_environment["created_bot_ids"]

    # Create a lab and bot to edit
    lab_name = f"EditBotParamLab_{int(time.time())}"
    create_lab_payload = {
        "script_id": script_id,
        "account_id": account_id,
        "market_category": "SPOT",
        "market_price_source": "BINANCE",
        "market_primary": "BTC",
        "market_secondary": "USDT",
        "exchange_code": "BINANCE",
        "interval": 1,
        "default_price_data_style": "CandleStick"
    }
    create_lab_response = client.post("/create_lab", json=create_lab_payload)
    assert create_lab_response.status_code == 200
    lab_id = create_lab_response.json()["lab_id"]
    created_lab_ids.append(lab_id)

    backtest_payload = {
        "lab_id": lab_id,
        "start_unix": 1672531200,
        "end_unix": 1675209600,
        "send_email": False
    }
    backtest_response = client.post("/backtest_lab", json=backtest_payload)
    assert backtest_response.status_code == 200

    # Poll for backtest completion and get backtest_id
    backtest_id = None
    for _ in range(120): # Poll for up to 120 seconds
        status_response = client.get(f"/get_lab_config/{lab_id}")
        if status_response.status_code == 200:
            lab_details = status_response.json()
            if lab_details.get("CB", 0) > 0: # Check if completed backtests count is greater than 0
                get_backtest_results_payload = {
                    "lab_id": lab_id,
                    "next_page_id": -1,
                    "page_length": 1
                }
                backtest_results_response = client.post("/get_backtest_results", json=get_backtest_results_payload)
                if backtest_results_response.status_code == 200 and backtest_results_response.json()["Data"]["I"]:
                    backtest_id = backtest_results_response.json()["Data"]["I"][0]["BID"]
                    print(f"Backtest {lab_id} completed. Backtest ID: {backtest_id}")
                    break
        time.sleep(1)
    assert backtest_id is not None, f"Backtest {lab_id} did not complete in time or backtest_id not found."

    bot_name = f"EditBotParam_{int(time.time())}"
    create_bot_payload = {
        "lab_id": lab_id,
        "backtest_id": backtest_id,
        "bot_name": bot_name,
        "account_id": account_id,
        "market": "BINANCE_BTC_USDT_",
        "leverage": 0
    }
    create_bot_response = client.post("/create_trade_bot_from_lab", json=create_bot_payload)
    assert create_bot_response.status_code == 200
    bot_id = create_bot_response.json()["bot_id"]
    created_bot_ids.append(bot_id)

    # Get current bot settings
    get_bot_response = client.get(f"/get_all_trade_bots")
    assert get_bot_response.status_code == 200
    current_bot = next((b for b in get_bot_response.json()["Data"] if b["ID"] == bot_id), None)
    assert current_bot is not None

    # Modify a setting (e.g., tradeAmount)
    updated_trade_amount = 250.0
    current_bot["ST"]["tradeAmount"] = updated_trade_amount

    # Prepare payload for /edit_bot_parameter
    payload = {
        "bot_id": bot_id,
        "settings": current_bot["ST"]
    }

    # Call the /edit_bot_parameter endpoint
    response = client.post("/edit_bot_parameter", json=payload)
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert response.json()["Data"]["ST"]["tradeAmount"] == updated_trade_amount

    # Verify the update by fetching the bot again
    get_bot_again_response = client.get(f"/get_all_trade_bots")
    assert get_bot_again_response.status_code == 200
    verified_bot = next((b for b in get_bot_again_response.json()["Data"] if b["ID"] == bot_id), None)
    assert verified_bot is not None
    assert verified_bot["ST"]["tradeAmount"] == updated_trade_amount

# Test /get_bot_logbook/{bot_id} endpoint
def test_get_bot_logbook(setup_test_environment):
    client = setup_test_environment["client"]
    # This test requires a valid bot_id from your live server that has some log data
    # You might need to create a bot and run it for a short period to generate logs
    bot_id = "YOUR_LIVE_BOT_ID_WITH_LOGS" # Placeholder for a bot that has generated logs
    response = client.get(f"/get_bot_logbook/{bot_id}")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert isinstance(response.json()["Data"], list)

# Test /get_all_completed_orders endpoint
def test_get_all_completed_orders(setup_test_environment):
    client = setup_test_environment["client"]
    response = client.get("/get_all_completed_orders")
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert isinstance(response.json()["Data"], list)