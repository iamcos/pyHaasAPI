"""
Final working unit tests for Pydantic models.
Tests the actual API structure with correct field usage and validation.
"""

import pytest
from datetime import datetime
from pyHaasAPI.models.lab import LabDetails, LabConfig, LabParameter, LabRecord, LabSettings
from pyHaasAPI.models.bot import BotDetails, BotConfiguration, BotRecord
from pyHaasAPI.models.common import ApiResponse, PaginatedResponse, ErrorResponse


class TestLabConfig:
    """Test LabConfig model - works with field names."""
    
    def test_lab_config_creation(self):
        """Test LabConfig model creation."""
        config = LabConfig(
            max_parallel=10,
            max_generations=30,
            max_epochs=3,
            max_runtime=3600,
            auto_restart=1
        )
        
        assert config.max_parallel == 10
        assert config.max_generations == 30
        assert config.max_epochs == 3
        assert config.max_runtime == 3600
        assert config.auto_restart == 1
    
    def test_lab_config_defaults(self):
        """Test LabConfig with default values."""
        config = LabConfig()
        
        assert config.max_parallel == 10
        assert config.max_generations == 30
        assert config.max_epochs == 3
        assert config.max_runtime == 0
        assert config.auto_restart == 0
    
    def test_lab_config_validation_errors(self):
        """Test LabConfig validation errors."""
        with pytest.raises(ValueError):
            LabConfig(max_parallel=0)  # Should be positive
        
        with pytest.raises(ValueError):
            LabConfig(max_generations=-1)  # Should be positive
        
        with pytest.raises(ValueError):
            LabConfig(max_epochs=0)  # Should be positive
        
        with pytest.raises(ValueError):
            LabConfig(max_runtime=-1)  # Should be non-negative
        
        with pytest.raises(ValueError):
            LabConfig(auto_restart=-1)  # Should be non-negative


class TestLabSettings:
    """Test LabSettings model - uses aliases."""
    
    def test_lab_settings_creation_with_aliases(self):
        """Test LabSettings creation using aliases."""
        settings = LabSettings(
            accountId="account123",  # Using alias
            marketTag="BTC_USDT",   # Using alias
            interval=1,
            tradeAmount=100.0,      # Using alias
            chartStyle=300,         # Using alias
            orderTemplate=500,      # Using alias
            leverage=20.0,
            positionMode=1,        # Using alias
            marginMode=0           # Using alias
        )
        
        assert settings.account_id == "account123"
        assert settings.market_tag == "BTC_USDT"
        assert settings.interval == 1
        assert settings.trade_amount == 100.0
        assert settings.chart_style == 300
        assert settings.order_template == 500
        assert settings.leverage == 20.0
        assert settings.position_mode == 1
        assert settings.margin_mode == 0
    
    def test_lab_settings_defaults(self):
        """Test LabSettings with default values."""
        settings = LabSettings(
            accountId="account123",
            marketTag="BTC_USDT"
        )
        
        assert settings.account_id == "account123"
        assert settings.market_tag == "BTC_USDT"
        assert settings.interval == 1  # Default
        assert settings.trade_amount == 100.0  # Default
        assert settings.chart_style == 300  # Default
        assert settings.order_template == 500  # Default
        assert settings.leverage == 0.0  # Default
        assert settings.position_mode == 0  # Default
        assert settings.margin_mode == 0  # Default


class TestLabParameter:
    """Test LabParameter model - uses aliases."""
    
    def test_lab_parameter_creation_with_aliases(self):
        """Test LabParameter creation using aliases."""
        param = LabParameter(
            key="test_param",
            value=10.5,
            type=1,  # Using alias
            options=[1, 2, 3],
            included=True,  # Using alias
            selected=False  # Using alias
        )
        
        assert param.key == "test_param"
        assert param.value == 10.5
        assert param.param_type == 1
        assert param.options == [1, 2, 3]
        assert param.is_included is True
        assert param.is_selected is False
    
    def test_lab_parameter_validation_errors(self):
        """Test LabParameter validation errors."""
        with pytest.raises(ValueError):
            LabParameter(
                key="test_param",
                value=10.5,
                type=5  # Invalid type
            )


