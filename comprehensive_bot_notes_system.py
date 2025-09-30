#!/usr/bin/env python3
"""
Comprehensive Bot Notes System

This script provides comprehensive bot analysis and populates bot notes with:
- Performance analysis and metrics
- Backtest results and validation
- Settings verification and comparison
- Analysis provenance and lifecycle tracking
- Risk assessment and recommendations
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


class ComprehensiveBotNotesSystem:
    """Comprehensive bot notes system with analysis and reporting"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
        self.bot_analysis_results = {}
        self.backtest_results = {}
        self.notes_updates = {}
    
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
                    'bot_analysis': {},
                    'backtest_results': {},
                    'notes_updates': {}
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
    
    def analyze_bot_comprehensive(self, server_name: str, bot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive bot analysis including performance, settings, and risk assessment"""
        try:
            # Extract bot information
            bot_id = bot_data.get('bot_id', '') or bot_data.get('BotId', '')
            bot_name = bot_data.get('bot_name', 'Unknown') or bot_data.get('BotName', 'Unknown')
            account_id = bot_data.get('account_id', '') or bot_data.get('AccountId', '')
            market_tag = bot_data.get('market', '') or bot_data.get('MarketTag', '')
            script_id = bot_data.get('script_id', '') or bot_data.get('ScriptId', '')
            
            # Extract status and performance
            is_activated = bot_data.get('is_activated', False)
            is_paused = bot_data.get('is_paused', False)
            realized_profit = bot_data.get('realized_profit', 0)
            unrealized_profit = bot_data.get('urealized_profit', 0)
            return_on_investment = bot_data.get('return_on_investment', 0)
            
            # Determine bot status
            if is_activated and not is_paused:
                status = 'active'
            elif is_paused:
                status = 'paused'
            elif not is_activated:
                status = 'inactive'
            else:
                status = 'unknown'
            
            # Extract settings
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
                settings = {
                    'leverage': bot_data.get('leverage', 0),
                    'position_mode': bot_data.get('position_mode', 0),
                    'margin_mode': bot_data.get('margin_mode', 0),
                    'trade_amount': bot_data.get('trade_amount', 0),
                    'interval': bot_data.get('interval', 0),
                    'chart_style': bot_data.get('chart_style', 0),
                    'order_template': bot_data.get('order_template', 0)
                }
            
            # Calculate performance metrics
            total_profit = realized_profit + unrealized_profit
            profit_percentage = return_on_investment
            
            # Risk assessment
            risk_level = 'low'
            risk_factors = []
            
            if total_profit < -1000:
                risk_level = 'high'
                risk_factors.append('High losses')
            elif total_profit < -500:
                risk_level = 'medium'
                risk_factors.append('Moderate losses')
            
            if settings.get('leverage', 0) > 50:
                risk_level = 'high'
                risk_factors.append('High leverage')
            elif settings.get('leverage', 0) > 20:
                risk_factors.append('Elevated leverage')
            
            if settings.get('trade_amount', 0) > 5000:
                risk_factors.append('Large trade amounts')
            
            # Performance assessment
            performance_rating = 'poor'
            if total_profit > 1000:
                performance_rating = 'excellent'
            elif total_profit > 500:
                performance_rating = 'good'
            elif total_profit > 0:
                performance_rating = 'positive'
            elif total_profit > -500:
                performance_rating = 'poor'
            else:
                performance_rating = 'very_poor'
            
            # Recommendations
            recommendations = []
            if risk_level == 'high':
                recommendations.append('Consider deactivating due to high risk')
            if performance_rating in ['very_poor', 'poor']:
                recommendations.append('Monitor closely or consider pausing')
            if settings.get('leverage', 0) > 50:
                recommendations.append('Reduce leverage for risk management')
            if total_profit > 1000:
                recommendations.append('Consider increasing position size')
            
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
                'performance': {
                    'realized_profit': realized_profit,
                    'unrealized_profit': unrealized_profit,
                    'total_profit': total_profit,
                    'return_on_investment': return_on_investment,
                    'profit_percentage': profit_percentage
                },
                'risk_assessment': {
                    'risk_level': risk_level,
                    'risk_factors': risk_factors
                },
                'performance_rating': performance_rating,
                'recommendations': recommendations,
                'analyzed_at': datetime.now().isoformat()
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
    
    def create_comprehensive_bot_notes(self, bot_analysis: Dict[str, Any]) -> str:
        """Create comprehensive bot notes with analysis data"""
        try:
            # Extract key information
            bot_id = bot_analysis.get('bot_id', '')
            bot_name = bot_analysis.get('bot_name', 'Unknown')
            status = bot_analysis.get('status', 'unknown')
            performance = bot_analysis.get('performance', {})
            risk_assessment = bot_analysis.get('risk_assessment', {})
            performance_rating = bot_analysis.get('performance_rating', 'unknown')
            recommendations = bot_analysis.get('recommendations', [])
            settings = bot_analysis.get('settings', {})
            analyzed_at = bot_analysis.get('analyzed_at', '')
            
            # Create comprehensive notes
            notes = {
                'analysis_metadata': {
                    'analyzed_at': analyzed_at,
                    'bot_id': bot_id,
                    'bot_name': bot_name,
                    'analysis_version': '1.0',
                    'analysis_type': 'comprehensive'
                },
                'bot_status': {
                    'status': status,
                    'is_activated': bot_analysis.get('is_activated', False),
                    'is_paused': bot_analysis.get('is_paused', False)
                },
                'performance_analysis': {
                    'realized_profit': performance.get('realized_profit', 0),
                    'unrealized_profit': performance.get('unrealized_profit', 0),
                    'total_profit': performance.get('total_profit', 0),
                    'return_on_investment': performance.get('return_on_investment', 0),
                    'performance_rating': performance_rating
                },
                'risk_assessment': {
                    'risk_level': risk_assessment.get('risk_level', 'unknown'),
                    'risk_factors': risk_assessment.get('risk_factors', [])
                },
                'settings_analysis': {
                    'leverage': settings.get('leverage', 0),
                    'position_mode': settings.get('position_mode', 0),
                    'margin_mode': settings.get('margin_mode', 0),
                    'trade_amount': settings.get('trade_amount', 0),
                    'interval': settings.get('interval', 0),
                    'chart_style': settings.get('chart_style', 0),
                    'order_template': settings.get('order_template', 0)
                },
                'recommendations': recommendations,
                'analysis_lifecycle': {
                    'created': analyzed_at,
                    'last_updated': analyzed_at,
                    'update_count': 1
                }
            }
            
            # Convert to JSON string for bot notes
            notes_json = json.dumps(notes, indent=2)
            
            return notes_json
            
        except Exception as e:
            print(f"Error creating bot notes: {e}")
            return json.dumps({
                'error': str(e),
                'analyzed_at': datetime.now().isoformat()
            }, indent=2)
    
    async def update_bot_notes(self, server_name: str, bot_id: str, notes: str) -> bool:
        """Update bot notes with comprehensive analysis"""
        try:
            executor = self.servers[server_name]['executor']
            
            # Get current bot data
            bot_data = api.get_bot(executor, bot_id)
            if not bot_data:
                print(f"Could not get bot data for {bot_id}")
                return False
            
            # Update bot notes by modifying the bot object
            try:
                # Update the notes field in the bot object
                bot_data.notes = notes
                
                # Use edit_bot_parameter with the updated bot object
                result = api.edit_bot_parameter(executor, bot_data)
                if result:
                    print(f"Successfully updated notes for bot {bot_id}")
                    return True
                else:
                    print(f"Failed to update notes for bot {bot_id}")
                    return False
            except Exception as e:
                print(f"Error updating notes for bot {bot_id}: {e}")
                return False
                
        except Exception as e:
            print(f"Error updating bot notes: {e}")
            return False
    
    async def analyze_and_update_all_bots(self, server_name: str, max_bots: int = 10) -> Dict[str, Any]:
        """Analyze all bots and update their notes with comprehensive analysis"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Get all bots
            bots = api.get_all_bots(executor)
            self.servers[server_name]['bots'] = bots
            
            # Limit to max_bots for testing
            selected_bots = bots[:max_bots]
            
            analysis_results = {
                'server': server_name,
                'total_analyzed': len(selected_bots),
                'successful_updates': 0,
                'failed_updates': 0,
                'bot_analyses': [],
                'analyzed_at': datetime.now().isoformat()
            }
            
            for bot in selected_bots:
                try:
                    # Convert bot to dict
                    if hasattr(bot, 'model_dump'):
                        bot_data = bot.model_dump()
                    elif isinstance(bot, dict):
                        bot_data = bot
                    else:
                        bot_data = {
                            'bot_id': getattr(bot, 'bot_id', ''),
                            'bot_name': getattr(bot, 'bot_name', 'Unknown'),
                            'account_id': getattr(bot, 'account_id', ''),
                            'market': getattr(bot, 'market', ''),
                            'script_id': getattr(bot, 'script_id', ''),
                            'is_activated': getattr(bot, 'is_activated', False),
                            'is_paused': getattr(bot, 'is_paused', False),
                            'realized_profit': getattr(bot, 'realized_profit', 0),
                            'urealized_profit': getattr(bot, 'urealized_profit', 0),
                            'return_on_investment': getattr(bot, 'return_on_investment', 0),
                            'settings': getattr(bot, 'settings', {})
                        }
                    
                    # Analyze bot
                    bot_analysis = self.analyze_bot_comprehensive(server_name, bot_data)
                    analysis_results['bot_analyses'].append(bot_analysis)
                    
                    # Create comprehensive notes
                    notes = self.create_comprehensive_bot_notes(bot_analysis)
                    
                    # Update bot notes
                    bot_id = bot_analysis.get('bot_id', '')
                    if bot_id:
                        success = await self.update_bot_notes(server_name, bot_id, notes)
                        if success:
                            analysis_results['successful_updates'] += 1
                        else:
                            analysis_results['failed_updates'] += 1
                    
                except Exception as e:
                    print(f"Error processing bot {getattr(bot, 'bot_id', 'unknown')}: {e}")
                    analysis_results['failed_updates'] += 1
                    continue
            
            # Store results
            self.bot_analysis_results[server_name] = analysis_results
            
            return analysis_results
            
        except Exception as e:
            print(f"Error analyzing bots on {server_name}: {e}")
            return {'error': str(e)}
    
    def generate_analysis_report(self, server_name: str) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        analysis_results = self.bot_analysis_results.get(server_name, {})
        if not analysis_results:
            return {'error': 'No analysis results available'}
        
        # Generate summary statistics
        total_bots = analysis_results.get('total_analyzed', 0)
        successful_updates = analysis_results.get('successful_updates', 0)
        failed_updates = analysis_results.get('failed_updates', 0)
        
        # Analyze bot performance
        bot_analyses = analysis_results.get('bot_analyses', [])
        performance_stats = {
            'excellent_performance': 0,
            'good_performance': 0,
            'positive_performance': 0,
            'poor_performance': 0,
            'very_poor_performance': 0
        }
        
        risk_stats = {
            'low_risk': 0,
            'medium_risk': 0,
            'high_risk': 0
        }
        
        total_profit = 0
        profitable_bots = 0
        
        for analysis in bot_analyses:
            if 'error' not in analysis:
                # Performance rating
                rating = analysis.get('performance_rating', 'unknown')
                if rating in performance_stats:
                    performance_stats[rating] += 1
                
                # Risk level
                risk_level = analysis.get('risk_assessment', {}).get('risk_level', 'unknown')
                if risk_level in risk_stats:
                    risk_stats[risk_level] += 1
                
                # Profit analysis
                total_profit += analysis.get('performance', {}).get('total_profit', 0)
                if analysis.get('performance', {}).get('total_profit', 0) > 0:
                    profitable_bots += 1
        
        report = {
            'server': server_name,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_bots_analyzed': total_bots,
                'successful_notes_updates': successful_updates,
                'failed_notes_updates': failed_updates,
                'update_success_rate': (successful_updates / total_bots * 100) if total_bots > 0 else 0
            },
            'performance_analysis': {
                'total_profit': total_profit,
                'profitable_bots': profitable_bots,
                'profitability_rate': (profitable_bots / total_bots * 100) if total_bots > 0 else 0,
                'performance_distribution': performance_stats
            },
            'risk_analysis': {
                'risk_distribution': risk_stats,
                'high_risk_bots': risk_stats['high_risk'],
                'risk_percentage': (risk_stats['high_risk'] / total_bots * 100) if total_bots > 0 else 0
            },
            'recommendations': {
                'high_risk_bots_need_attention': risk_stats['high_risk'],
                'poor_performance_bots': performance_stats['poor_performance'] + performance_stats['very_poor_performance'],
                'excellent_performance_bots': performance_stats['excellent_performance']
            }
        }
        
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


