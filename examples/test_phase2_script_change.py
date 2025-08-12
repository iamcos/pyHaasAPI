#!/usr/bin/env python3
"""
Phase 2 Test - Lab Script Change
Focused test using BTC/USDT labs only
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import time
import random
from loguru import logger
from pyHaasAPI import api


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
            email="garrypotterr@gmail.com",
            password="IQYTCQJIQYTCQJ"
        )
        
        logger.info("✅ Authentication successful")
        return executor
        
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        raise


def test_lab_script_change(executor: api.RequestsExecutor):
    """Test changing lab script functionality"""
    logger.info("\n🔄 Testing lab script change...")
    
    # Get labs and scripts, prefer BTC/USDT
    labs = api.get_all_labs(executor)
    btc_labs = [lab for lab in labs if "BTC_USDT" in lab.name or "BTC" in lab.name]
    
    if not btc_labs:
        logger.warning("⚠️ No BTC/USDT labs found, using any available lab")
        btc_labs = labs
    
    scripts = api.get_all_scripts(executor)
    
    if not btc_labs or not scripts:
        logger.warning("⚠️ Need both labs and scripts for script change testing")
        return None
    
    # Select a lab and a different script
    test_lab = random.choice(btc_labs)
    original_script_id = test_lab.script_id
    
    # Find a different script
    different_scripts = [s for s in scripts if s.script_id != original_script_id]
    if not different_scripts:
        logger.warning("⚠️ No different scripts available for testing")
        return None
    
    new_script = random.choice(different_scripts)
    
    try:
        # Change the lab's script
        updated_lab = api.change_lab_script(executor, test_lab.lab_id, new_script.script_id)
        logger.info(f"✅ Lab script changed: {test_lab.name} -> {new_script.script_name}")
        
        # Verify the change
        lab_details = api.get_lab_details(executor, test_lab.lab_id)
        if lab_details.script_id == new_script.script_id:
            logger.info("✅ Script change verified")
        else:
            logger.warning("⚠️ Script change verification failed")
        
        # Change back to original script
        api.change_lab_script(executor, test_lab.lab_id, original_script_id)
        logger.info("✅ Lab script restored to original")
        
        return updated_lab
        
    except Exception as e:
        logger.error(f"❌ Lab script change failed: {e}")
        return None


def main():
    """Main test function"""
    setup_logging()
    
    logger.info("🚀 Starting Phase 2D - Lab Script Change Test")
    logger.info("=" * 60)
    
    try:
        # Test authentication
        executor = test_authentication()
        
        # Test lab script change
        test_lab_script_change(executor)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Phase 2D tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Place the main execution logic here
    pass 