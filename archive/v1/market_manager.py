"""
Market Manager for HaasOnline
Consolidated market fetching, formatting, and management
"""

import logging
from typing import Dict, List, Any, Optional
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.model import CloudMarket
from pyHaasAPI_v1.price import PriceAPI

logger = logging.getLogger(__name__)

class MarketManager:
    """Consolidated market management and fetching"""
    
    def __init__(self, executor):
        self.executor = executor
        self.price_api = PriceAPI(executor)
        self._markets_cache = {}
        self._accounts_cache = {}
        
    def get_markets_efficiently(self, exchanges: List[str]) -> List[CloudMarket]:
        """
        Get markets efficiently for specified exchanges
        
        Args:
            exchanges: List of exchange codes (e.g., ["BINANCE", "BYBIT"])
            
        Returns:
            List of CloudMarket objects
        """
        all_markets = []
        
        for exchange in exchanges:
            try:
                logger.info(f"📊 Fetching markets for {exchange}...")
                markets = self.price_api.get_trade_markets(exchange)
                
                if markets:
                    all_markets.extend(markets)
                    logger.info(f"  ✅ Found {len(markets)} markets for {exchange}")
                else:
                    logger.warning(f"  ⚠️ No markets found for {exchange}")
                    
            except Exception as e:
                logger.error(f"  ❌ Error fetching markets for {exchange}: {e}")
        
        # Cache the markets
        self._markets_cache = {f"{m.price_source}_{m.primary}_{m.secondary}": m for m in all_markets}
        
        return all_markets
    
    def get_market_by_pair(self, exchange: str, primary: str, secondary: str) -> Optional[CloudMarket]:
        """
        Get a specific market by exchange and pair
        
        Args:
            exchange: Exchange code (e.g., "BINANCE")
            primary: Primary currency (e.g., "BTC")
            secondary: Secondary currency (e.g., "USDT")
            
        Returns:
            CloudMarket object or None if not found
        """
        cache_key = f"{exchange}_{primary}_{secondary}"
        
        if cache_key in self._markets_cache:
            return self._markets_cache[cache_key]
        
        # If not in cache, fetch all markets for this exchange
        markets = self.get_markets_efficiently([exchange])
        
        # Find the specific market
        for market in markets:
            if (market.price_source.upper() == exchange.upper() and 
                market.primary.upper() == primary.upper() and 
                market.secondary.upper() == secondary.upper()):
                return market
        
        return None
    
    def format_market_string(self, market: CloudMarket) -> str:
        """
        Format market to the correct string format for HaasOnline
        
        Args:
            market: CloudMarket object
            
        Returns:
            Formatted market string (e.g., "BINANCE_BTC_USDT_")
        """
        return f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
    
    def get_accounts(self, force_refresh: bool = False) -> List[Any]:
        """
        Get user accounts with caching
        
        Args:
            force_refresh: Force refresh the cache
            
        Returns:
            List of account objects
        """
        if not force_refresh and self._accounts_cache:
            return list(self._accounts_cache.values())
        
        try:
            logger.info("📊 Fetching user accounts...")
            accounts = api.get_accounts(self.executor)
            
            # Cache accounts
            self._accounts_cache = {acc.account_id: acc for acc in accounts}
            
            logger.info(f"  ✅ Found {len(accounts)} accounts")
            return accounts
            
        except Exception as e:
            logger.error(f"  ❌ Error fetching accounts: {e}")
            return []
    
    def get_test_account(self) -> Optional[Any]:
        """
        Get the first test/simulated account
        
        Returns:
            Account object or None if not found
        """
        accounts = self.get_accounts()
        
        # Look for test accounts first
        test_accounts = [acc for acc in accounts if acc.is_simulated or acc.is_test_net]
        
        if test_accounts:
            logger.info(f"  ✅ Found test account: {test_accounts[0].name}")
            return test_accounts[0]
        
        # Fall back to first account
        if accounts:
            logger.info(f"  ✅ Using first account: {accounts[0].name}")
            return accounts[0]
        
        return None
    
    def get_scripts_by_name(self, script_names: List[str]) -> Dict[str, Any]:
        """
        Get scripts by name with efficient caching
        
        Args:
            script_names: List of script names to find
            
        Returns:
            Dict mapping script names to script objects
        """
        try:
            logger.info("📊 Fetching scripts...")
            all_scripts = api.get_all_scripts(self.executor)
            
            found_scripts = {}
            for script in all_scripts:
                for name in script_names:
                    if name.lower() in script.script_name.lower():
                        found_scripts[name] = script
                        logger.info(f"  ✅ Found script: {script.script_name}")
                        break
            
            return found_scripts
            
        except Exception as e:
            logger.error(f"  ❌ Error fetching scripts: {e}")
            return {}
    
    def get_madhatter_script(self) -> Optional[Any]:
        """
        Get the MadHatter script specifically
        
        Returns:
            Script object or None if not found
        """
        try:
            logger.info("📊 Fetching scripts...")
            all_scripts = api.get_all_scripts(self.executor)
            
            # Priority 1: Look for the main MadHatter Bot (most specific)
            for script in all_scripts:
                if "Haasonline Original - MadHatter Bot" in script.script_name:
                    logger.info(f"  ✅ Found main MadHatter Bot: {script.script_name}")
                    return script
            
            # Priority 2: Look for any script with "MadHatter" and "Bot"
            for script in all_scripts:
                if "MadHatter" in script.script_name and "Bot" in script.script_name:
                    logger.info(f"  ✅ Found MadHatter Bot: {script.script_name}")
                    return script
            
            # Priority 3: Look for any script with just "MadHatter" (fallback)
            for script in all_scripts:
                if "MadHatter" in script.script_name and "RSI" not in script.script_name and "MACD" not in script.script_name and "BBands" not in script.script_name:
                    logger.info(f"  ✅ Found MadHatter script: {script.script_name}")
                    return script
            
            # Priority 4: Last resort - any MadHatter script
            for script in all_scripts:
                if "MadHatter" in script.script_name:
                    logger.info(f"  ✅ Found MadHatter component: {script.script_name}")
                    return script
            
            logger.error("  ❌ No MadHatter script found")
            return None
            
        except Exception as e:
            logger.error(f"  ❌ Error fetching scripts: {e}")
            return None
    
    def get_scalper_script(self) -> Optional[Any]:
        """
        Get the Scalper script specifically
        
        Returns:
            Script object or None if not found
        """
        scripts = self.get_scripts_by_name(["Scalper"])
        return scripts.get("Scalper")
    
    def validate_market_setup(self, exchange: str, primary: str, secondary: str) -> Dict[str, Any]:
        """
        Validate that a market setup is complete and ready for use
        
        Args:
            exchange: Exchange code
            primary: Primary currency
            secondary: Secondary currency
            
        Returns:
            Dict with validation results
        """
        logger.info(f"🔍 Validating market setup: {exchange} {primary}/{secondary}")
        
        validation = {
            "market_found": False,
            "account_found": False,
            "script_found": False,
            "ready": False,
            "market": None,
            "account": None,
            "script": None
        }
        
        # Check market
        market = self.get_market_by_pair(exchange, primary, secondary)
        if market:
            validation["market_found"] = True
            validation["market"] = market
            logger.info(f"  ✅ Market found: {self.format_market_string(market)}")
        else:
            logger.error(f"  ❌ Market not found: {exchange} {primary}/{secondary}")
        
        # Check account
        account = self.get_test_account()
        if account:
            validation["account_found"] = True
            validation["account"] = account
            logger.info(f"  ✅ Account found: {account.name}")
        else:
            logger.error("  ❌ No account found")
        
        # Check script (try MadHatter first)
        script = self.get_madhatter_script()
        if script:
            validation["script_found"] = True
            validation["script"] = script
            logger.info(f"  ✅ Script found: {script.script_name}")
        else:
            logger.error("  ❌ MadHatter script not found")
        
        # Overall readiness
        validation["ready"] = all([
            validation["market_found"],
            validation["account_found"],
            validation["script_found"]
        ])
        
        if validation["ready"]:
            logger.info("  ✅ Market setup is ready!")
        else:
            logger.error("  ❌ Market setup is incomplete")
        
        return validation 
 