"""
Menu System Components

Hierarchical menu system with keyboard navigation and context menus.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

from textual.widget import Widget
from textual.widgets import Button, Label, Tree, ListView, ListItem, Static
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key, Click
from textual.coordinate import Coordinate


class MenuItemType(Enum):
    """Types of menu items"""
    ACTION = "action"
    SUBMENU = "submenu"
    SEPARATOR = "separator"
    TOGGLE = "toggle"
    RADIO = "radio"


@dataclass
class MenuItem:
    """Menu item definition"""
    id: str
    label: str
    item_type: MenuItemType = MenuItemType.ACTION
    action: Optional[Callable] = None
    shortcut: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    checked: bool = False
    submenu: Optional[List['MenuItem']] = None
    help_text: Optional[str] = None
    
    def __post_init__(self):
        if self.submenu is None:
            self.submenu = []


class MenuBar(Container):
    """Top-level menu bar with dropdown menus"""
    
    DEFAULT_CSS = """
    MenuBar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        layout: horizontal;
    }
    
    MenuBar .menu-item {
        height: 1;
        padding: 0 2;
        background: transparent;
        border: none;
        color: $text;
    }
    
    MenuBar .menu-item:hover {
        background: $accent;
    }
    
    MenuBar .menu-item.active {
        background: $accent;
        color: $text;
    }
    
    MenuBar .dropdown-menu {
        position: absolute;
        z-index: 100;
        background: $surface;
        border: solid $primary;
        min-width: 20;
        max-height: 20;
    }
    """
    
    active_menu = reactive("")
    
    def __init__(self, menus: List[MenuItem] = None, **kwargs):
        super().__init__(**kwargs)
        self.menus = menus or []
        self.dropdown_visible = False
        self.current_dropdown: Optional[Widget] = None
    
    def compose(self) -> ComposeResult:
        """Compose menu bar"""
        for menu in self.menus:
            if menu.visible:
                button = Button(
                    menu.label,
                    variant="default",
                    classes="menu-item",
                    id=f"menu-{menu.id}"
                )
                yield button
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle menu button press"""
        button_id = event.button.id
        if button_id and button_id.startswith("menu-"):
            menu_id = button_id[5:]  # Remove "menu-" prefix
            await self.toggle_dropdown(menu_id)
    
    async def toggle_dropdown(self, menu_id: str) -> None:
        """Toggle dropdown menu"""
        menu_item = next((m for m in self.menus if m.id == menu_id), None)
        if not menu_item or not menu_item.submenu:
            return
        
        # Close existing dropdown
        if self.current_dropdown:
            await self.current_dropdown.remove()
            self.current_dropdown = None
        
        if self.active_menu == menu_id:
            # Close if same menu
            self.active_menu = ""
            self.dropdown_visible = False
        else:
            # Open new dropdown
            self.active_menu = menu_id
            self.dropdown_visible = True
            await self.show_dropdown(menu_item)
    
    async def show_dropdown(self, menu_item: MenuItem) -> None:
        """Show dropdown menu"""
        dropdown = DropdownMenu(menu_item.submenu, parent_menu=self)
        dropdown.add_class("dropdown-menu")
        
        # Position dropdown below the menu button
        button = self.query_one(f"#menu-{menu_item.id}", Button)
        dropdown.styles.left = button.region.x
        dropdown.styles.top = 1  # Below menu bar
        
        self.current_dropdown = dropdown
        await self.app.mount(dropdown)
    
    async def close_dropdown(self) -> None:
        """Close current dropdown"""
        if self.current_dropdown:
            await self.current_dropdown.remove()
            self.current_dropdown = None
        self.active_menu = ""
        self.dropdown_visible = False
    
    def watch_active_menu(self, menu_id: str) -> None:
        """React to active menu changes"""
        # Update button states
        for menu in self.menus:
            try:
                button = self.query_one(f"#menu-{menu.id}", Button)
                if menu.id == menu_id:
                    button.add_class("active")
                else:
                    button.remove_class("active")
            except:
                pass


