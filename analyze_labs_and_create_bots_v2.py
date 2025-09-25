#!/usr/bin/env python3
"""
Analyze Labs and Create Bots using v2 CLI with v1 API

This script uses the v2 CLI structure but with v1 API components that work reliably.
It will analyze labs on srv01 and create bots with 55+ win rate and no drawdown.
"""

import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.tools.utils import fetch_all_lab_backtests

# Load environment variables
load_dotenv()


class LabAnalyzerV2:
    """Lab analyzer using v2 CLI structure with v1 API components"""
    
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
            time.sleep(5)
            
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
    
    def analyze_lab(self, lab_id: str, min_winrate: float = 55.0, sort_by: str = "roe"):
        """Analyze a single lab"""
        try:
            print(f"🔍 Analyzing lab {lab_id}...")
            
            # Get all backtests for this lab
            backtests = fetch_all_lab_backtests(self.executor, lab_id)
            print(f"📊 Found {len(backtests)} backtests for lab {lab_id}")
            
            if not backtests:
                print(f"⚠️ No backtests found for lab {lab_id}")
                return None
            
            # Analyze backtests with criteria
            qualifying_backtests = []
            
            for backtest in backtests:
                try:
                    # Get backtest runtime data
                    runtime_data = api.get_backtest_runtime(self.executor, lab_id, backtest.backtest_id)
                    
                    # Extract performance metrics
                    roe = getattr(runtime_data, 'ROI', 0) or 0
                    winrate = getattr(runtime_data, 'WinRate', 0) or 0
                    max_drawdown = getattr(runtime_data, 'MaxDrawdown', 0) or 0
                    trades = getattr(runtime_data, 'TotalTrades', 0) or 0
                    
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
                            'runtime_data': runtime_data
                        })
                        
                except Exception as e:
                    print(f"⚠️ Could not analyze backtest {backtest.backtest_id}: {e}")
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
            
            # Get lab details for market info
            lab_details = api.get_lab_details(self.executor, backtest_data['lab_id'])
            market_tag = getattr(lab_details, 'market_tag', 'UNKNOWN')
            
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
            
            # Configure bot settings
            try:
                # Set leverage to 20x
                api.edit_bot_parameter(
                    self.executor,
                    bot,
                    leverage=20.0
                )
                
                # Set margin mode to CROSS
                api.edit_bot_parameter(
                    self.executor,
                    bot,
                    margin_mode=0  # CROSS
                )
                
                # Set position mode to HEDGE
                api.edit_bot_parameter(
                    self.executor,
                    bot,
                    position_mode=1  # HEDGE
                )
                
                # Set trade amount to $2000 USDT
                api.edit_bot_parameter(
                    self.executor,
                    bot,
                    trade_amount=2000.0
                )
                
                print(f"✅ Configured bot settings: 20x leverage, CROSS margin, HEDGE mode, $2000 trade amount")
                
            except Exception as e:
                print(f"⚠️ Could not configure bot settings: {e}")
            
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
    
    def assign_bot_to_account(self, bot, account):
        """Assign bot to account"""
        try:
            # Use the migrate function to assign bot to account
            result = api.migrate_bot_to_account(
                self.executor,
                bot.bot_id,
                account.account_id,
                preserve_settings=True,
                position_mode=1,
                margin_mode=0,
                leverage=20.0
            )
            
            print(f"✅ Assigned bot {bot.bot_name} to account {account.account_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to assign bot to account: {e}")
            return False
    
    def cleanup(self):
        """Clean up SSH tunnel"""
        if self.ssh_process:
            print("\n🧹 Cleaning up SSH tunnel...")
            try:
                self.ssh_process.terminate()
                time.sleep(1)
                if self.ssh_process.poll() is None:
                    self.ssh_process.kill()
                print("✅ SSH tunnel closed")
            except Exception as e:
                print(f"⚠️ Error closing SSH tunnel: {e}")


def main():
    """Main function"""
    print("🚀 Lab Analysis and Bot Creation using v2 CLI with v1 API")
    print("=" * 70)
    
    analyzer = LabAnalyzerV2()
    
    try:
        # Step 1: Establish SSH tunnel
        if not analyzer.establish_ssh_tunnel():
            print("❌ Failed to establish SSH tunnel")
            return 1
        
        # Step 2: Connect to API
        if not analyzer.connect():
            print("❌ Failed to connect to API")
            return 1
        
        # Step 3: List labs
        labs = analyzer.list_labs()
        if not labs:
            print("❌ No labs found")
            return 1
        
        # Step 4: Get accounts
        accounts = analyzer.get_accounts()
        if not accounts:
            print("❌ No accounts found")
            return 1
        
        # Step 5: Analyze labs and create bots
        created_bots = []
        
        for lab in labs[:5]:  # Analyze first 5 labs
            print(f"\n📊 Analyzing lab: {lab.lab_name}")
            
            # Analyze lab for qualifying backtests
            qualifying_backtests = analyzer.analyze_lab(
                lab.lab_id, 
                min_winrate=55.0, 
                sort_by="roe"
            )
            
            if not qualifying_backtests:
                print(f"⚠️ No qualifying backtests found for lab {lab.lab_name}")
                continue
            
            # Create bots from top 3 qualifying backtests
            for backtest_data in qualifying_backtests[:3]:
                bot = analyzer.create_bot_from_backtest(backtest_data, lab.lab_name)
                if bot:
                    created_bots.append(bot)
                    
                    # Assign to first available account
                    if accounts:
                        account = accounts[0]  # Use first account
                        analyzer.assign_bot_to_account(bot, account)
        
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
