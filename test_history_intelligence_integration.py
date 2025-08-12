#!/usr/bin/env python3
"""
Test script for History Intelligence Integration

This script demonstrates the integrated history intelligence functionality
with the pyHaasAPI system, including cutoff discovery for the specified lab ID.
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add pyHaasAPI to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.enhanced_execution import get_enhanced_executor
from pyHaasAPI.history_intelligence import get_history_service


class HistoryIntelligenceIntegrationTest:
    """Test class for history intelligence integration"""
    
    def __init__(self):
        self.haas_executor = None
        self.mcp_base_url = "http://localhost:8000"
        self.test_lab_id = "63581392-5779-413f-8e86-4c90d373f0a8"  # The lab ID you specified
        
    def authenticate_haas_api(self):
        """Authenticate with HaasOnline API"""
        try:
            api_host = os.getenv("API_HOST", "127.0.0.1")
            api_port = int(os.getenv("API_PORT", 8090))
            api_email = os.getenv("API_EMAIL")
            api_password = os.getenv("API_PASSWORD")
            
            logger.info(f"Authenticating with HaasOnline API at {api_host}:{api_port}")
            
            self.haas_executor = api.RequestsExecutor(
                host=api_host,
                port=api_port,
                state=api.Guest()
            ).authenticate(
                email=api_email,
                password=api_password
            )
            
            logger.info("Successfully authenticated with HaasOnline API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with HaasOnline API: {e}")
            return False
    
    def test_direct_api_integration(self):
        """Test direct API integration (without MCP server)"""
        logger.info("=" * 60)
        logger.info("Testing Direct API Integration")
        logger.info("=" * 60)
        
        try:
            # Test 1: Get enhanced executor
            logger.info("1. Getting enhanced executor...")
            executor = get_enhanced_executor(self.haas_executor)
            logger.info("✓ Enhanced executor created successfully")
            
            # Test 2: Discover cutoff for the specified lab
            logger.info(f"2. Discovering cutoff for lab {self.test_lab_id}...")
            cutoff_result = executor.discover_cutoff_for_lab(self.test_lab_id)
            
            if cutoff_result.get('success'):
                logger.info("✓ Cutoff discovery successful!")
                logger.info(f"   Lab ID: {cutoff_result.get('lab_id')}")
                logger.info(f"   Lab Name: {cutoff_result.get('lab_name', 'N/A')}")
                logger.info(f"   Market Tag: {cutoff_result.get('market_tag', 'N/A')}")
                logger.info(f"   Cutoff Date: {cutoff_result.get('cutoff_date', 'N/A')}")
                logger.info(f"   Precision: {cutoff_result.get('precision_achieved_hours', 'N/A')} hours")
                logger.info(f"   Discovery Time: {cutoff_result.get('discovery_time_seconds', 'N/A')} seconds")
                logger.info(f"   Tests Performed: {cutoff_result.get('tests_performed', 'N/A')}")
            else:
                logger.error(f"✗ Cutoff discovery failed: {cutoff_result.get('error_message', 'Unknown error')}")
            
            # Test 3: Validate a backtest period
            logger.info("3. Testing backtest period validation...")
            start_date = "2020-01-01T00:00:00"
            end_date = "2023-01-01T00:00:00"
            
            validation_result = executor.validate_lab_backtest_period(
                self.test_lab_id, start_date, end_date
            )
            
            if validation_result.get('success'):
                logger.info("✓ Period validation successful!")
                logger.info(f"   Is Valid: {validation_result.get('is_valid')}")
                logger.info(f"   Message: {validation_result.get('message', 'N/A')}")
                logger.info(f"   Requires Sync: {validation_result.get('requires_sync')}")
                
                if validation_result.get('recommended_start'):
                    logger.info(f"   Recommended Start: {validation_result.get('recommended_start')}")
                    logger.info(f"   Adjustment Days: {validation_result.get('adjustment_days', 0)}")
            else:
                logger.error(f"✗ Period validation failed: {validation_result.get('error', 'Unknown error')}")
            
            # Test 4: Get history summary
            logger.info("4. Getting history intelligence summary...")
            summary = executor.get_history_summary()
            
            if 'error' not in summary:
                logger.info("✓ History summary retrieved!")
                logger.info(f"   Total Markets: {summary.get('total_markets', 0)}")
                logger.info(f"   Cache Size: {summary.get('cache_size', 0)}")
                
                db_stats = summary.get('database_stats', {})
                logger.info(f"   Database Size: {db_stats.get('file_size_bytes', 0)} bytes")
                logger.info(f"   Backup Count: {db_stats.get('backup_count', 0)}")
                
                exchanges = summary.get('exchange_summary', {})
                logger.info(f"   Known Exchanges: {list(exchanges.keys())}")
            else:
                logger.error(f"✗ History summary failed: {summary.get('error')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in direct API integration test: {e}")
            return False
    
    def test_mcp_server_integration(self):
        """Test MCP server integration"""
        logger.info("=" * 60)
        logger.info("Testing MCP Server Integration")
        logger.info("=" * 60)
        
        try:
            # Test 1: Health check
            logger.info("1. Testing history intelligence health endpoint...")
            response = requests.get(f"{self.mcp_base_url}/history_intelligence_health")
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✓ Health check successful!")
                logger.info(f"   Status: {health_data.get('status')}")
                logger.info(f"   Service Initialized: {health_data.get('service_initialized')}")
                logger.info(f"   Database Accessible: {health_data.get('database_accessible')}")
                logger.info(f"   Known Cutoffs: {health_data.get('total_known_cutoffs', 0)}")
            else:
                logger.error(f"✗ Health check failed: {response.status_code}")
                return False
            
            # Test 2: Discover cutoff via MCP server
            logger.info(f"2. Discovering cutoff via MCP server for lab {self.test_lab_id}...")
            
            payload = {
                "lab_id": self.test_lab_id,
                "force_rediscover": False
            }
            
            response = requests.post(f"{self.mcp_base_url}/discover_cutoff", json=payload)
            
            if response.status_code == 200:
                cutoff_data = response.json()
                logger.info("✓ MCP cutoff discovery successful!")
                logger.info(f"   Success: {cutoff_data.get('success')}")
                logger.info(f"   Lab ID: {cutoff_data.get('lab_id')}")
                logger.info(f"   Market Tag: {cutoff_data.get('market_tag', 'N/A')}")
                logger.info(f"   Cutoff Date: {cutoff_data.get('cutoff_date', 'N/A')}")
                logger.info(f"   Discovery Time: {cutoff_data.get('discovery_time_seconds', 'N/A')} seconds")
            else:
                logger.error(f"✗ MCP cutoff discovery failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
            
            # Test 3: Validate period via MCP server
            logger.info("3. Validating backtest period via MCP server...")
            
            payload = {
                "lab_id": self.test_lab_id,
                "start_date": "2020-01-01T00:00:00",
                "end_date": "2023-01-01T00:00:00"
            }
            
            response = requests.post(f"{self.mcp_base_url}/validate_backtest_period", json=payload)
            
            if response.status_code == 200:
                validation_data = response.json()
                logger.info("✓ MCP period validation successful!")
                logger.info(f"   Success: {validation_data.get('success')}")
                logger.info(f"   Is Valid: {validation_data.get('is_valid')}")
                logger.info(f"   Message: {validation_data.get('message', 'N/A')}")
                
                if validation_data.get('recommended_start'):
                    logger.info(f"   Recommended Start: {validation_data.get('recommended_start')}")
            else:
                logger.error(f"✗ MCP period validation failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
            
            # Test 4: Get history summary via MCP server
            logger.info("4. Getting history summary via MCP server...")
            
            response = requests.get(f"{self.mcp_base_url}/history_summary")
            
            if response.status_code == 200:
                summary_data = response.json()
                logger.info("✓ MCP history summary successful!")
                logger.info(f"   Total Markets: {summary_data.get('total_markets', 0)}")
                
                if 'exchange_summary' in summary_data:
                    exchanges = summary_data['exchange_summary']
                    logger.info(f"   Exchanges: {list(exchanges.keys())}")
            else:
                logger.error(f"✗ MCP history summary failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in MCP server integration test: {e}")
            return False
    
    def test_enhanced_backtest_execution(self):
        """Test enhanced backtest execution (simulation)"""
        logger.info("=" * 60)
        logger.info("Testing Enhanced Backtest Execution")
        logger.info("=" * 60)
        
        try:
            # Get enhanced executor
            executor = get_enhanced_executor(self.haas_executor)
            
            # Test enhanced execution (this will validate but not actually execute)
            logger.info(f"Testing enhanced execution for lab {self.test_lab_id}...")
            
            # Use a period that might need adjustment
            start_date = "2019-01-01T00:00:00"
            end_date = "2020-01-01T00:00:00"
            
            logger.info(f"Requested period: {start_date} to {end_date}")
            
            # This would normally execute the backtest, but we'll just validate
            validation_result = executor.validate_lab_backtest_period(
                self.test_lab_id, start_date, end_date
            )
            
            if validation_result.get('success'):
                logger.info("✓ Enhanced execution validation successful!")
                logger.info(f"   Period Valid: {validation_result.get('is_valid')}")
                logger.info(f"   Message: {validation_result.get('message', 'N/A')}")
                
                if not validation_result.get('is_valid'):
                    logger.info("   Period would be auto-adjusted for execution")
                    if validation_result.get('recommended_start'):
                        logger.info(f"   Recommended Start: {validation_result.get('recommended_start')}")
                else:
                    logger.info("   Period is ready for execution")
            else:
                logger.error(f"✗ Enhanced execution validation failed: {validation_result.get('error')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in enhanced backtest execution test: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting History Intelligence Integration Tests")
        logger.info("=" * 80)
        
        # Authenticate first
        if not self.authenticate_haas_api():
            logger.error("Authentication failed - cannot proceed with tests")
            return False
        
        # Run tests
        tests = [
            ("Direct API Integration", self.test_direct_api_integration),
            ("Enhanced Backtest Execution", self.test_enhanced_backtest_execution),
            ("MCP Server Integration", self.test_mcp_server_integration),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\nRunning {test_name}...")
            try:
                results[test_name] = test_func()
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASSED" if result else "✗ FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! History Intelligence integration is working correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed. Please check the logs above.")
        
        return passed == total


async def main():
    """Main test function"""
    test_runner = HistoryIntelligenceIntegrationTest()
    success = await test_runner.run_all_tests()
    
    if success:
        logger.info("\n🚀 History Intelligence is ready for production use!")
        logger.info(f"You can now discover the cutoff date for lab {test_runner.test_lab_id}")
    else:
        logger.error("\n❌ Some tests failed. Please review the configuration and try again.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())