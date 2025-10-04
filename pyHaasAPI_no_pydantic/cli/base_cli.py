"""
Base CLI functionality for pyHaasAPI_no_pydantic

Provides common CLI functionality and utilities used across
all CLI tools, eliminating code duplication.
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

from ..api.client import APIClient
from ..api.lab_api import LabAPI
from ..services.lab_service import LabService
from ..services.analysis_service import AnalysisService
from ..api.exceptions import LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError


class BaseCLI:
    """
    Base CLI class with common functionality
    
    Provides shared functionality for all CLI tools including
    argument parsing, logging, error handling, and output formatting.
    """
    
    def __init__(self, description: str = "pyHaasAPI_no_pydantic CLI"):
        self.description = description
        self.logger = self._setup_logging()
        self.client = None
        self.lab_api = None
        self.lab_service = None
        self.analysis_service = None
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_api_connection(self, host: str = "127.0.0.1", port: int = 8090) -> None:
        """Setup API connection"""
        try:
            self.client = APIClient(base_url=f"http://{host}:{port}")
            self.lab_api = LabAPI(self.client)
            self.lab_service = LabService(self.lab_api)
            self.analysis_service = AnalysisService(self.lab_api)
            self.logger.info(f"API connection established: {host}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to setup API connection: {e}")
            raise
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with common options"""
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Common options
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="API host (default: 127.0.0.1)"
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8090,
            help="API port (default: 8090)"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose logging"
        )
        parser.add_argument(
            "--output", "-o",
            help="Output file path"
        )
        parser.add_argument(
            "--format",
            choices=["json", "csv", "table"],
            default="table",
            help="Output format (default: table)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes"
        )
        
        return parser
    
    def _format_output(self, data: Any, format_type: str = "table") -> str:
        """Format output data"""
        if format_type == "json":
            if hasattr(data, 'to_dict'):
                return json.dumps(data.to_dict(), indent=2, default=str)
            elif isinstance(data, list) and data and hasattr(data[0], 'to_dict'):
                return json.dumps([item.to_dict() for item in data], indent=2, default=str)
            else:
                return json.dumps(data, indent=2, default=str)
        
        elif format_type == "csv":
            if isinstance(data, list) and data and hasattr(data[0], 'to_dict'):
                import csv
                import io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].to_dict().keys())
                writer.writeheader()
                for item in data:
                    writer.writerow(item.to_dict())
                return output.getvalue()
            else:
                return str(data)
        
        else:  # table format
            if isinstance(data, list) and data and hasattr(data[0], 'to_dict'):
                # Create a simple table
                if not data:
                    return "No data available"
                
                first_item = data[0].to_dict()
                headers = list(first_item.keys())
                
                # Calculate column widths
                col_widths = {}
                for header in headers:
                    col_widths[header] = max(len(header), max(len(str(item.get(header, ""))) for item in data[:10]))
                
                # Create table
                lines = []
                lines.append(" | ".join(header.ljust(col_widths[header]) for header in headers))
                lines.append("-" * sum(col_widths.values()) + "-" * (len(headers) - 1))
                
                for item in data:
                    row = " | ".join(str(item.get(header, "")).ljust(col_widths[header]) for header in headers)
                    lines.append(row)
                
                return "\n".join(lines)
            else:
                return str(data)
    
    def _write_output(self, data: Any, output_file: Optional[str] = None, format_type: str = "table") -> None:
        """Write output to file or stdout"""
        formatted_data = self._format_output(data, format_type)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(formatted_data)
            self.logger.info(f"Output written to {output_file}")
        else:
            print(formatted_data)
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with proper logging and user feedback"""
        if isinstance(error, LabNotFoundError):
            self.logger.error(f"Lab not found: {error.lab_id}")
            print(f"❌ Lab not found: {error.lab_id}")
        elif isinstance(error, LabExecutionError):
            self.logger.error(f"Lab execution failed: {error.lab_id} - {error.error_message}")
            print(f"❌ Lab execution failed: {error.lab_id} - {error.error_message}")
        elif isinstance(error, LabConfigurationError):
            self.logger.error(f"Lab configuration error: {error.field_name} - {error.error_message}")
            print(f"❌ Lab configuration error: {error.field_name} - {error.error_message}")
        elif isinstance(error, LabAPIError):
            self.logger.error(f"Lab API error: {error.message}")
            print(f"❌ Lab API error: {error.message}")
        else:
            self.logger.error(f"Unexpected error: {error}")
            print(f"❌ Unexpected error: {error}")
        
        if context:
            self.logger.info(f"Context: {context}")
    
    def _print_success(self, message: str) -> None:
        """Print success message"""
        print(f"✅ {message}")
        self.logger.info(message)
    
    def _print_info(self, message: str) -> None:
        """Print info message"""
        print(f"ℹ️  {message}")
        self.logger.info(message)
    
    def _print_warning(self, message: str) -> None:
        """Print warning message"""
        print(f"⚠️  {message}")
        self.logger.warning(message)
    
    async def _confirm_action(self, message: str) -> bool:
        """Confirm action with user"""
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ('y', 'yes')
    
    def _load_environment(self) -> Dict[str, str]:
        """Load environment variables"""
        env_vars = {}
        
        # Load from .env file if it exists
        env_file = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Override with actual environment variables
        for key in ['API_EMAIL', 'API_PASSWORD', 'API_HOST', 'API_PORT']:
            if key in os.environ:
                env_vars[key] = os.environ[key]
        
        return env_vars
    
    def _validate_environment(self) -> None:
        """Validate required environment variables"""
        env_vars = self._load_environment()
        
        required_vars = ['API_EMAIL', 'API_PASSWORD']
        missing_vars = [var for var in required_vars if var not in env_vars]
        
        if missing_vars:
            self.logger.error(f"Missing required environment variables: {missing_vars}")
            print(f"❌ Missing required environment variables: {missing_vars}")
            print("Please set the following environment variables:")
            for var in missing_vars:
                print(f"  export {var}=your_value")
            sys.exit(1)
    
    async def run(self, args: List[str]) -> int:
        """Run the CLI with given arguments"""
        try:
            # Parse arguments
            parser = self._create_parser()
            parsed_args = parser.parse_args(args)
            
            # Setup logging level
            if parsed_args.verbose:
                self.logger.setLevel(logging.DEBUG)
            
            # Validate environment
            self._validate_environment()
            
            # Setup API connection
            self._setup_api_connection(parsed_args.host, parsed_args.port)
            
            # Run the specific command
            return await self._run_command(parsed_args)
            
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            print("\n⚠️  Operation cancelled by user")
            return 1
        except Exception as e:
            self._handle_error(e, "CLI execution failed")
            return 1
    
    async def _run_command(self, args: argparse.Namespace) -> int:
        """Run the specific command - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _run_command")
    
    def _create_subparsers(self, parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
        """Create subparsers for commands"""
        return parser.add_subparsers(dest='command', help='Available commands')
    
    def _add_common_lab_args(self, parser: argparse.ArgumentParser) -> None:
        """Add common lab-related arguments"""
        parser.add_argument(
            "--lab-id",
            help="Lab ID to operate on"
        )
        parser.add_argument(
            "--lab-ids",
            help="Comma-separated list of lab IDs"
        )
        parser.add_argument(
            "--script-id",
            help="Script ID for lab creation"
        )
        parser.add_argument(
            "--account-id",
            help="Account ID for lab creation"
        )
        parser.add_argument(
            "--market",
            help="Market tag for lab creation"
        )
        parser.add_argument(
            "--name",
            help="Lab name"
        )
    
    def _add_common_analysis_args(self, parser: argparse.ArgumentParser) -> None:
        """Add common analysis-related arguments"""
        parser.add_argument(
            "--top-count",
            type=int,
            default=10,
            help="Number of top performers to return (default: 10)"
        )
        parser.add_argument(
            "--min-winrate",
            type=float,
            default=0.3,
            help="Minimum win rate threshold (default: 0.3)"
        )
        parser.add_argument(
            "--min-trades",
            type=int,
            default=5,
            help="Minimum number of trades (default: 5)"
        )
        parser.add_argument(
            "--sort-by",
            choices=["roi", "roe", "winrate", "profit", "trades"],
            default="roe",
            help="Field to sort by (default: roe)"
        )
    
    def _add_common_execution_args(self, parser: argparse.ArgumentParser) -> None:
        """Add common execution-related arguments"""
        parser.add_argument(
            "--start-date",
            help="Start date for execution (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--end-date",
            help="End date for execution (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--max-iterations",
            type=int,
            default=1500,
            help="Maximum number of iterations (default: 1500)"
        )
        parser.add_argument(
            "--send-email",
            action="store_true",
            help="Send email notification when execution completes"
        )