class TestLabRecord:
    """Test LabRecord model - uses aliases."""
    
    def test_lab_record_creation_with_aliases(self):
        """Test LabRecord creation using aliases."""
        record = LabRecord(
            labId="lab123",  # Using alias
            name="Test Lab",
            scriptId="script456",  # Using alias
            scriptName="Test Script",  # Using alias
            accountId="account789",  # Using alias
            marketTag="BTC_USDT",  # Using alias
            status="ACTIVE",
            createdAt=datetime.now(),  # Using alias
            backtestCount=5  # Using alias
        )
        
        assert record.lab_id == "lab123"
        assert record.name == "Test Lab"
        assert record.script_id == "script456"
        assert record.script_name == "Test Script"
        assert record.account_id == "account789"
        assert record.market_tag == "BTC_USDT"
        assert record.status == "ACTIVE"
        assert record.backtest_count == 5


class TestLabDetails:
    """Test LabDetails model - uses aliases."""
    
    def test_lab_details_creation(self):
        """Test LabDetails model creation."""
        # Create required settings and config
        settings = LabSettings(
            accountId="account123",
            marketTag="BTC_USDT"
        )
        config = LabConfig(
            max_parallel=10,
            max_generations=30,
            max_epochs=3
        )
        
        lab = LabDetails(
            labId="lab123",  # Using alias
            name="Test Lab",
            scriptId="script456",  # Using alias
            scriptName="Test Script",  # Using alias
            settings=settings,
            config=config,
            status="ACTIVE",
            createdAt=datetime.now(),  # Using alias
            updatedAt=datetime.now()  # Using alias
        )
        
        assert lab.lab_id == "lab123"
        assert lab.name == "Test Lab"
        assert lab.script_id == "script456"
        assert lab.script_name == "Test Script"
        assert lab.settings is not None
        assert lab.config is not None
        assert lab.status == "ACTIVE"


class TestBotConfiguration:
    """Test BotConfiguration model - works with field names."""
    
    def test_bot_configuration_creation(self):
        """Test BotConfiguration model creation."""
        config = BotConfiguration(
            leverage=20.0,
            position_mode=1,
            margin_mode=0,
            trade_amount=2000.0,  # Default value
            interval=1,
            chart_style=300,
            order_template=500
        )
        
        assert config.leverage == 20.0
        assert config.position_mode == 1
        assert config.margin_mode == 0
        assert config.trade_amount == 2000.0
        assert config.interval == 1
        assert config.chart_style == 300
        assert config.order_template == 500


class TestBotRecord:
    """Test BotRecord model - uses aliases."""
    
    def test_bot_record_creation_with_aliases(self):
        """Test BotRecord creation using aliases."""
        record = BotRecord(
            botId="bot123",  # Using alias
            botName="Test Bot",  # Using alias
            scriptId="script456",  # Using alias
            scriptName="Test Script",  # Using alias
            accountId="account789",  # Using alias
            marketTag="BTC_USDT",  # Using alias
            status="ACTIVE",
            createdAt=datetime.now()  # Using alias
        )
        
        assert record.bot_id == "bot123"
        assert record.bot_name == "Test Bot"
        assert record.script_id == "script456"
        assert record.script_name == "Test Script"
        assert record.account_id == "account789"
        assert record.market_tag == "BTC_USDT"
        assert record.status == "ACTIVE"


class TestBotDetails:
    """Test BotDetails model - uses aliases."""
    
    def test_bot_details_creation(self):
        """Test BotDetails model creation."""
        config = BotConfiguration(
            leverage=20.0,
            position_mode=1,
            margin_mode=0
        )
        
        bot = BotDetails(
            botId="bot123",  # Using alias
            botName="Test Bot",  # Using alias
            scriptId="script456",  # Using alias
            scriptName="Test Script",  # Using alias
            scriptVersion=1,  # Using alias - must be int
            accountId="account789",  # Using alias
            marketTag="BTC_USDT",  # Using alias
            configuration=config,
            status="ACTIVE",
            createdAt=datetime.now()  # Using alias
        )
        
        assert bot.bot_id == "bot123"
        assert bot.bot_name == "Test Bot"
        assert bot.script_id == "script456"
        assert bot.script_name == "Test Script"
        assert bot.script_version == 1
        assert bot.account_id == "account789"
        assert bot.market_tag == "BTC_USDT"
        assert bot.configuration is not None
        assert bot.status == "ACTIVE"


