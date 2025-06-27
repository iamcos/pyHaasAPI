#!/usr/bin/env python3
"""
Phase 2 Test - Script Management
Focused test for script CRUD operations
"""

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
            email="your_email@example.com",
            password="your_password"
        )
        
        logger.info("✅ Authentication successful")
        return executor
        
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        raise


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
    
    # Test add script (with a minimal valid HaasScript)
    test_script_content = """
function OnTick()
    -- Minimal valid script for HaasScript
    return 1
end
"""
    
    try:
        new_script = api.add_script(
            executor, 
            f"TestScript_{int(time.time())}", 
            test_script_content,
            "Test script for API validation",
            0  # Use numeric script type
        )
        logger.info(f"✅ Script added: {new_script.script_name} (ID: {new_script.script_id})")
        
        # Test edit script
        edited_script = api.edit_script(
            executor,
            new_script.script_id,
            script_name=f"Edited_{new_script.script_name}",
            script_content=test_script_content,
            description="Test script for API validation"
        )
        if isinstance(edited_script, dict):
            logger.info("⚠️ Partial response from edit_script (likely compile log only):")
            # Print compile log if available
            cl = None
            if "CL" in edited_script:
                cl = edited_script["CL"]
            elif "Data" in edited_script and "CL" in edited_script["Data"]:
                cl = edited_script["Data"]["CL"]
            if cl:
                logger.info("\n".join(cl))
            else:
                logger.info(str(edited_script))
            # Fetch full script record after edit
            script_record = api.get_script_record(executor, new_script.script_id)
            logger.info(f"✅ Fetched script record after edit: {script_record.get('SN', 'Unknown')}")
        else:
            logger.info(f"✅ Script edited: {edited_script.script_name}")
        
        # Clean up - delete test script
        api.delete_script(executor, new_script.script_id)
        logger.info(f"✅ Test script deleted: {new_script.script_id}")
        
        return new_script
        
    except Exception as e:
        logger.error(f"❌ Script management failed: {e}")
        return None


def main():
    """Main test function"""
    setup_logging()
    
    logger.info("🚀 Starting Phase 2B - Script Management Test")
    logger.info("=" * 60)
    
    try:
        # Test authentication
        executor = test_authentication()
        
        # Test script management
        test_script_management(executor)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Phase 2B tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    main() 