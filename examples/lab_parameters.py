from pyHaasAPI import api
from pyHaasAPI.lab import get_lab_parameters, update_lab_parameter_ranges
from pyHaasAPI.parameters import ParameterType, ParameterRange
from pyHaasAPI.model import (
    CreateLabRequest,
)
import random
from typing import Any, Dict, List, Union
from loguru import logger

ParameterOption = Union[str, int, float, bool]

def print_script_details(script):
    """Print detailed information about a script"""
    logger.info("\n=== Script Details ===")
    logger.info(f"Name: {script.script_name}")
    logger.info(f"ID: {script.script_id}")
    logger.info(f"Description: {script.script_description}")
    logger.info(f"Type: {script.script_type}")
    logger.info(f"Dependencies: {', '.join(script.dependencies) if script.dependencies else 'None'}")
    logger.info("==================\n")

def print_lab_details(lab):
    """Print detailed information about a lab configuration"""
    # First, let's see the raw data
    logger.info("\n=== Raw Lab Response ===")
    logger.info(f"Available fields: {lab.model_dump().keys()}")
    logger.info(f"Raw data: {lab.model_dump_json(indent=2)}")
    
    logger.info("\n=== Lab Configuration ===")
    logger.info(f"Name: {lab.name}")
    logger.info(f"ID: {lab.lab_id}")
    logger.info(f"Status: {lab.status}")
    
    # Print settings using the actual response structure
    logger.info("\n--- Settings ---")
    if hasattr(lab, 'settings'):
        settings = lab.settings
        logger.info(f"Market: {getattr(settings, 'market_tag', 'N/A')}")
        logger.info(f"Interval: {getattr(settings, 'interval', 'N/A')}")
        logger.info(f"Trade Amount: {getattr(settings, 'trade_amount', 'N/A')}")
        logger.info(f"Leverage: {getattr(settings, 'leverage', 'N/A')}")
    
    # Print configuration using the actual response structure
    logger.info("\n--- Configuration ---")
    if hasattr(lab, 'config'):
        config = lab.config
        logger.info(f"Max Population: {getattr(config, 'max_population', 'N/A')}")
        logger.info(f"Max Generations: {getattr(config, 'max_generations', 'N/A')}")
        logger.info(f"Max Elites: {getattr(config, 'max_elites', 'N/A')}")
        logger.info(f"Mix Rate: {getattr(config, 'mix_rate', 'N/A')}")
        logger.info(f"Adjust Rate: {getattr(config, 'adjust_rate', 'N/A')}")
    
    # Print parameters if available
    if hasattr(lab, 'parameters'):
        logger.info("\n=== Parameters ===")
        current_group = []
        for param in lab.parameters:
            # Handle parameter groups (if present)
            is_group = param.get('is_setting_group') if isinstance(param, dict) else getattr(param, 'is_setting_group', False)
            group_path = param.get('group_path', []) if isinstance(param, dict) else getattr(param, 'group_path', [])
            display_name = param.get('display_name', param.get('K', '')) if isinstance(param, dict) else getattr(param, 'display_name', '')
            if is_group:
                if len(group_path) <= len(current_group):
                    current_group = current_group[:len(group_path)-1]
                current_group.append(display_name)
                logger.info(f"\n{' > '.join(current_group)}:")
                continue
            # Print parameter details
            indent = "  " * len(current_group)
            logger.info(f"{indent}{display_name}:")
            value = param.get('current_value', param.get('O', [''])[0]) if isinstance(param, dict) else getattr(param, 'current_value', '')
            param_type = param.get('param_type', param.get('T', '')) if isinstance(param, dict) else getattr(param, 'param_type', '')
            is_enabled = param.get('is_enabled', param.get('I', True)) if isinstance(param, dict) else getattr(param, 'is_enabled', True)
            possible_values = param.get('possible_values', param.get('O', [])) if isinstance(param, dict) else getattr(param, 'possible_values', [])
            logger.info(f"{indent}  Value: {value}")
            logger.info(f"{indent}  Type: {param_type}")
            logger.info(f"{indent}  Enabled: {is_enabled}")
            if len(possible_values) > 1:
                logger.info(f"{indent}  Possible values: {possible_values}")
    
    logger.info("==================\n")

