from pyHaasAPI.api import (
    RequestsExecutor,
    get_scripts_by_name,
    get_lab_details,
    create_lab,
    delete_lab,
    get_accounts,
    Guest
)
from pyHaasAPI.model import CreateLabRequest
from pyHaasAPI.price import PriceAPI
from pyHaasAPI.parameters import ScriptParameters, ParameterType
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Create and authenticate executor with Guest state
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
        
    script = scripts[0]  # Take first Scalper Bot script
    print(f"\nSelected Script: {script.script_name}")
    print(f"Script ID: {script.script_id}")
    
    # Get YAY account
    accounts = get_accounts(auth_executor)
    yay_account = next((acc for acc in accounts if "YAY" in acc.name), None)
    if not yay_account:
        print("No YAY account found!")
        return
    
    # Initialize PriceAPI and get valid market
    price_api = PriceAPI(auth_executor)
    market = price_api.get_valid_market(yay_account.exchange_code)
    
    # Create temporary lab
    lab = create_lab(auth_executor, CreateLabRequest(
        script_id=script.script_id,
        name="temp_settings_lab",
        account_id=yay_account.account_id,
        market=f"{yay_account.exchange_code.upper()}_{market.primary.upper()}_{market.secondary.upper()}_",
        interval=15,
        default_price_data_style="CandleStick"
    ))
    
    try:
        # Get lab details
        details = get_lab_details(auth_executor, lab.lab_id)
        
        # Print lab configuration
        print("\nLab Configuration:")
        for field, value in details.config.dict().items():
            print(f"  {field}: {value}")
        
        # Print lab settings
        print("\nLab Settings:")
        for field, value in details.settings.dict().items():
            print(f"  {field}: {value}")
        
        # Use ScriptParameters to handle parameter grouping and access
        script_params = ScriptParameters.from_api_response(details.parameters)
        
        print("\nParameters by Group:")
        def print_group(group, indent=""):
            for name, param in group.parameters.items():
                if param.value is not None:  # Only print parameters with values
                    print(f"\n{indent}Group Parameter: {name}")
                    print(f"{indent}  Type: {param.param_type}")
                    print(f"{indent}  Value: {param.value}")
                    print(f"{indent}  Enabled: {param.is_enabled}")
                    if param.options:
                        print(f"{indent}  Options: {param.options}")
            
            # Print subgroups
            for subgroup_name, subgroup in group.subgroups.items():
                print(f"\n{indent}Group: {subgroup_name}")
                print_group(subgroup, indent + "  ")
        
        # Ensure groups are initialized
        script_params._ensure_grouped()
        print_group(script_params._grouped_parameters)
            
    finally:
        # Clean up temporary lab
        delete_lab(auth_executor, lab.lab_id)
        print("\nTemporary lab deleted")

if __name__ == "__main__":
    main()