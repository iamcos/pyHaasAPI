#!/usr/bin/env python3
"""
Missing MCP Server Lab Execution Endpoints
Based on curl analysis and PyHaasAPI capabilities
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import time
import logging
from enum import Enum

# These would be added to tools/mcp_server/main.py

class BacktestPeriod(str, Enum):
    ONE_YEAR = "1_year"
    TWO_YEARS = "2_years" 
    THREE_YEARS = "3_years"
    CUSTOM = "custom"

def get_backtest_timestamps(period: BacktestPeriod, end_unix: Optional[int] = None) -> tuple[int, int]:
    """Get start/end timestamps for common backtest periods"""
    if not end_unix:
        end_unix = int(time.time())  # Now
    
    if period == BacktestPeriod.ONE_YEAR:
        start_unix = end_unix - (365 * 24 * 60 * 60)
    elif period == BacktestPeriod.TWO_YEARS:
        start_unix = end_unix - (2 * 365 * 24 * 60 * 60)
    elif period == BacktestPeriod.THREE_YEARS:
        start_unix = end_unix - (3 * 365 * 24 * 60 * 60)
    else:  # CUSTOM
        raise ValueError("Custom period requires explicit start_unix and end_unix")
    
    return start_unix, end_unix

# ============================================================================
# 1. CANCEL LAB EXECUTION (Missing from MCP)
# ============================================================================

class CancelLabExecutionPayload(BaseModel):
    lab_id: str

@app.post("/cancel_lab_execution")
async def cancel_lab_execution_endpoint(payload: CancelLabExecutionPayload):
    """Cancel running lab execution"""
    if not haas_executor:
        raise HTTPException(status_code=503, detail="HaasOnline API not authenticated")
    
    try:
        result = api.cancel_lab_execution(haas_executor, payload.lab_id)
        return {
            "Success": True, 
            "Error": "", 
            "Data": result,
            "message": f"Lab execution cancelled successfully"
        }
    except api.HaasApiError as e:
        logging.error(f"HaasOnline API Error in /cancel_lab_execution: {e}")
        raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
    except Exception as e:
        logging.error(f"Error in /cancel_lab_execution: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# ============================================================================
# 2. ENHANCED START LAB EXECUTION (Better than current /backtest_lab)
# ============================================================================

class StartLabExecutionPayload(BaseModel):
    lab_id: str
    period: BacktestPeriod = BacktestPeriod.TWO_YEARS
    custom_start_unix: Optional[int] = None
    custom_end_unix: Optional[int] = None
    send_email: Optional[bool] = False

@app.post("/start_lab_execution")
async def start_lab_execution_endpoint(payload: StartLabExecutionPayload):
    """Start lab execution with period presets or custom dates"""
    if not haas_executor:
        raise HTTPException(status_code=503, detail="HaasOnline API not authenticated")
    
    try:
        # Calculate timestamps
        if payload.period == BacktestPeriod.CUSTOM:
            if not payload.custom_start_unix or not payload.custom_end_unix:
                raise HTTPException(status_code=400, detail="Custom period requires start_unix and end_unix")
            start_unix = payload.custom_start_unix
            end_unix = payload.custom_end_unix
        else:
            start_unix, end_unix = get_backtest_timestamps(payload.period)
        
        # Create request
        req = api.StartLabExecutionRequest(
            lab_id=payload.lab_id,
            start_unix=start_unix,
            end_unix=end_unix,
            send_email=payload.send_email
        )
        
        # Start execution
        result = api.start_lab_execution(haas_executor, req)
        
        return {
            "Success": True,
            "Error": "",
            "Data": result,
            "message": f"Lab execution started successfully",
            "period": payload.period.value,
            "start_unix": start_unix,
            "end_unix": end_unix
        }
        
    except api.HaasApiError as e:
        logging.error(f"HaasOnline API Error in /start_lab_execution: {e}")
        raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
    except Exception as e:
        logging.error(f"Error in /start_lab_execution: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# ============================================================================
# 3. BULK LAB EXECUTION (Start multiple labs)
# ============================================================================

class BulkStartLabsPayload(BaseModel):
    lab_ids: List[str]
    period: BacktestPeriod = BacktestPeriod.TWO_YEARS
    custom_start_unix: Optional[int] = None
    custom_end_unix: Optional[int] = None
    send_email: Optional[bool] = False

@app.post("/start_multiple_labs")
async def start_multiple_labs_endpoint(payload: BulkStartLabsPayload):
    """Start multiple labs with same time period"""
    if not haas_executor:
        raise HTTPException(status_code=503, detail="HaasOnline API not authenticated")
    
    try:
        # Calculate timestamps
        if payload.period == BacktestPeriod.CUSTOM:
            if not payload.custom_start_unix or not payload.custom_end_unix:
                raise HTTPException(status_code=400, detail="Custom period requires start_unix and end_unix")
            start_unix = payload.custom_start_unix
            end_unix = payload.custom_end_unix
        else:
            start_unix, end_unix = get_backtest_timestamps(payload.period)
        
        results = {}
        failed_labs = {}
        
        print(f"🚀 Starting execution on {len(payload.lab_ids)} labs")
        
        for i, lab_id in enumerate(payload.lab_ids, 1):
            print(f"[{i}/{len(payload.lab_ids)}] Starting lab {lab_id}...")
            
            try:
                req = api.StartLabExecutionRequest(
                    lab_id=lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=payload.send_email
                )
                
                result = api.start_lab_execution(haas_executor, req)
                results[lab_id] = result
                print(f"  ✅ Started successfully")
                
            except Exception as e:
                failed_labs[lab_id] = str(e)
                print(f"  ❌ Failed: {e}")
        
        return {
            "Success": True,
            "Error": "",
            "Data": {
                "started_labs": len(results),
                "failed_labs": len(failed_labs),
                "results": results,
                "failures": failed_labs,
                "period": payload.period.value,
                "start_unix": start_unix,
                "end_unix": end_unix
            },
            "message": f"Started {len(results)} labs, {len(failed_labs)} failed"
        }
        
    except Exception as e:
        logging.error(f"Error in /start_multiple_labs: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# ============================================================================
# 4. ULTIMATE AUTOMATION: CLONE + EXECUTE
# ============================================================================

class CloneTarget(BaseModel):
    asset: str
    exchange: str = "BINANCEFUTURES"
    quote_asset: str = "USDT"
    contract_type: str = "PERPETUAL"
    account_id: Optional[str] = None
    lab_name_override: Optional[str] = None

class CloneAndExecutePayload(BaseModel):
    source_lab_id: str
    targets: List[CloneTarget]
    backtest_period: BacktestPeriod = BacktestPeriod.TWO_YEARS
    custom_start_unix: Optional[int] = None
    custom_end_unix: Optional[int] = None
    send_email: Optional[bool] = False
    auto_start: bool = True
    lab_name_template: str = "{strategy} - {primary} - {suffix}"

@app.post("/clone_and_execute_labs")
async def clone_and_execute_labs_endpoint(payload: CloneAndExecutePayload):
    """
    Ultimate automation: Clone labs to multiple markets AND start execution
    
    Workflow:
    1. Clone source lab to all specified targets
    2. Update each lab with correct market/account settings  
    3. Start backtest execution on all created labs (if auto_start=True)
    4. Return summary of created and started labs
    """
    if not haas_executor:
        raise HTTPException(status_code=503, detail="HaasOnline API not authenticated")
    
    try:
        # Step 1: Clone labs to markets (reuse existing logic)
        clone_payload = {
            "source_lab_id": payload.source_lab_id,
            "targets": [target.dict() for target in payload.targets],
            "lab_name_template": payload.lab_name_template
        }
        
        # This would call the existing clone_lab_to_markets function
        clone_result = await clone_lab_to_markets_endpoint(CloneLabToMarketsPayload(**clone_payload))
        
        if not clone_result["Success"]:
            return clone_result
        
        created_labs = clone_result["Data"]["labs"]
        lab_ids = list(created_labs.keys())
        
        execution_results = {}
        
        # Step 2: Start execution if requested
        if payload.auto_start and lab_ids:
            print(f"🚀 Starting execution on {len(lab_ids)} created labs...")
            
            # Calculate timestamps
            if payload.backtest_period == BacktestPeriod.CUSTOM:
                if not payload.custom_start_unix or not payload.custom_end_unix:
                    raise HTTPException(status_code=400, detail="Custom period requires start_unix and end_unix")
                start_unix = payload.custom_start_unix
                end_unix = payload.custom_end_unix
            else:
                start_unix, end_unix = get_backtest_timestamps(payload.backtest_period)
            
            # Start execution on all created labs
            bulk_start_payload = BulkStartLabsPayload(
                lab_ids=lab_ids,
                period=payload.backtest_period,
                custom_start_unix=payload.custom_start_unix,
                custom_end_unix=payload.custom_end_unix,
                send_email=payload.send_email
            )
            
            execution_result = await start_multiple_labs_endpoint(bulk_start_payload)
            execution_results = execution_result["Data"]
        
        return {
            "Success": True,
            "Error": "",
            "Data": {
                "clone_results": clone_result["Data"],
                "execution_results": execution_results,
                "total_labs_created": len(created_labs),
                "total_labs_started": execution_results.get("started_labs", 0) if payload.auto_start else 0,
                "auto_start": payload.auto_start
            },
            "message": f"Created {len(created_labs)} labs" + 
                      (f", started {execution_results.get('started_labs', 0)}" if payload.auto_start else "")
        }
        
    except Exception as e:
        logging.error(f"Error in /clone_and_execute_labs: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_usage():
    """Example usage of the new endpoints"""
    
    # 1. Cancel a running lab
    requests.post("/cancel_lab_execution", json={
        "lab_id": "55b45ee4-9cc5-42f7-8556-4c3aa2b13a44"
    })
    
    # 2. Start lab with 2-year backtest
    requests.post("/start_lab_execution", json={
        "lab_id": "55b45ee4-9cc5-42f7-8556-4c3aa2b13a44",
        "period": "2_years",
        "send_email": False
    })
    
    # 3. Start multiple labs
    requests.post("/start_multiple_labs", json={
        "lab_ids": ["lab1", "lab2", "lab3"],
        "period": "2_years"
    })
    
    # 4. Ultimate automation - clone AND execute
    requests.post("/clone_and_execute_labs", json={
        "source_lab_id": "7e39fd98-ad7c-4753-8802-c19b2ab11c31",
        "targets": [
            {"asset": "BTC"},
            {"asset": "ETH"}, 
            {"asset": "SOL"}
        ],
        "backtest_period": "2_years",
        "auto_start": True
    })

# ============================================================================
# SUMMARY OF ADDITIONS NEEDED
# ============================================================================

"""
Add to tools/mcp_server/main.py:

1. ✅ /cancel_lab_execution - Cancel running lab
2. ✅ /start_lab_execution - Enhanced start with period presets  
3. ✅ /start_multiple_labs - Bulk start execution
4. ✅ /clone_and_execute_labs - Ultimate one-shot automation

This completes the automation pipeline:
Clone → Configure → Execute → Monitor → Results
"""