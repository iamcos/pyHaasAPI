
import asyncio
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings

async def probe():
    sm = ServerManager(Settings())
    target = "srv03"
    
    print(f"Connecting to {target}...")
    if not await sm.connect_server(target):
        print("Failed to connect.")
        return

    # Probe 1: Check Process Info
    print("\n[Probing Process Info]")
    cmd = "pgrep -a -f Haas"
    success, stdout, stderr = await sm.execute_remote_command(target, cmd)
    print(f"Success: {success}")
    print(f"Output:\n{stdout}")
    
    # Probe 2: Check Systemd
    print("\n[Probing Systemd]")
    # Look for any service with 'haas' in the name
    cmd = "systemctl list-units --type=service --all | grep -i haas"
    success, stdout, stderr = await sm.execute_remote_command(target, cmd)
    print(f"Success: {success}")
    print(f"Output:\n{stdout}")
    
    # Probe 3: Check Docker
    print("\n[Probing Docker]")
    cmd = "docker ps --format '{{.Names}}' | grep -i haas"
    success, stdout, stderr = await sm.execute_remote_command(target, cmd)
    print(f"Success: {success}")
    print(f"Output:\n{stdout}")

    await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(probe())