class TestApiResponse:
    """Test ApiResponse model - uses aliases."""
    
    def test_api_response_creation_with_aliases(self):
        """Test ApiResponse creation using aliases."""
        response = ApiResponse(
            Success=True,  # Using alias
            Error="",  # Using alias
            Data={"test": "value"}  # Using alias
        )
        
        assert response.success is True
        assert response.error == ""
        assert response.data == {"test": "value"}
        assert response.is_success is True
        assert response.is_error is False
    
    def test_api_response_error(self):
        """Test ApiResponse with error."""
        response = ApiResponse(
            Success=False,  # Using alias
            Error="Test error",  # Using alias
            Data=None  # Using alias
        )
        
        assert response.success is False
        assert response.error == "Test error"
        assert response.data is None
        assert response.is_success is False
        assert response.is_error is True


class TestPaginatedResponse:
    """Test PaginatedResponse model - uses aliases with correct validation."""
    
    def test_paginated_response_creation_with_aliases(self):
        """Test PaginatedResponse creation using aliases with correct validation."""
        # Create response where page < total_pages to satisfy validation
        response = PaginatedResponse(
            items=[{"id": 1}, {"id": 2}],
            totalCount=100,  # Using alias
            page=1,
            pageSize=10,  # Using alias
            totalPages=10,  # Using alias
            hasNext=True,  # Using alias - must be True when page < total_pages
            hasPrevious=False  # Using alias - must be False when page = 1
        )
        
        assert len(response.items) == 2
        assert response.total_count == 100
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_pages == 10
        assert response.has_next is True
        assert response.has_previous is False
    
    def test_paginated_response_validation(self):
        """Test PaginatedResponse validation rules."""
        # Test that has_next is calculated correctly
        response = PaginatedResponse(
            items=[{"id": 1}],
            totalCount=100,
            page=1,
            pageSize=10,
            totalPages=10,
            hasNext=True,  # Must be True when page < total_pages
            hasPrevious=False  # Must be False when page = 1
        )
        
        # The validation should pass because page < total_pages
        assert response.has_next is True


class TestErrorResponse:
    """Test ErrorResponse model - uses aliases with correct field names."""
    
    def test_error_response_creation_with_aliases(self):
        """Test ErrorResponse creation using aliases."""
        error = ErrorResponse(
            errorCode="400",  # Using alias - must be string
            errorMessage="Bad Request",  # Using alias
            errorDetails={"field": "value is required"}  # Using alias - correct field name
        )
        
        assert error.error_code == "400"
        assert error.error_message == "Bad Request"
        assert error.error_details == {"field": "value is required"}


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_lab_config_serialization(self):
        """Test LabConfig serialization."""
        config = LabConfig(
            max_parallel=10,
            max_generations=30,
            max_epochs=3
        )
        
        # Test serialization
        data = config.model_dump()
        assert isinstance(data, dict)
        assert data["max_parallel"] == 10
        assert data["max_generations"] == 30
        assert data["max_epochs"] == 3
    
    def test_lab_config_deserialization(self):
        """Test LabConfig deserialization."""
        data = {
            "max_parallel": 10,
            "max_generations": 30,
            "max_epochs": 3,
            "max_runtime": 3600,
            "auto_restart": 1
        }
        
        config = LabConfig(**data)
        assert config.max_parallel == 10
        assert config.max_generations == 30
        assert config.max_epochs == 3
        assert config.max_runtime == 3600
        assert config.auto_restart == 1
    
    def test_lab_settings_serialization_with_aliases(self):
        """Test LabSettings serialization with aliases."""
        settings = LabSettings(
            accountId="account123",
            marketTag="BTC_USDT"
        )
        
        # Test serialization with aliases
        data = settings.model_dump(by_alias=True)
        assert "accountId" in data
        assert "marketTag" in data
        assert data["accountId"] == "account123"
        assert data["marketTag"] == "BTC_USDT"
    
    def test_lab_settings_deserialization_with_aliases(self):
        """Test LabSettings deserialization with aliases."""
        data = {
            "accountId": "account123",
            "marketTag": "BTC_USDT",
            "interval": 1,
            "tradeAmount": 100.0
        }
        
        settings = LabSettings(**data)
        assert settings.account_id == "account123"
        assert settings.market_tag == "BTC_USDT"
        assert settings.interval == 1
        assert settings.trade_amount == 100.0


