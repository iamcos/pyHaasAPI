Contributing
============

We welcome contributions to pyHaasAPI! This guide will help you get started.

Getting Started
--------------

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a virtual environment** and install dependencies
4. **Make your changes**
5. **Test your changes**
6. **Submit a pull request**

Development Setup
----------------

.. code-block:: bash

   # Clone your fork
   git clone https://github.com/YOUR_USERNAME/pyHaasAPI.git
   cd pyHaasAPI

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install development dependencies
   pip install -e ".[test]"
   pip install sphinx sphinx-rtd-theme myst-parser

   # Install pre-commit hooks
   pip install pre-commit
   pre-commit install

Code Style
----------

We follow PEP 8 style guidelines:

* Use 4 spaces for indentation
* Maximum line length of 88 characters (Black formatter)
* Use type hints for all function parameters and return values
* Follow Google-style docstrings

We use several tools to maintain code quality:

* **Black**: Code formatting
* **isort**: Import sorting
* **flake8**: Linting
* **mypy**: Type checking
* **pytest**: Testing

Running Tests
------------

.. code-block:: bash

   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=pyHaasAPI

   # Run specific test file
   pytest tests/test_api.py

   # Run with verbose output
   pytest -v

Building Documentation
---------------------

.. code-block:: bash

   # Build HTML documentation
   cd docs
   make html

   # View documentation
   open build/html/index.html

   # Auto-generate API docs
   sphinx-apidoc -o source/modules pyHaasAPI --separate --module-first

Pull Request Guidelines
----------------------

1. **Create a feature branch** from `main`
2. **Write tests** for new functionality
3. **Update documentation** if needed
4. **Ensure all tests pass**
5. **Update CHANGELOG.md** with your changes
6. **Write a clear description** of your changes

Example Pull Request
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Title: Add support for new API endpoint

   Description:
   This PR adds support for the new /api/v1/markets endpoint that was
   introduced in HaasOnline v2.1.0.

   Changes:
   - Added new MarketDataAPI class
   - Added tests for market data functionality
   - Updated documentation with examples
   - Added type hints for all new functions

   Tests:
   - [x] All existing tests pass
   - [x] New tests added for MarketDataAPI
   - [x] Documentation builds successfully

   Closes #123

Issue Guidelines
---------------

When reporting issues, please include:

* **Python version** and operating system
* **pyHaasAPI version**
* **HaasOnline version**
* **Complete error message** and traceback
* **Steps to reproduce** the issue
* **Expected vs actual behavior**

Example Issue
~~~~~~~~~~~~

.. code-block:: text

   Title: Authentication fails with specific error message

   Environment:
   - Python 3.11.0
   - pyHaasAPI 0.1.0
   - HaasOnline v2.1.0
   - macOS 14.0

   Steps to reproduce:
   1. Create RequestsExecutor with valid credentials
   2. Call authenticate() method
   3. Receive "Invalid credentials" error

   Expected: Successful authentication
   Actual: HaasAPIException with code 401

   Error message:
   ```
   pyHaasAPI.exceptions.HaasAPIException: Invalid credentials (401)
   ```

Development Workflow
-------------------

1. **Check existing issues** to avoid duplicates
2. **Create an issue** for significant changes
3. **Fork and clone** the repository
4. **Create a feature branch**
5. **Make your changes** with tests
6. **Run the test suite**
7. **Update documentation**
8. **Submit a pull request**

Code Review Process
------------------

1. **Automated checks** must pass (CI/CD)
2. **At least one maintainer** must approve
3. **All conversations resolved**
4. **Tests pass** on all supported Python versions
5. **Documentation updated** if needed

Release Process
--------------

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md**
3. **Create release notes**
4. **Tag the release**
5. **Publish to PyPI**

Contact
-------

* **GitHub Issues**: https://github.com/iamcos/pyHaasAPI/issues
* **Discussions**: https://github.com/iamcos/pyHaasAPI/discussions
* **Email**: contributors@pyhaasapi.com

Thank you for contributing to pyHaasAPI! 