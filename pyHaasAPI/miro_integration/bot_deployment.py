"""
Bot Deployment Center for Miro Integration

Provides interactive bot deployment management with Miro boards:
- One-click bot creation from lab analysis
- Real-time bot status monitoring
- Performance tracking and alerts
- Automated bot management workflows
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import time

from .client import MiroClient, MiroBoard, MiroItem
from ..analysis import HaasAnalyzer, UnifiedCacheManager
from ..analysis.models import LabAnalysisResult, BacktestAnalysis, BotCreationResult

logger = logging.getLogger(__name__)


@dataclass
class BotDeploymentConfig:
    """Configuration for bot deployment"""
    default_leverage: float = 20.0
    default_trade_amount_usdt: float = 2000.0
    position_mode: int = 1  # HEDGE
    margin_mode: int = 0    # CROSS
    auto_activate: bool = False
    max_bots_per_lab: int = 5
    account_distribution: str = "individual"  # individual, round_robin, manual


@dataclass
class BotDeploymentStatus:
    """Status of bot deployment"""
    bot_id: str
    bot_name: str
    lab_id: str
    backtest_id: str
    account_id: str
    market_tag: str
    status: str  # 'created', 'configured', 'activated', 'running', 'paused', 'failed'
    creation_timestamp: datetime
    activation_timestamp: Optional[datetime] = None
    performance_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BotDeploymentCenter:
    """Interactive bot deployment center with Miro integration"""
    
    def __init__(self, miro_client: MiroClient, analyzer: HaasAnalyzer,
                 config: Optional[BotDeploymentConfig] = None):
        """
        Initialize bot deployment center
        
        Args:
            miro_client: Miro API client
            analyzer: HaasAnalyzer instance
            config: Deployment configuration
        """
        self.miro_client = miro_client
        self.analyzer = analyzer
        self.config = config or BotDeploymentConfig()
        self.deployed_bots: Dict[str, BotDeploymentStatus] = {}
        self.board_items: Dict[str, Dict[str, str]] = {}  # bot_id -> {item_type: item_id}
        
    def create_bot_deployment_board(self, board_name: str = None) -> Optional[MiroBoard]:
        """Create a dedicated board for bot deployment management"""
        try:
            if not board_name:
                board_name = f"Bot Deployment Center - {datetime.now().strftime('%Y-%m-%d')}"
            
            board = self.miro_client.create_board(
                name=board_name,
                description="Interactive bot deployment and management center"
            )
            
            if board:
                logger.info(f"Created bot deployment board: {board.id}")
                self._setup_deployment_board_layout(board.id)
            
            return board
            
        except Exception as e:
            logger.error(f"Failed to create bot deployment board: {e}")
            return None
    
    def _setup_deployment_board_layout(self, board_id: str):
        """Set up the initial layout for deployment board"""
        try:
            # Create header
            header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🤖 pyHaasAPI Bot Deployment Center",
                x=0, y=-800,
                width=1200, height=80,
                style={"fontSize": 24, "fontWeight": "bold", "textAlign": "center"}
            )
            
            # Create status legend
            legend_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 Bot Status Legend:\n🟢 Running | 🟡 Paused | 🔴 Failed | ⚪ Created | 🔵 Activated",
                x=-1200, y=-700,
                width=300, height=100,
                style={"fontSize": 14, "fontWeight": "bold"}
            )
            
            # Create deployment controls
            controls_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🎛️ Deployment Controls",
                x=0, y=-600,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold"}
            )
            
            # Create bot list header
            bots_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🤖 Deployed Bots",
                x=-600, y=-600,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold"}
            )
            
            # Create deployment buttons
            self._create_deployment_buttons(board_id)
            
            logger.info(f"Set up deployment board layout for {board_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup deployment board layout: {e}")
    
    def _create_deployment_buttons(self, board_id: str):
        """Create deployment control buttons"""
        try:
            # Mass bot creation button
            mass_create_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=0, y=-500,
                width=200, height=60,
                content="🚀 Mass Bot Creator",
                style={
                    "backgroundColor": "#28A745",
                    "color": "#FFFFFF",
                    "fontSize": 14,
                    "fontWeight": "bold"
                }
            )
            
            # Analyze all labs button
            analyze_all_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=220, y=-500,
                width=200, height=60,
                content="📊 Analyze All Labs",
                style={
                    "backgroundColor": "#007ACC",
                    "color": "#FFFFFF",
                    "fontSize": 14,
                    "fontWeight": "bold"
                }
            )
            
            # Bot management button
            manage_bots_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=440, y=-500,
                width=200, height=60,
                content="⚙️ Manage Bots",
                style={
                    "backgroundColor": "#6C757D",
                    "color": "#FFFFFF",
                    "fontSize": 14,
                    "fontWeight": "bold"
                }
            )
            
            # Performance dashboard button
            performance_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=660, y=-500,
                width=200, height=60,
                content="📈 Performance",
                style={
                    "backgroundColor": "#FF9800",
                    "color": "#FFFFFF",
                    "fontSize": 14,
                    "fontWeight": "bold"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create deployment buttons: {e}")
    
    def create_bots_from_lab_analysis(self, lab_id: str, board_id: str, 
                                    top_count: int = 5, activate: bool = False) -> List[BotCreationResult]:
        """Create bots from lab analysis and add to Miro board"""
        try:
            logger.info(f"Creating bots from lab {lab_id} analysis...")
            
            # Analyze the lab
            analysis_result = self.analyzer.analyze_lab(lab_id, top_count=top_count)
            if not analysis_result or not analysis_result.top_backtests:
                logger.warning(f"No backtests found for lab {lab_id}")
                return []
            
            # Create bots from top backtests
            bot_results = []
            for i, backtest in enumerate(analysis_result.top_backtests[:top_count]):
                try:
                    # Generate bot name with lab name, ROI, and pop/gen as preferred
                    bot_name = self._generate_bot_name(backtest, i)
                    
                    # Create bot
                    bot_result = self.analyzer.create_bot_from_backtest(backtest, bot_name)
                    if bot_result and bot_result.success:
                        bot_results.append(bot_result)
                        
                        # Add to deployment tracking
                        deployment_status = BotDeploymentStatus(
                            bot_id=bot_result.bot_id,
                            bot_name=bot_result.bot_name,
                            lab_id=lab_id,
                            backtest_id=bot_result.backtest_id,
                            account_id=bot_result.account_id,
                            market_tag=bot_result.market_tag,
                            status="created",
                            creation_timestamp=datetime.now()
                        )
                        
                        self.deployed_bots[bot_result.bot_id] = deployment_status
                        
                        # Create bot card on Miro board
                        self._create_bot_card(board_id, deployment_status)
                        
                        # Activate if requested
                        if activate:
                            self._activate_bot(bot_result.bot_id, board_id)
                        
                        logger.info(f"Created bot: {bot_result.bot_name} ({bot_result.bot_id[:8]})")
                    
                except Exception as e:
                    logger.error(f"Failed to create bot from backtest {backtest.backtest_id}: {e}")
                    continue
            
            logger.info(f"Successfully created {len(bot_results)} bots from lab {lab_id}")
            return bot_results
            
        except Exception as e:
            logger.error(f"Failed to create bots from lab {lab_id}: {e}")
            return []
    
    def _generate_bot_name(self, backtest: BacktestAnalysis, index: int) -> str:
        """Generate bot name with lab name, ROI, and pop/gen as preferred"""
        try:
            # Extract lab name (first part before any separators)
            lab_name = backtest.lab_id[:8]  # Use lab ID prefix
            
            # Format ROI
            roi_str = f"{backtest.roi_percentage:.0f}"
            
            # Format population/generation if available
            pop_gen_str = ""
            if backtest.generation_idx is not None and backtest.population_idx is not None:
                pop_gen_str = f" {backtest.population_idx}/{backtest.generation_idx}"
            elif backtest.population_idx is not None:
                pop_gen_str = f" {backtest.population_idx}"
            
            # Format win rate
            wr_str = f"{backtest.win_rate:.0%}"
            
            # Create bot name following the preferred format
            bot_name = f"{lab_name} - {backtest.script_name} - {roi_str}%{pop_gen_str} {wr_str}"
            
            # Ensure name is not too long (Miro has limits)
            if len(bot_name) > 100:
                bot_name = bot_name[:97] + "..."
            
            return bot_name
            
        except Exception as e:
            logger.error(f"Failed to generate bot name: {e}")
            return f"Bot_{backtest.backtest_id[:8]}"
    
    def _create_bot_card(self, board_id: str, deployment_status: BotDeploymentStatus):
        """Create a bot status card on the Miro board"""
        try:
            # Calculate position based on number of deployed bots
            bot_count = len(self.deployed_bots)
            x = -600 + (bot_count % 2) * 650
            y = -500 + (bot_count // 2) * 300
            
            # Create status indicator
            status_emoji = {
                "created": "⚪",
                "configured": "🔵",
                "activated": "🔵",
                "running": "🟢",
                "paused": "🟡",
                "failed": "🔴"
            }.get(deployment_status.status, "⚪")
            
            # Create bot card content
            card_content = f"""
{status_emoji} {deployment_status.bot_name}

