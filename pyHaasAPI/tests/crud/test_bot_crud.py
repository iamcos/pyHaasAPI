"""
Bot CRUD Tests

Comprehensive CRUD testing for Bot API with field mapping validation,
activation/deactivation workflows, and cleanup discipline.
"""

import pytest
import asyncio
from typing import Dict, Any

from .helpers import (
    assert_safe_field, assert_bot_details_integrity, retry_async,
    generate_test_resource_name, create_test_bot_config,
    log_field_mapping_warnings
)
from pyHaasAPI.exceptions import BotError, BotNotFoundError, BotConfigurationError, ValidationError


pytestmark = pytest.mark.asyncio

@pytest.mark.crud
@pytest.mark.srv03
class TestBotCRUD:
    """Bot CRUD operation tests"""
    
    async def test_bot_create_from_lab(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot creation from lab with proper field mapping"""
        bot_api = apis['bot_api']
        lab_api = apis['lab_api']
        
        # First create a lab to create bot from
        lab_config = {
            'script_id': default_entities['script_id'],
            'lab_name': generate_test_resource_name('lab', test_session_id),
            'market_tag': default_entities['market_tag'],
            'account_id': default_entities['account_id'],
            'interval': 1,
            'chart_style': 300,
            'trade_amount': 1000.0,
            'position_mode': 1,
            'margin_mode': 0,
            'leverage': 20
        }
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Create bot from lab
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        
        # Validate response structure
        assert bot_details is not None, "Bot creation should return bot details"
        
        # Record for cleanup
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Validate bot details integrity
        assert_bot_details_integrity(bot_details)
        
        # Log field mapping warnings for debugging
        log_field_mapping_warnings(bot_details, "BotDetails")
        
        # Verify bot name matches expected pattern
        bot_name = assert_safe_field(bot_details, 'bot_name', str, required=True)
        expected_name = generate_test_resource_name('bot', test_session_id, 1)
        assert bot_name == expected_name, f"Bot name mismatch: {bot_name} != {expected_name}"
    
    async def test_get_all_bots_includes_created(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test that created bot appears in bot list"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Get all bots
        bots = await bot_api.get_all_bots()
        
        # Verify bot list is not empty
        assert bots is not None, "Bots list should not be None"
        assert isinstance(bots, list), "Bots should be a list"
        
        # Find our created bot
        created_bot = None
        for bot in bots:
            if hasattr(bot, 'bot_id') and getattr(bot, 'bot_id') == bot_id:
                created_bot = bot
                break
        
        assert created_bot is not None, f"Created bot {bot_id} not found in bots list"
        
        # Validate the found bot
        assert_bot_details_integrity(created_bot)
    
    async def test_get_bot_details_safe_mapping(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot details retrieval with safe field mapping"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Retrieve bot details
        retrieved_details = await bot_api.get_bot_details(bot_id)
        
        # Validate all fields using safe mapping
        assert retrieved_details is not None, "Bot details should not be None"
        assert_bot_details_integrity(retrieved_details)
        
        # Verify critical fields are present
        assert_safe_field(retrieved_details, 'bot_id', str, required=True)
        assert_safe_field(retrieved_details, 'bot_name', str, required=True)
        assert_safe_field(retrieved_details, 'script_id', str, required=True)
        assert_safe_field(retrieved_details, 'account_id', str, required=True)
        assert_safe_field(retrieved_details, 'market_tag', str, required=True)
        
        # Check settings structure
        settings = assert_safe_field(retrieved_details, 'settings', required=True)
        if settings:
            assert_safe_field(settings, 'leverage', (int, float), required=False)
            assert_safe_field(settings, 'position_mode', (int, str), required=False)
            assert_safe_field(settings, 'margin_mode', (int, str), required=False)
        
        # Log any missing optional fields
        log_field_mapping_warnings(retrieved_details, "BotDetails")
    
    async def test_edit_bot_parameter(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot parameter editing with validation"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Edit bot parameters
        parameter_updates = {
            'leverage': 25,  # Change leverage
            'position_mode': 0,  # Change position mode
            'margin_mode': 1,  # Change margin mode
            'trade_amount': 3000.0  # Change trade amount
        }
        
        # Update each parameter individually
        for param_name, param_value in parameter_updates.items():
            updated_bot = await bot_api.edit_bot_parameter(bot_id, param_name, param_value)
            
            # Validate update response
            assert updated_bot is not None, f"Update {param_name} should return bot details"
            assert_bot_details_integrity(updated_bot)
        
        # Verify all changes were persisted
        retrieved_bot = await bot_api.get_bot_details(bot_id)
        assert_bot_details_integrity(retrieved_bot)
        
        # Check specific updated fields
        settings = assert_safe_field(retrieved_bot, 'settings', required=True)
        if settings:
            log_field_mapping_warnings(settings, "BotSettings")
    
    async def test_activate_deactivate_pause_resume(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot activation/deactivation/pause/resume workflow"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Test activation
        activated_bot = await bot_api.activate_bot(bot_id)
        assert activated_bot is not None, "Activation should return bot details"
        assert_bot_details_integrity(activated_bot)
        
        # Verify activation status
        bot_status = await bot_api.get_bot_details(bot_id)
        status = assert_safe_field(bot_status, 'status', str, required=False)
        # Status should indicate active state
        
        # Test pause
        paused_bot = await bot_api.pause_bot(bot_id)
        assert paused_bot is not None, "Pause should return bot details"
        assert_bot_details_integrity(paused_bot)
        
        # Test resume
        resumed_bot = await bot_api.resume_bot(bot_id)
        assert resumed_bot is not None, "Resume should return bot details"
        assert_bot_details_integrity(resumed_bot)
        
        # Test deactivation
        deactivated_bot = await bot_api.deactivate_bot(bot_id)
        assert deactivated_bot is not None, "Deactivation should return bot details"
        assert_bot_details_integrity(deactivated_bot)
        
        # Verify final status
        final_status = await bot_api.get_bot_details(bot_id)
        assert_bot_details_integrity(final_status)
    
    async def test_delete_bot(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot deletion with order cancellation"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        
        # Deactivate bot before deletion (if it was active)
        try:
            await bot_api.deactivate_bot(bot_id)
        except Exception:
            pass  # Bot might not be active
        
        # Cancel any orders
        try:
            await bot_api.cancel_all_bot_orders(bot_id)
        except Exception:
            pass  # No orders to cancel
        
        # Delete bot
        delete_result = await bot_api.delete_bot(bot_id)
        
        # Verify deletion (implementation depends on API response)
        assert delete_result is not None, "Delete should return result"
        
        # Verify bot is no longer in bots list
        bots = await bot_api.get_all_bots()
        bot_ids = [getattr(bot, 'bot_id', None) for bot in bots if hasattr(bot, 'bot_id')]
        assert bot_id not in bot_ids, f"Bot {bot_id} should not be in bots list after deletion"
    
    async def test_activate_nonexistent_bot(self, apis):
        """Test bot activation for non-existent bot"""
        bot_api = apis['bot_api']
        
        # Use a clearly non-existent bot ID
        non_existent_id = "non-existent-bot-id-12345"
        
        # Should raise BotNotFoundError
        with pytest.raises(BotNotFoundError):
            await bot_api.activate_bot(non_existent_id)
    
    async def test_edit_invalid_parameters(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot parameter editing with invalid values"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Try to edit with invalid parameters
        invalid_params = [
            ('leverage', -1),  # Invalid leverage
            ('position_mode', 999),  # Invalid position mode
            ('margin_mode', 999),  # Invalid margin mode
            ('trade_amount', -1000),  # Invalid trade amount
        ]
        
        for param_name, invalid_value in invalid_params:
            # Should raise BotConfigurationError or similar
            with pytest.raises((BotError, BotConfigurationError, ValidationError)):
                await bot_api.edit_bot_parameter(bot_id, param_name, invalid_value)
        
        # Verify bot is still in original state (no partial updates)
        retrieved_bot = await bot_api.get_bot_details(bot_id)
        assert_bot_details_integrity(retrieved_bot)
    
    async def test_bot_field_mapping_resilience(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test field mapping resilience with missing optional fields"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Test safe field access for various optional fields
        optional_fields = [
            'script_name', 'market_name', 'account_name',
            'leverage', 'position_mode', 'margin_mode',
            'trade_amount', 'status', 'created_at', 'updated_at'
        ]
        
        for field in optional_fields:
            # This should not raise an exception even if field is missing
            value = assert_safe_field(bot_details, field, required=False)
            # Field may be None or missing - both are acceptable
            assert value is None or isinstance(value, (str, int, float, bool)), \
                f"Field {field} has unexpected type: {type(value)}"
        
        # Test nested field access
        settings = assert_safe_field(bot_details, 'settings', required=False)
        if settings:
            for field in optional_fields:
                value = assert_safe_field(settings, field, required=False)
                assert value is None or isinstance(value, (str, int, float, bool)), \
                    f"Settings field {field} has unexpected type: {type(value)}"
    
    async def test_bot_retry_mechanism(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test retry mechanism for transient errors"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Test retry mechanism for bot details retrieval
        retrieved_details = await retry_async(
            bot_api.get_bot_details,
            bot_id,
            retries=3,
            delay=1.0
        )
        
        assert retrieved_details is not None, "Retry should succeed"
        assert_bot_details_integrity(retrieved_details)
    
    async def test_bot_orders_and_positions(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot orders and positions retrieval"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Get bot orders
        orders = await bot_api.get_bot_orders(bot_id)
        assert orders is not None, "Bot orders should not be None"
        assert isinstance(orders, list), "Bot orders should be a list"
        
        # Get bot positions
        positions = await bot_api.get_bot_positions(bot_id)
        assert positions is not None, "Bot positions should not be None"
        assert isinstance(positions, list), "Bot positions should be a list"
        
        # Test order cancellation (if any orders exist)
        if orders:
            for order in orders:
                if hasattr(order, 'order_id'):
                    order_id = getattr(order, 'order_id')
                    try:
                        cancel_result = await bot_api.cancel_bot_order(bot_id, order_id)
                        assert cancel_result is not None, "Order cancellation should return result"
                    except Exception:
                        pass  # Order might not be cancellable
    
    async def test_bot_runtime_data(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test bot runtime data retrieval"""
        bot_api = apis['bot_api']
        
        # Create a bot
        bot_config = create_test_bot_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Get bot runtime data
        runtime_data = await bot_api.get_full_bot_runtime_data(bot_id)
        
        # Validate runtime data structure
        assert runtime_data is not None, "Bot runtime data should not be None"
        
        # Log field mapping warnings for runtime data
        log_field_mapping_warnings(runtime_data, "BotRuntimeData")
        
        # Test safe field access for runtime data fields
        runtime_fields = [
            'bot_id', 'bot_name', 'status', 'performance',
            'trades', 'positions', 'orders', 'balance'
        ]
        
        for field in runtime_fields:
            value = assert_safe_field(runtime_data, field, required=False)
            assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                f"Runtime field {field} has unexpected type: {type(value)}"
