"""
Navigation Manager

Navigation history, breadcrumbs, and navigation state management.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from textual.widget import Widget
from textual.widgets import Button, Label, Static
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.app import ComposeResult


@dataclass
class NavigationState:
    """Navigation state information"""
    view_id: str
    view_name: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    scroll_position: int = 0
    selected_item: Optional[str] = None


class NavigationHistory:
    """Navigation history manager"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history: List[NavigationState] = []
        self.current_index = -1
    
    def push(self, state: NavigationState) -> None:
        """Push new navigation state"""
        # Remove any forward history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new state
        self.history.append(state)
        self.current_index = len(self.history) - 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
    
    def can_go_back(self) -> bool:
        """Check if can go back"""
        return self.current_index > 0
    
    def can_go_forward(self) -> bool:
        """Check if can go forward"""
        return self.current_index < len(self.history) - 1
    
    def go_back(self) -> Optional[NavigationState]:
        """Go back in history"""
        if self.can_go_back():
            self.current_index -= 1
            return self.history[self.current_index]
        return None
    
    def go_forward(self) -> Optional[NavigationState]:
        """Go forward in history"""
        if self.can_go_forward():
            self.current_index += 1
            return self.history[self.current_index]
        return None
    
    def get_current(self) -> Optional[NavigationState]:
        """Get current navigation state"""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index]
        return None
    
    def get_back_list(self, count: int = 10) -> List[NavigationState]:
        """Get list of previous states"""
        start_index = max(0, self.current_index - count)
        return self.history[start_index:self.current_index]
    
    def get_forward_list(self, count: int = 10) -> List[NavigationState]:
        """Get list of forward states"""
        end_index = min(len(self.history), self.current_index + count + 1)
        return self.history[self.current_index + 1:end_index]
    
    def clear(self) -> None:
        """Clear navigation history"""
        self.history.clear()
        self.current_index = -1