🏪 Market: {deployment_status.market_tag}
💳 Account: {deployment_status.account_id[:8]}
📅 Created: {deployment_status.creation_timestamp.strftime('%H:%M:%S')}

{self._format_bot_performance(deployment_status.performance_data)}
            """.strip()
            
            # Create the card
            card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title=f"Bot {deployment_status.bot_id[:8]}",
                content=card_content,
                x=x, y=y,
                width=600, height=250,
                style=self._get_bot_card_style(deployment_status.status)
            )
            
            # Create action buttons
            self._create_bot_action_buttons(board_id, deployment_status, x, y + 200)
            
            # Store item references
            if deployment_status.bot_id not in self.board_items:
                self.board_items[deployment_status.bot_id] = {}
            
            self.board_items[deployment_status.bot_id]['card'] = card_id
            
        except Exception as e:
            logger.error(f"Failed to create bot card for {deployment_status.bot_id}: {e}")
    
    def _create_bot_action_buttons(self, board_id: str, deployment_status: BotDeploymentStatus, x: float, y: float):
        """Create action buttons for bot management"""
        try:
            # Activate button
            activate_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=x, y=y,
                width=100, height=40,
                content="▶️ Activate",
                style={
                    "backgroundColor": "#28A745",
                    "color": "#FFFFFF",
                    "fontSize": 11,
                    "fontWeight": "bold"
                }
            )
            
            # Pause button
            pause_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=x + 110, y=y,
                width=100, height=40,
                content="⏸️ Pause",
                style={
                    "backgroundColor": "#FF9800",
                    "color": "#FFFFFF",
                    "fontSize": 11,
                    "fontWeight": "bold"
                }
            )
            
            # Deactivate button
            deactivate_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=x + 220, y=y,
                width=100, height=40,
                content="⏹️ Stop",
                style={
                    "backgroundColor": "#DC3545",
                    "color": "#FFFFFF",
                    "fontSize": 11,
                    "fontWeight": "bold"
                }
            )
            
            # View performance button
            performance_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=x + 330, y=y,
                width=100, height=40,
                content="📊 Stats",
                style={
                    "backgroundColor": "#007ACC",
                    "color": "#FFFFFF",
                    "fontSize": 11,
                    "fontWeight": "bold"
                }
            )
            
            # Store button references
            self.board_items[deployment_status.bot_id]['activate_btn'] = activate_btn_id
            self.board_items[deployment_status.bot_id]['pause_btn'] = pause_btn_id
            self.board_items[deployment_status.bot_id]['deactivate_btn'] = deactivate_btn_id
            self.board_items[deployment_status.bot_id]['performance_btn'] = performance_btn_id
            
        except Exception as e:
            logger.error(f"Failed to create action buttons for {deployment_status.bot_id}: {e}")
    
    def _format_bot_performance(self, performance: Optional[Dict[str, Any]]) -> str:
        """Format bot performance data for display"""
        if not performance:
            return "📈 No performance data available"
        
        roi = performance.get('roi', 0)
        win_rate = performance.get('win_rate', 0)
        trades = performance.get('trades', 0)
        drawdown = performance.get('drawdown', 0)
        
        return f"""
