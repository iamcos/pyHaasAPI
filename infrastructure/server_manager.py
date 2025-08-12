#!/usr/bin/env python3
"""
Server Connection Management System

This module provides comprehensive server connection management for the distributed
trading bot testing automation system, handling SSH tunnels, connection health monitoring,
and graceful error handling for 504 errors and connection switching.
"""

import subprocess
import time
import logging
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import threading
import socket
from contextlib import closing

logger = logging.getLogger(__name__)

class ServerRole(Enum):
    """Server roles for different operations"""
    BACKTEST = "backtest"
    DEVELOPMENT = "development"
    MIXED = "mixed"

class ConnectionStatus(Enum):
    """Connection status states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class ServerConfig:
    """Configuration for a server connection"""
    server_id: str
    host: str
    ssh_port: int
    api_ports: List[int]  # [8090, 8092]
    max_population: int
    max_concurrent_tasks: int
    role: ServerRole
    ssh_user: str = "root"
    local_ports: Optional[List[int]] = None  # Local ports for SSH tunnels

@dataclass
class ConnectionHealth:
    """Health status of a server connection"""
    server_id: str
    status: ConnectionStatus
    last_check: float
    response_time: Optional[float]
    error_count: int
    last_error: Optional[str]
    ssh_tunnel_active: bool
    api_accessible: bool

class SSHTunnelManager:
    """Manages SSH tunnels for server connections"""
    
    def __init__(self):
        self.active_tunnels: Dict[str, subprocess.Popen] = {}
        self.tunnel_lock = threading.Lock()
    
    def create_tunnel(self, server_config: ServerConfig) -> bool:
        """
        Create SSH tunnel for a server.
        
        Args:
            server_config: Server configuration
            
        Returns:
            True if tunnel created successfully, False otherwise
        """
        with self.tunnel_lock:
            if server_config.server_id in self.active_tunnels:
                logger.info(f"SSH tunnel already exists for {server_config.server_id}")
                return True
            
            try:
                # Determine local ports
                if server_config.local_ports:
                    local_ports = server_config.local_ports
                else:
                    local_ports = self._find_available_ports(len(server_config.api_ports))
                
                if len(local_ports) != len(server_config.api_ports):
                    logger.error(f"Could not find enough available local ports for {server_config.server_id}")
                    return False
                
                # Build SSH command
                ssh_cmd = ["ssh", "-N", "-o", "StrictHostKeyChecking=no"]
                
                # Add port forwarding for each API port
                for local_port, remote_port in zip(local_ports, server_config.api_ports):
                    ssh_cmd.extend(["-L", f"{local_port}:localhost:{remote_port}"])
                
                # Add server connection
                ssh_cmd.append(f"{server_config.ssh_user}@{server_config.host}")
                
                logger.info(f"Creating SSH tunnel for {server_config.server_id}: {' '.join(ssh_cmd)}")
                
                # Start SSH tunnel
                process = subprocess.Popen(
                    ssh_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
                
                # Wait a moment for tunnel to establish
                time.sleep(2)
                
                # Check if process is still running
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    logger.error(f"SSH tunnel failed for {server_config.server_id}: {stderr.decode()}")
                    return False
                
                # Store tunnel info
                self.active_tunnels[server_config.server_id] = process
                server_config.local_ports = local_ports
                
                logger.info(f"SSH tunnel established for {server_config.server_id} on ports {local_ports}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to create SSH tunnel for {server_config.server_id}: {e}")
                return False
    
    def close_tunnel(self, server_id: str) -> bool:
        """
        Close SSH tunnel for a server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if tunnel closed successfully, False otherwise
        """
        with self.tunnel_lock:
            if server_id not in self.active_tunnels:
                logger.info(f"No SSH tunnel exists for {server_id}")
                return True
            
            try:
                process = self.active_tunnels[server_id]
                process.terminate()
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"SSH tunnel for {server_id} did not terminate gracefully, killing...")
                    process.kill()
                    process.wait()
                
                del self.active_tunnels[server_id]
                logger.info(f"SSH tunnel closed for {server_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to close SSH tunnel for {server_id}: {e}")
                return False
    
    def is_tunnel_active(self, server_id: str) -> bool:
        """Check if SSH tunnel is active for a server"""
        with self.tunnel_lock:
            if server_id not in self.active_tunnels:
                return False
            
            process = self.active_tunnels[server_id]
            return process.poll() is None
    
    def _find_available_ports(self, count: int, start_port: int = 8100) -> List[int]:
        """Find available local ports for SSH tunnels"""
        available_ports = []
        port = start_port
        
        while len(available_ports) < count and port < 65535:
            if self._is_port_available(port):
                available_ports.append(port)
            port += 1
        
        return available_ports
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for use"""
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(('localhost', port))
                return True
            except OSError:
                return False

