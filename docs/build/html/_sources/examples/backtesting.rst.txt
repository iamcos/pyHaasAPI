Backtesting Examples
===================

This page demonstrates how to run a backtest using pyHaasAPI, monitor its status, and retrieve results.

.. contents::
   :local:
   :depth: 2

Starting a Backtest
-------------------

.. code-block:: python

    from pyHaasAPI import api
    from pyHaasAPI.model import StartLabExecutionRequest, GetBacktestResultRequest
    from config import settings
    import time

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
    start_unix = int(time.time()) - 86400 * 30  # 30 days ago
    end_unix = int(time.time())
    request = StartLabExecutionRequest(
        lab_id=lab_id,
        start_unix=start_unix,
        end_unix=end_unix,
        send_email=False
    )
    result = api.start_lab_execution(executor, request)
    print(f"Backtest started. Status: {result.status}")

Monitoring Backtest Status
-------------------------

.. code-block:: python

    for _ in range(20):
        status = api.get_lab_execution_update(executor, lab_id)
        print(f"Current status: {status.execution_status}")
        if status.execution_status == "COMPLETED":
            break
        time.sleep(5)

Retrieving Backtest Results
--------------------------

.. code-block:: python

    results = api.get_backtest_result(
        executor,
        GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=100
        )
    )
    print(f"Backtest results: {results.items}")

This workflow covers the main steps for running and retrieving a backtest. You can expand it to analyze results, optimize parameters, and more. 