📈 ROI: {roi:.1f}%
🎯 Win Rate: {win_rate:.1%}
📊 Trades: {trades}
📉 Drawdown: {drawdown:.1f}%
        """.strip()
    
    def _get_bot_card_style(self, status: str) -> Dict[str, Any]:
        """Get card style based on bot status"""
        status_colors = {
            "created": {"backgroundColor": "#F5F5F5", "borderColor": "#9E9E9E"},
            "configured": {"backgroundColor": "#E3F2FD", "borderColor": "#2196F3"},
            "activated": {"backgroundColor": "#E8F5E8", "borderColor": "#4CAF50"},
            "running": {"backgroundColor": "#E8F5E8", "borderColor": "#4CAF50"},
            "paused": {"backgroundColor": "#FFF3E0", "borderColor": "#FF9800"},
            "failed": {"backgroundColor": "#FFEBEE", "borderColor": "#F44336"}
        }
        
        return status_colors.get(status, {"backgroundColor": "#F5F5F5", "borderColor": "#9E9E9E"})
    
    def _activate_bot(self, bot_id: str, board_id: str) -> bool:
        """Activate a bot and update status"""
        try:
            if bot_id not in self.deployed_bots:
                logger.warning(f"Bot {bot_id} not in deployment tracking")
                return False
            
            # Activate bot via API
            success = self.analyzer.activate_bot(bot_id)
            
            if success:
                # Update deployment status
                self.deployed_bots[bot_id].status = "activated"
                self.deployed_bots[bot_id].activation_timestamp = datetime.now()
                
                # Update Miro board
                self._update_bot_card(board_id, self.deployed_bots[bot_id])
                
                logger.info(f"Activated bot {bot_id}")
                return True
            else:
                self.deployed_bots[bot_id].status = "failed"
                self.deployed_bots[bot_id].error_message = "Failed to activate"
                logger.error(f"Failed to activate bot {bot_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error activating bot {bot_id}: {e}")
            if bot_id in self.deployed_bots:
                self.deployed_bots[bot_id].status = "failed"
                self.deployed_bots[bot_id].error_message = str(e)
            return False
    
    def _update_bot_card(self, board_id: str, deployment_status: BotDeploymentStatus):
        """Update bot card on Miro board"""
        try:
            if deployment_status.bot_id not in self.board_items or 'card' not in self.board_items[deployment_status.bot_id]:
                logger.warning(f"No card found for bot {deployment_status.bot_id}")
                return
            
            card_id = self.board_items[deployment_status.bot_id]['card']
            
            # Create updated content
            status_emoji = {
                "created": "⚪",
                "configured": "🔵",
                "activated": "🔵",
                "running": "🟢",
                "paused": "🟡",
                "failed": "🔴"
            }.get(deployment_status.status, "⚪")
            
            card_content = f"""
{status_emoji} {deployment_status.bot_name}

