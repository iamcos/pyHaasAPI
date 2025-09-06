#!/usr/bin/env python3
# Auto-generated configuration script for labs
# This script would complete the lab configuration once MCP server is enhanced

import requests

MCP_SERVER_URL = "http://127.0.0.1:8000"
TEST_ACCOUNT_ID = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe"

def configure_lab(lab_id: str, coin: str):
    market_tag = f"BINANCEFUTURES_{coin}_USDT_PERPETUAL"
    
    config = {
        "MP": 50,  # Max Population
        "MG": 50,  # Max Generations
        "ME": 3,   # Max Elites
        "MR": 40.0, # Mix Rate
        "AR": 25.0  # Adjust Rate
    }
    
    settings = {
        "accountId": TEST_ACCOUNT_ID,
        "marketTag": market_tag,
        "leverage": 20,
        "positionMode": 1,  # HEDGE mode
        "marginMode": 0,
        "interval": 1,
        "chartStyle": 300,
        "tradeAmount": 100,
        "orderTemplate": 500,
        "scriptParameters": {}
    }
    
    # This would call the UPDATE_LAB_DETAILS endpoint once implemented
    # payload = {"lab_id": lab_id, "config": config, "settings": settings}
    # response = requests.post(f"{MCP_SERVER_URL}/update_lab_details", json=payload)
    
    print(f"Would configure {coin} lab {lab_id} with market {market_tag}")

def main():
    print("🔧 Lab Configuration Script")
    print("⚠️  Requires UPDATE_LAB_DETAILS endpoint in MCP server")
    
    configure_lab("e8ccc535-b008-48de-ad79-09fe08c6d0ea", "BTC")
    configure_lab("6814fd33-9fcc-4965-ad25-8fa55e32c498", "ETH")
    configure_lab("97ab180f-896f-49a0-b306-f5fbc1ea41bc", "SOL")
    configure_lab("55e92025-326a-499e-9b84-f80e6f3d64d0", "BNB")
    configure_lab("43bdaf3f-e4a8-4350-8778-94108f00ba12", "XRP")
    configure_lab("8b3db2c7-31f9-46f0-878c-47e9a2a49e9e", "APT")
    configure_lab("b85d93bd-055e-432e-9690-454f5808c198", "LTC")
    configure_lab("ca29d3ab-3ec6-4a52-ac8a-2ee1ced23bec", "BCH")
    configure_lab("ebd41d3f-b52a-4227-8b7a-8bfc11ec7fa4", "ADA")
    configure_lab("752cea24-6a18-4ec3-85cf-eceb220b2482", "UNI")
    configure_lab("2b74d5f0-b714-44b8-90db-f5a51bed4fbf", "GALA")
    configure_lab("a75eeca4-cb51-4306-a539-14884ad3893f", "TRX")

if __name__ == "__main__":
    main()
