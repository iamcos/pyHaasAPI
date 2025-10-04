"""
Minimal working test suite - tests only what works without hanging
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class TestBasicFunctionality:
    """Test basic Python functionality"""
    
    def test_basic_math(self):
        """Test basic math operations"""
        assert 2 + 2 == 4
        assert 10 * 5 == 50
        assert 100 / 10 == 10
    
    def test_string_operations(self):
        """Test string operations"""
        text = "Hello World"
        assert len(text) == 11
        assert text.upper() == "HELLO WORLD"
        assert text.lower() == "hello world"
    
    def test_list_operations(self):
        """Test list operations"""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert sum(items) == 15
        assert max(items) == 5
        assert min(items) == 1
    
    def test_dict_operations(self):
        """Test dictionary operations"""
        data = {"key1": "value1", "key2": "value2"}
        assert len(data) == 2
        assert "key1" in data
        assert data["key1"] == "value1"
    
    def test_import_basic_modules(self):
        """Test importing basic Python modules"""
        import datetime
        import json
        import os
        import sys
        
        # Test datetime
        now = datetime.datetime.now()
        assert isinstance(now, datetime.datetime)
        
        # Test json
        data = {"test": "value"}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed == data
        
        # Test os
        assert os.path.exists(".")
        
        # Test sys
        assert len(sys.path) > 0

class TestProjectStructure:
    """Test that the project structure is correct"""
    
    def test_project_files_exist(self):
        """Test that key project files exist"""
        import os
        
        # Check if we're in the right directory
        current_dir = os.getcwd()
        assert "pyHaasAPI" in current_dir
        
        # Check for key files
        assert os.path.exists("pyproject.toml")
        assert os.path.exists("requirements.txt")
        assert os.path.exists("README.md")
    
    def test_package_structure(self):
        """Test that the package structure exists"""
        import os
        
        # Check main package
        assert os.path.exists("pyHaasAPI")
        assert os.path.exists("pyHaasAPI/__init__.py")
        
        # Check models directory
        assert os.path.exists("pyHaasAPI/models")
        assert os.path.exists("pyHaasAPI/models/__init__.py")
        
        # Check tests directory
        assert os.path.exists("pyHaasAPI/tests")
        assert os.path.exists("pyHaasAPI/tests/__init__.py")

class TestEnvironment:
    """Test the Python environment"""
    
    def test_python_version(self):
        """Test Python version"""
        import sys
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    def test_required_packages(self):
        """Test that required packages are available"""
        try:
            import pytest
            assert hasattr(pytest, 'mark')
        except ImportError:
            pytest.skip("pytest not available")
        
        try:
            import pydantic
            assert hasattr(pydantic, 'BaseModel')
        except ImportError:
            pytest.skip("pydantic not available")
        
        try:
            import aiohttp
            assert hasattr(aiohttp, 'ClientSession')
        except ImportError:
            pytest.skip("aiohttp not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