class DropdownMenu(Container):
    """Dropdown menu widget"""
    
    DEFAULT_CSS = """
    DropdownMenu {
        background: $surface;
        border: solid $primary;
        padding: 1;
        min-width: 20;
        max-height: 20;
        overflow-y: auto;
    }
    
    DropdownMenu .menu-item {
        height: 1;
        width: 1fr;
        padding: 0 1;
        background: transparent;
        border: none;
        text-align: left;
    }
    
    DropdownMenu .menu-item:hover {
        background: $accent;
    }
    
    DropdownMenu .menu-item:disabled {
        color: $text-muted;
        background: transparent;
    }
    
    DropdownMenu .menu-separator {
        height: 1;
        width: 1fr;
        background: $primary;
        margin: 1 0;
    }
    
    DropdownMenu .menu-shortcut {
        color: $text-muted;
        text-align: right;
    }
    """
    
    def __init__(self, items: List[MenuItem], parent_menu: MenuBar = None, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.parent_menu = parent_menu
    
    def compose(self) -> ComposeResult:
        """Compose dropdown menu"""
        for item in self.items:
            if not item.visible:
                continue
            
            if item.item_type == MenuItemType.SEPARATOR:
                yield Static("", classes="menu-separator")
            else:
                # Create menu item button
                label_text = item.label
                if item.icon:
                    label_text = f"{item.icon} {label_text}"
                if item.checked and item.item_type == MenuItemType.TOGGLE:
                    label_text = f"✓ {label_text}"
                
                item_container = Horizontal()
                
                button = Button(
                    label_text,
                    variant="default",
                    classes="menu-item",
                    disabled=not item.enabled,
                    id=f"item-{item.id}"
                )
                item_container.mount(button)
                
                # Add shortcut display
                if item.shortcut:
                    shortcut_label = Label(item.shortcut, classes="menu-shortcut")
                    item_container.mount(shortcut_label)
                
                yield item_container
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle menu item selection"""
        button_id = event.button.id
        if button_id and button_id.startswith("item-"):
            item_id = button_id[5:]  # Remove "item-" prefix
            item = next((i for i in self.items if i.id == item_id), None)
            
            if item and item.enabled:
                # Execute action
                if item.action:
                    await item.action()
                
                # Handle toggle items
                if item.item_type == MenuItemType.TOGGLE:
                    item.checked = not item.checked
                
                # Close dropdown
                if self.parent_menu:
                    await self.parent_menu.close_dropdown()
    
    async def on_key(self, event: Key) -> None:
        """Handle keyboard navigation"""
        if event.key == "escape":
            if self.parent_menu:
                await self.parent_menu.close_dropdown()
            event.prevent_default()


class ContextMenu(DropdownMenu):
    """Context menu that appears on right-click"""
    
    def __init__(self, items: List[MenuItem], **kwargs):
        super().__init__(items, **kwargs)
        self.add_class("context-menu")
    
    @classmethod
    async def show_at(cls, app, items: List[MenuItem], position: Coordinate) -> 'ContextMenu':
        """Show context menu at specific position"""
        context_menu = cls(items)
        context_menu.styles.position = "absolute"
        context_menu.styles.left = position.x
        context_menu.styles.top = position.y
        context_menu.styles.z_index = 1000
        
        await app.mount(context_menu)
        return context_menu
    
    async def on_click(self, event: Click) -> None:
        """Close menu when clicking outside"""
        # Check if click is outside the menu
        if not self.region.contains(event.screen_coordinate):
            await self.remove()


class HierarchicalMenu(Container):
    """Hierarchical menu with tree-like navigation"""
    
    DEFAULT_CSS = """
    HierarchicalMenu {
        height: 1fr;
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    HierarchicalMenu .menu-tree {
        height: 1fr;
        width: 1fr;
    }
    
    HierarchicalMenu .menu-breadcrumb {
        dock: top;
        height: 1;
        background: $surface;
        padding: 0 1;
    }
    """
    
    def __init__(self, root_items: List[MenuItem], **kwargs):
        super().__init__(**kwargs)
        self.root_items = root_items
        self.current_path: List[str] = []
    
    def compose(self) -> ComposeResult:
        """Compose hierarchical menu"""
        yield Label("", classes="menu-breadcrumb", id="breadcrumb")
        yield Tree("Menu", classes="menu-tree", id="menu-tree")
    
    async def on_mount(self) -> None:
        """Initialize menu tree"""
        await self._build_tree()
    
    async def _build_tree(self) -> None:
        """Build the menu tree"""
        tree = self.query_one("#menu-tree", Tree)
        tree.clear()
        
        # Add root items
        for item in self.root_items:
            if item.visible:
                node = tree.root.add(item.label, data=item)
                if item.submenu:
                    await self._add_submenu_items(node, item.submenu)
    
    async def _add_submenu_items(self, parent_node, items: List[MenuItem]) -> None:
        """Add submenu items to tree node"""
        for item in items:
            if item.visible:
                node = parent_node.add(item.label, data=item)
                if item.submenu:
                    await self._add_submenu_items(node, item.submenu)
    
    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection"""
        node = event.node
        if node.data and isinstance(node.data, MenuItem):
            item = node.data
            
            # Update breadcrumb
            self._update_breadcrumb(node)
            
            # Execute action if available
            if item.action and item.item_type == MenuItemType.ACTION:
                await item.action()
    
    def _update_breadcrumb(self, node) -> None:
        """Update breadcrumb navigation"""
        path_parts = []
        current = node
        
        while current and current.parent:
            if current.data and isinstance(current.data, MenuItem):
                path_parts.append(current.data.label)
            current = current.parent
        
        path_parts.reverse()
        breadcrumb_text = " > ".join(path_parts)
        
        try:
            breadcrumb = self.query_one("#breadcrumb", Label)
            breadcrumb.update(breadcrumb_text)
        except:
            pass


class MenuSystem(Container):
    """Complete menu system with menu bar and context menu support"""
    
    BINDINGS = [
        Binding("f10", "toggle_menu", "Menu", show=False),
        Binding("alt+f", "show_file_menu", "File", show=False),
        Binding("alt+e", "show_edit_menu", "Edit", show=False),
        Binding("alt+v", "show_view_menu", "View", show=False),
        Binding("alt+h", "show_help_menu", "Help", show=False),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_definitions = self._create_default_menus()
        self.context_menu_providers: Dict[str, Callable] = {}
    
    def compose(self) -> ComposeResult:
        """Compose menu system"""
        yield MenuBar(self.menu_definitions, id="menu-bar")
    
    def _create_default_menus(self) -> List[MenuItem]:
        """Create default application menus"""
        return [
            MenuItem(
                id="file",
                label="File",
                item_type=MenuItemType.SUBMENU,
                submenu=[
                    MenuItem(
                        id="new",
                        label="New",
                        action=self.action_new,
                        shortcut="Ctrl+N",
                        icon="📄"
                    ),
                    MenuItem(
                        id="open",
                        label="Open",
                        action=self.action_open,
                        shortcut="Ctrl+O",
                        icon="📂"
                    ),
                    MenuItem(
                        id="save",
                        label="Save",
                        action=self.action_save,
                        shortcut="Ctrl+S",
                        icon="💾"
                    ),
                    MenuItem(
                        id="sep1",
                        label="",
                        item_type=MenuItemType.SEPARATOR
                    ),
                    MenuItem(
                        id="exit",
                        label="Exit",
                        action=self.action_exit,
                        shortcut="Ctrl+Q",
                        icon="🚪"
                    ),
                ]
            ),
            MenuItem(
                id="edit",
                label="Edit",
                item_type=MenuItemType.SUBMENU,
                submenu=[
                    MenuItem(
                        id="undo",
                        label="Undo",
                        action=self.action_undo,
                        shortcut="Ctrl+Z",
                        icon="↶"
                    ),
                    MenuItem(
                        id="redo",
                        label="Redo",
                        action=self.action_redo,
                        shortcut="Ctrl+Y",
                        icon="↷"
                    ),
                    MenuItem(
                        id="sep2",
                        label="",
                        item_type=MenuItemType.SEPARATOR
                    ),
                    MenuItem(
                        id="cut",
                        label="Cut",
                        action=self.action_cut,
                        shortcut="Ctrl+X",
                        icon="✂"
                    ),
                    MenuItem(
                        id="copy",
                        label="Copy",
                        action=self.action_copy,
                        shortcut="Ctrl+C",
                        icon="📋"
                    ),
                    MenuItem(
                        id="paste",
                        label="Paste",
                        action=self.action_paste,
                        shortcut="Ctrl+V",
                        icon="📄"
                    ),
                ]
            ),
            MenuItem(
                id="view",
                label="View",
                item_type=MenuItemType.SUBMENU,
                submenu=[
                    MenuItem(
                        id="dashboard",
                        label="Dashboard",
                        action=lambda: self.app.action_show_dashboard(),
                        shortcut="F1",
                        icon="📊"
                    ),
                    MenuItem(
                        id="bots",
                        label="Bot Management",
                        action=lambda: self.app.action_show_bots(),
                        shortcut="F2",
                        icon="🤖"
                    ),
                    MenuItem(
                        id="labs",
                        label="Lab Management",
                        action=lambda: self.app.action_show_labs(),
                        shortcut="F3",
                        icon="🧪"
                    ),
                    MenuItem(
                        id="scripts",
                        label="Script Editor",
                        action=lambda: self.app.action_show_scripts(),
                        shortcut="F4",
                        icon="📝"
                    ),
                    MenuItem(
                        id="workflows",
                        label="Workflow Designer",
                        action=lambda: self.app.action_show_workflows(),
                        shortcut="F5",
                        icon="🔄"
                    ),
                    MenuItem(
                        id="markets",
                        label="Market Data",
                        action=lambda: self.app.action_show_markets(),
                        shortcut="F6",
                        icon="📈"
                    ),
                    MenuItem(
                        id="analytics",
                        label="Analytics",
                        action=lambda: self.app.action_show_analytics(),
                        shortcut="F7",
                        icon="📊"
                    ),
                    MenuItem(
                        id="settings",
                        label="Settings",
                        action=lambda: self.app.action_show_settings(),
                        shortcut="F8",
                        icon="⚙"
                    ),
                ]
            ),
            MenuItem(
                id="help",
                label="Help",
                item_type=MenuItemType.SUBMENU,
                submenu=[
                    MenuItem(
                        id="help_contents",
                        label="Help Contents",
                        action=self.action_help,
                        shortcut="F1",
                        icon="❓"
                    ),
                    MenuItem(
                        id="keyboard_shortcuts",
                        label="Keyboard Shortcuts",
                        action=self.action_shortcuts,
                        shortcut="Ctrl+?",
                        icon="⌨"
                    ),
                    MenuItem(
                        id="about",
                        label="About",
                        action=self.action_about,
                        icon="ℹ"
                    ),
                ]
            ),
        ]
    
    def register_context_menu_provider(self, context: str, provider: Callable) -> None:
        """Register context menu provider for specific context"""
        self.context_menu_providers[context] = provider
    
    async def show_context_menu(self, context: str, position: Coordinate) -> None:
        """Show context menu for specific context"""
        provider = self.context_menu_providers.get(context)
        if provider:
            items = await provider()
            if items:
                await ContextMenu.show_at(self.app, items, position)
    
    # Default menu actions (to be overridden by application)
    async def action_new(self) -> None:
        """New file action"""
        if hasattr(self.app, 'action_new'):
            await self.app.action_new()
    
    async def action_open(self) -> None:
        """Open file action"""
        if hasattr(self.app, 'action_open'):
            await self.app.action_open()
    
    async def action_save(self) -> None:
        """Save file action"""
        if hasattr(self.app, 'action_save'):
            await self.app.action_save()
    
    async def action_exit(self) -> None:
        """Exit application action"""
        self.app.exit()
    
    async def action_undo(self) -> None:
        """Undo action"""
        pass  # To be implemented
    
    async def action_redo(self) -> None:
        """Redo action"""
        pass  # To be implemented
    
    async def action_cut(self) -> None:
        """Cut action"""
        pass  # To be implemented
    
    async def action_copy(self) -> None:
        """Copy action"""
        pass  # To be implemented
    
    async def action_paste(self) -> None:
        """Paste action"""
        pass  # To be implemented
    
    async def action_help(self) -> None:
        """Show help action"""
        if hasattr(self.app, 'action_help'):
            await self.app.action_help()
    
    async def action_shortcuts(self) -> None:
        """Show keyboard shortcuts"""
        pass  # To be implemented
    
    async def action_about(self) -> None:
        """Show about dialog"""
        self.app.notify("MCP TUI Client v1.0\nHaasOnline Trading Interface", title="About")
    
    # Menu action handlers
    async def action_toggle_menu(self) -> None:
        """Toggle menu bar visibility"""
        menu_bar = self.query_one("#menu-bar", MenuBar)
        menu_bar.display = not menu_bar.display
    
    async def action_show_file_menu(self) -> None:
        """Show file menu"""
        menu_bar = self.query_one("#menu-bar", MenuBar)
        await menu_bar.toggle_dropdown("file")
    
    async def action_show_edit_menu(self) -> None:
        """Show edit menu"""
        menu_bar = self.query_one("#menu-bar", MenuBar)
        await menu_bar.toggle_dropdown("edit")
    
    async def action_show_view_menu(self) -> None:
        """Show view menu"""
        menu_bar = self.query_one("#menu-bar", MenuBar)
        await menu_bar.toggle_dropdown("view")
    
    async def action_show_help_menu(self) -> None:
        """Show help menu"""
        menu_bar = self.query_one("#menu-bar", MenuBar)
        await menu_bar.toggle_dropdown("help")