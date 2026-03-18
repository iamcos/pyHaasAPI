"""
Server Manager for pyHaasAPI v2

Manages SSH tunnels to multiple HaasOnline servers with automatic reconnection,
health monitoring, and load balancing capabilities.
"""

import asyncio
import subprocess
import time
import signal
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from contextlib import asynccontextmanager
import json
import psutil

from ..exceptions import ServerError, ConnectionError, ConfigurationError
from ..core.logging import get_logger
from ..config.settings import Settings


class ServerStatus(Enum):
    """Server connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


@dataclass
class ServerConfig:
    """Configuration for a single server"""
    name: str  # srv01, srv02, srv03
    hostname: str  # prod@srv01, prod@srv02, prod@srv03
    username: str = "prod"
    ssh_key_path: Optional[str] = None
    api_ports: List[int] = field(default_factory=lambda: [8090, 8092])
    local_ports: List[int] = field(default_factory=lambda: [8090, 8092])
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 5.0
    health_check_interval: float = 60.0
    enabled: bool = True
    api_email: Optional[str] = None
    api_password: Optional[str] = None


@dataclass
class ServerConnectionStatus:
    """Current status of a server connection"""
    config: ServerConfig
    status: ServerStatus = ServerStatus.DISCONNECTED
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    last_health_check: Optional[float] = None
    connection_count: int = 0
    last_error: Optional[str] = None
    reconnect_attempts: int = 0


class ServerManager:
    """
    Manages SSH tunnels to multiple HaasOnline servers
    
    Features:
    - Multiple server support (srv01, srv02, srv03)
    - Automatic SSH tunnel creation with port forwarding
    - Health monitoring and automatic reconnection
    - Server selection and load balancing
    - Connection status tracking
    - Graceful shutdown and cleanup
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger("server_manager")
        self.servers: Dict[str, ServerConnectionStatus] = {}
        self.active_server: Optional[str] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()
        
        # Load server configurations
        self._load_server_configs()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        # Enforce allowed local ports
        for name, status in self.servers.items():
            allowed_ports = [8090, 8092]
            if status.config.local_ports != allowed_ports or status.config.api_ports != allowed_ports:
                raise ConfigurationError(
                    f"Invalid port forwarding for {name}. Only 8090 and 8092 are allowed."
                )
    
    def _load_server_configs(self) -> None:
        """Load server configurations from file or use defaults"""
        file_path = "servers.json"
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                for name, config_data in data.items():
                    config = ServerConfig(**config_data)
                    self.servers[name] = ServerConnectionStatus(config=config)
                
                self.logger.info(f"Loaded {len(self.servers)} server configurations from {file_path}")
                return
            except Exception as e:
                self.logger.error(f"Failed to load server configurations from {file_path}: {e}")
        
        # Fallback to default server configurations
        default_servers = {
            "srv01": ServerConfig(
                name="srv01",
                hostname="srv01",
                username="prod",
                ssh_key_path=os.path.expanduser("~/.ssh/id_rsa"),
                api_ports=[8090, 8092],
                local_ports=[8090, 8092]
            ),
            "srv02": ServerConfig(
                name="srv02", 
                hostname="srv02",
                username="prod",
                ssh_key_path=os.path.expanduser("~/.ssh/id_rsa"),
                api_ports=[8090, 8092],
                local_ports=[8090, 8092]
            ),
            "srv03": ServerConfig(
                name="srv03",
                hostname="srv03", 
                username="prod",
                ssh_key_path=os.path.expanduser("~/.ssh/id_rsa"),
                api_ports=[8090, 8092],
                local_ports=[8090, 8092]
            )
        }
        
        # Initialize server statuses
        for name, config in default_servers.items():
            self.servers[name] = ServerConnectionStatus(config=config)
        
        # Save defaults to file
        self.save_servers()
        self.logger.info(f"Initialized {len(self.servers)} default server configurations")

    def save_servers(self) -> None:
        """Save server configurations to servers.json"""
        import dataclasses
        file_path = "servers.json"
        try:
            data = {name: dataclasses.asdict(status.config) for name, status in self.servers.items()}
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Saved {len(self.servers)} server configurations to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save server configurations: {e}")

    def add_server(self, config: ServerConfig) -> None:
        """Add a new server configuration"""
        if config.name in self.servers:
            raise ConfigurationError(f"Server with name {config.name} already exists")
        
        self.servers[config.name] = ServerConnectionStatus(config=config)
        self.save_servers()
        self.logger.info(f"Added new server configuration: {config.name}")

    def edit_server(self, name: str, config: ServerConfig) -> None:
        """Edit an existing server configuration"""
        if name not in self.servers:
            raise ConfigurationError(f"Server with name {name} does not exist")
        
        # If name is being changed, remove old and add new
        if name != config.name:
            if config.name in self.servers:
                raise ConfigurationError(f"Server with name {config.name} already exists")
            del self.servers[name]
        
        self.servers[config.name] = ServerConnectionStatus(config=config)
        self.save_servers()
        self.logger.info(f"Updated server configuration: {config.name}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def connect_server(self, server_name: str) -> bool:
        """
        Connect to a specific server via SSH tunnel
        
        Args:
            server_name: Name of the server to connect to (srv01, srv02, srv03)
            
        Returns:
            True if connection successful, False otherwise
        """
        if server_name not in self.servers:
            raise ServerError(f"Unknown server: {server_name}")
        
        server_status = self.servers[server_name]

        # Single-tunnel guard: disallow switching servers without teardown
        if self.active_server and self.active_server != server_name:
            raise ConfigurationError(
                f"Single-tunnel policy enforced. Active server is {self.active_server}. "
                f"Disconnect before connecting to {server_name}."
            )
        
        if server_status.status == ServerStatus.CONNECTED:
            self.logger.info(f"Server {server_name} already connected")
            return True
        
        try:
            self.logger.info(f"Connecting to server {server_name}")
            server_status.status = ServerStatus.CONNECTING
            
            # Guard: Check and Cleanup ports 8090/8092 if already in use locally
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port in [8090, 8092] and conn.status == 'LISTEN':
                        try:
                            p = psutil.Process(conn.pid)
                            if "ssh" in p.name().lower():
                                self.logger.warning(f"Cleaning up stale SSH tunnel (PID: {conn.pid}) on port {conn.laddr.port}")
                                p.terminate()
                                try:
                                    p.wait(timeout=2)
                                except psutil.TimeoutExpired:
                                    p.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except Exception as e:
                self.logger.warning(f"Error during port cleanup: {e}")

            # Build SSH command
            ssh_cmd = self._build_ssh_command(server_status.config)
            
            # Start SSH tunnel process
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for connection to establish with active polling
            start_time = time.time()
            connected = False
            while time.time() - start_time < server_status.config.timeout:
                if await self.preflight_check(timeout=1.0):
                    connected = True
                    break
                await asyncio.sleep(0.5)
                
                # Check if process died
                if process.poll() is not None:
                    break
            
            if not connected:
                try:
                    # Clean up process if preflight fails
                    if process and process.poll() is None:
                        process.terminate()
                except Exception:
                    pass
                server_status.status = ServerStatus.FAILED
                raise ConnectionError(
                    f"Tunnel preflight failed after {server_status.config.timeout}s. "
                    "Ensure SSH authentication works without password (key-based) and ports are free."
                )
            
            # Check if process is still running
            if process.poll() is None:
                server_status.process = process
                server_status.pid = process.pid
                server_status.status = ServerStatus.CONNECTED
                server_status.connection_count += 1
                server_status.last_error = None
                server_status.reconnect_attempts = 0
                
                self.logger.info(f"Successfully connected to {server_name} (PID: {process.pid})")
                
                # Set as active server if none is active
                if self.active_server is None:
                    self.active_server = server_name
                
                return True
            else:
                # Process exited, get error
                stdout, stderr = process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                server_status.last_error = error_msg
                server_status.status = ServerStatus.FAILED
                
                self.logger.error(f"Failed to connect to {server_name}: {error_msg}")
                return False
                
        except Exception as e:
            server_status.status = ServerStatus.FAILED
            server_status.last_error = str(e)
            self.logger.error(f"Error connecting to {server_name}: {e}")
            return False
    
    def _build_ssh_command(self, config: ServerConfig) -> List[str]:
        """Build SSH command for tunnel creation"""
        # Enforce exact ports 8090 and 8092
        if config.local_ports != [8090, 8092] or config.api_ports != [8090, 8092]:
            raise ConfigurationError("Only local/api ports 8090 and 8092 are permitted")
        cmd = [
            "ssh",
            "-N",  # Don't execute remote command
            "-L", f"{config.local_ports[0]}:127.0.0.1:{config.api_ports[0]}",  # Port 8090
            "-L", f"{config.local_ports[1]}:127.0.0.1:{config.api_ports[1]}",  # Port 8092
        ]
        
        # Add SSH key if specified
        if config.ssh_key_path and os.path.exists(config.ssh_key_path):
            cmd.extend(["-i", config.ssh_key_path])
        
        # Add connection options
        cmd.extend([
            "-o", "StrictHostKeyChecking=accept-new",  # Safer than 'no', auto-accepts new keys but warns on change
            "-o", "BatchMode=yes",  # Fail instead of hanging on interaction
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-o", f"ConnectTimeout={config.timeout}",
        ])
        
        # Add target host
        cmd.append(f"{config.username}@{config.hostname}")
        
        return cmd
    
    async def disconnect_server(self, server_name: str) -> bool:
        """
        Disconnect from a specific server
        
        Args:
            server_name: Name of the server to disconnect from
            
        Returns:
            True if disconnection successful, False otherwise
        """
        if server_name not in self.servers:
            raise ServerError(f"Unknown server: {server_name}")
        
        server_status = self.servers[server_name]
        
        if server_status.status == ServerStatus.DISCONNECTED:
            self.logger.info(f"Server {server_name} already disconnected")
            return True
        
        try:
            self.logger.info(f"Disconnecting from server {server_name}")
            
            if server_status.process and server_status.process.poll() is None:
                # Terminate the SSH process
                try:
                    server_status.process.terminate()
                    await asyncio.sleep(1)
                    
                    # Force kill if still running
                    if server_status.process.poll() is None:
                        server_status.process.kill()
                        await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"Error terminating process for {server_name}: {e}")
            
            server_status.status = ServerStatus.DISCONNECTED
            server_status.process = None
            server_status.pid = None
            
            # Clear active server if it was this one
            if self.active_server == server_name:
                self.active_server = None
            
            self.logger.info(f"Successfully disconnected from {server_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from {server_name}: {e}")
            return False
    
    async def switch_server(self, server_name: str) -> bool:
        """
        Switch to a different server with global locking
        """
        async with self._lock:
            # Aggressive cleanup of stale tunnels on these ports
            import psutil
            for conn in psutil.net_connections():
                if conn.laddr.port in [8090, 8092] and conn.status == 'LISTEN':
                    try:
                        p = psutil.Process(conn.pid)
                        if "ssh" in p.name().lower():
                            self.logger.info(f"Killing stale SSH tunnel (PID: {conn.pid}) on port {conn.laddr.port}")
                            p.terminate()
                            try:
                                p.wait(timeout=2)
                            except psutil.TimeoutExpired:
                                p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            return await self._switch_server_internal(server_name)

    async def _switch_server_internal(self, server_name: str) -> bool:
        """
        Internal switch implementation without lock
        """
        if server_name not in self.servers:
            raise ServerError(f"Unknown server: {server_name}")
        
        # If a different server is active, gracefully disconnect first (single-tunnel policy)
        if self.active_server and self.active_server != server_name:
            await self.disconnect_server(self.active_server)
        # Connect to the requested server
        if await self.connect_server(server_name):
            self.active_server = server_name
            # self.logger.info(f"Switched to server {server_name}")
            return True
        
        return False

    @asynccontextmanager
    async def server_session(self, server_name: str):
        """
        Context manager that holds the server lock during the entire session
        """
        async with self._lock:
            if await self._switch_server_internal(server_name):
                yield server_name
            else:
                raise ServerError(f"Could not establish session for {server_name}")
    
    async def get_server_status(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of server(s)
        
        Args:
            server_name: Specific server name, or None for all servers
            
        Returns:
            Dictionary with server status information
        """
        if server_name:
            if server_name not in self.servers:
                raise ServerError(f"Unknown server: {server_name}")
            
            server_status = self.servers[server_name]
            return {
                "name": server_name,
                "status": server_status.status.value,
                "connected": server_status.status == ServerStatus.CONNECTED,
                "pid": server_status.pid,
                "connection_count": server_status.connection_count,
                "last_error": server_status.last_error,
                "reconnect_attempts": server_status.reconnect_attempts,
                "last_health_check": server_status.last_health_check,
                "is_active": self.active_server == server_name
            }
        else:
            # Return status for all servers
            return {
                name: {
                    "name": name,
                    "status": status.status.value,
                    "connected": status.status == ServerStatus.CONNECTED,
                    "pid": status.pid,
                    "connection_count": status.connection_count,
                    "last_error": status.last_error,
                    "reconnect_attempts": status.reconnect_attempts,
                    "last_health_check": status.last_health_check,
                    "is_active": self.active_server == name
                }
                for name, status in self.servers.items()
            }
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all available servers with their status"""
        servers = []
        for name, status in self.servers.items():
            servers.append({
                "name": name,
                "hostname": status.config.hostname,
                "username": status.config.username,
                "status": status.status.value,
                "connected": status.status == ServerStatus.CONNECTED,
                "enabled": status.config.enabled,
                "is_active": self.active_server == name
            })
        return servers
    
    async def start_monitoring(self) -> None:
        """Start background monitoring of server connections"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.logger.warning("Monitoring already running")
            return
        
        self.monitoring_task = asyncio.create_task(self._monitor_servers())
        self.logger.info("Started server monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            self.logger.info("Stopped server monitoring")
    
    async def _monitor_servers(self) -> None:
        """Background task to monitor server connections"""
        while not self.shutdown_event.is_set():
            try:
                for name, status in self.servers.items():
                    if status.status == ServerStatus.CONNECTED:
                        # Check if process is still running
                        if status.process and status.process.poll() is not None:
                            self.logger.warning(f"Server {name} process died, attempting reconnection")
                            status.status = ServerStatus.RECONNECTING
                            
                            # Attempt reconnection
                            if await self.connect_server(name):
                                self.logger.info(f"Successfully reconnected to {name}")
                            else:
                                status.reconnect_attempts += 1
                                if status.reconnect_attempts >= status.config.retry_attempts:
                                    status.status = ServerStatus.FAILED
                                    self.logger.error(f"Failed to reconnect to {name} after {status.reconnect_attempts} attempts")
                        
                        # Update health check timestamp
                        status.last_health_check = time.time()
                
                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in server monitoring: {e}")
                await asyncio.sleep(5)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all connections"""
        self.logger.info("Shutting down server manager")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Disconnect all servers
        for server_name in list(self.servers.keys()):
            await self.disconnect_server(server_name)
        
        self.shutdown_event.set()
        self.logger.info("Server manager shutdown complete")
    
    async def ensure_srv03_tunnel(self) -> bool:
        """Convenience: ensure mandated tunnel to srv03 is active.
        - Respects single-tunnel policy
        - Performs preflight checks and retries once
        Returns True on success, False otherwise.
        """
        target = "srv03"
        # If already connected to srv03, just re-check health
        if self.active_server == target and await self.health_check(target):
            return True
        # If connected to another server, fail fast per policy
        if self.active_server and self.active_server != target:
            self.logger.error(
                f"Active server {self.active_server} present; cannot connect to {target} without teardown"
            )
            return False
        # Attempt connect with one retry on preflight failure
        if await self.connect_server(target):
            return True
        await asyncio.sleep(1.0)
        self.logger.warning("Retrying srv03 tunnel after initial failure…")
        return await self.connect_server(target)
    
    def get_active_server_config(self) -> Optional[ServerConfig]:
        """Get configuration of the currently active server"""
        if self.active_server and self.active_server in self.servers:
            return self.servers[self.active_server].config
        return None
    
    def get_active_server_name(self) -> Optional[str]:
        """Get name of the currently active server"""
        return self.active_server
    
    async def health_check(self, server_name: str) -> bool:
        """
        Perform health check on a server
        
        Args:
            server_name: Name of the server to check
            
        Returns:
            True if server is healthy, False otherwise
        """
        if server_name not in self.servers:
            raise ServerError(f"Unknown server: {server_name}")
        
        server_status = self.servers[server_name]
        
        if server_status.status != ServerStatus.CONNECTED:
            return False
        
        try:
            # Check if process is still running
            if server_status.process and server_status.process.poll() is not None:
                return False
            
            # Check if ports are accessible
            for port in server_status.config.local_ports:
                try:
                    # Try to connect to local port
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection('127.0.0.1', port),
                        timeout=5.0
                    )
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    return False
            
            server_status.last_health_check = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed for {server_name}: {e}")
            return False

    async def preflight_check(self, check_auxiliary: bool = True, timeout: float = 2.0) -> bool:
        """Verify that mandated local ports are reachable on localhost.
        Returns True if 127.0.0.1:8090 is reachable (and 8092 if requested).
        """
        async def _probe(port: int) -> bool:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection('127.0.0.1', port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                return True
            except Exception:
                return False
        ok_primary = await _probe(8090)
        ok_aux = True
        if check_auxiliary:
            ok_aux = await _probe(8092)
        return ok_primary and ok_aux

    async def execute_remote_command(self, server_name: str, command: str) -> Tuple[bool, str, str]:
        """
        Execute a command on a remote server via SSH
        
        Args:
            server_name: Name of the server
            command: Command to execute
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if server_name not in self.servers:
            return False, "", f"Unknown server: {server_name}"
            
        config = self.servers[server_name].config
        
        # Build SSH command for execution
        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={config.timeout}",
        ]
        
        if config.ssh_key_path and os.path.exists(config.ssh_key_path):
            cmd.extend(["-i", config.ssh_key_path])
            
        cmd.append(f"{config.username}@{config.hostname}")
        
        # Smart Sudo: If command contains sudo and we have a password, 
        # replace 'sudo' with 'sudo -S' and prepare to pipe password.
        use_password = False
        if "sudo " in command and self.settings.sudo_password:
            # Only inject -S if not already there and -n is not there
            if "sudo -S" not in command and "sudo -n" not in command:
                command = command.replace("sudo ", "sudo -S ")
                use_password = True
            elif "sudo -n" in command and self.settings.sudo_password:
                # Replace -n with -S to allow password usage
                command = command.replace("sudo -n", "sudo -S")
                use_password = True

        cmd.append(command)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if use_password else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                if use_password:
                    # Send password followed by newline
                    self.logger.debug(f"Sending sudo password to {server_name}")
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(input=f"{self.settings.sudo_password}\n".encode()), 
                        timeout=config.timeout + 2
                    )
                else:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=config.timeout + 2)
                
                return (
                    process.returncode == 0,
                    stdout.decode().strip(),
                    stderr.decode().strip()
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                return False, "", f"SSH command timed out after {config.timeout + 2}s"
            except asyncio.CancelledError:
                # Ensure cleaning up if task is cancelled
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                raise
                
        except Exception as e:
            if isinstance(e, asyncio.CancelledError):
                raise
            msg = f"Failed to execute remote command: {e}"
            self.logger.error(msg)
            return False, "", msg

    async def get_server_resources(self, server_name: str) -> Dict[str, Any]:
        """
        Get resource usage stats from remote server
        """
        # Improved script to be faster and more robust
        script = """
        echo "CPU_LOAD: $(cat /proc/loadavg | awk '{print $1}')"
        echo "RAM_USED: $(free -m | awk 'NR==2{if($2>0) printf "%.1f", $3/$2*100; else print "0"}')"
        echo "DISK_USED: $(df -h / | awk 'NR==2{print $5}' | tr -d '%')"
        if pgrep -f "Haas" > /dev/null; then echo "HAAS_STATUS: Running"; else echo "HAAS_STATUS: Stopped"; fi
        """
        
        success, stdout, stderr = await self.execute_remote_command(server_name, script)
        
        stats = {
            "cpu_load": "N/A",
            "ram_usage": "N/A",
            "disk_usage": "N/A",
            "haas_status": "Unknown",
            "success": success,
            "error": stderr if not success else None
        }
        
        if success:
            try:
                for line in stdout.splitlines():
                    line = line.strip()
                    if not line: continue
                    if line.startswith("CPU_LOAD:"):
                        stats["cpu_load"] = f"{line.split(':', 1)[1].strip()}"
                    elif line.startswith("RAM_USED:"):
                        stats["ram_usage"] = f"{line.split(':', 1)[1].strip()}%"
                    elif line.startswith("DISK_USED:"):
                        stats["disk_usage"] = f"{line.split(':', 1)[1].strip()}%"
                    elif line.startswith("HAAS_STATUS:"):
                        stats["haas_status"] = f"{line.split(':', 1)[1].strip()}"
            except Exception as e:
                self.logger.error(f"Error parsing resource stats from {server_name}: {e}")
        
        return stats

    async def restart_service(self, server_name: str) -> Tuple[bool, str]:
        """
        Attempt to restart Haas service using heuristics (Systemd -> Docker)
        
        Args:
            server_name: Name of the server
            
        Returns:
            Tuple of (success, message)
        """
        self.logger.info(f"Attempting smart restart for {server_name}")
        
        # Compound script to detect and restart in one go
        # This minimizes SSH round-trips and handles the "check-then-act" logic remotely
        script = """
        if systemctl list-units --full -all | grep -Fq "haas.service"; then
             echo "Found systemd service: haas.service"
             # Try restart, might need sudo passwordless for this user
             if sudo -n systemctl restart haas.service 2>/dev/null; then
                 echo "SUCCESS: Restarted via Systemd"
                 exit 0
             else
                 echo "FAILED: Found systemd but 'sudo systemctl restart' failed (permission?)"
                 exit 1
             fi
        elif docker ps | grep -q "haas"; then
             echo "Found Docker container"
             # Try to restart container matching 'haas'
             container_id=$(docker ps -q -f name=haas | head -n 1)
             if [ -n "$container_id" ]; then
                 docker restart "$container_id"
                 echo "SUCCESS: Restarted via Docker ($container_id)"
                 exit 0
             else
                 # Fallback grep if name filter failed
                 docker restart $(docker ps | grep "haas" | awk '{print $1}' | head -n 1)
                 echo "SUCCESS: Restarted via Docker (grep match)"
                 exit 0
             fi
        else
             echo "FAILED: No known managed service (Systemd/Docker) found"
             exit 1
        fi
        """
        
        success, stdout, stderr = await self.execute_remote_command(server_name, script)
        
        # Parse output for cleaner messages
        msg = stdout.strip() if stdout else stderr.strip()
        if "SUCCESS:" in msg:
             # Extract the success message specifically
             msg = [line for line in msg.splitlines() if "SUCCESS:" in line][0].replace("SUCCESS: ", "")
             return True, msg
        
        return False, f"Restart failed: {msg}"
