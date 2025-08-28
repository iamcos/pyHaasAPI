"""
Lab Management Endpoints
Handles lab creation, cloning, execution, and automation.
"""

import logging
import time
from enum import Enum
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel

# Import from parent package
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, CloudMarket


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
# PYDANTIC MODELS
# ============================================================================

class CreateLabPayload(BaseModel):
    script_id: str
    account_id: str
    market_category: str = "SPOT"
    market_price_source: str = "BINANCE"
    market_primary: str = "BTC"
    market_secondary: str = "USDT"
    exchange_code: str = "BINANCE"
    interval: int = 1
    default_price_data_style: str = "CandleStick"


class CloneLabPayload(BaseModel):
    lab_id: str
    new_name: Optional[str] = None


class BacktestLabPayload(BaseModel):
    lab_id: str
    start_unix: int
    end_unix: int
    send_email: Optional[bool] = False


class GetBacktestResultsPayload(BaseModel):
    lab_id: str
    next_page_id: Optional[int] = -1
    page_length: Optional[int] = 100


class CancelLabExecutionPayload(BaseModel):
    lab_id: str


class StartLabExecutionPayload(BaseModel):
    lab_id: str
    period: BacktestPeriod = BacktestPeriod.TWO_YEARS
    custom_start_unix: Optional[int] = None
    custom_end_unix: Optional[int] = None
    send_email: Optional[bool] = False


class BulkStartLabsPayload(BaseModel):
    lab_ids: List[str]
    period: BacktestPeriod = BacktestPeriod.TWO_YEARS
    custom_start_unix: Optional[int] = None
    custom_end_unix: Optional[int] = None
    send_email: Optional[bool] = False


class CloneTarget(BaseModel):
    asset: str
    exchange: str = "BINANCEFUTURES"
    quote_asset: str = "USDT"
    contract_type: str = "PERPETUAL"
    account_id: Optional[str] = None
    lab_name_override: Optional[str] = None


class CloneLabToMarketsPayload(BaseModel):
    source_lab_id: str
    targets: List[CloneTarget]
    lab_name_template: str = "{strategy} - {primary} - {suffix}"


class CloneAndExecutePayload(BaseModel):
    source_lab_id: str
    targets: List[CloneTarget]
    backtest_period: BacktestPeriod = BacktestPeriod.TWO_YEARS
    custom_start_unix: Optional[int] = None
    custom_end_unix: Optional[int] = None
    send_email: Optional[bool] = False
    auto_start: bool = True
    lab_name_template: str = "{strategy} - {primary} - {suffix}"


# ============================================================================
# ENDPOINT FUNCTIONS (to be registered with FastAPI app)
# ============================================================================