🏪 Market: {deployment_status.market_tag}
💳 Account: {deployment_status.account_id[:8]}
📅 Created: {deployment_status.creation_timestamp.strftime('%H:%M:%S')}
{'🚀 Activated: ' + deployment_status.activation_timestamp.strftime('%H:%M:%S') if deployment_status.activation_timestamp else ''}

{self._format_bot_performance(deployment_status.performance_data)}
            """.strip()
            
            # Update card content and style
            self.miro_client.update_item(
                board_id=board_id,
                item_id=card_id,
                content=card_content,
                style=self._get_bot_card_style(deployment_status.status)
            )
            
        except Exception as e:
            logger.error(f"Failed to update bot card for {deployment_status.bot_id}: {e}")
    
    def update_bot_performance(self, bot_id: str, board_id: str) -> bool:
        """Update bot performance data and refresh Miro board"""
        try:
            if bot_id not in self.deployed_bots:
                logger.warning(f"Bot {bot_id} not in deployment tracking")
                return False
            
            # Get bot performance data
            try:
                bot_data = self.analyzer.get_bot_details(bot_id)
                if bot_data:
                    # Extract performance metrics
                    performance_data = {
                        'roi': getattr(bot_data, 'roi', 0),
                        'win_rate': getattr(bot_data, 'win_rate', 0),
                        'trades': getattr(bot_data, 'total_trades', 0),
                        'drawdown': getattr(bot_data, 'max_drawdown', 0)
                    }
                    
                    self.deployed_bots[bot_id].performance_data = performance_data
                    
                    # Update Miro board
                    self._update_bot_card(board_id, self.deployed_bots[bot_id])
                    
                    return True
                    
            except Exception as e:
                logger.warning(f"Could not get performance data for bot {bot_id}: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update bot performance for {bot_id}: {e}")
            return False
    
    def update_all_bots_performance(self, board_id: str) -> Dict[str, bool]:
        """Update performance data for all deployed bots"""
        results = {}
        
        for bot_id in self.deployed_bots.keys():
            results[bot_id] = self.update_bot_performance(bot_id, board_id)
            time.sleep(1)  # Rate limiting
        
        return results
    
    def get_deployment_summary(self) -> Dict[str, Any]:
        """Get summary of all bot deployments"""
        try:
            total_bots = len(self.deployed_bots)
            status_counts = {}
            
            for bot in self.deployed_bots.values():
                status = bot.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_bots": total_bots,
                "status_distribution": status_counts,
                "active_bots": status_counts.get("running", 0) + status_counts.get("activated", 0),
                "failed_bots": status_counts.get("failed", 0),
                "deployment_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment summary: {e}")
            return {"error": str(e)}