class TestModelValidation:
    """Test model validation and edge cases."""
    
    def test_lab_status_validation(self):
        """Test lab status validation."""
        # Valid statuses
        valid_statuses = ["ACTIVE", "COMPLETED", "RUNNING", "FAILED", "CANCELLED"]
        
        for status in valid_statuses:
            record = LabRecord(
                labId="lab123",
                name="Test Lab",
                scriptId="script456",
                scriptName="Test Script",
                accountId="account789",
                marketTag="BTC_USDT",
                status=status
            )
            assert record.status == status.upper()
    
    def test_lab_status_validation_error(self):
        """Test lab status validation error."""
        with pytest.raises(ValueError):
            LabRecord(
                labId="lab123",
                name="Test Lab",
                scriptId="script456",
                scriptName="Test Script",
                accountId="account789",
                marketTag="BTC_USDT",
                status="INVALID_STATUS"
            )
    
    def test_bot_configuration_validation(self):
        """Test bot configuration validation."""
        # Test valid configuration
        config = BotConfiguration(
            leverage=20.0,
            position_mode=1,
            margin_mode=0
        )
        
        assert config.leverage == 20.0
        assert config.position_mode == 1
        assert config.margin_mode == 0
    
    def test_bot_configuration_validation_errors(self):
        """Test bot configuration validation errors."""
        # Test leverage validation
        with pytest.raises(ValueError, match="Leverage must be positive"):
            BotConfiguration(leverage=-1.0)  # Should be positive
        
        with pytest.raises(ValueError, match="Leverage must be positive"):
            BotConfiguration(leverage=0.0)  # Should be positive
        
        # Test position mode validation
        with pytest.raises(ValueError, match="Position mode must be 0 \\(ONE_WAY\\) or 1 \\(HEDGE\\)"):
            BotConfiguration(position_mode=5)  # Should be 0 or 1
        
        # Test margin mode validation
        with pytest.raises(ValueError, match="Margin mode must be 0 \\(CROSS\\) or 1 \\(ISOLATED\\)"):
            BotConfiguration(margin_mode=5)  # Should be 0 or 1
        
        # Test trade amount validation
        with pytest.raises(ValueError, match="Trade amount must be positive"):
            BotConfiguration(trade_amount=-1.0)  # Should be positive
        
        with pytest.raises(ValueError, match="Trade amount must be positive"):
            BotConfiguration(trade_amount=0.0)  # Should be positive
        
        # Test interval validation
        with pytest.raises(ValueError, match="Value must be positive"):
            BotConfiguration(interval=0)  # Should be positive
        
        with pytest.raises(ValueError, match="Value must be positive"):
            BotConfiguration(interval=-1)  # Should be positive


class TestModelEdgeCases:
    """Test model edge cases and boundary conditions."""
    
    def test_lab_config_boundary_values(self):
        """Test LabConfig with boundary values."""
        # Test minimum valid values
        config = LabConfig(
            max_parallel=1,
            max_generations=1,
            max_epochs=1,
            max_runtime=0,
            auto_restart=0
        )
        
        assert config.max_parallel == 1
        assert config.max_generations == 1
        assert config.max_epochs == 1
        assert config.max_runtime == 0
        assert config.auto_restart == 0
    
    def test_lab_settings_boundary_values(self):
        """Test LabSettings with boundary values."""
        settings = LabSettings(
            accountId="a",  # Minimum length
            marketTag="BTC_USDT",
            interval=0,  # Minimum value
            tradeAmount=0.0,  # Minimum value
            chartStyle=0,  # Minimum value
            orderTemplate=0,  # Minimum value
            leverage=0.0,  # Minimum value
            positionMode=0,  # Minimum value
            marginMode=0  # Minimum value
        )
        
        assert settings.account_id == "a"
        assert settings.market_tag == "BTC_USDT"
        assert settings.interval == 0
        assert settings.trade_amount == 0.0
        assert settings.chart_style == 0
        assert settings.order_template == 0
        assert settings.leverage == 0.0
        assert settings.position_mode == 0
        assert settings.margin_mode == 0
    
    def test_bot_configuration_boundary_values(self):
        """Test BotConfiguration with boundary values."""
        config = BotConfiguration(
            leverage=0.1,  # Smallest positive value
            position_mode=0,  # Minimum value
            margin_mode=0,  # Minimum value
            trade_amount=0.01,  # Smallest positive value
            interval=1,  # Smallest positive value
            chart_style=0,  # Minimum value
            order_template=0  # Minimum value
        )
        
        assert config.leverage == 0.1
        assert config.position_mode == 0
        assert config.margin_mode == 0
        assert config.trade_amount == 0.01
        assert config.interval == 1
        assert config.chart_style == 0
        assert config.order_template == 0

