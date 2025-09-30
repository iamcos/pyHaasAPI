"""
Miro API Client for pyHaasAPI Integration

Provides comprehensive Miro API integration for:
- Board management and creation
- Real-time updates and webhooks
- Interactive elements (buttons, cards, widgets)
- Data visualization and reporting
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


@dataclass
class MiroBoard:
    """Represents a Miro board"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    owner_id: Optional[str] = None
    team_id: Optional[str] = None


@dataclass
class MiroItem:
    """Represents a Miro board item (card, widget, etc.)"""
    id: str
    type: str  # 'card', 'text', 'shape', 'sticky_note', etc.
    x: float
    y: float
    width: float
    height: float
    content: Optional[str] = None
    style: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class MiroButton:
    """Represents an interactive button on Miro board"""
    id: str
    text: str
    x: float
    y: float
    width: float = 200.0
    height: float = 50.0
    style: Optional[Dict[str, Any]] = None
    action_data: Optional[Dict[str, Any]] = None


class MiroClient:
    """Miro API client for pyHaasAPI integration"""
    
    def __init__(self, access_token: str, team_id: Optional[str] = None):
        """
        Initialize Miro client
        
        Args:
            access_token: Miro API access token
            team_id: Optional team ID for team-specific operations
        """
        self.access_token = access_token
        self.team_id = team_id
        self.base_url = "https://api.miro.com/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request to Miro"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Miro API request failed: {e}")
            raise
    
    def get_boards(self, limit: int = 50) -> List[MiroBoard]:
        """Get all boards accessible to the user"""
        try:
            response = self._make_request("GET", f"boards?limit={limit}")
            boards = []
            
            for board_data in response.get("data", []):
                board = MiroBoard(
                    id=board_data["id"],
                    name=board_data["name"],
                    description=board_data.get("description"),
                    created_at=board_data.get("createdAt"),
                    modified_at=board_data.get("modifiedAt"),
                    owner_id=board_data.get("owner", {}).get("id"),
                    team_id=board_data.get("team", {}).get("id")
                )
                boards.append(board)
            
            return boards
            
        except Exception as e:
            logger.error(f"Failed to get boards: {e}")
            return []
    
    def get_board(self, board_id: str) -> Optional[MiroBoard]:
        """Get specific board by ID"""
        try:
            response = self._make_request("GET", f"boards/{board_id}")
            board_data = response
            
            return MiroBoard(
                id=board_data["id"],
                name=board_data["name"],
                description=board_data.get("description"),
                created_at=board_data.get("createdAt"),
                modified_at=board_data.get("modifiedAt"),
                owner_id=board_data.get("owner", {}).get("id"),
                team_id=board_data.get("team", {}).get("id")
            )
            
        except Exception as e:
            logger.error(f"Failed to get board {board_id}: {e}")
            return None
    
    def create_board(self, name: str, description: Optional[str] = None, 
                    team_id: Optional[str] = None) -> Optional[MiroBoard]:
        """Create a new Miro board"""
        try:
            data = {
                "name": name,
                "description": description or f"pyHaasAPI Board - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
            
            if team_id:
                data["teamId"] = team_id
            elif self.team_id:
                data["teamId"] = self.team_id
            
            response = self._make_request("POST", "boards", data)
            board_data = response
            
            return MiroBoard(
                id=board_data["id"],
                name=board_data["name"],
                description=board_data.get("description"),
                created_at=board_data.get("createdAt"),
                modified_at=board_data.get("modifiedAt"),
                owner_id=board_data.get("owner", {}).get("id"),
                team_id=board_data.get("team", {}).get("id")
            )
            
        except Exception as e:
            logger.error(f"Failed to create board: {e}")
            return None
    
    def get_board_items(self, board_id: str, limit: int = 100) -> List[MiroItem]:
        """Get all items from a board"""
        try:
            response = self._make_request("GET", f"boards/{board_id}/items?limit={limit}")
            items = []
            
            for item_data in response.get("data", []):
                item = MiroItem(
                    id=item_data["id"],
                    type=item_data["type"],
                    x=item_data.get("position", {}).get("x", 0),
                    y=item_data.get("position", {}).get("y", 0),
                    width=item_data.get("geometry", {}).get("width", 100),
                    height=item_data.get("geometry", {}).get("height", 100),
                    content=item_data.get("content", ""),
                    style=item_data.get("style", {}),
                    data=item_data.get("data", {})
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get board items for {board_id}: {e}")
            return []
    
    def create_text_item(self, board_id: str, text: str, x: float, y: float, 
                        width: float = 300, height: float = 100,
                        style: Optional[Dict] = None) -> Optional[str]:
        """Create a text item on the board"""
        try:
            data = {
                "type": "text",
                "content": text,
                "position": {"x": x, "y": y},
                "geometry": {"width": width, "height": height}
            }
            
            if style:
                data["style"] = style
            
            response = self._make_request("POST", f"boards/{board_id}/items", data)
            return response.get("id")
            
        except Exception as e:
            logger.error(f"Failed to create text item: {e}")
            return None
    
    def create_card_item(self, board_id: str, title: str, content: str, x: float, y: float,
                        width: float = 300, height: float = 200,
                        style: Optional[Dict] = None) -> Optional[str]:
        """Create a card item on the board"""
        try:
            data = {
                "type": "card",
                "data": {
                    "title": title,
                    "content": content
                },
                "position": {"x": x, "y": y},
                "geometry": {"width": width, "height": height}
            }
            
            if style:
                data["style"] = style
            
            response = self._make_request("POST", f"boards/{board_id}/items", data)
            return response.get("id")
            
        except Exception as e:
            logger.error(f"Failed to create card item: {e}")
            return None
    
    def create_shape_item(self, board_id: str, shape_type: str, x: float, y: float,
                         width: float = 200, height: float = 50,
                         content: Optional[str] = None,
                         style: Optional[Dict] = None) -> Optional[str]:
        """Create a shape item (button-like) on the board"""
        try:
            data = {
                "type": "shape",
                "data": {
                    "shape": shape_type,  # 'rectangle', 'round_rectangle', etc.
                    "content": content or ""
                },
                "position": {"x": x, "y": y},
                "geometry": {"width": width, "height": height}
            }
            
            if style:
                data["style"] = style
            
            response = self._make_request("POST", f"boards/{board_id}/items", data)
            return response.get("id")
            
        except Exception as e:
            logger.error(f"Failed to create shape item: {e}")
            return None
    
    def update_item(self, board_id: str, item_id: str, 
                   content: Optional[str] = None,
                   style: Optional[Dict] = None,
                   data: Optional[Dict] = None) -> bool:
        """Update an existing item on the board"""
        try:
            update_data = {}
            
            if content is not None:
                update_data["content"] = content
            
            if style is not None:
                update_data["style"] = style
            
            if data is not None:
                update_data["data"] = data
            
            if not update_data:
                return True  # Nothing to update
            
            self._make_request("PATCH", f"boards/{board_id}/items/{item_id}", update_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to update item {item_id}: {e}")
            return False
    
    def delete_item(self, board_id: str, item_id: str) -> bool:
        """Delete an item from the board"""
        try:
            self._make_request("DELETE", f"boards/{board_id}/items/{item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False
    
    def create_webhook(self, board_id: str, webhook_url: str, 
                      events: List[str] = None) -> Optional[str]:
        """Create a webhook for real-time updates"""
        try:
            if events is None:
                events = ["board:updated", "item:created", "item:updated", "item:deleted"]
            
            data = {
                "boardId": board_id,
                "url": webhook_url,
                "events": events
            }
            
            response = self._make_request("POST", "webhooks", data)
            return response.get("id")
            
        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            return None
    
    def get_webhooks(self) -> List[Dict]:
        """Get all webhooks"""
        try:
            response = self._make_request("GET", "webhooks")
            return response.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to get webhooks: {e}")
            return []
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        try:
            self._make_request("DELETE", f"webhooks/{webhook_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete webhook {webhook_id}: {e}")
            return False
