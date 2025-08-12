#!/usr/bin/env python3
"""
Test Backtest Start

This script tests starting a backtest on an existing lab to debug the 404 issue.
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI import api
from pyHaasAPI.model import StartLabExecutionRequest
from utils.auth.authenticator import authenticator

# Configure logging
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
    
    executor = authenticator.get_executor()
    logger.info("✅ Authentication successful")
    
    # Get all labs
    logger.info("🔍 Getting all labs...")
    labs = api.get_all_labs(executor)
    
    # Find a lab that's not running (not the Example lab)
    test_lab = None
    for lab in labs:
        if lab.name != "Example" and not lab.name.startswith("Example"):
            test_lab = lab
            break
    
    if not test_lab:
        logger.error("❌ No suitable test lab found")
        return
    
    logger.info(f"📋 Testing with lab: {test_lab.name} (ID: {test_lab.lab_id})")
    
    # Test starting a backtest
    start_time = int(datetime(2025, 4, 7, 14, 0, 0).timestamp())
    end_time = int(datetime(2025, 7, 20, 14, 0, 0).timestamp())
    
    logger.info(f"🚀 Starting backtest from {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)}")
    
    try:
        # Create the request
        request = StartLabExecutionRequest(
            lab_id=test_lab.lab_id,
            start_unix=start_time,
            end_unix=end_time,
            send_email=False
        )
        
        # Start the backtest
        response = api.start_lab_execution(executor, request)
        logger.info(f"✅ Backtest started successfully: {response}")
        
    except Exception as e:
        logger.error(f"❌ Failed to start backtest: {e}")
        
        # Try to get more details about the lab
        try:
            lab_details = api.get_lab_details(executor, test_lab.lab_id)
            logger.info(f"📋 Lab details: {lab_details}")
        except Exception as e2:
            logger.error(f"❌ Failed to get lab details: {e2}")

if __name__ == "__main__":
    main() 