pyHaasAPI Documentation
=======================

A Python library for interacting with the HaasOnline API, providing a robust and efficient way to manage labs, bots, scripts, and other resources within the HaasOnline ecosystem.

.. image:: https://img.shields.io/pypi/v/pyHaasAPI.svg
   :target: https://pypi.org/project/pyHaasAPI/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/pyHaasAPI.svg
   :target: https://pypi.org/project/pyHaasAPI/
   :alt: Python versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT License

Quick Start
----------

Install the package:

.. code-block:: bash

   pip install pyHaasAPI

Basic usage:

.. code-block:: python

   from pyHaasAPI import api

   # Initialize and authenticate
   executor = api.RequestsExecutor(
       host="your-haasonline-server.com",
       port=8090,
       state=api.Guest()
   ).authenticate(email="your-email", password="your-password")

   # Get all markets
   markets = api.get_all_markets(executor)

   # Get account information
   accounts = api.get_accounts(executor)

Key Features
-----------

* **Simplified API Interaction**: Abstracts away the complexities of the HaasOnline API
* **Robust Error Handling**: Comprehensive error handling with custom exceptions
* **Type Safety**: Leveraging Pydantic models for type safety
* **Efficient Resource Management**: Methods for managing labs, bots, and other resources
* **Comprehensive Trading Operations**: Full support for bot control and order management
* **Complete Account Management**: Monitor balances, positions, orders, and trade history
* **Advanced Lab Management**: Create, configure, and execute backtests with parameter optimization

Documentation Contents
---------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api_reference
   examples
   advanced_usage
   licensing
   contributing

API Reference
------------

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules/pyHaasAPI
   modules/pyHaasAPI.api
   modules/pyHaasAPI.client
   modules/pyHaasAPI.models
   modules/pyHaasAPI.lab
   modules/pyHaasAPI.market_manager

Examples
--------

.. toctree::
   :maxdepth: 2
   :caption: Examples:

   examples/basic_usage
   examples/lab_management
   examples/bot_management
   examples/market_data
   examples/backtesting

Advanced Topics
--------------

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics:

   advanced/authentication
   advanced/error_handling
   advanced/parameter_optimization
   advanced/performance_tips

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
-------

This project is licensed under the MIT License - see the :doc:`licensing` page for details.

Free for individual traders and research institutions. Commercial licensing available for hedge funds and financial institutions.

