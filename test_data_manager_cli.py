#!/usr/bin/env python3
"""
Test Data Manager CLI

This script tests the data manager CLI functionality with srv01.
"""

import asyncio
import subprocess
import sys
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
        print(f"Connecting to {server_name}...")
        
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
        await asyncio.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"SSH tunnel established (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"SSH tunnel failed: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"Failed to establish SSH tunnel: {e}")
        return None


async def cleanup_ssh_tunnel(process):
    """Clean up SSH tunnel"""
    try:
        if process and process.poll() is None:
            print("Cleaning up SSH tunnel...")
            process.terminate()
            process.wait(timeout=5)
            print("SSH tunnel cleaned up")
    except Exception as e:
        print(f"Error cleaning up SSH tunnel: {e}")


class DataManagerCLI:
    """Simple data manager CLI for testing"""
    
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
                logger.info("Successfully connected to HaasOnline API")
                return True
            else:
                logger.error("Failed to connect to HaasOnline API")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def fetch_all_data(self):
        """Fetch all data from the server"""
        try:
            logger.info("Fetching all server data...")
            
            # Fetch labs
            self.labs = api.get_all_labs(self.executor)
            logger.info(f"Fetched {len(self.labs)} labs")
            
            # Fetch bots
            self.bots = api.get_all_bots(self.executor)
            logger.info(f"Fetched {len(self.bots)} bots")
            
            # Fetch accounts
            self.accounts = api.get_all_accounts(self.executor)
            logger.info(f"Fetched {len(self.accounts)} accounts")
            
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
                        page_lenght=100
                    )
                    backtest_results = api.get_backtest_result(self.executor, request)
                    
                    if backtest_results and hasattr(backtest_results, '__iter__'):
                        # Convert to list and get the actual backtest objects
                        result_list = list(backtest_results)
                        
                        # Find the "items" tuple
                        for result_tuple in result_list:
                            if result_tuple[0] == "items":
                                lab_backtests = result_tuple[1]  # This is the list of LabBacktestResult objects
                                self.backtests[lab_id] = lab_backtests
                                total_backtests += len(lab_backtests)
                                logger.info(f"Fetched {len(lab_backtests)} backtests for lab {lab_id}")
                                break
                        else:
                            logger.warning(f"No backtests found for lab {lab_id}")
                    else:
                        logger.warning(f"No backtest results for lab {lab_id}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch backtests for lab {lab_id}: {e}")
                    continue
            
            logger.info(f"Total backtests fetched: {total_backtests}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return False
    
    def get_qualifying_backtests(self, min_winrate=55.0, max_drawdown=0.0, min_trades=5):
        """Get qualifying backtests from all labs"""
        qualifying = []
        
        for lab_id, backtests in self.backtests.items():
            for backtest in backtests:
                try:
                    # Extract performance metrics from summary
                    summary = backtest.summary
                    if not summary:
                        continue
                    
                    roi = getattr(summary, 'ReturnOnInvestment', 0) or 0
                    realized_profits = getattr(summary, 'RealizedProfits', 0) or 0
                    
                    # For now, use basic criteria (positive ROI)
                    if roi > 0:
                        qualifying.append({
                            'lab_id': lab_id,
                            'backtest_id': backtest.backtest_id,
                            'roi': roi,
                            'realized_profits': realized_profits,
                            'generation': backtest.generation_idx,
                            'population': backtest.population_idx,
                            'market_tag': backtest.settings.market_tag if backtest.settings else 'Unknown'
                        })
                        
                except Exception as e:
                    logger.warning(f"Error analyzing backtest: {e}")
                    continue
        
        # Sort by ROI descending
        qualifying.sort(key=lambda x: x['roi'], reverse=True)
        return qualifying
    
    def get_summary(self):
        """Get data summary"""
        return {
            'labs': len(self.labs),
            'bots': len(self.bots),
            'accounts': len(self.accounts),
            'backtests': sum(len(bt) for bt in self.backtests.values()),
            'qualifying_backtests': len(self.get_qualifying_backtests())
        }


async def test_data_manager_cli():
    """Test the data manager CLI functionality"""
    print("Testing Data Manager CLI")
    print("=" * 60)
    
    ssh_process = None
    data_manager = DataManagerCLI()
    
    try:
        # Step 1: Establish SSH tunnel
        ssh_process = await establish_ssh_tunnel("srv01")
        if not ssh_process:
            print("Failed to establish SSH tunnel. Exiting.")
            return 1
        
        # Step 2: Connect to API
        print("\nConnecting to HaasOnline API...")
        if not data_manager.connect():
            print("Failed to connect to API")
            return 1
        
        print("Connected successfully")
        
        # Step 3: Fetch all data
        print("\nFetching all server data...")
        if not data_manager.fetch_all_data():
            print("Failed to fetch data")
            return 1
        
        print("Data fetched successfully")
        
        # Step 4: Get summary
        summary = data_manager.get_summary()
        print(f"\nData Summary:")
        print(f"  Labs: {summary['labs']}")
        print(f"  Bots: {summary['bots']}")
        print(f"  Accounts: {summary['accounts']}")
        print(f"  Backtests: {summary['backtests']}")
        print(f"  Qualifying Backtests: {summary['qualifying_backtests']}")
        
        # Step 5: Get qualifying backtests
        print(f"\nAnalyzing for qualifying backtests (positive ROI)...")
        qualifying = data_manager.get_qualifying_backtests()
        
        if not qualifying:
            print("No qualifying backtests found")
            return 0
        
        print(f"Found {len(qualifying)} qualifying backtests")
        
        # Step 6: Display top results
        print(f"\nTop qualifying backtests:")
        for i, bt in enumerate(qualifying[:10]):
            print(f"  {i+1}. {bt['roi']:.1f}% ROI, ${bt['realized_profits']:.2f} profit, {bt['market_tag']}")
        
        print("\nData Manager CLI test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up SSH tunnel
        if ssh_process:
            await cleanup_ssh_tunnel(ssh_process)


async def main():
    """Main entry point"""
    return await test_data_manager_cli()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

