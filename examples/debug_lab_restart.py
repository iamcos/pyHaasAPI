#!/usr/bin/env python3
"""
Debug Lab Restart Script
-----------------------
Selects a running lab, stops it, and attempts to start it again, printing detailed debug output at every step.

All logs (including API requests, responses, and errors) are saved to debug_lab_restart.log for further analysis.
"""
import os
import sys
import time
import logging
import traceback
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from pyHaasAPI import api
from pyHaasAPI.model import StartLabExecutionRequest
from utils.auth.authenticator import authenticator

# Configure logging to both console and file
LOG_FILENAME = "debug_lab_restart.log"
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# File handler with rotation
file_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=2*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

def print_lab_details(lab, prefix="Lab details"):
    logger.info(f"{prefix}:\n" + "\n".join(f"  {k}: {v}" for k, v in lab.__dict__.items()))

def log_request_response(action, request=None, response=None, error=None):
    msg = f"\n--- {action} ---\n"
    if request is not None:
        msg += f"Request: {request}\n"
    if response is not None:
        msg += f"Response: {response}\n"
    if error is not None:
        msg += f"Error: {error}\n"
    logger.info(msg)

def main():
    load_dotenv()
    logger.info("🔐 Authenticating...")
    if not authenticator.authenticate():
        logger.error("Authentication failed")
        return
    executor = authenticator.get_executor()

    logger.info("📋 Fetching all labs...")
    try:
        labs = api.get_all_labs(executor)
        log_request_response("get_all_labs", request=None, response=labs)
    except Exception as e:
        logger.error(f"Error fetching labs: {e}")
        log_request_response("get_all_labs", error=traceback.format_exc())
        return
    if not labs:
        logger.error("No labs found.")
        return
    logger.info(f"Found {len(labs)} labs.")
    for i, lab in enumerate(labs, 1):
        logger.info(f"  [{i}] {lab.name} (ID: {lab.lab_id}) - Status: {lab.status}")

    # Select first running lab
    running_lab = next((lab for lab in labs if int(lab.status) == 2), None)
    if not running_lab:
        logger.error("No running lab found (status == 2).")
        return
    logger.info(f"Selected running lab: {running_lab.name} (ID: {running_lab.lab_id})")
    print_lab_details(running_lab, prefix="Selected running lab details")

    # Get full lab details
    try:
        lab_details = api.get_lab_details(executor, running_lab.lab_id)
        log_request_response("get_lab_details (before stopping)", request=running_lab.lab_id, response=lab_details)
    except Exception as e:
        logger.error(f"Error fetching lab details: {e}")
        log_request_response("get_lab_details (before stopping)", request=running_lab.lab_id, error=traceback.format_exc())
        return
    print_lab_details(lab_details, prefix="Full lab details before stopping")

    # Stop the lab
    logger.info("🛑 Stopping the lab...")
    try:
        api.cancel_lab_execution(executor, running_lab.lab_id)
        log_request_response("cancel_lab_execution", request=running_lab.lab_id, response="Cancel request sent.")
        logger.info("Cancel request sent. Waiting for lab to stop...")
    except Exception as e:
        logger.error(f"Failed to send cancel request: {e}")
        log_request_response("cancel_lab_execution", request=running_lab.lab_id, error=traceback.format_exc())
        traceback.print_exc()
        return

    # Wait for lab to stop
    for attempt in range(30):
        time.sleep(2)
        try:
            details = api.get_lab_details(executor, running_lab.lab_id)
            status = int(details.status)
            logger.info(f"  Attempt {attempt+1}: Lab status is {status}")
            if status != 2:
                logger.info(f"Lab stopped (status now {status})")
                break
        except Exception as e:
            logger.error(f"Error checking lab status: {e}")
            log_request_response("get_lab_details (waiting for stop)", request=running_lab.lab_id, error=traceback.format_exc())
            traceback.print_exc()
    else:
        logger.warning("Lab did not stop within expected time.")

    # Print lab details after stopping
    try:
        stopped_details = api.get_lab_details(executor, running_lab.lab_id)
        print_lab_details(stopped_details, prefix="Lab details after stopping")
        log_request_response("get_lab_details (after stopping)", request=running_lab.lab_id, response=stopped_details)
    except Exception as e:
        logger.error(f"Error fetching lab details after stopping: {e}")
        log_request_response("get_lab_details (after stopping)", request=running_lab.lab_id, error=traceback.format_exc())
        traceback.print_exc()

    # Attempt to start the lab again
    logger.info("🚀 Attempting to start the lab again...")
    start_unix = int(time.time()) - 86400 * 30  # 30 days ago
    end_unix = int(time.time())
    request_obj = StartLabExecutionRequest(
        lab_id=running_lab.lab_id,
        start_unix=start_unix,
        end_unix=end_unix,
        send_email=False
    )
    try:
        result = api.start_lab_execution(executor, request_obj)
        logger.info(f"Lab start result: {result.status if hasattr(result, 'status') else result}")
        print_lab_details(result, prefix="Lab details after start attempt")
        log_request_response("start_lab_execution", request=request_obj, response=result)
    except Exception as e:
        logger.error(f"Failed to start lab execution: {e}")
        log_request_response("start_lab_execution", request=request_obj, error=traceback.format_exc())
        traceback.print_exc()
        # Print all available debug info
        try:
            debug_details = api.get_lab_details(executor, running_lab.lab_id)
            print_lab_details(debug_details, prefix="Lab details after failed start")
            log_request_response("get_lab_details (after failed start)", request=running_lab.lab_id, response=debug_details)
        except Exception as e2:
            logger.error(f"Error fetching lab details after failed start: {e2}")
            log_request_response("get_lab_details (after failed start)", request=running_lab.lab_id, error=traceback.format_exc())
        try:
            exec_update = api.get_lab_execution_update(executor, running_lab.lab_id)
            logger.info(f"Lab execution update: {exec_update}")
            log_request_response("get_lab_execution_update", request=running_lab.lab_id, response=exec_update)
        except Exception as e3:
            logger.error(f"Error fetching lab execution update: {e3}")
            log_request_response("get_lab_execution_update", request=running_lab.lab_id, error=traceback.format_exc())
        logger.info("Check lab configuration, parameters, and server logs for further debugging.")

if __name__ == "__main__":
    main() 