import pytest
from .test_utils import TestLogger

@pytest.fixture
def logger():
    return TestLogger() 