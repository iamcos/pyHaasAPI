Error Handling Examples
======================

This page demonstrates robust error handling patterns for pyHaasAPI, including catching API errors, handling missing resources, and writing resilient workflows.

.. contents::
   :local:
   :depth: 2

Catching API Errors
-------------------

.. code-block:: python

    from pyHaasAPI import api
    from pyHaasAPI.exceptions import HaasApiError
    from config import settings

    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    try:
        labs = api.get_all_labs(executor)
        print(f"Found {len(labs)} labs.")
    except HaasApiError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

Handling Missing Resources
-------------------------

.. code-block:: python

    try:
        lab = api.get_lab_details(executor, "nonexistent_lab_id")
    except HaasApiError as e:
        print(f"Lab not found: {e}")

Retrying on Failure
-------------------

.. code-block:: python

    import time

    for attempt in range(3):
        try:
            labs = api.get_all_labs(executor)
            print("Success!")
            break
        except HaasApiError as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    else:
        print("All attempts failed.")

This workflow covers the basics of error handling. You can expand it to include logging, notifications, and more advanced recovery strategies. 