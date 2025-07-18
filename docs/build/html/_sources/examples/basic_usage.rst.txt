Basic Usage Examples
===================

This page demonstrates basic usage patterns with pyHaasAPI.

Authentication
--------------

.. code-block:: python

   from pyHaasAPI import api

   # Initialize the executor
   executor = api.RequestsExecutor(
       host="your-haasonline-server.com",
       port=8090,
       state=api.Guest()
   )

   # Authenticate
   executor = executor.authenticate(
       email="your-email@example.com",
       password="your-password"
   )

Getting Market Data
------------------

.. code-block:: python

   # Get all markets (slow but comprehensive)
   markets = api.get_all_markets(executor)
   print(f"Total markets: {len(markets)}")

   # Get markets for specific exchange (faster)
   from pyHaasAPI.price import PriceAPI
   price_api = PriceAPI(executor)
   
   exchanges = ["BINANCE", "KRAKEN"]
   for exchange in exchanges:
       try:
           exchange_markets = price_api.get_trade_markets(exchange)
           print(f"{exchange}: {len(exchange_markets)} markets")
       except Exception as e:
           print(f"Failed to get {exchange} markets: {e}")

Account Management
-----------------

.. code-block:: python

   # Get all accounts
   accounts = api.get_accounts(executor)
   
   for account in accounts:
       print(f"Account: {account.name}")
       print(f"  Balance: {account.balance}")
       print(f"  Currency: {account.currency}")
       print(f"  Status: {account.status}")

   # Get specific account details
   if accounts:
       account = accounts[0]
       balance = api.get_account_balance(executor, account.account_id)
       orders = api.get_account_orders(executor, account.account_id)
       positions = api.get_account_positions(executor, account.account_id)
       
       print(f"Balance: {balance}")
       print(f"Active orders: {len(orders)}")
       print(f"Open positions: {len(positions)}")

Lab Management
--------------

.. code-block:: python

   from pyHaasAPI.models.common import CreateLabRequest

   # Create a new lab
   lab_request = CreateLabRequest(
       name="My Test Lab",
       description="Testing strategy parameters",
       market="BINANCE_BTC_USDT",
       strategy="Scalper",
       # Add other parameters as needed
   )
   
   lab = api.create_lab(executor, lab_request)
   print(f"Created lab: {lab.lab_id}")

   # Get lab details
   lab_details = api.get_lab(executor, lab.lab_id)
   print(f"Lab status: {lab_details.status}")

   # Start lab execution
   from pyHaasAPI.models.common import StartLabExecutionRequest
   execution_request = StartLabExecutionRequest(
       lab_id=lab.lab_id
   )
   
   execution = api.start_lab_execution(executor, execution_request)
   print(f"Started execution: {execution.execution_id}")

Bot Management
--------------

.. code-block:: python

   # Create a bot from lab results
   from pyHaasAPI.models.common import AddBotFromLabRequest
   
   bot_request = AddBotFromLabRequest(
       lab_id=lab.lab_id,
       name="My Trading Bot",
       account_id=accounts[0].account_id,
       # Add other parameters
   )
   
   bot = api.add_bot_from_lab(executor, bot_request)
   print(f"Created bot: {bot.bot_id}")

   # Control the bot
   api.activate_bot(executor, bot.bot_id)  # Start trading
   
   # Check bot status
   bot_status = api.get_bot(executor, bot.bot_id)
   print(f"Bot status: {bot_status.status}")
   
   # Get bot orders and positions
   orders = api.get_bot_orders(executor, bot.bot_id)
   positions = api.get_bot_positions(executor, bot.bot_id)
   
   print(f"Bot orders: {len(orders)}")
   print(f"Bot positions: {len(positions)}")

   # Pause and resume
   api.pause_bot(executor, bot.bot_id)
   api.resume_bot(executor, bot.bot_id)
   
   # Stop the bot
   api.deactivate_bot(executor, bot.bot_id)

Error Handling
--------------

.. code-block:: python

   try:
       markets = api.get_all_markets(executor)
   except api.HaasAPIException as e:
       print(f"API Error: {e}")
       print(f"Error code: {e.code}")
       print(f"Error message: {e.message}")
   except Exception as e:
       print(f"Unexpected error: {e}")

Complete Working Example
-----------------------

Here's a complete example that you can run:

.. code-block:: python

   from pyHaasAPI import api
   from pyHaasAPI.price import PriceAPI

   def main():
       # Setup
       executor = api.RequestsExecutor(
           host="your-server.com",
           port=8090,
           state=api.Guest()
       ).authenticate(
           email="your-email@example.com",
           password="your-password"
       )

       try:
           # Get market data
           price_api = PriceAPI(executor)
           markets = price_api.get_trade_markets("BINANCE")
           print(f"Available Binance markets: {len(markets)}")

           # Get account info
           accounts = api.get_accounts(executor)
           if accounts:
               account = accounts[0]
               print(f"Using account: {account.name}")
               
               # Get account details
               balance = api.get_account_balance(executor, account.account_id)
               print(f"Account balance: {balance}")

           # Create a simple lab
           from pyHaasAPI.models.common import CreateLabRequest
           lab_request = CreateLabRequest(
               name="Basic Example Lab",
               description="Created from basic usage example",
               market="BINANCE_BTC_USDT"
           )
           
           lab = api.create_lab(executor, lab_request)
           print(f"Created lab: {lab.lab_id}")

       except api.HaasAPIException as e:
           print(f"API Error: {e}")
       except Exception as e:
           print(f"Unexpected error: {e}")

   if __name__ == "__main__":
       main() 