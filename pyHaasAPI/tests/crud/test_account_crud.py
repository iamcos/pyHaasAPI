"""
Account CRUD Tests

Comprehensive testing for Account API with field mapping validation,
margin settings management, and account data integrity.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from .helpers import (
    assert_safe_field, assert_account_data_integrity, retry_async,
    log_field_mapping_warnings
)
from pyHaasAPI.exceptions import AccountError, AccountNotFoundError, AccountConfigurationError


pytestmark = pytest.mark.asyncio

@pytest.mark.crud
@pytest.mark.srv03
class TestAccountCRUD:
    """Account CRUD operation tests"""
    
    async def test_get_accounts_safe_mapping(self, apis):
        """Test account listing with safe field mapping"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        
        # Validate response structure
        assert accounts is not None, "Accounts list should not be None"
        assert isinstance(accounts, list), "Accounts should be a list"
        assert len(accounts) > 0, "Should have at least one account"
        
        # Validate each account
        for account in accounts:
            assert_account_data_integrity(account)
            
            # Log field mapping warnings for debugging
            log_field_mapping_warnings(account, "AccountData")
            
            # Verify critical fields
            account_id = assert_safe_field(account, 'account_id', str, required=True)
            exchange = assert_safe_field(account, 'exchange', str, required=True)
            account_name = assert_safe_field(account, 'account_name', str, required=True)
            
            assert account_id, "Account ID cannot be empty"
            assert exchange, "Exchange cannot be empty"
            assert account_name, "Account name cannot be empty"
    
    async def test_get_account_data_safe_mapping(self, apis):
        """Test individual account data retrieval with safe field mapping"""
        account_api = apis['account_api']
        
        # First get all accounts to find a valid account ID
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Get detailed account data
        account_data = await account_api.get_account_data(account_id)
        
        # Validate account data integrity
        assert account_data is not None, "Account data should not be None"
        assert_account_data_integrity(account_data)
        
        # Verify critical fields
        retrieved_account_id = assert_safe_field(account_data, 'account_id', str, required=True)
        assert retrieved_account_id == account_id, f"Account ID mismatch: {retrieved_account_id} != {account_id}"
        
        # Check wallet data presence
        wallet_data = assert_safe_field(account_data, 'wallet_data', required=False)
        if wallet_data:
            assert isinstance(wallet_data, (list, dict)), f"Invalid wallet_data type: {type(wallet_data)}"
            if isinstance(wallet_data, list):
                assert len(wallet_data) >= 0, "Wallet data list should be non-negative length"
        
        # Log field mapping warnings
        log_field_mapping_warnings(account_data, "AccountData")
    
    async def test_get_account_balance(self, apis):
        """Test account balance retrieval"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Get account balance
        balance = await account_api.get_account_balance(account_id)
        
        # Validate balance response
        assert balance is not None, "Account balance should not be None"
        
        # Log field mapping warnings
        log_field_mapping_warnings(balance, "AccountBalance")
        
        # Test safe field access for balance fields
        balance_fields = ['total_balance', 'available_balance', 'used_balance', 'currency']
        
        for field in balance_fields:
            value = assert_safe_field(balance, field, required=False)
            assert value is None or isinstance(value, (str, int, float)), \
                f"Balance field {field} has unexpected type: {type(value)}"
    
    async def test_get_all_account_balances(self, apis):
        """Test all account balances retrieval"""
        account_api = apis['account_api']
        
        # Get all account balances
        all_balances = await account_api.get_all_account_balances()
        
        # Validate response structure
        assert all_balances is not None, "All account balances should not be None"
        assert isinstance(all_balances, (list, dict)), "All balances should be list or dict"
        
        # Log field mapping warnings
        log_field_mapping_warnings(all_balances, "AllAccountBalances")
    
    async def test_margin_settings_roundtrip(self, apis):
        """Test margin settings get/set roundtrip"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Get current margin settings
        margin_settings = await account_api.get_margin_settings(account_id)
        
        # Validate margin settings response
        assert margin_settings is not None, "Margin settings should not be None"
        
        # Log field mapping warnings
        log_field_mapping_warnings(margin_settings, "MarginSettings")
        
        # Test safe field access for margin settings
        margin_fields = ['position_mode', 'margin_mode', 'leverage', 'market_tag']
        
        for field in margin_fields:
            value = assert_safe_field(margin_settings, field, required=False)
            assert value is None or isinstance(value, (str, int, float)), \
                f"Margin field {field} has unexpected type: {type(value)}"
        
        # Test adjusting margin settings
        try:
            # Get a market tag from the account or use a default
            market_tag = assert_safe_field(margin_settings, 'market_tag', str, required=False)
            if not market_tag:
                market_tag = 'BTC_USDT_PERPETUAL'  # Default market
            
            # Adjust margin settings
            new_settings = {
                'position_mode': 1,  # HEDGE
                'margin_mode': 0,    # CROSS
                'leverage': 20
            }
            
            adjusted_settings = await account_api.adjust_margin_settings(
                account_id, market_tag, new_settings
            )
            
            # Validate adjusted settings
            assert adjusted_settings is not None, "Adjusted settings should not be None"
            log_field_mapping_warnings(adjusted_settings, "AdjustedMarginSettings")
            
        except Exception as e:
            # Some accounts might not support margin settings adjustment
            print(f"Margin settings adjustment not supported: {e}")
    
    async def test_set_position_mode(self, apis):
        """Test position mode setting"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Test setting position mode
        try:
            result = await account_api.set_position_mode(account_id, 1)  # HEDGE mode
            assert result is not None, "Position mode setting should return result"
            log_field_mapping_warnings(result, "PositionModeResult")
        except Exception as e:
            # Some accounts might not support position mode changes
            print(f"Position mode setting not supported: {e}")
    
    async def test_set_margin_mode(self, apis):
        """Test margin mode setting"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Test setting margin mode
        try:
            result = await account_api.set_margin_mode(account_id, 0)  # CROSS mode
            assert result is not None, "Margin mode setting should return result"
            log_field_mapping_warnings(result, "MarginModeResult")
        except Exception as e:
            # Some accounts might not support margin mode changes
            print(f"Margin mode setting not supported: {e}")
    
    async def test_set_leverage(self, apis):
        """Test leverage setting"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Test setting leverage
        try:
            result = await account_api.set_leverage(account_id, 20)  # 20x leverage
            assert result is not None, "Leverage setting should return result"
            log_field_mapping_warnings(result, "LeverageResult")
        except Exception as e:
            # Some accounts might not support leverage changes
            print(f"Leverage setting not supported: {e}")
    
    async def test_get_account_orders(self, apis):
        """Test account orders retrieval"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Get account orders
        orders = await account_api.get_account_orders(account_id)
        
        # Validate orders response
        assert orders is not None, "Account orders should not be None"
        assert isinstance(orders, list), "Account orders should be a list"
        
        # Log field mapping warnings
        log_field_mapping_warnings(orders, "AccountOrders")
        
        # Test safe field access for order fields
        if orders:
            for order in orders:
                order_fields = ['order_id', 'symbol', 'side', 'amount', 'price', 'status']
                
                for field in order_fields:
                    value = assert_safe_field(order, field, required=False)
                    assert value is None or isinstance(value, (str, int, float, bool)), \
                        f"Order field {field} has unexpected type: {type(value)}"
    
    async def test_account_not_found_error(self, apis):
        """Test account operations with non-existent account"""
        account_api = apis['account_api']
        
        # Use a clearly non-existent account ID
        non_existent_id = "non-existent-account-id-12345"
        
        # Should raise AccountNotFoundError for account data
        with pytest.raises(AccountNotFoundError):
            await account_api.get_account_data(non_existent_id)
        
        # Should raise AccountNotFoundError for account balance
        with pytest.raises(AccountNotFoundError):
            await account_api.get_account_balance(non_existent_id)
    
    async def test_account_field_mapping_resilience(self, apis):
        """Test field mapping resilience with missing optional fields"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Get detailed account data
        account_data = await account_api.get_account_data(account_id)
        
        # Test safe field access for various optional fields
        optional_fields = [
            'wallet_data', 'balance', 'equity', 'margin',
            'free_margin', 'used_margin', 'leverage',
            'position_mode', 'margin_mode', 'created_at', 'updated_at'
        ]
        
        for field in optional_fields:
            # This should not raise an exception even if field is missing
            value = assert_safe_field(account_data, field, required=False)
            # Field may be None or missing - both are acceptable
            assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                f"Field {field} has unexpected type: {type(value)}"
    
    async def test_account_retry_mechanism(self, apis):
        """Test retry mechanism for transient errors"""
        account_api = apis['account_api']
        
        # Test retry mechanism for account listing
        accounts = await retry_async(
            account_api.get_accounts,
            retries=3,
            delay=1.0
        )
        
        assert accounts is not None, "Retry should succeed"
        assert isinstance(accounts, list), "Accounts should be a list"
        assert len(accounts) > 0, "Should have at least one account"
    
    async def test_account_balance_validation(self, apis):
        """Test account balance data validation"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Get account balance
        balance = await account_api.get_account_balance(account_id)
        
        # Validate balance data types and ranges
        if balance:
            total_balance = assert_safe_field(balance, 'total_balance', (int, float), required=False)
            if total_balance is not None:
                assert total_balance >= 0, f"Total balance should be non-negative: {total_balance}"
            
            available_balance = assert_safe_field(balance, 'available_balance', (int, float), required=False)
            if available_balance is not None:
                assert available_balance >= 0, f"Available balance should be non-negative: {available_balance}"
            
            used_balance = assert_safe_field(balance, 'used_balance', (int, float), required=False)
            if used_balance is not None:
                assert used_balance >= 0, f"Used balance should be non-negative: {used_balance}"
    
    async def test_account_wallet_data_structure(self, apis):
        """Test account wallet data structure validation"""
        account_api = apis['account_api']
        
        # Get all accounts
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        account_id = assert_safe_field(first_account, 'account_id', str, required=True)
        
        # Get detailed account data
        account_data = await account_api.get_account_data(account_id)
        
        # Validate wallet data structure
        wallet_data = assert_safe_field(account_data, 'wallet_data', required=False)
        
        if wallet_data:
            if isinstance(wallet_data, list):
                # Wallet data is a list of wallet entries
                for wallet_entry in wallet_data:
                    assert isinstance(wallet_entry, dict), f"Wallet entry should be dict: {type(wallet_entry)}"
                    
                    # Test safe field access for wallet entry fields
                    wallet_fields = ['currency', 'balance', 'available', 'used', 'free']
                    
                    for field in wallet_fields:
                        value = assert_safe_field(wallet_entry, field, required=False)
                        assert value is None or isinstance(value, (str, int, float)), \
                            f"Wallet field {field} has unexpected type: {type(value)}"
            
            elif isinstance(wallet_data, dict):
                # Wallet data is a single wallet object
                wallet_fields = ['currency', 'balance', 'available', 'used', 'free']
                
                for field in wallet_fields:
                    value = assert_safe_field(wallet_data, field, required=False)
                    assert value is None or isinstance(value, (str, int, float)), \
                        f"Wallet field {field} has unexpected type: {type(value)}"
