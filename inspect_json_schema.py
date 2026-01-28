import json
import os
import glob
from tqdm import tqdm

CACHE_DIR = "unified_cache/backtests"

def inspect():
    files = glob.glob(os.path.join(CACHE_DIR, "*.json"))
    print(f"Checking {len(files)} files...")
    
    for f_path in tqdm(files):
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
            
            content = data.get("Data", data)
            positions = content.get("FinishedPositions", [])
            
            if positions:
                print(f"\nFound trades in: {f_path}")
                first_pos = positions[0]
                print("Position Keys:", list(first_pos.keys()))
                
                # Check for timestamps
                if "ot" in first_pos:
                    print(f"Open Time (ot): {first_pos['ot']}")
                if "ct" in first_pos:
                    print(f"Close Time (ct): {first_pos['ct']}")
                
                if "exo" in first_pos and first_pos["exo"]:
                    print("Exit Order Sample:", first_pos["exo"][0])
                
                # Look for common Haas timestamp fields
                possible_time_keys = ['t', 'T', 'sd', 'ed', 'st', 'et', 'time', 'Time', 'Timestamp', 'ot', 'ct']
                for pk in possible_time_keys:
                    if pk in first_pos:
                        print(f"Found direct time key: {pk} = {first_pos[pk]}")
                
                return # Stop after first success
        except:
            continue

if __name__ == "__main__":
    inspect()
