Quick Start Guide
================

This guide will help you get started with pyHaasAPI quickly.

Prerequisites
------------

* pyHaasAPI installed (see :doc:`installation`)
* HaasOnline Bot Software running
* API access credentials

Basic Setup
----------

First, import the library and set up authentication:

.. code-block:: python

   from pyHaasAPI import api

   # Initialize the executor
   executor = api.RequestsExecutor(
       host="your-haasonline-server.com",  # Your HaasOnline server
       port=8090,                          # Default API port
       state=api.Guest()                   # Start as guest
   )

   # Authenticate with your credentials
   executor = executor.authenticate(
       email="your-email@example.com",
       password="your-password"
   )

Getting Market Data
------------------

Retrieve available markets:

.. code-block:: python

   # Get all markets (may be slow)
   markets = api.get_all_markets(executor)
   print(f"Found {len(markets)} markets")

   # Get markets for specific exchange (faster)
   from pyHaasAPI.price import PriceAPI
   price_api = PriceAPI(executor)
   
   binance_markets = price_api.get_trade_markets("BINANCE")
   print(f"Found {len(binance_markets)} Binance markets")

Getting Account Information
--------------------------

Access your trading accounts:

.. code-block:: python

   # Get all accounts
   accounts = api.get_accounts(executor)
   
   for account in accounts:
       print(f"Account: {account.name}")
       print(f"Balance: {account.balance}")
       print(f"Currency: {account.currency}")

Lab Management
--------------

Create and manage backtesting labs:

.. code-block:: python

   from pyHaasAPI.models.common import CreateLabRequest

   # Create a new lab
   lab_request = CreateLabRequest(
       name="My Test Lab",
       description="Testing strategy",
       # Add other parameters as needed
   )
   
   lab = api.create_lab(executor, lab_request)
   print(f"Created lab: {lab.lab_id}")

Bot Management
--------------

Create and control trading bots:

.. code-block:: python

   # Create a bot from lab results
   from pyHaasAPI.models.common import AddBotFromLabRequest
   
   bot_request = AddBotFromLabRequest(
       lab_id=lab.lab_id,
       name="My Trading Bot",
       # Add other parameters
   )
   
   bot = api.add_bot_from_lab(executor, bot_request)
   print(f"Created bot: {bot.bot_id}")

   # Control the bot
   api.activate_bot(executor, bot.bot_id)  # Start trading
   api.pause_bot(executor, bot.bot_id)     # Pause trading
   api.resume_bot(executor, bot.bot_id)    # Resume trading
   api.deactivate_bot(executor, bot.bot_id) # Stop trading

Error Handling
--------------

pyHaasAPI provides comprehensive error handling:

.. code-block:: python

   try:
       markets = api.get_all_markets(executor)
   except api.HaasAPIException as e:
       print(f"API Error: {e}")
   except Exception as e:
       print(f"Unexpected error: {e}")

Complete Example
---------------

Here's a complete example that demonstrates the basic workflow:

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

       # Get market data
       price_api = PriceAPI(executor)
       markets = price_api.get_trade_markets("BINANCE")
       print(f"Available markets: {len(markets)}")

       # Get account info
       accounts = api.get_accounts(executor)
       for account in accounts:
           print(f"Account: {account.name} - Balance: {account.balance}")

       # Create a simple lab
       from pyHaasAPI.models.common import CreateLabRequest
       lab_request = CreateLabRequest(
           name="Quick Test Lab",
           description="Quick start example"
       )
       
       lab = api.create_lab(executor, lab_request)
       print(f"Created lab: {lab.lab_id}")

   if __name__ == "__main__":
       main()

Next Steps
----------

* Read the :doc:`api_reference` for detailed API documentation
* Check out :doc:`examples` for more complex examples
* Learn about :doc:`advanced_usage` for advanced features 