#!/usr/bin/env python3
"""
Complete debug script to trace the full data processing flow
"""
import json
import sys
import os
from pyHaasAPI.model import BacktestRuntimeData
from pyHaasAPI.backtest_object import BacktestObject, BacktestRuntime
from datetime import datetime

# Raw API response data from the terminal output (backtest with actual trading data)
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

def debug_full_flow():
    print("🔍 Complete Data Processing Flow Debug")
    print("=" * 60)

    # Step 1: Parse raw response with Pydantic
    print("\n📡 Step 1: Parse raw API response...")
    try:
        data_content = raw_api_response['Data']
        runtime_data = BacktestRuntimeData(**data_content)
        print("✅ Successfully parsed with BacktestRuntimeData")

        # Check if Reports exist and have data
        if runtime_data.Reports:
            report_key = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe_BINANCEFUTURES_UNI_USDT_PERPETUAL"
            report_data = runtime_data.Reports.get(report_key)

            if report_data:
                print("✅ Found report data with trading information")
                print(f"Report P.C (total trades): {report_data.P.C}")
                print(f"Report P.W (winning trades): {report_data.P.W}")
                print(f"Report PR.RP (total profit): {report_data.PR.RP}")
                print(f"Report PR.ROI: {report_data.PR.ROI}")
            else:
                print("❌ No report data found")
                return
        else:
            print("❌ No Reports found in runtime_data")
            return

    except Exception as e:
        print(f"❌ Failed to parse data: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Create BacktestObject and check its data processing
    print("\n🏗️ Step 2: Create BacktestObject and process data...")
    try:
        # Simulate what BacktestObject._load_core_data does
        report_key = "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe_BINANCEFUTURES_UNI_USDT_PERPETUAL"
        report_data = runtime_data.Reports.get(report_key)

        if report_data:
            # Calculate win rate properly
            total_trades = report_data.P.C
            winning_trades = report_data.P.W
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0

            # Create BacktestRuntime object (this is what _load_core_data does)
            runtime = BacktestRuntime(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=total_trades - winning_trades,
                win_rate=win_rate,
                total_profit=report_data.PR.RP,
                max_drawdown=report_data.PR.RM,
                sharpe_ratio=report_data.T.SHR,
                profit_factor=report_data.T.PF,
                execution_time_ms=0,
                raw_data=report_data.model_dump()
            )

            print("✅ BacktestRuntime object created successfully")
            print(f"  Total trades: {runtime.total_trades}")
            print(f"  Winning trades: {runtime.winning_trades}")
            print(f"  Losing trades: {runtime.losing_trades}")
            print(f"  Win rate: {runtime.win_rate}")
            print(f"  Total profit: {runtime.total_profit}")
            print(f"  Max drawdown: {runtime.max_drawdown}")
            print(f"  Sharpe ratio: {runtime.sharpe_ratio}")
            print(f"  Profit factor: {runtime.profit_factor}")

            # Save runtime data for inspection
            with open('debug_runtime_object.json', 'w') as f:
                json.dump({
                    'total_trades': runtime.total_trades,
                    'winning_trades': runtime.winning_trades,
                    'losing_trades': runtime.losing_trades,
                    'win_rate': runtime.win_rate,
                    'total_profit': runtime.total_profit,
                    'max_drawdown': runtime.max_drawdown,
                    'sharpe_ratio': runtime.sharpe_ratio,
                    'profit_factor': runtime.profit_factor,
                    'raw_data_keys': list(runtime.raw_data.keys()) if runtime.raw_data else []
                }, f, indent=2)
            print("💾 Runtime object data saved to debug_runtime_object.json")

    except Exception as e:
        print(f"❌ Failed to create BacktestRuntime: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Simulate what the financial analytics script does
    print("\n📊 Step 3: Simulate financial analytics processing...")
    try:
        # This simulates the analyze_backtest method in financial_analytics.py
        bt_object = type('MockBacktestObject', (), {})()
        bt_object.runtime = runtime
        bt_object.metadata = type('MockMetadata', (), {
            'script_name': 'ADX BB STOCH Scalper',
            'account_id': '6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe',
            'market_tag': 'BINANCEFUTURES_UNI_USDT_PERPETUAL',
            'start_time': datetime.fromtimestamp(1756245600),
            'end_time': datetime.fromtimestamp(1756331100)
        })()

        print("✅ Mock BacktestObject created with runtime data")

        # Simulate the financial analytics calculations
        losing_trades = runtime.total_trades - runtime.winning_trades
        avg_trade_profit = runtime.total_profit / runtime.total_trades if runtime.total_trades > 0 else 0

        # Calculate time duration
        duration_days = (bt_object.metadata.end_time - bt_object.metadata.start_time).days

        # Calculate fees (estimate if not available)
        total_fees = runtime.raw_data.get('F', {}).get('TFC', 0) if runtime.raw_data else 0
        net_profit_after_fees = runtime.total_profit - total_fees

        # Calculate ROI percentage
        roi_percentage = (runtime.total_profit / 100) * 100 if runtime.total_profit != 0 else 0

        # Calculate max drawdown percentage
        max_drawdown_percentage = (runtime.max_drawdown / runtime.total_profit) * 100 if runtime.total_profit > 0 else 0

        print("✅ Financial calculations completed")
        print(f"  Losing trades: {losing_trades}")
        print(f"  Avg trade profit: {avg_trade_profit}")
        print(f"  Duration days: {duration_days}")
        print(f"  Total fees: {total_fees}")
        print(f"  Net profit after fees: {net_profit_after_fees}")
        print(f"  ROI percentage: {roi_percentage}")
        print(f"  Max drawdown percentage: {max_drawdown_percentage}")

        # Quality indicators
        is_profitable = runtime.total_profit > 0
        has_positive_sharpe = runtime.sharpe_ratio > 0
        has_acceptable_drawdown = max_drawdown_percentage < 20
        has_good_win_rate = runtime.win_rate > 0.4

        print("✅ Quality indicators calculated")
        print(f"  Is profitable: {is_profitable}")
        print(f"  Has positive Sharpe: {has_positive_sharpe}")
        print(f"  Has acceptable drawdown: {has_acceptable_drawdown}")
        print(f"  Has good win rate: {has_good_win_rate}")

        # Overall score calculation
        score = 0
        if is_profitable:
            score += 40
            if roi_percentage > 50:
                score += 10
            elif roi_percentage > 20:
                score += 5

        if has_positive_sharpe:
            score += 15
        if has_acceptable_drawdown:
            score += 15

        if has_good_win_rate:
            score += 20
        elif runtime.win_rate > 0.3:
            score += 10

        if runtime.profit_factor > 2.0:
            score += 10
        elif runtime.profit_factor > 1.5:
            score += 5

        overall_score = min(score, 100)

        print(f"  Overall score: {overall_score}")

        # Save final analysis result
        analysis_result = {
            'backtest_id': '0e3a5382-3de3-4be4-935e-9511bd3d7f66',
            'lab_id': '6e04e13c-1a12-4759-b037-b6997f830edf',
            'script_name': bt_object.metadata.script_name,
            'account_id': bt_object.metadata.account_id,
            'market': bt_object.metadata.market_tag,
            'total_trades': runtime.total_trades,
            'winning_trades': runtime.winning_trades,
            'losing_trades': losing_trades,
            'win_rate': runtime.win_rate,
            'total_profit': runtime.total_profit,
            'roi_percentage': roi_percentage,
            'profit_factor': runtime.profit_factor,
            'max_drawdown': runtime.max_drawdown,
            'max_drawdown_percentage': max_drawdown_percentage,
            'sharpe_ratio': runtime.sharpe_ratio,
            'overall_score': overall_score,
            'is_profitable': is_profitable,
            'has_positive_sharpe': has_positive_sharpe,
            'has_acceptable_drawdown': has_acceptable_drawdown,
            'has_good_win_rate': has_good_win_rate
        }

        with open('debug_analysis_result.json', 'w') as f:
            json.dump(analysis_result, f, indent=2)
        print("💾 Analysis result saved to debug_analysis_result.json")

    except Exception as e:
        print(f"❌ Failed financial analysis simulation: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n🎯 Debug complete! All data processing steps traced successfully.")
    print("📋 Summary:")
    print(f"  - Raw API data: {runtime_data.Reports[report_key].P.C} trades, {runtime_data.Reports[report_key].PR.RP} profit")
    print(f"  - BacktestRuntime: {runtime.total_trades} trades, {runtime.total_profit} profit")
    print(f"  - Analysis result: {analysis_result['total_trades']} trades, {analysis_result['total_profit']} profit, {analysis_result['overall_score']} score")

if __name__ == "__main__":
    debug_full_flow()

