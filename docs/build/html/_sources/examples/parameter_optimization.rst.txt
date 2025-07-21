Parameter Optimization Examples
==============================

This page demonstrates how to optimize parameters for a lab using pyHaasAPI, including setting parameter ranges and running optimizations.

.. contents::
   :local:
   :depth: 2

Setting Parameter Ranges
------------------------

.. code-block:: python

    from pyHaasAPI import api
    from config import settings
    import random

    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # Assume you have a lab_id
    lab_id = "your_lab_id"
    lab_details = api.get_lab_details(executor, lab_id)

    # Set a range for a parameter (e.g., StopLoss)
    for param in lab_details.parameters:
        if param.get("K") == "StopLoss":
            param["O"] = [str(x) for x in range(1, 11)]  # 1 to 10
    updated_lab = api.update_lab_details(executor, lab_details)
    print("Parameter range set.")

Running Parameter Optimization
-----------------------------

.. code-block:: python

    # Start backtests for each parameter value (simple grid search)
    for value in range(1, 11):
        for param in updated_lab.parameters:
            if param.get("K") == "StopLoss":
                param["O"] = [str(value)]
        api.update_lab_details(executor, updated_lab)
        # Start a backtest for this value (see backtesting example)
        # ...
        print(f"Started backtest for StopLoss={value}")

This workflow covers the basics of parameter optimization. You can expand it to use genetic algorithms, analyze results, and automate the search for optimal parameters. 