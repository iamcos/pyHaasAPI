"""
Cursor MCP Tool Handlers for pyHaasAPI

This module contains all the tool handlers for the Cursor MCP server,
providing comprehensive access to pyHaasAPI functionality with server manager integration.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .cursor_mcp_server import cursor_mcp_server_instance
from ..core.logging import get_logger
from mcp.types import TextContent

logger = get_logger("cursor_mcp_handlers")

# Lab Management Handlers

async def handle_list_labs() -> List[TextContent]:
    """Handle list_labs tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_api = cursor_mcp_server_instance.get_current_api("lab_api")
        labs = await lab_api.get_labs()
        return [TextContent(type="text", text=json.dumps([lab.dict() for lab in labs], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing labs: {str(e)}")]

async def handle_get_lab_details(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_lab_details tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        lab_api = cursor_mcp_server_instance.get_current_api("lab_api")
        lab_details = await lab_api.get_lab_details(lab_id)
        return [TextContent(type="text", text=json.dumps(lab_details.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting lab details: {str(e)}")]

async def handle_create_lab(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle create_lab tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        name = arguments["name"]
        script_id = arguments["script_id"]
        account_id = arguments["account_id"]
        market = arguments["market"]
        parameters = arguments.get("parameters", {})
        
        lab_api = cursor_mcp_server_instance.get_current_api("lab_api")
        lab = await lab_api.create_lab(
            name=name,
            script_id=script_id,
            account_id=account_id,
            market=market,
            parameters=parameters
        )
        return [TextContent(type="text", text=json.dumps(lab.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating lab: {str(e)}")]

async def handle_start_lab_execution(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle start_lab_execution tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        max_iterations = arguments.get("max_iterations", 1500)
        
        lab_api = cursor_mcp_server_instance.get_current_api("lab_api")
        job_id = await lab_api.start_lab_execution(
            lab_id=lab_id,
            max_iterations=max_iterations
        )
        return [TextContent(type="text", text=f"Lab execution started with job ID: {job_id}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error starting lab execution: {str(e)}")]

async def handle_get_lab_execution_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_lab_execution_status tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        lab_api = cursor_mcp_server_instance.get_current_api("lab_api")
        status = await lab_api.get_lab_execution_status(lab_id)
        return [TextContent(type="text", text=json.dumps(status.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting lab execution status: {str(e)}")]

# Bot Management Handlers

async def handle_list_bots() -> List[TextContent]:
    """Handle list_bots tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        bot_api = cursor_mcp_server_instance.get_current_api("bot_api")
        bots = await bot_api.get_all_bots()
        return [TextContent(type="text", text=json.dumps([bot.dict() for bot in bots], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing bots: {str(e)}")]

async def handle_get_bot_details(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_bot_details tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        bot_id = arguments["bot_id"]
        bot_api = cursor_mcp_server_instance.get_current_api("bot_api")
        bot_details = await bot_api.get_bot_details(bot_id)
        return [TextContent(type="text", text=json.dumps(bot_details.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting bot details: {str(e)}")]

async def handle_create_bot(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle create_bot tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        name = arguments["name"]
        script_id = arguments["script_id"]
        account_id = arguments["account_id"]
        market = arguments["market"]
        leverage = arguments.get("leverage", 20.0)
        trade_amount = arguments.get("trade_amount", 2000.0)
        
        bot_api = cursor_mcp_server_instance.get_current_api("bot_api")
        bot = await bot_api.create_bot(
            name=name,
            script_id=script_id,
            account_id=account_id,
            market=market,
            leverage=leverage,
            trade_amount=trade_amount
        )
        return [TextContent(type="text", text=json.dumps(bot.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating bot: {str(e)}")]

async def handle_activate_bot(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle activate_bot tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        bot_id = arguments["bot_id"]
        bot_api = cursor_mcp_server_instance.get_current_api("bot_api")
        result = await bot_api.activate_bot(bot_id)
        return [TextContent(type="text", text=f"Bot {bot_id} activated successfully")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error activating bot: {str(e)}")]

async def handle_deactivate_bot(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle deactivate_bot tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        bot_id = arguments["bot_id"]
        bot_api = cursor_mcp_server_instance.get_current_api("bot_api")
        result = await bot_api.deactivate_bot(bot_id)
        return [TextContent(type="text", text=f"Bot {bot_id} deactivated successfully")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error deactivating bot: {str(e)}")]

# Analysis & Optimization Handlers

async def handle_analyze_lab(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle analyze_lab tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        top_count = arguments.get("top_count", 10)
        min_win_rate = arguments.get("min_win_rate", 0.3)
        min_trades = arguments.get("min_trades", 5)
        
        analysis_service = cursor_mcp_server_instance.get_current_api("analysis_service")
        analysis_result = await analysis_service.analyze_lab_comprehensive(
            lab_id=lab_id,
            top_count=top_count,
            min_win_rate=min_win_rate,
            min_trades=min_trades
        )
        return [TextContent(type="text", text=json.dumps(analysis_result.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error analyzing lab: {str(e)}")]

async def handle_create_bots_from_analysis(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle create_bots_from_analysis tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        count = arguments.get("count", 3)
        activate = arguments.get("activate", False)
        
        # First analyze the lab
        analysis_service = cursor_mcp_server_instance.get_current_api("analysis_service")
        analysis_result = await analysis_service.analyze_lab_comprehensive(lab_id)
        
        # Create bots from top backtests
        bot_service = cursor_mcp_server_instance.get_current_api("bot_service")
        created_bots = []
        for i, backtest in enumerate(analysis_result.top_backtests[:count]):
            bot = await bot_service.create_bot_from_lab_analysis(
                lab_id=lab_id,
                backtest_id=backtest.backtest_id,
                account_id=backtest.account_id,
                activate=activate
            )
            created_bots.append(bot)
        
        return [TextContent(type="text", text=json.dumps([bot.dict() for bot in created_bots], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating bots from analysis: {str(e)}")]

async def handle_run_wfo_analysis(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle run_wfo_analysis tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        start_date = arguments["start_date"]
        end_date = arguments["end_date"]
        training_days = arguments.get("training_days", 365)
        testing_days = arguments.get("testing_days", 90)
        
        # This would use the WFO analyzer from the CLI tools
        # For now, return a placeholder
        return [TextContent(type="text", text=f"WFO analysis for lab {lab_id} from {start_date} to {end_date} - Implementation needed")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error running WFO analysis: {str(e)}")]

# Account Management Handlers

async def handle_list_accounts() -> List[TextContent]:
    """Handle list_accounts tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        account_api = cursor_mcp_server_instance.get_current_api("account_api")
        accounts = await account_api.get_accounts()
        return [TextContent(type="text", text=json.dumps([account.dict() for account in accounts], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing accounts: {str(e)}")]

async def handle_get_account_balance(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_account_balance tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        account_id = arguments["account_id"]
        account_api = cursor_mcp_server_instance.get_current_api("account_api")
        balance = await account_api.get_account_balance(account_id)
        return [TextContent(type="text", text=json.dumps(balance.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting account balance: {str(e)}")]

async def handle_configure_account(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle configure_account tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        account_id = arguments["account_id"]
        leverage = arguments.get("leverage")
        margin_mode = arguments.get("margin_mode")
        position_mode = arguments.get("position_mode")
        
        account_api = cursor_mcp_server_instance.get_current_api("account_api")
        
        # Configure account settings
        if leverage:
            await account_api.set_leverage(account_id, leverage)
        if margin_mode:
            await account_api.set_margin_mode(account_id, margin_mode)
        if position_mode:
            await account_api.set_position_mode(account_id, position_mode)
        
        return [TextContent(type="text", text=f"Account {account_id} configured successfully")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error configuring account: {str(e)}")]

# Market Data Handlers

async def handle_get_markets() -> List[TextContent]:
    """Handle get_markets tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        market_api = cursor_mcp_server_instance.get_current_api("market_api")
        markets = await market_api.get_trade_markets()
        return [TextContent(type="text", text=json.dumps([market.dict() for market in markets], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting markets: {str(e)}")]

async def handle_get_price_data(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_price_data tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        market = arguments["market"]
        market_api = cursor_mcp_server_instance.get_current_api("market_api")
        price_data = await market_api.get_price_data(market)
        return [TextContent(type="text", text=json.dumps(price_data.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting price data: {str(e)}")]

async def handle_get_historical_data(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_historical_data tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        market = arguments["market"]
        start_date = arguments["start_date"]
        end_date = arguments["end_date"]
        interval = arguments.get("interval", "1h")
        
        market_api = cursor_mcp_server_instance.get_current_api("market_api")
        historical_data = await market_api.get_historical_data(
            market=market,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        return [TextContent(type="text", text=json.dumps([data.dict() for data in historical_data], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting historical data: {str(e)}")]

# Script Management Handlers

async def handle_list_scripts() -> List[TextContent]:
    """Handle list_scripts tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        script_api = cursor_mcp_server_instance.get_current_api("script_api")
        scripts = await script_api.get_all_scripts()
        return [TextContent(type="text", text=json.dumps([script.dict() for script in scripts], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing scripts: {str(e)}")]

async def handle_get_script_details(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_script_details tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        script_id = arguments["script_id"]
        script_api = cursor_mcp_server_instance.get_current_api("script_api")
        script_details = await script_api.get_script_details(script_id)
        return [TextContent(type="text", text=json.dumps(script_details.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting script details: {str(e)}")]

# Backtest Management Handlers

async def handle_get_lab_backtests(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_lab_backtests tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        backtest_api = cursor_mcp_server_instance.get_current_api("backtest_api")
        backtests = await backtest_api.get_lab_backtests(lab_id)
        return [TextContent(type="text", text=json.dumps([bt.dict() for bt in backtests], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting lab backtests: {str(e)}")]

async def handle_get_backtest_results(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_backtest_results tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        backtest_id = arguments["backtest_id"]
        backtest_api = cursor_mcp_server_instance.get_current_api("backtest_api")
        results = await backtest_api.get_backtest_result(backtest_id)
        return [TextContent(type="text", text=json.dumps(results.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting backtest results: {str(e)}")]

async def handle_run_longest_backtest(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle run_longest_backtest tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        max_iterations = arguments.get("max_iterations", 1500)
        
        # Use the lab service for longest backtest
        lab_service = cursor_mcp_server_instance.get_current_api("lab_service")
        result = await lab_service.run_longest_backtest(
            lab_id=lab_id,
            max_iterations=max_iterations
        )
        return [TextContent(type="text", text=json.dumps(result.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error running longest backtest: {str(e)}")]

# Order Management Handlers

async def handle_get_bot_orders(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_bot_orders tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        bot_id = arguments["bot_id"]
        order_api = cursor_mcp_server_instance.get_current_api("order_api")
        orders = await order_api.get_bot_orders(bot_id)
        return [TextContent(type="text", text=json.dumps([order.dict() for order in orders], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting bot orders: {str(e)}")]

async def handle_place_order(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle place_order tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        account_id = arguments["account_id"]
        market = arguments["market"]
        side = arguments["side"]
        amount = arguments["amount"]
        price = arguments.get("price")
        
        order_api = cursor_mcp_server_instance.get_current_api("order_api")
        order_id = await order_api.place_order(
            account_id=account_id,
            market=market,
            side=side,
            amount=amount,
            price=price
        )
        return [TextContent(type="text", text=f"Order placed with ID: {order_id}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error placing order: {str(e)}")]

async def handle_cancel_order(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle cancel_order tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        order_id = arguments["order_id"]
        order_api = cursor_mcp_server_instance.get_current_api("order_api")
        result = await order_api.cancel_order(order_id)
        return [TextContent(type="text", text=f"Order {order_id} cancelled successfully")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error cancelling order: {str(e)}")]

# Reporting & Analytics Handlers

async def handle_generate_analysis_report(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle generate_analysis_report tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        lab_id = arguments["lab_id"]
        format_type = arguments.get("format", "json")
        include_charts = arguments.get("include_charts", False)
        
        reporting_service = cursor_mcp_server_instance.get_current_api("reporting_service")
        report = await reporting_service.generate_report(
            lab_id=lab_id,
            report_type="lab_analysis",
            format_type=format_type,
            include_charts=include_charts
        )
        return [TextContent(type="text", text=json.dumps(report.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error generating analysis report: {str(e)}")]

async def handle_get_performance_metrics(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_performance_metrics tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        entity_type = arguments["entity_type"]
        entity_id = arguments["entity_id"]
        timeframe = arguments.get("timeframe", "all")
        
        if entity_type == "lab":
            analysis_service = cursor_mcp_server_instance.get_current_api("analysis_service")
            metrics = await analysis_service.get_lab_performance_metrics(
                lab_id=entity_id,
                timeframe=timeframe
            )
        elif entity_type == "bot":
            bot_service = cursor_mcp_server_instance.get_current_api("bot_service")
            metrics = await bot_service.get_bot_performance_metrics(
                bot_id=entity_id,
                timeframe=timeframe
            )
        else:
            return [TextContent(type="text", text="Invalid entity type. Use 'lab' or 'bot'")]
        
        return [TextContent(type="text", text=json.dumps(metrics.dict(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting performance metrics: {str(e)}")]

# Google Sheets Integration Handlers

async def handle_publish_to_google_sheets(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle publish_to_google_sheets tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        sheet_id = arguments["sheet_id"]
        credentials_path = arguments.get("credentials_path", "gdocs/google_credentials.json")
        server_configs = arguments.get("server_configs", {
            "srv01": {"host": "127.0.0.1", "port": 8090},
            "srv02": {"host": "127.0.0.1", "port": 8091},
            "srv03": {"host": "127.0.0.1", "port": 8092}
        })
        
        from ..services.google_sheets_service import GoogleSheetsService, MultiServerDataCollector
        
        # Initialize services
        sheets_service = GoogleSheetsService(credentials_path, sheet_id)
        data_collector = MultiServerDataCollector()
        
        # Collect data from all servers
        all_data = await data_collector.collect_all_server_data(server_configs)
        
        # Publish data for each server
        for server_name, data in all_data.items():
            await sheets_service.publish_server_data(server_name, data)
        
        # Publish summary
        await sheets_service.publish_summary(all_data)
        
        return [TextContent(type="text", text=f"Successfully published data to Google Sheets for {len(all_data)} servers")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error publishing to Google Sheets: {str(e)}")]

async def handle_update_google_sheets_server(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle update_google_sheets_server tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        sheet_id = arguments["sheet_id"]
        server_name = arguments["server_name"]
        credentials_path = arguments.get("credentials_path", "gdocs/google_credentials.json")
        
        from ..services.google_sheets_service import GoogleSheetsService, MultiServerDataCollector
        
        # Initialize services
        sheets_service = GoogleSheetsService(credentials_path, sheet_id)
        data_collector = MultiServerDataCollector()
        
        # Collect data from current server
        server_config = {server_name: {"host": "127.0.0.1", "port": 8090}}
        all_data = await data_collector.collect_all_server_data(server_config)
        
        # Publish data for the server
        if server_name in all_data:
            await sheets_service.publish_server_data(server_name, all_data[server_name])
            return [TextContent(type="text", text=f"Successfully updated Google Sheets for {server_name}")]
        else:
            return [TextContent(type="text", text=f"No data found for server {server_name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error updating Google Sheets for server: {str(e)}")]

# Mass Operations Handlers

async def handle_mass_bot_creation(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle mass_bot_creation tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        top_count = arguments.get("top_count", 5)
        min_win_rate = arguments.get("min_win_rate", 0.3)
        min_trades = arguments.get("min_trades", 5)
        activate = arguments.get("activate", False)
        
        # Get all labs
        lab_api = cursor_mcp_server_instance.get_current_api("lab_api")
        labs = await lab_api.get_labs()
        
        created_bots = []
        for lab in labs:
            try:
                # Analyze lab
                analysis_service = cursor_mcp_server_instance.get_current_api("analysis_service")
                analysis_result = await analysis_service.analyze_lab_comprehensive(
                    lab_id=lab.lab_id,
                    top_count=top_count,
                    min_win_rate=min_win_rate,
                    min_trades=min_trades
                )
                
                # Create bots from top backtests
                bot_service = cursor_mcp_server_instance.get_current_api("bot_service")
                for backtest in analysis_result.top_backtests[:top_count]:
                    bot = await bot_service.create_bot_from_lab_analysis(
                        lab_id=lab.lab_id,
                        backtest_id=backtest.backtest_id,
                        account_id=backtest.account_id,
                        activate=activate
                    )
                    created_bots.append(bot)
                    
            except Exception as e:
                logger.warning(f"Failed to create bots for lab {lab.lab_id}: {e}")
                continue
        
        return [TextContent(type="text", text=json.dumps([bot.dict() for bot in created_bots], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error in mass bot creation: {str(e)}")]

async def handle_analyze_all_labs(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle analyze_all_labs tool"""
    try:
        if not cursor_mcp_server_instance.active_server:
            return [TextContent(type="text", text="No active server connection. Please connect to a server first.")]
        
        min_win_rate = arguments.get("min_win_rate", 0.3)
        min_trades = arguments.get("min_trades", 5)
        generate_reports = arguments.get("generate_reports", True)
        
        # Get all labs
        lab_api = cursor_mcp_server_instance.get_current_api("lab_api")
        labs = await lab_api.get_labs()
        
        analysis_results = []
        for lab in labs:
            try:
                # Analyze lab
                analysis_service = cursor_mcp_server_instance.get_current_api("analysis_service")
                analysis_result = await analysis_service.analyze_lab_comprehensive(
                    lab_id=lab.lab_id,
                    min_win_rate=min_win_rate,
                    min_trades=min_trades
                )
                analysis_results.append(analysis_result)
                
                # Generate report if requested
                if generate_reports:
                    reporting_service = cursor_mcp_server_instance.get_current_api("reporting_service")
                    await reporting_service.generate_report(
                        lab_id=lab.lab_id,
                        report_type="lab_analysis"
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to analyze lab {lab.lab_id}: {e}")
                continue
        
        return [TextContent(type="text", text=json.dumps([result.dict() for result in analysis_results], indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error analyzing all labs: {str(e)}")]
