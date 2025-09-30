#!/usr/bin/env python3
"""
Advanced Data Manager

This script implements advanced features including:
- Lab creation and management
- Bot performance monitoring
- Automated decision making
- Portfolio management across servers
- Real-time performance tracking
"""

import asyncio
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


class AdvancedDataManager:
    """Advanced data manager with lab creation and bot monitoring"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
        self.performance_history = {}
        self.bot_monitoring = {}
        self.lab_management = {}
    
    async def connect_to_server(self, server_name):
        """Connect to a specific server"""
        try:
            # Establish SSH tunnel
            ssh_process = await self._establish_ssh_tunnel(server_name)
            if not ssh_process:
                return False
            
            self.ssh_processes[server_name] = ssh_process
            
            # Get credentials
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                print("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Initialize analyzer and connect
            cache = UnifiedCacheManager()
            analyzer = HaasAnalyzer(cache)
            success = analyzer.connect(
                host='127.0.0.1',
                port=8090,
                email=email,
                password=password
            )
            
            if success:
                self.servers[server_name] = {
                    'analyzer': analyzer,
                    'executor': analyzer.executor,
                    'cache': cache,
                    'labs': [],
                    'bots': [],
                    'accounts': [],
                    'backtests': {},
                    'performance_data': {},
                    'last_update': None
                }
                print(f"Successfully connected to {server_name}")
                return True
            else:
                print(f"Failed to connect to {server_name}")
                return False
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _establish_ssh_tunnel(self, server_name):
        """Establish SSH tunnel to server"""
        try:
            print(f"Connecting to {server_name}...")
            
            ssh_cmd = [
                "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
                f"prod@{server_name}"
            ]
            
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            await asyncio.sleep(5)
            
            if process.poll() is None:
                print(f"SSH tunnel established to {server_name} (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"SSH tunnel failed for {server_name}: {stderr.decode()}")
                return None
                
        except Exception as e:
            print(f"Failed to establish SSH tunnel to {server_name}: {e}")
            return None
    
    async def create_lab(self, server_name: str, lab_config: Dict[str, Any]) -> Optional[str]:
        """Create a new lab on specified server"""
        if server_name not in self.servers:
            print(f"No connection to {server_name}")
            return None
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Create lab using API
            lab_id = api.create_lab(executor, lab_config)
            
            if lab_id:
                print(f"Created lab {lab_id} on {server_name}")
                
                # Update server data
                self.servers[server_name]['labs'].append({
                    'lab_id': lab_id,
                    'config': lab_config,
                    'created_at': datetime.now(),
                    'status': 'created'
                })
                
                return lab_id
            else:
                print(f"Failed to create lab on {server_name}")
                return None
                
        except Exception as e:
            print(f"Error creating lab on {server_name}: {e}")
            return None
    
    async def monitor_bot_performance(self, server_name: str, bot_id: str) -> Dict[str, Any]:
        """Monitor performance of a specific bot"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Get bot details
            bot_details = api.get_bot(executor, bot_id)
            if not bot_details:
                return {'error': 'Bot not found'}
            
            # Get bot runtime data
            runtime_data = api.get_full_bot_runtime_data(executor, bot_id)
            
            # Extract performance metrics - handle both dict and object types
            if hasattr(bot_details, 'bot_name'):
                bot_name = bot_details.bot_name
            elif isinstance(bot_details, dict):
                bot_name = bot_details.get('bot_name', 'Unknown')
            else:
                bot_name = 'Unknown'
            
            # Extract other attributes safely
            status = getattr(bot_details, 'status', None) or (bot_details.get('status') if isinstance(bot_details, dict) else 'unknown')
            account_id = getattr(bot_details, 'account_id', None) or (bot_details.get('account_id') if isinstance(bot_details, dict) else 'unknown')
            market = getattr(bot_details, 'market', None) or (bot_details.get('market') if isinstance(bot_details, dict) else 'unknown')
            leverage = getattr(bot_details, 'leverage', None) or (bot_details.get('leverage') if isinstance(bot_details, dict) else 0)
            trade_amount = getattr(bot_details, 'trade_amount', None) or (bot_details.get('trade_amount') if isinstance(bot_details, dict) else 0)
            
            # Extract PnL from runtime data
            realized_pnl = 0
            unrealized_pnl = 0
            if runtime_data:
                if isinstance(runtime_data, dict):
                    realized_pnl = runtime_data.get('realized_pnl', 0)
                    unrealized_pnl = runtime_data.get('unrealized_pnl', 0)
                else:
                    realized_pnl = getattr(runtime_data, 'realized_pnl', 0)
                    unrealized_pnl = getattr(runtime_data, 'unrealized_pnl', 0)
            
            # Extract performance metrics
            performance = {
                'bot_id': bot_id,
                'bot_name': bot_name,
                'status': status,
                'account_id': account_id,
                'market': market,
                'leverage': leverage,
                'trade_amount': trade_amount,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'total_pnl': realized_pnl + unrealized_pnl,
                'monitored_at': datetime.now().isoformat(),
                'runtime_data': runtime_data
            }
            
            # Store in monitoring data
            if server_name not in self.bot_monitoring:
                self.bot_monitoring[server_name] = {}
            
            self.bot_monitoring[server_name][bot_id] = performance
            
            return performance
            
        except Exception as e:
            print(f"Error monitoring bot {bot_id} on {server_name}: {e}")
            return {'error': str(e)}
    
    async def analyze_portfolio_performance(self, server_name: str) -> Dict[str, Any]:
        """Analyze portfolio performance across all bots on a server"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        try:
            executor = self.servers[server_name]['executor']
            bots = self.servers[server_name]['bots']
            
            portfolio_analysis = {
                'server': server_name,
                'total_bots': len(bots),
                'active_bots': 0,
                'inactive_bots': 0,
                'total_pnl': 0.0,
                'winning_bots': 0,
                'losing_bots': 0,
                'bot_performance': []
            }
            
            for bot in bots:
                try:
                    # Extract bot_id safely
                    if hasattr(bot, 'bot_id'):
                        bot_id = bot.bot_id
                    elif isinstance(bot, dict):
                        bot_id = bot.get('bot_id')
                    else:
                        bot_id = str(bot)
                    
                    if not bot_id:
                        continue
                    
                    performance = await self.monitor_bot_performance(server_name, bot_id)
                    
                    if 'error' not in performance:
                        portfolio_analysis['bot_performance'].append(performance)
                        
                        # Count active/inactive
                        if performance.get('status') == 'active':
                            portfolio_analysis['active_bots'] += 1
                        else:
                            portfolio_analysis['inactive_bots'] += 1
                        
                        # Analyze PnL from performance data
                        total_pnl = performance.get('total_pnl', 0)
                        portfolio_analysis['total_pnl'] += total_pnl
                        
                        if total_pnl > 0:
                            portfolio_analysis['winning_bots'] += 1
                        elif total_pnl < 0:
                            portfolio_analysis['losing_bots'] += 1
                
                except Exception as e:
                    print(f"Error analyzing bot {getattr(bot, 'bot_id', 'unknown')}: {e}")
                    continue
            
            # Store analysis
            self.performance_history[server_name] = {
                'analysis': portfolio_analysis,
                'timestamp': datetime.now()
            }
            
            return portfolio_analysis
            
        except Exception as e:
            print(f"Error analyzing portfolio on {server_name}: {e}")
            return {'error': str(e)}
    
    async def make_automated_decisions(self, server_name: str) -> List[Dict[str, Any]]:
        """Make automated decisions based on bot performance"""
        if server_name not in self.servers:
            return []
        
        decisions = []
        
        try:
            # Get portfolio analysis
            portfolio = await self.analyze_portfolio_performance(server_name)
            
            if 'error' in portfolio:
                return decisions
            
            # Decision logic based on performance
            for bot_perf in portfolio['bot_performance']:
                bot_id = bot_perf['bot_id']
                bot_name = bot_perf['bot_name']
                status = bot_perf['status']
                total_pnl = bot_perf.get('total_pnl', 0)
                
                # Decision 1: Deactivate underperforming bots
                if total_pnl < -1000:  # Loss threshold
                    decisions.append({
                        'action': 'deactivate',
                        'bot_id': bot_id,
                        'bot_name': bot_name,
                        'reason': f'Underperforming: ${total_pnl:.2f} PnL',
                        'priority': 'high'
                    })
                
                # Decision 2: Activate profitable bots
                if status == 'inactive' and total_pnl > 500:  # Profit threshold
                    decisions.append({
                        'action': 'activate',
                        'bot_id': bot_id,
                        'bot_name': bot_name,
                        'reason': f'Profitable: ${total_pnl:.2f} PnL',
                        'priority': 'medium'
                    })
            
            # Store decisions
            if server_name not in self.lab_management:
                self.lab_management[server_name] = {}
            
            self.lab_management[server_name]['decisions'] = decisions
            
            return decisions
            
        except Exception as e:
            print(f"Error making automated decisions for {server_name}: {e}")
            return []
    
    async def execute_decisions(self, server_name: str, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute automated decisions"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        results = {
            'executed': 0,
            'failed': 0,
            'actions': []
        }
        
        try:
            executor = self.servers[server_name]['executor']
            
            for decision in decisions:
                action = decision['action']
                bot_id = decision['bot_id']
                bot_name = decision['bot_name']
                
                try:
                    if action == 'deactivate':
                        api.deactivate_bot(executor, bot_id)
                        results['actions'].append(f"Deactivated {bot_name}")
                        results['executed'] += 1
                        
                    elif action == 'activate':
                        api.activate_bot(executor, bot_id)
                        results['actions'].append(f"Activated {bot_name}")
                        results['executed'] += 1
                    
                    print(f"Executed: {action} for {bot_name}")
                    
                except Exception as e:
                    print(f"Failed to execute {action} for {bot_name}: {e}")
                    results['failed'] += 1
                    results['actions'].append(f"Failed: {action} for {bot_name}")
            
            return results
            
        except Exception as e:
            print(f"Error executing decisions for {server_name}: {e}")
            return {'error': str(e)}
    
    def get_advanced_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all advanced features"""
        summary = {
            'servers': {},
            'total_decisions': 0,
            'total_bots_monitored': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        for server_name, server_data in self.servers.items():
            server_summary = {
                'labs': len(server_data['labs']),
                'bots': len(server_data['bots']),
                'accounts': len(server_data['accounts']),
                'backtests': sum(len(bt) for bt in server_data['backtests'].values()),
                'last_update': server_data['last_update'].isoformat() if server_data['last_update'] else None
            }
            
            # Add performance data
            if server_name in self.performance_history:
                server_summary['portfolio_analysis'] = self.performance_history[server_name]['analysis']
            
            # Add decisions
            if server_name in self.lab_management and 'decisions' in self.lab_management[server_name]:
                decisions = self.lab_management[server_name]['decisions']
                server_summary['decisions'] = len(decisions)
                summary['total_decisions'] += len(decisions)
            
            # Add bot monitoring
            if server_name in self.bot_monitoring:
                monitored_bots = len(self.bot_monitoring[server_name])
                server_summary['monitored_bots'] = monitored_bots
                summary['total_bots_monitored'] += monitored_bots
            
            summary['servers'][server_name] = server_summary
        
        return summary
    
    async def create_advanced_lab(self, server_name: str, lab_config: Dict[str, Any]) -> Optional[str]:
        """Create an advanced lab with optimization settings"""
        if server_name not in self.servers:
            print(f"No connection to {server_name}")
            return None
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Enhanced lab configuration
            enhanced_config = {
                **lab_config,
                'optimization_enabled': True,
                'max_generations': lab_config.get('max_generations', 50),
                'population_size': lab_config.get('population_size', 100),
                'mutation_rate': lab_config.get('mutation_rate', 0.1),
                'crossover_rate': lab_config.get('crossover_rate', 0.8),
                'elite_size': lab_config.get('elite_size', 10)
            }
            
            # Create lab using API
            lab_id = api.create_lab(executor, enhanced_config)
            
            if lab_id:
                print(f"Created advanced lab {lab_id} on {server_name}")
                
                # Update server data
                self.servers[server_name]['labs'].append({
                    'lab_id': lab_id,
                    'config': enhanced_config,
                    'created_at': datetime.now(),
                    'status': 'created',
                    'type': 'advanced'
                })
                
                return lab_id
            else:
                print(f"Failed to create advanced lab on {server_name}")
                return None
                
        except Exception as e:
            print(f"Error creating advanced lab on {server_name}: {e}")
            return None
    
    async def monitor_lab_progress(self, server_name: str, lab_id: str) -> Dict[str, Any]:
        """Monitor lab execution progress"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Get lab execution status
            execution_status = api.get_lab_execution_update(executor, lab_id)
            
            # Get lab details
            lab_details = api.get_lab_details(executor, lab_id)
            
            progress_info = {
                'lab_id': lab_id,
                'status': execution_status.get('status', 'unknown'),
                'progress': execution_status.get('progress', 0),
                'generation': execution_status.get('generation', 0),
                'population': execution_status.get('population', 0),
                'best_fitness': execution_status.get('best_fitness', 0),
                'monitored_at': datetime.now().isoformat(),
                'lab_details': lab_details
            }
            
            return progress_info
            
        except Exception as e:
            print(f"Error monitoring lab {lab_id} on {server_name}: {e}")
            return {'error': str(e)}
    
    async def analyze_multi_server_performance(self) -> Dict[str, Any]:
        """Analyze performance across all connected servers"""
        multi_server_analysis = {
            'total_servers': len(self.servers),
            'total_labs': 0,
            'total_bots': 0,
            'total_accounts': 0,
            'total_pnl': 0.0,
            'server_performance': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for server_name, server_data in self.servers.items():
            # Get server-specific data
            labs_count = len(server_data['labs'])
            bots_count = len(server_data['bots'])
            accounts_count = len(server_data['accounts'])
            
            multi_server_analysis['total_labs'] += labs_count
            multi_server_analysis['total_bots'] += bots_count
            multi_server_analysis['total_accounts'] += accounts_count
            
            # Get portfolio analysis for this server
            portfolio = await self.analyze_portfolio_performance(server_name)
            if 'error' not in portfolio:
                server_pnl = portfolio.get('total_pnl', 0)
                multi_server_analysis['total_pnl'] += server_pnl
                
                multi_server_analysis['server_performance'][server_name] = {
                    'labs': labs_count,
                    'bots': bots_count,
                    'accounts': accounts_count,
                    'total_pnl': server_pnl,
                    'active_bots': portfolio.get('active_bots', 0),
                    'winning_bots': portfolio.get('winning_bots', 0),
                    'losing_bots': portfolio.get('losing_bots', 0)
                }
        
        return multi_server_analysis
    
    async def execute_risk_management(self, server_name: str) -> Dict[str, Any]:
        """Execute risk management rules across all bots"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        risk_actions = {
            'deactivated_bots': [],
            'paused_bots': [],
            'leverage_adjusted': [],
            'trade_amount_adjusted': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            executor = self.servers[server_name]['executor']
            bots = self.servers[server_name]['bots']
            
            for bot in bots:
                try:
                    bot_id = getattr(bot, 'bot_id', None) or (bot.get('bot_id') if isinstance(bot, dict) else None)
                    if not bot_id:
                        continue
                    
                    # Get bot performance
                    performance = await self.monitor_bot_performance(server_name, bot_id)
                    if 'error' in performance:
                        continue
                    
                    total_pnl = performance.get('total_pnl', 0)
                    leverage = performance.get('leverage', 0)
                    trade_amount = performance.get('trade_amount', 0)
                    
                    # Risk management rules
                    if total_pnl < -2000:  # High loss threshold
                        # Deactivate bot
                        api.deactivate_bot(executor, bot_id)
                        risk_actions['deactivated_bots'].append({
                            'bot_id': bot_id,
                            'bot_name': performance.get('bot_name', 'Unknown'),
                            'reason': f'High loss: ${total_pnl:.2f}',
                            'action': 'deactivated'
                        })
                    
                    elif total_pnl < -1000:  # Medium loss threshold
                        # Pause bot
                        api.pause_bot(executor, bot_id)
                        risk_actions['paused_bots'].append({
                            'bot_id': bot_id,
                            'bot_name': performance.get('bot_name', 'Unknown'),
                            'reason': f'Medium loss: ${total_pnl:.2f}',
                            'action': 'paused'
                        })
                    
                    # Leverage adjustment for high-risk bots
                    if leverage > 50 and total_pnl < -500:
                        # Reduce leverage
                        new_leverage = min(leverage * 0.5, 20)
                        api.edit_bot_parameter(executor, bot_id, {'leverage': new_leverage})
                        risk_actions['leverage_adjusted'].append({
                            'bot_id': bot_id,
                            'bot_name': performance.get('bot_name', 'Unknown'),
                            'old_leverage': leverage,
                            'new_leverage': new_leverage,
                            'reason': 'High risk reduction'
                        })
                    
                    # Trade amount adjustment for underperforming bots
                    if total_pnl < -300 and trade_amount > 1000:
                        # Reduce trade amount
                        new_trade_amount = max(trade_amount * 0.7, 500)
                        api.edit_bot_parameter(executor, bot_id, {'trade_amount': new_trade_amount})
                        risk_actions['trade_amount_adjusted'].append({
                            'bot_id': bot_id,
                            'bot_name': performance.get('bot_name', 'Unknown'),
                            'old_amount': trade_amount,
                            'new_amount': new_trade_amount,
                            'reason': 'Risk reduction'
                        })
                
                except Exception as e:
                    print(f"Error applying risk management to bot {getattr(bot, 'bot_id', 'unknown')}: {e}")
                    continue
            
            return risk_actions
            
        except Exception as e:
            print(f"Error executing risk management for {server_name}: {e}")
            return {'error': str(e)}
    
    async def cleanup_all(self):
        """Clean up all SSH tunnels"""
        for server_name, process in self.ssh_processes.items():
            print(f"Cleaning up {server_name}...")
            try:
                if process and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                print(f"Error cleaning up {server_name}: {e}")


async def test_advanced_data_manager():
    """Test the advanced data manager"""
    print("Testing Advanced Data Manager")
    print("=" * 60)
    
    data_manager = AdvancedDataManager()
    
    try:
        # Connect to srv01
        print("Connecting to srv01...")
        if not await data_manager.connect_to_server("srv01"):
            print("Failed to connect to srv01")
            return 1
        
        # Fetch initial data
        print("\nFetching initial data...")
        executor = data_manager.servers["srv01"]['executor']
        
        # Get labs, bots, accounts
        labs = api.get_all_labs(executor)
        bots = api.get_all_bots(executor)
        accounts = api.get_all_accounts(executor)
        
        data_manager.servers["srv01"]['labs'] = labs
        data_manager.servers["srv01"]['bots'] = bots
        data_manager.servers["srv01"]['accounts'] = accounts
        
        print(f"Fetched {len(labs)} labs, {len(bots)} bots, {len(accounts)} accounts")
        
        # Test bot performance monitoring
        print("\nTesting bot performance monitoring...")
        if bots:
            first_bot = bots[0]
            performance = await data_manager.monitor_bot_performance("srv01", first_bot.bot_id)
            print(f"Bot performance: {performance.get('bot_name', 'Unknown')} - {performance.get('status', 'Unknown')}")
        
        # Test portfolio analysis
        print("\nTesting portfolio analysis...")
        portfolio = await data_manager.analyze_portfolio_performance("srv01")
        print(f"Portfolio: {portfolio.get('total_bots', 0)} bots, {portfolio.get('active_bots', 0)} active")
        
        # Test automated decisions
        print("\nTesting automated decisions...")
        decisions = await data_manager.make_automated_decisions("srv01")
        print(f"Generated {len(decisions)} decisions")
        
        for decision in decisions[:3]:  # Show first 3 decisions
            print(f"  - {decision['action']} {decision['bot_name']}: {decision['reason']}")
        
        # Test risk management
        print("\nTesting risk management...")
        risk_actions = await data_manager.execute_risk_management("srv01")
        if 'error' not in risk_actions:
            print(f"Risk management executed:")
            print(f"  Deactivated bots: {len(risk_actions['deactivated_bots'])}")
            print(f"  Paused bots: {len(risk_actions['paused_bots'])}")
            print(f"  Leverage adjustments: {len(risk_actions['leverage_adjusted'])}")
            print(f"  Trade amount adjustments: {len(risk_actions['trade_amount_adjusted'])}")
        
        # Test multi-server analysis
        print("\nTesting multi-server analysis...")
        multi_analysis = await data_manager.analyze_multi_server_performance()
        print(f"Multi-server analysis:")
        print(f"  Total servers: {multi_analysis['total_servers']}")
        print(f"  Total labs: {multi_analysis['total_labs']}")
        print(f"  Total bots: {multi_analysis['total_bots']}")
        print(f"  Total PnL: ${multi_analysis['total_pnl']:.2f}")
        
        # Test lab monitoring (if we have labs)
        if labs:
            print("\nTesting lab monitoring...")
            first_lab = labs[0]
            lab_id = getattr(first_lab, 'lab_id', None) or (first_lab.get('lab_id') if isinstance(first_lab, dict) else None)
            if lab_id:
                lab_progress = await data_manager.monitor_lab_progress("srv01", lab_id)
                if 'error' not in lab_progress:
                    print(f"Lab {lab_id} status: {lab_progress.get('status', 'unknown')}")
                    print(f"  Progress: {lab_progress.get('progress', 0)}%")
                    print(f"  Generation: {lab_progress.get('generation', 0)}")
        
        # Show advanced summary
        print("\nAdvanced Summary:")
        summary = data_manager.get_advanced_summary()
        print(f"  Total decisions: {summary['total_decisions']}")
        print(f"  Total bots monitored: {summary['total_bots_monitored']}")
        print(f"  Servers: {list(summary['servers'].keys())}")
        
        print("\nAdvanced data manager test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await data_manager.cleanup_all()


async def main():
    """Main entry point"""
    return await test_advanced_data_manager()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
