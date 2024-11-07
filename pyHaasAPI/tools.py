import random
from typing import Any, Callable, Optional

from pyHaasAPI import api
from pyHaasAPI.api import SyncExecutor
from pyHaasAPI.model import CloudMarket
from pyHaasAPI.price import PriceAPI


def select_random_markets(
    executor: SyncExecutor[Any],
    count: int,
    filterer: Optional[Callable[[CloudMarket], bool]] = None,
) -> list[CloudMarket]:
    """
    Selects random markets filtered by given criteria
    """
    price_api = PriceAPI(executor)
    all_markets = price_api.get_all_markets()
    
    if filterer:
        filtered_markets = [m for m in all_markets if filterer(m)]
    else:
        filtered_markets = all_markets

    if count >= len(filtered_markets):
        return filtered_markets

    return random.sample(filtered_markets, count)
