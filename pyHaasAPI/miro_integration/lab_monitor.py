"""
Lab Monitoring Integration with Miro

Provides real-time lab progression monitoring with Miro board updates:
- Live lab status tracking
- Performance metrics visualization
- Automated progress reports
- Interactive lab management
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import time

from .client import MiroClient, MiroBoard, MiroItem
from ..analysis import HaasAnalyzer, UnifiedCacheManager
from ..analysis.models import LabAnalysisResult, BacktestAnalysis

logger = logging.getLogger(__name__)


@dataclass
class LabMonitorConfig:
    """Configuration for lab monitoring"""
    update_interval_minutes: int = 15
    max_labs_per_board: int = 20
    include_performance_charts: bool = True
    auto_create_bots: bool = False
    notification_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.notification_thresholds is None:
            self.notification_thresholds = {
                "min_roi": 50.0,
                "min_win_rate": 0.6,
                "max_drawdown": 20.0
            }


@dataclass
class LabStatus:
    """Current status of a lab"""
    lab_id: str
    lab_name: str
    status: str  # 'running', 'completed', 'failed', 'paused'
    progress_percentage: float
    total_backtests: int
    completed_backtests: int
    estimated_completion: Optional[datetime] = None
    last_update: datetime = None
    performance_summary: Optional[Dict[str, Any]] = None


class LabMonitor:
    """Real-time lab monitoring with Miro integration"""
    
    def __init__(self, miro_client: MiroClient, analyzer: HaasAnalyzer, 
                 config: Optional[LabMonitorConfig] = None):
        """
        Initialize lab monitor
        
        Args:
            miro_client: Miro API client
            analyzer: HaasAnalyzer instance
            config: Monitoring configuration
        """
        self.miro_client = miro_client
        self.analyzer = analyzer
        self.config = config or LabMonitorConfig()
        self.monitored_labs: Dict[str, LabStatus] = {}
        self.board_items: Dict[str, Dict[str, str]] = {}  # lab_id -> {item_type: item_id}
        
    def create_lab_monitoring_board(self, board_name: str = None) -> Optional[MiroBoard]:
        """Create a dedicated board for lab monitoring"""
        try:
            if not board_name:
                board_name = f"Lab Monitoring - {datetime.now().strftime('%Y-%m-%d')}"
            
            board = self.miro_client.create_board(
                name=board_name,
                description="Real-time lab progression monitoring and management"
            )
            
            if board:
                logger.info(f"Created lab monitoring board: {board.id}")
                self._setup_monitoring_board_layout(board.id)
            
            return board
            
        except Exception as e:
            logger.error(f"Failed to create lab monitoring board: {e}")
            return None
    
    def _setup_monitoring_board_layout(self, board_id: str):
        """Set up the initial layout for monitoring board"""
        try:
            # Create header
            header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🚀 pyHaasAPI Lab Monitoring Dashboard",
                x=0, y=-800,
                width=1200, height=80,
                style={"fontSize": 24, "fontWeight": "bold", "textAlign": "center"}
            )
            
            # Create status legend
            legend_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 Status Legend:\n🟢 Running | 🟡 Paused | 🔴 Failed | ✅ Completed",
                x=-1200, y=-700,
                width=300, height=100,
                style={"fontSize": 14, "fontWeight": "bold"}
            )
            
            # Create performance metrics header
            metrics_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📈 Performance Metrics",
                x=0, y=-600,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold"}
            )
            
            # Create lab list header
            labs_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🧪 Active Labs",
                x=-600, y=-600,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold"}
            )
            
            logger.info(f"Set up monitoring board layout for {board_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring board layout: {e}")
    
    def add_lab_to_monitoring(self, lab_id: str, board_id: str) -> bool:
        """Add a lab to monitoring with Miro board updates"""
        try:
            # Get lab details
            lab_details = self.analyzer.get_lab_details(lab_id)
            if not lab_details:
                logger.error(f"Could not get details for lab {lab_id}")
                return False
            
            lab_name = getattr(lab_details, 'name', f'Lab {lab_id[:8]}')
            
            # Create lab status
            lab_status = LabStatus(
                lab_id=lab_id,
                lab_name=lab_name,
                status="running",
                progress_percentage=0.0,
                total_backtests=0,
                completed_backtests=0,
                last_update=datetime.now()
            )
            
            self.monitored_labs[lab_id] = lab_status
            
            # Create lab card on Miro board
            self._create_lab_card(board_id, lab_status)
            
            logger.info(f"Added lab {lab_name} to monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add lab {lab_id} to monitoring: {e}")
            return False
    
    def _create_lab_card(self, board_id: str, lab_status: LabStatus):
        """Create a lab status card on the Miro board"""
        try:
            # Calculate position based on number of monitored labs
            lab_count = len(self.monitored_labs)
            x = -600 + (lab_count % 2) * 650
            y = -500 + (lab_count // 2) * 300
            
            # Create status indicator
            status_emoji = {
                "running": "🟢",
                "paused": "🟡", 
                "failed": "🔴",
                "completed": "✅"
            }.get(lab_status.status, "⚪")
            
            # Create lab card content
            card_content = f"""
{status_emoji} {lab_status.lab_name}

