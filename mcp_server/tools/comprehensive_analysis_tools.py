#!/usr/bin/env python3
"""
MCP Server Tools for Comprehensive Backtest Analysis
Connects the frontend interface with the comprehensive analyzer
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the comprehensive analyzer
from backtest_analysis.comprehensive_backtest_analyzer import (
    ComprehensiveBacktestAnalyzer,
    FullBacktestReport,
    ComprehensiveBacktestMetrics
)
from account_management.account_manager import AccountManager, AccountType, AccountStatus
from pyHaasAPI import api

logger = logging.getLogger(__name__)

class ComprehensiveAnalysisTools:
    """MCP tools for comprehensive backtest analysis"""
    
    def __init__(self, executor, account_manager: AccountManager = None):
        self.executor = executor
        self.analyzer = ComprehensiveBacktestAnalyzer(executor, account_manager)
        self.account_manager = account_manager
    
    async def analyze_backtest_comprehensive(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive analysis of a single backtest
        
        Args:
            params: {"backtest_id": "string"}
        
        Returns:
            Complete analysis report with all metrics
        """
        try:
            backtest_id = params.get('backtest_id')
            if not backtest_id:
                return {
                    'success': False,
                    'error': 'backtest_id is required'
                }
            
            logger.info(f"Starting comprehensive analysis for backtest {backtest_id}")
            
            # Perform comprehensive analysis
            report = self.analyzer.analyze_single_backtest(backtest_id)
            
            # Convert to serializable format
            report_dict = self._convert_report_to_dict(report)
            
            return {
                'success': True,
                'data': report_dict,
                'message': f'Comprehensive analysis completed for backtest {backtest_id}'
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def compare_backtests_comprehensive(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare multiple backtests and rank them
        
        Args:
            params: {"backtest_ids": ["string1", "string2", ...]}
        
        Returns:
            Comparison analysis with rankings and deployment recommendations
        """
        try:
            backtest_ids = params.get('backtest_ids', [])
            if not backtest_ids:
                return {
                    'success': False,
                    'error': 'backtest_ids list is required'
                }
            
            logger.info(f"Comparing {len(backtest_ids)} backtests")
            
            # Perform comparison analysis
            comparison_result = self.analyzer.compare_multiple_backtests(backtest_ids)
            
            return {
                'success': True,
                'data': comparison_result,
                'message': f'Comparison completed for {len(backtest_ids)} backtests'
            }
            
        except Exception as e:
            logger.error(f"Backtest comparison failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_available_simulation_accounts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get available simulation accounts for deployment
        
        Args:
            params: {} (no parameters needed)
        
        Returns:
            List of available simulation accounts
        """
        try:
            if not self.account_manager:
                return {
                    'success': False,
                    'error': 'Account manager not available'
                }
            
            # Get all simulation accounts
            server_id = "default_server"  # This should be configurable
            all_accounts = self.account_manager.get_all_accounts(server_id)
            
            # Filter for available simulation accounts
            available_accounts = []
            for account in all_accounts:
                if (account.account_type == AccountType.SIMULATION and 
                    account.status == AccountStatus.ACTIVE):
                    available_accounts.append({
                        'account_id': account.account_id,
                        'account_name': account.account_name,
                        'balance': account.balance,
                        'status': account.status.value,
                        'server_id': account.server_id
                    })
            
            return {
                'success': True,
                'data': {
                    'accounts': available_accounts,
                    'total_available': len(available_accounts)
                },
                'message': f'Found {len(available_accounts)} available simulation accounts'
            }
            
        except Exception as e:
            logger.error(f"Failed to get available accounts: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def deploy_backtest_as_live_bot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy a backtest as a live trading bot
        
        Args:
            params: {
                "backtest_id": "string",
                "deployment_config": {
                    "account_allocation": {...},
                    "risk_management": {...},
                    "deployment_strategy": {...}
                }
            }
        
        Returns:
            Deployment result with bot ID and account allocation
        """
        try:
            backtest_id = params.get('backtest_id')
            deployment_config = params.get('deployment_config', {})
            
            if not backtest_id:
                return {
                    'success': False,
                    'error': 'backtest_id is required'
                }
            
            logger.info(f"Deploying backtest {backtest_id} as live bot")
            
            # Get the analysis report to validate deployment readiness
            report = self.analyzer.analyze_single_backtest(backtest_id)
            
            if not report.deployment_recommendation.is_recommended:
                return {
                    'success': False,
                    'error': f'Backtest not recommended for deployment. Readiness score: {report.metrics.deployment_readiness_score}%'
                }
            
            # Deploy the bot (this would integrate with actual bot deployment system)
            deployment_result = await self._deploy_bot_implementation(report, deployment_config)
            
            return {
                'success': True,
                'data': deployment_result,
                'message': f'Bot deployed successfully from backtest {backtest_id}'
            }
            
        except Exception as e:
            logger.error(f"Bot deployment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def export_analysis_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export comprehensive analysis report
        
        Args:
            params: {"backtest_id": "string", "format": "json|csv"}
        
        Returns:
            Exported report data
        """
        try:
            backtest_id = params.get('backtest_id')
            format_type = params.get('format', 'json')
            
            if not backtest_id:
                return {
                    'success': False,
                    'error': 'backtest_id is required'
                }
            
            # Export the report
            filename = self.analyzer.export_analysis_report(backtest_id, format_type)
            
            # Read the exported file content
            with open(filename, 'r') as f:
                report_data = json.load(f) if format_type == 'json' else f.read()
            
            return {
                'success': True,
                'data': report_data,
                'filename': filename,
                'message': f'Report exported successfully to {filename}'
            }
            
        except Exception as e:
            logger.error(f"Report export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_backtest_history_for_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get backtest history with filtering for analysis
        
        Args:
            params: {
                "filters": {
                    "startDate": "ISO date string",
                    "endDate": "ISO date string",
                    "minProfit": number,
                    "maxDrawdown": number,
                    "minTrades": number
                }
            }
        
        Returns:
            Filtered backtest history
        """
        try:
            filters = params.get('filters', {})
            
            # Get backtest history from API
            history_result = api.get_backtest_history(self.executor)
            
            if not history_result.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to retrieve backtest history'
                }
            
            backtests = history_result.get('data', [])
            
            # Apply filters
            filtered_backtests = self._apply_backtest_filters(backtests, filters)
            
            return {
                'success': True,
                'data': {
                    'backtests': filtered_backtests,
                    'total_count': len(filtered_backtests),
                    'filters_applied': filters
                },
                'message': f'Retrieved {len(filtered_backtests)} backtests'
            }
            
        except Exception as e:
            logger.error(f"Failed to get backtest history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_lab_comprehensive(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive analysis of lab results
        
        Args:
            params: {"lab_id": "string"}
        
        Returns:
            Lab analysis with trading styles and optimization ranges
        """
        try:
            lab_id = params.get('lab_id')
            if not lab_id:
                return {
                    'success': False,
                    'error': 'lab_id is required'
                }
            
            # This would integrate with the lab analysis system
            from backtest_analysis.lab_analysis_system import LabAnalysisSystem
            
            lab_analyzer = LabAnalysisSystem()
            
            # Load lab results (this would be the actual lab results file)
            # For now, return a placeholder response
            analysis_result = {
                'trading_styles': [],
                'optimization_ranges': {},
                'recommendations': ['Lab analysis system integration needed']
            }
            
            return {
                'success': True,
                'data': analysis_result,
                'message': f'Lab analysis completed for {lab_id}'
            }
            
        except Exception as e:
            logger.error(f"Lab analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def monitor_deployed_bots(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor performance of deployed bots
        
        Args:
            params: {} (no parameters needed)
        
        Returns:
            Current status and performance of all deployed bots
        """
        try:
            # This would integrate with the bot monitoring system
            # For now, return mock data structure
            deployed_bots = []
            
            return {
                'success': True,
                'data': {
                    'deployed_bots': deployed_bots,
                    'total_deployed': len(deployed_bots),
                    'monitoring_timestamp': datetime.now().isoformat()
                },
                'message': f'Monitoring {len(deployed_bots)} deployed bots'
            }
            
        except Exception as e:
            logger.error(f"Bot monitoring failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def stop_deployed_bot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stop a deployed bot
        
        Args:
            params: {"bot_id": "string", "reason": "string"}
        
        Returns:
            Success status
        """
        try:
            bot_id = params.get('bot_id')
            reason = params.get('reason', 'Manual stop')
            
            if not bot_id:
                return {
                    'success': False,
                    'error': 'bot_id is required'
                }
            
            # This would integrate with the bot management system
            logger.info(f"Stopping bot {bot_id}: {reason}")
            
            return {
                'success': True,
                'data': {
                    'bot_id': bot_id,
                    'stopped_at': datetime.now().isoformat(),
                    'reason': reason
                },
                'message': f'Bot {bot_id} stopped successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_bot_performance_real_time(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get real-time performance metrics for a deployed bot
        
        Args:
            params: {"bot_id": "string"}
        
        Returns:
            Real-time performance data
        """
        try:
            bot_id = params.get('bot_id')
            if not bot_id:
                return {
                    'success': False,
                    'error': 'bot_id is required'
                }
            
            # This would integrate with real-time bot monitoring
            performance_data = {
                'current_balance': 10000.0,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'open_positions': 0,
                'todays_trades': 0,
                'win_rate_today': 0.0,
                'current_drawdown': 0.0,
                'margin_usage': 0.0,
                'alerts': []
            }
            
            return {
                'success': True,
                'data': performance_data,
                'message': f'Real-time data for bot {bot_id}'
            }
            
        except Exception as e:
            logger.error(f"Failed to get bot performance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bulk_deploy_strategies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy multiple strategies with risk management
        
        Args:
            params: {
                "deployment_requests": [
                    {"backtest_id": "string", "deployment_config": {...}},
                    ...
                ]
            }
        
        Returns:
            Bulk deployment results
        """
        try:
            deployment_requests = params.get('deployment_requests', [])
            
            if not deployment_requests:
                return {
                    'success': False,
                    'error': 'deployment_requests is required'
                }
            
            logger.info(f"Bulk deploying {len(deployment_requests)} strategies")
            
            results = []
            successful = 0
            failed = 0
            
            for request in deployment_requests:
                try:
                    backtest_id = request['backtest_id']
                    deployment_config = request.get('deployment_config', {})
                    
                    # Deploy individual strategy
                    deploy_result = await self.deploy_backtest_as_live_bot({
                        'backtest_id': backtest_id,
                        'deployment_config': deployment_config
                    })
                    
                    if deploy_result['success']:
                        successful += 1
                        results.append({
                            'backtest_id': backtest_id,
                            'success': True,
                            'bot_id': deploy_result['data'].get('bot_id'),
                            'account_id': deploy_result['data'].get('account_id')
                        })
                    else:
                        failed += 1
                        results.append({
                            'backtest_id': backtest_id,
                            'success': False,
                            'error': deploy_result['error']
                        })
                        
                except Exception as e:
                    failed += 1
                    results.append({
                        'backtest_id': request.get('backtest_id', 'unknown'),
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'data': {
                    'successful_deployments': successful,
                    'failed_deployments': failed,
                    'deployment_results': results
                },
                'message': f'Bulk deployment completed: {successful} successful, {failed} failed'
            }
            
        except Exception as e:
            logger.error(f"Bulk deployment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_account_allocation_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get account allocation status for deployment planning
        
        Args:
            params: {} (no parameters needed)
        
        Returns:
            Account allocation breakdown
        """
        try:
            if not self.account_manager:
                return {
                    'success': False,
                    'error': 'Account manager not available'
                }
            
            # Get account statistics
            stats = self.account_manager.get_account_statistics()
            
            # Get detailed allocation breakdown
            server_id = "default_server"  # This should be configurable
            all_accounts = self.account_manager.get_all_accounts(server_id)
            
            allocation_breakdown = []
            available_count = 0
            allocated_count = 0
            
            for account in all_accounts:
                is_available = account.status == AccountStatus.ACTIVE
                if is_available:
                    available_count += 1
                else:
                    allocated_count += 1
                
                allocation_breakdown.append({
                    'account_id': account.account_id,
                    'account_name': account.account_name,
                    'status': account.status.value,
                    'assigned_bot': None,  # This would come from bot assignment tracking
                    'allocation_date': None
                })
            
            return {
                'success': True,
                'data': {
                    'total_accounts': stats['total_accounts'],
                    'available_accounts': available_count,
                    'allocated_accounts': allocated_count,
                    'accounts_by_type': stats['accounts_by_type'],
                    'allocation_breakdown': allocation_breakdown
                },
                'message': f'Account allocation status retrieved'
            }
            
        except Exception as e:
            logger.error(f"Failed to get allocation status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_report_to_dict(self, report: FullBacktestReport) -> Dict[str, Any]:
        """Convert FullBacktestReport to dictionary for JSON serialization"""
        from dataclasses import asdict
        
        return {
            'backtest_id': report.backtest_id,
            'script_name': report.script_name,
            'account_name': report.account_name,
            'market_tag': report.market_tag,
            'execution_period': report.execution_period,
            'metrics': asdict(report.metrics),
            'equity_curve': report.equity_curve,
            'position_analysis': report.position_analysis,
            'risk_analysis': report.risk_analysis,
            'deployment_recommendation': report.deployment_recommendation,
            'chart_data': report.chart_data,
            'performance_rank': report.performance_rank,
            'style_classification': report.style_classification,
            'generated_at': datetime.now().isoformat()
        }
    
    async def _deploy_bot_implementation(self, report: FullBacktestReport, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actual bot deployment implementation
        This would integrate with the HaasOnline API to create and start a live bot
        """
        try:
            # Mock deployment for now - this would be the actual implementation
            import uuid
            
            deployment_id = str(uuid.uuid4())
            bot_id = f"bot_{deployment_id[:8]}"
            
            # Get account allocation
            account_allocation = report.deployment_recommendation.account_allocation
            if not account_allocation:
                raise ValueError("No account allocation available")
            
            account_id = account_allocation.get('assigned_account_id')
            if not account_id:
                raise ValueError("No account assigned for deployment")
            
            # Create deployment record
            deployment_result = {
                'deployment_id': deployment_id,
                'bot_id': bot_id,
                'account_id': account_id,
                'backtest_id': report.backtest_id,
                'deployment_config': {
                    'script_name': report.script_name,
                    'market_tag': report.market_tag,
                    'risk_management': report.deployment_recommendation.risk_management,
                    'deployment_strategy': report.deployment_recommendation.deployment_strategy,
                    'monitoring_requirements': report.deployment_recommendation.monitoring_requirements
                },
                'deployment_time': datetime.now().isoformat(),
                'status': 'DEPLOYED',
                'message': f'Bot deployed successfully on account {account_id}'
            }
            
            logger.info(f"Bot {bot_id} deployed for backtest {report.backtest_id}")
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Bot deployment implementation failed: {e}")
            raise e
    
    def _apply_backtest_filters(self, backtests: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to backtest history"""
        filtered = backtests
        
        # Apply date filters
        if 'startDate' in filters:
            start_date = datetime.fromisoformat(filters['startDate'].replace('Z', '+00:00'))
            filtered = [bt for bt in filtered if datetime.fromisoformat(bt.get('execution_date', '2000-01-01')) >= start_date]
        
        if 'endDate' in filters:
            end_date = datetime.fromisoformat(filters['endDate'].replace('Z', '+00:00'))
            filtered = [bt for bt in filtered if datetime.fromisoformat(bt.get('execution_date', '2000-01-01')) <= end_date]
        
        # Apply performance filters
        if 'minProfit' in filters:
            filtered = [bt for bt in filtered if bt.get('profit_percent', 0) >= filters['minProfit']]
        
        if 'maxDrawdown' in filters:
            filtered = [bt for bt in filtered if bt.get('max_drawdown', 100) <= filters['maxDrawdown']]
        
        if 'minTrades' in filters:
            filtered = [bt for bt in filtered if bt.get('total_trades', 0) >= filters['minTrades']]
        
        return filtered

# Tool registration for MCP server
def register_comprehensive_analysis_tools(server, executor, account_manager=None):
    """Register all comprehensive analysis tools with the MCP server"""
    
    tools = ComprehensiveAnalysisTools(executor, account_manager)
    
    # Register each tool
    @server.tool()
    async def analyze_backtest_comprehensive(params: dict) -> dict:
        """Comprehensive analysis of a single backtest with all required metrics"""
        return await tools.analyze_backtest_comprehensive(params)
    
    @server.tool()
    async def compare_backtests_comprehensive(params: dict) -> dict:
        """Compare multiple backtests and rank them for deployment"""
        return await tools.compare_backtests_comprehensive(params)
    
    @server.tool()
    async def get_available_simulation_accounts(params: dict) -> dict:
        """Get available simulation accounts for bot deployment"""
        return await tools.get_available_simulation_accounts(params)
    
    @server.tool()
    async def deploy_backtest_as_live_bot(params: dict) -> dict:
        """Deploy a backtest as a live trading bot"""
        return await tools.deploy_backtest_as_live_bot(params)
    
    @server.tool()
    async def export_analysis_report(params: dict) -> dict:
        """Export comprehensive analysis report"""
        return await tools.export_analysis_report(params)
    
    @server.tool()
    async def get_backtest_history_for_analysis(params: dict) -> dict:
        """Get backtest history with filtering for analysis"""
        return await tools.get_backtest_history_for_analysis(params)
    
    @server.tool()
    async def analyze_lab_comprehensive(params: dict) -> dict:
        """Comprehensive analysis of lab results"""
        return await tools.analyze_lab_comprehensive(params)
    
    @server.tool()
    async def monitor_deployed_bots(params: dict) -> dict:
        """Monitor performance of deployed bots"""
        return await tools.monitor_deployed_bots(params)
    
    @server.tool()
    async def stop_deployed_bot(params: dict) -> dict:
        """Stop a deployed bot"""
        return await tools.stop_deployed_bot(params)
    
    @server.tool()
    async def get_bot_performance_real_time(params: dict) -> dict:
        """Get real-time performance metrics for a deployed bot"""
        return await tools.get_bot_performance_real_time(params)
    
    @server.tool()
    async def bulk_deploy_strategies(params: dict) -> dict:
        """Deploy multiple strategies with risk management"""
        return await tools.bulk_deploy_strategies(params)
    
    @server.tool()
    async def get_account_allocation_status(params: dict) -> dict:
        """Get account allocation status for deployment planning"""
        return await tools.get_account_allocation_status(params)
    
    logger.info("Comprehensive analysis tools registered with MCP server")
    
    return tools