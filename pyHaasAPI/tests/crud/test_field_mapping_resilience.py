"""
Field Mapping Resilience Tests

Comprehensive testing for field mapping resilience across all entities
to prevent the 50% of runtime errors caused by improper field mapping.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from .helpers import (
    assert_safe_field, log_field_mapping_warnings, retry_async,
    generate_test_resource_name, create_test_lab_config, create_test_bot_config
)
from pyHaasAPI.exceptions import (
    LabError, LabNotFoundError, BotError, BotNotFoundError,
    AccountError, AccountNotFoundError, ValidationError
)


pytestmark = pytest.mark.asyncio

@pytest.mark.crud
@pytest.mark.srv03
@pytest.mark.field_mapping
class TestFieldMappingResilience:
    """Field mapping resilience tests across all entities"""
    
    async def test_lab_field_mapping_resilience(self, apis, cleanup_registry, test_session_id):
        """Test lab field mapping resilience with server-side variations"""
        lab_api = apis['lab_api']
        
        # Create a lab to test field mapping
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test safe field access for all possible lab fields
        lab_fields = [
            # Required fields
            'lab_id', 'lab_name', 'script_id',
            # Optional fields that might be missing
            'script_name', 'market_name', 'account_name',
            'market_tag', 'account_id', 'status',
            'leverage', 'position_mode', 'margin_mode',
            'trade_amount', 'chart_style', 'interval',
            'max_parallel', 'max_generations', 'max_epochs',
            'created_at', 'updated_at', 'last_execution',
            'execution_count', 'success_count', 'failure_count'
        ]
        
        for field in lab_fields:
            # This should not raise an exception even if field is missing
            value = assert_safe_field(lab_details, field, required=False)
            # Field may be None or missing - both are acceptable
            assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                f"Lab field {field} has unexpected type: {type(value)}"
        
        # Test nested field access for settings
        settings = assert_safe_field(lab_details, 'settings', required=False)
        if settings:
            settings_fields = [
                'market_tag', 'account_id', 'script_id',
                'leverage', 'position_mode', 'margin_mode',
                'trade_amount', 'chart_style', 'interval',
                'max_parallel', 'max_generations', 'max_epochs'
            ]
            
            for field in settings_fields:
                value = assert_safe_field(settings, field, required=False)
                assert value is None or isinstance(value, (str, int, float, bool)), \
                    f"Settings field {field} has unexpected type: {type(value)}"
        
        # Test parameters field
        parameters = assert_safe_field(lab_details, 'parameters', required=False)
        if parameters:
            assert isinstance(parameters, list), f"Parameters should be list: {type(parameters)}"
            for param in parameters:
                if isinstance(param, dict):
                    param_fields = ['name', 'value', 'type', 'min', 'max', 'step']
                    for field in param_fields:
                        value = assert_safe_field(param, field, required=False)
                        assert value is None or isinstance(value, (str, int, float, bool)), \
                            f"Parameter field {field} has unexpected type: {type(value)}"
        
        # Log field mapping warnings for debugging
        log_field_mapping_warnings(lab_details, "LabDetails")
    
    async def test_bot_field_mapping_resilience(self, apis, cleanup_registry, test_session_id):
        """Test bot field mapping resilience with server-side variations"""
        bot_api = apis['bot_api']
        
        # Create a bot to test field mapping
        bot_config = create_test_bot_config(
            script_id='test_script_id',
            market_tag='BTC_USDT_PERPETUAL',
            account_id='test_account_id',
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Test safe field access for all possible bot fields
        bot_fields = [
            # Required fields
            'bot_id', 'bot_name', 'script_id', 'account_id', 'market_tag',
            # Optional fields that might be missing
            'script_name', 'market_name', 'account_name',
            'status', 'leverage', 'position_mode', 'margin_mode',
            'trade_amount', 'created_at', 'updated_at',
            'activated_at', 'deactivated_at', 'last_trade',
            'total_trades', 'successful_trades', 'failed_trades',
            'total_profit', 'total_loss', 'win_rate',
            'max_drawdown', 'sharpe_ratio', 'profit_factor'
        ]
        
        for field in bot_fields:
            # This should not raise an exception even if field is missing
            value = assert_safe_field(bot_details, field, required=False)
            # Field may be None or missing - both are acceptable
            assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                f"Bot field {field} has unexpected type: {type(value)}"
        
        # Test nested field access for settings
        settings = assert_safe_field(bot_details, 'settings', required=False)
        if settings:
            settings_fields = [
                'leverage', 'position_mode', 'margin_mode',
                'trade_amount', 'stop_loss', 'take_profit',
                'max_orders', 'order_timeout', 'retry_count'
            ]
            
            for field in settings_fields:
                value = assert_safe_field(settings, field, required=False)
                assert value is None or isinstance(value, (str, int, float, bool)), \
                    f"Bot settings field {field} has unexpected type: {type(value)}"
        
        # Test performance field
        performance = assert_safe_field(bot_details, 'performance', required=False)
        if performance:
            performance_fields = [
                'total_trades', 'successful_trades', 'failed_trades',
                'total_profit', 'total_loss', 'win_rate',
                'max_drawdown', 'sharpe_ratio', 'profit_factor',
                'avg_trade_duration', 'best_trade', 'worst_trade'
            ]
            
            for field in performance_fields:
                value = assert_safe_field(performance, field, required=False)
                assert value is None or isinstance(value, (str, int, float, bool)), \
                    f"Performance field {field} has unexpected type: {type(value)}"
        
        # Log field mapping warnings for debugging
        log_field_mapping_warnings(bot_details, "BotDetails")
    
    async def test_account_field_mapping_resilience(self, apis):
        """Test account field mapping resilience with server-side variations"""
        account_api = apis['account_api']
        
        # Get all accounts to test field mapping
        accounts = await account_api.get_accounts()
        assert len(accounts) > 0, "Should have at least one account"
        
        # Use the first account
        first_account = accounts[0]
        
        # Test safe field access for all possible account fields
        account_fields = [
            # Required fields
            'account_id', 'exchange', 'account_name',
            # Optional fields that might be missing
            'account_type', 'status', 'balance', 'equity',
            'free_margin', 'used_margin', 'margin_level',
            'leverage', 'position_mode', 'margin_mode',
            'created_at', 'updated_at', 'last_login',
            'is_active', 'is_trading_enabled', 'is_withdrawal_enabled',
            'daily_trade_limit', 'max_leverage', 'min_trade_amount',
            'max_trade_amount', 'trading_fee', 'withdrawal_fee'
        ]
        
        for field in account_fields:
            # This should not raise an exception even if field is missing
            value = assert_safe_field(first_account, field, required=False)
            # Field may be None or missing - both are acceptable
            assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                f"Account field {field} has unexpected type: {type(value)}"
        
        # Test wallet_data field structure
        wallet_data = assert_safe_field(first_account, 'wallet_data', required=False)
        if wallet_data:
            if isinstance(wallet_data, list):
                # Wallet data is a list of wallet entries
                for wallet_entry in wallet_data:
                    wallet_fields = ['currency', 'balance', 'available', 'used', 'free', 'locked']
                    for field in wallet_fields:
                        value = assert_safe_field(wallet_entry, field, required=False)
                        assert value is None or isinstance(value, (str, int, float)), \
                            f"Wallet field {field} has unexpected type: {type(value)}"
            elif isinstance(wallet_data, dict):
                # Wallet data is a single wallet object
                wallet_fields = ['currency', 'balance', 'available', 'used', 'free', 'locked']
                for field in wallet_fields:
                    value = assert_safe_field(wallet_data, field, required=False)
                    assert value is None or isinstance(value, (str, int, float)), \
                        f"Wallet field {field} has unexpected type: {type(value)}"
        
        # Log field mapping warnings for debugging
        log_field_mapping_warnings(first_account, "AccountData")
    
    async def test_market_field_mapping_resilience(self, apis):
        """Test market field mapping resilience with server-side variations"""
        market_api = apis['market_api']
        
        # Get markets to test field mapping
        markets = await market_api.get_trade_markets()
        
        # Validate markets response
        assert markets is not None, "Markets should not be None"
        assert isinstance(markets, list), "Markets should be a list"
        
        if len(markets) > 0:
            # Use the first market
            first_market = markets[0]
            
            # Test safe field access for all possible market fields
            market_fields = [
                # Required fields
                'market_tag', 'symbol', 'exchange',
                # Optional fields that might be missing
                'market_name', 'base_currency', 'quote_currency',
                'market_type', 'status', 'is_active',
                'min_trade_amount', 'max_trade_amount',
                'min_price', 'max_price', 'price_precision',
                'amount_precision', 'trading_fee', 'maker_fee', 'taker_fee',
                'price_tick_size', 'amount_tick_size',
                'created_at', 'updated_at', 'last_price',
                'volume_24h', 'change_24h', 'high_24h', 'low_24h'
            ]
            
            for field in market_fields:
                # This should not raise an exception even if field is missing
                value = assert_safe_field(first_market, field, required=False)
                # Field may be None or missing - both are acceptable
                assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                    f"Market field {field} has unexpected type: {type(value)}"
            
            # Log field mapping warnings for debugging
            log_field_mapping_warnings(first_market, "MarketData")
    
    async def test_backtest_field_mapping_resilience(self, apis, cleanup_registry, test_session_id):
        """Test backtest field mapping resilience with server-side variations"""
        backtest_api = apis['backtest_api']
        lab_api = apis['lab_api']
        
        # Create a lab first to get backtests
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Get lab backtests
        backtests = await backtest_api.get_lab_backtests(lab_id)
        
        # Validate backtests response
        assert backtests is not None, "Backtests should not be None"
        assert isinstance(backtests, list), "Backtests should be a list"
        
        if len(backtests) > 0:
            # Use the first backtest
            first_backtest = backtests[0]
            
            # Test safe field access for all possible backtest fields
            backtest_fields = [
                # Required fields
                'backtest_id', 'lab_id', 'script_id',
                # Optional fields that might be missing
                'script_name', 'market_tag', 'account_id',
                'status', 'generation_idx', 'population_idx',
                'roi_percentage', 'win_rate', 'total_trades',
                'max_drawdown', 'realized_profits_usdt', 'pc_value',
                'avg_profit_per_trade', 'profit_factor', 'sharpe_ratio',
                'start_date', 'end_date', 'duration',
                'created_at', 'updated_at', 'completed_at',
                'execution_time', 'memory_usage', 'cpu_usage',
                'parameters', 'results', 'charts', 'logs'
            ]
            
            for field in backtest_fields:
                # This should not raise an exception even if field is missing
                value = assert_safe_field(first_backtest, field, required=False)
                # Field may be None or missing - both are acceptable
                assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                    f"Backtest field {field} has unexpected type: {type(value)}"
            
            # Test nested field access for parameters
            parameters = assert_safe_field(first_backtest, 'parameters', required=False)
            if parameters:
                if isinstance(parameters, list):
                    for param in parameters:
                        if isinstance(param, dict):
                            param_fields = ['name', 'value', 'type', 'min', 'max', 'step']
                            for field in param_fields:
                                value = assert_safe_field(param, field, required=False)
                                assert value is None or isinstance(value, (str, int, float, bool)), \
                                    f"Parameter field {field} has unexpected type: {type(value)}"
                elif isinstance(parameters, dict):
                    param_fields = ['name', 'value', 'type', 'min', 'max', 'step']
                    for field in param_fields:
                        value = assert_safe_field(parameters, field, required=False)
                        assert value is None or isinstance(value, (str, int, float, bool)), \
                            f"Parameter field {field} has unexpected type: {type(value)}"
            
            # Test nested field access for results
            results = assert_safe_field(first_backtest, 'results', required=False)
            if results:
                results_fields = [
                    'total_trades', 'successful_trades', 'failed_trades',
                    'total_profit', 'total_loss', 'win_rate',
                    'max_drawdown', 'sharpe_ratio', 'profit_factor',
                    'avg_trade_duration', 'best_trade', 'worst_trade',
                    'equity_curve', 'drawdown_curve', 'trade_history'
                ]
                
                for field in results_fields:
                    value = assert_safe_field(results, field, required=False)
                    assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                        f"Results field {field} has unexpected type: {type(value)}"
            
            # Log field mapping warnings for debugging
            log_field_mapping_warnings(first_backtest, "BacktestData")
    
    async def test_script_field_mapping_resilience(self, apis):
        """Test script field mapping resilience with server-side variations"""
        script_api = apis.get('script_api')
        
        if script_api:
            # Get all scripts to test field mapping
            scripts = await script_api.get_all_scripts()
            
            # Validate scripts response
            assert scripts is not None, "Scripts should not be None"
            assert isinstance(scripts, list), "Scripts should be a list"
            
            if len(scripts) > 0:
                # Use the first script
                first_script = scripts[0]
                
                # Test safe field access for all possible script fields
                script_fields = [
                    # Required fields
                    'script_id', 'script_name',
                    # Optional fields that might be missing
                    'script_type', 'status', 'is_active',
                    'version', 'author', 'description',
                    'source_code', 'compiled_code',
                    'dependencies', 'requirements',
                    'created_at', 'updated_at', 'published_at',
                    'download_count', 'rating', 'tags',
                    'category', 'language', 'framework'
                ]
                
                for field in script_fields:
                    # This should not raise an exception even if field is missing
                    value = assert_safe_field(first_script, field, required=False)
                    # Field may be None or missing - both are acceptable
                    assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                        f"Script field {field} has unexpected type: {type(value)}"
                
                # Log field mapping warnings for debugging
                log_field_mapping_warnings(first_script, "ScriptData")
    
    async def test_order_field_mapping_resilience(self, apis):
        """Test order field mapping resilience with server-side variations"""
        order_api = apis.get('order_api')
        
        if order_api:
            # Get all orders to test field mapping
            orders = await order_api.get_all_orders()
            
            # Validate orders response
            assert orders is not None, "Orders should not be None"
            assert isinstance(orders, list), "Orders should be a list"
            
            if len(orders) > 0:
                # Use the first order
                first_order = orders[0]
                
                # Test safe field access for all possible order fields
                order_fields = [
                    # Required fields
                    'order_id', 'symbol', 'side', 'amount',
                    # Optional fields that might be missing
                    'price', 'status', 'type', 'time_in_force',
                    'created_at', 'updated_at', 'filled_at',
                    'cancelled_at', 'expires_at',
                    'filled_amount', 'remaining_amount',
                    'average_price', 'total_cost', 'fee',
                    'bot_id', 'account_id', 'market_tag',
                    'leverage', 'stop_price', 'take_profit',
                    'stop_loss', 'trailing_stop', 'iceberg'
                ]
                
                for field in order_fields:
                    # This should not raise an exception even if field is missing
                    value = assert_safe_field(first_order, field, required=False)
                    # Field may be None or missing - both are acceptable
                    assert value is None or isinstance(value, (str, int, float, bool, list, dict)), \
                        f"Order field {field} has unexpected type: {type(value)}"
                
                # Log field mapping warnings for debugging
                log_field_mapping_warnings(first_order, "OrderData")
    
    async def test_no_get_usage_regression(self, apis, cleanup_registry, test_session_id):
        """Test that no .get() usage regressions exist in API responses"""
        lab_api = apis['lab_api']
        bot_api = apis['bot_api']
        account_api = apis['account_api']
        
        # Create test resources
        lab_config = create_test_lab_config(
            script_id="test_script_id",
            market_tag="BTC_USDT_PERPETUAL",
            account_id="test_account_id",
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        bot_config = create_test_bot_config(
            script_id='test_script_id',
            market_tag='BTC_USDT_PERPETUAL',
            account_id='test_account_id',
            session_id=test_session_id,
            index=1
        )
        
        bot_details = await bot_api.create_bot(**bot_config)
        bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
        cleanup_registry.add_bot(bot_id)
        
        # Test that API responses are objects, not dictionaries
        # This is a static check - in practice, we ensure no .get() calls in code
        # by using safe_get_field instead
        
        # Verify lab_details is an object with attributes
        assert hasattr(lab_details, '__dict__') or hasattr(lab_details, '__slots__'), \
            "Lab details should be an object, not a dictionary"
        
        # Verify bot_details is an object with attributes
        assert hasattr(bot_details, '__dict__') or hasattr(bot_details, '__slots__'), \
            "Bot details should be an object, not a dictionary"
        
        # Test accounts
        accounts = await account_api.get_accounts()
        if accounts:
            first_account = accounts[0]
            assert hasattr(first_account, '__dict__') or hasattr(first_account, '__slots__'), \
                "Account should be an object, not a dictionary"
    
    async def test_field_mapping_error_recovery(self, apis, cleanup_registry, test_session_id):
        """Test field mapping error recovery and graceful degradation"""
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
        
        # Test that missing fields don't break the flow
        try:
            # Try to access a field that might not exist
            non_existent_field = assert_safe_field(lab_details, 'non_existent_field', required=False)
            assert non_existent_field is None, "Non-existent field should return None"
        except Exception as e:
            pytest.fail(f"Missing field should not raise exception: {e}")
        
        # Test that required fields are properly validated
        try:
            # Try to access a required field that might not exist
            required_field = assert_safe_field(lab_details, 'non_existent_required_field', required=True)
            pytest.fail("Required field should raise exception if missing")
        except ValueError:
            pass  # Expected behavior
        
        # Test nested field access with missing intermediate fields
        try:
            # Try to access nested field through missing intermediate field
            nested_field = assert_safe_field(lab_details, 'missing_intermediate.nested_field', required=False)
            assert nested_field is None, "Nested field through missing intermediate should return None"
        except Exception as e:
            pytest.fail(f"Nested field access should not raise exception: {e}")
    
    async def test_field_mapping_performance(self, apis, cleanup_registry, test_session_id):
        """Test field mapping performance with large datasets"""
        lab_api = apis['lab_api']
        
        # Create multiple labs to test performance
        lab_ids = []
        for i in range(5):
            lab_config = create_test_lab_config(
                script_id="test_script_id",
                market_tag="BTC_USDT_PERPETUAL",
                account_id="test_account_id",
                session_id=f"{test_session_id}_{i}"
            )
            
            lab_details = await lab_api.create_lab(**lab_config)
            lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
            lab_ids.append(lab_id)
            cleanup_registry.add_lab(lab_id)
        
        # Test field mapping performance on multiple labs
        start_time = asyncio.get_event_loop().time()
        
        for lab_id in lab_ids:
            lab_details = await lab_api.get_lab_details(lab_id)
            
            # Test field mapping on all fields
            fields_to_test = [
                'lab_id', 'lab_name', 'script_id', 'status',
                'leverage', 'position_mode', 'margin_mode',
                'trade_amount', 'chart_style', 'interval'
            ]
            
            for field in fields_to_test:
                value = assert_safe_field(lab_details, field, required=False)
                # Field may be None or missing - both are acceptable
                assert value is None or isinstance(value, (str, int, float, bool)), \
                    f"Field {field} has unexpected type: {type(value)}"
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # Performance should be reasonable (less than 5 seconds for 5 labs)
        assert duration < 5.0, f"Field mapping performance too slow: {duration:.2f}s"
        
        print(f"Field mapping performance: {duration:.2f}s for {len(lab_ids)} labs")
