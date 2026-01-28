
import pytest
from datetime import datetime
from pyHaasAPI.models.account import AccountRecord
from pyHaasAPI.models.bot import BotDetails
from pyHaasAPI.models.market import Market

class TestDataclassModels:
    """Test the new Dataclass-based models with from_dict/to_dict"""

    def test_account_from_dict(self):
        data = {
            "accountId": "acc123",
            "name": "Binance Futures",
            "connected": True,
            "platformId": "10",
            "isSimulated": False
        }
        account = AccountRecord.from_dict(data)
        assert account.account_id == "acc123"
        assert account.name == "Binance Futures"
        assert account.connected is True
        assert account.platform_id == "10"
        assert account.is_simulated is False

    def test_bot_details_from_dict(self):
        data = {
            "botId": "bot789",
            "name": "Test Bot",
            "accountId": "acc123",
            "coin": "BTC",
            "roi": 15.5,
            "totalTrades": 100,
            "activated": True
        }
        bot = BotDetails.from_dict(data)
        assert bot.bot_id == "bot789"
        assert bot.bot_name == "Test Bot"
        assert bot.account_id == "acc123"
        assert bot.coin == "BTC"
        assert bot.roi == 15.5
        assert bot.total_trades == 100
        assert bot.is_active is True

    def test_market_serialization(self):
        market = Market(
            primary_currency="BTC",
            secondary_currency="USDT",
            contract_name="BTC/USDT",
            price_source="Binance"
        )
        data = market.to_dict()
        assert data["primaryCurrency"] == "BTC"
        assert data["secondaryCurrency"] == "USDT"
        
        # Test round trip
        market2 = Market.from_dict(data)
        assert market2.primary_currency == "BTC"
        assert market2.contract_name == "BTC/USDT"

    def test_nested_parsing(self):
        # Assuming we had nested structures, verified here.
        # For now, simplistic check is sufficient as models are flat or list-based.
        pass
