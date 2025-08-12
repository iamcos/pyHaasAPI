#!/usr/bin/env python3
"""
Lab Management System Test Suite

This module provides comprehensive tests for the lab cloning and market
resolution components of the lab management system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from lab_cloner import (
    LabCloner, MarketDiscovery, LabCloneRequest, LabCloneResult,
    MarketInfo, MarketType
)
from market_resolver import MarketResolver, ExchangeType

class TestMarketResolver(unittest.TestCase):
    """Test cases for MarketResolver"""
    
    def setUp(self):
        """Set up test environment"""
        self.resolver = MarketResolver()
    
    def test_market_tag_parsing(self):
        """Test market tag parsing functionality"""
        # Test valid perpetual market tag
        tag = "BINANCEFUTURES_BTC_USDT_PERPETUAL"
        parsed = self.resolver.parse_market_tag(tag)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['exchange'], 'BINANCEFUTURES')
        self.assertEqual(parsed['base_asset'], 'BTC')
        self.assertEqual(parsed['quote_asset'], 'USDT')
        self.assertEqual(parsed['market_type'], 'perpetual')
        
        # Test valid spot market tag
        tag = "BINANCE_ETH_USDT_"
        parsed = self.resolver.parse_market_tag(tag)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['exchange'], 'BINANCE')
        self.assertEqual(parsed['base_asset'], 'ETH')
        self.assertEqual(parsed['quote_asset'], 'USDT')
        self.assertEqual(parsed['market_type'], 'spot')
        
        # Test invalid market tag
        tag = "INVALID_FORMAT"
        parsed = self.resolver.parse_market_tag(tag)
        self.assertIsNone(parsed)
    
    def test_market_tag_formatting(self):
        """Test market tag formatting functionality"""
        # Test perpetual market formatting
        tag = self.resolver.format_market_tag(
            "BINANCEFUTURES", "BTC", "USDT", "perpetual"
        )
        self.assertEqual(tag, "BINANCEFUTURES_BTC_USDT_PERPETUAL")
        
        # Test spot market formatting
        tag = self.resolver.format_market_tag(
            "BINANCE", "ETH", "USDT", "spot"
        )
        self.assertEqual(tag, "BINANCE_ETH_USDT_")
        
        # Test quarterly market formatting
        tag = self.resolver.format_market_tag(
            "BINANCEQUARTERLY", "BTC", "USD", "quarterly"
        )
        self.assertEqual(tag, "BINANCEQUARTERLY_BTC_USD_QUARTERLY")
    
    def test_asset_normalization(self):
        """Test asset symbol normalization"""
        # Test known aliases
        self.assertEqual(self.resolver.normalize_asset("BITCOIN"), "BTC")
        self.assertEqual(self.resolver.normalize_asset("ETHEREUM"), "ETH")
        self.assertEqual(self.resolver.normalize_asset("TETHER"), "USDT")
        
        # Test case insensitive
        self.assertEqual(self.resolver.normalize_asset("bitcoin"), "BTC")
        self.assertEqual(self.resolver.normalize_asset("Bitcoin"), "BTC")
        
        # Test unknown asset (should return as-is)
        self.assertEqual(self.resolver.normalize_asset("UNKNOWN"), "UNKNOWN")
    
    def test_market_tag_validation(self):
        """Test market tag validation"""
        # Test valid market tag
        is_valid, error = self.resolver.validate_market_tag("BINANCEFUTURES_BTC_USDT_PERPETUAL")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Test invalid format
        is_valid, error = self.resolver.validate_market_tag("INVALID_FORMAT")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        
        # Test unknown exchange
        is_valid, error = self.resolver.validate_market_tag("UNKNOWN_BTC_USDT_")
        self.assertFalse(is_valid)
        self.assertIn("Unknown exchange", error)
        
        # Test unsupported asset
        is_valid, error = self.resolver.validate_market_tag("BINANCEFUTURES_UNSUPPORTED_USDT_PERPETUAL")
        self.assertFalse(is_valid)
        self.assertIn("not supported", error)
    
    def test_supported_exchanges(self):
        """Test getting supported exchanges"""
        # Test all exchanges
        all_exchanges = self.resolver.get_supported_exchanges()
        self.assertIn("BINANCE", all_exchanges)
        self.assertIn("BINANCEFUTURES", all_exchanges)
        self.assertNotIn("COINBASE", all_exchanges)  # Inactive
        
        # Test futures exchanges only
        futures_exchanges = self.resolver.get_supported_exchanges("futures")
        self.assertIn("BINANCEFUTURES", futures_exchanges)
        self.assertNotIn("BINANCE", futures_exchanges)  # Spot exchange
    
    def test_market_suggestions(self):
        """Test market tag suggestions"""
        suggestions = self.resolver.suggest_market_tags(
            base_assets=["BTC", "ETH"],
            quote_assets=["USDT"],
            market_type="perpetual"
        )
        
        self.assertGreater(len(suggestions), 0)
        
        # Check that all suggestions are valid
        for suggestion in suggestions:
            is_valid, _ = self.resolver.validate_market_tag(suggestion)
            self.assertTrue(is_valid, f"Invalid suggestion: {suggestion}")
        
        # Check that all suggestions are perpetual
        perpetual_suggestions = self.resolver.filter_perpetual_markets(suggestions)
        self.assertEqual(len(suggestions), len(perpetual_suggestions))
    
    def test_market_filtering_and_grouping(self):
        """Test market filtering and grouping"""
        test_markets = [
            "BINANCEFUTURES_BTC_USDT_PERPETUAL",
            "BINANCE_ETH_USDT_",
            "BINANCEQUARTERLY_SOL_USD_PERPETUAL",
            "KRAKEN_BTC_USD_"
        ]
        
        # Test perpetual filtering
        perpetual_markets = self.resolver.filter_perpetual_markets(test_markets)
        self.assertEqual(len(perpetual_markets), 2)
        self.assertIn("BINANCEFUTURES_BTC_USDT_PERPETUAL", perpetual_markets)
        self.assertIn("BINANCEQUARTERLY_SOL_USD_PERPETUAL", perpetual_markets)
        
        # Test grouping by exchange
        grouped = self.resolver.group_markets_by_exchange(test_markets)
        self.assertIn("BINANCEFUTURES", grouped)
        self.assertIn("BINANCE", grouped)
        self.assertIn("BINANCEQUARTERLY", grouped)
        self.assertIn("KRAKEN", grouped)
        
        self.assertEqual(len(grouped["BINANCEFUTURES"]), 1)
        self.assertEqual(len(grouped["BINANCE"]), 1)

class TestMarketDiscovery(unittest.TestCase):
    """Test cases for MarketDiscovery"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_executor = Mock()
        self.discovery = MarketDiscovery(self.mock_executor)
    
    def test_market_classification(self):
        """Test market classification functionality"""
        # Create mock market
        mock_market = Mock()
        mock_market.primary_currency = "BTC"
        mock_market.secondary_currency = "USDT"
        mock_market.format_futures_market_tag = Mock(return_value="BINANCEFUTURES_BTC_USDT_PERPETUAL")
        
        # Test classification
        market_info = self.discovery._classify_market(mock_market, "BINANCEFUTURES")
        
        self.assertIsNotNone(market_info)
        self.assertEqual(market_info.base_asset, "BTC")
        self.assertEqual(market_info.quote_asset, "USDT")
        self.assertEqual(market_info.exchange, "BINANCEFUTURES")
        self.assertEqual(market_info.market_type, MarketType.PERPETUAL)
    
    def test_market_filtering_by_assets(self):
        """Test filtering markets by assets"""
        # Create test markets
        markets = [
            MarketInfo("BTC_USDT", "BINANCE", "BTC", "USDT", MarketType.PERPETUAL),
            MarketInfo("ETH_USDT", "BINANCE", "ETH", "USDT", MarketType.PERPETUAL),
            MarketInfo("ADA_USDT", "BINANCE", "ADA", "USDT", MarketType.PERPETUAL),
        ]
        
        # Filter by specific assets
        filtered = self.discovery.filter_markets_by_assets(markets, ["BTC", "ETH"])
        
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(m.base_asset in ["BTC", "ETH"] for m in filtered))
    
    def test_cache_functionality(self):
        """Test market discovery caching"""
        exchange = "BINANCEFUTURES"
        
        # Initially cache should be invalid
        self.assertFalse(self.discovery._is_cache_valid(exchange))
        
        # Simulate cache population
        test_markets = [
            MarketInfo("BTC_USDT", exchange, "BTC", "USDT", MarketType.PERPETUAL)
        ]
        self.discovery._market_cache[exchange] = test_markets
        self.discovery._cache_timestamp[exchange] = time.time()
        
        # Cache should now be valid
        self.assertTrue(self.discovery._is_cache_valid(exchange))
    
    def test_market_summary_generation(self):
        """Test market summary generation"""
        test_markets = {
            "BINANCEFUTURES": [
                MarketInfo("BTC_USDT", "BINANCEFUTURES", "BTC", "USDT", MarketType.PERPETUAL),
                MarketInfo("ETH_USDT", "BINANCEFUTURES", "ETH", "USDT", MarketType.PERPETUAL),
            ],
            "BINANCE": [
                MarketInfo("BTC_USDT", "BINANCE", "BTC", "USDT", MarketType.SPOT),
            ]
        }
        
        summary = self.discovery.get_market_summary(test_markets)
        
        self.assertEqual(summary['total_markets'], 3)
        self.assertEqual(len(summary['exchanges']), 2)
        self.assertIn('BINANCEFUTURES', summary['exchanges'])
        self.assertIn('BINANCE', summary['exchanges'])
        self.assertEqual(summary['markets_per_exchange']['BINANCEFUTURES'], 2)
        self.assertEqual(summary['markets_per_exchange']['BINANCE'], 1)

