Installation
===========

Requirements
-----------

* Python 3.11 or higher
* HaasOnline Bot Software (for API access)

Installation
-----------

Install pyHaasAPI using pip:

.. code-block:: bash

   pip install pyHaasAPI

Or install from source:

.. code-block:: bash

   git clone https://github.com/iamcos/pyHaasAPI.git
   cd pyHaasAPI
   pip install -e .

Dependencies
-----------

The following packages are automatically installed:

* `pydantic <https://pydantic.dev/>`_ >= 2.0.0 - Data validation using Python type annotations
* `requests <https://requests.readthedocs.io/>`_ >= 2.31.0 - HTTP library for Python
* `loguru <https://loguru.readthedocs.io/>`_ >= 0.7.0 - Python logging made simple
* `typing-extensions <https://pypi.org/project/typing-extensions/>`_ >= 4.7.0 - Backported and experimental type hints

Optional Dependencies
--------------------

For development and testing:

.. code-block:: bash

   pip install pyHaasAPI[test]

This installs:

* `pytest <https://pytest.org/>`_ >= 8.0.0 - Testing framework
* `pytest-cov <https://pytest-cov.readthedocs.io/>`_ >= 4.1.0 - Coverage plugin
* `pytest-mock <https://pytest-mock.readthedocs.io/>`_ >= 3.14.0 - Mocking plugin

Verification
-----------

To verify the installation, run:

.. code-block:: python

   import pyHaasAPI
   print("pyHaasAPI installed successfully!")

You should see no errors and the success message.

Upgrading
---------

To upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade pyHaasAPI

Uninstalling
-----------

To uninstall pyHaasAPI:

.. code-block:: bash

   pip uninstall pyHaasAPI 