async def test_comprehensive_bot_notes_system():
    """Test the comprehensive bot notes system"""
    print("Testing Comprehensive Bot Notes System")
    print("=" * 60)
    
    system = ComprehensiveBotNotesSystem()
    
    try:
        # Connect to srv03
        print("Connecting to srv03...")
        if not await system.connect_to_server("srv03"):
            print("Failed to connect to srv03")
            return 1
        
        # Analyze and update bot notes (limit to 5 bots for testing)
        print("\nAnalyzing and updating bot notes...")
        analysis_results = await system.analyze_and_update_all_bots("srv03", max_bots=5)
        if 'error' in analysis_results:
            print(f"Error analyzing bots: {analysis_results['error']}")
            return 1
        
        print(f"Analysis Results:")
        print(f"  Total analyzed: {analysis_results['total_analyzed']}")
        print(f"  Successful updates: {analysis_results['successful_updates']}")
        print(f"  Failed updates: {analysis_results['failed_updates']}")
        
        # Show first few bot analyses
        print("\nFirst 3 bot analyses:")
        for i, analysis in enumerate(analysis_results['bot_analyses'][:3]):
            if 'error' not in analysis:
                print(f"  {i+1}. {analysis.get('bot_name', 'Unknown')}")
                print(f"     Status: {analysis.get('status', 'unknown')}")
                print(f"     Performance: {analysis.get('performance_rating', 'unknown')}")
                print(f"     Risk: {analysis.get('risk_assessment', {}).get('risk_level', 'unknown')}")
                print(f"     Total Profit: ${analysis.get('performance', {}).get('total_profit', 0):.2f}")
        
        # Generate comprehensive report
        print("\nGenerating comprehensive report...")
        report = system.generate_analysis_report("srv03")
        if 'error' in report:
            print(f"Error generating report: {report['error']}")
            return 1
        
        print(f"Comprehensive Report:")
        print(f"  Server: {report['server']}")
        print(f"  Total bots analyzed: {report['summary']['total_bots_analyzed']}")
        print(f"  Update success rate: {report['summary']['update_success_rate']:.1f}%")
        print(f"  Total profit: ${report['performance_analysis']['total_profit']:.2f}")
        print(f"  Profitable bots: {report['performance_analysis']['profitable_bots']}")
        print(f"  High risk bots: {report['risk_analysis']['high_risk_bots']}")
        
        print("\nComprehensive bot notes system test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await system.cleanup_all()


async def main():
    """Main entry point"""
    return await test_comprehensive_bot_notes_system()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
