"""
Example demonstrating proper parameter handling for HaaS labs.

This example shows:
1. Creating a lab with default parameters
2. Reading and formatting parameters
3. Updating parameters with proper type handling
4. Verifying parameter updates
"""

import random
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import os

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
from pyHaasAPI.parameters import ScriptParameters, ParameterType
from pyHaasAPI.price import PriceAPI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_parameter_details(param: Dict[str, Any]) -> None:
    """Log detailed information about a parameter"""
    logger.debug("Parameter Details:")
    logger.debug(f"  Key: {param.get('K', 'N/A')}")
    logger.debug(f"  Type: {param.get('T', 'N/A')}")
    logger.debug(f"  Options: {param.get('O', 'N/A')}")
    logger.debug(f"  Is Enabled: {param.get('I', 'N/A')}")
    logger.debug(f"  Is Selected: {param.get('IS', 'N/A')}")

def format_parameter_value(value: Any, param_type: ParameterType) -> str:
    """Format parameter value based on type"""
    if param_type == ParameterType.INTEGER:
        return str(int(float(value)))
    elif param_type == ParameterType.DECIMAL:
        return str(round(float(value), 8))
    elif param_type == ParameterType.BOOLEAN:
        return str(bool(value))
    else:
        return str(value)

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
    market_tag = f"{account.exchange_code}_{market.primary}_{market.secondary}_"
    print(f"Trade market: {market_tag}")
    
    # Create temporary lab
    lab = create_lab(auth_executor, CreateLabRequest(
        script_id=script.script_id,
        name="parameter_handling_example",
        account_id=account.account_id,
        market=market_tag,
        interval=15,
        default_price_data_style="CandleStick"
    ))
    
    try:
        # Get initial lab details
        details = get_lab_details(auth_executor, lab.lab_id)
        logger.debug("Retrieved initial lab details")
        
        # Get current parameters
        script_params = ScriptParameters.from_api_response(details.parameters)
        print("\nOriginal Parameters:")
        for param in script_params:
            if param.is_enabled:
                print(f"{param.key}: {param.current_value}")
        
        # Update parameters with proper type handling
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
                print(f"{param.key}:")
                print(f"  Type: {ParameterType(param.type).name}")
                print(f"  Options: {param.options}")
                
        # Demonstrate parameter type handling
        print("\nParameter Type Examples:")
        for param in updated_params:
            if not param.is_enabled:
                continue
                
            param_type = ParameterType(param.type)
            print(f"\n{param.key} ({param_type.name}):")
            
            if param_type == ParameterType.INTEGER:
                print("  Range: [base-2, base, base+2]")
            elif param_type == ParameterType.DECIMAL:
                print("  Range: [base*0.8, base, base*1.2]")
            elif param_type == ParameterType.BOOLEAN:
                print("  Options: ['True', 'False']")
            elif param_type == ParameterType.STRING:
                print("  Keeping original options")
            elif param_type == ParameterType.SELECTION:
                print("  Keeping original selection values")
                
            print(f"  Current Options: {param.options}")
            
    finally:
        # Clean up temporary lab
        delete_lab(auth_executor, lab.lab_id)
        print("\nTemporary lab deleted")
        
    print('\nDone')

if __name__ == "__main__":
    main() 