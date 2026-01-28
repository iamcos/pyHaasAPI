import os
import zipfile
import glob

def restore_cache():
    prefix = "unified_cache.zip.part_"
    output_zip = "unified_cache.zip"
    extract_dir = "unified_cache"
    
    # 1. Find and sort parts correctly
    parts = glob.glob(f"{prefix}*")
    # Sort by the integer suffix to handle non-zero padded numbers correctly (part_2 vs part_10)
    try:
        parts.sort(key=lambda x: int(x.split('_')[-1]))
    except ValueError:
        parts.sort() # Fallback to lexicographical sort
    
    if not parts:
        print(f"❌ No parts found matching {prefix}*")
        return

    print(f"📦 Found {len(parts)} parts: {', '.join(parts)}")

    # 2. Join the parts
    print(f"🏗️  Reassembling {output_zip}...")
    try:
        with open(output_zip, 'wb') as outfile:
            for part in parts:
                print(f"  -> Adding {part}...")
                with open(part, 'rb') as infile:
                    # Use a buffer to avoid high memory usage
                    while True:
                        chunk = infile.read(1024 * 1024) # 1MB chunks
                        if not chunk:
                            break
                        outfile.write(chunk)
        print(f"✅ Reassembly complete: {output_zip}")
    except Exception as e:
        print(f"❌ Error during reassembly: {e}")
        return

    # 3. Extract the zip
    print(f"🔓 Extracting to '{extract_dir}' (this may take a while, 15GB total)...")
    try:
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
            
        with zipfile.ZipFile(output_zip, 'r') as zip_ref:
            # Get list of files to show progress
            members = zip_ref.infolist()
            total_files = len(members)
            
            # Safe extraction logic
            target_path = os.path.abspath(extract_dir)
            for i, member in enumerate(members):
                # Check for Zip Slip
                member_path = os.path.join(target_path, member.filename)
                if not os.path.abspath(member_path).startswith(target_path):
                    raise Exception(f"Attempted Path Traversal in Zip File: {member.filename}")
                
                zip_ref.extract(member, extract_dir)
                if i % 1000 == 0:
                    percent = (i / total_files) * 100
                    print(f"  📊 Progress: {percent:.1f}% ({i}/{total_files} files)")
                    
        print(f"✨ EXTRACTION COMPLETE! Data is in '{extract_dir}'")
        
    except zipfile.BadZipFile:
        print("❌ Reassembled file is not a valid zip archive. Parts might be corrupted or missing.")
    except Exception as e:
        print(f"❌ Error during extraction: {e}")

if __name__ == "__main__":
    restore_cache()
