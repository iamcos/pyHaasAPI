from haaslib import api
from haaslib.lab import get_lab_parameters, update_lab_parameter_ranges
from haaslib.model import ParameterRange, ParameterType
import random
from typing import Any, List, Union

def generate_random_value(param_type: ParameterType, current_value: Any) -> Union[ParameterRange, List[Any]]:
    """Generate random parameter values based on type"""
    if param_type == ParameterType.INTEGER:
        # Generate random integer range around current value
        current = int(float(current_value))  # Handle both string and float inputs
        return ParameterRange(
            start=max(1, current - 5),
            end=current + 5,
            step=1
        )
    elif param_type == ParameterType.DECIMAL:
        # Generate random decimal range around current value
        current = float(current_value)
        return ParameterRange(
            start=max(0.1, current - 1.0),
            end=current + 1.0,
            step=0.1,
            decimals=3
        )
    elif param_type == ParameterType.BOOLEAN:
        return [True, False]  # Always test both values
    elif param_type == ParameterType.SELECTION:
        # For selection types, randomize the order of available values
        if isinstance(current_value, list):
            values = current_value
        else:
            values = [current_value]
        return random.sample(values, len(values))
    else:  # STRING or other types
        return [str(current_value)]  # Convert to string to be safe

def main():
    # Setup connection
    executor = api.RequestsExecutor(host="127.0.0.1", port=8090, state=api.Guest())
    executor = executor.authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    
    # Get all scripts and choose one that has parameters
    scripts = api.get_all_scripts(executor)
    script = next(
        (s for s in scripts if s.script_name == "Haasonline Original - Scalper Bot"),
        random.choice(scripts)
    )
    
    # Create a test lab
    accounts = api.get_accounts(executor)
    markets = api.get_all_markets(executor)
    
    lab = api.create_lab(
        executor,
        api.CreateLabRequest(
            script_id=script.script_id,
            name=f"Parameter Test Lab {random.randint(1000,9999)}",
            account_id=random.choice(accounts).account_id,
            market=random.choice(markets).as_market_tag(),
            interval=15,
            default_price_data_style="CandleStick"
        )
    )
    
    try:
        # Get current parameters
        parameters = get_lab_parameters(executor, lab.lab_id)
        
        print("\nCurrent parameters:")
        for param in parameters:
            print(f"\nParameter: {param.name}")
            print(f"Type: {param.param_type}")
            print(f"Current value: {param.current_value}")
            if param.range_config:
                print(f"Current range: {param.range_config.start} to {param.range_config.end} step {param.range_config.step}")
            
        # Generate random parameter updates
        updates = {}
        for param in parameters:
            if not param.is_enabled:
                continue
                
            new_values = generate_random_value(
                param.param_type,
                param.current_value
            )
            updates[param.name] = new_values
            
        # Update parameters
        print("\nUpdating parameters with new values:")
        for name, values in updates.items():
            if isinstance(values, ParameterRange):
                print(f"{name}: Range {values.start} to {values.end} step {values.step}")
            else:
                print(f"{name}: Values {values}")
                
        update_lab_parameter_ranges(executor, lab.lab_id, updates)
        
        # Verify updates
        updated_params = get_lab_parameters(executor, lab.lab_id)
        print("\nUpdated parameters:")
        for param in updated_params:
            print(f"\n{param.name}:")
            print(f"Type: {param.param_type}")
            print(f"Possible values: {param.possible_values}")
            
    finally:
        # Cleanup
        print("\nCleaning up test lab...")
        api.delete_lab(executor, lab.lab_id)
        print("Done!")

if __name__ == "__main__":
    main()