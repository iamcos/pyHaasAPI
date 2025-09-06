#!/usr/bin/env python3
"""
Main CLI entry point for pyHaasAPI

This provides a unified command-line interface for all pyHaasAPI operations.
"""

import sys
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.cli.simple_cli import main as simple_cli_main


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="pyHaasAPI Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a lab and create bots
  python -m pyHaasAPI.cli analyze lab-id --create-count 3 --activate
  
  # List all labs
  python -m pyHaasAPI.cli list-labs
  
  # Run complete bot management workflow
  python -m pyHaasAPI.cli complete-workflow lab-id --create-count 2 --verify
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze lab and create bots')
    analyze_parser.add_argument('lab_id', help='Lab ID to analyze')
    analyze_parser.add_argument('--create-count', type=int, help='Number of bots to create')
    analyze_parser.add_argument('--activate', action='store_true', help='Activate bots after creation')
    analyze_parser.add_argument('--verify', action='store_true', help='Verify bot configuration')
    
    # List labs command
    list_parser = subparsers.add_parser('list-labs', help='List all available labs')
    
    # Complete workflow command
    workflow_parser = subparsers.add_parser('complete-workflow', help='Run complete bot management workflow')
    workflow_parser.add_argument('lab_id', help='Lab ID to process')
    workflow_parser.add_argument('--create-count', type=int, default=3, help='Number of bots to create')
    workflow_parser.add_argument('--activate', action='store_true', help='Activate bots after creation')
    workflow_parser.add_argument('--verify', action='store_true', help='Verify bot configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'analyze':
            simple_cli_main(['analyze', args.lab_id] + 
                          (['--create-count', str(args.create_count)] if args.create_count else []) +
                          (['--activate'] if args.activate else []) +
                          (['--verify'] if args.verify else []))
        elif args.command == 'list-labs':
            simple_cli_main(['list-labs'])
        elif args.command == 'complete-workflow':
            # Import and run the complete workflow
            from pyHaasAPI.examples.complete_bot_management_example import main as workflow_main
            workflow_args = [args.lab_id]
            if args.create_count:
                workflow_args.extend(['--create-count', str(args.create_count)])
            if args.activate:
                workflow_args.append('--activate')
            if args.verify:
                workflow_args.append('--verify')
            workflow_main(workflow_args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
