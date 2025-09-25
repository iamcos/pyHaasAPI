"""
Test suite for pyHaasAPI v2

This module provides comprehensive testing for all pyHaasAPI v2 components
including unit tests, integration tests, and performance tests.
"""

from .conftest import *
from .test_core import *
from .test_api import *
from .test_services import *
from .test_tools import *
from .test_cli import *

__all__ = [
    # Test configuration
    "pytest_configure",
    "pytest_collection_modifyitems",
    
    # Core tests
    "TestAsyncClient",
    "TestAuthenticationManager", 
    "TestTypeValidation",
    "TestAsyncUtils",
    
    # API tests
    "TestLabAPI",
    "TestBotAPI",
    "TestAccountAPI",
    "TestScriptAPI",
    "TestMarketAPI",
    "TestBacktestAPI",
    "TestOrderAPI",
    
    # Service tests
    "TestLabService",
    "TestBotService",
    "TestAnalysisService",
    "TestReportingService",
    
    # Tools tests
    "TestDataDumper",
    "TestTestingManager",
    
    # CLI tests
    "TestBaseCLI",
    "TestLabCLI",
    "TestBotCLI",
    "TestAnalysisCLI",
]