def generate_parameter_range(
    param_type: ParameterType,
    current_value: Any
) -> Union[ParameterRange, List[Any]]:
    """
    Generate parameter range based on type and current value
    
    Args:
        param_type: Type of the parameter
        current_value: Current parameter value
    
    Returns:
        Either a ParameterRange for numeric types or a list of values for others
    """
    try:
        if param_type == ParameterType.INTEGER:
            current = int(float(current_value))
            return ParameterRange(
                start=max(0, current - 5),
                end=current + 5,
                step=1
            )
        elif param_type == ParameterType.DECIMAL:
            current = float(current_value)
            return ParameterRange(
                start=max(0.001, current - 0.5),
                end=current + 0.5,
                step=0.001
            )
        elif param_type == ParameterType.BOOLEAN:
            return [True, False]
        elif param_type == ParameterType.SELECTION:
            if isinstance(current_value, (list, tuple)):
                return list(current_value)
            return [current_value]
        else:  # STRING or unknown types
            return [str(current_value)]
    except (ValueError, TypeError) as e:
        logger.warning(f"Error generating range for {param_type} with value {current_value}: {e}")
        return [current_value]

def main():
    # Initialize API executor
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    )
    
    # Authenticate
    executor = executor.authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    
    # Get available Scalper Bot scripts
    scripts = api.get_scripts_by_name(executor, "Haasonline Original - Scalper Bot")
    if not scripts:
        logger.error("No Scalper Bot scripts found")
        return
        
    # Print all available Scalper Bot scripts
    logger.info("\nAvailable Scalper Bot Scripts:")
    for idx, script in enumerate(scripts, 1):
        logger.info(f"{idx}. {script.script_name}")
    
    # Select first Scalper Bot script
    script = scripts[0]
    print_script_details(script)
    
    # Get random account and market
    accounts = api.get_accounts(executor)
    markets = api.get_all_markets(executor)
    
    if not accounts or not markets:
        logger.error("No accounts or markets available")
        return
        
    account = random.choice(accounts)
    market = random.choice(markets)
    
    lab = None
    lab_id = None  # Initialize lab_id at the start
    
    try:
        # Create lab
        lab_request = CreateLabRequest(
            script_id=script.script_id,
            name=f"PNL_Test_{random.randint(1000, 9999)}",
            account_id=account.account_id,
            market=market,
            interval=15,
            default_price_data_style="CandleStick"
        )
        
        response = api.create_lab(executor, lab_request)
        logger.debug(f"Lab creation response: {response.model_dump()}")
        
        # Store lab ID immediately after creation
        lab_id = response.lab_id if hasattr(response, 'lab_id') else None
        if not lab_id:
            raise ValueError("Failed to get lab ID from response")
            
        lab = response
        
        print_lab_details(lab)
        
        # Get and display current parameters
        parameters = get_lab_parameters(executor, lab.lab_id)
        logger.info("\n=== Current Parameters ===")
        for param in parameters:
            logger.info(f"\nParameter: {param}")
            logger.info(f"Type: {param.type}")
            logger.info(f"Current value: {param.current_value}")
            logger.info(f"Enabled: {param.is_enabled}")
            if hasattr(param, 'description') and param.description:
                logger.info(f"Description: {param.description}")
            
        # Generate parameter updates
        parameter_updates: Dict[str, Union[ParameterRange, List[Any]]] = {}
        for param in parameters:
            if not param.is_enabled:
                continue
                
            new_range = generate_parameter_range(
                ParameterType(param.type),
                param.current_value
            )
            parameter_updates[param.key] = new_range
            
        # Update parameters
        logger.info("\n=== Updating Parameters ===")
        for name, value_range in parameter_updates.items():
            if isinstance(value_range, ParameterRange):
                logger.info(f"{name}:")
                logger.info(f"  Range: {value_range.start} to {value_range.end}")
                logger.info(f"  Step: {value_range.step}")
            else:
                logger.info(f"{name}: Values {value_range}")
                
        update_lab_parameter_ranges(executor, lab.lab_id, parameter_updates)
        
        # Verify updates
        updated_params = get_lab_parameters(executor, lab.lab_id)
        logger.info("\n=== Updated Parameters ===")
        for param in updated_params:
            logger.info(f"\nParameter: {param.name}")
            logger.info(f"Type: {param.type}")
            logger.info(f"Possible values: {param.possible_values}")
            
    except Exception as e:
        logger.error(f"Error during parameter testing: {e}")
        raise
    finally:
        if lab_id:  # Now lab_id will always be defined
            logger.info(f"\nCleaning up test lab {lab_id}...")
            try:
                api.delete_lab(executor, lab_id)
                logger.info("Cleanup complete")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup lab: {cleanup_error}")

if __name__ == "__main__":
    main()