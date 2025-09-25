#!/usr/bin/env python3
"""
Simple Lab Analysis using v2 CLI with v1 API

This script assumes the SSH tunnel is already established and focuses on lab analysis and bot creation.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.tools.utils import fetch_all_lab_backtests

# Load environment variables
load_dotenv()


class SimpleLabAnalyzer:
    """Simple lab analyzer using v1 API components"""
    
    def __init__(self):
        self.executor = None
        self.analyzer = None
        self.cache = UnifiedCacheManager()
    
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
    
    def analyze_lab_simple(self, lab_id: str, min_winrate: float = 55.0):
        """Simple lab analysis using cached data or basic API calls"""
        try:
            print(f"🔍 Analyzing lab {lab_id}...")
            
            # Get lab details first
            lab_details = api.get_lab_details(self.executor, lab_id)
            print(f"📊 Lab: {lab_details.lab_name}")
            
            # Get backtest results
            backtest_results = api.get_backtest_result(
                self.executor,
                api.GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=0,
                    page_lenght=100
                )
            )
            
            if not backtest_results or not backtest_results.data:
                print(f"⚠️ No backtest results found for lab {lab_id}")
                return None
            
            print(f"📈 Found {len(backtest_results.data)} backtest results")
            
            # Analyze backtests
            qualifying_backtests = []
            
            for backtest in backtest_results.data:
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
                        
                        print(f"✅ Qualifying backtest: {roe:.1f}% ROE, {winrate:.1f}% WR, {trades} trades")
                        
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


def main():
    """Main function"""
    print("🚀 Simple Lab Analysis and Bot Creation")
    print("=" * 50)
    
    analyzer = SimpleLabAnalyzer()
    
    try:
        # Step 1: Connect to API
        if not analyzer.connect():
            print("❌ Failed to connect to API")
            return 1
        
        # Step 2: List labs
        labs = analyzer.list_labs()
        if not labs:
            print("❌ No labs found")
            return 1
        
        # Step 3: Get accounts
        accounts = analyzer.get_accounts()
        if not accounts:
            print("❌ No accounts found")
            return 1
        
        # Step 4: Analyze labs and create bots
        created_bots = []
        
        for lab in labs[:3]:  # Analyze first 3 labs
            print(f"\n📊 Analyzing lab: {lab.lab_name}")
            
            # Analyze lab for qualifying backtests
            qualifying_backtests = analyzer.analyze_lab_simple(
                lab.lab_id, 
                min_winrate=55.0
            )
            
            if not qualifying_backtests:
                print(f"⚠️ No qualifying backtests found for lab {lab.lab_name}")
                continue
            
            # Create bots from top 2 qualifying backtests
            for backtest_data in qualifying_backtests[:2]:
                bot = analyzer.create_bot_from_backtest(backtest_data, lab.lab_name)
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


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
