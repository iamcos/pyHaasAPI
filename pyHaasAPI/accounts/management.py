"""
Account Management System

This module provides comprehensive account management functionality for
HaasOnline trading operations, including account creation, verification,
and management with standardized naming schemas.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

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
    account_type: AccountType
    balance: float
    currency: str
    status: AccountStatus
    exchange: str = ""
    created_time: Optional[float] = None
    last_verified: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Check if account is active"""
        return self.status == AccountStatus.ACTIVE
    
    @property
    def is_test_account(self) -> bool:
        """Check if this is a test account"""
        return self.account_type == AccountType.TEST
    
    @property
    def balance_k(self) -> float:
        """Get balance in thousands"""
        return self.balance / 1000.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'account_id': self.account_id,
            'account_name': self.account_name,
            'account_type': self.account_type.value,
            'balance': self.balance,
            'currency': self.currency,
            'status': self.status.value,
            'exchange': self.exchange,
            'is_active': self.is_active,
            'is_test_account': self.is_test_account,
            'balance_k': self.balance_k,
            'created_time': self.created_time,
            'last_verified': self.last_verified,
            'error_message': self.error_message
        }

@dataclass
class AccountCreationRequest:
    """Request for creating a new account"""
    account_name: str
    account_type: AccountType
    initial_balance: float
    currency: str = "USDT"
    exchange: str = "BINANCE"
    additional_config: Optional[Dict[str, Any]] = None

