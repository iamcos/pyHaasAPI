"""
FastAPI webhook server to handle Miro board interactions
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import asyncio
from typing import Dict, Any
import os
from dotenv import load_dotenv

from miro_haas_bridge import MiroHaasBridge
from pyHaasAPI import SyncExecutor

load_dotenv()

app = FastAPI(title="Miro-Haas Integration Server")

# Global bridge instance
bridge: MiroHaasBridge = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Miro-Haas bridge on startup"""
    global bridge
    
    miro_token = os.getenv("MIRO_ACCESS_TOKEN")
    if not miro_token:
        raise ValueError("MIRO_ACCESS_TOKEN environment variable required")
    
    # Initialize your Haas executor here
    haas_executor = SyncExecutor()  # Configure with your credentials
    
    bridge = MiroHaasBridge(miro_token, haas_executor)
    logging.info("Miro-Haas bridge initialized")

@app.post("/webhook/miro")
async def handle_miro_webhook(request: Request):
    """Handle incoming webhooks from Miro"""
    try:
        webhook_data = await request.json()
        
        # Verify webhook signature if needed
        # signature = request.headers.get("X-Miro-Signature")
        # if not verify_signature(signature, webhook_data):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process the webhook
        await bridge.handle_miro_interaction(webhook_data)
        
        return JSONResponse({"status": "success"})
        
    except Exception as e:
        logging.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dashboard/create")
async def create_dashboard(team_id: str):
    """Create a new trading dashboard board"""
    try:
        board_id = await bridge.create_trading_dashboard_board(team_id)
        return {"board_id": board_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dashboard/{board_id}/update")
async def update_dashboard(board_id: str):
    """Manually trigger dashboard update"""
    try:
        await bridge.update_dashboard_data(board_id)
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "miro-haas-integration"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)