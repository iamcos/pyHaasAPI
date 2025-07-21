Bot Management Examples
======================

This page demonstrates how to manage trading bots using pyHaasAPI, including listing, creating, activating, and deleting bots.

.. contents::
   :local:
   :depth: 2

Listing Bots
------------

To list all bots:

.. code-block:: python

    from pyHaasAPI import api
    from config import settings

    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    bots = api.get_all_bots(executor)
    for bot in bots:
        print(f"Bot: {bot.bot_name} (ID: {bot.bot_id})")

Creating a Bot from a Lab
-------------------------

You can create a bot from a completed lab backtest configuration:

.. code-block:: python

    from pyHaasAPI.model import AddBotFromLabRequest, CloudMarket

    # Assume you have a completed lab and backtest result
    lab_id = "your_lab_id"
    backtest_id = "your_backtest_id"
    account_id = "your_account_id"
    market = CloudMarket(
        category="SPOT",
        price_source="BINANCE",
        primary="BTC",
        secondary="USDT"
    )
    bot_name = "MyBotFromLab"

    request = AddBotFromLabRequest(
        lab_id=lab_id,
        backtest_id=backtest_id,
        bot_name=bot_name,
        account_id=account_id,
        market=market,
        leverage=0
    )
    bot = api.add_bot_from_lab(executor, request)
    print(f"Created bot: {bot.bot_name} (ID: {bot.bot_id})")

Activating and Deactivating a Bot
---------------------------------

.. code-block:: python

    # Activate a bot
    api.activate_bot(executor, bot.bot_id)
    print("Bot activated.")

    # Deactivate a bot
    api.deactivate_bot(executor, bot.bot_id)
    print("Bot deactivated.")

Deleting a Bot
--------------

.. code-block:: python

    api.delete_bot(executor, bot.bot_id)
    print("Bot deleted.")

This workflow covers the main bot management operations. You can expand it to include order management, position tracking, and more. 