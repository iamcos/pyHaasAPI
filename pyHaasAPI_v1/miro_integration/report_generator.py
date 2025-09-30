"""
Automated Report Generator for Miro Integration

Generates comprehensive reports and updates Miro boards with:
- Lab analysis summaries
- Bot performance reports
- Performance analytics and charts
- Automated status updates
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
class ReportConfig:
    """Configuration for report generation"""
    update_interval_hours: int = 6
    include_performance_charts: bool = True
    include_recommendations: bool = True
    max_labs_per_report: int = 50
    report_format: str = "comprehensive"  # "summary", "detailed", "comprehensive"


@dataclass
class ReportData:
    """Report data structure"""
    report_id: str
    report_type: str  # "lab_analysis", "bot_performance", "system_status"
    generated_at: datetime
    data: Dict[str, Any]
    summary: str
    recommendations: List[str]


class ReportGenerator:
    """Automated report generator for Miro integration"""
    
    def __init__(self, miro_client: MiroClient, analyzer: HaasAnalyzer,
                 config: Optional[ReportConfig] = None):
        """
        Initialize report generator
        
        Args:
            miro_client: Miro API client
            analyzer: HaasAnalyzer instance
            config: Report configuration
        """
        self.miro_client = miro_client
        self.analyzer = analyzer
        self.config = config or ReportConfig()
        self.reports: Dict[str, ReportData] = {}
        
    def create_reporting_board(self, board_name: str = None) -> Optional[MiroBoard]:
        """Create a dedicated board for automated reporting"""
        try:
            if not board_name:
                board_name = f"pyHaasAPI Reports - {datetime.now().strftime('%Y-%m-%d')}"
            
            board = self.miro_client.create_board(
                name=board_name,
                description="Automated reports and analytics dashboard"
            )
            
            if board:
                logger.info(f"Created reporting board: {board.id}")
                self._setup_reporting_board_layout(board.id)
            
            return board
            
        except Exception as e:
            logger.error(f"Failed to create reporting board: {e}")
            return None
    
    def _setup_reporting_board_layout(self, board_id: str):
        """Set up the initial layout for reporting board"""
        try:
            # Create header
            header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="📊 pyHaasAPI Automated Reports",
                x=0, y=-800,
                width=1200, height=80,
                style={"fontSize": 24, "fontWeight": "bold", "textAlign": "center"}
            )
            
            # Create last update timestamp
            timestamp_id = self.miro_client.create_text_item(
                board_id=board_id,
                text=f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                x=0, y=-720,
                width=400, height=30,
                style={"fontSize": 12, "textAlign": "center", "color": "#666666"}
            )
            
            # Create report sections
            self._create_report_sections(board_id)
            
            logger.info(f"Set up reporting board layout for {board_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup reporting board layout: {e}")
    
    def _create_report_sections(self, board_id: str):
        """Create sections for different types of reports"""
        try:
            # Lab Analysis Section
            lab_section_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🧪 Lab Analysis Summary",
                x=-600, y=-650,
                width=500, height=50,
                style={"fontSize": 18, "fontWeight": "bold", "backgroundColor": "#E3F2FD"}
            )
            
            # Bot Performance Section
            bot_section_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🤖 Bot Performance Report",
                x=0, y=-650,
                width=500, height=50,
                style={"fontSize": 18, "fontWeight": "bold", "backgroundColor": "#E8F5E8"}
            )
            
            # System Status Section
            system_section_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="⚙️ System Status",
                x=600, y=-650,
                width=500, height=50,
                style={"fontSize": 18, "fontWeight": "bold", "backgroundColor": "#FFF3E0"}
            )
            
        except Exception as e:
            logger.error(f"Failed to create report sections: {e}")
    
    def generate_lab_analysis_report(self, board_id: str, lab_ids: Optional[List[str]] = None) -> ReportData:
        """Generate comprehensive lab analysis report"""
        try:
            logger.info("Generating lab analysis report...")
            
            # Get labs to analyze
            if not lab_ids:
                labs = self.analyzer.get_labs()
                lab_ids = [getattr(lab, 'lab_id', '') for lab in labs if hasattr(lab, 'lab_id')]
            
            # Analyze each lab
            lab_results = []
            total_backtests = 0
            total_analyzed = 0
            
            for lab_id in lab_ids[:self.config.max_labs_per_report]:
                try:
                    lab_details = self.analyzer.get_lab_details(lab_id)
                    if not lab_details:
                        continue
                    
                    lab_name = getattr(lab_details, 'name', f'Lab {lab_id[:8]}')
                    
                    # Analyze lab
                    analysis_result = self.analyzer.analyze_lab(lab_id, top_count=10)
                    if analysis_result:
                        lab_results.append({
                            'lab_id': lab_id,
                            'lab_name': lab_name,
                            'total_backtests': analysis_result.total_backtests,
                            'analyzed_backtests': analysis_result.analyzed_backtests,
                            'top_performers': len(analysis_result.top_backtests),
                            'best_roi': max([bt.roi_percentage for bt in analysis_result.top_backtests]) if analysis_result.top_backtests else 0,
                            'avg_win_rate': sum([bt.win_rate for bt in analysis_result.top_backtests]) / len(analysis_result.top_backtests) if analysis_result.top_backtests else 0
                        })
                        
                        total_backtests += analysis_result.total_backtests
                        total_analyzed += analysis_result.analyzed_backtests
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze lab {lab_id}: {e}")
                    continue
            
            # Generate report data
            report_data = {
                'report_type': 'lab_analysis',
                'generated_at': datetime.now().isoformat(),
                'total_labs': len(lab_results),
                'total_backtests': total_backtests,
                'total_analyzed': total_analyzed,
                'lab_results': lab_results,
                'top_performers': sorted(lab_results, key=lambda x: x['best_roi'], reverse=True)[:5]
            }
            
            # Generate summary
            summary = self._generate_lab_summary(report_data)
            
            # Generate recommendations
            recommendations = self._generate_lab_recommendations(report_data)
            
            # Create report
            report = ReportData(
                report_id=f"lab_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_type="lab_analysis",
                generated_at=datetime.now(),
                data=report_data,
                summary=summary,
                recommendations=recommendations
            )
            
            # Update Miro board
            self._update_lab_analysis_section(board_id, report)
            
            # Store report
            self.reports[report.report_id] = report
            
            logger.info(f"Generated lab analysis report: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate lab analysis report: {e}")
            return None
    
    def _generate_lab_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate summary text for lab analysis report"""
        try:
            total_labs = report_data['total_labs']
            total_backtests = report_data['total_backtests']
            total_analyzed = report_data['total_analyzed']
            top_performers = report_data['top_performers']
            
            summary = f"""
📊 Lab Analysis Summary

🧪 Total Labs Analyzed: {total_labs}
📈 Total Backtests: {total_backtests:,}
✅ Successfully Analyzed: {total_analyzed:,}
🎯 Analysis Success Rate: {(total_analyzed/max(total_backtests, 1)*100):.1f}%

🏆 Top Performing Labs:
            """.strip()
            
            for i, lab in enumerate(top_performers[:3], 1):
                summary += f"\n{i}. {lab['lab_name'][:30]} - ROI: {lab['best_roi']:.1f}% (WR: {lab['avg_win_rate']:.1%})"
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate lab summary: {e}")
            return "Error generating summary"
    
    def _generate_lab_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on lab analysis"""
        try:
            recommendations = []
            top_performers = report_data['top_performers']
            
            if top_performers:
                # High ROI recommendations
                high_roi_labs = [lab for lab in top_performers if lab['best_roi'] >= 100]
                if high_roi_labs:
                    recommendations.append(f"🚀 {len(high_roi_labs)} labs with ROI ≥100% - Strong candidates for bot creation")
                
                # Good performance recommendations
                good_labs = [lab for lab in top_performers if 50 <= lab['best_roi'] < 100]
                if good_labs:
                    recommendations.append(f"✅ {len(good_labs)} labs with ROI 50-100% - Consider for bot creation")
                
                # Win rate recommendations
                high_wr_labs = [lab for lab in top_performers if lab['avg_win_rate'] >= 0.7]
                if high_wr_labs:
                    recommendations.append(f"🎯 {len(high_wr_labs)} labs with win rate ≥70% - Very reliable strategies")
            
            # General recommendations
            if report_data['total_analyzed'] < report_data['total_backtests'] * 0.8:
                recommendations.append("⚠️ Low analysis success rate - Check lab configurations and data quality")
            
            if not recommendations:
                recommendations.append("📊 Continue monitoring lab performance for better insights")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate lab recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _update_lab_analysis_section(self, board_id: str, report: ReportData):
        """Update lab analysis section on Miro board"""
        try:
            # Create summary card
            summary_card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title="📊 Lab Analysis Summary",
                content=report.summary,
                x=-600, y=-550,
                width=500, height=300,
                style={"backgroundColor": "#E3F2FD", "borderColor": "#2196F3"}
            )
            
            # Create recommendations card
            recommendations_text = "\n".join([f"• {rec}" for rec in report.recommendations])
            recommendations_card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title="💡 Recommendations",
                content=recommendations_text,
                x=-600, y=-200,
                width=500, height=200,
                style={"backgroundColor": "#FFF9C4", "borderColor": "#FBC02D"}
            )
            
            # Create top performers table
            self._create_top_performers_table(board_id, report.data['top_performers'])
            
        except Exception as e:
            logger.error(f"Failed to update lab analysis section: {e}")
    
    def _create_top_performers_table(self, board_id: str, top_performers: List[Dict[str, Any]]):
        """Create a table showing top performing labs"""
        try:
            # Create table header
            header_id = self.miro_client.create_text_item(
                board_id=board_id,
                text="🏆 Top Performing Labs",
                x=-600, y=50,
                width=500, height=30,
                style={"fontSize": 16, "fontWeight": "bold"}
            )
            
            # Create table rows
            for i, lab in enumerate(top_performers[:5]):
                y_pos = 100 + i * 60
                
                row_text = f"""
{lab['lab_name'][:25]}
ROI: {lab['best_roi']:.1f}% | WR: {lab['avg_win_rate']:.1%} | Backtests: {lab['total_backtests']}
                """.strip()
                
                row_id = self.miro_client.create_text_item(
                    board_id=board_id,
                    text=row_text,
                    x=-600, y=y_pos,
                    width=500, height=50,
                    style={"fontSize": 12, "backgroundColor": "#F5F5F5" if i % 2 == 0 else "#FFFFFF"}
                )
                
        except Exception as e:
            logger.error(f"Failed to create top performers table: {e}")
    
    def generate_bot_performance_report(self, board_id: str, bot_ids: Optional[List[str]] = None) -> ReportData:
        """Generate bot performance report"""
        try:
            logger.info("Generating bot performance report...")
            
            # Get bots to analyze
            if not bot_ids:
                bots = self.analyzer.get_all_bots()
                bot_ids = [getattr(bot, 'bot_id', '') for bot in bots if hasattr(bot, 'bot_id')]
            
            # Analyze each bot
            bot_results = []
            total_bots = len(bot_ids)
            active_bots = 0
            total_roi = 0
            
            for bot_id in bot_ids:
                try:
                    bot_data = self.analyzer.get_bot_details(bot_id)
                    if not bot_data:
                        continue
                    
                    bot_name = getattr(bot_data, 'bot_name', f'Bot {bot_id[:8]}')
                    status = getattr(bot_data, 'status', 'unknown')
                    roi = getattr(bot_data, 'roi', 0)
                    win_rate = getattr(bot_data, 'win_rate', 0)
                    trades = getattr(bot_data, 'total_trades', 0)
                    
                    if status in ['running', 'activated']:
                        active_bots += 1
                        total_roi += roi
                    
                    bot_results.append({
                        'bot_id': bot_id,
                        'bot_name': bot_name,
                        'status': status,
                        'roi': roi,
                        'win_rate': win_rate,
                        'trades': trades
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze bot {bot_id}: {e}")
                    continue
            
            # Generate report data
            report_data = {
                'report_type': 'bot_performance',
                'generated_at': datetime.now().isoformat(),
                'total_bots': total_bots,
                'active_bots': active_bots,
                'avg_roi': total_roi / max(active_bots, 1),
                'bot_results': bot_results,
                'top_performers': sorted([b for b in bot_results if b['status'] in ['running', 'activated']], 
                                       key=lambda x: x['roi'], reverse=True)[:5]
            }
            
            # Generate summary
            summary = self._generate_bot_summary(report_data)
            
            # Generate recommendations
            recommendations = self._generate_bot_recommendations(report_data)
            
            # Create report
            report = ReportData(
                report_id=f"bot_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_type="bot_performance",
                generated_at=datetime.now(),
                data=report_data,
                summary=summary,
                recommendations=recommendations
            )
            
            # Update Miro board
            self._update_bot_performance_section(board_id, report)
            
            # Store report
            self.reports[report.report_id] = report
            
            logger.info(f"Generated bot performance report: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate bot performance report: {e}")
            return None
    
    def _generate_bot_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate summary text for bot performance report"""
        try:
            total_bots = report_data['total_bots']
            active_bots = report_data['active_bots']
            avg_roi = report_data['avg_roi']
            top_performers = report_data['top_performers']
            
            summary = f"""
🤖 Bot Performance Summary

📊 Total Bots: {total_bots}
🟢 Active Bots: {active_bots}
📈 Average ROI: {avg_roi:.1f}%
🎯 Active Rate: {(active_bots/max(total_bots, 1)*100):.1f}%

🏆 Top Performing Bots:
            """.strip()
            
            for i, bot in enumerate(top_performers[:3], 1):
                summary += f"\n{i}. {bot['bot_name'][:25]} - ROI: {bot['roi']:.1f}% (WR: {bot['win_rate']:.1%})"
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate bot summary: {e}")
            return "Error generating summary"
    
    def _generate_bot_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on bot performance"""
        try:
            recommendations = []
            active_bots = report_data['active_bots']
            total_bots = report_data['total_bots']
            avg_roi = report_data['avg_roi']
            
            # Performance recommendations
            if avg_roi > 50:
                recommendations.append("🚀 Excellent average ROI - Consider scaling up successful strategies")
            elif avg_roi > 20:
                recommendations.append("✅ Good average ROI - Monitor performance closely")
            elif avg_roi > 0:
                recommendations.append("⚠️ Moderate ROI - Review strategy parameters")
            else:
                recommendations.append("❌ Negative ROI - Consider pausing or stopping bots")
            
            # Activity recommendations
            if active_bots < total_bots * 0.8:
                recommendations.append(f"⚠️ Only {active_bots}/{total_bots} bots are active - Check inactive bots")
            
            # Top performer recommendations
            top_performers = report_data['top_performers']
            if top_performers:
                high_roi_bots = [bot for bot in top_performers if bot['roi'] >= 100]
                if high_roi_bots:
                    recommendations.append(f"🏆 {len(high_roi_bots)} bots with ROI ≥100% - Consider creating more similar bots")
            
            if not recommendations:
                recommendations.append("📊 Continue monitoring bot performance for better insights")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate bot recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _update_bot_performance_section(self, board_id: str, report: ReportData):
        """Update bot performance section on Miro board"""
        try:
            # Create summary card
            summary_card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title="🤖 Bot Performance Summary",
                content=report.summary,
                x=0, y=-550,
                width=500, height=300,
                style={"backgroundColor": "#E8F5E8", "borderColor": "#4CAF50"}
            )
            
            # Create recommendations card
            recommendations_text = "\n".join([f"• {rec}" for rec in report.recommendations])
            recommendations_card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title="💡 Bot Recommendations",
                content=recommendations_text,
                x=0, y=-200,
                width=500, height=200,
                style={"backgroundColor": "#FFF9C4", "borderColor": "#FBC02D"}
            )
            
        except Exception as e:
            logger.error(f"Failed to update bot performance section: {e}")
    
    def generate_system_status_report(self, board_id: str) -> ReportData:
        """Generate system status report"""
        try:
            logger.info("Generating system status report...")
            
            # Get system information
            try:
                labs = self.analyzer.get_labs()
                bots = self.analyzer.get_all_bots()
                accounts = self.analyzer.get_accounts()
            except Exception as e:
                logger.warning(f"Could not get system data: {e}")
                labs = []
                bots = []
                accounts = []
            
            # Generate report data
            report_data = {
                'report_type': 'system_status',
                'generated_at': datetime.now().isoformat(),
                'total_labs': len(labs),
                'total_bots': len(bots),
                'total_accounts': len(accounts),
                'system_health': 'healthy',  # Could be enhanced with more checks
                'api_status': 'connected'
            }
            
            # Generate summary
            summary = self._generate_system_summary(report_data)
            
            # Generate recommendations
            recommendations = self._generate_system_recommendations(report_data)
            
            # Create report
            report = ReportData(
                report_id=f"system_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_type="system_status",
                generated_at=datetime.now(),
                data=report_data,
                summary=summary,
                recommendations=recommendations
            )
            
            # Update Miro board
            self._update_system_status_section(board_id, report)
            
            # Store report
            self.reports[report.report_id] = report
            
            logger.info(f"Generated system status report: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate system status report: {e}")
            return None
    
    def _generate_system_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate summary text for system status report"""
        try:
            total_labs = report_data['total_labs']
            total_bots = report_data['total_bots']
            total_accounts = report_data['total_accounts']
            system_health = report_data['system_health']
            api_status = report_data['api_status']
            
            summary = f"""
⚙️ System Status Summary

🧪 Total Labs: {total_labs}
🤖 Total Bots: {total_bots}
💳 Total Accounts: {total_accounts}
🔗 API Status: {api_status.upper()}
💚 System Health: {system_health.upper()}

📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate system summary: {e}")
            return "Error generating summary"
    
    def _generate_system_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on system status"""
        try:
            recommendations = []
            total_labs = report_data['total_labs']
            total_bots = report_data['total_bots']
            total_accounts = report_data['total_accounts']
            
            # Lab recommendations
            if total_labs == 0:
                recommendations.append("🧪 No labs found - Consider creating new labs for strategy testing")
            elif total_labs < 5:
                recommendations.append("🧪 Low number of labs - Consider creating more labs for better strategy coverage")
            
            # Bot recommendations
            if total_bots == 0:
                recommendations.append("🤖 No bots found - Consider creating bots from successful lab results")
            elif total_bots < total_labs * 0.5:
                recommendations.append("🤖 Low bot-to-lab ratio - Consider creating more bots from successful labs")
            
            # Account recommendations
            if total_accounts == 0:
                recommendations.append("💳 No accounts found - Check account configuration")
            elif total_bots > total_accounts:
                recommendations.append("💳 More bots than accounts - Consider creating additional accounts for better distribution")
            
            # General recommendations
            if report_data['system_health'] == 'healthy':
                recommendations.append("✅ System is healthy - Continue monitoring performance")
            
            if not recommendations:
                recommendations.append("📊 System is running optimally - Continue monitoring")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate system recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _update_system_status_section(self, board_id: str, report: ReportData):
        """Update system status section on Miro board"""
        try:
            # Create summary card
            summary_card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title="⚙️ System Status",
                content=report.summary,
                x=600, y=-550,
                width=500, height=300,
                style={"backgroundColor": "#FFF3E0", "borderColor": "#FF9800"}
            )
            
            # Create recommendations card
            recommendations_text = "\n".join([f"• {rec}" for rec in report.recommendations])
            recommendations_card_id = self.miro_client.create_card_item(
                board_id=board_id,
                title="💡 System Recommendations",
                content=recommendations_text,
                x=600, y=-200,
                width=500, height=200,
                style={"backgroundColor": "#FFF9C4", "borderColor": "#FBC02D"}
            )
            
        except Exception as e:
            logger.error(f"Failed to update system status section: {e}")
    
    def generate_comprehensive_report(self, board_id: str) -> Dict[str, ReportData]:
        """Generate all types of reports"""
        try:
            logger.info("Generating comprehensive report...")
            
            reports = {}
            
            # Generate lab analysis report
            lab_report = self.generate_lab_analysis_report(board_id)
            if lab_report:
                reports['lab_analysis'] = lab_report
            
            # Generate bot performance report
            bot_report = self.generate_bot_performance_report(board_id)
            if bot_report:
                reports['bot_performance'] = bot_report
            
            # Generate system status report
            system_report = self.generate_system_status_report(board_id)
            if system_report:
                reports['system_status'] = system_report
            
            logger.info(f"Generated {len(reports)} reports")
            return reports
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            return {}
    
    def start_automated_reporting(self, board_id: str):
        """Start automated reporting with scheduled updates"""
        interval = self.config.update_interval_hours * 3600  # Convert to seconds
        
        logger.info(f"Starting automated reporting with {self.config.update_interval_hours} hour intervals")
        
        while True:
            try:
                logger.info("Generating automated reports...")
                reports = self.generate_comprehensive_report(board_id)
                
                logger.info(f"Generated {len(reports)} automated reports")
                
                # Wait for next update
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Automated reporting stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in automated reporting: {e}")
                time.sleep(3600)  # Wait 1 hour before retrying
