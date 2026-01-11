import asyncio
import os
import sys
from datetime import datetime
from telethon import TelegramClient

# Configuration from telegram-mcp/.env
API_ID = 26840423
API_HASH = "b1675e4a4791a8ae25f16e792127ee16"
SESSION_PATH = "/home/cosmos/Documents/github/telegram-mcp/session_name.session"

async def main():
    if not os.path.exists(SESSION_PATH):
        print(f"❌ Session file not found: {SESSION_PATH}")
        return

    # Use the session file from telegram-mcp
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    
    try:
        await client.start()
        print("✅ Telegram connection established.")
        
        # Get list of parts in the current directory
        parts = sorted([f for f in os.listdir('.') if f.startswith('unified_cache.zip.part_')])
        
        if not parts:
            print("❌ No parts found to upload (unified_cache.zip.part_*)")
            return

        print(f"🚀 Starting upload of {len(parts)} parts to Saved Messages...")
        
        for part in parts:
            file_path = os.path.abspath(part)
            file_size_gb = os.path.getsize(file_path) / (1024**3)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Uploading {part} ({file_size_gb:.2f} GB)...")
            
            last_percent = -10
            def progress_callback(current, total):
                nonlocal last_percent
                percent = (current / total) * 100
                if int(percent) >= last_percent + 10:
                    last_percent = int(percent // 10) * 10
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Progress: {last_percent}%")

            await client.send_file(
                'me', 
                file_path, 
                caption=f"Unified Cache Part: {part}",
                progress_callback=progress_callback
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Finished {part}")
            
        print("✨ All parts uploaded successfully!")
        
    except Exception as e:
        print(f"❌ Error during upload: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
