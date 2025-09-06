"""
Market data fetching utilities for pyHaasAPI
"""

import logging
from typing import List, Dict, Any, Optional
from pyHaasAPI import api
from pyHaasAPI.price import PriceAPI
from config.settings import DEFAULT_EXCHANGES, DEFAULT_TRADING_PAIRS

logger = logging.getLogger(__name__)

class MarketFetcher:
    """Centralized market data fetching handler"""
    
    def __init__(self, executor):
        self.executor = executor
        self.price_api = PriceAPI(executor)
    
    def get_markets_efficiently(self, exchanges: List[str] = None) -> List[Any]:
        """Get markets efficiently using exchange-specific endpoints"""
        if exchanges is None:
            exchanges = DEFAULT_EXCHANGES
        
        logger.info(f"📊 Fetching markets efficiently from {exchanges}...")
        all_markets = []
        
        for exchange in exchanges:
            try:
                logger.info(f"  🔍 Fetching {exchange} markets...")
                exchange_markets = self.price_api.get_trade_markets(exchange)
                all_markets.extend(exchange_markets)
                logger.info(f"  ✅ Found {len(exchange_markets)} {exchange} markets")
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to get {exchange} markets: {e}")
                continue
        
        logger.info(f"✅ Found {len(all_markets)} total markets across exchanges")
        return all_markets
    
    def find_trading_pairs(self, markets: List[Any], pairs: List[str] = None) -> Dict[str, List[Any]]:
        """Find markets for specific trading pairs"""
        if pairs is None:
            pairs = DEFAULT_TRADING_PAIRS
            
        logger.info(f"🔍 Finding markets for pairs: {pairs}")
        
        pair_to_markets = {}
        for pair in pairs:
            base, quote = pair.split('/')
            matching = [m for m in markets if m.primary == base.upper() and m.secondary == quote.upper()]
            if matching:
                pair_to_markets[pair] = matching
                logger.info(f"  ✅ {pair}: {len(matching)} market(s) found: {[m.price_source for m in matching]}")
            else:
                logger.warning(f"  ❌ {pair}: No markets found")
        
        return pair_to_markets
    
    def get_bot_scripts(self, executor, script_names: List[str]) -> Dict[str, Any]:
        """Get bot scripts by name"""
        logger.info(f"🔍 Finding bot scripts: {script_names}")
        
        scripts = {}
        for script_name in script_names:
            try:
                found_scripts = api.get_scripts_by_name(executor, script_name)
                if found_scripts:
                    scripts[script_name] = found_scripts[0]
                    logger.info(f"  ✅ {script_name}: Found (ID: {found_scripts[0].script_id})")
                else:
                    logger.warning(f"  ❌ {script_name}: Not found")
            except Exception as e:
                logger.error(f"  ❌ {script_name}: Error - {e}")
        
        return scripts
    
    def get_accounts(self, executor) -> List[Any]:
        """Get available accounts"""
        logger.info("🏦 Getting accounts...")
        
        try:
            accounts = api.get_accounts(executor)
            if accounts:
                logger.info(f"✅ Found {len(accounts)} account(s)")
                for account in accounts:
                    logger.info(f"  - {account.name} (ID: {account.account_id})")
                return accounts
            else:
                logger.warning("❌ No accounts found")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting accounts: {e}")
            return []
    
    def format_market_string(self, market) -> str:
        """Format market object to string format required by API"""
        return f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_" 
        """Format market object to string format required by API"""
        return f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_" 
        """Format market object to string format required by API"""
        return f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_" 