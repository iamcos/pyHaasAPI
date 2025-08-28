#!/usr/bin/env python3
"""
Debug script to trace the data parsing issue
"""
import json
import sys
import os
from pyHaasAPI.model import BacktestRuntimeData, Report
from pyHaasAPI.backtest_object import BacktestObject, BacktestRuntime

# Raw API response data from the debug output
raw_api_response = {
    "Success": True,
    "Error": "",
    "Data": {
        "Chart": {
            "Guid": "16fc5be5-e400-464a-b0f5-5f8ffe856202",
            "Interval": 1,
            "Charts": {},
            "Colors": {
                "Font": "Tahoma",
                "Axis": "#000000",
                "Grid": "#303030",
                "Text": "#BBBBBB",
                "Background": "rgb(37, 37, 37)",
                "PriceGhostLine": "#FFFF00",
                "VolumeGhostLine": "#FFFF00"
            },
            "IsLastPartition": True,
            "Status": 1
        },
        "CompilerErrors": [],
        "Reports": {
            "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe_BINANCEFUTURES_UNI_USDT_PERPETUAL": {
                "AID": "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe",
                "M": "BINANCEFUTURES_UNI_USDT_PERPETUAL",
                "AL": "UNI",
                "ML": "USDT",
                "PL": "USDT",
                "F": {
                    "FC": 18.8369775,
                    "FR": 0.0,
                    "TFC": 18.8369775,
                    "FPC": {"USDT": 18.8369775}
                },
                "PR": {
                    "SP": 9.963,
                    "SB": 9836.828567235,
                    "PC": -0.2509,
                    "BC": 0.0,
                    "GP": 488.7330,
                    "RP": 469.8960225,
                    "UP": 0.0,
                    "ROI": 50.5465,
                    "RM": 929.63055,
                    "CRM": 0.0,
                    "RPH": [469.8960225],
                    "ROIH": [50.5465]
                },
                "O": {
                    "F": 2,
                    "P": 0,
                    "C": 0,
                    "R": 0,
                    "A": 0,
                    "L": 1756309680,
                    "PT": 1,
                    "LT": 0,
                    "BW": 488.7330,
                    "BL": 0.0
                },
                "P": {
                    "C": 1,
                    "W": 1,
                    "AP": 469.8960225,
                    "APS": 1887.0,
                    "APM": 929.63055,
                    "TEM": 1883.69775,
                    "AW": 469.8960225,
                    "BW": 469.8960225,
                    "TW": 469.8960225,
                    "AL": 0.0,
                    "BL": 0.0,
                    "TL": 0.0,
                    "PH": [469.8960225]
                },
                "T": {
                    "SHR": 0.0,
                    "SOR": 0.0,
                    "WP": 0.0,
                    "WLP": 0.0,
                    "PF": 0.0,
                    "CPC": 0.0,
                    "TR": 1.0,
                    "CSR": 0.0,
                    "OWR": 1.0,
                    "OLR": 1.0,
                    "PMR": 0.01,
                    "BW": 469.8960225,
                    "BL": 0.0,
                    "HP": 469.8960225,
                    "LP": -9.2963055,
                    "TM": 929.63055,
                    "AVM": 0.0,
                    "AVP": 0.0
                }
            }
        },
        "CustomReport": {},
        "ScriptNote": "",
        "TrackedOrderLimit": 150,
        "OpenOrders": [],
        "FailedOrders": [],
        "ManagedLongPosition": {
            "pg": "88645e5c-8e3c-4e6d-b801-ec9419b920a8",
            "g": "8a084f5a-c758-45a7-b3dd-76dc3bbf87d0",
            "ac": "",
            "ma": "",
            "le": 0.0,
            "d": 0,
            "mt": 0,
            "pl": None,
            "al": None,
            "pd": 0,
            "ad": 0,
            "ot": 0,
            "ct": 0,
            "ic": False,
            "ap": 0.0,
            "t": 0.0,
            "av": 0.0,
            "io": 0.0,
            "eno": [],
            "exo": [],
            "cp": 0.0,
            "fe": 0.0,
            "rp": 0.0,
            "up": 0.0,
            "roi": 0.0,
            "hpip": 0.0,
            "lpip": 0.0
        },
        "ManagedShortPosition": {
            "pg": "d770b054-7974-4eb7-8a7b-5f7105d0d613",
            "g": "bc989532-dd0f-46e8-b15a-344af4134b27",
            "ac": "",
            "ma": "",
            "le": 0.0,
            "d": 0,
            "mt": 0,
            "pl": None,
            "al": None,
            "pd": 0,
            "ad": 0,
            "ot": 0,
            "ct": 0,
            "ic": False,
            "ap": 0.0,
            "t": 0.0,
            "av": 0.0,
            "io": 0.0,
            "eno": [],
            "exo": [],
            "cp": 0.0,
            "fe": 0.0,
            "rp": 0.0,
            "up": 0.0,
            "roi": 0.0,
            "hpip": 0.0,
            "lpip": 0.0
        },
        "UnmanagedPositions": [],
        "FinishedPositions": [
            {
                "pg": "2ac1d86a-0620-4a55-8f65-6f34454489b4",
                "g": "9d9d8e64-6e33-4c18-a3b0-61b8f0d85035",
                "ac": "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe",
                "ma": "BINANCEFUTURES_UNI_USDT_PERPETUAL",
                "le": 20.0,
                "d": 0,
                "mt": 1502,
                "pl": "USDT",
                "al": "UNI",
                "pd": 3,
                "ad": 0,
                "ot": 1756255800,
                "ct": 1756309680,
                "ic": True,
                "ap": 9.853,
                "t": 0.0,
                "av": 0.0,
                "io": 0.0,
                "eno": [
                    {
                        "paid": "",
                        "pa": 0,
                        "id": "f614099cf6b243fd966c5f1614aaa53f",
                        "eid": "f614099cf6b243fd966c5f1614aaa53f",
                        "ot": 1756255800,
                        "ct": 1756255800,
                        "to": 300,
                        "d": 2,
                        "t": 501,
                        "p": 9.853,
                        "tp": 0.0,
                        "ep": 9.853,
                        "a": 1887.0,
                        "af": 1887.0,
                        "fe": 9.2963055,
                        "fc": "USDT",
                        "m": 929.63055,
                        "pr": 0.0,
                        "r": 0.0,
                        "cr": 0,
                        "n": "LE"
                    }
                ],
                "exo": [
                    {
                        "paid": "",
                        "pa": 0,
                        "id": "be6e5a1991d94a488e86acbfe1637fbe",
                        "eid": "be6e5a1991d94a488e86acbfe1637fbe",
                        "ot": 1756309680,
                        "ct": 1756309680,
                        "to": 0,
                        "d": 3,
                        "t": 501,
                        "p": 10.114,
                        "tp": 0.0,
                        "ep": 10.112,
                        "a": 1887.0,
                        "af": 1887.0,
                        "fe": 9.5406720,
                        "fc": "USDT",
                        "m": 954.0672,
                        "pr": 488.7330,
                        "r": 52.5728,
                        "cr": 0,
                        "n": "TP"
                    }
                ],
                "cp": 0.0,
                "fe": 18.8369775,
                "rp": 469.8960225,
                "up": 0.0,
                "roi": 50.5465,
                "hpip": 0.0,
                "lpip": 0.0
            }
        ],
        "InputFields": {
            "3-3-17-22.Trade amount by margin": {
                "T": 2,
                "ST": -1,
                "G": "TRADE SETTINGS",
                "K": "3-3-17-22.Trade amount by margin",
                "EK": "3-3-17-22",
                "N": "Trade amount by margin",
                "TT": "",
                "V": "True",
                "D": "True",
                "O": None,
                "MIN": 0.0,
                "MAX": 0.0
            }
        },
        "ScriptMemory": {},
        "LocalMemory": {},
        "RedisKeys": [],
        "Files": {},
        "LogId": "0663356f",
        "LogCount": 0,
        "ExecutionLog": [],
        "UserId": "r_816_trade@stm.ooo",
        "BotId": "0e3a5382-3de3-4be4-935e-9511bd3d7f66",
        "BotName": "",
        "ScriptId": "7dda6a1e59594d4588b62619a848a6ae",
        "ScriptName": "ADX BB STOCH Scalper",
        "Activated": True,
        "Paused": False,
        "IsWhiteLabel": False,
        "ActivatedSince": 1756245600,
        "DeactivatedSince": 0,
        "DeactivatedReason": "",
        "AccountId": "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe",
        "PriceMarket": "BINANCEFUTURES_UNI_USDT_PERPETUAL",
        "Leverage": 20.0,
        "MarginMode": 0,
        "PositionMode": 1,
        "TradeAmount": 100.0,
        "OrderTemplate": 500,
        "DefaultInterval": 20,
        "DefaultChartType": 300,
        "HideTradeAmountSettings": False,
        "HideOrderSettings": False,
        "OrderPersistenceEnabled": False,
        "OrderPersistenceLimit": 10,
        "EnableHighSpeedUpdates": False,
        "UpdateAfterCompletedOrder": False,
        "IndicatorContainerLogs": True,
        "IsScriptOk": True,
        "TradeAmountError": False,
        "ScriptTradeAmountError": False,
        "UpdateCounter": 0,
        "IsSpotSupported": False,
        "IsMarginSupported": True,
        "IsLeverageSupported": True,
        "IsManagedTrading": False,
        "IsOneDirection": False,
        "IsMultiMarket": False,
        "IsRemoteSignalBased": False,
        "IsWebHookBased": False,
        "WebHookSignalId": "",
        "IsTAUsed": False,
        "Timestamp": 1756331100,
        "MinuteTimestamp": 1756331100,
        "LastUpdateTimestamp": 1756331100
    }
}

