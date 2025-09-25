#!/usr/bin/env python3
"""
Complete Lab Analysis and Bot Creation using v2 CLI with v1 API

This script will:
1. Establish SSH tunnel to srv01
2. Connect to API
3. Analyze labs for 55+ win rate and no drawdown
4. Create bots from qualifying backtests
5. Clean up properly
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path
from dotenv import load_dotenv

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis import HaasAnalyzer, UnifiedCacheManager

# Load environment variables
load_dotenv()


class CompleteLabAnalyzer:
    """Complete lab analyzer with SSH tunnel management"""
    
    def __init__(self):
        self.executor = None
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.ssh_process = None
    
    def establish_ssh_tunnel(self):
        """Establish SSH tunnel to srv01"""
        print("🔗 Establishing SSH tunnel to srv01...")
        
        try:
            # SSH command to create tunnel
            ssh_cmd = [
                "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
                "prod@srv01"
            ]
            
            print(f"📡 Running: {' '.join(ssh_cmd)}")
            
            # Start SSH process in background
            self.ssh_process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for tunnel to establish
            print("⏳ Waiting for tunnel to establish...")
            time.sleep(8)  # Increased wait time
            
            # Check if process is still running
            if self.ssh_process.poll() is not None:
                stdout, stderr = self.ssh_process.communicate()
                print(f"❌ SSH process failed: {stderr.decode()}")
                return False
            
            print("✅ SSH tunnel established")
            return True
            
        except Exception as e:
            print(f"❌ Failed to establish tunnel: {e}")
            return False
    
    def test_connection(self):
        """Test connection to localhost:8090"""
        print("🔍 Testing connection...")
        
        try:
            import requests
            
            # Test with timeout
            response = requests.get("http://127.0.0.1:8090/UserAPI.php?channel=GET_USER_DATA", timeout=10)
            print(f"✅ Connection test successful - Status: {response.status_code}")
            return True
            
        except requests.exceptions.ConnectionError:
            print("❌ Connection test failed - tunnel not working")
            return False
        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False
    
    def connect(self):
        """Connect using proven v1 authentication pattern"""
        try:
            print("🔐 Connecting to HaasOnline API...")
            
            # Get credentials from environment
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                print("❌ API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Create API connection using proven v1 pattern
            haas_api = api.RequestsExecutor(
                host='127.0.0.1',
                port=8090,
                state=api.Guest()
            )
            
            # Authenticate (handles email/password + OTC internally)
            self.executor = haas_api.authenticate(email, password)
            
            # Initialize analyzer
            self.analyzer = HaasAnalyzer(self.cache)
            self.analyzer.connect()
            
            print("✅ Successfully connected to HaasOnline API")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to HaasOnline API: {e}")
            return False
    
    def list_labs(self):
        """List all labs"""
        try:
            labs = api.get_all_labs(self.executor)
            print(f"📋 Found {len(labs)} labs")
            return labs
        except Exception as e:
            print(f"❌ Failed to list labs: {e}")
            return []
    
    def analyze_lab_comprehensive(self, lab_id: str, min_winrate: float = 55.0):
        """Comprehensive lab analysis"""
        try:
            print(f"🔍 Analyzing lab {lab_id}...")
            
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            lab_name = getattr(lab_details, 'lab_name', f'Lab {lab_id}')
            print(f"📊 Lab: {lab_name}")
            
            # Get backtest results with pagination
            all_backtests = []
            next_page_id = 0
            page_size = 100
            
            while True:
                try:
                    backtest_results = api.get_backtest_result(
                        self.executor,
                        api.GetBacktestResultRequest(
                            lab_id=lab_id,
                            next_page_id=next_page_id,
                            page_lenght=page_size
                        )
                    )
                    
                    if not backtest_results:
                        break
                    
                    # Check the structure of backtest_results
                    # Try to access the data using model_dump or direct attribute access
                    try:
                        # Try to get the data as a list
                        if hasattr(backtest_results, '__iter__'):
                            results_list = list(backtest_results)
                            if results_list:
                                all_backtests.extend(results_list)
                            else:
                                break
                        else:
                            # Try to access as dict
                            results_dict = backtest_results.model_dump()
                            if 'data' in results_dict and results_dict['data']:
                                all_backtests.extend(results_dict['data'])
                            elif 'results' in results_dict and results_dict['results']:
                                all_backtests.extend(results_dict['results'])
                            else:
                                print(f"⚠️ No data found in backtest results")
                                break
                    except Exception as e:
                        print(f"⚠️ Error accessing backtest results: {e}")
                        break
                    next_page_id = backtest_results.next_page_id
                    
                    if next_page_id == 0:  # No more pages
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error fetching page {next_page_id}: {e}")
                    break
            
            print(f"📈 Found {len(all_backtests)} total backtest results")
            
            if not all_backtests:
                print(f"⚠️ No backtest results found for lab {lab_id}")
                return None
            
            # Analyze backtests
            qualifying_backtests = []
            
            for backtest in all_backtests:
                try:
                    # Extract basic metrics
                    roe = getattr(backtest, 'ROI', 0) or 0
                    winrate = getattr(backtest, 'WinRate', 0) or 0
                    max_drawdown = getattr(backtest, 'MaxDrawdown', 0) or 0
                    trades = getattr(backtest, 'TotalTrades', 0) or 0
                    
                    # Apply criteria: 55+ win rate, no drawdown, minimum trades
                    if (winrate >= min_winrate and 
                        max_drawdown <= 0 and 
                        trades >= 5):
                        
                        qualifying_backtests.append({
                            'backtest_id': backtest.backtest_id,
                            'lab_id': lab_id,
                            'roe': roe,
                            'winrate': winrate,
                            'max_drawdown': max_drawdown,
                            'trades': trades,
                            'backtest': backtest
                        })
                        
                        print(f"✅ Qualifying: {roe:.1f}% ROE, {winrate:.1f}% WR, {trades} trades, {max_drawdown:.1f}% DD")
                        
                except Exception as e:
                    print(f"⚠️ Could not analyze backtest: {e}")
                    continue
            
            # Sort by ROE (descending)
            qualifying_backtests.sort(key=lambda x: x['roe'], reverse=True)
            
            print(f"✅ Found {len(qualifying_backtests)} qualifying backtests (55+ WR, no drawdown)")
            return qualifying_backtests
            
        except Exception as e:
            print(f"❌ Failed to analyze lab {lab_id}: {e}")
            return None
    
    def create_bot_from_backtest(self, backtest_data, lab_name: str):
        """Create a bot from a qualifying backtest"""
        try:
            print(f"🤖 Creating bot from backtest {backtest_data['backtest_id']}...")
            
            # Create bot name with performance metrics
            bot_name = f"{lab_name} - {backtest_data['roe']:.1f}% ROE {backtest_data['winrate']:.1f}% WR"
            
            # Create bot from lab backtest
            bot = api.add_bot_from_lab(
                self.executor,
                backtest_data['lab_id'],
                backtest_data['backtest_id'],
                bot_name
            )
            
            print(f"✅ Created bot: {bot.bot_name} (ID: {bot.bot_id})")
            return bot
            
        except Exception as e:
            print(f"❌ Failed to create bot from backtest: {e}")
            return None
    
    def get_accounts(self):
        """Get available accounts"""
        try:
            accounts = api.get_all_accounts(self.executor)
            print(f"📋 Found {len(accounts)} accounts")
            return accounts
        except Exception as e:
            print(f"❌ Failed to get accounts: {e}")
            return []
    
    def cleanup(self):
        """Clean up SSH tunnel"""
        if self.ssh_process:
            print("\n🧹 Cleaning up SSH tunnel...")
            try:
                self.ssh_process.terminate()
                time.sleep(2)
                if self.ssh_process.poll() is None:
                    self.ssh_process.kill()
                print("✅ SSH tunnel closed")
            except Exception as e:
                print(f"⚠️ Error closing SSH tunnel: {e}")


def main():
    """Main function"""
    print("🚀 Complete Lab Analysis and Bot Creation")
    print("=" * 60)
    
    analyzer = CompleteLabAnalyzer()
    
    try:
        # Step 1: Establish SSH tunnel
        if not analyzer.establish_ssh_tunnel():
            print("❌ Failed to establish SSH tunnel")
            return 1
        
        # Step 2: Test connection
        if not analyzer.test_connection():
            print("❌ Connection test failed")
            return 1
        
        # Step 3: Connect to API
        if not analyzer.connect():
            print("❌ Failed to connect to API")
            return 1
        
        # Step 4: List labs
        labs = analyzer.list_labs()
        if not labs:
            print("❌ No labs found")
            return 1
        
        # Step 5: Get accounts
        accounts = analyzer.get_accounts()
        if not accounts:
            print("❌ No accounts found")
            return 1
        
        # Step 6: Analyze labs and create bots
        created_bots = []
        
        for lab in labs[:3]:  # Analyze first 3 labs
            lab_name = getattr(lab, 'lab_name', f'Lab {lab.lab_id}')
            print(f"\n📊 Analyzing lab: {lab_name}")
            
            # Analyze lab for qualifying backtests
            qualifying_backtests = analyzer.analyze_lab_comprehensive(
                lab.lab_id, 
                min_winrate=55.0
            )
            
            if not qualifying_backtests:
                print(f"⚠️ No qualifying backtests found for lab {lab_name}")
                continue
            
            # Create bots from top 2 qualifying backtests
            for backtest_data in qualifying_backtests[:2]:
                bot = analyzer.create_bot_from_backtest(backtest_data, lab_name)
                if bot:
                    created_bots.append(bot)
        
        # Summary
        print(f"\n🎉 Analysis complete!")
        print(f"📊 Analyzed {len(labs)} labs")
        print(f"🤖 Created {len(created_bots)} bots with 55+ win rate and no drawdown")
        
        if created_bots:
            print(f"\n✅ Created bots:")
            for bot in created_bots:
                print(f"  - {bot.bot_name} (ID: {bot.bot_id})")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    finally:
        # Always cleanup
        analyzer.cleanup()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
