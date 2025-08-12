import os
import json
from dotenv import load_dotenv
load_dotenv()

from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest, LabBacktestResult

def get_top_roi_chart():
    print("🚀 Getting chart for top ROI backtest...")

    # Initialize and authenticate
    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    target_lab_id = "9539af71-48db-4b13-a583-3169e57d107c"
    print(f"🎯 Target Lab ID: {target_lab_id}")

    # Get backtest results for the lab
    try:
        results = api.get_backtest_result(
            executor,
            GetBacktestResultRequest(
                lab_id=target_lab_id,
                next_page_id=0,
                page_lenght=100 # Fetch enough results to find the top ROI
            )
        )
        print(f"✅ Retrieved {len(results.items)} backtest configurations")
    except Exception as e:
        print(f"❌ Failed to get backtest results: {e}")
        return

    if not results.items:
        print("⚠️ No backtest results found for this lab.")
        return

    # Find the backtest with the highest ROI
    top_roi_backtest = None
    max_roi = -float('inf')

    for result in results.items:
        if result.summary and result.summary.ReturnOnInvestment is not None:
            current_roi = result.summary.ReturnOnInvestment
            if current_roi > max_roi:
                max_roi = current_roi
                top_roi_backtest = result
    
    if top_roi_backtest:
        print(f"🏆 Top ROI Backtest Found: ID={top_roi_backtest.backtest_id}, ROI={max_roi:.4f}%")
        
        # Get chart data for the top ROI backtest
        try:
            print(f"📈 Retrieving chart data for backtest {top_roi_backtest.backtest_id}...")
            chart_data = api.get_backtest_chart(executor, target_lab_id, top_roi_backtest.backtest_id)
            
            # Save chart data to chart_sample.json
            output_json_path = "chart_sample.json"
            with open(output_json_path, 'w') as f:
                json.dump(chart_data, f, indent=2, default=str)
            print(f"✅ Chart data saved to {output_json_path}")

            # Now run the visualization script
            print("📊 Running chart visualization script...")
            # Assuming visualize_chart_data.py is in the same directory
            os.system(f'"/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/.venv/bin/python3.11" "/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/visualize_chart_data.py"')
            print("✅ Chart visualization script executed.")

        except Exception as e:
            print(f"❌ Failed to retrieve or save chart data: {e}")
    else:
        print("❌ Could not find a backtest with a valid ROI.")

if __name__ == "__main__":
    get_top_roi_chart()
