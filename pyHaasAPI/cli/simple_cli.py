#!/usr/bin/env python3
"""
Simple CLI using integrated pyHaasAPI analysis functionality

This is a simplified version that uses the new integrated analysis classes
from the pyHaasAPI library instead of duplicating functionality.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of other loggers
logging.getLogger('pyHaasAPI').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


def analyze_lab(lab_id: str, top_count: int = 5, create_bots: bool = False):
    """Analyze a lab and optionally create bots"""
    logger.info(f"🚀 Starting analysis of lab {lab_id[:8]}...")
    
    # Create analyzer with cache manager
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        logger.error("❌ Failed to connect to HaasOnline API")
        return False
    
    try:
        # Analyze lab
        result = analyzer.analyze_lab(lab_id, top_count)
        
        # Save report
        report_path = cache_manager.save_analysis_report(result)
        logger.info(f"📊 Analysis report saved: {report_path}")
        
        # Create bots if requested
        if create_bots and result.top_backtests:
            logger.info(f"🤖 Creating bots from top {len(result.top_backtests)} backtests...")
            bots_created = analyzer.create_bots_from_analysis(result)
            
            successful_bots = [bot for bot in bots_created if bot.success]
            logger.info(f"✅ Successfully created {len(successful_bots)} bots")
            
            for bot in successful_bots:
                logger.info(f"  🤖 {bot.bot_name} (ID: {bot.bot_id[:8]})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during analysis: {e}")
        return False


def list_labs(status_filter: str = None):
    """List available labs"""
    logger.info("📋 Fetching available labs...")
    
    # Create analyzer
    analyzer = HaasAnalyzer()
    
    # Connect to API
    if not analyzer.connect():
        logger.error("❌ Failed to connect to HaasOnline API")
        return False
    
    try:
        from pyHaasAPI import api
        
        # Get all labs
        labs = api.get_all_labs(analyzer.executor)
        
        # Filter by status if specified
        if status_filter:
            labs = [lab for lab in labs if lab.status == status_filter]
        
        logger.info(f"📊 Found {len(labs)} labs:")
        for lab in labs:
            logger.info(f"  🧪 {lab.name} (ID: {lab.lab_id[:8]}, Status: {lab.status})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fetching labs: {e}")
        return False


def main(args=None):
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Simple HaasOnline Analysis CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a lab and optionally create bots')
    analyze_parser.add_argument('lab_id', help='Lab ID to analyze')
    analyze_parser.add_argument('--top', type=int, default=5, help='Number of top backtests to analyze (default: 5)')
    analyze_parser.add_argument('--create-bots', action='store_true', help='Create bots from top backtests')
    
    # List labs command
    list_parser = subparsers.add_parser('list-labs', help='List available labs')
    list_parser.add_argument('--status', choices=['active', 'completed', 'paused'], help='Filter labs by status')
    
    args = parser.parse_args(args)
    
    if args.command == 'analyze':
        success = analyze_lab(args.lab_id, args.top, args.create_bots)
    elif args.command == 'list-labs':
        success = list_labs(args.status)
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