def debug_parsing():
    print("🔍 Debugging data parsing issue")
    print("=" * 60)

    # Step 1: Extract data content (like get_full_backtest_runtime_data does)
    print("\n📡 Step 1: Extracting data content...")
    data_content = raw_api_response.get("Data", {})
    print(f"✅ Data content extracted, keys: {list(data_content.keys())}")

    # Step 2: Try to parse with BacktestRuntimeData
    print("\n🏗️ Step 2: Parsing with BacktestRuntimeData...")
    try:
        full_runtime_data = BacktestRuntimeData.model_validate(data_content)
        print("✅ Successfully parsed with BacktestRuntimeData")
        print(f"   Reports keys: {list(full_runtime_data.Reports.keys())}")

        # Step 3: Check the report data
        print("\n🎯 Step 3: Checking report data...")
        for report_key, report_data in full_runtime_data.Reports.items():
            print(f"   Report key: {report_key}")
            print(f"   Report type: {type(report_data)}")
            print(f"   Report P.C (total trades): {getattr(report_data, 'p', {}).get('c', 'MISSING')}")
            print(f"   Report P.W (winning trades): {getattr(report_data, 'p', {}).get('w', 'MISSING')}")
            print(f"   Report PR.RP (total profit): {getattr(report_data, 'pr', {}).get('rp', 'MISSING')}")

            # Try to create the runtime object
            if report_data:
                print("\n🏗️ Step 4: Creating BacktestRuntime object...")
                try:
                    runtime = BacktestRuntime(
                        total_trades=report_data.p.c,  # This should be 1
                        winning_trades=report_data.p.w,  # This should be 1
                        losing_trades=report_data.p.c - report_data.p.w,  # This should be 0
                        win_rate=(report_data.p.w / report_data.p.c) if report_data.p.c > 0 else 0.0,
                        total_profit=report_data.pr.rp,  # This should be 469.8960225
                        max_drawdown=report_data.pr.rm if hasattr(report_data.pr, 'rm') else 0,
                        sharpe_ratio=report_data.t.shr if hasattr(report_data.t, 'shr') else 0,
                        profit_factor=report_data.t.pf if hasattr(report_data.t, 'pf') else 0,
                        execution_time_ms=0,
                        raw_data=report_data.model_dump()
                    )
                    print("✅ BacktestRuntime created successfully")
                    print(f"   Total trades: {runtime.total_trades}")
                    print(f"   Winning trades: {runtime.winning_trades}")
                    print(f"   Total profit: {runtime.total_profit}")

                except Exception as e:
                    print(f"❌ Error creating BacktestRuntime: {e}")
                    print(f"Error type: {type(e)}")
                    import traceback
                    traceback.print_exc()

    except Exception as e:
        print(f"❌ Error parsing data: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parsing()