def register_lab_endpoints(app, haas_executor):
    """Register all lab management endpoints with the FastAPI app"""
    
    @app.post("/create_lab")
    async def create_haas_lab(payload: CreateLabPayload):
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated or connected.")

        try:
            market = CloudMarket(
                C=payload.market_category,
                PS=payload.market_price_source,
                P=payload.market_primary,
                S=payload.market_secondary
            )
            req = CreateLabRequest.with_generated_name(
                script_id=payload.script_id,
                account_id=payload.account_id,
                market=market,
                exchange_code=payload.exchange_code,
                interval=payload.interval,
                default_price_data_style=payload.default_price_data_style
            )
            lab = api.create_lab(haas_executor, req)
            return {"message": "Lab created successfully", "lab_id": lab.lab_id, "lab_name": lab.name}
        except api.HaasApiError as e:
            logging.error(f"HaasOnline API Error in /create_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in /create_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    @app.post("/clone_lab")
    async def clone_lab_endpoint(payload: CloneLabPayload):
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated or connected.")
        try:
            cloned_lab = api.clone_lab(haas_executor, payload.lab_id, payload.new_name)
            return {"message": "Lab cloned successfully", "lab_id": cloned_lab.lab_id, "lab_name": cloned_lab.name, "Success": True, "Error": "", "Data": cloned_lab}
        except api.HaasApiError as e:
            logging.error(f"HaasOnline API Error in /clone_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in /clone_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    @app.post("/backtest_lab")
    async def backtest_lab_endpoint(payload: BacktestLabPayload):
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated or connected.")
        try:
            req = api.StartLabExecutionRequest(
                lab_id=payload.lab_id,
                start_unix=payload.start_unix,
                end_unix=payload.end_unix,
                send_email=payload.send_email
            )
            result = api.start_lab_execution(haas_executor, req)
            return {"message": "Backtest started successfully", "result": result, "Success": True, "Error": "", "Data": result}
        except api.HaasApiError as e:
            logging.error(f"HaasOnline API Error in /backtest_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in /backtest_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    @app.post("/get_backtest_results")
    async def get_backtest_results_endpoint(payload: GetBacktestResultsPayload):
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated or connected.")
        try:
            req = api.GetBacktestResultRequest(
                lab_id=payload.lab_id,
                next_page_id=payload.next_page_id,
                page_lenght=payload.page_length
            )
            results = api.get_backtest_result(haas_executor, req)
            return {"Success": True, "Error": "", "Data": results}
        except api.HaasApiError as e:
            logging.error(f"HaasOnline API Error in /get_backtest_results: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in /get_backtest_results: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    @app.delete("/delete_lab/{lab_id}")
    async def delete_lab_endpoint(lab_id: str):
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated or connected.")
        try:
            success = api.delete_lab(haas_executor, lab_id)
            if success:
                return {"message": f"Lab {lab_id} deleted successfully", "Success": True, "Error": "", "Data": None}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to delete lab {lab_id}")
        except api.HaasApiError as e:
            logging.error(f"HaasOnline API Error in /delete_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in /delete_lab: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    @app.get("/get_all_labs")
    async def get_all_labs_endpoint():
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated or connected.")
        try:
            labs = api.get_all_labs(haas_executor)
            return {"Success": True, "Error": "", "Data": labs}
        except api.HaasApiError as e:
            logging.error(f"HaasOnline API Error in /get_all_labs: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in /get_all_labs: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    @app.delete("/labs/delete_all_except/{lab_name_to_keep}")
    async def delete_all_labs_except_endpoint(lab_name_to_keep: str):
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated or connected.")
        
        deleted_labs_count = 0
        errors = []
        
        try:
            while True:
                all_labs = api.get_all_labs(haas_executor)
                labs_to_delete = [lab for lab in all_labs if lab.name != lab_name_to_keep]

                if not labs_to_delete:
                    break

                for lab in labs_to_delete:
                    try:
                        api.delete_lab(haas_executor, lab.lab_id)
                        deleted_labs_count += 1
                    except Exception as e:
                        error_message = f"Could not delete lab {lab.name} ({lab.lab_id}): {e}"
                        logging.error(error_message)
                        errors.append(error_message)
            
            if errors:
                return {"message": f"Completed with errors. Deleted {deleted_labs_count} labs.", "errors": errors, "Success": False}
            
            return {"message": f"Successfully deleted {deleted_labs_count} labs.", "Success": True}

        except api.HaasApiError as e:
            logging.error(f"HaasOnline API Error in /labs/delete_all_except: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"HaasOnline API Error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred in /labs/delete_all_except: {e}", exc_info=True)

    # ============================================================================
    # ADVANCED LAB EXECUTION ENDPOINTS
    # ============================================================================

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

    @app.post("/clone_lab_to_markets")
    async def clone_lab_to_markets_endpoint(payload: CloneLabToMarketsPayload):
        """Clone a lab to multiple markets with automatic market resolution"""
        if not haas_executor:
            raise HTTPException(status_code=503, detail="HaasOnline API not authenticated")
        
        try:
            # Get source lab details
            source_lab = api.get_lab_details(haas_executor, payload.source_lab_id)
            if not source_lab:
                raise HTTPException(status_code=404, detail=f"Source lab {payload.source_lab_id} not found")
            
            created_labs = {}
            failed_targets = {}
            
            print(f"🔄 Cloning lab to {len(payload.targets)} markets...")
            
            for i, target in enumerate(payload.targets, 1):
                print(f"[{i}/{len(payload.targets)}] Cloning to {target.asset}...")
                
                try:
                    # Generate lab name
                    strategy_name = source_lab.name.split(" - ")[0] if " - " in source_lab.name else source_lab.name
                    lab_name = payload.lab_name_template.format(
                        strategy=strategy_name,
                        primary=target.asset,
                        suffix=f"{target.exchange[:3]}"
                    )
                    
                    # Clone the lab
                    cloned_lab = api.clone_lab(haas_executor, payload.source_lab_id, lab_name)
                    
                    # Update market settings (this would need to be implemented based on your market resolver)
                    # For now, we'll just return the cloned lab info
                    created_labs[cloned_lab.lab_id] = {
                        "lab_id": cloned_lab.lab_id,
                        "lab_name": cloned_lab.name,
                        "target": target.dict()
                    }
                    print(f"  ✅ Created: {cloned_lab.name}")
                    
                except Exception as e:
                    failed_targets[f"{target.asset}_{target.exchange}"] = str(e)
                    print(f"  ❌ Failed: {e}")
            
            return {
                "Success": True,
                "Error": "",
                "Data": {
                    "labs": created_labs,
                    "failures": failed_targets,
                    "created_count": len(created_labs),
                    "failed_count": len(failed_targets)
                },
                "message": f"Created {len(created_labs)} labs, {len(failed_targets)} failed"
            }
            
        except Exception as e:
            logging.error(f"Error in /clone_lab_to_markets: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

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
            # Step 1: Clone labs to markets
            clone_payload = CloneLabToMarketsPayload(
                source_lab_id=payload.source_lab_id,
                targets=payload.targets,
                lab_name_template=payload.lab_name_template
            )
            
            clone_result = await clone_lab_to_markets_endpoint(clone_payload)
            
            if not clone_result["Success"]:
                return clone_result
            
            created_labs = clone_result["Data"]["labs"]
            lab_ids = list(created_labs.keys())
            
            execution_results = {}
            
            # Step 2: Start execution if requested
            if payload.auto_start and lab_ids:
                print(f"🚀 Starting execution on {len(lab_ids)} created labs...")
                
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