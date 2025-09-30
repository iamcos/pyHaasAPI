#!/usr/bin/env python3
"""
Bot Analysis and Backtest System

This script provides comprehensive bot analysis including:
- Bot status detection (active/inactive/paused)
- Bot settings verification
- Backtest creation from bots with proper settings
- Short backtest execution (1 day) for validation
- Settings comparison between bot and backtest
"""

import asyncio
import subprocess
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


class BotAnalysisAndBacktestSystem:
    """Comprehensive bot analysis and backtest creation system"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
        self.bot_analysis_results = {}
        self.backtest_results = {}
    
    async def connect_to_server(self, server_name: str) -> bool:
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
                    'bots': [],
                    'bot_status': {},
                    'backtest_results': {}
                }
                print(f"Successfully connected to {server_name}")
                return True
            else:
                print(f"Failed to connect to {server_name}")
                return False
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _establish_ssh_tunnel(self, server_name: str):
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
    
    def analyze_bot_status(self, server_name: str, bot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bot status and settings"""
        try:
            # Extract bot information from HaasBot model data
            bot_id = bot_data.get('bot_id', '') or bot_data.get('BotId', '')
            bot_name = bot_data.get('bot_name', 'Unknown') or bot_data.get('BotName', 'Unknown')
            account_id = bot_data.get('account_id', '') or bot_data.get('AccountId', '')
            market_tag = bot_data.get('market', '') or bot_data.get('MarketTag', '')
            script_id = bot_data.get('script_id', '') or bot_data.get('ScriptId', '')
            
            # Extract status from bot data
            is_activated = bot_data.get('is_activated', False)
            is_paused = bot_data.get('is_paused', False)
            
            # Determine bot status
            if is_activated and not is_paused:
                status = 'active'
            elif is_paused:
                status = 'paused'
            elif not is_activated:
                status = 'inactive'
            else:
                status = 'unknown'
            
            # Extract settings from bot data
            settings_data = bot_data.get('settings', {})
            if isinstance(settings_data, dict):
                settings = {
                    'leverage': settings_data.get('leverage', 0),
                    'position_mode': settings_data.get('position_mode', 0),
                    'margin_mode': settings_data.get('margin_mode', 0),
                    'trade_amount': settings_data.get('trade_amount', 0),
                    'interval': settings_data.get('interval', 0),
                    'chart_style': settings_data.get('chart_style', 0),
                    'order_template': settings_data.get('order_template', 0)
                }
            else:
                # Fallback to direct bot data
                settings = {
                    'leverage': bot_data.get('leverage', 0),
                    'position_mode': bot_data.get('position_mode', 0),
                    'margin_mode': bot_data.get('margin_mode', 0),
                    'trade_amount': bot_data.get('trade_amount', 0),
                    'interval': bot_data.get('interval', 0),
                    'chart_style': bot_data.get('chart_style', 0),
                    'order_template': bot_data.get('order_template', 0)
                }
            
            # Get performance data
            realized_profit = bot_data.get('realized_profit', 0)
            unrealized_profit = bot_data.get('urealized_profit', 0)  # Note: typo in API
            return_on_investment = bot_data.get('return_on_investment', 0)
            
            # Get margin settings for verification
            executor = self.servers[server_name]['executor']
            margin_settings = {}
            try:
                margin_settings = api.get_margin_settings(executor, account_id, market_tag)
            except Exception as e:
                print(f"Could not get margin settings for {bot_id}: {e}")
            
            analysis = {
                'bot_id': bot_id,
                'bot_name': bot_name,
                'account_id': account_id,
                'market_tag': market_tag,
                'script_id': script_id,
                'status': status,
                'is_activated': is_activated,
                'is_paused': is_paused,
                'settings': settings,
                'margin_settings': margin_settings,
                'performance': {
                    'realized_profit': realized_profit,
                    'unrealized_profit': unrealized_profit,
                    'return_on_investment': return_on_investment,
                    'total_profit': realized_profit + unrealized_profit
                },
                'analyzed_at': datetime.now().isoformat(),
                'is_active': status == 'active',
                'is_paused': status == 'paused',
                'is_inactive': status == 'inactive'
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing bot {bot_data.get('bot_id', bot_data.get('BotId', 'unknown'))}: {e}")
            return {
                'bot_id': bot_data.get('bot_id', bot_data.get('BotId', '')),
                'bot_name': bot_data.get('bot_name', bot_data.get('BotName', 'Unknown')),
                'error': str(e),
                'analyzed_at': datetime.now().isoformat()
            }
    
    def create_backtest_from_bot(self, server_name: str, bot_data: Dict[str, Any], duration_days: int = 1) -> Dict[str, Any]:
        """Create a backtest from bot with proper settings verification"""
        try:
            executor = self.servers[server_name]['executor']
            
            # Extract bot information from HaasBot model data
            bot_id = bot_data.get('bot_id', '') or bot_data.get('BotId', '')
            bot_name = bot_data.get('bot_name', 'Unknown') or bot_data.get('BotName', 'Unknown')
            script_id = bot_data.get('script_id', '') or bot_data.get('ScriptId', '')
            market_tag = bot_data.get('market', '') or bot_data.get('MarketTag', '')
            
            if not script_id:
                return {
                    'success': False,
                    'error': 'Bot has no ScriptId',
                    'bot_id': bot_id,
                    'bot_name': bot_name
                }
            
            # Get script record
            from pyHaasAPI.model import GetScriptRecordRequest
            script_request = GetScriptRecordRequest(script_id=script_id)
            script_record = api.get_script_record(executor, script_request)
            
            if not script_record:
                return {
                    'success': False,
                    'error': 'Failed to get script record',
                    'bot_id': bot_id,
                    'bot_name': bot_name
                }
            
            # Build backtest settings from bot data
            settings = api.build_backtest_settings(bot_data, script_record)
            
            # Set time range for short backtest
            end_time = datetime.now()
            start_time = end_time - timedelta(days=duration_days)
            start_unix = int(start_time.timestamp())
            end_unix = int(end_time.timestamp())
            
            # Create backtest request
            from pyHaasAPI.model import ExecuteBacktestRequest
            backtest_id = str(uuid.uuid4())
            
            request = ExecuteBacktestRequest(
                backtest_id=backtest_id,
                script_id=script_id,
                settings=settings,
                start_unix=start_unix,
                end_unix=end_unix
            )
            
            # Execute backtest
            result = api.execute_backtest(executor, request)
            
            if result.get('Success', False):
                return {
                    'success': True,
                    'backtest_id': backtest_id,
                    'bot_id': bot_id,
                    'bot_name': bot_name,
                    'script_id': script_id,
                    'market_tag': market_tag,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_days': duration_days,
                    'settings': settings,
                    'result': result,
                    'created_at': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': result.get('Error', 'Unknown error'),
                    'bot_id': bot_id,
                    'bot_name': bot_name,
                    'result': result
                }
                
        except Exception as e:
            print(f"Error creating backtest for bot {bot_data.get('BotId', 'unknown')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bot_id': bot_data.get('BotId', ''),
                'bot_name': bot_data.get('BotName', 'Unknown')
            }
    
    def verify_backtest_settings(self, bot_data: Dict[str, Any], backtest_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that backtest settings match bot settings"""
        verification = {
            'matches': True,
            'differences': [],
            'bot_settings': {},
            'backtest_settings': {},
            'verified_at': datetime.now().isoformat()
        }
        
        # Extract bot settings
        bot_settings = {
            'leverage': bot_data.get('Leverage', 0),
            'position_mode': bot_data.get('PositionMode', 0),
            'margin_mode': bot_data.get('MarginMode', 0),
            'trade_amount': bot_data.get('TradeAmount', 0),
            'interval': bot_data.get('Interval', 0),
            'chart_style': bot_data.get('ChartStyle', 0),
            'order_template': bot_data.get('OrderTemplate', 0)
        }
        
        # Extract backtest settings
        backtest_extracted = {
            'leverage': backtest_settings.get('leverage', 0),
            'position_mode': backtest_settings.get('positionMode', 0),
            'margin_mode': backtest_settings.get('marginMode', 0),
            'trade_amount': backtest_settings.get('tradeAmount', 0),
            'interval': backtest_settings.get('interval', 0),
            'chart_style': backtest_settings.get('chartStyle', 0),
            'order_template': backtest_settings.get('orderTemplate', 0)
        }
        
        verification['bot_settings'] = bot_settings
        verification['backtest_settings'] = backtest_extracted
        
        # Compare settings
        for key in bot_settings:
            bot_value = bot_settings[key]
            backtest_value = backtest_extracted[key]
            
            if bot_value != backtest_value:
                verification['matches'] = False
                verification['differences'].append({
                    'setting': key,
                    'bot_value': bot_value,
                    'backtest_value': backtest_value,
                    'match': False
                })
            else:
                verification['differences'].append({
                    'setting': key,
                    'bot_value': bot_value,
                    'backtest_value': backtest_value,
                    'match': True
                })
        
        return verification
    
    async def analyze_all_bots(self, server_name: str) -> Dict[str, Any]:
        """Analyze all bots on a server"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Get all bots
            bots = api.get_all_bots(executor)
            self.servers[server_name]['bots'] = bots
            
            analysis_results = {
                'server': server_name,
                'total_bots': len(bots),
                'active_bots': 0,
                'inactive_bots': 0,
                'paused_bots': 0,
                'unknown_status': 0,
                'bot_analysis': [],
                'analyzed_at': datetime.now().isoformat()
            }
            
            for bot in bots:
                # Convert HaasBot Pydantic model to dict
                if hasattr(bot, 'model_dump'):
                    bot_data = bot.model_dump()
                elif isinstance(bot, dict):
                    bot_data = bot
                else:
                    # Extract from HaasBot attributes
                    bot_data = {
                        'BotId': getattr(bot, 'bot_id', ''),
                        'BotName': getattr(bot, 'bot_name', 'Unknown'),
                        'AccountId': getattr(bot, 'account_id', ''),
                        'MarketTag': getattr(bot, 'market', ''),
                        'ScriptId': getattr(bot, 'script_id', ''),
                        'Leverage': getattr(bot, 'leverage', 0),
                        'PositionMode': getattr(bot, 'position_mode', 0),
                        'MarginMode': getattr(bot, 'margin_mode', 0),
                        'TradeAmount': getattr(bot, 'trade_amount', 0),
                        'Interval': getattr(bot, 'interval', 0),
                        'ChartStyle': getattr(bot, 'chart_style', 0),
                        'OrderTemplate': getattr(bot, 'order_template', 0)
                    }
                
                # Analyze bot
                bot_analysis = self.analyze_bot_status(server_name, bot_data)
                analysis_results['bot_analysis'].append(bot_analysis)
                
                # Count by status
                if bot_analysis.get('is_active'):
                    analysis_results['active_bots'] += 1
                elif bot_analysis.get('is_paused'):
                    analysis_results['paused_bots'] += 1
                elif bot_analysis.get('is_inactive'):
                    analysis_results['inactive_bots'] += 1
                else:
                    analysis_results['unknown_status'] += 1
            
            # Store results
            self.bot_analysis_results[server_name] = analysis_results
            
            return analysis_results
            
        except Exception as e:
            print(f"Error analyzing bots on {server_name}: {e}")
            return {'error': str(e)}
    
    async def create_short_backtests(self, server_name: str, max_bots: int = 5) -> Dict[str, Any]:
        """Create short backtests for a limited number of bots"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        try:
            bots = self.servers[server_name]['bots']
            if not bots:
                return {'error': 'No bots available'}
            
            # Select first few bots for testing
            selected_bots = bots[:max_bots]
            
            backtest_results = {
                'server': server_name,
                'total_attempted': len(selected_bots),
                'successful': 0,
                'failed': 0,
                'backtests': [],
                'created_at': datetime.now().isoformat()
            }
            
            for bot in selected_bots:
                # Convert HaasBot Pydantic model to dict
                if hasattr(bot, 'model_dump'):
                    bot_data = bot.model_dump()
                elif isinstance(bot, dict):
                    bot_data = bot
                else:
                    # Extract from HaasBot attributes
                    bot_data = {
                        'bot_id': getattr(bot, 'bot_id', ''),
                        'bot_name': getattr(bot, 'bot_name', 'Unknown'),
                        'account_id': getattr(bot, 'account_id', ''),
                        'market': getattr(bot, 'market', ''),
                        'script_id': getattr(bot, 'script_id', ''),
                        'leverage': getattr(bot, 'leverage', 0),
                        'position_mode': getattr(bot, 'position_mode', 0),
                        'margin_mode': getattr(bot, 'margin_mode', 0),
                        'trade_amount': getattr(bot, 'trade_amount', 0),
                        'interval': getattr(bot, 'interval', 0),
                        'chart_style': getattr(bot, 'chart_style', 0),
                        'order_template': getattr(bot, 'order_template', 0)
                    }
                
                # Create backtest
                backtest_result = self.create_backtest_from_bot(server_name, bot_data, duration_days=1)
                backtest_results['backtests'].append(backtest_result)
                
                if backtest_result.get('success'):
                    backtest_results['successful'] += 1
                    
                    # Verify settings
                    if 'settings' in backtest_result:
                        verification = self.verify_backtest_settings(bot_data, backtest_result['settings'])
                        backtest_result['settings_verification'] = verification
                else:
                    backtest_results['failed'] += 1
            
            # Store results
            self.backtest_results[server_name] = backtest_results
            
            return backtest_results
            
        except Exception as e:
            print(f"Error creating backtests on {server_name}: {e}")
            return {'error': str(e)}
    
    def generate_comprehensive_report(self, server_name: str) -> Dict[str, Any]:
        """Generate comprehensive report for a server"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        report = {
            'server': server_name,
            'generated_at': datetime.now().isoformat(),
            'bot_analysis': self.bot_analysis_results.get(server_name, {}),
            'backtest_results': self.backtest_results.get(server_name, {}),
            'summary': {
                'total_bots': 0,
                'active_bots': 0,
                'inactive_bots': 0,
                'paused_bots': 0,
                'backtests_created': 0,
                'backtests_successful': 0,
                'backtests_failed': 0
            }
        }
        
        # Add bot analysis summary
        if 'bot_analysis' in report and report['bot_analysis']:
            bot_analysis = report['bot_analysis']
            report['summary']['total_bots'] = bot_analysis.get('total_bots', 0)
            report['summary']['active_bots'] = bot_analysis.get('active_bots', 0)
            report['summary']['inactive_bots'] = bot_analysis.get('inactive_bots', 0)
            report['summary']['paused_bots'] = bot_analysis.get('paused_bots', 0)
        
        # Add backtest summary
        if 'backtest_results' in report and report['backtest_results']:
            backtest_results = report['backtest_results']
            report['summary']['backtests_created'] = backtest_results.get('total_attempted', 0)
            report['summary']['backtests_successful'] = backtest_results.get('successful', 0)
            report['summary']['backtests_failed'] = backtest_results.get('failed', 0)
        
        return report
    
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


async def test_bot_analysis_and_backtest_system():
    """Test the bot analysis and backtest system"""
    print("Testing Bot Analysis and Backtest System")
    print("=" * 60)
    
    system = BotAnalysisAndBacktestSystem()
    
    try:
        # Connect to srv01
        print("Connecting to srv01...")
        if not await system.connect_to_server("srv01"):
            print("Failed to connect to srv01")
            return 1
        
        # Analyze all bots
        print("\nAnalyzing all bots...")
        bot_analysis = await system.analyze_all_bots("srv01")
        if 'error' in bot_analysis:
            print(f"Error analyzing bots: {bot_analysis['error']}")
            return 1
        
        print(f"Bot Analysis Results:")
        print(f"  Total bots: {bot_analysis['total_bots']}")
        print(f"  Active bots: {bot_analysis['active_bots']}")
        print(f"  Inactive bots: {bot_analysis['inactive_bots']}")
        print(f"  Paused bots: {bot_analysis['paused_bots']}")
        print(f"  Unknown status: {bot_analysis['unknown_status']}")
        
        # Show first few bot details
        print("\nFirst 5 bot details:")
        for i, bot in enumerate(bot_analysis['bot_analysis'][:5]):
            print(f"  {i+1}. {bot.get('bot_name', 'Unknown')} - Status: {bot.get('status', 'unknown')}")
            if 'settings' in bot:
                settings = bot['settings']
                print(f"     Leverage: {settings.get('leverage', 0)}, Trade Amount: {settings.get('trade_amount', 0)}")
        
        # Create short backtests for first 3 bots
        print("\nCreating short backtests (1 day) for first 3 bots...")
        backtest_results = await system.create_short_backtests("srv01", max_bots=3)
        if 'error' in backtest_results:
            print(f"Error creating backtests: {backtest_results['error']}")
            return 1
        
        print(f"Backtest Results:")
        print(f"  Total attempted: {backtest_results['total_attempted']}")
        print(f"  Successful: {backtest_results['successful']}")
        print(f"  Failed: {backtest_results['failed']}")
        
        # Show backtest details
        for i, backtest in enumerate(backtest_results['backtests']):
            print(f"\nBacktest {i+1}:")
            print(f"  Bot: {backtest.get('bot_name', 'Unknown')}")
            print(f"  Success: {backtest.get('success', False)}")
            if backtest.get('success'):
                print(f"  Backtest ID: {backtest.get('backtest_id', 'N/A')}")
                print(f"  Duration: {backtest.get('duration_days', 0)} days")
                if 'settings_verification' in backtest:
                    verification = backtest['settings_verification']
                    print(f"  Settings match: {verification.get('matches', False)}")
                    if not verification.get('matches'):
                        print(f"  Differences: {len(verification.get('differences', []))}")
            else:
                print(f"  Error: {backtest.get('error', 'Unknown error')}")
        
        # Generate comprehensive report
        print("\nGenerating comprehensive report...")
        report = system.generate_comprehensive_report("srv01")
        print(f"Comprehensive Report:")
        print(f"  Server: {report['server']}")
        print(f"  Total bots: {report['summary']['total_bots']}")
        print(f"  Active bots: {report['summary']['active_bots']}")
        print(f"  Backtests created: {report['summary']['backtests_created']}")
        print(f"  Backtests successful: {report['summary']['backtests_successful']}")
        
        print("\nBot analysis and backtest system test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await system.cleanup_all()


async def main():
    """Main entry point"""
    return await test_bot_analysis_and_backtest_system()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