class TestLabCloner(unittest.TestCase):
    """Test cases for LabCloner"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_server_manager = Mock()
        self.lab_cloner = LabCloner(self.mock_server_manager)
    
    def test_clone_request_creation(self):
        """Test lab clone request creation"""
        market_info = MarketInfo(
            market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
            exchange="BINANCEFUTURES",
            base_asset="BTC",
            quote_asset="USDT",
            market_type=MarketType.PERPETUAL
        )
        
        clone_request = LabCloneRequest(
            base_lab_id="test-lab-id",
            target_server_id="srv01",
            new_lab_name="Test_Clone",
            market_info=market_info,
            account_id="test-account"
        )
        
        self.assertEqual(clone_request.base_lab_id, "test-lab-id")
        self.assertEqual(clone_request.target_server_id, "srv01")
        self.assertEqual(clone_request.market_info.base_asset, "BTC")
        self.assertEqual(clone_request.account_id, "test-account")
    
    def test_statistics_generation(self):
        """Test cloning statistics generation"""
        # Create mock results
        mock_results = {
            "srv01": [
                LabCloneResult(True, "lab1", "srv01", "BTC_USDT", execution_time=1.5),
                LabCloneResult(False, None, "srv01", "ETH_USDT", "Connection error", 2.0),
                LabCloneResult(True, "lab2", "srv01", "ADA_USDT", execution_time=1.2)
            ],
            "srv02": [
                LabCloneResult(True, "lab3", "srv02", "SOL_USDT", execution_time=1.8),
                LabCloneResult(False, None, "srv02", "BNB_USDT", "API error", 1.0)
            ]
        }
        
        stats = self.lab_cloner.get_cloning_statistics(mock_results)
        
        # Check overall statistics
        self.assertEqual(stats['total_attempts'], 5)
        self.assertEqual(stats['total_successes'], 3)
        self.assertEqual(stats['total_failures'], 2)
        self.assertEqual(stats['overall_success_rate'], 0.6)
        
        # Check server statistics
        self.assertIn('srv01', stats['server_statistics'])
        self.assertIn('srv02', stats['server_statistics'])
        
        srv01_stats = stats['server_statistics']['srv01']
        self.assertEqual(srv01_stats['attempts'], 3)
        self.assertEqual(srv01_stats['successes'], 2)
        self.assertEqual(srv01_stats['failures'], 1)
        
        # Check error summary
        self.assertIn('error_summary', stats)
        self.assertIn('Connection error', stats['error_summary'])
        self.assertIn('API error', stats['error_summary'])
    
    @patch('lab_cloner.api')
    def test_lab_creation_from_template(self, mock_api):
        """Test lab creation from template"""
        # Mock base lab
        mock_base_lab = Mock()
        mock_base_lab.script_id = "test-script-id"
        mock_base_lab.settings.interval = 15
        mock_base_lab.settings.price_data_style = "CandleStick"
        
        # Mock new lab creation
        mock_new_lab = Mock()
        mock_new_lab.lab_id = "new-lab-id"
        mock_api.create_lab.return_value = mock_new_lab
        
        # Create clone request
        market_info = MarketInfo(
            market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
            exchange="BINANCEFUTURES",
            base_asset="BTC",
            quote_asset="USDT",
            market_type=MarketType.PERPETUAL
        )
        
        clone_request = LabCloneRequest(
            base_lab_id="base-lab-id",
            target_server_id="srv01",
            new_lab_name="Test_Clone",
            market_info=market_info,
            account_id="test-account"
        )
        
        # Test lab creation
        mock_executor = Mock()
        result = self.lab_cloner._create_lab_from_template(
            mock_executor, mock_base_lab, clone_request
        )
        
        self.assertEqual(result.lab_id, "new-lab-id")
        mock_api.create_lab.assert_called_once()
    
    def test_market_distribution(self):
        """Test market distribution across servers"""
        # Create test markets
        all_markets = {
            "BINANCEFUTURES": [
                MarketInfo("BTC_USDT", "BINANCEFUTURES", "BTC", "USDT", MarketType.PERPETUAL),
                MarketInfo("ETH_USDT", "BINANCEFUTURES", "ETH", "USDT", MarketType.PERPETUAL),
                MarketInfo("ADA_USDT", "BINANCEFUTURES", "ADA", "USDT", MarketType.PERPETUAL),
            ]
        }
        
        available_servers = ["srv01", "srv02"]
        
        # Test distribution
        distribution = self.lab_cloner._distribute_markets_across_servers(
            all_markets, available_servers
        )
        
        # Check that all servers are included
        self.assertEqual(set(distribution.keys()), set(available_servers))
        
        # Check that all markets are distributed
        total_distributed = sum(len(markets) for markets in distribution.values())
        self.assertEqual(total_distributed, 3)
        
        # Check roughly even distribution
        for server_markets in distribution.values():
            self.assertGreaterEqual(len(server_markets), 1)
            self.assertLessEqual(len(server_markets), 2)

class TestIntegration(unittest.TestCase):
    """Integration tests for lab management system"""
    
    def test_market_resolver_and_discovery_integration(self):
        """Test integration between market resolver and discovery"""
        resolver = MarketResolver()
        
        # Generate market suggestions
        suggestions = resolver.suggest_market_tags(
            base_assets=["BTC", "ETH"],
            quote_assets=["USDT"],
            market_type="perpetual"
        )
        
        # Test that all suggestions can be parsed
        for suggestion in suggestions:
            parsed = resolver.parse_market_tag(suggestion)
            self.assertIsNotNone(parsed)
            self.assertEqual(parsed['market_type'], 'perpetual')
        
        # Test filtering
        perpetual_only = resolver.filter_perpetual_markets(suggestions)
        self.assertEqual(len(suggestions), len(perpetual_only))
    
    def test_end_to_end_workflow_simulation(self):
        """Test end-to-end workflow simulation"""
        # Initialize components
        resolver = MarketResolver()
        mock_server_manager = Mock()
        mock_server_manager.get_available_servers.return_value = ["srv01", "srv02"]
        
        lab_cloner = LabCloner(mock_server_manager)
        
        # Generate market suggestions
        suggestions = resolver.suggest_market_tags(
            base_assets=["BTC", "ETH"],
            quote_assets=["USDT"],
            market_type="perpetual"
        )
        
        # Create market info objects
        market_infos = []
        for suggestion in suggestions[:4]:  # Limit to 4 for testing
            parsed = resolver.parse_market_tag(suggestion)
            if parsed:
                market_info = MarketInfo(
                    market_tag=suggestion,
                    exchange=parsed['exchange'],
                    base_asset=parsed['base_asset'],
                    quote_asset=parsed['quote_asset'],
                    market_type=MarketType.PERPETUAL
                )
                market_infos.append(market_info)
        
        # Test market distribution
        all_markets = {"BINANCEFUTURES": market_infos}
        available_servers = ["srv01", "srv02"]
        
        distribution = lab_cloner._distribute_markets_across_servers(
            all_markets, available_servers
        )
        
        # Verify distribution
        self.assertEqual(len(distribution), 2)
        total_markets = sum(len(markets) for markets in distribution.values())
        self.assertEqual(total_markets, len(market_infos))

def run_lab_management_tests():
    """Run all lab management tests"""
    print("Running Lab Management System Tests...")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestMarketResolver))
    test_suite.addTest(unittest.makeSuite(TestMarketDiscovery))
    test_suite.addTest(unittest.makeSuite(TestLabCloner))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    run_lab_management_tests()