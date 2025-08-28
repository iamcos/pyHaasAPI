"""
Miro-HaasOnline Integration Bridge
Connects Miro boards with local Haas server via pyHaasAPI
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass

from pyHaasAPI import SyncExecutor, Authenticated
from pyHaasAPI.lab_manager import LabManager
from pyHaasAPI.market_manager import MarketManager

@dataclass
class MiroWidget:
    """Represents a Miro board widget"""
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    content: Dict[str, Any]

@dataclass
class HaasDashboardData:
    """Data structure for Haas server dashboard information"""
    accounts: List[Dict]
    bots: List[Dict]
    positions: List[Dict]
    market_data: Dict
    performance_metrics: Dict

class MiroHaasBridge:
    """Bridge between Miro boards and HaasOnline server"""
    
    def __init__(self, miro_access_token: str, haas_executor: SyncExecutor):
        self.miro_token = miro_access_token
        self.haas_executor = haas_executor
        self.miro_api_base = "https://api.miro.com/v2"
        self.headers = {
            "Authorization": f"Bearer {miro_access_token}",
            "Content-Type": "application/json"
        }
        self.lab_manager = LabManager(haas_executor)
        self.market_manager = MarketManager(haas_executor)
        
    async def create_trading_dashboard_board(self, team_id: str) -> str:
        """Create a new Miro board for trading dashboard"""
        board_data = {
            "name": f"HaasOnline Trading Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "description": "Real-time trading dashboard connected to HaasOnline server",
            "policy": {
                "permissionsPolicy": {
                    "collaborationToolsStartAccess": "all_editors",
                    "copyAccess": "anyone",
                    "sharingAccess": "team_members_with_editing_rights"
                }
            }
        }
        
        response = requests.post(
            f"{self.miro_api_base}/boards",
            headers=self.headers,
            json=board_data,
            params={"team_id": team_id}
        )
        
        if response.status_code == 201:
            board = response.json()
            board_id = board["id"]
            await self._setup_dashboard_layout(board_id)
            return board_id
        else:
            raise Exception(f"Failed to create board: {response.text}")
    
    async def _setup_dashboard_layout(self, board_id: str):
        """Set up the initial dashboard layout with sections"""
        widgets = [
            # Header
            {
                "type": "text",
                "data": {
                    "content": "<h1>HaasOnline Trading Dashboard</h1>",
                    "shape": "rectangle"
                },
                "style": {
                    "fillColor": "dark_blue",
                    "textAlign": "center"
                },
                "geometry": {"width": 800, "height": 100},
                "position": {"x": 0, "y": -400}
            },
            
            # Account Summary Section
            {
                "type": "text",
                "data": {
                    "content": "<h2>Account Summary</h2>",
                    "shape": "rectangle"
                },
                "style": {"fillColor": "light_blue"},
                "geometry": {"width": 300, "height": 60},
                "position": {"x": -350, "y": -250}
            },
            
            # Bot Status Section
            {
                "type": "text",
                "data": {
                    "content": "<h2>Trading Bots</h2>",
                    "shape": "rectangle"
                },
                "style": {"fillColor": "light_green"},
                "geometry": {"width": 300, "height": 60},
                "position": {"x": 0, "y": -250}
            },
            
            # Market Data Section
            {
                "type": "text",
                "data": {
                    "content": "<h2>Market Overview</h2>",
                    "shape": "rectangle"
                },
                "style": {"fillColor": "light_yellow"},
                "geometry": {"width": 300, "height": 60},
                "position": {"x": 350, "y": -250}
            }
        ]
        
        for widget in widgets:
            await self._create_widget(board_id, widget)
    
    async def _create_widget(self, board_id: str, widget_data: Dict):
        """Create a widget on the Miro board"""
        response = requests.post(
            f"{self.miro_api_base}/boards/{board_id}/items",
            headers=self.headers,
            json=widget_data
        )
        
        if response.status_code != 201:
            logging.error(f"Failed to create widget: {response.text}")
    
    async def update_dashboard_data(self, board_id: str):
        """Update the dashboard with fresh data from Haas server"""
        try:
            # Fetch data from Haas server
            dashboard_data = await self._fetch_haas_data()
            
            # Update account widgets
            await self._update_account_widgets(board_id, dashboard_data.accounts)
            
            # Update bot status widgets
            await self._update_bot_widgets(board_id, dashboard_data.bots)
            
            # Update market data widgets
            await self._update_market_widgets(board_id, dashboard_data.market_data)
            
            logging.info(f"Dashboard {board_id} updated successfully")
            
        except Exception as e:
            logging.error(f"Failed to update dashboard: {e}")
    
    async def _fetch_haas_data(self) -> HaasDashboardData:
        """Fetch current data from HaasOnline server"""
        # This would use your existing pyHaasAPI methods
        accounts = []  # self.haas_executor.get_accounts()
        bots = []      # self.haas_executor.get_bots()
        positions = [] # self.haas_executor.get_positions()
        market_data = {} # self.market_manager.get_market_overview()
        performance_metrics = {} # Calculate from positions/trades
        
        return HaasDashboardData(
            accounts=accounts,
            bots=bots,
            positions=positions,
            market_data=market_data,
            performance_metrics=performance_metrics
        )
    
    async def _update_account_widgets(self, board_id: str, accounts: List[Dict]):
        """Update account summary widgets"""
        y_offset = -150
        for i, account in enumerate(accounts):
            widget_data = {
                "type": "card",
                "data": {
                    "title": f"Account: {account.get('name', 'Unknown')}",
                    "description": f"Balance: ${account.get('balance', 0):.2f}\nP&L: ${account.get('pnl', 0):.2f}"
                },
                "style": {
                    "fillColor": "green" if account.get('pnl', 0) >= 0 else "red"
                },
                "geometry": {"width": 280, "height": 120},
                "position": {"x": -350, "y": y_offset + (i * 140)}
            }
            await self._create_widget(board_id, widget_data)
    
    async def _update_bot_widgets(self, board_id: str, bots: List[Dict]):
        """Update trading bot status widgets"""
        y_offset = -150
        for i, bot in enumerate(bots):
            status_color = "green" if bot.get('active', False) else "gray"
            widget_data = {
                "type": "card",
                "data": {
                    "title": f"Bot: {bot.get('name', 'Unknown')}",
                    "description": f"Status: {'Active' if bot.get('active', False) else 'Inactive'}\nProfit: ${bot.get('profit', 0):.2f}"
                },
                "style": {"fillColor": status_color},
                "geometry": {"width": 280, "height": 120},
                "position": {"x": 0, "y": y_offset + (i * 140)}
            }
            await self._create_widget(board_id, widget_data)
    
    async def _update_market_widgets(self, board_id: str, market_data: Dict):
        """Update market overview widgets"""
        # Create market summary cards
        markets = market_data.get('markets', [])
        y_offset = -150
        
        for i, market in enumerate(markets[:5]):  # Show top 5 markets
            widget_data = {
                "type": "card",
                "data": {
                    "title": f"{market.get('symbol', 'Unknown')}",
                    "description": f"Price: ${market.get('price', 0):.4f}\nChange: {market.get('change_24h', 0):.2f}%"
                },
                "style": {
                    "fillColor": "green" if market.get('change_24h', 0) >= 0 else "red"
                },
                "geometry": {"width": 280, "height": 120},
                "position": {"x": 350, "y": y_offset + (i * 140)}
            }
            await self._create_widget(board_id, widget_data)
    
    async def setup_webhook_listener(self, board_id: str, webhook_url: str):
        """Set up webhook to listen for Miro board interactions"""
        webhook_data = {
            "url": webhook_url,
            "events": ["item_created", "item_updated", "item_deleted"]
        }
        
        response = requests.post(
            f"{self.miro_api_base}/boards/{board_id}/webhooks",
            headers=self.headers,
            json=webhook_data
        )
        
        if response.status_code == 201:
            logging.info(f"Webhook set up for board {board_id}")
        else:
            logging.error(f"Failed to set up webhook: {response.text}")
    
    async def handle_miro_interaction(self, webhook_data: Dict):
        """Handle interactions from Miro board (e.g., clicking on bot cards)"""
        event_type = webhook_data.get("type")
        item_data = webhook_data.get("data", {})
        
        if event_type == "item_updated":
            # Check if it's a bot control interaction
            if "Bot:" in item_data.get("title", ""):
                bot_name = item_data["title"].replace("Bot: ", "")
                # Toggle bot status or perform other actions
                await self._handle_bot_interaction(bot_name, item_data)
    
    async def _handle_bot_interaction(self, bot_name: str, interaction_data: Dict):
        """Handle bot-related interactions from Miro"""
        # This would integrate with your bot management system
        logging.info(f"Bot interaction for {bot_name}: {interaction_data}")
        # Example: Start/stop bot based on interaction
        # self.lab_manager.toggle_bot_status(bot_name)

# Usage example
async def main():
    # Initialize with your tokens
    miro_token = "your_miro_access_token"
    haas_executor = SyncExecutor()  # Your authenticated executor
    
    bridge = MiroHaasBridge(miro_token, haas_executor)
    
    # Create dashboard board
    team_id = "your_miro_team_id"
    board_id = await bridge.create_trading_dashboard_board(team_id)
    
    # Set up real-time updates
    while True:
        await bridge.update_dashboard_data(board_id)
        await asyncio.sleep(30)  # Update every 30 seconds

if __name__ == "__main__":
    asyncio.run(main())