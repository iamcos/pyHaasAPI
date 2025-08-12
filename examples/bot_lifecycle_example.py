#!/usr/bin/env python3
"""
Bot Lifecycle Example
---------------------
Demonstrates the full lifecycle of a bot:
- Create bot
- Activate bot
- Monitor bot
- Pause bot
- Resume bot
- Deactivate bot
- Delete bot

Run with: python -m examples.bot_lifecycle_example
"""
from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import CreateBotRequest, CloudMarket
import time

def main():
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # Fetch a real CloudMarket from the API
    markets = api.get_all_markets(executor)
    market = next((m for m in markets if m.price_source == "BINANCE" and m.primary == "BTC" and m.secondary == "USDT"), markets[0])
    market_tag = market.format_market_tag(market.price_source)  # Use market tag string, not CloudMarket object

    # Auto-select the first available script and account if placeholders are present
    script_id = "your_script_id"
    account_id = "your_account_id"
    scripts = api.get_all_scripts(executor)
    accounts = api.get_accounts(executor)
    if script_id == "your_script_id":
        if not scripts:
            print("No scripts found. Please create a script in the UI first.")
            return
        script_id = scripts[0].script_id
        print(f"Auto-selected script_id: {script_id}")
    if account_id == "your_account_id":
        if not accounts:
            print("No accounts found. Please create an account in the UI first.")
            return
        account_id = accounts[0].account_id
        print(f"Auto-selected account_id: {account_id}")
    script_obj = api.get_script_item(executor, script_id)
    req = CreateBotRequest(
        bot_name="ExampleBot",
        script=script_obj,
        account_id=account_id,
        market=market_tag  # Pass market tag string
    )
    bot = api.add_bot(executor, req)
    print(f"Bot created: {bot.bot_id}")

    # 2. Activate bot
    bot = api.activate_bot(executor, bot.bot_id, cleanreports=False)
    print(f"Bot activated: {bot.bot_id}")

    # 3. Monitor bot (print status)
    for _ in range(5):
        bot_info = api.get_bot(executor, bot.bot_id)
        print(f"Bot is_activated: {bot_info.is_activated}, is_paused: {bot_info.is_paused}")
        time.sleep(5)

    # 4. Pause bot
    bot = api.pause_bot(executor, bot.bot_id)
    print(f"Bot paused: {bot.bot_id}")
    time.sleep(2)

    # 5. Resume bot
    bot = api.resume_bot(executor, bot.bot_id)
    print(f"Bot resumed: {bot.bot_id}")
    time.sleep(2)

    # 6. Deactivate bot
    bot = api.deactivate_bot(executor, bot.bot_id, cancelorders=False)
    print(f"Bot deactivated: {bot.bot_id}")
    time.sleep(2)

    # 7. Delete bot
    api.delete_bot(executor, bot.bot_id)
    print("Bot deleted.")

if __name__ == "__main__":
    main() 