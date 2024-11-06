from typing import Literal, TypeVar
from pydantic import BaseModel
from typing import Collection

ApiResponseData = TypeVar("ApiResponseData", bound=BaseModel | Collection[BaseModel] | bool | str)
"""Any response from Haas API should be `pydantic` model or collection of them."""

HaasApiEndpoint = Literal["Labs", "Account", "HaasScript", "Price", "User", "Bot"]
"""Known Haas API endpoints"""

PriceDataStyle = Literal[
    "CandleStick",
    "CandleStickHLC", 
    "HeikinAshi",
    "OHLC",
    "HLC",
    "CloseLine",
    "Line",
    "Mountain",
] 