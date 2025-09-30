"""
Authentication utilities for pyHaasAPI
"""

import time
import logging
from typing import Optional
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.price import PriceAPI
from config.settings import (
    API_HOST, API_PORT, API_EMAIL, API_PASSWORD,
    AUTH_RETRY_ATTEMPTS, AUTH_RETRY_DELAY
)

logger = logging.getLogger(__name__)

class Authenticator:
    """Centralized authentication handler"""
    
    def __init__(self):
        self.executor = None
        self.price_api = None
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with HaasOnline API with retry logic"""
        logger.info("🔐 Authenticating with HaasOnline API...")
        
        for attempt in range(AUTH_RETRY_ATTEMPTS):
            try:
                self.executor = api.RequestsExecutor(
                    host=API_HOST,
                    port=API_PORT,
                    state=api.Guest()
                ).authenticate(
                    email=API_EMAIL,
                    password=API_PASSWORD
                )
                
                self.price_api = PriceAPI(self.executor)
                self._authenticated = True
                logger.info("✅ Authentication successful")
                return True
                
            except Exception as e:
                logger.error(f"❌ Authentication attempt {attempt + 1} failed: {e}")
                if attempt < AUTH_RETRY_ATTEMPTS - 1:
                    logger.info(f"⏳ Waiting {AUTH_RETRY_DELAY} seconds before retry...")
                    time.sleep(AUTH_RETRY_DELAY)
                else:
                    logger.error("💥 Authentication failed after all attempts")
                    return False
        
        return False
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        return self._authenticated
    
    def get_executor(self):
        """Get the authenticated executor"""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        return self.executor
    
    def get_price_api(self):
        """Get the price API instance"""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        return self.price_api
    
    def logout(self):
        """Logout and cleanup"""
        self.executor = None
        self.price_api = None
        self._authenticated = False
        logger.info("👋 Logged out")

# Global authenticator instance
authenticator = Authenticator() 