class Breadcrumb(Container):
    """Breadcrumb navigation widget"""
    
    DEFAULT_CSS = """
    Breadcrumb {
        dock: top;
        height: 1;
        background: $surface;
        layout: horizontal;
        align: center middle;
        padding: 0 1;
    }
    
    Breadcrumb .breadcrumb-item {
        height: 1;
        margin: 0;
        padding: 0 1;
        background: transparent;
        border: none;
        color: $text;
    }
    
    Breadcrumb .breadcrumb-item:hover {
        background: $accent;
        color: $text;
    }
    
    Breadcrumb .breadcrumb-separator {
        color: $text-muted;
        margin: 0 1;
    }
    
    Breadcrumb .breadcrumb-current {
        color: $accent;
        text-style: bold;
    }
    """
    
    path = reactive([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path_items: List[Dict[str, Any]] = []
        self.navigation_callback: Optional[Callable] = None
    
    def compose(self) -> ComposeResult:
        """Compose breadcrumb (initially empty)"""
        return []
    
    def set_path(self, path_items: List[Dict[str, Any]]) -> None:
        """Set breadcrumb path"""
        self.path_items = path_items
        self.path = [item.get("name", "") for item in path_items]
    
    def set_navigation_callback(self, callback: Callable) -> None:
        """Set callback for breadcrumb navigation"""
        self.navigation_callback = callback
    
    def watch_path(self, new_path: List[str]) -> None:
        """React to path changes"""
        self._rebuild_breadcrumb()
    
    def _rebuild_breadcrumb(self) -> None:
        """Rebuild breadcrumb display"""
        self.remove_children()
        
        if not self.path_items:
            return
        
        for i, item in enumerate(self.path_items):
            # Add separator (except for first item)
            if i > 0:
                separator = Label(">", classes="breadcrumb-separator")
                self.mount(separator)
            
            # Add breadcrumb item
            if i == len(self.path_items) - 1:
                # Current item (not clickable)
                current_label = Label(item.get("name", ""), classes="breadcrumb-current")
                self.mount(current_label)
            else:
                # Clickable item
                item_button = Button(
                    item.get("name", ""),
                    variant="default",
                    classes="breadcrumb-item",
                    id=f"breadcrumb-{i}"
                )
                self.mount(item_button)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle breadcrumb navigation"""
        button_id = event.button.id
        if button_id and button_id.startswith("breadcrumb-"):
            try:
                index = int(button_id[11:])  # Remove "breadcrumb-" prefix
                if 0 <= index < len(self.path_items):
                    item = self.path_items[index]
                    if self.navigation_callback:
                        await self.navigation_callback(item)
            except ValueError:
                pass


class NavigationManager(Container):
    """Complete navigation management system"""
    
    DEFAULT_CSS = """
    NavigationManager {
        dock: top;
        height: 3;
        background: $surface;
        layout: vertical;
    }
    
    NavigationManager .nav-controls {
        dock: top;
        height: 1;
        layout: horizontal;
        align: center middle;
        padding: 0 1;
    }
    
    NavigationManager .nav-button {
        margin: 0 1;
        min-width: 8;
    }
    
    NavigationManager .nav-info {
        width: 1fr;
        text-align: center;
        color: $text-muted;
    }
    
    NavigationManager .breadcrumb-container {
        height: 1;
    }
    """
    
    current_view = reactive("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = NavigationHistory()
        self.view_change_callback: Optional[Callable] = None
        self.breadcrumb_items: List[Dict[str, Any]] = []
    
    def compose(self) -> ComposeResult:
        """Compose navigation manager"""
        # Navigation controls
        controls = Horizontal(classes="nav-controls")
        
        back_button = Button(
            "◀ Back",
            variant="outline",
            classes="nav-button",
            id="nav-back",
            disabled=True
        )
        controls.mount(back_button)
        
        forward_button = Button(
            "Forward ▶",
            variant="outline",
            classes="nav-button",
            id="nav-forward",
            disabled=True
        )
        controls.mount(forward_button)
        
        nav_info = Label("", classes="nav-info", id="nav-info")
        controls.mount(nav_info)
        
        yield controls
        
        # Breadcrumb
        breadcrumb_container = Container(classes="breadcrumb-container")
        breadcrumb = Breadcrumb(id="breadcrumb")
        breadcrumb.set_navigation_callback(self._handle_breadcrumb_navigation)
        breadcrumb_container.mount(breadcrumb)
        yield breadcrumb_container
    
    def set_view_change_callback(self, callback: Callable) -> None:
        """Set callback for view changes"""
        self.view_change_callback = callback
    
    async def navigate_to(
        self,
        view_id: str,
        view_name: str,
        context: Dict[str, Any] = None,
        update_history: bool = True
    ) -> None:
        """Navigate to a view"""
        if update_history:
            # Save current state to history
            current_state = NavigationState(
                view_id=view_id,
                view_name=view_name,
                timestamp=datetime.now(),
                context=context or {}
            )
            self.history.push(current_state)
        
        self.current_view = view_id
        
        # Update navigation controls
        self._update_navigation_controls()
        
        # Trigger view change
        if self.view_change_callback:
            await self.view_change_callback(view_id, context or {})
    
    async def go_back(self) -> bool:
        """Go back in navigation history"""
        previous_state = self.history.go_back()
        if previous_state:
            await self.navigate_to(
                previous_state.view_id,
                previous_state.view_name,
                previous_state.context,
                update_history=False
            )
            return True
        return False
    
    async def go_forward(self) -> bool:
        """Go forward in navigation history"""
        next_state = self.history.go_forward()
        if next_state:
            await self.navigate_to(
                next_state.view_id,
                next_state.view_name,
                next_state.context,
                update_history=False
            )
            return True
        return False
    
    def set_breadcrumb(self, items: List[Dict[str, Any]]) -> None:
        """Set breadcrumb path"""
        self.breadcrumb_items = items
        breadcrumb = self.query_one("#breadcrumb", Breadcrumb)
        breadcrumb.set_path(items)
    
    def add_breadcrumb_item(self, name: str, view_id: str = None, context: Dict[str, Any] = None) -> None:
        """Add item to breadcrumb"""
        item = {
            "name": name,
            "view_id": view_id,
            "context": context or {}
        }
        self.breadcrumb_items.append(item)
        self.set_breadcrumb(self.breadcrumb_items)
    
    def clear_breadcrumb(self) -> None:
        """Clear breadcrumb"""
        self.breadcrumb_items.clear()
        self.set_breadcrumb([])
    
    async def _handle_breadcrumb_navigation(self, item: Dict[str, Any]) -> None:
        """Handle breadcrumb navigation"""
        view_id = item.get("view_id")
        context = item.get("context", {})
        
        if view_id and self.view_change_callback:
            await self.navigate_to(view_id, item.get("name", ""), context)
    
    def _update_navigation_controls(self) -> None:
        """Update navigation control states"""
        try:
            back_button = self.query_one("#nav-back", Button)
            forward_button = self.query_one("#nav-forward", Button)
            nav_info = self.query_one("#nav-info", Label)
            
            # Update button states
            back_button.disabled = not self.history.can_go_back()
            forward_button.disabled = not self.history.can_go_forward()
            
            # Update info
            current_state = self.history.get_current()
            if current_state:
                info_text = f"{current_state.view_name} | {len(self.history.history)} items in history"
                nav_info.update(info_text)
        except:
            pass  # Widgets might not be mounted yet
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button presses"""
        button_id = event.button.id
        
        if button_id == "nav-back":
            await self.go_back()
        elif button_id == "nav-forward":
            await self.go_forward()
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get navigation history summary"""
        return {
            "current_view": self.current_view,
            "history_length": len(self.history.history),
            "current_index": self.history.current_index,
            "can_go_back": self.history.can_go_back(),
            "can_go_forward": self.history.can_go_forward(),
            "recent_views": [
                {"view": state.view_name, "timestamp": state.timestamp.isoformat()}
                for state in self.history.get_back_list(5)
            ]
        }
    
    def watch_current_view(self, view_id: str) -> None:
        """React to current view changes"""
        self._update_navigation_controls()
        
        # Update breadcrumb for known views
        view_breadcrumbs = {
            "dashboard": [{"name": "Dashboard", "view_id": "dashboard"}],
            "bots": [
                {"name": "Dashboard", "view_id": "dashboard"},
                {"name": "Bot Management", "view_id": "bots"}
            ],
            "labs": [
                {"name": "Dashboard", "view_id": "dashboard"},
                {"name": "Lab Management", "view_id": "labs"}
            ],
            "scripts": [
                {"name": "Dashboard", "view_id": "dashboard"},
                {"name": "Script Editor", "view_id": "scripts"}
            ],
            "workflows": [
                {"name": "Dashboard", "view_id": "dashboard"},
                {"name": "Workflow Designer", "view_id": "workflows"}
            ],
            "markets": [
                {"name": "Dashboard", "view_id": "dashboard"},
                {"name": "Market Data", "view_id": "markets"}
            ],
            "analytics": [
                {"name": "Dashboard", "view_id": "dashboard"},
                {"name": "Analytics", "view_id": "analytics"}
            ],
            "settings": [
                {"name": "Dashboard", "view_id": "dashboard"},
                {"name": "Settings", "view_id": "settings"}
            ],
        }
        
        if view_id in view_breadcrumbs:
            self.set_breadcrumb(view_breadcrumbs[view_id])