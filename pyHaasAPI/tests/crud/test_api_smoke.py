"""
Basic API smoke tests to validate connectivity and JSON-capable endpoints.
"""

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.crud
@pytest.mark.srv03
async def test_health_endpoint(auth_context):
    client = auth_context['client']
    # Use the lightweight health/ping the client already supports
    response = await client.get("/UserAPI.php", params={"channel": "REFRESH_LICENSE"})
    assert response.status == 200


@pytest.mark.crud
@pytest.mark.srv03
async def test_auth_session_valid(auth_context):
    session = auth_context['session']
    assert getattr(session, 'user_id', None), "Authenticated session must include user_id"
    assert getattr(session, 'interface_key', None), "Authenticated session must include interface_key"


@pytest.mark.crud
@pytest.mark.srv03
async def test_accounts_list_smoke(apis):
    account_api = apis['account_api']
    accounts = await account_api.get_accounts()
    assert isinstance(accounts, list)


@pytest.mark.crud
@pytest.mark.srv03
async def test_markets_read_smoke(apis):
    market_api = apis['market_api']
    markets = await market_api.get_trade_markets()
    assert isinstance(markets, list)


@pytest.mark.crud
@pytest.mark.srv03
async def test_scripts_read_smoke(apis):
    script_api = apis['script_api']
    scripts = await script_api.get_all_scripts()
    assert isinstance(scripts, list)


@pytest.mark.crud
@pytest.mark.srv03
async def test_orders_read_smoke(apis, default_entities):
    order_api = apis['order_api']
    account_id = default_entities['account_id']
    orders = await order_api.get_account_orders(account_id)
    assert isinstance(orders, list)


@pytest.mark.crud
@pytest.mark.srv03
async def test_backtests_read_smoke(apis):
    backtest_api = apis['backtest_api']
    status = await backtest_api.get_history_status()
    assert isinstance(status, (dict, list))


@pytest.mark.crud
@pytest.mark.srv03
async def test_lab_bot_crud_smoke(apis, default_entities):
    """Create minimal lab and bot, read back, then delete (smoke)."""
    lab_api = apis['lab_api']
    bot_api = apis['bot_api']
    account_id = default_entities['account_id']
    market_tag = default_entities['market_tag']

    # Scripts are optional here; use a placeholder or first available
    script_id = default_entities['script_id']

    # Create lab (name should be unique per run)
    lab_name = f"smoke-lab"
    try:
        lab = await lab_api.create_lab(
            script_id=script_id,
            name=lab_name,
            account_id=account_id,
            market=market_tag,
            interval=1,
            trade_amount=100.0,
        )
        assert getattr(lab, 'lab_id', None)

        # Read lab details
        details = await lab_api.get_lab_details(lab.lab_id)
        assert getattr(details, 'lab_id', None) == lab.lab_id

        # Create bot from basic params (direct create)
        bot_name = f"smoke-bot"
        bot = await bot_api.create_bot(
            bot_name=bot_name,
            script_id=script_id,
            script_type="trading",
            account_id=account_id,
            market=market_tag,
        )
        assert getattr(bot, 'bot_id', None)

        # Read bot details
        bot_details = await bot_api.get_bot_details(bot.bot_id)
        assert getattr(bot_details, 'bot_id', None) == bot.bot_id

    finally:
        try:
            # Delete bot first
            if 'bot' in locals() and getattr(bot, 'bot_id', None):
                await bot_api.deactivate_bot(bot.bot_id)
                await bot_api.delete_bot(bot.bot_id)
        except Exception:
            pass
        try:
            # Delete lab
            if 'lab' in locals() and getattr(lab, 'lab_id', None):
                await lab_api.delete_lab(lab.lab_id)
        except Exception:
            pass
