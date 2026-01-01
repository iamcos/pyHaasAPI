"""
Comprehensive lab analyzer for pyHaasAPI

This module provides the main HaasAnalyzer class for analyzing labs,
extracting backtest data, and creating optimized trading bots.
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from .. import api
from ..api import get_full_backtest_runtime_data
from ..model import AddBotFromLabRequest
from ..tools.utils import BacktestFetcher, BacktestFetchConfig
from .models import BacktestAnalysis, BotCreationResult, LabAnalysisResult, DrawdownAnalysis
from .cache import UnifiedCacheManager

logger = logging.getLogger(__name__)


class HaasAnalyzer:
    """Main analyzer class for comprehensive lab analysis and bot creation"""
    
    def __init__(self, cache_manager: Optional[UnifiedCacheManager] = None):
        self.cache_manager = cache_manager or UnifiedCacheManager()
        self.executor = None
        self.accounts = None
    
    def connect(self, host: str = None, port: int = None, email: str = None, password: str = None) -> bool:
        """Connect to HaasOnline API"""
        try:
            # Use provided parameters or environment variables
            host = host or os.getenv('API_HOST', '127.0.0.1')
            port = port or int(os.getenv('API_PORT', 8090))
            email = email or os.getenv('API_EMAIL')
            password = password or os.getenv('API_PASSWORD')
            
            if not email or not password:
                raise ValueError("Email and password must be provided or set in environment variables")
            
            # Create API connection
            haas_api = api.RequestsExecutor(
                host=host,
                port=port,
                state=api.Guest()
            )
            
            # Authenticate
            self.executor = haas_api.authenticate(email, password)
            
            logger.info("✅ Successfully connected to HaasOnline API")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to HaasOnline API: {e}")
            return False
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get available accounts"""
        if self.accounts is None:
            try:
                self.accounts = api.get_all_accounts(self.executor)
                logger.info(f"📋 Found {len(self.accounts)} accounts")
            except Exception as e:
                logger.error(f"❌ Failed to get accounts: {e}")
                self.accounts = []
        return self.accounts
    
    def analyze_backtest(self, lab_id: str, backtest_obj) -> Optional[BacktestAnalysis]:
        """Analyze a single backtest with full data extraction"""
        try:
            # Handle different backtest object structures
            if hasattr(backtest_obj, 'backtest_id'):
                backtest_id = backtest_obj.backtest_id
            elif hasattr(backtest_obj, 'ID'):
                backtest_id = backtest_obj.ID
            elif isinstance(backtest_obj, dict) and 'ID' in backtest_obj:
                backtest_id = backtest_obj['ID']
            else:
                logger.error(f"❌ Error analyzing backtest: 'backtest_id'")
                return None
                
            logger.info(f"🔍 Analyzing backtest {backtest_id[:8]}...")
            
            # Check cache first
            cached_data = self.cache_manager.load_backtest_cache(lab_id, backtest_id)
            if cached_data:
                logger.info(f"📁 Using cached data for {backtest_id[:8]}")
                return self._create_analysis_from_cache(cached_data, lab_id, backtest_obj)
            
            # Get full runtime data
            runtime_data = get_full_backtest_runtime_data(self.executor, lab_id, backtest_id)
            if not runtime_data:
                logger.warning(f"⚠️ Could not get runtime data for {backtest_id[:8]}")
                return None
            
            # Extract basic info - handle different object structures
            if isinstance(backtest_obj, dict):
                generation_idx = backtest_obj.get('GI', backtest_obj.get('generation_idx', None))
                population_idx = backtest_obj.get('PI', backtest_obj.get('population_idx', None))
                settings = backtest_obj.get('SE', backtest_obj.get('settings', {}))
            else:
                generation_idx = getattr(backtest_obj, 'generation_idx', getattr(backtest_obj, 'GI', None))
                population_idx = getattr(backtest_obj, 'population_idx', getattr(backtest_obj, 'PI', None))
                settings = getattr(backtest_obj, 'settings', getattr(backtest_obj, 'SE', None))
            
            # Extract settings - handle different structures
            if isinstance(settings, dict):
                market_tag = settings.get('market_tag', settings.get('MarketTag', ''))
                script_id = settings.get('script_id', settings.get('ScriptId', ''))
                script_name = settings.get('script_name', settings.get('ScriptName', ''))
            else:
                market_tag = getattr(settings, 'market_tag', getattr(settings, 'MarketTag', '')) if settings else ''
                script_id = getattr(settings, 'script_id', getattr(settings, 'ScriptId', '')) if settings else ''
                script_name = getattr(settings, 'script_name', getattr(settings, 'ScriptName', '')) if settings else ''
            
            # Initialize analysis
            analysis_data = {
                'roi_percentage': 0.0,  # ROI from lab data
                'calculated_roi_percentage': 0.0,  # ROI calculated from trades
                'roi_difference': 0.0,  # Difference between lab and calculated ROI
                'win_rate': 0.0,
                'total_trades': 0,
                'max_drawdown': 0.0,
                'realized_profits_usdt': 0.0,
                'pc_value': 0.0,
                'avg_profit_per_trade': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0
            }
            
            # Extract performance data from runtime Reports
            if hasattr(runtime_data, 'Reports') and runtime_data.Reports:
                report_key = list(runtime_data.Reports.keys())[0]
                report_data = runtime_data.Reports[report_key]
                
                # Extract performance metrics
                if hasattr(report_data, 'PR'):
                    pr_data = report_data.PR
                    analysis_data['realized_profits_usdt'] = float(pr_data.RP) if hasattr(pr_data, 'RP') else 0.0
                    analysis_data['roi_percentage'] = float(pr_data.ROI) if hasattr(pr_data, 'ROI') else 0.0
                    analysis_data['max_drawdown'] = float(pr_data.RM) if hasattr(pr_data, 'RM') else 0.0
                    analysis_data['pc_value'] = float(pr_data.PC) if hasattr(pr_data, 'PC') else 0.0
                
                # Extract trade statistics
                if hasattr(report_data, 'P'):
                    p_data = report_data.P
                    analysis_data['total_trades'] = int(p_data.C) if hasattr(p_data, 'C') else 0
                    winning_trades = int(p_data.W) if hasattr(p_data, 'W') else 0
                    analysis_data['win_rate'] = (winning_trades / analysis_data['total_trades']) if analysis_data['total_trades'] > 0 else 0.0
                
                # Calculate additional metrics
                if analysis_data['total_trades'] > 0:
                    analysis_data['avg_profit_per_trade'] = analysis_data['realized_profits_usdt'] / analysis_data['total_trades']
                
                # Calculate profit factor (simplified)
                if analysis_data['realized_profits_usdt'] > 0:
                    analysis_data['profit_factor'] = analysis_data['realized_profits_usdt'] / abs(analysis_data['max_drawdown']) if analysis_data['max_drawdown'] != 0 else 0.0
            
            # Calculate ROI from trades data
            calculated_roi = self._calculate_roi_from_trades(runtime_data)
            analysis_data['calculated_roi_percentage'] = calculated_roi
            analysis_data['roi_difference'] = abs(analysis_data['roi_percentage'] - calculated_roi)
            
            # Analyze drawdowns from balance history
            drawdown_analysis = self._analyze_drawdowns_from_balance_history(runtime_data)
            
            # Extract balance information
            balance_info = self._extract_balance_information(runtime_data)
            analysis_data.update(balance_info)
            
            # Create analysis object
            analysis = BacktestAnalysis(
                backtest_id=backtest_id,
                lab_id=lab_id,
                generation_idx=generation_idx,
                population_idx=population_idx,
                market_tag=market_tag,
                script_id=script_id,
                script_name=script_name,
                roi_percentage=analysis_data['roi_percentage'],
                calculated_roi_percentage=analysis_data['calculated_roi_percentage'],
                roi_difference=analysis_data['roi_difference'],
                win_rate=analysis_data['win_rate'],
                total_trades=analysis_data['total_trades'],
                max_drawdown=analysis_data['max_drawdown'],
                realized_profits_usdt=analysis_data['realized_profits_usdt'],
                pc_value=analysis_data['pc_value'],
                drawdown_analysis=drawdown_analysis,
                avg_profit_per_trade=analysis_data['avg_profit_per_trade'],
                profit_factor=analysis_data['profit_factor'],
                sharpe_ratio=analysis_data['sharpe_ratio'],
                starting_balance=analysis_data['starting_balance'],
                final_balance=analysis_data['final_balance'],
                peak_balance=analysis_data['peak_balance'],
                analysis_timestamp=datetime.now().isoformat()
            )
            
            # Cache the data
            cache_data = asdict(analysis)
            cache_data['runtime_data'] = runtime_data.model_dump() if hasattr(runtime_data, 'model_dump') else str(runtime_data)
            self.cache_manager.cache_backtest_data(lab_id, backtest_id, cache_data)
            
            # Enhanced logging with drawdown details
            drawdown_info = ""
            if analysis.drawdown_analysis:
                dd = analysis.drawdown_analysis
                drawdown_info = f", DD Count={dd.drawdown_count}, Lowest={dd.lowest_balance:.1f}"
            
            logger.info(f"✅ Analysis complete: Lab ROI={analysis.roi_percentage:.2f}%, ROE={analysis.calculated_roi_percentage:.2f}%, Win Rate={analysis.win_rate:.1%}, Max DD={analysis.max_drawdown:.1f}%, Trades={analysis.total_trades}, Balance: {analysis.starting_balance:.0f}→{analysis.final_balance:.0f} USDT{drawdown_info}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing backtest: {e}")
            return None
    
    def _create_analysis_from_cache(self, cached_data: Dict[str, Any], lab_id: str, backtest_obj) -> BacktestAnalysis:
        """Create analysis from cached data"""
        
        # Extract balance information from runtime_data in cache
        balance_info = {
            'starting_balance': 0.0,
            'final_balance': 0.0,
            'peak_balance': 0.0
        }
        
        if 'runtime_data' in cached_data:
            balance_info = self._extract_balance_information(cached_data['runtime_data'])
        
        # Extract parameter values from cached data
        parameter_values = self._extract_parameter_values_from_cache(cached_data)
        
        return BacktestAnalysis(
            backtest_id=cached_data['backtest_id'],
            lab_id=lab_id,
            generation_idx=cached_data['generation_idx'],
            population_idx=cached_data['population_idx'],
            market_tag=cached_data['market_tag'],
            script_id=cached_data['script_id'],
            script_name=cached_data['script_name'],
            roi_percentage=cached_data['roi_percentage'],
            calculated_roi_percentage=cached_data.get('calculated_roi_percentage', 0.0),
            roi_difference=cached_data.get('roi_difference', 0.0),
            win_rate=cached_data['win_rate'],
            total_trades=cached_data['total_trades'],
            max_drawdown=cached_data['max_drawdown'],
            realized_profits_usdt=cached_data['realized_profits_usdt'],
            pc_value=cached_data['pc_value'],
            avg_profit_per_trade=cached_data['avg_profit_per_trade'],
            profit_factor=cached_data['profit_factor'],
            sharpe_ratio=cached_data['sharpe_ratio'],
            starting_balance=balance_info['starting_balance'],
            final_balance=balance_info['final_balance'],
            peak_balance=balance_info['peak_balance'],
            analysis_timestamp=cached_data['analysis_timestamp'],
            parameter_values=parameter_values
        )
    
    def _extract_parameter_values_from_cache(self, cached_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract parameter values from cached backtest data"""
        try:
            input_fields = cached_data.get('InputFields', {})
            parameters = {}
            
            # Extract key parameters (filter out non-optimizable ones)
            for key, field in input_fields.items():
                param_name = field.get('N', '')  # Parameter name
                param_value = field.get('V', '')  # Parameter value
                
                # Skip system parameters and focus on optimizable ones
                if param_name and param_value and not any(skip in param_name.lower() for skip in 
                    ['trade amount', 'order size', 'entry order type', 'colldown', 'reset']):
                    # Clean up parameter name
                    clean_name = param_name.replace('TP ', 'Take Profit ').replace('SL ', 'Stop Loss ').replace('pct', '%')
                    parameters[clean_name] = param_value
            
            return parameters
            
        except Exception as e:
            logger.debug(f"Could not extract parameters from cache: {e}")
            return {}
    
    def _calculate_roi_from_trades(self, runtime_data) -> float:
        """Calculate ROI from individual trades data"""
        try:
            # Extract trades from runtime data
            trades = self._extract_trades_from_runtime_data(runtime_data)
            if not trades:
                logger.warning("No trades found in runtime data for ROI calculation")
                return 0.0
            
            # Calculate total profit/loss from trades
            total_profit = 0.0
            total_investment = 0.0
            
            for trade in trades:
                # Get trade profit/loss (net after fees)
                trade_profit = trade.get('net_profit', trade.get('profit_loss', 0.0))
                trade_amount = trade.get('trade_amount', trade.get('margin', 0.0))
                
                total_profit += trade_profit
                total_investment += trade_amount
            
            # Calculate ROI percentage
            if total_investment > 0:
                roi_percentage = (total_profit / total_investment) * 100
                logger.debug(f"Calculated ROI from {len(trades)} trades: {roi_percentage:.2f}%")
                return roi_percentage
            else:
                logger.warning("Total investment is 0, cannot calculate ROI")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating ROI from trades: {e}")
            return 0.0
    
    def _extract_trades_from_runtime_data(self, runtime_data) -> List[Dict[str, Any]]:
        """Extract trades from runtime data - handles both dict and object formats"""
        trades = []
        
        try:
            # Handle dict format (from cached data)
            if isinstance(runtime_data, dict):
                # Look for FinishedPositions at the top level of runtime_data
                finished_positions = runtime_data.get('FinishedPositions', [])
                
                for position in finished_positions:
                    # Extract trade data from finished position
                    trade_data = {
                        'position_id': position.get('g', ''),
                        'profit_loss': position.get('rp', 0.0),  # Realized profit
                        'fees': position.get('fe', 0.0),  # Total fees for position
                        'trade_amount': 0.0,  # Will be calculated from entry orders
                        'net_profit': 0.0  # Will be calculated
                    }
                    
                    # Get trade amount from entry orders (eno)
                    entry_orders = position.get('eno', [])
                    if entry_orders:
                        # Sum up all entry order margins
                        total_margin = sum(order.get('m', 0.0) for order in entry_orders)
                        trade_data['trade_amount'] = total_margin
                    
                    # Calculate net profit (profit - fees)
                    trade_data['net_profit'] = trade_data['profit_loss'] - trade_data['fees']
                    
                    # Only include trades with actual activity
                    if trade_data['trade_amount'] > 0 or trade_data['profit_loss'] != 0:
                        trades.append(trade_data)
            
            # Handle object format (from API)
            else:
                # Look for positions in runtime data
                if hasattr(runtime_data, 'Positions') and runtime_data.Positions:
                    for position_id, position in runtime_data.Positions.items():
                        # Extract trade data from position
                        trade_data = {
                            'position_id': position_id,
                            'profit_loss': getattr(position, 'rp', 0.0),  # Realized profit
                            'fees': getattr(position, 'fe', 0.0),  # Fees
                            'trade_amount': getattr(position, 'm', 0.0),  # Margin/trade amount
                            'net_profit': 0.0  # Will be calculated
                        }
                        
                        # Calculate net profit (profit - fees)
                        trade_data['net_profit'] = trade_data['profit_loss'] - trade_data['fees']
                        
                        trades.append(trade_data)
                
                # Alternative: look for trades in different structure
                elif hasattr(runtime_data, 'trades') and runtime_data.trades:
                    for trade in runtime_data.trades:
                        trade_data = {
                            'position_id': getattr(trade, 'id', ''),
                            'profit_loss': getattr(trade, 'profit', 0.0),
                            'fees': getattr(trade, 'fees', 0.0),
                            'trade_amount': getattr(trade, 'amount', 0.0),
                            'net_profit': 0.0
                        }
                        trade_data['net_profit'] = trade_data['profit_loss'] - trade_data['fees']
                        trades.append(trade_data)
            
            logger.debug(f"Extracted {len(trades)} trades from runtime data")
            
        except Exception as e:
            logger.error(f"Error extracting trades from runtime data: {e}")
        
        return trades
    
    def _analyze_drawdowns_from_balance_history(self, runtime_data) -> Optional[DrawdownAnalysis]:
        """Analyze drawdowns from balance history (RPH array)"""
        try:
            # Handle dict format (from cached data)
            if isinstance(runtime_data, dict):
                # Look for balance history in Reports section
                reports = runtime_data.get('Reports', {})
                for report_key, report_data in reports.items():
                    pr_data = report_data.get('PR', {})
                    balance_history = pr_data.get('RPH', [])  # Realized Profit History
                    
                    if balance_history:
                        return self._calculate_drawdown_analysis(balance_history)
            
            # Handle object format (from API)
            else:
                if hasattr(runtime_data, 'Reports') and runtime_data.Reports:
                    report_key = list(runtime_data.Reports.keys())[0]
                    report_data = runtime_data.Reports[report_key]
                    
                    if hasattr(report_data, 'PR'):
                        pr_data = report_data.PR
                        if hasattr(pr_data, 'RPH'):
                            balance_history = pr_data.RPH
                            return self._calculate_drawdown_analysis(balance_history)
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing drawdowns: {e}")
            return None
    
    def _extract_balance_information(self, runtime_data) -> Dict[str, float]:
        """Extract balance information from runtime data"""
        try:
            balance_info = {
                'starting_balance': 0.0,
                'final_balance': 0.0,
                'peak_balance': 0.0
            }
            
            # Handle dict format (from cached data)
            if isinstance(runtime_data, dict):
                reports = runtime_data.get('Reports', {})
                for report_key, report_data in reports.items():
                    pr_data = report_data.get('PR', {})
                    
                    # Get starting balance (SB field)
                    starting_balance = pr_data.get('SB', 0.0)
                    
                    # Get RPH (Realized Profit History)
                    rph_data = pr_data.get('RPH', [])
                    
                    if rph_data and starting_balance > 0:
                        # Calculate real account balances
                        starting_balance_real = starting_balance
                        final_profit = rph_data[-1] if rph_data else 0.0
                        peak_profit = max(rph_data) if rph_data else 0.0
                        
                        balance_info['starting_balance'] = starting_balance_real
                        balance_info['final_balance'] = starting_balance_real + final_profit
                        balance_info['peak_balance'] = starting_balance_real + peak_profit
                        
                        logger.debug(f"Balance info: Start={starting_balance_real:.2f}, Final={balance_info['final_balance']:.2f}, Peak={balance_info['peak_balance']:.2f}")
                        break
            
            # Handle object format (from API)
            else:
                if hasattr(runtime_data, 'Reports') and runtime_data.Reports:
                    report_key = list(runtime_data.Reports.keys())[0]
                    report_data = runtime_data.Reports[report_key]
                    
                    if hasattr(report_data, 'PR'):
                        pr_data = report_data.PR
                        starting_balance = getattr(pr_data, 'SB', 0.0)
                        
                        if hasattr(pr_data, 'RPH'):
                            rph_data = pr_data.RPH
                            if rph_data and starting_balance > 0:
                                starting_balance_real = starting_balance
                                final_profit = rph_data[-1] if rph_data else 0.0
                                peak_profit = max(rph_data) if rph_data else 0.0
                                
                                balance_info['starting_balance'] = starting_balance_real
                                balance_info['final_balance'] = starting_balance_real + final_profit
                                balance_info['peak_balance'] = starting_balance_real + peak_profit
            
            return balance_info
            
        except Exception as e:
            logger.error(f"Error extracting balance information: {e}")
            return {'starting_balance': 0.0, 'final_balance': 0.0, 'peak_balance': 0.0}
    
    def _calculate_drawdown_analysis(self, balance_history: List[float]) -> DrawdownAnalysis:
        """Calculate comprehensive drawdown analysis from balance history"""
        from .models import DrawdownEvent, DrawdownAnalysis
        from datetime import datetime, timedelta
        
        if not balance_history:
            return DrawdownAnalysis(
                max_drawdown_percentage=0.0,
                lowest_balance=0.0,
                drawdown_count=0,
                drawdown_events=[],
                balance_history=[]
            )
        
        # Find the lowest balance
        lowest_balance = min(balance_history)
        
        # Calculate max drawdown percentage
        # Assuming starting balance is 0, so max drawdown is the lowest point
        max_drawdown_percentage = abs(lowest_balance) if lowest_balance < 0 else 0.0
        
        # Count drawdowns (times balance went below zero)
        drawdown_events = []
        drawdown_count = 0
        
        # Create timestamps (assuming equal intervals - we'll use relative timestamps)
        start_time = datetime.now() - timedelta(days=len(balance_history))
        
        for i, balance in enumerate(balance_history):
            if balance < 0:  # Below zero = drawdown
                drawdown_count += 1
                
                # Create timestamp (relative to start)
                timestamp = start_time + timedelta(days=i)
                
                # Calculate drawdown amount and percentage
                drawdown_amount = abs(balance)
                drawdown_percentage = abs(balance) if balance < 0 else 0.0
                
                drawdown_events.append(DrawdownEvent(
                    timestamp=timestamp.strftime("%d.%m.%y %H:%M"),
                    balance=balance,
                    drawdown_amount=drawdown_amount,
                    drawdown_percentage=drawdown_percentage
                ))
        
        return DrawdownAnalysis(
            max_drawdown_percentage=max_drawdown_percentage,
            lowest_balance=lowest_balance,
            drawdown_count=drawdown_count,
            drawdown_events=drawdown_events,
            balance_history=balance_history
        )
    
    def analyze_lab(self, lab_id: str, top_count: int = 5) -> LabAnalysisResult:
        """Analyze a lab and return top performing backtests"""
        start_time = time.time()
        logger.info(f"🚀 Starting analysis of lab {lab_id[:8]}...")
        
        try:
            # Get lab details
            labs = api.get_all_labs(self.executor)
            lab = next((l for l in labs if l.lab_id == lab_id), None)
            if not lab:
                raise ValueError(f"Lab {lab_id} not found")
            
            lab_name = lab.name
            logger.info(f"📊 Lab: {lab_name}")
            
            # Get backtests using centralized fetcher
            fetcher = BacktestFetcher(self.executor, BacktestFetchConfig(page_size=100))
            backtests = fetcher.fetch_all_backtests(lab_id)
            
            if not backtests:
                raise ValueError("No backtests found")
            total_backtests = len(backtests)
            logger.info(f"📈 Found {total_backtests} backtests")
            
            # Analyze backtests
            analyzed_backtests = []
            for i, backtest in enumerate(backtests, 1):
                logger.info(f"📊 Analyzing backtest {i}/{total_backtests}")
                analysis = self.analyze_backtest(lab_id, backtest)
                if analysis:
                    analyzed_backtests.append(analysis)
            
            # Select top performers
            positive_backtests = [bt for bt in analyzed_backtests if bt.roi_percentage > 0]
            sorted_backtests = sorted(
                positive_backtests,
                key=lambda x: (x.roi_percentage, x.win_rate, -x.max_drawdown),
                reverse=True
            )
            
            top_backtests = sorted_backtests[:top_count]
            
            logger.info(f"🏆 Selected top {len(top_backtests)} backtests:")
            for i, bt in enumerate(top_backtests, 1):
                logger.info(f"  {i}. ROI: {bt.roi_percentage:.2f}%, Win Rate: {bt.win_rate:.1%}, Trades: {bt.total_trades}")
            
            processing_time = time.time() - start_time
            
            return LabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_name,
                total_backtests=total_backtests,
                analyzed_backtests=len(analyzed_backtests),
                top_backtests=top_backtests,
                bots_created=[],
                analysis_timestamp=datetime.now().isoformat(),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing lab: {e}")
            raise
    
    def create_bot_from_backtest(self, backtest: BacktestAnalysis, bot_name: str) -> Optional[BotCreationResult]:
        """Create a bot from a backtest analysis"""
        try:
            # Get accounts
            accounts = self.get_accounts()
            if not accounts:
                raise ValueError("No accounts available")
            
            # Get a unique account for this bot (round-robin assignment)
            if not hasattr(self, '_account_index'):
                self._account_index = 0
            
            account = accounts[self._account_index % len(accounts)]
            account_id = account['AID']
            self._account_index += 1
            
            logger.info(f"🤖 Creating bot: {bot_name}")
            logger.info(f"📊 From backtest: {backtest.backtest_id[:8]}")
            logger.info(f"🏪 Market: {backtest.market_tag}")
            logger.info(f"💳 Account: {account_id[:8]}")
            
            # Create bot request
            request = AddBotFromLabRequest(
                lab_id=backtest.lab_id,
                backtest_id=backtest.backtest_id,
                bot_name=bot_name,
                account_id=account_id,
                market=backtest.market_tag,
                leverage=20.0
            )
            
            # Create bot
            bot_response = api.add_bot_from_lab(self.executor, request)
            if not bot_response or not hasattr(bot_response, 'bot_id'):
                raise ValueError("Failed to create bot")
            
            bot_id = bot_response.bot_id
            logger.info(f"✅ Bot created successfully: {bot_id[:8]}")
            
            # Configure bot settings
            self._configure_bot_settings(account_id, backtest.market_tag)
            
            # Configure bot trade amount (20% of $10,000 = $2,000 USDT equivalent in base currency)
            trade_amount_configured = self._configure_bot_trade_amount(bot_id, 2000.0, backtest.market_tag)
            
            return BotCreationResult(
                bot_id=bot_id,
                bot_name=bot_name,
                backtest_id=backtest.backtest_id,
                account_id=account_id,
                market_tag=backtest.market_tag,
                leverage=20.0,
                margin_mode="CROSS",
                position_mode="HEDGE",
                trade_amount_usdt=2000.0,
                creation_timestamp=datetime.now().isoformat(),
                success=True,
                activated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating bot: {e}")
            return BotCreationResult(
                bot_id="",
                bot_name=bot_name,
                backtest_id=backtest.backtest_id,
                account_id="",
                market_tag=backtest.market_tag,
                leverage=20.0,
                margin_mode="CROSS",
                position_mode="HEDGE",
                trade_amount_usdt=2000.0,
                creation_timestamp=datetime.now().isoformat(),
                success=False,
                activated=False,
                error_message=str(e)
            )
    
    def _configure_bot_settings(self, account_id: str, market_tag: str) -> None:
        """Configure bot margin settings"""
        try:
            # Set margin settings: HEDGE mode, CROSS margin, 20x leverage
            api.set_position_mode(self.executor, account_id, market_tag, 1)  # HEDGE
            api.set_margin_mode(self.executor, account_id, market_tag, 0)    # CROSS
            api.set_leverage(self.executor, account_id, market_tag, 20.0)    # 20x leverage
            
            logger.info(f"✅ Bot configured with HEDGE, CROSS, 20x leverage")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not configure bot settings: {e}")
    
    def _configure_bot_trade_amount(self, bot_id: str, trade_amount_usdt: float = 2000.0, market_tag: str = None) -> bool:
        """Configure bot trade amount based on current market price (default: $2,000 USDT equivalent)"""
        try:
            # Get current bot details using get_full_bot_runtime_data for complete settings
            bot = api.get_full_bot_runtime_data(self.executor, bot_id)
            if not bot:
                logger.error(f"❌ Could not get bot details for {bot_id}")
                return False
            
            # Get market tag from bot if not provided
            if not market_tag:
                market_tag = bot.market
            
            # Calculate trade amount in base currency based on current market price
            calculated_trade_amount = self._calculate_trade_amount_in_base_currency(
                trade_amount_usdt, market_tag
            )
            
            # Update the bot's trade amount directly
            bot.settings.trade_amount = calculated_trade_amount
            
            # Ensure all required fields are populated
            bot.settings.bot_id = bot.bot_id
            bot.settings.bot_name = bot.bot_name
            bot.settings.account_id = bot.account_id
            bot.settings.market_tag = bot.market
            
            # Apply the trade amount setting using edit_bot_parameter
            updated_bot = api.edit_bot_parameter(self.executor, bot)
            
            logger.info(f"✅ Bot trade amount set to {calculated_trade_amount:.4f} base currency (${trade_amount_usdt} USDT equivalent)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Could not configure bot trade amount: {e}")
            return False
    
    def _calculate_trade_amount_in_base_currency(self, usdt_amount: float, market_tag: str) -> float:
        """Calculate trade amount in base currency based on current market price"""
        try:
            from pyHaasAPI_v1.price import PriceAPI
            
            # Initialize price API
            price_api = PriceAPI(self.executor)
            
            # Get current price data
            price_data = price_api.get_price_data(market_tag)
            current_price = price_data.close
            
            # Calculate trade amount in base currency
            # For USDT pairs: usdt_amount / current_price
            # For other pairs: need to handle conversion
            if 'USDT' in market_tag:
                # Direct USDT pair - divide USDT amount by current price
                trade_amount = usdt_amount / current_price
            else:
                # For non-USDT pairs, we'd need additional conversion logic
                # For now, assume it's a USDT pair or use a simplified approach
                trade_amount = usdt_amount / current_price
            
            # Apply smart precision
            trade_amount = self._apply_smart_precision(trade_amount)
            
            logger.info(f"💰 Market: {market_tag}, Price: ${current_price:.4f}, Trade Amount: {trade_amount} base currency")
            return trade_amount
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get current price for {market_tag}, using default calculation: {e}")
            # Fallback: assume $1 per unit for non-USDT pairs or if price fetch fails
            return usdt_amount
    
    def _apply_smart_precision(self, amount: float) -> float:
        """Apply smart precision based on decimal places - keep 3 significant digits after zeros"""
        if amount == 0:
            return 0.0
        
        # Convert to string to analyze decimal places
        amount_str = f"{amount:.15f}".rstrip('0').rstrip('.')
        
        # Find the position of the first non-zero digit after decimal
        if '.' in amount_str:
            decimal_part = amount_str.split('.')[1]
            first_non_zero = 0
            for i, char in enumerate(decimal_part):
                if char != '0':
                    first_non_zero = i
                    break
            
            # Keep 3 significant digits after the first non-zero
            precision = first_non_zero + 3
        else:
            # For whole numbers, keep 3 decimal places
            precision = 3
        
        # Round to the calculated precision
        rounded_amount = round(amount, precision)
        
        # Convert back to float and remove trailing zeros
        return float(f"{rounded_amount:.{precision}f}".rstrip('0').rstrip('.'))
    
    def activate_bot(self, bot_id: str) -> bool:
        """Activate a bot for live trading"""
        try:
            activated_bot = api.activate_bot(self.executor, bot_id, cleanreports=False)
            logger.info(f"✅ Bot activated: {bot_id[:8]}")
            return True
        except Exception as e:
            logger.error(f"❌ Could not activate bot {bot_id[:8]}: {e}")
            return False
    
    def create_bots_from_analysis(self, analysis_result: LabAnalysisResult, create_count: Optional[int] = None) -> List[BotCreationResult]:
        """Create bots from top backtests in analysis result"""
        if create_count is None:
            create_count = len(analysis_result.top_backtests)
        
        bots_created = []
        for i, backtest in enumerate(analysis_result.top_backtests[:create_count], 1):
            # Create bot name following the convention: LabName - ScriptName - ROI pop/gen WR%
            lab_name_clean = analysis_result.lab_name.replace('_', ' ').replace('-', ' ')
            roi_str = f"{backtest.roi_percentage:.0f}"
            pop_gen_str = f"{backtest.population_idx or 0}/{backtest.generation_idx or 0}"
            win_rate_percent = f"{backtest.win_rate * 100:.0f}%"
            bot_name = f"{lab_name_clean} - {backtest.script_name} - {roi_str} {pop_gen_str} {win_rate_percent}"
            
            bot_result = self.create_bot_from_backtest(backtest, bot_name)
            if bot_result:
                bots_created.append(bot_result)
        
        # Update the analysis result with created bots
        analysis_result.bots_created = bots_created
        
        return bots_created
    
    def create_and_activate_bots(self, analysis_result: LabAnalysisResult, create_count: Optional[int] = None, activate: bool = True) -> List[BotCreationResult]:
        """Create bots and optionally activate them for live trading"""
        # Create bots first
        bots_created = self.create_bots_from_analysis(analysis_result, create_count)
        
        if activate:
            logger.info(f"🚀 Activating {len(bots_created)} bots for live trading...")
            for bot_result in bots_created:
                if bot_result.success:
                    activation_success = self.activate_bot(bot_result.bot_id)
                    if activation_success:
                        bot_result.activated = True
                        logger.info(f"✅ Bot {bot_result.bot_name} is now LIVE and trading!")
                    else:
                        logger.warning(f"⚠️ Bot {bot_result.bot_name} created but not activated")
        
        return bots_created