class ServerHealthMonitor:
    """Monitors health of server connections"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_status: Dict[str, ConnectionHealth] = {}
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.health_lock = threading.Lock()
    
    def start_monitoring(self, server_configs: Dict[str, ServerConfig]):
        """Start health monitoring for all servers"""
        if self.monitoring_active:
            logger.warning("Health monitoring is already active")
            return
        
        # Initialize health status
        with self.health_lock:
            for server_id, config in server_configs.items():
                self.health_status[server_id] = ConnectionHealth(
                    server_id=server_id,
                    status=ConnectionStatus.DISCONNECTED,
                    last_check=0.0,
                    response_time=None,
                    error_count=0,
                    last_error=None,
                    ssh_tunnel_active=False,
                    api_accessible=False
                )
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(server_configs,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Server health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Server health monitoring stopped")
    
    def get_health_status(self, server_id: str) -> Optional[ConnectionHealth]:
        """Get health status for a specific server"""
        with self.health_lock:
            return self.health_status.get(server_id)
    
    def get_all_health_status(self) -> Dict[str, ConnectionHealth]:
        """Get health status for all servers"""
        with self.health_lock:
            return self.health_status.copy()
    
    def _monitor_loop(self, server_configs: Dict[str, ServerConfig]):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                for server_id, config in server_configs.items():
                    self._check_server_health(server_id, config)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(5)  # Brief pause before retrying
    
    def _check_server_health(self, server_id: str, config: ServerConfig):
        """Check health of a specific server"""
        start_time = time.time()
        
        with self.health_lock:
            health = self.health_status[server_id]
            health.last_check = start_time
        
        try:
            # Check if SSH tunnel is active (if local ports are configured)
            ssh_tunnel_active = True  # Assume true if no tunnel manager
            
            # Check API accessibility
            api_accessible = False
            response_time = None
            
            if config.local_ports:
                # Use local ports for API check
                for local_port in config.local_ports:
                    try:
                        url = f"http://localhost:{local_port}/api/health"  # Assuming health endpoint
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            api_accessible = True
                            response_time = time.time() - start_time
                            break
                    except requests.RequestException:
                        continue
            
            # Update health status
            with self.health_lock:
                health.ssh_tunnel_active = ssh_tunnel_active
                health.api_accessible = api_accessible
                health.response_time = response_time
                
                if api_accessible:
                    health.status = ConnectionStatus.CONNECTED
                    health.error_count = 0
                    health.last_error = None
                else:
                    health.status = ConnectionStatus.ERROR
                    health.error_count += 1
                    health.last_error = "API not accessible"
        
        except Exception as e:
            with self.health_lock:
                health.status = ConnectionStatus.ERROR
                health.error_count += 1
                health.last_error = str(e)
                health.ssh_tunnel_active = False
                health.api_accessible = False

class ServerManager:
    """Main server connection manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.server_configs: Dict[str, ServerConfig] = {}
        self.ssh_manager = SSHTunnelManager()
        self.health_monitor = ServerHealthMonitor()
        self.connection_lock = threading.Lock()
        
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """Load server configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            self.server_configs = {}
            for server_id, server_data in config_data.get('servers', {}).items():
                self.server_configs[server_id] = ServerConfig(
                    server_id=server_id,
                    host=server_data['host'],
                    ssh_port=server_data.get('ssh_port', 22),
                    api_ports=server_data['api_ports'],
                    max_population=server_data['max_population'],
                    max_concurrent_tasks=server_data['max_concurrent_tasks'],
                    role=ServerRole(server_data['role']),
                    ssh_user=server_data.get('ssh_user', 'root')
                )
            
            logger.info(f"Loaded configuration for {len(self.server_configs)} servers")
            
        except Exception as e:
            logger.error(f"Failed to load server configuration: {e}")
            raise
    
    def connect_to_server(self, server_id: str) -> bool:
        """
        Establish connection to a specific server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if connection established successfully, False otherwise
        """
        if server_id not in self.server_configs:
            logger.error(f"Server configuration not found for {server_id}")
            return False
        
        config = self.server_configs[server_id]
        
        with self.connection_lock:
            logger.info(f"Connecting to server {server_id}...")
            
            # Create SSH tunnel
            if not self.ssh_manager.create_tunnel(config):
                logger.error(f"Failed to create SSH tunnel for {server_id}")
                return False
            
            # Wait for tunnel to stabilize
            time.sleep(3)
            
            # Verify connection
            if self._verify_connection(config):
                logger.info(f"Successfully connected to server {server_id}")
                return True
            else:
                logger.error(f"Connection verification failed for {server_id}")
                self.ssh_manager.close_tunnel(server_id)
                return False
    
    def disconnect_from_server(self, server_id: str) -> bool:
        """
        Disconnect from a specific server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if disconnection successful, False otherwise
        """
        with self.connection_lock:
            logger.info(f"Disconnecting from server {server_id}...")
            return self.ssh_manager.close_tunnel(server_id)
    
    def connect_to_all_servers(self) -> Dict[str, bool]:
        """
        Connect to all configured servers.
        
        Returns:
            Dictionary mapping server_id to connection success status
        """
        results = {}
        
        for server_id in self.server_configs:
            results[server_id] = self.connect_to_server(server_id)
        
        # Start health monitoring
        if any(results.values()):
            self.health_monitor.start_monitoring(self.server_configs)
        
        return results
    
    def disconnect_from_all_servers(self):
        """Disconnect from all servers"""
        self.health_monitor.stop_monitoring()
        
        for server_id in self.server_configs:
            self.disconnect_from_server(server_id)
    
    def get_available_servers(self, role: Optional[ServerRole] = None) -> List[str]:
        """
        Get list of available servers, optionally filtered by role.
        
        Args:
            role: Optional server role filter
            
        Returns:
            List of available server IDs
        """
        available_servers = []
        
        for server_id, config in self.server_configs.items():
            if role and config.role != role:
                continue
            
            health = self.health_monitor.get_health_status(server_id)
            if health and health.status == ConnectionStatus.CONNECTED:
                available_servers.append(server_id)
        
        return available_servers
    
    def execute_api_request(self, server_id: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Execute API request on a specific server with error handling.
        
        Args:
            server_id: Server identifier
            endpoint: API endpoint
            method: HTTP method
            data: Request data for POST/PUT requests
            
        Returns:
            API response data or None if failed
        """
        if server_id not in self.server_configs:
            logger.error(f"Server configuration not found for {server_id}")
            return None
        
        config = self.server_configs[server_id]
        
        if not config.local_ports:
            logger.error(f"No local ports configured for server {server_id}")
            return None
        
        # Try each local port
        for local_port in config.local_ports:
            try:
                url = f"http://localhost:{local_port}{endpoint}"
                
                if method.upper() == "GET":
                    response = requests.get(url, timeout=30)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, timeout=30)
                elif method.upper() == "PUT":
                    response = requests.put(url, json=data, timeout=30)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    continue
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 504:
                    logger.warning(f"504 Gateway Timeout for {server_id} on port {local_port}")
                    continue
                else:
                    logger.warning(f"API request failed with status {response.status_code} for {server_id}")
                    continue
                    
            except requests.RequestException as e:
                logger.warning(f"API request failed for {server_id} on port {local_port}: {e}")
                continue
        
        logger.error(f"All API requests failed for server {server_id}")
        return None
    
    def handle_connection_error(self, server_id: str, error: Exception) -> bool:
        """
        Handle connection errors with automatic retry and reconnection.
        
        Args:
            server_id: Server identifier
            error: The error that occurred
            
        Returns:
            True if error was handled and connection restored, False otherwise
        """
        logger.warning(f"Handling connection error for {server_id}: {error}")
        
        # Update health status
        health = self.health_monitor.get_health_status(server_id)
        if health:
            with self.health_monitor.health_lock:
                health.status = ConnectionStatus.RECONNECTING
                health.error_count += 1
                health.last_error = str(error)
        
        # Attempt reconnection
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            logger.info(f"Reconnection attempt {attempt + 1}/{max_retries} for {server_id}")
            
            # Close existing connection
            self.disconnect_from_server(server_id)
            
            # Wait before retry
            time.sleep(retry_delay)
            
            # Attempt reconnection
            if self.connect_to_server(server_id):
                logger.info(f"Successfully reconnected to {server_id}")
                return True
            
            retry_delay *= 2  # Exponential backoff
        
        logger.error(f"Failed to reconnect to {server_id} after {max_retries} attempts")
        return False
    
    def _verify_connection(self, config: ServerConfig) -> bool:
        """Verify that connection to server is working"""
        if not config.local_ports:
            return False
        
        for local_port in config.local_ports:
            try:
                # Try to connect to the local port
                with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                    sock.settimeout(5)
                    result = sock.connect_ex(('localhost', local_port))
                    if result == 0:
                        return True
            except Exception:
                continue
        
        return False
    
    def get_server_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive server status report"""
        report = {
            'timestamp': time.time(),
            'total_servers': len(self.server_configs),
            'servers': {}
        }
        
        connected_count = 0
        error_count = 0
        
        for server_id, config in self.server_configs.items():
            health = self.health_monitor.get_health_status(server_id)
            
            server_report = {
                'config': {
                    'host': config.host,
                    'role': config.role.value,
                    'max_population': config.max_population,
                    'max_concurrent_tasks': config.max_concurrent_tasks,
                    'api_ports': config.api_ports,
                    'local_ports': config.local_ports
                },
                'health': {
                    'status': health.status.value if health else 'unknown',
                    'ssh_tunnel_active': health.ssh_tunnel_active if health else False,
                    'api_accessible': health.api_accessible if health else False,
                    'response_time': health.response_time if health else None,
                    'error_count': health.error_count if health else 0,
                    'last_error': health.last_error if health else None,
                    'last_check': health.last_check if health else 0
                }
            }
            
            if health and health.status == ConnectionStatus.CONNECTED:
                connected_count += 1
            elif health and health.status == ConnectionStatus.ERROR:
                error_count += 1
            
            report['servers'][server_id] = server_report
        
        report['summary'] = {
            'connected': connected_count,
            'errors': error_count,
            'disconnected': len(self.server_configs) - connected_count - error_count
        }
        
        return report

def main():
    """Test the server manager"""
    # Create test configuration
    test_config = {
        "servers": {
            "srv01": {
                "host": "srv01",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 50,
                "max_concurrent_tasks": 5,
                "role": "backtest",
                "ssh_user": "root"
            },
            "srv02": {
                "host": "srv02",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 30,
                "max_concurrent_tasks": 3,
                "role": "mixed",
                "ssh_user": "root"
            },
            "srv03": {
                "host": "srv03",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 20,
                "max_concurrent_tasks": 2,
                "role": "development",
                "ssh_user": "root"
            }
        }
    }
    
    # Save test configuration
    with open('server_config.json', 'w') as f:
        json.dump(test_config, f, indent=2)
    
    # Initialize server manager
    manager = ServerManager('server_config.json')
    
    try:
        # Connect to all servers
        print("Connecting to servers...")
        results = manager.connect_to_all_servers()
        
        for server_id, success in results.items():
            print(f"  {server_id}: {'✓' if success else '✗'}")
        
        # Wait a moment for health monitoring
        time.sleep(5)
        
        # Get status report
        print("\nServer Status Report:")
        report = manager.get_server_status_report()
        print(json.dumps(report, indent=2))
        
        # Test API request (this will likely fail without actual servers)
        print("\nTesting API request...")
        response = manager.execute_api_request("srv01", "/api/test")
        print(f"API response: {response}")
        
    finally:
        # Cleanup
        print("\nDisconnecting from servers...")
        manager.disconnect_from_all_servers()

if __name__ == "__main__":
    main()