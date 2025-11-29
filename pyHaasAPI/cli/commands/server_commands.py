"""
Server command handlers - Direct calls to ServerManager/ServerContentManager
"""

from typing import Any
from ..base import BaseCLI


class ServerCommands:
    """Server command handlers - thin wrappers around ServerManager/ServerContentManager"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle server commands"""
        server_manager = self.cli.server_manager
        server_content_manager = self.cli.server_content_manager
        
        if not server_manager:
            self.cli.logger.error("ServerManager not initialized")
            return 1
        
        try:
            if action == 'list':
                # List available servers
                servers = list(server_manager.servers.keys())
                server_data = [
                    {
                        'server': server,
                        'status': 'connected' if server_manager.servers[server].connected else 'disconnected',
                        'active': server == server_manager.active_server
                    }
                    for server in servers
                ]
                self.cli.format_output(server_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'status':
                # Get server connection status
                if args.server_name:
                    if args.server_name not in server_manager.servers:
                        self.cli.logger.error(f"Server {args.server_name} not found")
                        return 1
                    
                    status = server_manager.servers[args.server_name]
                    status_data = [{
                        'server': args.server_name,
                        'connected': status.connected,
                        'active': args.server_name == server_manager.active_server,
                        'last_error': status.last_error,
                        'reconnect_attempts': status.reconnect_attempts
                    }]
                    self.cli.format_output(status_data, args.output_format, args.output_file)
                else:
                    # Get status for all servers
                    all_status = []
                    for server_name, status in server_manager.servers.items():
                        all_status.append({
                            'server': server_name,
                            'connected': status.connected,
                            'active': server_name == server_manager.active_server,
                            'last_error': status.last_error,
                            'reconnect_attempts': status.reconnect_attempts
                        })
                    self.cli.format_output(all_status, args.output_format, args.output_file)
                return 0
                
            elif action == 'connect':
                # Connect to specific server
                if not args.server_name:
                    self.cli.logger.error("--server-name is required")
                    return 1
                
                # Preflight check
                ok = await server_manager.preflight_check()
                if not ok:
                    self.cli.logger.error("Tunnel preflight failed")
                    return 1
                
                # Set active server
                if args.server_name in server_manager.servers:
                    server_manager.active_server = args.server_name
                    self.cli.logger.info(f"Connected to server {args.server_name}")
                    return 0
                else:
                    self.cli.logger.error(f"Server {args.server_name} not found")
                    return 1
                
            elif action == 'snapshot':
                # Create server snapshot
                if not server_content_manager:
                    self.cli.logger.error("ServerContentManager not initialized")
                    return 1
                
                snapshot = await server_content_manager.snapshot()
                snapshot_data = [{
                    'server': snapshot.server,
                    'timestamp': snapshot.timestamp,
                    'labs_count': len(snapshot.labs),
                    'bots_count': len(snapshot.bots),
                    'labs_without_bots_count': len(snapshot.labs_without_bots),
                    'coins_count': len(snapshot.coins),
                    'coins_without_labs_count': len(snapshot.coins_without_labs)
                }]
                self.cli.format_output(snapshot_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'analyze':
                # Analyze server content (gaps, duplicates)
                if not server_content_manager:
                    self.cli.logger.error("ServerContentManager not initialized")
                    return 1
                
                snapshot = await server_content_manager.snapshot()
                duplicates = server_content_manager.detect_duplicate_bots(snapshot.bots)
                
                analysis_data = [{
                    'server': snapshot.server,
                    'total_labs': len(snapshot.labs),
                    'total_bots': len(snapshot.bots),
                    'labs_without_bots': len(snapshot.labs_without_bots),
                    'duplicate_bots_count': sum(len(v) for v in duplicates.values()),
                    'duplicate_groups': len(duplicates)
                }]
                self.cli.format_output(analysis_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'fetch-backtests':
                # Fetch backtests for labs
                if not server_content_manager:
                    self.cli.logger.error("ServerContentManager not initialized")
                    return 1
                
                if not args.lab_ids:
                    self.cli.logger.error("--lab-ids is required")
                    return 1
                
                lab_ids = [lid.strip() for lid in args.lab_ids.split(',')]
                results = await server_content_manager.fetch_backtests_for_labs(
                    lab_ids=lab_ids,
                    count=args.count or 5,
                    resume=args.resume if hasattr(args, 'resume') else True
                )
                
                results_data = [
                    {'lab_id': lab_id, 'backtests_fetched': count}
                    for lab_id, count in results.items()
                ]
                self.cli.format_output(results_data, args.output_format, args.output_file)
                return 0
                
            else:
                self.cli.logger.error(f"Unknown server action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing server command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

