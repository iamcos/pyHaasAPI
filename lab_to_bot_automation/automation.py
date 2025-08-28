#!/usr/bin/env python3
"""
Main Lab to Bot Automation Orchestrator

This module contains the main automation class that coordinates all phases
of the lab-to-bot conversion process.

Author: AI Assistant
Date: 2024
"""

import os
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from pyHaasAPI.api import RequestsExecutor

from .wfo_analyzer import WFOAnalyzer, WFOConfig, WFOMetrics, BotRecommendation
from .account_manager import AccountManager, AccountConfig, AccountInfo
from .bot_creation_engine import BotCreationEngine, BotCreationConfig, BotDeploymentResult


@dataclass
class AutomationConfig:
    """Configuration for the entire automation process"""
    lab_id: str
    max_backtests: int = 50
    wfo_config: WFOConfig = None
    account_config: AccountConfig = None
    bot_config: BotCreationConfig = None
    dry_run: bool = False
    verbose: bool = False
    output_dir: str = "automation_reports"


class LabToBotAutomation:
    """
    Main automation orchestrator for converting lab backtests to live trading bots.
    
    This class coordinates the entire workflow:
    1. WFO Analysis of backtests
    2. Account management and allocation
    3. Bot deployment and configuration
    """
    
    def __init__(self, executor: RequestsExecutor, config: AutomationConfig):
        """
        Initialize the automation system
        
        Args:
            executor: HaasOnline API executor
            config: Automation configuration
        """
        self.executor = executor
        self.config = config
        
        # Initialize components
        self.wfo_analyzer = WFOAnalyzer(executor, config.wfo_config)
        self.account_manager = AccountManager(executor, config.account_config)
        self.bot_engine = BotCreationEngine(executor, config.bot_config)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Results storage
        self.analysis_results: List[WFOMetrics] = []
        self.recommendations: List[BotRecommendation] = []
        self.deployment_results: List[BotDeploymentResult] = []
        
    def _setup_logger(self):
        """Setup logging for the automation system"""
        logger = logging.getLogger(f"LabToBot-{id(self)}")
        logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def execute_automation(self) -> bool:
        """
        Execute the complete automation workflow
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("🚀 Starting Lab to Bot Automation")
            self.logger.info(f"📊 Lab ID: {self.config.lab_id}")
            self.logger.info(f"🔍 Dry Run: {self.config.dry_run}")
            
            # Phase 1: WFO Analysis
            self.logger.info("\n📈 Phase 1: Walk Forward Optimization Analysis")
            if not self._execute_wfo_analysis():
                self.logger.error("❌ WFO Analysis failed")
                return False
            
            # Phase 2: Account Management
            self.logger.info("\n💰 Phase 2: Account Management")
            if not self._execute_account_management():
                self.logger.error("❌ Account Management failed")
                return False
            
            # Phase 3: Bot Deployment
            if not self.config.dry_run:
                self.logger.info("\n🤖 Phase 3: Bot Deployment")
                if not self._execute_bot_deployment():
                    self.logger.error("❌ Bot Deployment failed")
                    return False
            else:
                self.logger.info("\n🔍 Dry Run: Skipping Bot Deployment")
            
            # Generate final report
            self._generate_final_report()
            
            self.logger.info("\n🎉 Lab to Bot Automation completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Automation failed with error: {e}")
            return False
    
    def _execute_wfo_analysis(self) -> bool:
        """Execute WFO analysis phase"""
        try:
            self.logger.info("Starting WFO analysis...")
            
            # Analyze backtests using WFO
            self.analysis_results = self.wfo_analyzer.analyze_lab_backtests(
                self.config.lab_id
            )
            
            if not self.analysis_results:
                self.logger.warning("⚠️ No backtests met the analysis criteria")
                return True  # Not a failure, just no results
            
            self.logger.info(f"✅ WFO Analysis completed: {len(self.analysis_results)} backtests analyzed")
            
            # Generate bot recommendations
            self.recommendations = self.wfo_analyzer.generate_bot_recommendations(
                self.config.lab_id
            )
            
            self.logger.info(f"✅ Generated {len(self.recommendations)} bot recommendations")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in WFO analysis: {e}")
            return False
    
    def _execute_account_management(self) -> bool:
        """Execute account management phase"""
        try:
            self.logger.info("Starting account management...")
            
            # Reserve accounts for bot deployment
            required_accounts = len(self.recommendations)
            if required_accounts == 0:
                self.logger.info("No accounts needed (no recommendations)")
                return True
            
            reserved_accounts = self.account_manager.reserve_accounts_for_bots(
                required_accounts
            )
            
            if not reserved_accounts:
                self.logger.error("Failed to reserve accounts")
                return False
            
            self.logger.info(f"✅ Account management completed: {len(reserved_accounts)} accounts reserved")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in account management: {e}")
            return False
    
    def _execute_bot_deployment(self) -> bool:
        """Execute bot deployment phase"""
        try:
            self.logger.info("Starting bot deployment...")
            
            if not self.recommendations:
                self.logger.info("No bots to deploy")
                return True
            
            # Deploy bots from recommendations
            self.deployment_results = self.bot_engine.deploy_bots_batch(
                self.recommendations
            )
            
            successful_deployments = [r for r in self.deployment_results if r.success]
            self.logger.info(f"✅ Bot deployment completed: {len(successful_deployments)}/{len(self.recommendations)} successful")
            
            return len(successful_deployments) > 0
            
        except Exception as e:
            self.logger.error(f"Error in bot deployment: {e}")
            return False
    
    def _generate_final_report(self):
        """Generate final automation report"""
        try:
            # Create output directory
            os.makedirs(self.config.output_dir, exist_ok=True)
            
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create report filename
            report_filename = f"automation_report_{self.config.lab_id}_{timestamp}.txt"
            report_path = os.path.join(self.config.output_dir, report_filename)
            
            with open(report_path, 'w') as f:
                f.write("Lab to Bot Automation Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Lab ID: {self.config.lab_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Dry Run: {self.config.dry_run}\n\n")
                
                # WFO Analysis Results
                f.write("WFO Analysis Results:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Backtests Analyzed: {len(self.analysis_results)}\n")
                f.write(f"Recommendations Generated: {len(self.recommendations)}\n\n")
                
                # Bot Recommendations
                if self.recommendations:
                    f.write("Bot Recommendations:\n")
                    f.write("-" * 20 + "\n")
                    for i, rec in enumerate(self.recommendations, 1):
                        f.write(f"{i}. {rec.script_name}\n")
                        f.write(f"   ROI: {rec.roi_percentage:.2f}%\n")
                        f.write(f"   Score: {rec.overall_score:.3f}\n")
                        f.write(f"   Trades: {rec.total_trades}\n\n")
                
                # Deployment Results
                if self.deployment_results:
                    f.write("Deployment Results:\n")
                    f.write("-" * 20 + "\n")
                    successful = [r for r in self.deployment_results if r.success]
                    f.write(f"Successful Deployments: {len(successful)}/{len(self.deployment_results)}\n\n")
                    
                    for result in self.deployment_results:
                        status = "✅ SUCCESS" if result.success else "❌ FAILED"
                        f.write(f"{status}: {result.bot_name}\n")
                        if result.error_message:
                            f.write(f"   Error: {result.error_message}\n")
                        f.write("\n")
            
            self.logger.info(f"📄 Report saved to: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the automation results"""
        return {
            "lab_id": self.config.lab_id,
            "dry_run": self.config.dry_run,
            "backtests_analyzed": len(self.analysis_results),
            "recommendations_generated": len(self.recommendations),
            "bots_deployed": len([r for r in self.deployment_results if r.success]) if self.deployment_results else 0,
            "total_deployment_attempts": len(self.deployment_results) if self.deployment_results else 0,
            "success": len(self.deployment_results) > 0 if self.deployment_results else True
        }
