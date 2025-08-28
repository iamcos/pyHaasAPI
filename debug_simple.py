#!/usr/bin/env python3
"""
Simple debug script to trace data processing using the raw API response
"""
import json
from pyHaasAPI.model import BacktestRuntimeData, Report
from pyHaasAPI.backtest_object import BacktestObject, BacktestRuntime
from datetime import datetime

# Raw API response data from the terminal output (truncated for readability)
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
                    "FPC": {
                        "USDT": 18.8369775
                    }
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

def debug_data_processing():
    print("🔍 Debug: Data Processing Analysis")
    print("=" * 60)

    # Step 1: Parse the raw data with BacktestRuntimeData
    print("\n📡 Step 1: Parsing raw API response...")
    try:
        data_content = raw_api_response['Data']
        runtime_data = BacktestRuntimeData(**data_content)
        print("✅ Successfully parsed with BacktestRuntimeData")

        # Check Reports
        print(f"Reports keys: {list(runtime_data.Reports.keys())}")

        # Get the specific report
        report_key = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe_BINANCEFUTURES_UNI_USDT_PERPETUAL"
        report_data = runtime_data.Reports.get(report_key)

        if report_data:
            print("✅ Found report data")
            print(f"Report type: {type(report_data)}")

            # Check the structure
            print(f"Report dict: {report_data.model_dump()}")

            # Extract trading data - this is where the issue might be
            print("\n📊 Step 2: Extracting trading data...")

            # Access the nested data structures
            if hasattr(report_data, 'P'):
                print(f"Position data (P): {report_data.P}")
                if hasattr(report_data.P, 'C'):
                    total_trades = report_data.P.C
                    print(f"Total trades from P.C: {total_trades}")
                if hasattr(report_data.P, 'W'):
                    winning_trades = report_data.P.W
                    print(f"Winning trades from P.W: {winning_trades}")

            if hasattr(report_data, 'PR'):
                print(f"Profit data (PR): {report_data.PR}")
                if hasattr(report_data.PR, 'RP'):
                    total_profit = report_data.PR.RP
                    print(f"Total profit from PR.RP: {total_profit}")

            if hasattr(report_data, 'T'):
                print(f"Trade data (T): {report_data.T}")
                if hasattr(report_data.T, 'TR'):
                    total_return = report_data.T.TR
                    print(f"Total return from T.TR: {total_return}")

        else:
            print("❌ No report data found")

    except Exception as e:
        print(f"❌ Failed to parse data: {e}")
        import traceback
        traceback.print_exc()

    # Step 3: Test the BacktestObject data processing
    print("\n🏗️ Step 3: Testing BacktestObject processing...")
    try:
        # Create a minimal BacktestObject to test the _load_core_data method
        # We'll simulate what happens in the method

        # Get the report data
        report_key = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe_BINANCEFUTURES_UNI_USDT_PERPETUAL"
        report_data = runtime_data.Reports.get(report_key)

        if report_data:
            # Use the corrected method from the fixed BacktestObject
            total_trades = report_data.P.C
            winning_trades = report_data.P.W
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0

            runtime = BacktestRuntime(
                total_trades=total_trades,  # This should be 1
                winning_trades=winning_trades,  # This should be 1
                losing_trades=total_trades - winning_trades,  # This should be 0
                win_rate=win_rate,  # Use calculated win rate instead of API value
                total_profit=report_data.PR.RP,  # This should be 469.8960225
                max_drawdown=report_data.PR.RM,
                sharpe_ratio=report_data.T.SHR,
                profit_factor=report_data.T.PF,
                execution_time_ms=0,
                raw_data=report_data.model_dump()
            )

            print("✅ Created BacktestRuntime object")
            print(f"Total trades: {runtime.total_trades}")
            print(f"Winning trades: {runtime.winning_trades}")
            print(f"Total profit: {runtime.total_profit}")
            print(f"Win rate: {runtime.win_rate}")
            print(f"Win rate (as %): {runtime.win_rate * 100:.1f}%")

            # Verify calculation
            expected_win_rate = runtime.winning_trades / runtime.total_trades if runtime.total_trades > 0 else 0
            print(f"Expected win rate: {expected_win_rate}")
            print(f"Win rate matches: {abs(runtime.win_rate - expected_win_rate) < 0.001}")

        else:
            print("❌ No report data for BacktestObject test")

    except Exception as e:
        print(f"❌ Failed BacktestObject processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_processing()
