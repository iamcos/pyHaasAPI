#!/usr/bin/env python3
"""
Debug Lab Config

This script examines the Example lab's actual config parameters to understand the issue.
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
    
    # Find the Example lab
    logger.info("🔍 Looking for Example labs...")
    labs = api.get_all_labs(executor)
    example_labs = [lab for lab in labs if lab.name == "Example"]
    
    if not example_labs:
        raise Exception("Example lab not found.")
    
    logger.info(f"Found {len(example_labs)} Example labs:")
    
    for i, lab in enumerate(example_labs, 1):
        logger.info(f"\n📋 Example Lab {i}:")
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
        
        # Check if this is the running one
        if lab.status == 1:  # Assuming 1 means running
            logger.info("  ⚡ This is the RUNNING lab")
        else:
            logger.info("  💤 This is the IDLE lab")

if __name__ == "__main__":
    main() 