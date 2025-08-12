"""
Clone Existing Example Lab to Trending Markets

This script clones the existing \"Example\" lab to a list of trending markets.
The Example lab should already be configured with intelligent mode parameters.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI import api
from pyHaasAPI.model import CloudMarket
from utils.auth.authenticator import authenticator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrendingLabCloner:
    def __init__(self):
        self.executor = None
        self.account = None
        self.example_lab_id = None
        self.cloned_labs = []
        
        # Target markets
        self.trending_crypto_pairs = [
            "NEXO/BTC", "TON/BTC", "ZRO/BTC", "XRP/BTC", "GT/BTC", "TIDAL/USDT",
            "MTV/USDT", "PROS/USDT", "1EARTH/USDT", "NYAN/USDT", "XTZ/BTC",
            "BCH/BTC", "FLOKI/BTC", "XMR/BTC", "CAKE/BTC", "DOP/USDT", "DADDY/USDT",
            "SHILL/USDT", "CARR/USDT", "NURA/USDT", "BDX/BTC", "ENA/BTC",
            "KINGSHIB/USDT", "CHRP/USDT", "SKYA/USDT", "ATM/USDT", "STRONG/USDT",
            "HBAR/BTC", "MOTHER/USDT", "XPR/USDT", "YALA/USDT", "STRD/USDT",
            "DONKEY/USDT", "LINK/BTC", "QNT/BTC", "THETA/BTC", "PUMP/USDT",
            "IOTX/USDT", "IP/USDT", "MAX/USDT", "LTO/USDT", "INJ/BTC", "TAO/BTC",
            "RENDER/BTC", "LAUNCHCOIN/USDT", "XDB/USDT", "M87/USDT", "DSYNC/USDT"
        ]
        
    def setup(self):
        """Initialize authentication and get account"""
        logger.info("🔐 Setting up authentication...")
        
        # Authenticate
        success = authenticator.authenticate()
        if not success:
            raise Exception("Authentication failed")
        
        # Get the authenticated executor
        self.executor = authenticator.get_executor()
        
        # Get any available account
        accounts = api.get_accounts(self.executor)
        
        if not accounts:
            raise Exception("No accounts found")
        
        self.account = accounts[0]
        logger.info(f"✅ Using account: {self.account.name} ({self.account.account_id})")
        
    def find_example_lab(self):
        """Find the existing Example lab"""
        logger.info("🔍 Looking for existing Example lab...")
        
        # Get all labs
        labs = api.get_all_labs(self.executor)
        
        # Find the Example lab
        example_labs = [lab for lab in labs if lab.name == "Example"]
        
        if not example_labs:
            raise Exception("Example lab not found. Please create it first with intelligent mode configuration.")
        
        self.example_lab_id = example_labs[0].lab_id
        logger.info(f"✅ Found Example lab: {example_labs[0].name} (ID: {self.example_lab_id})")
        
        return example_labs[0]

    def get_all_markets(self) -> List[CloudMarket]:
        """Get all available markets"""
        logger.info("Getting all available markets...")
        all_markets = api.get_all_markets(self.executor)
        logger.info(f"Found {len(all_markets)} markets.")
        return all_markets

    def find_matching_markets(self, all_markets: List[CloudMarket]) -> Dict[str, List[CloudMarket]]:
        """Find markets that match the trending pairs"""
        logger.info("Finding matching markets for trending pairs...")
        matched_markets = {}
        for pair in self.trending_crypto_pairs:
            primary_coin, secondary_coin = pair.split('/')
            matches = []
            for market in all_markets:
                if (market.primary == primary_coin and market.secondary == secondary_coin) or \
                   (market.primary == primary_coin):
                    matches.append(market)
            
            if matches:
                matched_markets[pair] = matches
                logger.info(f"Found {len(matches)} matches for {pair}")
        
        logger.info(f"Found matches for {len(matched_markets)} pairs.")
        return matched_markets

    def clone_to_trending_markets(self, matched_markets: Dict[str, List[CloudMarket]]):
        """Clone the example lab to the trending markets"""
        logger.info(f"🔄 Cloning lab to {len(matched_markets)} trending markets...")
        
        for pair, markets in matched_markets.items():
            for market in markets:
                try:
                    # Generate lab name
                    timestamp = int(time.time())
                    lab_name = f"Clone_{market.primary}_{market.secondary}_{market.price_source}_{timestamp}"
                    
                    logger.info(f"  Cloning to {market.format_market_tag(market.price_source)}...")
                    
                    # Clone lab
                    cloned_lab = api.clone_lab(self.executor, self.example_lab_id, lab_name)
                    
                    # Update market tag and account ID
                    lab_details = api.get_lab_details(self.executor, cloned_lab.lab_id)
                    lab_details.settings.market_tag = market.format_market_tag(market.price_source)
                    lab_details.settings.account_id = self.account.account_id
                    updated_lab = api.update_lab_details(self.executor, lab_details)
                    
                    self.cloned_labs.append({
                        'lab': updated_lab,
                        'market_pair': pair,
                        'market_tag': lab_details.settings.market_tag
                    })
                    
                    logger.info(f"  ✅ Cloned: {updated_lab.name} -> {lab_details.settings.market_tag}")
                    
                    # Small delay to avoid rate limits
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to clone to {market.primary}/{market.secondary} on {market.price_source}: {e}")
                    continue
        
        logger.info(f"✅ Successfully cloned {len(self.cloned_labs)} labs")

    def run_complete_workflow(self):
        """Run the complete workflow"""
        logger.info("🚀 Starting complete lab cloning workflow...")
        
        try:
            # Step 1: Setup
            self.setup()
            
            # Step 2: Find existing Example lab
            self.find_example_lab()
            
            # Step 3: Get all markets
            all_markets = self.get_all_markets()

            # Step 4: Find matching markets
            matched_markets = self.find_matching_markets(all_markets)

            # Step 5: Clone to trending markets
            self.clone_to_trending_markets(matched_markets)
            
            logger.info("🎉 Complete workflow finished successfully!")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            raise

def main():
    """Main function"""
    load_dotenv()
    
    cloner = TrendingLabCloner()
    cloner.run_complete_workflow()

if __name__ == "__main__":
    main()
