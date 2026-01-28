import json
import os
import sys

# Import functions from aggregate_backtests
sys.path.append(os.getcwd())
from aggregate_backtests import parse_report, calculate_metrics

def debug_one(file_path):
    print(f"Debugging: {file_path}")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"Success: {data.get('Success')}")
        content = data.get("Data", {})
        print(f"Data keys: {list(content.keys()) if content else 'Null'}")
        
        reports = content.get("Reports", {})
        print(f"Number of reports found: {len(reports)}")
        
        root_fp = content.get("FinishedPositions", [])
        print(f"Root FinishedPositions count: {len(root_fp)}")

        for k, v in reports.items():
            print(f"  Report Key: {k}")
            fp = v.get("FinishedPositions", [])
            print(f"  FinishedPositions count: {len(fp)}")
            metrics = calculate_metrics(fp)
            print(f"  Metrics: {metrics is not None}")

        res = parse_report(file_path)
        print(f"\nFinal Result: {res}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Find a file that has Success: true
    import glob
    files = glob.glob("unified_cache/backtests/*.json")
    for f in files:
        with open(f, 'r') as jf:
            d = json.load(jf)
            if d.get("Success"):
                debug_one(f)
                break