📊 Progress: {lab_status.progress_percentage:.1f}%
🧪 Backtests: {lab_status.completed_backtests}/{lab_status.total_backtests}
⏱️ Last Update: {lab_status.last_update.strftime('%H:%M:%S') if lab_status.last_update else 'Never'}

{self._format_performance_summary(lab_status.performance_summary)}
            """.strip()
            
            # Create the card
            card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title=f"Lab {lab_status.lab_id[:8]}",
                content=card_content,
                x=x, y=y,
                width=600, height=250,
                style=self._get_lab_card_style(lab_status.status)
            )
            
            # Create action buttons
            self._create_lab_action_buttons(board_id, lab_status, x, y + 200)
            
            # Store item references
            if lab_status.lab_id not in self.board_items:
                self.board_items[lab_status.lab_id] = {}
            
            self.board_items[lab_status.lab_id]['card'] = card_id
            
        except Exception as e:
            logger.error(f"Failed to create lab card for {lab_status.lab_id}: {e}")
    
    def _create_lab_action_buttons(self, board_id: str, lab_status: LabStatus, x: float, y: float):
        """Create action buttons for lab management"""
        try:
            # Analyze button
            analyze_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=x, y=y,
                width=120, height=40,
                content="📊 Analyze",
                style={
                    "backgroundColor": "#007ACC",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
            # Create bots button
            create_bots_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle", 
                x=x + 130, y=y,
                width=120, height=40,
                content="🤖 Create Bots",
                style={
                    "backgroundColor": "#28A745",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
            # View details button
            details_btn_id = self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=x + 260, y=y,
                width=120, height=40,
                content="👁️ Details",
                style={
                    "backgroundColor": "#6C757D",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
            # Store button references
            self.board_items[lab_status.lab_id]['analyze_btn'] = analyze_btn_id
            self.board_items[lab_status.lab_id]['create_bots_btn'] = create_bots_btn_id
            self.board_items[lab_status.lab_id]['details_btn'] = details_btn_id
            
        except Exception as e:
            logger.error(f"Failed to create action buttons for {lab_status.lab_id}: {e}")
    
    def _format_performance_summary(self, performance: Optional[Dict[str, Any]]) -> str:
        """Format performance summary for display"""
        if not performance:
            return "📈 No performance data available"
        
        roi = performance.get('roi_percentage', 0)
        win_rate = performance.get('win_rate', 0)
        trades = performance.get('total_trades', 0)
        
        return f"""
📈 ROI: {roi:.1f}%
🎯 Win Rate: {win_rate:.1%}
📊 Trades: {trades}
        """.strip()
    
    def _get_lab_card_style(self, status: str) -> Dict[str, Any]:
        """Get card style based on lab status"""
        status_colors = {
            "running": {"backgroundColor": "#E3F2FD", "borderColor": "#2196F3"},
            "paused": {"backgroundColor": "#FFF3E0", "borderColor": "#FF9800"},
            "failed": {"backgroundColor": "#FFEBEE", "borderColor": "#F44336"},
            "completed": {"backgroundColor": "#E8F5E8", "borderColor": "#4CAF50"}
        }
        
        return status_colors.get(status, {"backgroundColor": "#F5F5F5", "borderColor": "#9E9E9E"})
    
    def update_lab_status(self, lab_id: str, board_id: str) -> bool:
        """Update lab status and refresh Miro board"""
        try:
            if lab_id not in self.monitored_labs:
                logger.warning(f"Lab {lab_id} not in monitoring list")
                return False
            
            lab_status = self.monitored_labs[lab_id]
            
            # Get current lab details
            lab_details = self.analyzer.get_lab_details(lab_id)
            if not lab_details:
                logger.error(f"Could not get details for lab {lab_id}")
                return False
            
            # Update lab status
            lab_status.last_update = datetime.now()
            lab_status.status = getattr(lab_details, 'status', 'unknown')
            
            # Get backtest progress
            try:
                analysis_result = self.analyzer.analyze_lab(lab_id, top_count=10)
                if analysis_result:
                    lab_status.total_backtests = analysis_result.total_backtests
                    lab_status.completed_backtests = analysis_result.analyzed_backtests
                    lab_status.progress_percentage = (lab_status.completed_backtests / max(lab_status.total_backtests, 1)) * 100
                    
                    # Update performance summary
                    if analysis_result.top_backtests:
                        top_backtest = analysis_result.top_backtests[0]
                        lab_status.performance_summary = {
                            'roi_percentage': top_backtest.roi_percentage,
                            'win_rate': top_backtest.win_rate,
                            'total_trades': top_backtest.total_trades,
                            'max_drawdown': top_backtest.max_drawdown
                        }
            except Exception as e:
                logger.warning(f"Could not get analysis for lab {lab_id}: {e}")
            
            # Update Miro board
            self._update_lab_card(board_id, lab_status)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update lab status for {lab_id}: {e}")
            return False
    
    def _update_lab_card(self, board_id: str, lab_status: LabStatus):
        """Update lab card on Miro board"""
        try:
            if lab_status.lab_id not in self.board_items or 'card' not in self.board_items[lab_status.lab_id]:
                logger.warning(f"No card found for lab {lab_status.lab_id}")
                return
            
            card_id = self.board_items[lab_status.lab_id]['card']
            
            # Create updated content
            status_emoji = {
                "running": "🟢",
                "paused": "🟡",
                "failed": "🔴", 
                "completed": "✅"
            }.get(lab_status.status, "⚪")
            
            card_content = f"""
{status_emoji} {lab_status.lab_name}

