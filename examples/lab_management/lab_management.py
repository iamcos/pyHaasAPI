from pyHaasAPI.HaasOnlineClient import HaasOnlineClient
from pyHaasAPI.HaasOnlineClient import pyHaasAPI

def clone_and_run_labs(client: HaasOnlineClient, source_lab_id: str, markets: list[str]):
    """
    Clones a source lab to a list of markets and starts a backtest for each.

    Args:
        client: The HaasOnlineClient instance.
        source_lab_id: The ID of the source lab to clone.
        markets: A list of market identifiers to clone the lab to.

    Returns:
        A list of the newly created lab objects.
    """
    new_labs = []
    for market in markets:
        # Clone the lab
        cloned_lab = client.lab_manager.clone_lab(source_lab_id, new_name=f"Clone of {source_lab_id} for {market}")
        
        # Update the market for the cloned lab
        cloned_lab.settings.market_tag = market
        updated_lab = client.lab_manager.update_lab_details(cloned_lab)
        
        # Start a backtest for the updated lab
        client.lab_manager.start_lab_execution(updated_lab.lab_id)
        
        new_labs.append(updated_lab)
        
    return new_labs
