"""
Dashboard Manager for Miro Integration

Centralized management of all Miro dashboards and integrations:
- Unified dashboard creation and management
- Real-time monitoring coordination
- Automated workflow orchestration
- Integration status tracking
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import time
import threading

from .client import MiroClient, MiroBoard
from .lab_monitor import LabMonitor, LabMonitorConfig
from .bot_deployment import BotDeploymentCenter, BotDeploymentConfig
from .report_generator import ReportGenerator, ReportConfig
from ..analysis import HaasAnalyzer, UnifiedCacheManager

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Configuration for dashboard management"""
    update_interval_minutes: int = 15
    enable_lab_monitoring: bool = True
    enable_bot_deployment: bool = True
    enable_automated_reporting: bool = True
    lab_monitoring_config: Optional[LabMonitorConfig] = None
    bot_deployment_config: Optional[BotDeploymentConfig] = None
    report_config: Optional[ReportConfig] = None


@dataclass
class DashboardStatus:
    """Status of dashboard components"""
    dashboard_id: str
    lab_monitor_active: bool = False
    bot_deployment_active: bool = False
    reporting_active: bool = False
    last_update: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None


class DashboardManager:
    """Centralized dashboard management for Miro integration"""
    
    def __init__(self, miro_client: MiroClient, analyzer: HaasAnalyzer,
                 config: Optional[DashboardConfig] = None):
        """
        Initialize dashboard manager
        
        Args:
            miro_client: Miro API client
            analyzer: HaasAnalyzer instance
            config: Dashboard configuration
        """
        self.miro_client = miro_client
        self.analyzer = analyzer
        self.config = config or DashboardConfig()
        
        # Initialize components
        self.lab_monitor = LabMonitor(
            miro_client, 
            analyzer, 
            self.config.lab_monitoring_config or LabMonitorConfig()
        )
        
        self.bot_deployment = BotDeploymentCenter(
            miro_client,
            analyzer,
            self.config.bot_deployment_config or BotDeploymentConfig()
        )
        
        self.report_generator = ReportGenerator(
            miro_client,
            analyzer,
            self.config.report_config or ReportConfig()
        )
        
        # Dashboard tracking
        self.dashboards: Dict[str, DashboardStatus] = {}
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        
    def create_comprehensive_dashboard(self, dashboard_name: str = None) -> Optional[MiroBoard]:
        """Create a comprehensive dashboard with all components"""
        try:
            if not dashboard_name:
                dashboard_name = f"pyHaasAPI Dashboard - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create main dashboard board
            dashboard = self.miro_client.create_board(
                name=dashboard_name,
                description="Comprehensive pyHaasAPI monitoring and management dashboard"
            )
            
            if dashboard:
                logger.info(f"Created comprehensive dashboard: {dashboard.id}")
                self._setup_comprehensive_dashboard(dashboard.id)
                
                # Initialize dashboard status
                self.dashboards[dashboard.id] = DashboardStatus(
                    dashboard_id=dashboard.id,
                    last_update=datetime.now()
                )
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to create comprehensive dashboard: {e}")
            return None
    
    def _setup_comprehensive_dashboard(self, board_id: str):
        """Set up the comprehensive dashboard layout"""
        try:
            # Create main header
            header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🚀 pyHaasAPI Comprehensive Dashboard",
                x=0, y=-1000,
                width=1400, height=100,
                style={"fontSize": 28, "fontWeight": "bold", "textAlign": "center"}
            )
            
            # Create status indicator
            status_id = self.miro_client.create_text_item(
                board_id=board_id,
                text=f"🟢 System Online | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                x=0, y=-900,
                width=600, height=40,
                style={"fontSize": 14, "textAlign": "center", "color": "#28A745"}
            )
            
            # Create navigation section
            self._create_navigation_section(board_id)
            
            # Create lab monitoring section
            if self.config.enable_lab_monitoring:
                self._create_lab_monitoring_section(board_id)
            
            # Create bot deployment section
            if self.config.enable_bot_deployment:
                self._create_bot_deployment_section(board_id)
            
            # Create reporting section
            if self.config.enable_automated_reporting:
                self._create_reporting_section(board_id)
            
            # Create system overview section
            self._create_system_overview_section(board_id)
            
            logger.info(f"Set up comprehensive dashboard layout for {board_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup comprehensive dashboard layout: {e}")
    
    def _create_navigation_section(self, board_id: str):
        """Create navigation section with quick access buttons"""
        try:
            # Navigation header
            nav_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🧭 Quick Navigation",
                x=-1400, y=-800,
                width=300, height=50,
                style={"fontSize": 18, "fontWeight": "bold"}
            )
            
            # Quick action buttons
            buttons = [
                ("📊 Analyze All Labs", "#007ACC", -1400, -700),
                ("🤖 Mass Bot Creator", "#28A745", -1400, -600),
                ("📈 Generate Reports", "#FF9800", -1400, -500),
                ("⚙️ System Status", "#6C757D", -1400, -400),
                ("🔄 Refresh All", "#9C27B0", -1400, -300)
            ]
            
            for text, color, x, y in buttons:
                self.miro_client.create_shape_item(
                    board_id=board_id,
                    shape_type="round_rectangle",
                    x=x, y=y,
                    width=250, height=50,
                    content=text,
                    style={
                        "backgroundColor": color,
                        "color": "#FFFFFF",
                        "fontSize": 12,
                        "fontWeight": "bold"
                    }
                )
            
        except Exception as e:
            logger.error(f"Failed to create navigation section: {e}")
    
    def _create_lab_monitoring_section(self, board_id: str):
        """Create lab monitoring section"""
        try:
            # Lab monitoring header
            lab_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🧪 Lab Monitoring",
                x=-1000, y=-800,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold", "backgroundColor": "#E3F2FD"}
            )
            
            # Lab status summary
            lab_summary_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 Lab Status Summary\n\n🟢 Active Labs: 0\n🟡 Paused Labs: 0\n🔴 Failed Labs: 0\n✅ Completed Labs: 0",
                x=-1000, y=-700,
                width=400, height=150,
                style={"fontSize": 14, "backgroundColor": "#F5F5F5"}
            )
            
            # Lab monitoring controls
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=-1000, y=-500,
                width=180, height=40,
                content="📊 Add Lab",
                style={
                    "backgroundColor": "#007ACC",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=-800, y=-500,
                width=180, height=40,
                content="🔄 Refresh",
                style={
                    "backgroundColor": "#28A745",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create lab monitoring section: {e}")
    
    def _create_bot_deployment_section(self, board_id: str):
        """Create bot deployment section"""
        try:
            # Bot deployment header
            bot_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🤖 Bot Deployment",
                x=-500, y=-800,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold", "backgroundColor": "#E8F5E8"}
            )
            
            # Bot status summary
            bot_summary_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 Bot Status Summary\n\n🟢 Running Bots: 0\n🟡 Paused Bots: 0\n🔴 Failed Bots: 0\n⚪ Created Bots: 0",
                x=-500, y=-700,
                width=400, height=150,
                style={"fontSize": 14, "backgroundColor": "#F5F5F5"}
            )
            
            # Bot deployment controls
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=-500, y=-500,
                width=180, height=40,
                content="🚀 Create Bots",
                style={
                    "backgroundColor": "#28A745",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=-300, y=-500,
                width=180, height=40,
                content="⚙️ Manage",
                style={
                    "backgroundColor": "#6C757D",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create bot deployment section: {e}")
    
    def _create_reporting_section(self, board_id: str):
        """Create reporting section"""
        try:
            # Reporting header
            report_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 Automated Reports",
                x=0, y=-800,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold", "backgroundColor": "#FFF3E0"}
            )
            
            # Report status summary
            report_summary_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 Report Status\n\n📈 Lab Analysis: Ready\n🤖 Bot Performance: Ready\n⚙️ System Status: Ready\n🔄 Next Update: --:--",
                x=0, y=-700,
                width=400, height=150,
                style={"fontSize": 14, "backgroundColor": "#F5F5F5"}
            )
            
            # Report controls
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=0, y=-500,
                width=180, height=40,
                content="📊 Generate",
                style={
                    "backgroundColor": "#FF9800",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=200, y=-500,
                width=180, height=40,
                content="⚙️ Schedule",
                style={
                    "backgroundColor": "#9C27B0",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create reporting section: {e}")
    
    def _create_system_overview_section(self, board_id: str):
        """Create system overview section"""
        try:
            # System overview header
            system_header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="⚙️ System Overview",
                x=500, y=-800,
                width=400, height=50,
                style={"fontSize": 18, "fontWeight": "bold", "backgroundColor": "#F3E5F5"}
            )
            
            # System status summary
            system_summary_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 System Status\n\n🔗 API: Connected\n💾 Cache: Active\n📊 Database: Healthy\n🔄 Services: Running",
                x=500, y=-700,
                width=400, height=150,
                style={"fontSize": 14, "backgroundColor": "#F5F5F5"}
            )
            
            # System controls
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=500, y=-500,
                width=180, height=40,
                content="🔄 Refresh",
                style={
                    "backgroundColor": "#28A745",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
            self.miro_client.create_shape_item(
                board_id=board_id,
                shape_type="round_rectangle",
                x=700, y=-500,
                width=180, height=40,
                content="📊 Health Check",
                style={
                    "backgroundColor": "#007ACC",
                    "color": "#FFFFFF",
                    "fontSize": 12,
                    "fontWeight": "bold"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create system overview section: {e}")
    
    def start_lab_monitoring(self, board_id: str, lab_ids: List[str]) -> bool:
        """Start lab monitoring for specified labs"""
        try:
            if not self.config.enable_lab_monitoring:
                logger.warning("Lab monitoring is disabled")
                return False
            
            # Add labs to monitoring
            for lab_id in lab_ids:
                self.lab_monitor.add_lab_to_monitoring(lab_id, board_id)
            
            # Start monitoring thread
            def monitoring_loop():
                self.lab_monitor.start_monitoring(board_id)
            
            monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
            monitoring_thread.start()
            
            self.monitoring_threads[f"{board_id}_lab_monitor"] = monitoring_thread
            
            # Update dashboard status
            if board_id in self.dashboards:
                self.dashboards[board_id].lab_monitor_active = True
                self.dashboards[board_id].last_update = datetime.now()
            
            logger.info(f"Started lab monitoring for {len(lab_ids)} labs on board {board_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start lab monitoring: {e}")
            return False
    
    def start_automated_reporting(self, board_id: str) -> bool:
        """Start automated reporting"""
        try:
            if not self.config.enable_automated_reporting:
                logger.warning("Automated reporting is disabled")
                return False
            
            # Start reporting thread
            def reporting_loop():
                self.report_generator.start_automated_reporting(board_id)
            
            reporting_thread = threading.Thread(target=reporting_loop, daemon=True)
            reporting_thread.start()
            
            self.monitoring_threads[f"{board_id}_reporting"] = reporting_thread
            
            # Update dashboard status
            if board_id in self.dashboards:
                self.dashboards[board_id].reporting_active = True
                self.dashboards[board_id].last_update = datetime.now()
            
            logger.info(f"Started automated reporting for board {board_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start automated reporting: {e}")
            return False
    
    def create_bots_from_lab(self, board_id: str, lab_id: str, 
                           top_count: int = 5, activate: bool = False) -> List[Any]:
        """Create bots from lab analysis"""
        try:
            if not self.config.enable_bot_deployment:
                logger.warning("Bot deployment is disabled")
                return []
            
            # Create bots using bot deployment center
            bot_results = self.bot_deployment.create_bots_from_lab_analysis(
                lab_id, board_id, top_count, activate
            )
            
            # Update dashboard status
            if board_id in self.dashboards:
                self.dashboards[board_id].bot_deployment_active = True
                self.dashboards[board_id].last_update = datetime.now()
            
            logger.info(f"Created {len(bot_results)} bots from lab {lab_id}")
            return bot_results
            
        except Exception as e:
            logger.error(f"Failed to create bots from lab {lab_id}: {e}")
            return []
    
    def update_dashboard_status(self, board_id: str) -> bool:
        """Update dashboard status and refresh all components"""
        try:
            if board_id not in self.dashboards:
                logger.warning(f"Dashboard {board_id} not found")
                return False
            
            dashboard_status = self.dashboards[board_id]
            
            # Update lab monitoring if active
            if dashboard_status.lab_monitor_active:
                try:
                    self.lab_monitor.update_all_labs(board_id)
                except Exception as e:
                    logger.error(f"Failed to update lab monitoring: {e}")
                    dashboard_status.error_count += 1
                    dashboard_status.last_error = str(e)
            
            # Update bot deployment if active
            if dashboard_status.bot_deployment_active:
                try:
                    self.bot_deployment.update_all_bots_performance(board_id)
                except Exception as e:
                    logger.error(f"Failed to update bot deployment: {e}")
                    dashboard_status.error_count += 1
                    dashboard_status.last_error = str(e)
            
            # Update reporting if active
            if dashboard_status.reporting_active:
                try:
                    self.report_generator.generate_comprehensive_report(board_id)
                except Exception as e:
                    logger.error(f"Failed to update reporting: {e}")
                    dashboard_status.error_count += 1
                    dashboard_status.last_error = str(e)
            
            # Update dashboard status
            dashboard_status.last_update = datetime.now()
            
            logger.info(f"Updated dashboard status for {board_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update dashboard status: {e}")
            return False
    
    def get_dashboard_status(self, board_id: str) -> Optional[DashboardStatus]:
        """Get current dashboard status"""
        return self.dashboards.get(board_id)
    
    def get_all_dashboard_statuses(self) -> Dict[str, DashboardStatus]:
        """Get status of all dashboards"""
        return self.dashboards.copy()
    
    def stop_dashboard_monitoring(self, board_id: str) -> bool:
        """Stop all monitoring for a dashboard"""
        try:
            # Stop monitoring threads
            for thread_name, thread in self.monitoring_threads.items():
                if board_id in thread_name:
                    # Note: Threads are daemon threads, so they'll stop when main process stops
                    # In a real implementation, you'd want proper thread management
                    pass
            
            # Update dashboard status
            if board_id in self.dashboards:
                self.dashboards[board_id].lab_monitor_active = False
                self.dashboards[board_id].bot_deployment_active = False
                self.dashboards[board_id].reporting_active = False
                self.dashboards[board_id].last_update = datetime.now()
            
            logger.info(f"Stopped monitoring for dashboard {board_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop dashboard monitoring: {e}")
            return False
    
    def start_comprehensive_monitoring(self, board_id: str, lab_ids: List[str]) -> bool:
        """Start comprehensive monitoring for all components"""
        try:
            logger.info(f"Starting comprehensive monitoring for board {board_id}")
            
            # Start lab monitoring
            if self.config.enable_lab_monitoring and lab_ids:
                self.start_lab_monitoring(board_id, lab_ids)
            
            # Start automated reporting
            if self.config.enable_automated_reporting:
                self.start_automated_reporting(board_id)
            
            # Start dashboard status updates
            def dashboard_update_loop():
                while True:
                    try:
                        self.update_dashboard_status(board_id)
                        time.sleep(self.config.update_interval_minutes * 60)
                    except Exception as e:
                        logger.error(f"Error in dashboard update loop: {e}")
                        time.sleep(60)
            
            dashboard_thread = threading.Thread(target=dashboard_update_loop, daemon=True)
            dashboard_thread.start()
            
            self.monitoring_threads[f"{board_id}_dashboard"] = dashboard_thread
            
            logger.info(f"Started comprehensive monitoring for board {board_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start comprehensive monitoring: {e}")
            return False
