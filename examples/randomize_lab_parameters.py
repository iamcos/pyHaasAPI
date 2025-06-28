from pyHaasAPI.api import (
    RequestsExecutor,
    get_scripts_by_name,
    get_lab_details,
    create_lab,
    delete_lab,
    get_accounts,
    Guest
)
from pyHaasAPI.lab import update_lab_parameter_ranges
from pyHaasAPI.model import CreateLabRequest
from pyHaasAPI.parameters import ScriptParameters
from pyHaasAPI.price import PriceAPI
import os
import random
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    # Create and authenticate executor
    executor = RequestsExecutor(
        host=os.getenv("HAAS_API_HOST", "127.0.0.1"),
        port=int(os.getenv("HAAS_API_PORT", "8090")),
        state=Guest()
    )
    
    auth_executor = executor.authenticate(
        email=os.getenv("HAAS_API_EMAIL"),
        password=os.getenv("HAAS_API_PASSWORD")
    )
    
    # Get Scalper Bot scripts
    scripts = get_scripts_by_name(auth_executor, "Haasonline Original - Scalper Bot")
    if not scripts:
        print("No Scalper Bot scripts found!")
        return
        
    script = random.choice(scripts)
    print(f"\nSelected Script: {script.script_name}")
    
    # Get first available account
    accounts = get_accounts(auth_executor)
    if not accounts:
        print("No accounts found!")
        return
    account = accounts[0]
    
    # Initialize PriceAPI and get valid market
    price_api = PriceAPI(auth_executor)
    market = price_api.get_valid_market(account.exchange_code)
    market_tag = f"{account.exchange_code.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
    print(f"Trade market: {market_tag}")
    
    # Create temporary lab
    lab = create_lab(auth_executor, CreateLabRequest(
        script_id=script.script_id,
        name="temp_random_params_lab",
        account_id=account.account_id,
        market=market_tag,
        interval=15,
        default_price_data_style="CandleStick"
    ))
    
    try:
        # Get initial lab details
        details = get_lab_details(auth_executor, lab.lab_id)
        logger.debug("Retrieved initial lab details")
        
        # Get current parameters using updated ScriptParameters class
        script_params = ScriptParameters.from_api_response(details.parameters)
        print("\nOriginal Parameters:")
        for param in script_params:
            if param.is_enabled:
                print(f"{param.key}: {param.current_value}")
        
        # Update parameters using the improved function
        updated_details = update_lab_parameter_ranges(
            executor=auth_executor,
            lab_id=lab.lab_id,
            randomize=True
        )
        
        # Verify updates
        print("\nUpdated Parameters:")
        updated_params = ScriptParameters.from_api_response(updated_details.parameters)
        for param in updated_params:
            if param.is_enabled:
                print(f"{param.key}: {param.options}")
            
    finally:
        # Clean up temporary lab
        delete_lab(auth_executor, lab.lab_id)
        print("\nTemporary lab deleted")
        
        print('Done')

if __name__ == "__main__":
    main() 