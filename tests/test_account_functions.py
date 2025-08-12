#!/usr/bin/env python3
"""
Integration tests for account management functions using pyHaasAPI.

Tests include:
- Getting account balance
- Renaming an account (and reverting the change)
- Depositing funds (parameters may need to be mocked for real tests)

Requires at least one account to exist for the test user (see README).
"""
import pytest
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
from pyHaasAPI import api

@pytest.fixture(scope="module")
def executor():
    """Authenticated API executor using credentials from .env."""
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    return executor

@pytest.fixture(scope="module")
def ensure_test_account(executor):
    """Ensures at least one test account exists, or creates a simulated account if none exist."""
    accounts = api.get_accounts(executor)
    if not accounts:
        # Create a simulated account for testing
        api.add_simulated_account(
            executor,
            name="pytest_sim",
            driver_code="BINANCEQUARTERLY",
            driver_type=2
        )
        accounts = api.get_accounts(executor)
    assert accounts, "No accounts available for testing. Please check API permissions."
    return accounts

@pytest.fixture(scope="module")
def accounts(executor, ensure_test_account):
    """Returns the list of available accounts for the test user."""
    return ensure_test_account

@pytest.fixture(scope="module")
def account_id(accounts):
    """Returns the account_id of the first available account."""
    return accounts[0].account_id

@pytest.fixture(scope="module")
def original_name(accounts):
    """Returns the original name of the first available account."""
    return accounts[0].name

def test_get_balance(executor, account_id):
    """Test that account balance can be retrieved for the test account."""
    balance = api.get_account_balance(executor, account_id)
    assert balance is not None, "Failed to get balance!"

def test_rename_account(executor, account_id, original_name):
    """Test renaming the account and reverting to the original name."""
    test_name = f"{original_name}_TEST"
    result = api.rename_account(executor, account_id, test_name)
    assert result, "Account rename failed!"
    # Rename back to original
    result = api.rename_account(executor, account_id, original_name)
    assert result, "Failed to rename account back to original!"

def test_deposit_funds(executor, account_id):
    """Test depositing funds to the test account (parameters may need to be mocked)."""
    # These values may need to be parameterized or mocked for a real test
    currency = "USDC"
    wallet_id = "USDC"
    amount = 100.0
    result = api.deposit_funds(executor, account_id, currency, wallet_id, amount)
    assert result, "Fund deposit failed!" 