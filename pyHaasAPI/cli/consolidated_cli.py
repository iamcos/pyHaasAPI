#!/usr/bin/env python3
"""
Consolidated pyHaasAPI v2 CLI - All functionality in one place

This is the main CLI that consolidates all the working functionality from:
- working_cli.py
- working_v2_cli.py  
- simple_v2_cli.py
- simple_working_v2_cli.py

Uses the v2 pyHaasAPI architecture with PHP endpoints.
"""

import os
import sys
import argparse
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Use v2 API components
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.api.lab import LabAPI
from pyHaasAPI.api.bot import BotAPI
from pyHaasAPI.api.account import AccountAPI
from pyHaasAPI.api.backtest import BacktestAPI
from pyHaasAPI.api.market import MarketAPI
from pyHaasAPI.api.script import ScriptAPI
from pyHaasAPI.api.order import OrderAPI
from pyHaasAPI.services.lab import LabService
from pyHaasAPI.services.bot import BotService
from pyHaasAPI.services.analysis import AnalysisService
from pyHaasAPI.services.analysis_manager import AnalysisManager
from pyHaasAPI.services.bot_manager import BotManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.config.logging_config import LoggingConfig
from pyHaasAPI.core.logging import get_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = get_logger("consolidated_cli")


class ConsolidatedCLI:
    """Consolidated v2 CLI with all functionality"""
    
    def __init__(self):
        self.client: Optional[AsyncHaasClient] = None
        self.auth_manager: Optional[AuthenticationManager] = None
        self.server_manager: Optional[ServerManager] = None
        
        # API modules
        self.lab_api: Optional[LabAPI] = None
        self.bot_api: Optional[BotAPI] = None
        self.account_api: Optional[AccountAPI] = None
        self.backtest_api: Optional[BacktestAPI] = None
        self.market_api: Optional[MarketAPI] = None
        self.script_api: Optional[ScriptAPI] = None
        self.order_api: Optional[OrderAPI] = None
        
        # Services
        self.lab_service: Optional[LabService] = None
        self.bot_service: Optional[BotService] = None
        self.analysis_service: Optional[AnalysisService] = None
        
        # Centralized managers
        self.analysis_manager: Optional[AnalysisManager] = None
        self.bot_manager: Optional[BotManager] = None
        
    async def connect(self) -> bool:
        """Connect using v2 authentication and server manager"""
        try:
            # Get credentials from environment
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                logger.error("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Initialize server manager
            self.server_manager = ServerManager()
            
            # Ensure tunnel is available
            if not await self.server_manager.ensure_srv03_tunnel():
                logger.error("Failed to establish SSH tunnel to srv03")
                return False
            
            # Preflight check
            if not await self.server_manager.preflight_check():
                logger.error("Preflight check failed - tunnel not available")
                return False
            
            # Create API config
            logging_config = LoggingConfig()
            config = APIConfig(
                host='127.0.0.1',
                port=8090,
                logging=logging_config
            )
            
            # Create client
            self.client = AsyncHaasClient(config)
            
            # Create authentication manager
            self.auth_manager = AuthenticationManager(self.client, config)
            
            # Authenticate
            await self.auth_manager.authenticate(email, password)
            
            # Initialize API modules
            self.lab_api = LabAPI(self.client)
            self.bot_api = BotAPI(self.client)
            self.account_api = AccountAPI(self.client)
            self.backtest_api = BacktestAPI(self.client)
            self.market_api = MarketAPI(self.client)
            self.script_api = ScriptAPI(self.client)
            self.order_api = OrderAPI(self.client)
            
            # Initialize services
            self.lab_service = LabService(self.client)
            self.bot_service = BotService(self.client)
            self.analysis_service = AnalysisService(self.client)
            
            # Initialize centralized managers
            self.analysis_manager = AnalysisManager(self.lab_api, self.analysis_service)
            self.bot_manager = BotManager(self.bot_service)
            
            logger.info("✅ Successfully connected to HaasOnline API using v2 client")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to HaasOnline API: {e}")
            return False
    
    async def list_labs(self) -> List[Dict[str, Any]]:
        """List all labs using v2 API"""
        try:
            labs = await self.lab_api.get_all_labs()
            logger.info(f"📋 Found {len(labs)} labs")
            return labs
        except Exception as e:
            logger.error(f"❌ Failed to list labs: {e}")
            return []
    
    async def analyze_lab(self, lab_id: str, min_winrate: float = 55.0, sort_by: str = "roe") -> Dict[str, Any]:
        """Analyze a single lab with zero drawdown requirement using centralized manager"""
        return await self.analysis_manager.analyze_lab_with_zero_drawdown(lab_id, min_winrate, sort_by)
    
    async def analyze_all_labs(self, min_winrate: float = 55.0, sort_by: str = "roe") -> Dict[str, Any]:
        """Analyze all labs with zero drawdown requirement using centralized manager"""
        return await self.analysis_manager.analyze_all_labs_with_zero_drawdown(min_winrate, sort_by)
    
    async def create_bot_from_backtest(self, backtest_id: str, lab_name: str, script_name: str, 
                                     roi_percentage: float, win_rate: float) -> Dict[str, Any]:
        """Create a bot from a backtest using centralized manager"""
        return await self.bot_manager.create_bot_from_backtest(backtest_id, lab_name, script_name, roi_percentage, win_rate)
    
    async def create_bots_from_analysis(self, lab_results: Dict[str, Any], bots_per_lab: int = 2) -> List[Dict[str, Any]]:
        """Create top bots for each lab with zero drawdown using centralized manager"""
        return await self.bot_manager.create_bots_from_analysis(lab_results, bots_per_lab)
    
    def print_analysis_report(self, lab_results: Dict[str, Any]):
        """Print analysis report"""
        print("\n" + "="*80)
        print("📊 LAB ANALYSIS REPORT - ZERO DRAWDOWN BOTS ONLY (v2 API)")
        print("="*80)
        
        for lab_id, data in lab_results.items():
            print(f"\n🔬 Lab: {data['lab_name']} ({lab_id[:8]})")
            print(f"   Script: {data['script_name']}")
            print(f"   Market: {data['market_tag']}")
            print(f"   Qualifying Bots: {data['total_backtests']}")
            print(f"   Average ROI: {data['average_roi']:.2f}%")
            print(f"   Best ROI: {data['best_roi']:.2f}%")
            print(f"   Average Win Rate: {data['average_win_rate']:.2f}%")
            print(f"   Best Win Rate: {data['best_win_rate']:.2f}%")
            
            print(f"   Top Performers:")
            for i, bt in enumerate(data['top_backtests'][:5], 1):
                print(f"     {i}. ROI: {bt.roi_percentage:.2f}% | WR: {bt.win_rate*100:.1f}% | Trades: {bt.total_trades} | DD: {bt.max_drawdown:.2f}")
        
        print("="*80)
    
    def print_bot_creation_report(self, created_bots: List[Dict[str, Any]]):
        """Print bot creation report"""
        print("\n" + "="*80)
        print("🤖 BOT CREATION REPORT (v2 API)")
        print("="*80)
        
        for bot in created_bots:
            print(f"\n✅ Bot Created:")
            print(f"   Lab ID: {bot['lab_id'][:8]}")
            print(f"   Bot ID: {bot['bot_id'][:8]}")
            print(f"   Name: {bot['bot_name']}")
            print(f"   ROI: {bot['roi_percentage']:.2f}%")
            print(f"   Win Rate: {bot['win_rate']*100:.1f}%")
        
        print(f"\n🎯 Total Bots Created: {len(created_bots)}")
        print("="*80)
    
    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.close()


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Consolidated pyHaasAPI v2 CLI - Zero Drawdown Analysis & Bot Creation (v2 API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze labs and create top 2 bots for each
  python -m pyHaasAPI.cli.consolidated_cli --analyze --create-bots --bots-per-lab 2
  
  # Analyze with custom win rate threshold
  python -m pyHaasAPI.cli.consolidated_cli --analyze --min-winrate 60
  
  # Just analyze without creating bots
  python -m pyHaasAPI.cli.consolidated_cli --analyze
        """
    )
    
    parser.add_argument('--analyze', action='store_true', help='Analyze labs with zero drawdown requirement')
    parser.add_argument('--create-bots', action='store_true', help='Create bots from analysis results')
    parser.add_argument('--min-winrate', type=float, default=55.0, help='Minimum win rate percentage (default: 55)')
    parser.add_argument('--bots-per-lab', type=int, default=2, help='Number of bots to create per lab (default: 2)')
    parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate'], default='roe', help='Sort by metric (default: roe)')
    
    args = parser.parse_args()
    
    if not args.analyze and not args.create_bots:
        parser.print_help()
        return 0
    
    # Initialize CLI
    cli = ConsolidatedCLI()
    
    try:
        # Connect to API
        if not await cli.connect():
            logger.error("Failed to connect to API")
            return 1
        
        lab_results = {}
        
        # Analyze labs if requested
        if args.analyze:
            lab_results = await cli.analyze_all_labs(
                min_winrate=args.min_winrate,
                sort_by=args.sort_by
            )
            
            if lab_results:
                cli.print_analysis_report(lab_results)
            else:
                logger.warning("No qualifying labs found")
                return 0
        
        # Create bots if requested
        if args.create_bots:
            if not lab_results:
                # Re-analyze if not already done
                lab_results = await cli.analyze_all_labs(
                    min_winrate=args.min_winrate,
                    sort_by=args.sort_by
                )
            
            if lab_results:
                created_bots = await cli.create_bots_from_analysis(lab_results, args.bots_per_lab)
                if created_bots:
                    cli.print_bot_creation_report(created_bots)
                else:
                    logger.warning("No bots were created")
            else:
                logger.warning("No qualifying labs found for bot creation")
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await cli.close()


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
