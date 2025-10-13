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
        """Load server configurations from settings or defaults"""
        # Default server configurations
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
        
        self.logger.info(f"Loaded {len(self.servers)} server configurations")
    
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
            
            # Build SSH command
            ssh_cmd = self._build_ssh_command(server_status.config)
            
            # Start SSH tunnel process
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for connection to establish
            await asyncio.sleep(2)
            
            # Preflight check: verify localhost:8090 (and 8092) are reachable
            preflight_ok = await self.preflight_check()
            if not preflight_ok:
                try:
                    # Clean up process if preflight fails
                    if process and process.poll() is None:
                        process.terminate()
                except Exception:
                    pass
                server_status.status = ServerStatus.FAILED
                raise ConnectionError(
                    "Tunnel preflight failed. Start the mandated SSH tunnel: "
                    "ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv0*"
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
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
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
        Switch to a different server
        
        Args:
            server_name: Name of the server to switch to
            
        Returns:
            True if switch successful, False otherwise
        """
        if server_name not in self.servers:
            raise ServerError(f"Unknown server: {server_name}")
        
        # If a different server is active, gracefully disconnect first (single-tunnel policy)
        if self.active_server and self.active_server != server_name:
            await self.disconnect_server(self.active_server)
        # Connect to the requested server
        if await self.connect_server(server_name):
            self.active_server = server_name
            self.logger.info(f"Switched to server {server_name}")
            return True
        
        return False
    
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
