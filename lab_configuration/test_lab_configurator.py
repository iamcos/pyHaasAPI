#!/usr/bin/env python3
"""
Test Lab Configuration System
This module provides comprehensive tests for the lab configuration system.
"""

import unittest
import time
from lab_configurator import (
    LabConfigurator, LabConfiguration, LabAlgorithm, LabStatus,
    LabAlgorithmConfig, LabExecutionConfig, LabMarketConfig, LabAccountConfig
)

class TestLabConfigurator(unittest.TestCase):
    """Test cases for LabConfigurator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.configurator = LabConfigurator()
        self.configurator.register_server_config("test-srv01", 50, 5)
        self.configurator.register_server_config("test-srv02", 30, 3)
    
    def test_template_initialization(self):
        """Test that templates are properly initialized"""
        templates = self.configurator.templates
        self.assertIn("standard", templates)
        self.assertIn("high_frequency", templates)
        self.assertIn("extended", templates)
        self.assertIn("futures", templates)
        
        # Test template properties
        standard = templates["standard"]
        self.assertEqual(standard.default_algorithm_config.max_population, 50)
        
        hf = templates["high_frequency"]
        self.assertEqual(hf.default_algorithm_config.max_population, 30)
        self.assertEqual(hf.default_market_config.interval, 1)
    
    def test_create_standard_configuration(self):
        """Test creating a standard lab configuration"""
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-001",
            lab_name="Test Lab",
            script_id="script-123",
            server_id="test-srv01",
            market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
            exchange_code="BINANCEFUTURES",
            account_id="account-456"
        )
        
        self.assertIsInstance(config, LabConfiguration)
        self.assertEqual(config.lab_id, "test-lab-001")
        self.assertEqual(config.lab_name, "Test Lab")
        self.assertEqual(config.script_id, "script-123")
        self.assertEqual(config.server_id, "test-srv01")
        self.assertEqual(config.market_config.market_tag, "BINANCEFUTURES_BTC_USDT_PERPETUAL")
        self.assertEqual(config.market_config.exchange_code, "BINANCEFUTURES")
        self.assertEqual(config.account_config.account_id, "account-456")
        self.assertEqual(config.status, LabStatus.CREATED)
        
        # Check that configuration is stored
        self.assertIn("test-lab-001", self.configurator.configurations)
    
    def test_create_configuration_with_overrides(self):
        """Test creating configuration with parameter overrides"""
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-002",
            lab_name="Custom Lab",
            script_id="script-456",
            server_id="test-srv01",
            market_tag="BINANCE_ETH_USDT",
            exchange_code="BINANCE",
            account_id="account-789",
            max_population=25,
            max_generations=75,
            trade_amount=200.0,
            leverage=10.0
        )
        
        self.assertEqual(config.algorithm_config.max_population, 25)
        self.assertEqual(config.algorithm_config.max_generations, 75)
        self.assertEqual(config.account_config.trade_amount, 200.0)
        self.assertEqual(config.market_config.leverage, 10.0)
    
    def test_server_limits_enforcement(self):
        """Test that server limits are enforced"""
        # Create config for server with 30 max population
        config = self.configurator.create_lab_configuration(
            template_name="extended",  # Default 100 population
            lab_id="test-lab-003",
            lab_name="Limited Lab",
            script_id="script-789",
            server_id="test-srv02",  # Max 30 population
            market_tag="BINANCE_BTC_USDT",
            exchange_code="BINANCE",
            account_id="account-123"
        )
        
        # Should be limited to server max
        self.assertEqual(config.algorithm_config.max_population, 30)
    
    def test_update_configuration(self):
        """Test updating existing configuration"""
        # Create initial configuration
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-004",
            lab_name="Update Test Lab",
            script_id="script-update",
            server_id="test-srv01",
            market_tag="BINANCE_ADA_USDT",
            exchange_code="BINANCE",
            account_id="account-update"
        )
        
        initial_modified = config.last_modified
        time.sleep(0.01)  # Ensure time difference
        
        # Update configuration
        updated_config = self.configurator.update_lab_configuration(
            "test-lab-004",
            lab_name="Updated Lab Name",
            algorithm_max_population=40,
            market_leverage=5.0,
            account_trade_amount=150.0
        )
        
        self.assertIsNotNone(updated_config)
        self.assertEqual(updated_config.lab_name, "Updated Lab Name")
        self.assertEqual(updated_config.algorithm_config.max_population, 40)
        self.assertEqual(updated_config.market_config.leverage, 5.0)
        self.assertEqual(updated_config.account_config.trade_amount, 150.0)
        self.assertGreater(updated_config.last_modified, initial_modified)
    
    def test_configure_algorithm(self):
        """Test configuring lab algorithm"""
        # Create configuration
        self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-005",
            lab_name="Algorithm Test Lab",
            script_id="script-algo",
            server_id="test-srv01",
            market_tag="BINANCE_DOT_USDT",
            exchange_code="BINANCE",
            account_id="account-algo"
        )
        
        # Configure algorithm
        success = self.configurator.configure_lab_algorithm(
            "test-lab-005",
            LabAlgorithm.BRUTE_FORCE,
            max_possibilities=2000,
            max_generations=150
        )
        
        self.assertTrue(success)
        
        config = self.configurator.get_lab_configuration("test-lab-005")
        self.assertEqual(config.algorithm_config.algorithm, LabAlgorithm.BRUTE_FORCE)
        self.assertEqual(config.algorithm_config.max_possibilities, 2000)
        self.assertEqual(config.algorithm_config.max_generations, 150)
    
    def test_update_market(self):
        """Test updating lab market configuration"""
        # Create configuration
        self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-006",
            lab_name="Market Test Lab",
            script_id="script-market",
            server_id="test-srv01",
            market_tag="BINANCE_BTC_USDT",
            exchange_code="BINANCE",
            account_id="account-market"
        )
        
        # Update market
        success = self.configurator.update_lab_market(
            "test-lab-006",
            "BINANCEFUTURES_ETH_USDT_PERPETUAL",
            "BINANCEFUTURES"
        )
        
        self.assertTrue(success)
        
        config = self.configurator.get_lab_configuration("test-lab-006")
        self.assertEqual(config.market_config.market_tag, "BINANCEFUTURES_ETH_USDT_PERPETUAL")
        self.assertEqual(config.market_config.exchange_code, "BINANCEFUTURES")
    
    def test_set_execution_timeframe(self):
        """Test setting lab execution timeframe"""
        # Create configuration
        self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-007",
            lab_name="Timeframe Test Lab",
            script_id="script-time",
            server_id="test-srv01",
            market_tag="BINANCE_LTC_USDT",
            exchange_code="BINANCE",
            account_id="account-time"
        )
        
        # Set timeframe
        start_time = int(time.time()) - 86400 * 365  # 1 year ago
        end_time = int(time.time())
        
        success = self.configurator.set_lab_execution_timeframe(
            "test-lab-007",
            start_time,
            end_time,
            send_email=True,
            priority=2
        )
        
        self.assertTrue(success)
        
        config = self.configurator.get_lab_configuration("test-lab-007")
        self.assertEqual(config.execution_config.start_unix, start_time)
        self.assertEqual(config.execution_config.end_unix, end_time)
        self.assertTrue(config.execution_config.send_email)
        self.assertEqual(config.execution_config.priority, 2)
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        # Create valid configuration
        self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-008",
            lab_name="Validation Test Lab",
            script_id="script-valid",
            server_id="test-srv01",
            market_tag="BINANCE_XRP_USDT",
            exchange_code="BINANCE",
            account_id="account-valid"
        )
        
        # Test valid configuration
        is_valid, issues = self.configurator.validate_configuration("test-lab-008")
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
        
        # Create invalid configuration
        config = self.configurator.get_lab_configuration("test-lab-008")
        config.algorithm_config.max_population = -5  # Invalid
        config.execution_config.start_unix = config.execution_config.end_unix + 1000  # Invalid
        config.market_config.market_tag = ""  # Invalid
        config.account_config.trade_amount = -100  # Invalid
        
        is_valid, issues = self.configurator.validate_configuration("test-lab-008")
        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)
        
        # Check specific issues
        issue_text = " ".join(issues)
        self.assertIn("population", issue_text.lower())
        self.assertIn("time", issue_text.lower())
        self.assertIn("market", issue_text.lower())
        self.assertIn("amount", issue_text.lower())
    
    def test_export_import_configuration(self):
        """Test configuration export and import"""
        # Create configuration
        original_config = self.configurator.create_lab_configuration(
            template_name="futures",
            lab_id="test-lab-009",
            lab_name="Export Test Lab",
            script_id="script-export",
            server_id="test-srv01",
            market_tag="BINANCEFUTURES_BNB_USDT_PERPETUAL",
            exchange_code="BINANCEFUTURES",
            account_id="account-export",
            leverage=15.0
        )
        
        # Export configuration
        exported = self.configurator.export_configuration("test-lab-009")
        self.assertIsNotNone(exported)
        self.assertIsInstance(exported, dict)
        self.assertEqual(exported['lab_id'], "test-lab-009")
        self.assertEqual(exported['lab_name'], "Export Test Lab")
        
        # Import configuration with new ID
        exported['lab_id'] = "test-lab-010"
        exported['lab_name'] = "Imported Test Lab"
        
        imported_config = self.configurator.import_configuration(exported)
        self.assertEqual(imported_config.lab_id, "test-lab-010")
        self.assertEqual(imported_config.lab_name, "Imported Test Lab")
        self.assertEqual(imported_config.script_id, original_config.script_id)
        self.assertEqual(imported_config.market_config.leverage, 15.0)
        
        # Verify imported config is stored
        self.assertIn("test-lab-010", self.configurator.configurations)
    
    def test_get_configurations(self):
        """Test getting configurations"""
        # Create configurations on different servers
        self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-011",
            lab_name="Server 1 Lab",
            script_id="script-srv1",
            server_id="test-srv01",
            market_tag="BINANCE_ATOM_USDT",
            exchange_code="BINANCE",
            account_id="account-srv1"
        )
        
        self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-lab-012",
            lab_name="Server 2 Lab",
            script_id="script-srv2",
            server_id="test-srv02",
            market_tag="BINANCE_LINK_USDT",
            exchange_code="BINANCE",
            account_id="account-srv2"
        )
        
        # Test get all configurations
        all_configs = self.configurator.get_all_configurations()
        self.assertGreaterEqual(len(all_configs), 2)
        
        # Test get configurations by server
        srv1_configs = self.configurator.get_all_configurations("test-srv01")
        srv2_configs = self.configurator.get_all_configurations("test-srv02")
        
        srv1_ids = [config.lab_id for config in srv1_configs]
        srv2_ids = [config.lab_id for config in srv2_configs]
        
        self.assertIn("test-lab-011", srv1_ids)
        self.assertIn("test-lab-012", srv2_ids)
        self.assertNotIn("test-lab-012", srv1_ids)
        self.assertNotIn("test-lab-011", srv2_ids)
    
    def test_configuration_summary(self):
        """Test configuration summary generation"""
        # Create various configurations
        configs_to_create = [
            ("standard", "test-lab-013", "test-srv01", LabAlgorithm.INTELLIGENT),
            ("high_frequency", "test-lab-014", "test-srv01", LabAlgorithm.GENETIC),
            ("futures", "test-lab-015", "test-srv02", LabAlgorithm.BRUTE_FORCE),
        ]
        
        for template, lab_id, server_id, algorithm in configs_to_create:
            config = self.configurator.create_lab_configuration(
                template_name=template,
                lab_id=lab_id,
                lab_name=f"Summary Test {lab_id}",
                script_id=f"script-{lab_id}",
                server_id=server_id,
                market_tag="BINANCE_TEST_USDT",
                exchange_code="BINANCE",
                account_id=f"account-{lab_id}"
            )
            
            # Update algorithm
            self.configurator.configure_lab_algorithm(lab_id, algorithm)
        
        # Get summary
        summary = self.configurator.get_configuration_summary()
        
        self.assertIn('total_configurations', summary)
        self.assertIn('status_distribution', summary)
        self.assertIn('server_distribution', summary)
        self.assertIn('algorithm_distribution', summary)
        self.assertIn('available_templates', summary)
        self.assertIn('registered_servers', summary)
        
        # Check that we have at least our test configurations
        self.assertGreaterEqual(summary['total_configurations'], 3)
        
        # Check server distribution
        self.assertIn('test-srv01', summary['server_distribution'])
        self.assertIn('test-srv02', summary['server_distribution'])
        
        # Check algorithm distribution
        algorithm_dist = summary['algorithm_distribution']
        self.assertIn('Intelligent', algorithm_dist)
        self.assertIn('Genetic', algorithm_dist)
        self.assertIn('BruteForce', algorithm_dist)
        
        # Check templates
        self.assertEqual(len(summary['available_templates']), 4)
        self.assertIn('standard', summary['available_templates'])
    
    def test_nonexistent_operations(self):
        """Test operations on nonexistent configurations"""
        # Test getting nonexistent configuration
        config = self.configurator.get_lab_configuration("nonexistent")
        self.assertIsNone(config)
        
        # Test updating nonexistent configuration
        updated = self.configurator.update_lab_configuration("nonexistent", lab_name="New Name")
        self.assertIsNone(updated)
        
        # Test configuring algorithm for nonexistent lab
        success = self.configurator.configure_lab_algorithm("nonexistent", LabAlgorithm.GENETIC)
        self.assertFalse(success)
        
        # Test updating market for nonexistent lab
        success = self.configurator.update_lab_market("nonexistent", "NEW_MARKET")
        self.assertFalse(success)
        
        # Test setting timeframe for nonexistent lab
        success = self.configurator.set_lab_execution_timeframe("nonexistent", 0, 1000)
        self.assertFalse(success)
        
        # Test validating nonexistent configuration
        is_valid, issues = self.configurator.validate_configuration("nonexistent")
        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)
        
        # Test exporting nonexistent configuration
        exported = self.configurator.export_configuration("nonexistent")
        self.assertIsNone(exported)
    
    def test_invalid_template(self):
        """Test creating configuration with invalid template"""
        with self.assertRaises(ValueError):
            self.configurator.create_lab_configuration(
                template_name="nonexistent_template",
                lab_id="test-lab-invalid",
                lab_name="Invalid Template Lab",
                script_id="script-invalid",
                server_id="test-srv01",
                market_tag="BINANCE_INVALID_USDT",
                exchange_code="BINANCE",
                account_id="account-invalid"
            )

def main():
    """Run all tests"""
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()