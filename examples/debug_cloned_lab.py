#!/usr/bin/env python3
"""
Debug Cloned Lab Config

This script examines one of the cloned labs to see what went wrong with config copying.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI import api
from utils.auth.authenticator import authenticator

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    load_dotenv()
    
    logger.info("🔐 Setting up authentication...")
    
    # Authenticate
    success = authenticator.authenticate()
    if not success:
        raise Exception("Authentication failed")
    
    # Get the authenticated executor
    executor = authenticator.get_executor()
    
    # Find cloned labs
    logger.info("🔍 Looking for cloned labs...")
    labs = api.get_all_labs(executor)
    cloned_labs = [lab for lab in labs if lab.name.startswith("MadHatter_")]
    
    logger.info(f"Found {len(cloned_labs)} cloned labs:")
    
    for i, lab in enumerate(cloned_labs[:3], 1):  # Check first 3
        logger.info(f"\n📋 Cloned Lab {i}:")
        logger.info(f"  ID: {lab.lab_id}")
        logger.info(f"  Name: {lab.name}")
        logger.info(f"  Status: {lab.status}")
        
        # Get detailed lab info
        lab_details = api.get_lab_details(executor, lab.lab_id)
        
        logger.info(f"  Config: {lab_details.config}")
        
        # Try to access config as dict
        if hasattr(lab_details.config, '__dict__'):
            logger.info(f"  Config dict: {lab_details.config.__dict__}")
        
        # Try to access individual fields
        try:
            logger.info(f"  MP (Max Population): {getattr(lab_details.config, 'max_positions', 'N/A')}")
            logger.info(f"  MG (Max Generation): {getattr(lab_details.config, 'max_generations', 'N/A')}")
            logger.info(f"  ME (Max Elites): {getattr(lab_details.config, 'max_evaluations', 'N/A')}")
            logger.info(f"  MR (Mix Ratio): {getattr(lab_details.config, 'min_roi', 'N/A')}")
            logger.info(f"  AR (Adjust Ratio): {getattr(lab_details.config, 'acceptable_risk', 'N/A')}")
        except Exception as e:
            logger.error(f"  Error accessing config fields: {e}")
        
        # Check settings
        logger.info(f"  Market Tag: {lab_details.settings.market_tag}")
        logger.info(f"  Account ID: {lab_details.settings.account_id}")

if __name__ == "__main__":
    main() 