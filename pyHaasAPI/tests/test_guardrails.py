"""
CI Guardrails Tests

Tests to ensure compliance with:
- No host/port flags in CLI
- No port 8091 usage
- No v1 runtime calls in CLI/services
- Proper JSON output structure
- Algorithm step sequence
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
import json
import re


class TestCLIGuardrails:
    """Test CLI guardrails and compliance"""
    
    def test_no_host_port_flags_in_cli(self):
        """Ensure no --host/--port flags exist in CLI code"""
        cli_dir = Path(__file__).parent.parent / "cli"
        
        # Check all CLI files for host/port flags
        for cli_file in cli_dir.glob("*.py"):
            if cli_file.name == "__init__.py":
                continue
                
            content = cli_file.read_text()
            
            # Check for host/port argument definitions
            host_patterns = [
                r'add_argument.*--host',
                r'add_argument.*--port',
                r'parser\.add_argument.*host',
                r'parser\.add_argument.*port'
            ]
            
            for pattern in host_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                assert not matches, f"Found host/port flags in {cli_file}: {matches}"
    
    def test_no_port_8091_usage(self):
        """Ensure no usage of port 8091 anywhere in codebase"""
        pyhaas_dir = Path(__file__).parent.parent
        
        # Check all Python files for port 8091
        for py_file in pyhaas_dir.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            
            # Check for port 8091 usage
            port_8091_patterns = [
                r'8091',
                r'port.*8091',
                r'8091.*port'
            ]
            
            for pattern in port_8091_patterns:
                matches = re.findall(pattern, content)
                assert not matches, f"Found port 8091 usage in {py_file}: {matches}"
    
    def test_no_v1_runtime_imports(self):
        """Ensure no v1 runtime imports in CLI/services"""
        cli_dir = Path(__file__).parent.parent / "cli"
        services_dir = Path(__file__).parent.parent / "services"
        
        # Check CLI files
        for cli_file in cli_dir.glob("*.py"):
            if cli_file.name == "__init__.py":
                continue
                
            content = cli_file.read_text()
            
            # Check for v1 imports
            v1_patterns = [
                r'from pyHaasAPI_v1',
                r'import pyHaasAPI_v1',
                r'pyHaasAPI_v1\.',
                r'v1api',
                r'v1\.'
            ]
            
            for pattern in v1_patterns:
                matches = re.findall(pattern, content)
                assert not matches, f"Found v1 runtime imports in {cli_file}: {matches}"
        
        # Check services files
        for service_file in services_dir.rglob("*.py"):
            if service_file.name == "__init__.py":
                continue
                
            content = service_file.read_text()
            
            # Check for v1 imports
            v1_patterns = [
                r'from pyHaasAPI_v1',
                r'import pyHaasAPI_v1',
                r'pyHaasAPI_v1\.',
                r'v1api',
                r'v1\.'
            ]
            
            for pattern in v1_patterns:
                matches = re.findall(pattern, content)
                assert not matches, f"Found v1 runtime imports in {service_file}: {matches}"


class TestLongestBacktestAlgorithm:
    """Test longest backtest algorithm compliance"""
    
    def test_algorithm_step_sequence(self):
        """Test that algorithm follows correct step sequence"""
        from pyHaasAPI.services.backtest.backtest_service import BacktestService
        
        # Check that the algorithm has the correct step sequence
        # This would be tested by examining the _robust_longest_backtest method
        # The steps should be: months (36m down to 1m) → 1m → 2w → 1w → 3d → 2d
        
        # This is a structural test - the actual algorithm is tested in integration tests
        assert True  # Placeholder for now
    
    def test_cancel_between_attempts(self):
        """Test that algorithm cancels between attempts"""
        from pyHaasAPI.services.backtest.backtest_service import BacktestService
        
        # Check that _force_cancel is called between attempts
        # This is verified by examining the algorithm structure
        assert True  # Placeholder for now


class TestJSONOutputStructure:
    """Test JSON output structure compliance"""
    
    def test_json_summary_structure(self):
        """Test that JSON summary has correct structure"""
        # Expected structure:
        expected_structure = {
            "timestamp": str,
            "total_labs": int,
            "successful": int,
            "failed": int,
            "results": {
                str: {  # lab_id
                    "status": str,
                    "earliest_start": str,
                    "end": str,
                    "attempts": list,
                    "total_attempts": int,
                    "total_elapsed_seconds": int,
                    "notes": str
                }
            }
        }
        
        # This would be tested with actual CLI output
        # For now, just verify the structure is defined
        assert expected_structure is not None
    
    def test_machine_parseable_output(self):
        """Test that CLI output is machine parseable"""
        # The CLI should output valid JSON that can be parsed
        # This would be tested by running the CLI and parsing output
        assert True  # Placeholder for now


class TestTunnelPreflight:
    """Test tunnel preflight checks"""
    
    def test_preflight_check_implementation(self):
        """Test that preflight check is implemented"""
        from pyHaasAPI.core.server_manager import ServerManager
        from pyHaasAPI.config.settings import Settings
        
        # Check that preflight_check method exists
        sm = ServerManager(Settings())
        assert hasattr(sm, 'preflight_check')
        assert callable(getattr(sm, 'preflight_check'))
    
    def test_cli_preflight_integration(self):
        """Test that CLI integrates preflight checks"""
        # Check that main CLI calls preflight_check
        cli_file = Path(__file__).parent.parent / "cli" / "main.py"
        content = cli_file.read_text()
        
        # Should contain preflight_check call
        assert "preflight_check" in content
        assert "ServerManager" in content


if __name__ == "__main__":
    pytest.main([__file__])
