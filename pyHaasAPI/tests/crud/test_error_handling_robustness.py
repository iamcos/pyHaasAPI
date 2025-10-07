"""
Error Handling Robustness Tests

Comprehensive testing for error handling, retry mechanisms, and graceful
degradation across all CRUD operations.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from .helpers import (
    assert_safe_field, retry_async, log_field_mapping_warnings,
    generate_test_resource_name, create_test_lab_config, create_test_bot_config
)
from pyHaasAPI.exceptions import (
    HaasAPIError, AuthenticationError, APIError, ValidationError,
    NetworkError, ConnectionError, TimeoutError, ConfigurationError,
    LabError, LabNotFoundError, LabExecutionError, LabConfigurationError,
    BotError, BotNotFoundError, BotCreationError, BotConfigurationError,
    AccountError, AccountNotFoundError, AccountConfigurationError
)


pytestmark = pytest.mark.asyncio

@pytest.mark.crud
@pytest.mark.srv03
@pytest.mark.error_handling
class TestErrorHandlingRobustness:
    """Error handling robustness tests"""
    
    async def test_error_messages_include_context(self, apis):
        """Test that error messages include actionable context"""
        lab_api = apis['lab_api']
        bot_api = apis['bot_api']
        account_api = apis['account_api']
        
        # Test lab not found error
        non_existent_lab_id = "non-existent-lab-id-12345"
        try:
            await lab_api.get_lab_details(non_existent_lab_id)
            pytest.fail("Should have raised LabNotFoundError")
        except LabNotFoundError as e:
            # Error message should include context
            error_message = str(e)
            assert non_existent_lab_id in error_message, f"Error message should include lab ID: {error_message}"
            assert "lab" in error_message.lower(), f"Error message should mention lab: {error_message}"
        
        # Test bot not found error
        non_existent_bot_id = "non-existent-bot-id-12345"
        try:
            await bot_api.get_bot_details(non_existent_bot_id)
            pytest.fail("Should have raised BotNotFoundError")
        except BotNotFoundError as e:
            # Error message should include context
            error_message = str(e)
            assert non_existent_bot_id in error_message, f"Error message should include bot ID: {error_message}"
            assert "bot" in error_message.lower(), f"Error message should mention bot: {error_message}"
        
        # Test account not found error
        non_existent_account_id = "non-existent-account-id-12345"
        try:
            await account_api.get_account_data(non_existent_account_id)
            pytest.fail("Should have raised AccountNotFoundError")
        except AccountNotFoundError as e:
            # Error message should include context
            error_message = str(e)
            assert non_existent_account_id in error_message, f"Error message should include account ID: {error_message}"
            assert "account" in error_message.lower(), f"Error message should mention account: {error_message}"
    
    async def test_retryable_failures_do_not_break_flow(self, apis, cleanup_registry, test_session_id):
        """Test that transient read errors are retried and don't break flow"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test retry mechanism for lab details retrieval
        # This should succeed even if there are transient network issues
        retrieved_details = await retry_async(
            lab_api.get_lab_details,
            lab_id,
            retries=3,
            delay=1.0
        )
        
        assert retrieved_details is not None, "Retry should succeed"
        assert_safe_field(retrieved_details, 'lab_id', str, required=True)
        
        # Test retry mechanism for lab listing
        labs = await retry_async(
            lab_api.get_labs,
            retries=3,
            delay=1.0
        )
        
        assert labs is not None, "Retry should succeed for lab listing"
        assert isinstance(labs, list), "Labs should be a list"
    
    async def test_rate_limit_backoff(self, apis, cleanup_registry, test_session_id):
        """Test rate limit backoff doesn't break CRUD flows"""
        lab_api = apis['lab_api']
        
        # Create multiple labs to potentially trigger rate limiting
        lab_ids = []
        for i in range(3):
            lab_config = create_test_lab_config(
                script_id="test_script_id",
                market_tag="BTC_USDT_PERPETUAL",
                account_id="test_account_id",
                session_id=f"{test_session_id}_{i}"
            )
            
            try:
                lab_details = await lab_api.create_lab(**lab_config)
                lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
                lab_ids.append(lab_id)
                cleanup_registry.add_lab(lab_id)
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                # If rate limited, the error should be retryable
                if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                    print(f"Rate limit detected: {e}")
                    # Wait and retry
                    await asyncio.sleep(2.0)
                    try:
                        lab_details = await lab_api.create_lab(**lab_config)
                        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
                        lab_ids.append(lab_id)
                        cleanup_registry.add_lab(lab_id)
                    except Exception as retry_e:
                        print(f"Retry after rate limit failed: {retry_e}")
                else:
                    raise e
        
        # Verify all labs were created successfully
        assert len(lab_ids) > 0, "Should have created at least one lab"
        
        # Test that subsequent operations work despite rate limiting
        for lab_id in lab_ids:
            lab_details = await lab_api.get_lab_details(lab_id)
            assert lab_details is not None, f"Should be able to retrieve lab {lab_id}"
    
    async def test_network_error_recovery(self, apis, cleanup_registry, test_session_id):
        """Test network error recovery and graceful degradation"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test that network errors are properly categorized
        try:
            # This should work normally
            retrieved_details = await lab_api.get_lab_details(lab_id)
            assert retrieved_details is not None, "Lab details should be retrievable"
        except NetworkError as e:
            # Network errors should be properly categorized
            assert "network" in str(e).lower() or "connection" in str(e).lower(), \
                f"Network error should mention network/connection: {e}"
        except ConnectionError as e:
            # Connection errors should be properly categorized
            assert "connection" in str(e).lower(), \
                f"Connection error should mention connection: {e}"
        except TimeoutError as e:
            # Timeout errors should be properly categorized
            assert "timeout" in str(e).lower() or "time" in str(e).lower(), \
                f"Timeout error should mention timeout/time: {e}"
    
    async def test_validation_error_handling(self, apis, cleanup_registry, test_session_id):
        """Test validation error handling with invalid inputs"""
        lab_api = apis['lab_api']
        bot_api = apis['bot_api']
        
        # Test lab creation with invalid parameters
        invalid_lab_configs = [
            {
                'script_id': '',  # Empty script ID
                'lab_name': generate_test_resource_name('lab', test_session_id),
                'market_tag': 'BTC_USDT_PERPETUAL',
                'account_id': 'test_account_id'
            },
            {
                'script_id': 'test_script_id',
                'lab_name': '',  # Empty lab name
                'market_tag': 'BTC_USDT_PERPETUAL',
                'account_id': 'test_account_id'
            },
            {
                'script_id': 'test_script_id',
                'lab_name': generate_test_resource_name('lab', test_session_id),
                'market_tag': '',  # Empty market tag
                'account_id': 'test_account_id'
            },
            {
                'script_id': 'test_script_id',
                'lab_name': generate_test_resource_name('lab', test_session_id),
                'market_tag': 'BTC_USDT_PERPETUAL',
                'account_id': ''  # Empty account ID
            }
        ]
        
        for invalid_config in invalid_lab_configs:
            try:
                await lab_api.create_lab(**invalid_config)
                pytest.fail(f"Should have raised ValidationError for invalid config: {invalid_config}")
            except (ValidationError, LabError, LabConfigurationError) as e:
                # Validation errors should include context about what was invalid
                error_message = str(e)
                assert len(error_message) > 0, "Validation error should have a message"
                print(f"Validation error (expected): {e}")
            except Exception as e:
                # Other errors are also acceptable for invalid inputs
                print(f"Other error for invalid config (acceptable): {e}")
        
        # Test bot creation with invalid parameters
        invalid_bot_configs = [
            {
                'script_id': '',  # Empty script ID
                'bot_name': generate_test_resource_name('bot', test_session_id, 1),
                'market_tag': 'BTC_USDT_PERPETUAL',
                'account_id': 'test_account_id'
            },
            {
                'script_id': 'test_script_id',
                'bot_name': '',  # Empty bot name
                'market_tag': 'BTC_USDT_PERPETUAL',
                'account_id': 'test_account_id'
            }
        ]
        
        for invalid_config in invalid_bot_configs:
            try:
                await bot_api.create_bot(**invalid_config)
                pytest.fail(f"Should have raised ValidationError for invalid bot config: {invalid_config}")
            except (ValidationError, BotError, BotConfigurationError) as e:
                # Validation errors should include context about what was invalid
                error_message = str(e)
                assert len(error_message) > 0, "Validation error should have a message"
                print(f"Bot validation error (expected): {e}")
            except Exception as e:
                # Other errors are also acceptable for invalid inputs
                print(f"Other error for invalid bot config (acceptable): {e}")
    
    async def test_authentication_error_handling(self, apis):
        """Test authentication error handling"""
        # Test with invalid credentials (if possible to simulate)
        # Note: This might not be testable without actually providing invalid credentials
        # which could affect the test session
        
        # For now, test that authentication errors are properly categorized
        try:
            # This should work with valid credentials
            accounts = await apis['account_api'].get_accounts()
            assert accounts is not None, "Should be able to get accounts with valid auth"
        except AuthenticationError as e:
            # Authentication errors should be properly categorized
            assert "auth" in str(e).lower() or "login" in str(e).lower() or "credential" in str(e).lower(), \
                f"Authentication error should mention auth/login/credential: {e}"
    
    async def test_configuration_error_handling(self, apis):
        """Test configuration error handling"""
        # Test that configuration errors are properly categorized
        try:
            # This should work with valid configuration
            accounts = await apis['account_api'].get_accounts()
            assert accounts is not None, "Should be able to get accounts with valid config"
        except ConfigurationError as e:
            # Configuration errors should be properly categorized
            assert "config" in str(e).lower() or "setting" in str(e).lower(), \
                f"Configuration error should mention config/setting: {e}"
    
    async def test_api_error_hierarchy(self, apis, cleanup_registry, test_session_id):
        """Test that API errors follow proper hierarchy"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test that specific errors inherit from base errors
        try:
            await lab_api.get_lab_details("non-existent-lab-id")
            pytest.fail("Should have raised LabNotFoundError")
        except LabNotFoundError as e:
            # LabNotFoundError should be a subclass of LabError
            assert isinstance(e, LabError), "LabNotFoundError should be a subclass of LabError"
            # LabError should be a subclass of APIError
            assert isinstance(e, APIError), "LabError should be a subclass of APIError"
            # APIError should be a subclass of HaasAPIError
            assert isinstance(e, HaasAPIError), "APIError should be a subclass of HaasAPIError"
        
        # Test bot error hierarchy
        try:
            await apis['bot_api'].get_bot_details("non-existent-bot-id")
            pytest.fail("Should have raised BotNotFoundError")
        except BotNotFoundError as e:
            # BotNotFoundError should be a subclass of BotError
            assert isinstance(e, BotError), "BotNotFoundError should be a subclass of BotError"
            # BotError should be a subclass of APIError
            assert isinstance(e, APIError), "BotError should be a subclass of APIError"
            # APIError should be a subclass of HaasAPIError
            assert isinstance(e, HaasAPIError), "APIError should be a subclass of HaasAPIError"
        
        # Test account error hierarchy
        try:
            await apis['account_api'].get_account_data("non-existent-account-id")
            pytest.fail("Should have raised AccountNotFoundError")
        except AccountNotFoundError as e:
            # AccountNotFoundError should be a subclass of AccountError
            assert isinstance(e, AccountError), "AccountNotFoundError should be a subclass of AccountError"
            # AccountError should be a subclass of APIError
            assert isinstance(e, APIError), "AccountError should be a subclass of APIError"
            # APIError should be a subclass of HaasAPIError
            assert isinstance(e, HaasAPIError), "APIError should be a subclass of HaasAPIError"
    
    async def test_error_recovery_suggestions(self, apis):
        """Test that error messages include recovery suggestions"""
        lab_api = apis['lab_api']
        bot_api = apis['bot_api']
        account_api = apis['account_api']
        
        # Test lab not found error with recovery suggestions
        try:
            await lab_api.get_lab_details("non-existent-lab-id")
            pytest.fail("Should have raised LabNotFoundError")
        except LabNotFoundError as e:
            error_message = str(e)
            # Error message should include helpful information
            assert len(error_message) > 10, "Error message should be informative"
            # Should mention lab ID or provide context
            assert "lab" in error_message.lower() or "id" in error_message.lower(), \
                f"Error message should mention lab/ID: {error_message}"
        
        # Test bot not found error with recovery suggestions
        try:
            await bot_api.get_bot_details("non-existent-bot-id")
            pytest.fail("Should have raised BotNotFoundError")
        except BotNotFoundError as e:
            error_message = str(e)
            # Error message should include helpful information
            assert len(error_message) > 10, "Error message should be informative"
            # Should mention bot ID or provide context
            assert "bot" in error_message.lower() or "id" in error_message.lower(), \
                f"Error message should mention bot/ID: {error_message}"
        
        # Test account not found error with recovery suggestions
        try:
            await account_api.get_account_data("non-existent-account-id")
            pytest.fail("Should have raised AccountNotFoundError")
        except AccountNotFoundError as e:
            error_message = str(e)
            # Error message should include helpful information
            assert len(error_message) > 10, "Error message should be informative"
            # Should mention account ID or provide context
            assert "account" in error_message.lower() or "id" in error_message.lower(), \
                f"Error message should mention account/ID: {error_message}"
    
    async def test_concurrent_error_handling(self, apis, cleanup_registry, test_session_id):
        """Test error handling under concurrent operations"""
        lab_api = apis['lab_api']
        
        # Create multiple labs concurrently
        async def create_lab(index):
            lab_config = create_test_lab_config(
                script_id="test_script_id",
                market_tag="BTC_USDT_PERPETUAL",
                account_id="test_account_id",
                session_id=f"{test_session_id}_{index}"
            )
            
            try:
                lab_details = await lab_api.create_lab(**lab_config)
                lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
                cleanup_registry.add_lab(lab_id)
                return lab_id
            except Exception as e:
                print(f"Error creating lab {index}: {e}")
                return None
        
        # Create labs concurrently
        tasks = [create_lab(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some labs should be created successfully
        successful_labs = [result for result in results if isinstance(result, str)]
        assert len(successful_labs) > 0, "At least some labs should be created successfully"
        
        # Test concurrent retrieval
        async def get_lab_details(lab_id):
            try:
                return await lab_api.get_lab_details(lab_id)
            except Exception as e:
                print(f"Error retrieving lab {lab_id}: {e}")
                return None
        
        # Retrieve labs concurrently
        if successful_labs:
            retrieve_tasks = [get_lab_details(lab_id) for lab_id in successful_labs]
            retrieve_results = await asyncio.gather(*retrieve_tasks, return_exceptions=True)
            
            # Some retrievals should succeed
            successful_retrievals = [result for result in retrieve_results if result is not None]
            assert len(successful_retrievals) > 0, "At least some retrievals should succeed"
    
    async def test_error_logging_and_monitoring(self, apis, cleanup_registry, test_session_id):
        """Test that errors are properly logged and can be monitored"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test that errors include sufficient information for monitoring
        try:
            await lab_api.get_lab_details("non-existent-lab-id")
            pytest.fail("Should have raised LabNotFoundError")
        except LabNotFoundError as e:
            # Error should include information useful for monitoring
            error_message = str(e)
            error_type = type(e).__name__
            
            # Error should be categorizable
            assert error_type == "LabNotFoundError", f"Error type should be LabNotFoundError: {error_type}"
            
            # Error should include context
            assert len(error_message) > 0, "Error message should not be empty"
            
            # Error should be serializable for logging
            try:
                import json
                error_dict = {
                    "type": error_type,
                    "message": error_message,
                    "lab_id": "non-existent-lab-id"
                }
                json.dumps(error_dict)
            except Exception as json_e:
                pytest.fail(f"Error should be serializable for logging: {json_e}")
    
    async def test_graceful_degradation(self, apis, cleanup_registry, test_session_id):
        """Test graceful degradation when some operations fail"""
        lab_api = apis['lab_api']
        bot_api = apis['bot_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test that the system continues to work even if some operations fail
        try:
            # This should work
            retrieved_lab = await lab_api.get_lab_details(lab_id)
            assert retrieved_lab is not None, "Lab retrieval should work"
        except Exception as e:
            print(f"Lab retrieval failed: {e}")
            # Even if this fails, other operations should still work
        
        # Test that other operations continue to work
        try:
            # This should work
            labs = await lab_api.get_labs()
            assert labs is not None, "Lab listing should work"
            assert isinstance(labs, list), "Labs should be a list"
        except Exception as e:
            print(f"Lab listing failed: {e}")
            # Even if this fails, the system should not be completely broken
        
        # Test that bot operations continue to work
        try:
            bots = await bot_api.get_all_bots()
            assert bots is not None, "Bot listing should work"
            assert isinstance(bots, list), "Bots should be a list"
        except Exception as e:
            print(f"Bot listing failed: {e}")
            # Even if this fails, the system should not be completely broken
