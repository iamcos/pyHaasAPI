
import os
import sys
import random
from pprint import pprint
from dotenv import load_dotenv
from pyHaasAPI.api import RequestsExecutor, HaasApiError, Guest, get_bot, edit_bot, get_all_bots
from pyHaasAPI.model import HaasBot

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

def authenticate_and_get_executor():
    """
    Authenticates with the Haas API and returns an executor object.
    """
    try:
        executor = RequestsExecutor(host=ip, port=port, state=Guest())
        interface_key = "".join(f"{random.randint(0, 100)}" for _ in range(10))

        # Authenticate and get the user ID
        auth_response = executor.execute(
            "User",
            response_type=dict,
            query_params={
                "channel": "LOGIN_WITH_ONE_TIME_CODE",
                "email": email,
                "pincode": 123456, # Using a static pincode
                "interfaceKey": interface_key,
            },
        )

        print("Authentication response:", auth_response)
        if not auth_response.get("Success"):
            raise HaasApiError("Failed to login with credentials")

        # Manually create the authenticated state
        # This is where we were having issues before
        # We will need to inspect the auth_response to get the user ID
        user_id = "" # Replace with the actual user ID from the response

        authenticated_state = Authenticated(user_id=user_id, interface_key=interface_key)
        return RequestsExecutor(host=ip, port=port, state=authenticated_state)

    except HaasApiError as e:
        print(f"Authentication failed: {e}")
        return None

def edit_bot_parameter(executor, bot_id: str, parameter_key: str, new_value: any):
    """
    Edits a specific parameter of a given bot.
    """
    try:
        # Get the full bot object
        bot = get_bot(executor, bot_id)
        if not bot:
            return {"success": False, "message": f"Bot with ID '{bot_id}' not found."}

        # Update the parameter value in the bot's script_parameters
        if parameter_key not in bot.settings.script_parameters:
            return {"success": False, "message": f"Parameter '{parameter_key}' not found for bot '{bot_id}'."}

        bot.settings.script_parameters[parameter_key] = new_value

        # Update the bot with the modified parameters
        response = edit_bot(executor, bot)

        return {"success": True, "message": "Bot parameter edited successfully.", "response": response}
    except HaasApiError as e:
        print(f"Error editing bot parameter: {e}")
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    executor = authenticate_and_get_executor()
    if not executor:
        print("Authentication failed. Exiting.")
        sys.exit(1)

    try:
        # Get all bots
        all_bots = get_all_bots(executor)
        if not all_bots:
            print("No bots found.")
            sys.exit(0)

        # Select the first bot
        target_bot = all_bots[0]
        bot_id = target_bot.bot_id

        # Find a parameter to edit (example: first parameter)
        if not target_bot.settings.script_parameters:
            print(f"No parameters found for bot '{bot_id}'.")
            sys.exit(0)

        param_to_edit_key = list(target_bot.settings.script_parameters.keys())[0]
        current_value = target_bot.settings.script_parameters[param_to_edit_key]
        
        # Determine a new value (e.g., increment if it's a number)
        try:
            new_value = float(current_value) + 1
        except (ValueError, TypeError):
            new_value = "edited_by_gemini"

        print(f"Editing bot '{bot_id}'")
        print(f"  Parameter: '{param_to_edit_key}'")
        print(f"  Current Value: '{current_value}'")
        print(f"  New Value: '{new_value}'")

        # Edit the bot parameter
        result = edit_bot_parameter(executor, bot_id, param_to_edit_key, new_value)
        pprint(result)

    except HaasApiError as e:
        print(f"An API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
