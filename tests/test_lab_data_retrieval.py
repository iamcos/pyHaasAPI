
import os
import pytest
from dotenv import load_dotenv
from pyHaasAPI.api import RequestsExecutor, get_lab_details, get_backtest_result
from pyHaasAPI.backtest_object import BacktestObject
from pyHaasAPI.model import GetBacktestResultRequest

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(scope="module")
def authenticated_executor():
    """Provides an authenticated Haas API executor."""
    host = os.getenv("API_HOST")
    port = int(os.getenv("API_PORT"))
    email = os.getenv("API_EMAIL")
    password = os.getenv("API_PASSWORD")

    # Check if all required environment variables are set
    if not all([host, port, email, password]):
        pytest.fail("Missing required environment variables (API_HOST, API_PORT, API_EMAIL, API_PASSWORD)")

    # Create a guest executor and authenticate
    guest_executor = RequestsExecutor(host=host, port=port, state=None)
    try:
        auth_executor = guest_executor.authenticate(email, password)
        return auth_executor
    except Exception as e:
        pytest.fail(f"Authentication failed: {e}")

def test_retrieve_all_lab_data(authenticated_executor):
    """
    Test to retrieve all available data for a specific lab, including all its backtests.
    """
    lab_id = "8a03fde1-c755-494c-a975-daeed1257518"

    print(f"--- Retrieving data for Lab ID: {lab_id} ---")

    # 1. Get Lab Details
    try:
        lab_details = get_lab_details(authenticated_executor, lab_id)
        print(f"Successfully retrieved details for Lab: {lab_details.name}")
        assert lab_details.lab_id == lab_id
    except Exception as e:
        pytest.fail(f"Failed to get lab details: {e}")

    # 2. Get Backtest Results for the Lab
    backtests = []
    try:
        req = GetBacktestResultRequest(lab_id=lab_id, next_page_id=0, page_lenght=100)
        paginated_response = get_backtest_result(authenticated_executor, req)
        
        if hasattr(paginated_response, 'items'):
             backtests = paginated_response.items
        else:
            backtests = paginated_response

        print(f"Found {len(backtests)} backtests for Lab ID: {lab_id}")
        assert isinstance(backtests, list)
    except Exception as e:
        pytest.fail(f"Failed to get backtest results: {e}")

    if not backtests:
        print("No backtests found for this lab. Test finished.")
        return

    # 3. For each backtest, retrieve all its data using BacktestObject
    for i, backtest_summary in enumerate(backtests):
        if i >= 2:
            print(f"\n--- Skipping Backtest ID: {backtest_summary.backtest_id} (limited to first 2 for testing) ---")
            continue

        backtest_id = backtest_summary.backtest_id
        print(f"\n--- Processing Backtest ID: {backtest_id} ---")
        try:
            backtest_obj = BacktestObject(authenticated_executor, lab_id, backtest_id)

            print(f"- Metadata: {backtest_obj.metadata.__dict__ if backtest_obj.metadata else 'Not Loaded'}")
            print(f"- Runtime: {backtest_obj.runtime.__dict__ if backtest_obj.runtime else 'Not Loaded'}")
            print(f"- Positions: {len(backtest_obj.positions) if backtest_obj.positions is not None else 'Not Loaded'}")
            print(f"- Logs: {backtest_obj.logs.__dict__ if backtest_obj.logs else 'Not Loaded'}")
            
            # Fetch chart data for the first two backtests
            print(f"- Chart: {backtest_obj.chart_partition is not None}")

            print(f"--- Finished Processing Backtest ID: {backtest_id} ---")

        except Exception as e:
            pytest.fail(f"An unexpected error occurred while processing backtest {backtest_id}: {e}")
