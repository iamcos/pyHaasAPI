import os
from pathlib import Path

def sync_cache():
    source_root = Path("unified_cache/runtime_reports")
    target_dir = Path("unified_cache/backtests")
    
    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔄 Syncing {source_root} to {target_dir}...")
    
    sync_count = 0
    skip_count = 0
    
    # Iterate through server/lab/backtest folders
    for server_dir in source_root.iterdir():
        if not server_dir.is_dir():
            continue
            
        for lab_dir in server_dir.iterdir():
            if not lab_dir.is_dir():
                continue
                
            lab_id = lab_dir.name
            
            for report_file in lab_dir.glob("*_runtime.json"):
                # Extract backtest_id from filename (e.g., bt-id_runtime.json -> bt-id)
                backtest_id = report_file.name.replace("_runtime.json", "")
                
                # Target filename: {lab_id}_{backtest_id}.json (as expected by CachedAnalysisService)
                # Wait, CachedAnalysisService uses {lab_id}_*.json pattern?
                # Let's check CachedAnalysisService.get_cached_backtest_files_for_lab
                # pattern = f"{lab_id}_*.json"
                
                target_filename = f"{lab_id}_{backtest_id}.json"
                target_path = target_dir / target_filename
                
                if not target_path.exists():
                    try:
                        # Create symbolic link (absolute path for reliability)
                        # Actually, relative path is better if the whole unified_cache moves
                        # But let's use absolute for now as per implementation plan rules
                        os.symlink(report_file.absolute(), target_path)
                        sync_count += 1
                    except Exception as e:
                        print(f"❌ Error linking {report_file.name}: {e}")
                else:
                    skip_count += 1
                    
        if sync_count % 1000 == 0 and sync_count > 0:
            print(f"✅ Sync Progress: {sync_count} links created")

    print(f"\n📊 SYNC SUMMARY:")
    print(f"✅ Links created: {sync_count}")
    print(f"⏭️  Already exists: {skip_count}")
    print(f"📊 Total in target: {len(list(target_dir.glob('*.json')))}")

if __name__ == "__main__":
    sync_cache()
