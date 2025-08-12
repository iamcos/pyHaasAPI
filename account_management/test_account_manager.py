#!/usr/bin/env python3
"""
Account Management System Test

This module tests the account management functionality independently.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, patch
from account_manager import (
    AccountManager, AccountNamingManager, AccountInfo, AccountCreationRequest,
    AccountType, AccountStatus, AccountVerificationResult
)

class MockConfigManager:
    """Mock configuration manager for testing"""
    
    def get_account_settings(self):
        return Mock(
            test_account_names=["для тестов 10к"],
            initial_balance=10000.0
        )

class TestAccountNamingManager(unittest.TestCase):
    """Test cases for AccountNamingManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.config_manager = MockConfigManager()
        self.naming_manager = AccountNamingManager(self.config_manager)
    
    def test_account_name_generation(self):
        """Test account name generation"""
        # Test production account naming
        name = self.naming_manager.generate_account_name(AccountType.PRODUCTION, 1, 10000.0)
        self.assertEqual(name, "4AA-10k")
        
        name = self.naming_manager.generate_account_name(AccountType.PRODUCTION, 2, 10000.0)
        self.assertEqual(name, "4AB-10k")
        
        name = self.naming_manager.generate_account_name(AccountType.PRODUCTION, 27, 10000.0)
        self.assertEqual(name, "4BA-10k")  # 27th sequence
        
        # Test test account naming
        name = self.naming_manager.generate_account_name(AccountType.TEST, 1, 10000.0)
        self.assertEqual(name, "для тестов 10к")
        
        # Test development account naming
        name = self.naming_manager.generate_account_name(AccountType.DEVELOPMENT, 5, 15000.0)
        self.assertEqual(name, "dev-5-15k")
        
        # Test simulation account naming
        name = self.naming_manager.generate_account_name(AccountType.SIMULATION, 3, 5000.0)
        self.assertEqual(name, "sim-3-5k")
    
    def test_account_name_parsing(self):
        """Test account name parsing"""
        # Test production account parsing
        parsed = self.naming_manager.parse_account_name("4AA-10k")
        self.assertEqual(parsed['type'], AccountType.PRODUCTION)
        self.assertEqual(parsed['balance'], 10000.0)
        
        # Test test account parsing
        parsed = self.naming_manager.parse_account_name("для тестов 10к")
        self.assertEqual(parsed['type'], AccountType.TEST)
        self.assertEqual(parsed['balance'], 10000.0)
        
        # Test development account parsing
        parsed = self.naming_manager.parse_account_name("dev-5-15k")
        self.assertEqual(parsed['type'], AccountType.DEVELOPMENT)
        self.assertEqual(parsed['sequence'], 5)
        self.assertEqual(parsed['balance'], 15000.0)
        
        # Test simulation account parsing
        parsed = self.naming_manager.parse_account_name("sim-3-5k")
        self.assertEqual(parsed['type'], AccountType.SIMULATION)
        self.assertEqual(parsed['sequence'], 3)
        self.assertEqual(parsed['balance'], 5000.0)
    
    def test_letter_number_conversion(self):
        """Test letter to number conversion"""
        # Test number to letters
        self.assertEqual(self.naming_manager._number_to_letters(1), "AA")
        self.assertEqual(self.naming_manager._number_to_letters(2), "AB")
        self.assertEqual(self.naming_manager._number_to_letters(26), "AZ")
        self.assertEqual(self.naming_manager._number_to_letters(27), "BA")
        
        # Test letters to number
        self.assertEqual(self.naming_manager._letters_to_number("AA"), 1)
        self.assertEqual(self.naming_manager._letters_to_number("AB"), 2)
        self.assertEqual(self.naming_manager._letters_to_number("AZ"), 26)
        self.assertEqual(self.naming_manager._letters_to_number("BA"), 27)

