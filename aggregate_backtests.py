import os
import json
import glob
import pandas as pd
import multiprocessing
from tqdm import tqdm
import numpy as np

CACHE_DIR = "unified_cache/backtests"
OUTPUT_FILE = "backtest_data.parquet"

def calculate_metrics(finished_positions):
    if not finished_positions:
        return None
    
    total_net_profit = 0.0
    wins = 0
    losses = 0
    gross_profit = 0.0
    gross_loss = 0.0
    
    cumulative_profits = [0.0]
    running_balance = 0.0 # Will offset this later or treat as profit curve
    
    # Try to infer initial capital from the first trade's investment
    # Most bots trade with a fixed amount or specific % of wallet.
    # finished_positions[0]["eno"][0]["a"] (Amount) or similar
    try:
         # "a" is usually amount of asset, "pa" might be position amount/value?
         # "eno" -> entry orders. "a" = amount, "p" = price.
         # Invested Value = Amount * Price
         first_entry = finished_positions[0]["eno"][0]
         initial_invested = float(first_entry["a"]) * float(first_entry["p"])
    except:
         initial_invested = 1000.0 # Fallback default
         
    if initial_invested == 0: initial_invested = 1000.0

    for pos in finished_positions:
        # Net Profit for this position
        # rp = Realized Profit (Net of fees usually, verified in manual check)
        # However, let's be safe: rp is usually the final PnL.
        pnl = float(pos.get("rp", 0.0))
        
        total_net_profit += pnl
        
        if pnl > 0:
            wins += 1
            gross_profit += pnl
        else:
            losses += 1
            gross_loss += abs(pnl)
            
        running_balance += pnl
        cumulative_profits.append(running_balance)

    # Win Rate
    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    
    # Profit Factor
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
    
    # ROI (Return On Investment)
    # ROI = (Total Net Profit / Initial Investment) * 100
    roi_percent = (total_net_profit / initial_invested) * 100
    
    # Max Drawdown
    # Calculate peak-to-valley
    cum_array = np.array(cumulative_profits)
    # We need a base to calc drawdown against. If we assume starting at Initial Invested:
    equity_curve = initial_invested + cum_array
    
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak * 100 # Percentage drawdown
    max_drawdown = np.min(drawdown) # Should be negative or zero
    
    return {
        "roi_custom": roi_percent,
        "net_profit_custom": total_net_profit,
        "max_drawdown_custom": max_drawdown,
        "win_rate_custom": win_rate,
        "profit_factor_custom": profit_factor,
        "total_trades_custom": total_trades,
        "initial_capital_inferred": initial_invested
    }

def parse_report(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not data.get("Success"):
            return None

        content = data.get("Data", {})
        if not content:
            return None

        # The structure is often Data -> Reports -> {ReportKey} -> AID, M, FinishedPositions
        reports = content.get("Reports", {})
        extracted_results = []
        
        # Step 1: Try nested reports first
        for r_key, r_data in reports.items():
            lab_id = r_data.get("AID", r_data.get("LabID", "Unknown"))
            market = r_data.get("M", r_data.get("PriceMarket", "Unknown"))
            finished_positions = r_data.get("FinishedPositions", [])
            
            if not finished_positions:
                continue
                
            parameters = r_data.get("P", {}) # Parameters
            
            # 4. Calculate Custom Metrics
            custom_metrics = calculate_metrics(finished_positions)
            
            if not custom_metrics:
                continue # Skip reports with no trades
                
            # Merge basic info with metrics
            result = {
                "file": os.path.basename(file_path),
                "lab_id": lab_id,
                "market": market,
                "parameters": json.dumps(parameters) # Store as JSON string for parity
            }
            result.update(custom_metrics)
            extracted_results.append(result)

        # Step 2: Fallback to root level if no trades found in nested reports
        if not extracted_results:
            root_fp = content.get("FinishedPositions", [])
            if root_fp:
                lab_id = content.get("AID", content.get("LabID", "Unknown"))
                market = content.get("PriceMarket", content.get("M", "Unknown"))
                
                # Check for Market DNA or similar keys if M is unknown
                if market == "Unknown":
                    market = content.get("PriceMarket", "Unknown")

                # Filename Fallback
                fname = os.path.basename(file_path).replace(".json", "")
                parts = fname.split("_", 1)
                if len(parts) == 2:
                    if lab_id == "Unknown": lab_id = parts[0]
                    if market == "Unknown": market = parts[1]

                custom_metrics = calculate_metrics(root_fp)
                if custom_metrics:
                    result = {
                        "file": os.path.basename(file_path),
                        "lab_id": lab_id,
                        "market": market,
                    }
                    result.update(custom_metrics)
                    extracted_results.append(result)
            
        return extracted_results if extracted_results else None
        
    except Exception as e:
        return None

def main():
    print(f"🔍 Scanning {CACHE_DIR}...")
    files = glob.glob(os.path.join(CACHE_DIR, "*.json"))
    
    if not files:
        print("❌ No JSON files found!")
        return

    print(f"found {len(files)} files. Starting aggregation...")
    
    # Use multiprocessing
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    
    all_results = []
    with tqdm(total=len(files)) as pbar:
        for results_list in pool.imap_unordered(parse_report, files):
            if results_list:
                all_results.extend(results_list)
            pbar.update()
            
    pool.close()
    pool.join()
    
    print(f"📊 Processed {len(all_results)} valid accounts with trades.")
    
    if all_results:
        print("💾 Saving to Parquet...")
        df = pd.DataFrame(all_results)
        df.to_parquet(OUTPUT_FILE, index=False)
        print(f"✅ Saved {OUTPUT_FILE} ({len(df)} rows)")
    else:
        print("⚠️ No valid data extracted.")

if __name__ == "__main__":
    main()
