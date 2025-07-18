#!/usr/bin/env python3
"""
Phase 2 Test - Authentication and Lab Cloning
Focused test using Binance BTC/USDT market only
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import time
import random
from loguru import logger
from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest


def setup_logging():
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def test_authentication() -> api.RequestsExecutor:
    """Test authentication"""
    logger.info("🔐 Testing authentication...")
    
    try:
        # Initialize API executor
        executor = api.RequestsExecutor(
            host="127.0.0.1",
            port=8090,
            state=api.Guest()
        )
        
        # Authenticate
        executor = executor.authenticate(
            email="your_email@example.com",
            password="your_password"
        )
        
        logger.info("✅ Authentication successful")
        return executor
        
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        raise


def test_lab_cloning(executor: api.RequestsExecutor):
    """Test lab cloning functionality"""
    logger.info("\n🔄 Testing lab cloning...")
    
    # Get labs and find one with BTC/USDT
    labs = api.get_all_labs(executor)
    btc_labs = [lab for lab in labs if "BTC_USDT" in lab.name or "BTC" in lab.name]
    
    if not btc_labs:
        logger.warning("⚠️ No BTC/USDT labs found, using any available lab")
        btc_labs = labs
    
    if not btc_labs:
        logger.error("❌ No labs available for cloning test")
        return None
    
    # Select a lab to clone
    test_lab = random.choice(btc_labs)
    logger.info(f"🎯 Selected lab to clone: {test_lab.name}")
    
    try:
        # Get lab details
        lab_details = api.get_lab_details(executor, test_lab.lab_id)
        logger.info(f"✅ Retrieved lab details: {len(lab_details.parameters)} parameters")
        
        # Clone the lab
        clone_name = f"Clone_{int(time.time())}"
        cloned_lab = api.clone_lab(executor, test_lab.lab_id, clone_name)
        logger.info(f"✅ Lab cloned successfully: {cloned_lab.name} (ID: {cloned_lab.lab_id})")
        
        # Verify clone has same parameters
        clone_details = api.get_lab_details(executor, cloned_lab.lab_id)
        logger.info(f"✅ Clone verification: {len(clone_details.parameters)} parameters")
        
        # Clean up - delete cloned lab
        api.delete_lab(executor, cloned_lab.lab_id)
        logger.info(f"✅ Cloned lab cleaned up: {cloned_lab.lab_id}")
        
        return cloned_lab
        
    except Exception as e:
        logger.error(f"❌ Lab cloning failed: {e}")
        return None


def main():
    """Main test function"""
    setup_logging()
    
    logger.info("🚀 Starting Phase 2A - Authentication & Lab Cloning Test")
    logger.info("=" * 60)
    
    try:
        # Test authentication
        executor = test_authentication()
        
        # Test lab cloning
        test_lab_cloning(executor)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Phase 2A tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Place the main execution logic here
    pass 