📊 Progress: {lab_status.progress_percentage:.1f}%
🧪 Backtests: {lab_status.completed_backtests}/{lab_status.total_backtests}
⏱️ Last Update: {lab_status.last_update.strftime('%H:%M:%S') if lab_status.last_update else 'Never'}

{self._format_performance_summary(lab_status.performance_summary)}
            """.strip()
            
            # Update card content and style
            self.miro_client.update_item(
                board_id=board_id,
                item_id=card_id,
                content=card_content,
                style=self._get_lab_card_style(lab_status.status)
            )
            
        except Exception as e:
            logger.error(f"Failed to update lab card for {lab_status.lab_id}: {e}")
    
    def update_all_labs(self, board_id: str) -> Dict[str, bool]:
        """Update all monitored labs"""
        results = {}
        
        for lab_id in self.monitored_labs.keys():
            results[lab_id] = self.update_lab_status(lab_id, board_id)
            time.sleep(1)  # Rate limiting
        
        return results
    
    def start_monitoring(self, board_id: str, update_interval: Optional[int] = None):
        """Start continuous monitoring of all labs"""
        interval = update_interval or self.config.update_interval_minutes
        
        logger.info(f"Starting lab monitoring with {interval} minute intervals")
        
        while True:
            try:
                logger.info("Updating all monitored labs...")
                results = self.update_all_labs(board_id)
                
                successful_updates = sum(1 for success in results.values() if success)
                total_labs = len(results)
                
                logger.info(f"Updated {successful_updates}/{total_labs} labs successfully")
                
                # Wait for next update
                time.sleep(interval * 60)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_lab_recommendations(self, lab_id: str) -> Dict[str, Any]:
        """Get recommendations for a lab based on performance"""
        try:
            if lab_id not in self.monitored_labs:
                return {"error": "Lab not monitored"}
            
            lab_status = self.monitored_labs[lab_id]
            
            if not lab_status.performance_summary:
                return {"error": "No performance data available"}
            
            performance = lab_status.performance_summary
            recommendations = {
                "lab_id": lab_id,
                "lab_name": lab_status.lab_name,
                "recommendations": [],
                "risk_level": "UNKNOWN",
                "bot_creation_recommended": False
            }
            
            # Analyze performance and generate recommendations
            roi = performance.get('roi_percentage', 0)
            win_rate = performance.get('win_rate', 0)
            drawdown = performance.get('max_drawdown', 0)
            
            # ROI recommendations
            if roi >= 100:
                recommendations["recommendations"].append("🚀 Excellent ROI - Strong candidate for bot creation")
                recommendations["bot_creation_recommended"] = True
            elif roi >= 50:
                recommendations["recommendations"].append("✅ Good ROI - Consider bot creation")
                recommendations["bot_creation_recommended"] = True
            elif roi >= 20:
                recommendations["recommendations"].append("⚠️ Moderate ROI - Monitor closely")
            else:
                recommendations["recommendations"].append("❌ Low ROI - Not recommended for bot creation")
            
            # Win rate recommendations
            if win_rate >= 0.7:
                recommendations["recommendations"].append("🎯 High win rate - Very reliable strategy")
            elif win_rate >= 0.6:
                recommendations["recommendations"].append("✅ Good win rate - Reliable strategy")
            elif win_rate >= 0.5:
                recommendations["recommendations"].append("⚠️ Moderate win rate - Monitor performance")
            else:
                recommendations["recommendations"].append("❌ Low win rate - High risk strategy")
            
            # Drawdown recommendations
            if drawdown <= 10:
                recommendations["risk_level"] = "LOW"
                recommendations["recommendations"].append("🛡️ Low drawdown - Safe strategy")
            elif drawdown <= 20:
                recommendations["risk_level"] = "MEDIUM"
                recommendations["recommendations"].append("⚠️ Moderate drawdown - Monitor risk")
            else:
                recommendations["risk_level"] = "HIGH"
                recommendations["recommendations"].append("🚨 High drawdown - High risk strategy")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get recommendations for lab {lab_id}: {e}")
            return {"error": str(e)}
