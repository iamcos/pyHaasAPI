#!/usr/bin/env python3
"""
Phase 2 Test - Advanced Lab Analytics
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
            email="garrypotterr@gmail.com",
            password="IQYTCQJIQYTCQJ"
        )
        
        logger.info("✅ Authentication successful")
        return executor
        
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        raise


def test_advanced_lab_analytics(executor: api.RequestsExecutor):
    """Test advanced lab analytics functions"""
    logger.info("\n📊 Testing advanced lab analytics...")
    
    # Get labs with completed backtests, prefer BTC/USDT
    labs = api.get_all_labs(executor)
    btc_labs = [lab for lab in labs if ("BTC_USDT" in lab.name or "BTC" in lab.name) and lab.completed_backtests > 0]
    
    if not btc_labs:
        logger.warning("⚠️ No BTC/USDT labs with backtests, using any available")
        completed_labs = [lab for lab in labs if lab.completed_backtests > 0]
        if not completed_labs:
            logger.warning("⚠️ No labs with completed backtests for analytics testing")
            return None
        btc_labs = completed_labs
    
    # Select a lab with completed backtests
    test_lab = random.choice(btc_labs)
    logger.info(f"🎯 Selected lab for analytics: {test_lab.name} ({test_lab.completed_backtests} backtests)")
    
    # Get backtest results to find a backtest ID
    try:
        backtest_results = api.get_backtest_result(
            executor,
            GetBacktestResultRequest(
                lab_id=test_lab.lab_id,
                next_page_id=0,
                page_lenght=5  # Reduced for faster response
            )
        )
        
        if backtest_results.items:
            backtest = backtest_results.items[0]
            backtest_id = backtest.backtest_id
            
            # Test get backtest runtime
            try:
                runtime = api.get_backtest_runtime(executor, test_lab.lab_id, backtest_id)
                logger.info(f"✅ Backtest runtime retrieved: {len(str(runtime))} chars")
            except Exception as e:
                logger.error(f"❌ Get backtest runtime failed: {e}")
            
            # Test get backtest chart
            try:
                chart = api.get_backtest_chart(executor, test_lab.lab_id, backtest_id)
                logger.info(f"✅ Backtest chart retrieved: {len(chart) if isinstance(chart, dict) else 'N/A'} data points")
            except Exception as e:
                logger.error(f"❌ Get backtest chart failed: {e}")
            
            # Test get backtest log
            try:
                log_entries = api.get_backtest_log(executor, test_lab.lab_id, backtest_id)
                logger.info(f"✅ Backtest log retrieved: {len(log_entries)} entries")
            except Exception as e:
                logger.error(f"❌ Get backtest log failed: {e}")
                
        else:
            logger.warning("⚠️ No backtest results found for analytics testing")
            
    except Exception as e:
        logger.error(f"❌ Backtest results retrieval failed: {e}")
    
    return test_lab


def main():
    """Main test function"""
    setup_logging()
    
    logger.info("🚀 Starting Phase 2C - Advanced Analytics Test")
    logger.info("=" * 60)
    
    try:
        # Test authentication
        executor = test_authentication()
        
        # Test advanced lab analytics
        test_advanced_lab_analytics(executor)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Phase 2C tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Place the main execution logic here
    pass 