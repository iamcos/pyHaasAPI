"""
Lab CLI for pyHaasAPI v2

This module provides command-line interface for lab operations
using the new v2 architecture with async support and type safety.
"""

import asyncio
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseCLI, CLIConfig
from ..core.logging import get_logger
from ..core.type_definitions import LabID, LabStatus
from ..exceptions import APIError, ValidationError

logger = get_logger("lab_cli")


class LabCLI(BaseCLI):
    """
    CLI for lab operations.
    
    Provides command-line interface for lab management, analysis,
    and execution operations.
    """

    def __init__(self, config: Optional[CLIConfig] = None):
        super().__init__(config)
        self.logger = get_logger("lab_cli")

    async def run(self, args: List[str]) -> int:
        """
        Run the lab CLI with the given arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parser = self.create_lab_parser()
            parsed_args = parser.parse_args(args)
            
            # Update config from args
            self.update_config_from_args(parsed_args)
            
            # Connect to API
            if not await self.connect():
                self.logger.error("Failed to connect to API")
                return 1
            
            # Execute command
            if parsed_args.action == 'list':
                return await self.list_labs(parsed_args)
            elif parsed_args.action == 'create':
                return await self.create_lab(parsed_args)
            elif parsed_args.action == 'delete':
                return await self.delete_lab(parsed_args)
            elif parsed_args.action == 'analyze':
                return await self.analyze_lab(parsed_args)
            elif parsed_args.action == 'execute':
                return await self.execute_lab(parsed_args)
            elif parsed_args.action == 'status':
                return await self.get_lab_status(parsed_args)
            else:
                self.logger.error(f"Unknown action: {parsed_args.action}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error in lab CLI: {e}")
            return 1

    def create_lab_parser(self) -> argparse.ArgumentParser:
        """Create lab-specific argument parser"""
        parser = argparse.ArgumentParser(
            description="Lab operations for pyHaasAPI v2",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # List all labs
  python -m pyHaasAPI_v2.cli lab list
  
  # Create a new lab
  python -m pyHaasAPI_v2.cli lab create --name "Test Lab" --script-id script123
  
  # Analyze a lab
  python -m pyHaasAPI_v2.cli lab analyze --lab-id lab123 --top-count 5
  
  # Execute a lab
  python -m pyHaasAPI_v2.cli lab execute --lab-id lab123
  
  # Get lab status
  python -m pyHaasAPI_v2.cli lab status --lab-id lab123
            """
        )
        
        # Add common options
        parser = self.create_parser("Lab operations")
        
        # Lab-specific options
        parser.add_argument(
            'action',
            choices=['list', 'create', 'delete', 'analyze', 'execute', 'status'],
            help='Lab action to perform'
        )
        parser.add_argument('--lab-id', help='Lab ID')
        parser.add_argument('--name', help='Lab name')
        parser.add_argument('--script-id', help='Script ID')
        parser.add_argument('--description', help='Lab description')
        parser.add_argument('--top-count', type=int, default=10, help='Number of top results to show')
        parser.add_argument('--generate-reports', action='store_true', help='Generate analysis reports')
        parser.add_argument('--output-format', choices=['json', 'csv', 'table'], default='table', help='Output format')
        parser.add_argument('--output-file', help='Output file path')
        
        return parser

    async def list_labs(self, args: argparse.Namespace) -> int:
        """List all labs"""
        try:
            self.logger.info("Fetching labs...")
            
            if not self.lab_api:
                self.logger.error("Lab API not initialized")
                return 1
            
            # Get labs
            labs = await self.lab_api.get_labs()
            
            if not labs:
                self.logger.info("No labs found")
                return 0
            
            # Display results
            if args.output_format == 'json':
                import json
                output = json.dumps([lab.dict() for lab in labs], indent=2)
                if args.output_file:
                    with open(args.output_file, 'w') as f:
                        f.write(output)
                else:
                    print(output)
            elif args.output_format == 'csv':
                import csv
                if args.output_file:
                    with open(args.output_file, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'script_id', 'status', 'created_at'])
                        writer.writeheader()
                        for lab in labs:
                            writer.writerow(lab.dict())
                else:
                    print("id,name,script_id,status,created_at")
                    for lab in labs:
                        print(f"{lab.id},{lab.name},{lab.script_id},{lab.status},{lab.created_at}")
            else:
                # Table format
                print(f"\nFound {len(labs)} labs:")
                print("-" * 80)
                print(f"{'ID':<20} {'Name':<30} {'Script ID':<20} {'Status':<10}")
                print("-" * 80)
                for lab in labs:
                    print(f"{lab.id:<20} {lab.name[:30]:<30} {lab.script_id:<20} {lab.status:<10}")
                print("-" * 80)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error listing labs: {e}")
            return 1

    async def create_lab(self, args: argparse.Namespace) -> int:
        """Create a new lab"""
        try:
            if not args.name or not args.script_id:
                self.logger.error("Name and script-id are required for lab creation")
                return 1
            
            self.logger.info(f"Creating lab '{args.name}' with script '{args.script_id}'...")
            
            if not self.lab_api:
                self.logger.error("Lab API not initialized")
                return 1
            
            # Create lab
            lab_details = await self.lab_api.create_lab(
                name=args.name,
                script_id=args.script_id,
                description=args.description or ""
            )
            
            if lab_details:
                self.logger.info(f"Successfully created lab: {lab_details.lab_id}")
                print(f"Lab ID: {lab_details.lab_id}")
                print(f"Name: {lab_details.name}")
                print(f"Script ID: {lab_details.script_id}")
                print(f"Status: {lab_details.status}")
                return 0
            else:
                self.logger.error("Failed to create lab")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error creating lab: {e}")
            return 1

    async def delete_lab(self, args: argparse.Namespace) -> int:
        """Delete a lab"""
        try:
            if not args.lab_id:
                self.logger.error("Lab ID is required for deletion")
                return 1
            
            self.logger.info(f"Deleting lab '{args.lab_id}'...")
            
            if not self.lab_api:
                self.logger.error("Lab API not initialized")
                return 1
            
            # Delete lab
            success = await self.lab_api.delete_lab(args.lab_id)
            
            if success:
                self.logger.info(f"Successfully deleted lab: {args.lab_id}")
                return 0
            else:
                self.logger.error("Failed to delete lab")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error deleting lab: {e}")
            return 1

    async def analyze_lab(self, args: argparse.Namespace) -> int:
        """Analyze a lab"""
        try:
            if not args.lab_id:
                self.logger.error("Lab ID is required for analysis")
                return 1
            
            self.logger.info(f"Analyzing lab '{args.lab_id}'...")
            
            if not self.analysis_service:
                self.logger.error("Analysis service not initialized")
                return 1
            
            # Analyze lab
            result = await self.analysis_service.analyze_lab_comprehensive(
                lab_id=args.lab_id,
                top_count=args.top_count
            )
            
            if result.success:
                self.logger.info(f"Successfully analyzed lab: {args.lab_id}")
                
                # Display results
                if args.output_format == 'json':
                    import json
                    output = json.dumps({
                        'lab_id': result.lab_id,
                        'lab_name': result.lab_name,
                        'total_backtests': result.total_backtests,
                        'average_roi': result.average_roi,
                        'best_roi': result.best_roi,
                        'average_win_rate': result.average_win_rate,
                        'top_performers': [
                            {
                                'backtest_id': bt.backtest_id,
                                'roi_percentage': bt.roi_percentage,
                                'win_rate': bt.win_rate,
                                'total_trades': bt.total_trades,
                                'realized_profits_usdt': bt.realized_profits_usdt
                            } for bt in result.top_performers
                        ]
                    }, indent=2)
                    if args.output_file:
                        with open(args.output_file, 'w') as f:
                            f.write(output)
                    else:
                        print(output)
                elif args.output_format == 'csv':
                    import csv
                    if args.output_file:
                        with open(args.output_file, 'w', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=['backtest_id', 'roi', 'win_rate', 'trades', 'profit'])
                            writer.writeheader()
                            for backtest in result.top_performers:
                                writer.writerow({
                                    'backtest_id': backtest.backtest_id,
                                    'roi': backtest.roi_percentage,
                                    'win_rate': backtest.win_rate,
                                    'trades': backtest.total_trades,
                                    'profit': backtest.realized_profits_usdt
                                })
                    else:
                        print("backtest_id,roi,win_rate,trades,profit")
                        for backtest in result.top_performers:
                            print(f"{backtest.backtest_id},{backtest.roi_percentage},{backtest.win_rate},{backtest.total_trades},{backtest.realized_profits_usdt}")
                else:
                    # Table format
                    print(f"\nLab Analysis Results for {args.lab_id}:")
                    print("-" * 100)
                    print(f"{'Backtest ID':<20} {'ROI %':<10} {'Win Rate':<10} {'Trades':<10} {'Profit USDT':<15}")
                    print("-" * 100)
                    for backtest in result.top_performers:
                        print(f"{backtest.backtest_id:<20} {backtest.roi_percentage:<10.2f} {backtest.win_rate:<10.2f} {backtest.total_trades:<10} {backtest.realized_profits_usdt:<15.2f}")
                    print("-" * 100)
                
                # Generate reports if requested
                if args.generate_reports and self.reporting_service:
                    from ..services.reporting import ReportConfig, ReportType, ReportFormat
                    config = ReportConfig(
                        report_type=ReportType.LAB_ANALYSIS,
                        format=ReportFormat.CSV
                    )
                    report_result = await self.reporting_service.generate_analysis_report([result], config)
                    self.logger.info(f"Analysis report generated: {report_result.report_path}")
                
                return 0
            else:
                self.logger.error(f"Failed to analyze lab: {result.error_message}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error analyzing lab: {e}")
            return 1

    async def execute_lab(self, args: argparse.Namespace) -> int:
        """Execute a lab"""
        try:
            if not args.lab_id:
                self.logger.error("Lab ID is required for execution")
                return 1
            
            self.logger.info(f"Executing lab '{args.lab_id}'...")
            
            if not self.lab_service:
                self.logger.error("Lab service not initialized")
                return 1
            
            # Execute lab
            result = await self.lab_service.execute_lab(args.lab_id)
            
            if result.success:
                self.logger.info(f"Successfully started lab execution: {args.lab_id}")
                print(f"Lab ID: {result.data.lab_id}")
                print(f"Status: {result.data.status}")
                print(f"Started at: {result.data.started_at}")
                return 0
            else:
                self.logger.error(f"Failed to execute lab: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error executing lab: {e}")
            return 1

    async def get_lab_status(self, args: argparse.Namespace) -> int:
        """Get lab status"""
        try:
            if not args.lab_id:
                self.logger.error("Lab ID is required for status check")
                return 1
            
            self.logger.info(f"Getting status for lab '{args.lab_id}'...")
            
            if not self.lab_service:
                self.logger.error("Lab service not initialized")
                return 1
            
            # Get lab status
            result = await self.lab_service.get_lab_status(args.lab_id)
            
            if result.success:
                self.logger.info(f"Lab status retrieved: {args.lab_id}")
                print(f"Lab ID: {result.data.lab_id}")
                print(f"Status: {result.data.status}")
                print(f"Progress: {result.data.progress}%")
                print(f"Started at: {result.data.started_at}")
                if result.data.completed_at:
                    print(f"Completed at: {result.data.completed_at}")
                return 0
            else:
                self.logger.error(f"Failed to get lab status: {result.error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error getting lab status: {e}")
            return 1
