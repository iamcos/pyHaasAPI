#!/usr/bin/env python3
"""
Data Manager Test with SSH Tunnel

This script establishes an SSH tunnel to srv01 and then tests the data manager.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


async def establish_ssh_tunnel(server_name="srv01"):
    """Establish SSH tunnel to server"""
    try:
        print(f"🔗 Establishing SSH tunnel to {server_name}...")
        
        # SSH command for tunnel
        ssh_cmd = [
            "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
            f"prod@{server_name}"
        ]
        
        # Start SSH process
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        # Wait a moment for tunnel to establish
        await asyncio.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ SSH tunnel established (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ SSH tunnel failed: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to establish SSH tunnel: {e}")
        return None


async def cleanup_ssh_tunnel(process):
    """Clean up SSH tunnel"""
    try:
        if process and process.poll() is None:
            print("🧹 Cleaning up SSH tunnel...")
            process.terminate()
            process.wait(timeout=5)
            print("✅ SSH tunnel cleaned up")
    except Exception as e:
        print(f"⚠️ Error cleaning up SSH tunnel: {e}")


class SimpleDataManager:
    """Simple data manager using v1 API components"""
    
    def __init__(self):
        self.executor = None
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.labs = []
        self.bots = []
        self.accounts = []
        self.backtests = {}
    
    def connect(self, host='127.0.0.1', port=8090, email=None, password=None):
        """Connect using v1 authentication"""
        try:
            # Get credentials from environment
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            email = email or os.getenv('API_EMAIL')
            password = password or os.getenv('API_PASSWORD')
            
            if not email or not password:
                logger.error("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Initialize analyzer and connect
            self.analyzer = HaasAnalyzer(self.cache)
            success = self.analyzer.connect(
                host=host,
                port=port,
                email=email,
                password=password
            )
            
            if success:
                self.executor = self.analyzer.executor
                logger.info("✅ Successfully connected to HaasOnline API")
                return True
            else:
                logger.error("❌ Failed to connect to HaasOnline API")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def fetch_all_data(self):
        """Fetch all data from the server"""
        try:
            logger.info("📊 Fetching all server data...")
            
            # Fetch labs
            self.labs = api.get_all_labs(self.executor)
            logger.info(f"✅ Fetched {len(self.labs)} labs")
            
            # Fetch bots
            self.bots = api.get_all_bots(self.executor)
            logger.info(f"✅ Fetched {len(self.bots)} bots")
            
            # Fetch accounts
            self.accounts = api.get_all_accounts(self.executor)
            logger.info(f"✅ Fetched {len(self.accounts)} accounts")
            
            # Fetch backtests for each lab
            total_backtests = 0
            for lab in self.labs:
                lab_id = lab.lab_id
                try:
                    # Get backtest results for this lab
                    from pyHaasAPI.model import GetBacktestResultRequest
                    request = GetBacktestResultRequest(
                        lab_id=lab_id,
                        next_page_id=0,
                        page_lenght=1000
                    )
                    backtest_results = api.get_backtest_result(self.executor, request)
                    
                    if backtest_results and hasattr(backtest_results, '__iter__'):
                        lab_backtests = list(backtest_results)
                        self.backtests[lab_id] = lab_backtests
                        total_backtests += len(lab_backtests)
                        logger.info(f"✅ Fetched {len(lab_backtests)} backtests for lab {lab_id}")
                    else:
                        logger.warning(f"⚠️ No backtests found for lab {lab_id}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch backtests for lab {lab_id}: {e}")
                    continue
            
            logger.info(f"✅ Total backtests fetched: {total_backtests}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch data: {e}")
            return False
    
    def get_qualifying_backtests(self, min_winrate=55.0, max_drawdown=0.0, min_trades=5):
        """Get qualifying backtests from all labs"""
        qualifying = []
        
        for lab_id, backtests in self.backtests.items():
            for backtest in backtests:
                try:
                    # Extract performance metrics
                    winrate = getattr(backtest, 'WinRate', 0) or 0
                    max_dd = getattr(backtest, 'MaxDrawdown', 0) or 0
                    trades = getattr(backtest, 'TotalTrades', 0) or 0
                    roe = getattr(backtest, 'ROI', 0) or 0
                    
                    # Check qualifying criteria
                    if (winrate >= min_winrate and 
                        max_dd <= max_drawdown and 
                        trades >= min_trades):
                        
                        qualifying.append({
                            'lab_id': lab_id,
                            'backtest_id': getattr(backtest, 'backtest_id', 'unknown'),
                            'roe': roe,
                            'winrate': winrate,
                            'max_drawdown': max_dd,
                            'trades': trades,
                            'script_name': getattr(backtest, 'script_name', 'Unknown'),
                            'script_id': getattr(backtest, 'script_id', 'unknown')
                        })
                        
                except Exception as e:
                    logger.warning(f"Error analyzing backtest: {e}")
                    continue
        
        # Sort by ROE descending
        qualifying.sort(key=lambda x: x['roe'], reverse=True)
        return qualifying
    
    def create_bots_from_qualifying(self, qualifying_backtests, max_bots=5):
        """Create bots from qualifying backtests"""
        created_bots = []
        
        for backtest_data in qualifying_backtests[:max_bots]:
            try:
                # Create bot name
                bot_name = f"{backtest_data['script_name']} - {backtest_data['roe']:.1f}% ROE {backtest_data['winrate']:.1f}% WR"
                
                # Find a suitable account
                target_account = None
                for acc in self.accounts:
                    if "BINANCEFUTURES" in acc.account_name.upper():
                        target_account = acc
                        break
                
                if not target_account:
                    logger.warning("No BinanceFutures account found")
                    continue
                
                # Create bot
                from pyHaasAPI.model import CreateBotRequest
                create_req = CreateBotRequest(
                    bot_name=bot_name,
                    account_id=target_account.account_id,
                    script_id=backtest_data['script_id'],
                    script_settings={},  # Use default settings
                    trade_amount=2000.0,
                    leverage=20.0,
                    margin_mode=0,  # CROSS
                    position_mode=1,  # HEDGE
                    notes=f"Created from lab {backtest_data['lab_id']} backtest {backtest_data['backtest_id']}"
                )
                
                new_bot = api.add_bot(self.executor, create_req)
                created_bots.append({
                    'bot_id': new_bot.bot_id,
                    'bot_name': new_bot.bot_name,
                    'lab_id': backtest_data['lab_id'],
                    'backtest_id': backtest_data['backtest_id']
                })
                
                logger.info(f"✅ Created bot: {new_bot.bot_name}")
                
            except Exception as e:
                logger.warning(f"Failed to create bot from backtest {backtest_data['backtest_id']}: {e}")
                continue
        
        return created_bots
    
    def get_summary(self):
        """Get data summary"""
        return {
            'labs': len(self.labs),
            'bots': len(self.bots),
            'accounts': len(self.accounts),
            'backtests': sum(len(bt) for bt in self.backtests.values()),
            'qualifying_backtests': len(self.get_qualifying_backtests())
        }


async def test_data_manager_with_ssh():
    """Test the data manager with SSH tunnel"""
    print("🚀 Testing Data Manager with SSH Tunnel")
    print("=" * 60)
    
    ssh_process = None
    data_manager = SimpleDataManager()
    
    try:
        # Step 1: Establish SSH tunnel
        ssh_process = await establish_ssh_tunnel("srv01")
        if not ssh_process:
            print("❌ Failed to establish SSH tunnel. Exiting.")
            return 1
        
        # Step 2: Connect to API
        print("\n🔐 Connecting to HaasOnline API...")
        if not data_manager.connect():
            print("❌ Failed to connect to API")
            return 1
        
        print("✅ Connected successfully")
        
        # Step 3: Fetch all data
        print("\n📊 Fetching all server data...")
        if not data_manager.fetch_all_data():
            print("❌ Failed to fetch data")
            return 1
        
        print("✅ Data fetched successfully")
        
        # Step 4: Get summary
        summary = data_manager.get_summary()
        print(f"\n📋 Data Summary:")
        print(f"  Labs: {summary['labs']}")
        print(f"  Bots: {summary['bots']}")
        print(f"  Accounts: {summary['accounts']}")
        print(f"  Backtests: {summary['backtests']}")
        print(f"  Qualifying Backtests: {summary['qualifying_backtests']}")
        
        # Step 5: Get qualifying backtests
        print(f"\n🔍 Analyzing for qualifying backtests (55+ WR, no drawdown)...")
        qualifying = data_manager.get_qualifying_backtests(min_winrate=55.0, max_drawdown=0.0, min_trades=5)
        
        if not qualifying:
            print("⚠️ No qualifying backtests found")
            return 0
        
        print(f"✅ Found {len(qualifying)} qualifying backtests")
        
        # Step 6: Display top results
        print(f"\n🏆 Top qualifying backtests:")
        for i, bt in enumerate(qualifying[:10]):
            print(f"  {i+1}. {bt['roe']:.1f}% ROE, {bt['winrate']:.1f}% WR, {bt['trades']} trades, {bt['max_drawdown']:.1f}% DD")
        
        # Step 7: Create bots
        print(f"\n🤖 Creating bots from top {min(5, len(qualifying))} backtests...")
        created_bots = data_manager.create_bots_from_qualifying(qualifying, max_bots=5)
        
        if created_bots:
            print(f"✅ Created {len(created_bots)} bots:")
            for bot in created_bots:
                print(f"  - {bot['bot_name']} (ID: {bot['bot_id']})")
        else:
            print("⚠️ No bots were created")
        
        print("\n🎉 Data manager test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        # Step 8: Clean up SSH tunnel
        if ssh_process:
            await cleanup_ssh_tunnel(ssh_process)


async def main():
    """Main entry point"""
    return await test_data_manager_with_ssh()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
