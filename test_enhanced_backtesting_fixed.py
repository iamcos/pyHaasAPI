#!/usr/bin/env python3
"""
Enhanced Backtesting Test - Fixed Version

This script fixes the issues found in the previous test:
- Handles bots with no optimizable parameters
- Fixes lab configuration update issues
- Implements proper parameter analysis
- Uses actual bot parameters instead of assuming optimization
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pyHaasAPI import api
from pyHaasAPI.model import (
    CreateLabRequest, StartLabExecutionRequest, AddBotFromLabRequest,
    GetBacktestResultRequest
)
from pyHaasAPI.price import PriceAPI

class FixedBacktestingTester:
    """Fixed backtesting tester that handles real bot configurations"""
    
    def __init__(self):
        self.executor = None
        self.price_api = None
        
    def authenticate(self):
        """Authenticate with HaasOnline API"""
        print("🔐 Authenticating with HaasOnline API...")
        
        for attempt in range(3):
            try:
                self.executor = api.RequestsExecutor(
                    host="127.0.0.1",
                    port=8090,
                    state=api.Guest()
                ).authenticate(
                    email="your_email@example.com",
                    password="your_password"
                )
                
                self.price_api = PriceAPI(self.executor)
                print("✅ Authentication successful")
                return True
                
            except Exception as e:
                print(f"❌ Authentication attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    print("⏳ Waiting 10 seconds before retry...")
                    time.sleep(10)
                else:
                    print("💥 Authentication failed after all attempts")
                    return False
    
    def get_markets_efficiently(self, exchanges: List[str] = None) -> List[Any]:
        """Get markets efficiently using exchange-specific endpoints"""
        if exchanges is None:
            exchanges = ["BINANCE"]
        
        print(f"📊 Fetching markets efficiently from {exchanges}...")
        all_markets = []
        
        for exchange in exchanges:
            try:
                print(f"  🔍 Fetching {exchange} markets...")
                exchange_markets = self.price_api.get_trade_markets(exchange)
                all_markets.extend(exchange_markets)
                print(f"  ✅ Found {len(exchange_markets)} {exchange} markets")
            except Exception as e:
                print(f"  ⚠️ Failed to get {exchange} markets: {e}")
                continue
        
        print(f"✅ Found {len(all_markets)} total markets across exchanges")
        return all_markets
    
    def find_trading_pairs(self, markets: List[Any], pairs: List[str]) -> Dict[str, List[Any]]:
        """Find markets for specific trading pairs"""
        print(f"🔍 Finding markets for pairs: {pairs}")
        
        pair_to_markets = {}
        for pair in pairs:
            base, quote = pair.split('/')
            matching = [m for m in markets if m.primary == base.upper() and m.secondary == quote.upper()]
            if matching:
                pair_to_markets[pair] = matching
                print(f"  ✅ {pair}: {len(matching)} market(s) found: {[m.price_source for m in matching]}")
            else:
                print(f"  ❌ {pair}: No markets found")
        
        return pair_to_markets
    
    def get_bot_scripts(self, script_names: List[str]) -> Dict[str, Any]:
        """Get bot scripts by name"""
        print(f"🔍 Finding bot scripts: {script_names}")
        
        scripts = {}
        for script_name in script_names:
            try:
                found_scripts = api.get_scripts_by_name(self.executor, script_name)
                if found_scripts:
                    scripts[script_name] = found_scripts[0]
                    print(f"  ✅ {script_name}: Found (ID: {found_scripts[0].script_id})")
                else:
                    print(f"  ❌ {script_name}: Not found")
            except Exception as e:
                print(f"  ❌ {script_name}: Error - {e}")
        
        return scripts
    
    def get_accounts(self) -> List[Any]:
        """Get available accounts"""
        print("🏦 Getting accounts...")
        
        try:
            accounts = api.get_accounts(self.executor)
            if accounts:
                print(f"✅ Found {len(accounts)} account(s)")
                for account in accounts:
                    print(f"  - {account.name} (ID: {account.account_id})")
                return accounts
            else:
                print("❌ No accounts found")
                return []
        except Exception as e:
            print(f"❌ Error getting accounts: {e}")
            return []
    
    def analyze_lab_parameters(self, lab_details) -> Dict[str, Any]:
        """Analyze lab parameters and show what's available"""
        print("🔧 Analyzing lab parameters...")
        
        parameter_analysis = {
            "all_params": [],
            "optimizable_params": [],
            "parameter_details": {}
        }
        
        for param in lab_details.parameters:
            key = param.get('K', '')
            param_type = param.get('T', 0)
            current_options = param.get('O', [])
            is_enabled = param.get('I', True)
            is_selected = param.get('IS', True)
            
            param_info = {
                "key": key,
                "type": param_type,
                "type_name": self.get_param_type_name(param_type),
                "current_options": current_options,
                "is_enabled": is_enabled,
                "is_selected": is_selected,
                "bruteforce": param.get('bruteforce', False),
                "intelligent": param.get('intelligent', False)
            }
            
            parameter_analysis["all_params"].append(key)
            parameter_analysis["parameter_details"][key] = param_info
            
            # Check if parameter is optimizable
            is_optimizable = (
                param.get('bruteforce', False) or 
                param.get('intelligent', False) or
                len(current_options) > 1
            )
            
            if is_optimizable:
                parameter_analysis["optimizable_params"].append(key)
                print(f"  ✅ {key}: Type {param_type} ({self.get_param_type_name(param_type)}), Options: {len(current_options)}")
            else:
                print(f"  📝 {key}: Type {param_type} ({self.get_param_type_name(param_type)}), Value: {current_options[0] if current_options else 'None'}")
        
        print(f"✅ Found {len(parameter_analysis['all_params'])} total parameters")
        print(f"✅ Found {len(parameter_analysis['optimizable_params'])} optimizable parameters")
        return parameter_analysis
    
    def get_param_type_name(self, param_type: int) -> str:
        """Get parameter type name"""
        type_names = {
            0: "INTEGER",
            1: "DECIMAL", 
            2: "BOOLEAN",
            3: "STRING",
            4: "SELECTION"
        }
        return type_names.get(param_type, f"UNKNOWN({param_type})")
    
    def create_lab_simple(self, script_id: str, lab_name: str, account_id: str, 
                         market: str, backtest_hours: int) -> Dict[str, Any]:
        """Create lab with simple configuration (no optimization)"""
        print(f"📋 Creating lab: {lab_name}")
        
        try:
            # Create lab
            lab = api.create_lab(
                self.executor,
                CreateLabRequest(
                    script_id=script_id,
                    name=lab_name,
                    account_id=account_id,
                    market=market,
                    interval=1,
                    default_price_data_style="CandleStick"
                )
            )
            print(f"  ✅ Lab created: {lab.lab_id}")
            
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab.lab_id)
            
            # Analyze parameters (just for information)
            param_analysis = self.analyze_lab_parameters(lab_details)
            
            return {
                "lab": lab,
                "lab_details": lab_details,
                "param_analysis": param_analysis
            }
            
        except Exception as e:
            print(f"  ❌ Failed to create lab: {e}")
            return None
    
    def run_backtest(self, lab_id: str, backtest_hours: int) -> Dict[str, Any]:
        """Run backtest with specified duration"""
        print(f"🚀 Starting {backtest_hours}-hour backtest for lab {lab_id}")
        
        try:
            now = int(time.time())
            start_unix = now - (backtest_hours * 3600)
            end_unix = now
            
            api.start_lab_execution(
                self.executor,
                StartLabExecutionRequest(
                    lab_id=lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=False
                )
            )
            
            print(f"  ✅ Backtest started (period: {backtest_hours} hours)")
            
            return {
                "lab_id": lab_id,
                "start_unix": start_unix,
                "end_unix": end_unix,
                "duration_hours": backtest_hours
            }
            
        except Exception as e:
            print(f"  ❌ Failed to start backtest: {e}")
            return None
    
    def wait_for_backtest_completion(self, lab_id: str, timeout_minutes: int = 30) -> bool:
        """Wait for backtest to complete"""
        print(f"⏳ Waiting for backtest completion (timeout: {timeout_minutes} minutes)...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                details = api.get_lab_details(self.executor, lab_id)
                status = getattr(details, 'status', None)
                
                if status == '3':  # COMPLETED
                    print(f"  ✅ Backtest completed successfully")
                    return True
                elif status == '4':  # CANCELLED
                    print(f"  ❌ Backtest was cancelled")
                    return False
                else:
                    print(f"  🔄 Status: {status} - Waiting...")
                    time.sleep(30)  # Check every 30 seconds
                    
            except Exception as e:
                print(f"  ⚠️ Error checking status: {e}")
                time.sleep(30)
        
        print(f"  ⏰ Backtest timed out after {timeout_minutes} minutes")
        return False
    
    def get_backtest_results(self, lab_id: str) -> Dict[str, Any]:
        """Get backtest results and analyze performance"""
        print(f"📊 Getting backtest results for lab {lab_id}")
        
        try:
            results = api.get_backtest_result(
                self.executor,
                GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=0,
                    page_lenght=1000
                )
            )
            
            if not results.items:
                print(f"  ❌ No backtest results found")
                return None
            
            # Find best configuration
            best_result = max(results.items, key=lambda x: x.summary.ReturnOnInvestment if x.summary else 0)
            
            analysis = {
                "total_configurations": len(results.items),
                "best_roi": best_result.summary.ReturnOnInvestment if best_result.summary else 0,
                "best_backtest_id": best_result.backtest_id,
                "best_parameters": getattr(best_result, 'parameters', {}),
                "average_roi": sum(x.summary.ReturnOnInvestment if x.summary else 0 for x in results.items) / len(results.items),
                "profitable_configs": sum(1 for x in results.items if x.summary and x.summary.ReturnOnInvestment > 0)
            }
            
            print(f"  ✅ Results analyzed:")
            print(f"     Total configurations: {analysis['total_configurations']}")
            print(f"     Best ROI: {analysis['best_roi']:.2f}%")
            print(f"     Average ROI: {analysis['average_roi']:.2f}%")
            print(f"     Profitable configs: {analysis['profitable_configs']}")
            
            return analysis
            
        except Exception as e:
            print(f"  ❌ Failed to get results: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run comprehensive backtesting test"""
        print("🚀 Fixed Enhanced Backtesting Test - MadHatter vs Scalper")
        print("=" * 60)
        
        # 1. Authenticate
        if not self.authenticate():
            return
        
        # 2. Get markets efficiently
        markets = self.get_markets_efficiently(["BINANCE"])
        
        # 3. Find trading pairs
        trading_pairs = ["BTC/USDT", "ETH/BTC"]
        pair_to_markets = self.find_trading_pairs(markets, trading_pairs)
        
        if not pair_to_markets:
            print("❌ No valid markets found for trading pairs")
            return
        
        # 4. Get bot scripts
        script_names = ["MadHatter Bot", "Scalper Bot"]
        scripts = self.get_bot_scripts(script_names)
        
        if not scripts:
            print("❌ No bot scripts found")
            return
        
        # 5. Get accounts
        accounts = self.get_accounts()
        if not accounts:
            print("❌ No accounts available")
            return
        
        account = accounts[0]
        
        # 6. Define test scenarios (reduced for testing)
        test_scenarios = []
        backtest_periods = [24]  # Start with 1 day only for testing
        
        for script_name, script in scripts.items():
            for pair, pair_markets in pair_to_markets.items():
                for market in pair_markets:
                    for hours in backtest_periods:
                        test_scenarios.append({
                            "script_name": script_name,
                            "script_id": script.script_id,
                            "pair": pair,
                            "market": market,
                            "backtest_hours": hours
                        })
        
        print(f"\n📋 Test Scenarios: {len(test_scenarios)} total")
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"  {i}. {scenario['script_name']} - {scenario['pair']} - {scenario['backtest_hours']}h")
        
        # 7. Run tests
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'='*60}")
            print(f"🧪 Test {i}/{len(test_scenarios)}: {scenario['script_name']} - {scenario['pair']} - {scenario['backtest_hours']}h")
            print(f"{'='*60}")
            
            # Create lab name
            lab_name = f"FixedTest_{scenario['script_name'].replace(' ', '_')}_{scenario['pair'].replace('/', '_')}_{scenario['backtest_hours']}h_{int(time.time())}"
            
            # Create lab (simple version)
            lab_result = self.create_lab_simple(
                script_id=scenario['script_id'],
                lab_name=lab_name,
                account_id=account.account_id,
                market=f"{scenario['market'].price_source.upper()}_{scenario['market'].primary.upper()}_{scenario['market'].secondary.upper()}_",
                backtest_hours=scenario['backtest_hours']
            )
            
            if not lab_result:
                print(f"❌ Failed to create lab for scenario {i}")
                continue
            
            # Run backtest
            backtest_result = self.run_backtest(
                lab_id=lab_result['lab'].lab_id,
                backtest_hours=scenario['backtest_hours']
            )
            
            if not backtest_result:
                print(f"❌ Failed to start backtest for scenario {i}")
                continue
            
            # Wait for completion
            completed = self.wait_for_backtest_completion(lab_result['lab'].lab_id)
            
            if not completed:
                print(f"❌ Backtest did not complete for scenario {i}")
                continue
            
            # Get results
            analysis = self.get_backtest_results(lab_result['lab'].lab_id)
            
            if analysis:
                test_result = {
                    "scenario": scenario,
                    "lab_id": lab_result['lab'].lab_id,
                    "analysis": analysis,
                    "param_analysis": lab_result['param_analysis']
                }
                results.append(test_result)
            
            # Clean up lab
            try:
                api.delete_lab(self.executor, lab_result['lab'].lab_id)
                print(f"  🧹 Lab cleaned up")
            except Exception as e:
                print(f"  ⚠️ Failed to clean up lab: {e}")
            
            # Wait between tests
            time.sleep(5)
        
        # 8. Summary report
        self.print_summary_report(results)
    
    def print_summary_report(self, results: List[Dict[str, Any]]):
        """Print comprehensive summary report"""
        print(f"\n{'='*60}")
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*60}")
        
        if not results:
            print("❌ No successful tests completed")
            return
        
        print(f"✅ Total successful tests: {len(results)}")
        
        # Group results by script
        script_results = {}
        for result in results:
            script_name = result['scenario']['script_name']
            if script_name not in script_results:
                script_results[script_name] = []
            script_results[script_name].append(result)
        
        # Analyze each script
        for script_name, script_tests in script_results.items():
            print(f"\n🤖 {script_name} Results:")
            print(f"   Tests completed: {len(script_tests)}")
            
            # Calculate averages
            avg_roi = sum(r['analysis']['best_roi'] for r in script_tests) / len(script_tests)
            avg_configs = sum(r['analysis']['total_configurations'] for r in script_tests) / len(script_tests)
            profitable_rate = sum(1 for r in script_tests if r['analysis']['best_roi'] > 0) / len(script_tests) * 100
            
            print(f"   Average Best ROI: {avg_roi:.2f}%")
            print(f"   Average Configurations: {avg_configs:.0f}")
            print(f"   Profitable Rate: {profitable_rate:.1f}%")
            
            # Best performing test for this script
            best_test = max(script_tests, key=lambda x: x['analysis']['best_roi'])
            print(f"   Best Test: {best_test['scenario']['pair']} - {best_test['scenario']['backtest_hours']}h - ROI: {best_test['analysis']['best_roi']:.2f}%")
        
        # Overall best test
        overall_best = max(results, key=lambda x: x['analysis']['best_roi'])
        print(f"\n🏆 Overall Best Performance:")
        print(f"   Script: {overall_best['scenario']['script_name']}")
        print(f"   Pair: {overall_best['scenario']['pair']}")
        print(f"   Period: {overall_best['scenario']['backtest_hours']} hours")
        print(f"   ROI: {overall_best['analysis']['best_roi']:.2f}%")
        print(f"   Configurations: {overall_best['analysis']['total_configurations']}")
        
        # Parameter analysis summary
        print(f"\n🔧 Parameter Analysis Summary:")
        total_params = sum(len(r['param_analysis']['all_params']) for r in results)
        total_optimizable = sum(len(r['param_analysis']['optimizable_params']) for r in results)
        print(f"   Total parameters analyzed: {total_params}")
        print(f"   Total optimizable parameters: {total_optimizable}")
        print(f"   Average params per bot: {total_params / len(results):.0f}")
        
        print(f"\n🎉 Fixed enhanced backtesting test completed successfully!")

def main():
    """Main function"""
    tester = FixedBacktestingTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 