class AccountNamingManager:
    """Manages account naming schemas and generation"""
    
    def __init__(self):
        self.naming_patterns = {
            'standard': '4{sequence}-{balance}k',
            'test': 'для тестов {balance}к',
            'development': 'dev-{sequence}-{balance}k',
            'simulation': 'sim-{sequence}-{balance}k'
        }
    
    def generate_account_name(
        self, 
        account_type: AccountType, 
        sequence_number: int = 1, 
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
            return self.naming_patterns['test'].format(balance=balance_k)
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
            return self.naming_patterns['standard'].format(
                sequence=sequence_letters, 
                balance=balance_k
            )
    
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
        import re
        
        # Test account pattern
        if "для тестов" in account_name:
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

class AccountManager:
    """Main account management system"""
    
    def __init__(self, executor):
        """
        Initialize account manager.
        
        Args:
            executor: HaasOnline API executor
        """
        self.executor = executor
        self.naming_manager = AccountNamingManager()
        
        # Account cache
        self._account_cache: Dict[str, AccountInfo] = {}
        self._cache_timestamp: float = 0
        self.cache_duration = 300  # 5 minutes
    
    def create_account(self, request: AccountCreationRequest) -> Optional[AccountInfo]:
        """
        Create a new trading account.
        
        Args:
            request: Account creation request
            
        Returns:
            AccountInfo object if successful, None otherwise
        """
        logger.info(f"Creating account {request.account_name}")
        
        try:
            # Create the account using HaasOnline API
            account_id = self._create_haas_account(request)
            
            if account_id:
                # Create AccountInfo object
                account_info = AccountInfo(
                    account_id=account_id,
                    account_name=request.account_name,
                    account_type=request.account_type,
                    balance=request.initial_balance,
                    currency=request.currency,
                    status=AccountStatus.ACTIVE,
                    exchange=request.exchange,
                    created_time=time.time()
                )
                
                # Update cache
                self._account_cache[account_id] = account_info
                
                logger.info(f"Successfully created account {account_id}")
                return account_info
            else:
                logger.error(f"Failed to create account {request.account_name}")
                return None
                
        except Exception as e:
            logger.error(f"Account creation failed: {e}")
            return None
    
    def create_test_accounts(self, count: int = 2) -> List[AccountInfo]:
        """
        Create test accounts.
        
        Args:
            count: Number of test accounts to create
            
        Returns:
            List of created account information
        """
        logger.info(f"Creating {count} test accounts")
        
        created_accounts = []
        
        for i in range(count):
            # Generate test account name
            if i == 0:
                account_name = "для тестов 10к"
            else:
                account_name = f"для тестов 10к {i+1}"
            
            request = AccountCreationRequest(
                account_name=account_name,
                account_type=AccountType.TEST,
                initial_balance=10000.0,
                currency="USDT"
            )
            
            account_info = self.create_account(request)
            if account_info:
                created_accounts.append(account_info)
            
            # Brief pause between creations
            time.sleep(1.0)
        
        logger.info(f"Created {len(created_accounts)}/{count} test accounts")
        return created_accounts
    
    def create_standard_accounts(self, count: int = 100) -> List[AccountInfo]:
        """
        Create standard accounts following the naming schema.
        
        Args:
            count: Number of accounts to create
            
        Returns:
            List of created account information
        """
        logger.info(f"Creating {count} standard accounts")
        
        created_accounts = []
        
        for i in range(1, count + 1):
            # Generate account name using naming schema
            account_name = self.naming_manager.generate_account_name(
                AccountType.PRODUCTION, 
                i, 
                10000.0
            )
            
            request = AccountCreationRequest(
                account_name=account_name,
                account_type=AccountType.PRODUCTION,
                initial_balance=10000.0,
                currency="USDT"
            )
            
            account_info = self.create_account(request)
            if account_info:
                created_accounts.append(account_info)
            
            # Brief pause between creations
            time.sleep(0.5)
            
            # Log progress every 10 accounts
            if i % 10 == 0:
                logger.info(f"Created {len(created_accounts)}/{i} accounts")
        
        logger.info(f"Created {len(created_accounts)}/{count} standard accounts")
        return created_accounts
    
    def get_all_accounts(self, use_cache: bool = True) -> List[AccountInfo]:
        """
        Get all accounts.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            List of account information
        """
        # Check cache first
        if use_cache and self._is_cache_valid():
            logger.debug("Using cached accounts")
            return list(self._account_cache.values())
        
        logger.info("Fetching all accounts")
        
        try:
            # Get accounts from HaasOnline API
            accounts_data = self._get_haas_accounts()
            
            accounts = []
            for account_data in accounts_data:
                account_info = AccountInfo(
                    account_id=account_data['id'],
                    account_name=account_data['name'],
                    account_type=self._determine_account_type(account_data['name']),
                    balance=account_data.get('balance', 0.0),
                    currency=account_data.get('currency', 'USDT'),
                    status=AccountStatus.ACTIVE,
                    exchange=account_data.get('exchange', ''),
                    last_verified=time.time()
                )
                accounts.append(account_info)
            
            # Update cache
            self._account_cache = {acc.account_id: acc for acc in accounts}
            self._cache_timestamp = time.time()
            
            logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return []
    
    def find_test_accounts(self) -> List[AccountInfo]:
        """
        Find test accounts.
        
        Returns:
            List of found test accounts
        """
        logger.info("Finding test accounts")
        
        all_accounts = self.get_all_accounts()
        test_accounts = [acc for acc in all_accounts if acc.is_test_account]
        
        logger.info(f"Found {len(test_accounts)} test accounts")
        return test_accounts
    
    def find_account_by_name(self, account_name: str) -> Optional[AccountInfo]:
        """
        Find account by name.
        
        Args:
            account_name: Account name to search for
            
        Returns:
            AccountInfo if found, None otherwise
        """
        all_accounts = self.get_all_accounts()
        
        for account in all_accounts:
            if account.account_name == account_name:
                return account
        
        return None
    
    def find_accounts_by_type(self, account_type: AccountType) -> List[AccountInfo]:
        """
        Find accounts by type.
        
        Args:
            account_type: Account type to filter by
            
        Returns:
            List of accounts of the specified type
        """
        all_accounts = self.get_all_accounts()
        return [acc for acc in all_accounts if acc.account_type == account_type]
    
    def verify_account(self, account_id: str) -> Dict[str, Any]:
        """
        Verify an account's status and configuration.
        
        Args:
            account_id: Account ID to verify
            
        Returns:
            Verification result dictionary
        """
        logger.debug(f"Verifying account {account_id}")
        
        try:
            # Verify account using HaasOnline API
            account_data = self._verify_haas_account(account_id)
            
            if account_data:
                issues = []
                
                # Check balance
                expected_balance = 10000.0  # Default expected balance
                if abs(account_data['balance'] - expected_balance) > 1.0:
                    issues.append(f"Balance mismatch: expected {expected_balance}, got {account_data['balance']}")
                
                # Check currency
                if account_data['currency'] != 'USDT':
                    issues.append(f"Unexpected currency: {account_data['currency']}")
                
                return {
                    'account_id': account_id,
                    'is_valid': len(issues) == 0,
                    'balance': account_data['balance'],
                    'currency': account_data['currency'],
                    'issues': issues,
                    'verification_time': time.time()
                }
            else:
                return {
                    'account_id': account_id,
                    'is_valid': False,
                    'issues': ['Account not found or inaccessible'],
                    'verification_time': time.time()
                }
                
        except Exception as e:
            return {
                'account_id': account_id,
                'is_valid': False,
                'issues': [str(e)],
                'verification_time': time.time()
            }
    
    def assign_account_to_lab(self, lab_id: str, account_type: AccountType = AccountType.TEST) -> Optional[str]:
        """
        Assign an appropriate account to a lab.
        
        Args:
            lab_id: Lab ID that needs an account
            account_type: Preferred account type
            
        Returns:
            Account ID if assignment successful, None otherwise
        """
        logger.info(f"Assigning {account_type.value} account to lab {lab_id}")
        
        try:
            # Get available accounts of the requested type
            suitable_accounts = self.find_accounts_by_type(account_type)
            active_accounts = [acc for acc in suitable_accounts if acc.is_active]
            
            if not active_accounts:
                logger.warning(f"No suitable {account_type.value} accounts found")
                return None
            
            # Select the first available account (could be enhanced with load balancing)
            selected_account = active_accounts[0]
            
            logger.info(f"Assigned account {selected_account.account_id} ({selected_account.account_name}) to lab {lab_id}")
            return selected_account.account_id
            
        except Exception as e:
            logger.error(f"Failed to assign account to lab {lab_id}: {e}")
            return None
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """
        Get account statistics.
        
        Returns:
            Dictionary with account statistics
        """
        accounts = self.get_all_accounts()
        
        stats = {
            'total_accounts': len(accounts),
            'accounts_by_type': {},
            'accounts_by_status': {},
            'total_balance': 0.0,
            'average_balance': 0.0,
            'currencies': set()
        }
        
        for account in accounts:
            # Count by type
            acc_type = account.account_type.value
            stats['accounts_by_type'][acc_type] = stats['accounts_by_type'].get(acc_type, 0) + 1
            
            # Count by status
            acc_status = account.status.value
            stats['accounts_by_status'][acc_status] = stats['accounts_by_status'].get(acc_status, 0) + 1
            
            # Sum balances
            stats['total_balance'] += account.balance
            stats['currencies'].add(account.currency)
        
        # Calculate average balance
        if stats['total_accounts'] > 0:
            stats['average_balance'] = stats['total_balance'] / stats['total_accounts']
        
        # Convert set to list for JSON serialization
        stats['currencies'] = list(stats['currencies'])
        
        return stats
    
    def _create_haas_account(self, request: AccountCreationRequest) -> Optional[str]:
        """Create account using HaasOnline API"""
        try:
            from .. import api
            
            # Create simulated account
            account_request = {
                'name': request.account_name,
                'driver_code': request.exchange,
                'driver_type': 2,  # Simulated account type
                'initial_balance': request.initial_balance,
                'currency': request.currency
            }
            
            result = api.add_simulated_account(self.executor, account_request)
            return result.account_id if result else None
            
        except Exception as e:
            logger.error(f"Failed to create HaasOnline account: {e}")
            return None
    
    def _get_haas_accounts(self) -> List[Dict[str, Any]]:
        """Get accounts using HaasOnline API"""
        try:
            from .. import api
            
            accounts = api.get_all_accounts(self.executor)
            return [
                {
                    'id': acc.account_id,
                    'name': acc.name,
                    'balance': 10000.0,  # Default balance
                    'currency': 'USDT',
                    'exchange': acc.exchange_code
                }
                for acc in accounts
            ]
            
        except Exception as e:
            logger.error(f"Failed to get HaasOnline accounts: {e}")
            return []
    
    def _verify_haas_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Verify account using HaasOnline API"""
        try:
            from .. import api
            
            account = api.get_account_details(self.executor, account_id)
            if account:
                return {
                    'id': account_id,
                    'balance': 10000.0,  # Default balance
                    'currency': 'USDT'
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to verify HaasOnline account: {e}")
            return None
    
    def _determine_account_type(self, account_name: str) -> AccountType:
        """Determine account type from account name"""
        parsed = self.naming_manager.parse_account_name(account_name)
        return parsed.get('type', AccountType.PRODUCTION)
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        return (time.time() - self._cache_timestamp) < self.cache_duration
    
    def clear_cache(self):
        """Clear account cache"""
        self._account_cache.clear()
        self._cache_timestamp = 0
        logger.info("Cleared account cache")

# Convenience functions
def create_test_account(executor, account_name: str = "для тестов 10к") -> Optional[AccountInfo]:
    """
    Convenience function to create a test account.
    
    Args:
        executor: HaasOnline API executor
        account_name: Account name
        
    Returns:
        AccountInfo if successful
    """
    manager = AccountManager(executor)
    request = AccountCreationRequest(
        account_name=account_name,
        account_type=AccountType.TEST,
        initial_balance=10000.0
    )
    return manager.create_account(request)

def find_test_account(executor) -> Optional[AccountInfo]:
    """
    Convenience function to find a test account.
    
    Args:
        executor: HaasOnline API executor
        
    Returns:
        First test account found, or None
    """
    manager = AccountManager(executor)
    test_accounts = manager.find_test_accounts()
    return test_accounts[0] if test_accounts else None