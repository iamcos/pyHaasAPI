Lab Management Examples
======================

This page demonstrates how to manage labs using pyHaasAPI, including creating, updating, and deleting labs.

.. contents::
   :local:
   :depth: 2

Creating a Lab
--------------

To create a new lab, you need a script, an account, and a market. Here is a step-by-step example:

.. code-block:: python

    from pyHaasAPI import api
    from pyHaasAPI.model import CreateLabRequest
    from config import settings
    import time

    # Authenticate
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # Get the first available script, account, and market
    scripts = api.get_all_scripts(executor)
    accounts = api.get_accounts(executor)
    markets = api.get_all_markets(executor)
    script_id = scripts[0].script_id
    account_id = accounts[0].account_id
    market = markets[0]

    # Create the lab
    req = CreateLabRequest.with_generated_name(
        script_id=script_id,
        account_id=account_id,
        market=market,
        exchange_code=market.price_source,
        interval=1,
        default_price_data_style="CandleStick"
    )
    lab = api.create_lab(executor, req)
    print(f"Lab created: {lab.lab_id}")

Updating Lab Details
--------------------

You can update lab details, such as the market or account:

.. code-block:: python

    # Fetch lab details
    lab_details = api.get_lab_details(executor, lab.lab_id)
    # Change the market to another available market
    new_market = markets[1]
    lab_details.settings.market_tag = new_market.format_market_tag(new_market.price_source)
    updated_lab = api.update_lab_details(executor, lab_details)
    print(f"Lab updated: {updated_lab.lab_id}")

Deleting a Lab
--------------

To delete a lab:

.. code-block:: python

    api.delete_lab(executor, updated_lab.lab_id)
    print("Lab deleted.")

Full Workflow
-------------

This workflow demonstrates creating, updating, and deleting a lab. You can expand it to include parameter updates, backtesting, and more. 

Updating Lab Configuration for Mad Hatter Bot
--------------------------------------------

This section demonstrates how to find a lab using the Mad Hatter bot, update its parameters (such as 'StopLoss' and 'TakeProfit'), and save the changes.

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

    # Find a lab using the Mad Hatter bot
    labs = api.get_all_labs(executor)
    mad_hatter_labs = [lab for lab in labs if "MadHatter" in lab.name or "Mad Hatter" in lab.name]
    if not mad_hatter_labs:
        print("No Mad Hatter labs found!")
    else:
        lab = mad_hatter_labs[0]
        print(f"Found Mad Hatter lab: {lab.name} (ID: {lab.lab_id})")

        # Fetch lab details
        lab_details = api.get_lab_details(executor, lab.lab_id)

        # Update parameters (e.g., set StopLoss to 2.0 and TakeProfit to 3.0)
        for param in lab_details.parameters:
            if param.get("K") == "StopLoss":
                param["O"] = ["2.0"]
            if param.get("K") == "TakeProfit":
                param["O"] = ["3.0"]
        updated_lab = api.update_lab_details(executor, lab_details)
        print("Updated Mad Hatter lab parameters.")

You can expand this workflow to update any parameter supported by the Mad Hatter bot, or to automate parameter sweeps for optimization. 