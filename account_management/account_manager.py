#!/usr/bin/env python3
"""
Account Management System

This module provides comprehensive account management functionality for the
distributed trading bot testing automation system, including account creation,
verification, and management across multiple servers.
"""

import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from infrastructure.server_manager import ServerManager
from infrastructure.error_handler import retry_on_error, RetryConfig, GracefulErrorHandler, ErrorCategory
from infrastructure.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class AccountType(Enum):
    """Account type classification"""
    PRODUCTION = "production"
    TEST = "test"
    SIMULATION = "simulation"
    DEVELOPMENT = "development"

class AccountStatus(Enum):
    """Account status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class AccountInfo:
    """Information about a trading account"""
    account_id: str
    account_name: str
    server_id: str
    account_type: AccountType
    balance: float
    currency: str
    status: AccountStatus
    created_time: Optional[float] = None
    last_verified: Optional[float] = None
    error_message: Optional[str] = None

@dataclass
class AccountCreationRequest:
    """Request for creating a new account"""
    account_name: str
    server_id: str
    account_type: AccountType
    initial_balance: float
    currency: str = "USDT"
    additional_config: Optional[Dict[str, Any]] = None

@dataclass
class AccountVerificationResult:
    """Result of account verification"""
    account_id: str
    is_valid: bool
    balance: float
    currency: str
    status: AccountStatus
    issues: List[str]
    verification_time: float

class AccountNamingManager:
    """Manages account naming schemas and generation"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.naming_patterns = self._initialize_naming_patterns()
    
    def _initialize_naming_patterns(self) -> Dict[str, str]:
        """Initialize naming patterns for different account types"""
        return {
            'standard': '4{sequence}-10k',
            'test': 'для тестов 10к',
            'development': 'dev-{sequence}-{balance}k',
            'simulation': 'sim-{sequence}-{balance}k'
        }
    
    def generate_account_name(
        self, 
        account_type: AccountType, 
        sequence_number: int, 
        balance: float = 10000.0
    ) -> str:
        """
        Generate account name based on type and sequence.
        
        Args:
            account_type: Type of account
            sequence_number: Sequence number for naming
            balance: Account balance for naming
            
        Returns:
            Generated account name
        """
        balance_k = int(balance / 1000)
        
        if account_type == AccountType.TEST:
            return self.naming_patterns['test']
        elif account_type == AccountType.DEVELOPMENT:
            return self.naming_patterns['development'].format(
                sequence=sequence_number, 
                balance=balance_k
            )
        elif account_type == AccountType.SIMULATION:
            return self.naming_patterns['simulation'].format(
                sequence=sequence_number, 
                balance=balance_k
            )
        else:  # PRODUCTION or default
            # Generate sequence letter combination (AA, AB, AC, etc.)
            sequence_letters = self._number_to_letters(sequence_number)
            return self.naming_patterns['standard'].format(sequence=sequence_letters)
    
    def _number_to_letters(self, number: int) -> str:
        """Convert number to letter sequence (1=AA, 2=AB, etc.)"""
        if number <= 0:
            return "AA"
        
        # Simple mapping for the expected range
        if number <= 26:
            return "A" + chr(64 + number)  # AA, AB, AC, ..., AZ
        else:
            # For numbers > 26, use a simple wrapping approach
            first_letter = chr(65 + ((number - 1) // 26))
            second_letter = chr(65 + ((number - 1) % 26))
            return first_letter + second_letter
    
    def parse_account_name(self, account_name: str) -> Dict[str, Any]:
        """
        Parse account name to extract information.
        
        Args:
            account_name: Account name to parse
            
        Returns:
            Dictionary with parsed information
        """
        # Test account pattern
        if account_name == self.naming_patterns['test']:
            return {
                'type': AccountType.TEST,
                'sequence': 0,
                'balance': 10000.0
            }
        
        # Standard pattern (4XX-10k)
        standard_match = re.match(r'4([A-Z]+)-(\d+)k', account_name)
        if standard_match:
            letters = standard_match.group(1)
            balance = int(standard_match.group(2)) * 1000
            sequence = self._letters_to_number(letters)
            return {
                'type': AccountType.PRODUCTION,
                'sequence': sequence,
                'balance': balance
            }
        
        # Development pattern
        dev_match = re.match(r'dev-(\d+)-(\d+)k', account_name)
        if dev_match:
            sequence = int(dev_match.group(1))
            balance = int(dev_match.group(2)) * 1000
            return {
                'type': AccountType.DEVELOPMENT,
                'sequence': sequence,
                'balance': balance
            }
        
        # Simulation pattern
        sim_match = re.match(r'sim-(\d+)-(\d+)k', account_name)
        if sim_match:
            sequence = int(sim_match.group(1))
            balance = int(sim_match.group(2)) * 1000
            return {
                'type': AccountType.SIMULATION,
                'sequence': sequence,
                'balance': balance
            }
        
        # Unknown pattern
        return {
            'type': AccountType.PRODUCTION,
            'sequence': 0,
            'balance': 0.0
        }
    
    def _letters_to_number(self, letters: str) -> int:
        """Convert letter sequence to number (AA=1, AB=2, etc.)"""
        if len(letters) == 2:
            first = ord(letters[0]) - 65
            second = ord(letters[1]) - 65
            return first * 26 + second + 1
        return 1
    
    def get_next_sequence_number(self, server_id: str, account_type: AccountType) -> int:
        """Get the next sequence number for account creation"""
        # This would typically query existing accounts to find the next available number
        # For now, return a placeholder
        return 1

class AccountManager:
    """Main account management system"""
    
    def __init__(self, server_manager: ServerManager, config_manager: ConfigManager):
        self.server_manager = server_manager
        self.config_manager = config_manager
        self.naming_manager = AccountNamingManager(config_manager)
        self.error_handler = GracefulErrorHandler()
        
        # Account cache
        self._account_cache: Dict[str, Dict[str, AccountInfo]] = {}  # server_id -> account_id -> AccountInfo
        self._cache_timestamp: Dict[str, float] = {}
        self.cache_duration = 300  # 5 minutes
        
        self._register_error_handlers()
    
    def _register_error_handlers(self):
        """Register error handlers for account operations"""
        def account_creation_fallback(error, context):
            return f"Account creation failed: {error}"
        
        def account_verification_fallback(error, context):
            return AccountVerificationResult(
                account_id=context.get('account_id', 'unknown'),
                is_valid=False,
                balance=0.0,
                currency='USDT',
                status=AccountStatus.ERROR,
                issues=[str(error)],
                verification_time=time.time()
            )
        
        self.error_handler.register_fallback_handler(ErrorCategory.API, account_creation_fallback)
        self.error_handler.register_fallback_handler(ErrorCategory.DATA_ERROR, account_verification_fallback)
    
    @retry_on_error(RetryConfig(max_attempts=3, base_delay=2.0))
    def create_account(self, request: AccountCreationRequest) -> Optional[AccountInfo]:
        """
        Create a new trading account.
        
        Args:
            request: Account creation request
            
        Returns:
            AccountInfo object if successful, None otherwise
        """
        logger.info(f"Creating account {request.account_name} on server {request.server_id}")
        
        try:
            # Get executor for the target server
            executor = self._get_server_executor(request.server_id)
            if not executor:
                logger.error(f"Failed to get executor for server {request.server_id}")
                return None
            
            # Create the account using HaasOnline API
            # Note: This is a placeholder - actual implementation would depend on HaasOnline API
            account_id = self._create_haas_account(executor, request)
            
            if account_id:
                # Create AccountInfo object
                account_info = AccountInfo(
                    account_id=account_id,
                    account_name=request.account_name,
                    server_id=request.server_id,
                    account_type=request.account_type,
                    balance=request.initial_balance,
                    currency=request.currency,
                    status=AccountStatus.ACTIVE,
                    created_time=time.time()
                )
                
                # Update cache
                self._update_account_cache(request.server_id, account_info)
                
                logger.info(f"Successfully created account {account_id}")
                return account_info
            else:
                logger.error(f"Failed to create account {request.account_name}")
                return None
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(
                e,
                {
                    'operation': 'create_account',
                    'server_id': request.server_id,
                    'account_name': request.account_name
                },
                None
            )
            logger.error(f"Account creation failed: {error_msg}")
            return None
    
    def create_test_accounts(self, server_id: str, count: int = 2) -> List[AccountInfo]:
        """
        Create test accounts on a server.
        
        Args:
            server_id: Target server ID
            count: Number of test accounts to create
            
        Returns:
            List of created account information
        """
        logger.info(f"Creating {count} test accounts on server {server_id}")
        
        created_accounts = []
        account_settings = self.config_manager.get_account_settings()
        
        for i in range(count):
            # Generate test account name
            if i == 0:
                account_name = account_settings.test_account_names[0]  # "для тестов 10к"
            else:
                account_name = f"{account_settings.test_account_names[0]} {i+1}"
            
            request = AccountCreationRequest(
                account_name=account_name,
                server_id=server_id,
                account_type=AccountType.TEST,
                initial_balance=account_settings.initial_balance,
                currency="USDT"
            )
            
            account_info = self.create_account(request)
            if account_info:
                created_accounts.append(account_info)
            
            # Brief pause between creations
            time.sleep(1.0)
        
        logger.info(f"Created {len(created_accounts)}/{count} test accounts on {server_id}")
        return created_accounts
    
    def create_standard_accounts(self, server_id: str, count: int = 100) -> List[AccountInfo]:
        """
        Create standard accounts following the naming schema.
        
        Args:
            server_id: Target server ID
            count: Number of accounts to create
            
        Returns:
            List of created account information
        """
        logger.info(f"Creating {count} standard accounts on server {server_id}")
        
        created_accounts = []
        account_settings = self.config_manager.get_account_settings()
        
        for i in range(1, count + 1):
            # Generate account name using naming schema
            account_name = self.naming_manager.generate_account_name(
                AccountType.PRODUCTION, 
                i, 
                account_settings.initial_balance
            )
            
            request = AccountCreationRequest(
                account_name=account_name,
                server_id=server_id,
                account_type=AccountType.PRODUCTION,
                initial_balance=account_settings.initial_balance,
                currency="USDT"
            )
            
            account_info = self.create_account(request)
            if account_info:
                created_accounts.append(account_info)
            
            # Brief pause between creations
            time.sleep(0.5)
            
            # Log progress every 10 accounts
            if i % 10 == 0:
                logger.info(f"Created {len(created_accounts)}/{i} accounts on {server_id}")
        
        logger.info(f"Created {len(created_accounts)}/{count} standard accounts on {server_id}")
        return created_accounts
    
    @retry_on_error(RetryConfig(max_attempts=2, base_delay=1.0))
    def verify_account(self, server_id: str, account_id: str) -> AccountVerificationResult:
        """
        Verify an account's status and configuration.
        
        Args:
            server_id: Server ID where account is located
            account_id: Account ID to verify
            
        Returns:
            Account verification result
        """
        logger.debug(f"Verifying account {account_id} on server {server_id}")
        
        try:
            executor = self._get_server_executor(server_id)
            if not executor:
                return AccountVerificationResult(
                    account_id=account_id,
                    is_valid=False,
                    balance=0.0,
                    currency='USDT',
                    status=AccountStatus.ERROR,
                    issues=['Failed to get server executor'],
                    verification_time=time.time()
                )
            
            # Verify account using HaasOnline API
            account_data = self._verify_haas_account(executor, account_id)
            
            if account_data:
                issues = []
                
                # Check balance
                expected_balance = self.config_manager.get_account_settings().initial_balance
                if abs(account_data['balance'] - expected_balance) > 1.0:
                    issues.append(f"Balance mismatch: expected {expected_balance}, got {account_data['balance']}")
                
                # Check currency
                if account_data['currency'] != 'USDT':
                    issues.append(f"Unexpected currency: {account_data['currency']}")
                
                # Check for additional coins
                if account_data.get('additional_coins'):
                    issues.append(f"Additional coins found: {account_data['additional_coins']}")
                
                return AccountVerificationResult(
                    account_id=account_id,
                    is_valid=len(issues) == 0,
                    balance=account_data['balance'],
                    currency=account_data['currency'],
                    status=AccountStatus.ACTIVE if len(issues) == 0 else AccountStatus.ERROR,
                    issues=issues,
                    verification_time=time.time()
                )
            else:
                return AccountVerificationResult(
                    account_id=account_id,
                    is_valid=False,
                    balance=0.0,
                    currency='USDT',
                    status=AccountStatus.ERROR,
                    issues=['Account not found or inaccessible'],
                    verification_time=time.time()
                )
                
        except Exception as e:
            return self.error_handler.handle_error(
                e,
                {'operation': 'verify_account', 'account_id': account_id, 'server_id': server_id},
                AccountVerificationResult(
                    account_id=account_id,
                    is_valid=False,
                    balance=0.0,
                    currency='USDT',
                    status=AccountStatus.ERROR,
                    issues=[str(e)],
                    verification_time=time.time()
                )
            )
    
    def find_test_accounts(self, server_id: str) -> List[AccountInfo]:
        """
        Find test accounts on a server.
        
        Args:
            server_id: Server ID to search
            
        Returns:
            List of found test accounts
        """
        logger.info(f"Finding test accounts on server {server_id}")
        
        try:
            # Get all accounts from server
            all_accounts = self.get_all_accounts(server_id)
            
            # Filter for test accounts
            test_accounts = []
            test_account_names = self.config_manager.get_account_settings().test_account_names
            
            for account in all_accounts:
                if any(test_name in account.account_name for test_name in test_account_names):
                    account.account_type = AccountType.TEST
                    test_accounts.append(account)
            
            logger.info(f"Found {len(test_accounts)} test accounts on {server_id}")
            return test_accounts
            
        except Exception as e:
            logger.error(f"Failed to find test accounts on {server_id}: {e}")
            return []
    
    def get_all_accounts(self, server_id: str, use_cache: bool = True) -> List[AccountInfo]:
        """
        Get all accounts from a server.
        
        Args:
            server_id: Server ID
            use_cache: Whether to use cached data if available
            
        Returns:
            List of account information
        """
        # Check cache first
        if use_cache and self._is_cache_valid(server_id):
            logger.debug(f"Using cached accounts for server {server_id}")
            return list(self._account_cache[server_id].values())
        
        logger.info(f"Fetching all accounts from server {server_id}")
        
        try:
            executor = self._get_server_executor(server_id)
            if not executor:
                logger.error(f"Failed to get executor for server {server_id}")
                return []
            
            # Get accounts from HaasOnline API
            accounts_data = self._get_haas_accounts(executor)
            
            accounts = []
            for account_data in accounts_data:
                account_info = AccountInfo(
                    account_id=account_data['id'],
                    account_name=account_data['name'],
                    server_id=server_id,
                    account_type=self._determine_account_type(account_data['name']),
                    balance=account_data.get('balance', 0.0),
                    currency=account_data.get('currency', 'USDT'),
                    status=AccountStatus.ACTIVE,
                    last_verified=time.time()
                )
                accounts.append(account_info)
            
            # Update cache
            self._account_cache[server_id] = {acc.account_id: acc for acc in accounts}
            self._cache_timestamp[server_id] = time.time()
            
            logger.info(f"Retrieved {len(accounts)} accounts from server {server_id}")
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get accounts from server {server_id}: {e}")
            return []
    
    def assign_account_to_lab(self, lab_id: str, server_id: str, account_type: AccountType = AccountType.TEST) -> Optional[str]:
        """
        Assign an appropriate account to a lab.
        
        Args:
            lab_id: Lab ID that needs an account
            server_id: Server where the lab is located
            account_type: Preferred account type
            
        Returns:
            Account ID if assignment successful, None otherwise
        """
        logger.info(f"Assigning {account_type.value} account to lab {lab_id} on server {server_id}")
        
        try:
            # Get available accounts of the requested type
            all_accounts = self.get_all_accounts(server_id)
            suitable_accounts = [acc for acc in all_accounts if acc.account_type == account_type and acc.status == AccountStatus.ACTIVE]
            
            if not suitable_accounts:
                logger.warning(f"No suitable {account_type.value} accounts found on server {server_id}")
                return None
            
            # Select the first available account (could be enhanced with load balancing)
            selected_account = suitable_accounts[0]
            
            logger.info(f"Assigned account {selected_account.account_id} ({selected_account.account_name}) to lab {lab_id}")
            return selected_account.account_id
            
        except Exception as e:
            logger.error(f"Failed to assign account to lab {lab_id}: {e}")
            return None
    
    def get_account_statistics(self, server_id: str = None) -> Dict[str, Any]:
        """
        Get account statistics for a server or all servers.
        
        Args:
            server_id: Optional server ID filter
            
        Returns:
            Dictionary with account statistics
        """
        if server_id:
            servers_to_check = [server_id]
        else:
            servers_to_check = self.server_manager.get_available_servers()
        
        total_stats = {
            'total_accounts': 0,
            'accounts_by_type': {},
            'accounts_by_status': {},
            'accounts_by_server': {},
            'total_balance': 0.0,
            'average_balance': 0.0
        }
        
        for srv_id in servers_to_check:
            accounts = self.get_all_accounts(srv_id)
            
            server_stats = {
                'total': len(accounts),
                'by_type': {},
                'by_status': {},
                'total_balance': 0.0
            }
            
            for account in accounts:
                # Count by type
                acc_type = account.account_type.value
                server_stats['by_type'][acc_type] = server_stats['by_type'].get(acc_type, 0) + 1
                total_stats['accounts_by_type'][acc_type] = total_stats['accounts_by_type'].get(acc_type, 0) + 1
                
                # Count by status
                acc_status = account.status.value
                server_stats['by_status'][acc_status] = server_stats['by_status'].get(acc_status, 0) + 1
                total_stats['accounts_by_status'][acc_status] = total_stats['accounts_by_status'].get(acc_status, 0) + 1
                
                # Sum balances
                server_stats['total_balance'] += account.balance
                total_stats['total_balance'] += account.balance
            
            total_stats['accounts_by_server'][srv_id] = server_stats
            total_stats['total_accounts'] += len(accounts)
        
        # Calculate average balance
        if total_stats['total_accounts'] > 0:
            total_stats['average_balance'] = total_stats['total_balance'] / total_stats['total_accounts']
        
        return total_stats
    
    def _create_haas_account(self, executor, request: AccountCreationRequest) -> Optional[str]:
        """Create account using HaasOnline API (placeholder implementation)"""
        # This is a placeholder - actual implementation would use HaasOnline API
        logger.warning("Using mock account creation - implement with actual HaasOnline API")
        
        # Generate mock account ID
        import uuid
        return str(uuid.uuid4())
    
    def _verify_haas_account(self, executor, account_id: str) -> Optional[Dict[str, Any]]:
        """Verify account using HaasOnline API (placeholder implementation)"""
        # This is a placeholder - actual implementation would use HaasOnline API
        logger.warning("Using mock account verification - implement with actual HaasOnline API")
        
        return {
            'id': account_id,
            'balance': 10000.0,
            'currency': 'USDT',
            'additional_coins': []
        }
    
    def _get_haas_accounts(self, executor) -> List[Dict[str, Any]]:
        """Get accounts using HaasOnline API (placeholder implementation)"""
        # This is a placeholder - actual implementation would use HaasOnline API
        logger.warning("Using mock account retrieval - implement with actual HaasOnline API")
        
        return [
            {'id': 'test-account-1', 'name': 'для тестов 10к', 'balance': 10000.0, 'currency': 'USDT'},
            {'id': 'test-account-2', 'name': '4AA-10k', 'balance': 10000.0, 'currency': 'USDT'}
        ]
    
    def _get_server_executor(self, server_id: str):
        """Get executor for a specific server (placeholder implementation)"""
        # This would integrate with the server manager to get an authenticated executor
        logger.warning(f"Using mock executor for server {server_id} - implement with actual server connection")
        return None
    
    def _determine_account_type(self, account_name: str) -> AccountType:
        """Determine account type from account name"""
        parsed = self.naming_manager.parse_account_name(account_name)
        return parsed.get('type', AccountType.PRODUCTION)
    
    def _update_account_cache(self, server_id: str, account_info: AccountInfo):
        """Update account cache with new information"""
        if server_id not in self._account_cache:
            self._account_cache[server_id] = {}
        
        self._account_cache[server_id][account_info.account_id] = account_info
        self._cache_timestamp[server_id] = time.time()
    
    def _is_cache_valid(self, server_id: str) -> bool:
        """Check if cached data is still valid"""
        if server_id not in self._cache_timestamp:
            return False
        
        return (time.time() - self._cache_timestamp[server_id]) < self.cache_duration

def main():
    """Test the account management system"""
    from infrastructure.server_manager import ServerManager
    from infrastructure.config_manager import ConfigManager
    
    # Initialize components
    config_manager = ConfigManager()
    server_manager = ServerManager()
    account_manager = AccountManager(server_manager, config_manager)
    
    print("Testing Account Management System...")
    print("=" * 50)
    
    # Test naming manager
    print("1. Testing account naming:")
    naming_manager = account_manager.naming_manager
    
    # Test name generation
    test_names = [
        (AccountType.PRODUCTION, 1, 10000.0),
        (AccountType.PRODUCTION, 27, 10000.0),  # Should be "AB"
        (AccountType.TEST, 1, 10000.0),
        (AccountType.DEVELOPMENT, 5, 15000.0),
        (AccountType.SIMULATION, 3, 5000.0)
    ]
    
    for acc_type, seq, balance in test_names:
        name = naming_manager.generate_account_name(acc_type, seq, balance)
        print(f"  {acc_type.value} #{seq} ({balance}): {name}")
    
    # Test name parsing
    print("\n2. Testing account name parsing:")
    test_parse_names = [
        "4AA-10k",
        "4AB-10k", 
        "для тестов 10к",
        "dev-5-15k",
        "sim-3-5k"
    ]
    
    for name in test_parse_names:
        parsed = naming_manager.parse_account_name(name)
        print(f"  {name}: {parsed}")
    
    # Test account creation request
    print("\n3. Testing account creation request:")
    request = AccountCreationRequest(
        account_name="test-account",
        server_id="srv01",
        account_type=AccountType.TEST,
        initial_balance=10000.0,
        currency="USDT"
    )
    print(f"  Created request: {request.account_name} on {request.server_id}")
    
    # Test account verification (mock)
    print("\n4. Testing account verification:")
    verification = account_manager.verify_account("srv01", "test-account-id")
    print(f"  Verification result: valid={verification.is_valid}, balance={verification.balance}")
    
    # Test account statistics
    print("\n5. Testing account statistics:")
    stats = account_manager.get_account_statistics("srv01")
    print(f"  Statistics: {stats}")
    
    print("\n" + "=" * 50)
    print("Account management system test completed!")
    print("Key features implemented:")
    print("  - Account naming schema management")
    print("  - Account creation and verification")
    print("  - Test account discovery")
    print("  - Account assignment to labs")
    print("  - Comprehensive statistics and reporting")

if __name__ == "__main__":
    main()