class TestAccountManager(unittest.TestCase):
    """Test cases for AccountManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_server_manager = Mock()
        self.mock_config_manager = MockConfigManager()
        self.account_manager = AccountManager(self.mock_server_manager, self.mock_config_manager)
    
    def test_account_creation_request(self):
        """Test account creation request"""
        request = AccountCreationRequest(
            account_name="test-account",
            server_id="srv01",
            account_type=AccountType.TEST,
            initial_balance=10000.0,
            currency="USDT"
        )
        
        self.assertEqual(request.account_name, "test-account")
        self.assertEqual(request.server_id, "srv01")
        self.assertEqual(request.account_type, AccountType.TEST)
        self.assertEqual(request.initial_balance, 10000.0)
        self.assertEqual(request.currency, "USDT")
    
    def test_account_info_creation(self):
        """Test account info object creation"""
        account_info = AccountInfo(
            account_id="test-id",
            account_name="test-account",
            server_id="srv01",
            account_type=AccountType.TEST,
            balance=10000.0,
            currency="USDT",
            status=AccountStatus.ACTIVE
        )
        
        self.assertEqual(account_info.account_id, "test-id")
        self.assertEqual(account_info.account_name, "test-account")
        self.assertEqual(account_info.server_id, "srv01")
        self.assertEqual(account_info.account_type, AccountType.TEST)
        self.assertEqual(account_info.balance, 10000.0)
        self.assertEqual(account_info.currency, "USDT")
        self.assertEqual(account_info.status, AccountStatus.ACTIVE)
    
    def test_account_verification_result(self):
        """Test account verification result"""
        result = AccountVerificationResult(
            account_id="test-id",
            is_valid=True,
            balance=10000.0,
            currency="USDT",
            status=AccountStatus.ACTIVE,
            issues=[],
            verification_time=1234567890.0
        )
        
        self.assertEqual(result.account_id, "test-id")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.balance, 10000.0)
        self.assertEqual(result.currency, "USDT")
        self.assertEqual(result.status, AccountStatus.ACTIVE)
        self.assertEqual(len(result.issues), 0)
    
    def test_account_type_determination(self):
        """Test account type determination from names"""
        # Test various account names
        test_cases = [
            ("4AA-10k", AccountType.PRODUCTION),
            ("для тестов 10к", AccountType.TEST),
            ("dev-5-15k", AccountType.DEVELOPMENT),
            ("sim-3-5k", AccountType.SIMULATION),
            ("unknown-format", AccountType.PRODUCTION)  # Default
        ]
        
        for account_name, expected_type in test_cases:
            determined_type = self.account_manager._determine_account_type(account_name)
            self.assertEqual(determined_type, expected_type, f"Failed for {account_name}")
    
    @patch('account_manager.time.time')
    def test_cache_functionality(self, mock_time):
        """Test account caching functionality"""
        mock_time.return_value = 1000.0
        
        # Test cache validity
        self.assertFalse(self.account_manager._is_cache_valid("srv01"))
        
        # Add to cache
        account_info = AccountInfo(
            account_id="test-id",
            account_name="test-account",
            server_id="srv01",
            account_type=AccountType.TEST,
            balance=10000.0,
            currency="USDT",
            status=AccountStatus.ACTIVE
        )
        
        self.account_manager._update_account_cache("srv01", account_info)
        
        # Cache should now be valid
        self.assertTrue(self.account_manager._is_cache_valid("srv01"))
        
        # Test cache expiry
        mock_time.return_value = 1400.0  # 400 seconds later (beyond cache duration)
        self.assertFalse(self.account_manager._is_cache_valid("srv01"))
    
    def test_account_assignment(self):
        """Test account assignment to labs"""
        # Mock get_all_accounts to return test accounts
        test_accounts = [
            AccountInfo("test-1", "для тестов 10к", "srv01", AccountType.TEST, 10000.0, "USDT", AccountStatus.ACTIVE),
            AccountInfo("prod-1", "4AA-10k", "srv01", AccountType.PRODUCTION, 10000.0, "USDT", AccountStatus.ACTIVE)
        ]
        
        self.account_manager.get_all_accounts = Mock(return_value=test_accounts)
        
        # Test assigning test account
        assigned_id = self.account_manager.assign_account_to_lab("lab-1", "srv01", AccountType.TEST)
        self.assertEqual(assigned_id, "test-1")
        
        # Test assigning production account
        assigned_id = self.account_manager.assign_account_to_lab("lab-2", "srv01", AccountType.PRODUCTION)
        self.assertEqual(assigned_id, "prod-1")
        
        # Test no suitable accounts
        assigned_id = self.account_manager.assign_account_to_lab("lab-3", "srv01", AccountType.DEVELOPMENT)
        self.assertIsNone(assigned_id)

def run_account_tests():
    """Run all account management tests"""
    print("Running Account Management System Tests...")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestAccountNamingManager))
    test_suite.addTest(unittest.makeSuite(TestAccountManager))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success

def demo_account_management():
    """Demonstrate account management functionality"""
    print("\nAccount Management System Demo")
    print("=" * 40)
    
    # Initialize components
    config_manager = MockConfigManager()
    naming_manager = AccountNamingManager(config_manager)
    
    # Demo naming functionality
    print("1. Account Naming Demo:")
    test_cases = [
        (AccountType.PRODUCTION, 1),
        (AccountType.PRODUCTION, 2),
        (AccountType.PRODUCTION, 27),
        (AccountType.TEST, 1),
        (AccountType.DEVELOPMENT, 5),
        (AccountType.SIMULATION, 3)
    ]
    
    for acc_type, seq in test_cases:
        name = naming_manager.generate_account_name(acc_type, seq, 10000.0)
        parsed = naming_manager.parse_account_name(name)
        print(f"  {acc_type.value} #{seq}: {name} -> {parsed}")
    
    # Demo account creation request
    print("\n2. Account Creation Demo:")
    request = AccountCreationRequest(
        account_name="demo-account",
        server_id="srv01",
        account_type=AccountType.TEST,
        initial_balance=10000.0
    )
    print(f"  Created request: {request}")
    
    # Demo verification result
    print("\n3. Account Verification Demo:")
    verification = AccountVerificationResult(
        account_id="demo-id",
        is_valid=True,
        balance=10000.0,
        currency="USDT",
        status=AccountStatus.ACTIVE,
        issues=[],
        verification_time=1234567890.0
    )
    print(f"  Verification result: valid={verification.is_valid}, balance={verification.balance}")
    
    print("\n" + "=" * 40)
    print("Account management demo completed!")

if __name__ == "__main__":
    # Run tests
    success = run_account_tests()
    
    # Run demo
    demo_account_management()
    
    # Exit with appropriate code
    exit(0 if success else 1)