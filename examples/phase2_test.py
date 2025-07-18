#!/usr/bin/env python3
"""
Phase 2 Test Script: Advanced Lab Features & Script Management

This script tests the new Phase 2 features we've implemented:
- Lab cloning
- Script management (add, edit, delete, publish)
- Advanced lab analytics (runtime, charts, logs)
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import random
import time
from loguru import logger

from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, StartLabExecutionRequest, GetBacktestResultRequest
from pyHaasAPI.domain import BacktestPeriod


def setup_logging():
    """Configure logging for the test script"""
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def test_authentication() -> api.RequestsExecutor:
    """Test authentication and return authenticated executor"""
    logger.info("🔐 Testing authentication...")
    
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    )
    
    # Authenticate
    executor = executor.authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    
    logger.info("✅ Authentication successful")
    return executor


def test_lab_cloning(executor: api.RequestsExecutor):
    """Test lab cloning functionality"""
    logger.info("\n🔄 Testing lab cloning...")
    
    # Get existing labs
    labs = api.get_all_labs(executor)
    if not labs:
        logger.warning("⚠️ No existing labs to clone")
        return None
    
    # Select a lab to clone
    original_lab = random.choice(labs)
    logger.info(f"🎯 Selected lab to clone: {original_lab.name}")
    
    # Get lab details
    lab_details = api.get_lab_details(executor, original_lab.lab_id)
    logger.info(f"✅ Retrieved lab details: {len(lab_details.parameters)} parameters")
    
    # Clone the lab
    try:
        cloned_lab = api.clone_lab(executor, original_lab.lab_id, f"Clone_{int(time.time())}")
        logger.info(f"✅ Lab cloned successfully: {cloned_lab.name} (ID: {cloned_lab.lab_id})")
        
        # Verify clone has same parameters
        cloned_details = api.get_lab_details(executor, cloned_lab.lab_id)
        logger.info(f"✅ Clone verification: {len(cloned_details.parameters)} parameters")
        
        # Clean up cloned lab
        api.delete_lab(executor, cloned_lab.lab_id)
        logger.info(f"✅ Cloned lab cleaned up: {cloned_lab.lab_id}")
        
        return cloned_lab
        
    except Exception as e:
        logger.error(f"❌ Lab cloning failed: {e}")
        return None


def test_script_management(executor: api.RequestsExecutor):
    """Test script management functions"""
    logger.info("\n📝 Testing script management...")
    
    # Get existing scripts
    scripts = api.get_all_scripts(executor)
    logger.info(f"✅ Found {len(scripts)} existing scripts")
    
    if not scripts:
        logger.warning("⚠️ No scripts available for testing")
        return None
    
    # Test get script item
    test_script = random.choice(scripts)
    try:
        script_details = api.get_script_item(executor, test_script.script_id)
        logger.info(f"✅ Script details retrieved: {script_details.script_name}")
    except Exception as e:
        logger.error(f"❌ Get script item failed: {e}")
    
    # Test add script (with a simple test script)
    test_script_content = """
// Simple test script
function OnTick()
{
    // Test function
    return;
}
"""
    
    try:
        new_script = api.add_script(
            executor, 
            f"TestScript_{int(time.time())}", 
            test_script_content,
            "Test script for API validation",
            0  # Use numeric script type instead of string
        )
        logger.info(f"✅ Script added: {new_script.script_name} (ID: {new_script.script_id})")
        
        # Test edit script
        edited_script = api.edit_script(
            executor,
            new_script.script_id,
            script_name=f"Edited_{new_script.script_name}"
        )
        logger.info(f"✅ Script edited: {edited_script.script_name}")
        
        # Clean up - delete test script
        api.delete_script(executor, new_script.script_id)
        logger.info(f"✅ Test script deleted: {new_script.script_id}")
        
        return new_script
        
    except Exception as e:
        logger.error(f"❌ Script management failed: {e}")
        return None


def test_advanced_lab_analytics(executor: api.RequestsExecutor):
    """Test advanced lab analytics functions"""
    logger.info("\n📊 Testing advanced lab analytics...")
    
    # Get labs with completed backtests
    labs = api.get_all_labs(executor)
    completed_labs = [lab for lab in labs if lab.completed_backtests > 0]
    
    if not completed_labs:
        logger.warning("⚠️ No labs with completed backtests for analytics testing")
        return None
    
    # Select a lab with completed backtests
    test_lab = random.choice(completed_labs)
    logger.info(f"🎯 Selected lab for analytics: {test_lab.name} ({test_lab.completed_backtests} backtests)")
    
    # Get backtest results to find a backtest ID
    try:
        backtest_results = api.get_backtest_result(
            executor,
            GetBacktestResultRequest(
                lab_id=test_lab.lab_id,
                next_page_id=0,
                page_lenght=10
            )
        )
        
        if backtest_results.items:
            backtest = backtest_results.items[0]
            backtest_id = backtest.backtest_id
            
            # Test get backtest runtime
            try:
                runtime = api.get_backtest_runtime(executor, test_lab.lab_id, backtest_id)
                logger.info(f"✅ Backtest runtime retrieved: {runtime}")
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


def test_lab_script_change(executor: api.RequestsExecutor):
    """Test changing lab script functionality"""
    logger.info("\n🔄 Testing lab script change...")
    
    # Get labs and scripts
    labs = api.get_all_labs(executor)
    scripts = api.get_all_scripts(executor)
    
    if not labs or not scripts:
        logger.warning("⚠️ Need both labs and scripts for script change testing")
        return None
    
    # Select a lab and a different script
    test_lab = random.choice(labs)
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
    
    logger.info("🚀 Starting Phase 2 API test")
    logger.info("=" * 60)
    
    try:
        # Test authentication
        executor = test_authentication()
        
        # Test lab cloning
        test_lab_cloning(executor)
        
        # Test script management
        test_script_management(executor)
        
        # Test advanced lab analytics
        test_advanced_lab_analytics(executor)
        
        # Test lab script change
        test_lab_script_change(executor)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Phase 2 tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Place the main execution logic here
    pass 