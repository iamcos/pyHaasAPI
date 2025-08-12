import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import time
import os
from dotenv import load_dotenv

# Load environment variables from the project root's .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../.env'))

# Fixture to create a TestClient for testing FastAPI endpoints
@pytest.fixture(scope="module")
def client():
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

def test_edit_bot_settings(setup_test_environment):
    client = setup_test_environment["client"]
    account_id = setup_test_environment["account_id"]
    script_id = setup_test_environment["script_id"]
    created_lab_ids = setup_test_environment["created_lab_ids"]
    created_bot_ids = setup_test_environment["created_bot_ids"]

    # Create a lab and run a backtest to get a backtest_id
    lab_name = f"EditBotSettingsLab_{int(time.time())}"
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

    bot_name = f"BotToEdit_{int(time.time())}"
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
    bots = get_bot_response.json()["Data"]
    current_bot = next((b for b in bots if b["ID"] == bot_id), None)
    assert current_bot is not None, f"Bot with ID {bot_id} not found."

    # Modify a setting (e.g., bot_name)
    updated_bot_name = f"BotEdited_{int(time.time())}"
    
    # Construct the settings payload. This needs to match the HaasScriptSettings model.
    # For simplicity, let's assume we are only changing the bot name, which is part of the top-level HaasBot object,
    # not directly in HaasScriptSettings.
    # The `edit_bot_settings` function in pyHaasAPI/api.py takes a HaasBot object.
    # The endpoint in mcp_server/main.py takes a HaasScriptSettings object.
    # This means we need to fetch the bot, update its settings, and then send the settings.
    
    # Let's assume for this test that we are modifying a parameter within the script settings.
    # We need to get the current settings, modify a parameter, and then send it back.
    # This requires a more complex setup to get the actual script parameters.
    # For now, let's just test the endpoint with a dummy settings object,
    # assuming the API will handle the update.
    # In a real scenario, you'd fetch the bot's full settings, modify a specific parameter,
    # and then send the updated settings.

    # For now, let's create a dummy HaasScriptSettings object to send.
    # This will likely overwrite existing settings if not handled carefully in the API.
    # The `edit_bot_settings` in `pyHaasAPI/api.py` takes a HaasBot object,
    # and the `mcp_server` endpoint takes `HaasScriptSettings`.
    # This means the `mcp_server` endpoint needs to fetch the bot, update its settings,
    # and then pass the full bot object to `api.edit_bot_settings`.
    # The `mcp_server/main.py` has been updated to do this.

    # Let's create a dummy settings object for the test.
    # In a real scenario, you'd fetch the bot's current settings and modify them.
    # Since we don't have a direct way to get HaasScriptSettings from the bot object via the API,
    # we'll have to make a simplified assumption for this test.
    # The `edit_bot_settings` function in `pyHaasAPI/api.py` expects a HaasBot object.
    # The `mcp_server` endpoint expects `HaasScriptSettings`.
    # The `mcp_server` endpoint should fetch the bot, update its settings, and then call the API.

    # Let's assume we want to change a simple string parameter within the settings.
    # We need to construct a valid HaasScriptSettings object.
    # This is a placeholder for actual script settings.
    # For a real test, you'd need to know the structure of the script's settings.
    # For now, let's just send a minimal valid HaasScriptSettings object.
    
    # The `HaasScriptSettings` model is defined in `pyHaasAPI/model.py`.
    # It has `script_id` and `parameters`.
    # We need to get the current script_id from the bot.
    
    # Fetch the bot again to get its current script_id and settings
    get_bot_response_after_creation = client.get(f"/get_all_trade_bots")
    assert get_bot_response_after_creation.status_code == 200
    bots_after_creation = get_bot_response_after_creation.json()["Data"]
    bot_details_after_creation = next((b for b in bots_after_creation if b["ID"] == bot_id), None)
    assert bot_details_after_creation is not None, f"Bot with ID {bot_id} not found after creation."

    # Extract current settings from the bot details
    # The settings are usually under a key like 'S' or 'Settings' in the raw API response
    # and then need to be parsed into HaasScriptSettings.
    # For this test, let's assume a simple structure for settings.
    # This part is tricky because the `HaasBot` object returned by `get_all_bots`
    # might not contain the full `HaasScriptSettings` object directly.
    # The `edit_bot_settings` function in `pyHaasAPI/api.py` expects a `HaasBot` object
    # with its `settings` attribute populated.
    # The `mcp_server` endpoint expects `HaasScriptSettings`.

    # Let's simplify and assume we are just sending a new settings object.
    # This might not be a true "edit" but a "replace" of settings.
    # To truly "edit", we would need to fetch the current settings, modify them, and send them back.
    # The `get_bot_script_parameters` function in `pyHaasAPI/api.py` can get script parameters.
    # However, the `edit_bot_settings` endpoint in `mcp_server` takes `HaasScriptSettings`.

    # Let's create a dummy HaasScriptSettings object with a modified parameter.
    # This assumes a parameter named "BotName" exists and is a string.
    # This is a simplification for testing the endpoint's basic functionality.
    
    # The `HaasScriptSettings` model has `script_id` and `parameters`.
    # The `parameters` is a list of `ScriptParameter`.
    # A `ScriptParameter` has `key`, `value`, `type`, etc.

    # Let's try to modify the bot's name through settings, if possible.
    # The `HaasBot` object has a `name` attribute.
    # The `edit_bot_settings` in `pyHaasAPI/api.py` takes a `HaasBot` object.
    # The `mcp_server` endpoint takes `HaasScriptSettings`.
    # This means the `mcp_server` endpoint needs to fetch the bot, update its `settings` attribute,
    # and then pass the `HaasBot` object to `api.edit_bot_settings`.

    # Let's assume we want to change a parameter within the bot's script settings.
    # We need to construct a valid HaasScriptSettings object.
    # For this test, let's assume a simple script with a single parameter.
    
    # Get the bot's current details to extract its script_id
    get_bot_details_response = client.get(f"/get_all_trade_bots")
    assert get_bot_details_response.status_code == 200
    all_bots = get_bot_details_response.json()["Data"]
    target_bot = next((b for b in all_bots if b["ID"] == bot_id), None)
    assert target_bot is not None, f"Bot with ID {bot_id} not found."
    
    current_script_id = target_bot["ScriptId"] # Assuming ScriptId is available

    # Create a dummy HaasScriptSettings object with a modified parameter
    # This is a placeholder. In a real scenario, you'd fetch the actual parameters
    # and modify one.
    updated_settings = {
        "script_id": current_script_id,
        "parameters": [
            {"key": "SomeParameter", "value": "NewValue", "type": "string"}
        ]
    }

    edit_payload = {
        "bot_id": bot_id,
        "settings": updated_settings
    }

    response = client.post("/edit_bot_settings", json=edit_payload)
    assert response.status_code == 200
    assert response.json()["Success"] == True
    assert "message" in response.json()
    assert response.json()["Data"]["ID"] == bot_id

    # Verify the setting has been updated (this might be tricky without a direct get_bot_settings endpoint)
    # For now, we'll rely on the API's success response.
    # A more robust test would involve fetching the bot again and inspecting its settings.
    # However, the `get_bot` endpoint in `pyHaasAPI/api.py` returns a `HaasBot` object,
    # but it might not contain the detailed `HaasScriptSettings` directly.
    # The `get_bot_script_parameters` function exists, but it returns a list of `ScriptParameter`.
    # We can use that to verify.

    # Let's try to get the bot again and check if its name (or some other easily verifiable setting) changed.
    # The `edit_bot_settings` function in `pyHaasAPI/api.py` returns the updated `HaasBot` object.
    # The `mcp_server` endpoint also returns the updated `HaasBot` object.
    # We can check the `Name` attribute of the returned bot.
    
    # The `edit_bot_settings` endpoint in `mcp_server/main.py` now fetches the bot,
    # updates its settings, and then calls `api.edit_bot_settings`.
    # The `api.edit_bot_settings` returns the updated `HaasBot`.
    # So, we can check the `Name` of the returned bot.
    
    # The `edit_bot_settings` function in `pyHaasAPI/api.py` does not directly change the bot's name.
    # It changes the `settings` attribute of the `HaasBot` object.
    # The `HaasScriptSettings` object does not have a `name` attribute.
    # So, we cannot verify the bot's name change through `edit_bot_settings`.
    # We need to verify that the `settings` themselves are updated.
    
    # This test needs to be refined to actually check if the `settings` were updated.
    # This would involve:
    # 1. Getting the bot's current settings (e.g., using `get_bot_script_parameters`).
    # 2. Modifying a specific parameter within those settings.
    # 3. Sending the updated settings via `/edit_bot_settings`.
    # 4. Getting the bot's settings again and asserting the change.

    # For now, let's just assert that the call was successful.
    # A more complete test would require a way to inspect the bot's script parameters after the update.
    # The `get_bot_script_parameters` function returns a list of `ScriptParameter`.
    # We can use that to verify.

    # Get the bot's script parameters after the update
    get_updated_params_response = client.get(f"/get_bot_script_parameters/{bot_id}")
    assert get_updated_params_response.status_code == 200
    updated_params = get_updated_params_response.json()["Data"]
    
    # Find the parameter we tried to change
    changed_param = next((p for p in updated_params if p["Key"] == "SomeParameter"), None)
    assert changed_param is not None
    assert changed_param["Value"] == "NewValue"