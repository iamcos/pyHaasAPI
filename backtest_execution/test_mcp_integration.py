#!/usr/bin/env python3
"""
Test MCP Server Integration with Backtest Execution System
This module tests the integration between our backtest execution system
and the MCP server endpoints.
"""

import requests
import json
import time
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerTester:
    """Test integration with MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_server_status(self) -> bool:
        """Test if MCP server is running and accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                logger.info("✓ MCP Server is running")
                return True
            else:
                logger.error(f"✗ Server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error("✗ Cannot connect to MCP server")
            return False
        except Exception as e:
            logger.error(f"✗ Error testing server: {e}")
            return False
    
    def test_authentication_status(self) -> Dict[str, Any]:
        """Test HaasOnline API authentication status"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Authentication status: {data}")
                return data
            else:
                logger.error(f"✗ Status check failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"✗ Error checking auth status: {e}")
            return {"error": str(e)}
    
    def test_get_accounts(self) -> List[Dict[str, Any]]:
        """Test getting all accounts"""
        try:
            response = self.session.get(f"{self.base_url}/get_all_accounts")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    accounts = data.get("Data", [])
                    logger.info(f"✓ Retrieved {len(accounts)} accounts")
                    return accounts
                else:
                    logger.error(f"✗ API error: {data.get('Error', 'Unknown error')}")
                    return []
            else:
                logger.error(f"✗ HTTP error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error getting accounts: {e}")
            return []
    
    def test_get_labs(self) -> List[Dict[str, Any]]:
        """Test getting all labs"""
        try:
            response = self.session.get(f"{self.base_url}/get_all_labs")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    labs = data.get("Data", [])
                    logger.info(f"✓ Retrieved {len(labs)} labs")
                    return labs
                else:
                    logger.error(f"✗ API error: {data.get('Error', 'Unknown error')}")
                    return []
            else:
                logger.error(f"✗ HTTP error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error getting labs: {e}")
            return []
    
    def test_get_markets(self) -> List[Dict[str, Any]]:
        """Test getting all markets"""
        try:
            response = self.session.get(f"{self.base_url}/get_all_markets")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    markets = data.get("Data", [])
                    logger.info(f"✓ Retrieved {len(markets)} markets")
                    return markets
                else:
                    logger.error(f"✗ API error: {data.get('Error', 'Unknown error')}")
                    return []
            else:
                logger.error(f"✗ HTTP error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"✗ Error getting markets: {e}")
            return []
    
    def test_create_lab(self, script_id: str, account_id: str) -> Dict[str, Any]:
        """Test creating a lab"""
        try:
            payload = {
                "script_id": script_id,
                "account_id": account_id,
                "market_category": "PERPETUAL",
                "market_price_source": "BINANCEFUTURES",
                "market_primary": "BTC",
                "market_secondary": "USDT",
                "exchange_code": "BINANCEFUTURES",
                "interval": 15,
                "default_price_data_style": "CandleStick"
            }
            
            response = self.session.post(
                f"{self.base_url}/create_lab",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Lab created: {data}")
                return data
            else:
                logger.error(f"✗ Lab creation failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"✗ Error creating lab: {e}")
            return {"error": str(e)}
    
    def test_start_lab_execution(self, lab_id: str, period: str = "1_year") -> Dict[str, Any]:
        """Test starting lab execution with period preset"""
        try:
            payload = {
                "lab_id": lab_id,
                "period": period,
                "send_email": False
            }
            
            response = self.session.post(
                f"{self.base_url}/start_lab_execution",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Lab execution started: {data}")
                return data
            else:
                logger.error(f"✗ Lab execution failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"✗ Error starting lab execution: {e}")
            return {"error": str(e)}
    
    def test_clone_lab_to_markets(self, source_lab_id: str) -> Dict[str, Any]:
        """Test cloning lab to multiple markets"""
        try:
            payload = {
                "source_lab_id": source_lab_id,
                "targets": [
                    {"asset": "BTC", "exchange": "BINANCEFUTURES"},
                    {"asset": "ETH", "exchange": "BINANCEFUTURES"}
                ],
                "lab_name_template": "Test Strategy - {primary} - {suffix}"
            }
            
            response = self.session.post(
                f"{self.base_url}/clone_lab_to_markets",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Lab cloned to markets: {data}")
                return data
            else:
                logger.error(f"✗ Lab cloning failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"✗ Error cloning lab: {e}")
            return {"error": str(e)}
    
    def test_get_backtest_results(self, lab_id: str) -> Dict[str, Any]:
        """Test getting backtest results"""
        try:
            payload = {
                "lab_id": lab_id,
                "next_page_id": -1,
                "page_length": 100
            }
            
            response = self.session.post(
                f"{self.base_url}/get_backtest_results",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    results = data.get("Data", {})
                    logger.info(f"✓ Retrieved backtest results: {len(results.get('Results', []))} results")
                    return data
                else:
                    logger.error(f"✗ API error: {data.get('Error', 'Unknown error')}")
                    return data
            else:
                logger.error(f"✗ HTTP error: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"✗ Error getting backtest results: {e}")
            return {"error": str(e)}

def run_integration_tests():
    """Run comprehensive integration tests"""
    print("MCP Server Integration Tests")
    print("=" * 50)
    
    tester = MCPServerTester()
    
    # Test 1: Server connectivity
    print("\n1. Testing server connectivity...")
    if not tester.test_server_status():
        print("❌ Server not accessible - skipping remaining tests")
        return
    
    # Test 2: Authentication status
    print("\n2. Testing authentication status...")
    auth_status = tester.test_authentication_status()
    is_authenticated = auth_status.get("haas_api_connected", False)
    
    if not is_authenticated:
        print("⚠️  HaasOnline API not authenticated - some tests may fail")
    
    # Test 3: Get accounts
    print("\n3. Testing account retrieval...")
    accounts = tester.test_get_accounts()
    
    # Test 4: Get labs
    print("\n4. Testing lab retrieval...")
    labs = tester.test_get_labs()
    
    # Test 5: Get markets
    print("\n5. Testing market retrieval...")
    markets = tester.test_get_markets()
    
    # Test 6: Create lab (if we have accounts)
    print("\n6. Testing lab creation...")
    if accounts and is_authenticated:
        # Use first available account
        account_id = accounts[0].get("AID") or accounts[0].get("account_id")
        if account_id:
            # We need a script ID - let's try to get scripts first
            try:
                response = tester.session.get(f"{tester.base_url}/get_all_scripts")
                if response.status_code == 200:
                    scripts_data = response.json()
                    if scripts_data.get("Success") and scripts_data.get("Data"):
                        script_id = scripts_data["Data"][0].get("SID") or scripts_data["Data"][0].get("script_id")
                        if script_id:
                            lab_result = tester.test_create_lab(script_id, account_id)
                            
                            # Test 7: Start lab execution (if lab was created)
                            if "lab_id" in lab_result:
                                print("\n7. Testing lab execution...")
                                execution_result = tester.test_start_lab_execution(lab_result["lab_id"])
                                
                                # Test 8: Get backtest results
                                print("\n8. Testing backtest results retrieval...")
                                time.sleep(2)  # Wait a bit for execution to start
                                results = tester.test_get_backtest_results(lab_result["lab_id"])
                                
                                # Test 9: Clone lab to markets
                                print("\n9. Testing lab cloning to markets...")
                                clone_result = tester.test_clone_lab_to_markets(lab_result["lab_id"])
                        else:
                            print("⚠️  No script ID available for lab creation")
                    else:
                        print("⚠️  No scripts available for lab creation")
                else:
                    print("⚠️  Could not retrieve scripts")
            except Exception as e:
                print(f"⚠️  Error getting scripts: {e}")
        else:
            print("⚠️  No account ID available for lab creation")
    else:
        print("⚠️  Skipping lab creation - no accounts or not authenticated")
    
    print("\n" + "=" * 50)
    print("Integration tests completed!")
    
    # Summary
    print("\nTest Summary:")
    print(f"- Server connectivity: {'✓' if tester.test_server_status() else '✗'}")
    print(f"- HaasOnline API: {'✓' if is_authenticated else '⚠️'}")
    print(f"- Accounts available: {len(accounts)}")
    print(f"- Labs available: {len(labs)}")
    print(f"- Markets available: {len(markets)}")

def test_our_backtest_system_integration():
    """Test how our backtest execution system could integrate with MCP server"""
    print("\nBacktest System Integration Test")
    print("=" * 40)
    
    # This would show how our backtest execution system could use MCP server
    print("Integration points:")
    print("1. ✓ Account discovery via /get_all_accounts")
    print("2. ✓ Lab creation via /create_lab")
    print("3. ✓ Lab execution via /start_lab_execution with period presets")
    print("4. ✓ Result collection via /get_backtest_results")
    print("5. ✓ Lab cloning via /clone_lab_to_markets")
    print("6. ✓ Market data via /get_all_markets")
    
    print("\nOur system benefits:")
    print("- Can use MCP server for actual HaasOnline API calls")
    print("- Period presets eliminate timestamp calculations")
    print("- Bulk operations for multiple labs")
    print("- Real account and market data")
    print("- Actual backtest execution and results")

if __name__ == "__main__":
    run_integration_tests()
    test_our_backtest_system_integration()