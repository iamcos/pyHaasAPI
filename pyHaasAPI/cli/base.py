#!/usr/bin/env python3
"""
Base CLI Classes for pyHaasAPI

This module provides base classes with proven working patterns extracted from
the most comprehensive and working CLI tools in the codebase.
"""

import os
import sys
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.api import RequestsExecutor, Guest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BaseCLI(ABC):
    """Base class for all CLI tools with proven working authentication pattern"""
    
    def __init__(self):
        self.executor = None
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup consistent logging for all CLI tools"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def connect(self) -> bool:
        """
        PROVEN working authentication pattern from analyze_from_cache.py
        Includes smart cache-only mode fallback
        """
        try:
            # Check if we have cached data first (smart fallback)
            cached_labs = self.get_cached_labs()
            if cached_labs:
                self.logger.info(f"📁 Found {len(cached_labs)} labs with cached data - using cache-only mode")
                self.logger.info("✅ Cache-only mode activated (no API connection required)")
                return True
            
            self.logger.info("🔌 No cached data found - attempting to connect to HaasOnline API...")
            
            # Initialize analyzer with cache
            self.analyzer = HaasAnalyzer(self.cache)
            
            # Connect using the proven pattern
            if not self.analyzer.connect():
                self.logger.error("❌ Failed to connect to HaasOnline API")
                return False
                
            # Store executor for direct API access if needed
            self.executor = self.analyzer.executor
            self.logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_cached_labs(self) -> Dict[str, int]:
        """Get dictionary of labs with cached data and their backtest counts"""
        cache_dir = self.cache.base_dir / "backtests"
        if not cache_dir.exists():
            return {}
        
        # Get unique lab IDs from cached files with counts
        lab_counts = {}
        for cache_file in cache_dir.glob("*.json"):
            lab_id = cache_file.name.split('_')[0]
            lab_counts[lab_id] = lab_counts.get(lab_id, 0) + 1
        
        return lab_counts
    
    @abstractmethod
    def run(self, args) -> bool:
        """Main execution method - must be implemented by subclasses"""
        pass


class BaseAnalysisCLI(BaseCLI):
    """Base class for analysis-related CLI tools with proven working patterns"""
    
    def filter_labs(self, all_labs: List[Any], lab_ids: List[str] = None, 
                   exclude_lab_ids: List[str] = None) -> List[Any]:
        """PROVEN working lab filtering logic from mass_bot_creator.py"""
        filtered_labs = []
        
        for lab in all_labs:
            lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            
            # If specific lab IDs are provided, only include those
            if lab_ids:
                if lab_id in lab_ids:
                    filtered_labs.append(lab)
                continue
            
            # If exclude lab IDs are provided, skip those
            if exclude_lab_ids:
                if lab_id in exclude_lab_ids:
                    continue
            
            # If no filters, include all labs
            filtered_labs.append(lab)
        
        return filtered_labs
    
    def sort_backtests(self, backtests: List[Any], sort_by: str) -> List[Any]:
        """PROVEN working backtest sorting logic from analyze_from_cache.py"""
        if sort_by.lower() == 'roe':
            # Calculate ROE (Return on Equity) - using realized profits / starting balance
            return sorted(backtests, key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
        elif sort_by.lower() == 'roi':
            return sorted(backtests, key=lambda x: x.roi_percentage, reverse=True)
        elif sort_by.lower() == 'winrate':
            return sorted(backtests, key=lambda x: x.win_rate, reverse=True)
        elif sort_by.lower() == 'profit':
            return sorted(backtests, key=lambda x: x.realized_profits_usdt, reverse=True)
        elif sort_by.lower() == 'trades':
            return sorted(backtests, key=lambda x: x.total_trades, reverse=True)
        else:
            # Default to ROE sorting (most comprehensive)
            return sorted(backtests, key=lambda x: (x.realized_profits_usdt / max(x.starting_balance, 1)) * 100, reverse=True)
    
    def print_summary(self, result: Dict[str, Any], title: str = "SUMMARY"):
        """Standard summary printing with consistent formatting"""
        self.logger.info("=" * 60)
        self.logger.info(f"📊 {title}")
        self.logger.info("=" * 60)
        
        for key, value in result.items():
            if isinstance(value, (int, float)):
                self.logger.info(f"{key}: {value}")
            else:
                self.logger.info(f"{key}: {value}")
        
        self.logger.info("=" * 60)


class BaseBotCLI(BaseCLI):
    """Base class for bot management CLI tools"""
    
    def __init__(self):
        super().__init__()
        self.accounts = []
        self.account_index = 0
    
    def get_next_account(self) -> Optional[Dict]:
        """PROVEN working account assignment from mass_bot_creator.py"""
        if not self.accounts:
            self.logger.error("❌ No accounts available")
            return None
            
        # Use round-robin assignment
        account = self.accounts[self.account_index % len(self.accounts)]
        self.account_index += 1
        
        return account
    
    def filter_bots(self, all_bots: List[Any], bot_ids: List[str] = None, 
                   exclude_bot_ids: List[str] = None) -> List[Any]:
        """PROVEN working bot filtering logic from fix_bot_trade_amounts.py"""
        filtered_bots = []
        
        for bot in all_bots:
            bot_id = getattr(bot, 'bot_id', None) or getattr(bot, 'ID', '')
            
            # If specific bot IDs are provided, only include those
            if bot_ids:
                if bot_id in bot_ids:
                    filtered_bots.append(bot)
                continue
            
            # If exclude bot IDs are provided, skip those
            if exclude_bot_ids:
                if bot_id in exclude_bot_ids:
                    continue
            
            # If no filters, include all bots
            filtered_bots.append(bot)
        
        return filtered_bots


class BaseDirectAPICLI(BaseCLI):
    """Base class for CLI tools that need direct API access (not through HaasAnalyzer)"""
    
    def connect(self) -> bool:
        """Direct API connection pattern from price_tracker.py and fix_bot_trade_amounts.py"""
        try:
            self.logger.info("🔌 Connecting to HaasOnline API...")
            
            # Initialize executor with proven pattern
            haas_api = RequestsExecutor(
                host=os.getenv('API_HOST', '127.0.0.1'),
                port=int(os.getenv('API_PORT', 8090)),
                state=Guest()
            )
            
            # Authenticate using proven pattern
            self.executor = haas_api.authenticate(
                os.getenv('API_EMAIL'), 
                os.getenv('API_PASSWORD')
            )
            
            self.logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False















