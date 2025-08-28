"""
Help System

Contextual help and documentation system with keyboard shortcuts.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from textual.widget import Widget
from textual.widgets import (
    Button, Label, Tree, ListView, ListItem, Static, 
    TabbedContent, TabPane, Markdown, RichLog, Input
)
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.binding import Binding


class HelpCategory(Enum):
    """Categories of help content"""
    GETTING_STARTED = "getting_started"
    USER_GUIDE = "user_guide"
    KEYBOARD_SHORTCUTS = "keyboard_shortcuts"
    API_REFERENCE = "api_reference"
    TROUBLESHOOTING = "troubleshooting"
    FAQ = "faq"


@dataclass
class HelpTopic:
    """Help topic definition"""
    id: str
    title: str
    category: HelpCategory
    content: str
    keywords: List[str]
    related_topics: List[str]
    last_updated: str = ""


class HelpProvider(ABC):
    """Abstract base class for help content providers"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def get_topics(self) -> List[HelpTopic]:
        """Get all help topics from this provider"""
        pass
    
    @abstractmethod
    async def get_topic_content(self, topic_id: str) -> Optional[str]:
        """Get content for specific topic"""
        pass
    
    @abstractmethod
    async def search_topics(self, query: str) -> List[HelpTopic]:
        """Search topics by query"""
        pass


class StaticHelpProvider(HelpProvider):
    """Static help content provider"""
    
    def __init__(self):
        super().__init__("Static Help")
        self.topics = self._create_default_topics()
    
    def _create_default_topics(self) -> List[HelpTopic]:
        """Create default help topics"""
        return [
            HelpTopic(
                id="getting_started",
                title="Getting Started",
                category=HelpCategory.GETTING_STARTED,
                content="""
# Getting Started with MCP TUI Client

Welcome to the MCP TUI Client! This guide will help you get started with the terminal-based interface for HaasOnline trading.

## First Steps

1. **Connection Setup**: Configure your MCP server connection in Settings (F8)
2. **Dashboard Overview**: Start with the Dashboard (F1) to see system status
3. **Bot Management**: Use F2 to access bot management features
4. **Lab Management**: Use F3 for backtesting and strategy development

## Navigation

- Use function keys F1-F8 to switch between main views
- Use Ctrl+F for global search
- Use Ctrl+H for help (this screen)
- Use Ctrl+Q to quit the application

## Quick Actions

- Ctrl+Shift+B: Quick bot creation
- Ctrl+Shift+L: Quick lab setup
- Ctrl+Shift+W: Quick workflow creation

For more detailed information, explore the other help topics.
                """,
                keywords=["start", "begin", "introduction", "setup", "first"],
                related_topics=["keyboard_shortcuts", "dashboard_overview"]
            ),
            
            HelpTopic(
                id="keyboard_shortcuts",
                title="Keyboard Shortcuts",
                category=HelpCategory.KEYBOARD_SHORTCUTS,
                content="""
# Keyboard Shortcuts

## Global Navigation
- **F1**: Dashboard
- **F2**: Bot Management
- **F3**: Lab Management
- **F4**: Script Editor
- **F5**: Workflow Designer
- **F6**: Market Data
- **F7**: Analytics
- **F8**: Settings

## Global Actions
- **Ctrl+Q**: Quit application
- **Ctrl+H**: Show help
- **Ctrl+R**: Refresh current view
- **Ctrl+F**: Global search
- **Ctrl+S**: Save (context-dependent)
- **Ctrl+O**: Open (context-dependent)
- **Ctrl+N**: New (context-dependent)

## Quick Actions
- **Ctrl+Shift+B**: Quick bot action
- **Ctrl+Shift+L**: Quick lab action
- **Ctrl+Shift+W**: Quick workflow action

## Menu System
- **F10**: Toggle menu bar
- **Alt+F**: File menu
- **Alt+E**: Edit menu
- **Alt+V**: View menu
- **Alt+H**: Help menu

## Navigation
- **Escape**: Cancel/Back
- **Tab**: Next field/element
- **Shift+Tab**: Previous field/element
- **Enter**: Confirm/Execute
- **Space**: Toggle/Select

## Context-Specific Shortcuts
Each view may have additional shortcuts. Check the footer bar for view-specific shortcuts.
                """,
                keywords=["shortcuts", "keys", "hotkeys", "navigation", "commands"],
                related_topics=["getting_started", "navigation_guide"]
            ),
            
            HelpTopic(
                id="bot_management",
                title="Bot Management",
                category=HelpCategory.USER_GUIDE,
                content="""
# Bot Management Guide

The Bot Management view (F2) provides comprehensive control over your trading bots.

## Bot Overview
- View all active and inactive bots
- Monitor real-time performance metrics
- Check bot status and health

## Bot Operations
- **Start/Stop**: Control bot execution
- **Pause/Resume**: Temporarily halt trading
- **Clone**: Duplicate bot configuration
- **Delete**: Remove bot (with confirmation)

## Performance Monitoring
- Real-time P&L tracking
- Trade history and statistics
- Risk metrics and exposure
- Performance charts

## Bot Configuration
- Trading pair settings
- Script assignment
- Risk parameters
- Account allocation

## Bulk Operations
- Select multiple bots for batch operations
- Start/stop multiple bots simultaneously
- Export bot configurations
- Import bot settings

## Troubleshooting
- Check bot logs for errors
- Verify account balances
- Confirm market connectivity
- Review script compilation status

For lab-to-bot conversion, see the Lab Management guide.
                """,
                keywords=["bot", "trading", "management", "performance", "monitoring"],
                related_topics=["lab_management", "script_editor", "troubleshooting"]
            ),
            
            HelpTopic(
                id="lab_management",
                title="Lab Management",
                category=HelpCategory.USER_GUIDE,
                content="""
# Lab Management Guide

The Lab Management view (F3) is your backtesting and strategy development environment.

## Creating Labs
1. Click "New Lab" or use Ctrl+Shift+L
2. Select trading pair and timeframe
3. Choose script and parameters
4. Set backtest period
5. Configure account settings

## Backtesting Features
- **Intelligent History**: Automatic period adjustment
- **Parameter Optimization**: Mixed algorithm optimization
- **Bulk Operations**: Test across multiple markets
- **Performance Analytics**: Comprehensive metrics

## Lab Operations
- **Run Backtest**: Execute strategy simulation
- **Clone Lab**: Duplicate for testing variations
- **Export Results**: Save backtest data
- **Deploy to Bot**: Convert successful lab to live bot

## Performance Analysis
- Return metrics (total, annualized, risk-adjusted)
- Drawdown analysis
- Trade statistics
- Sharpe ratio and other risk metrics
- Equity curve visualization

## Optimization
- Parameter sweep optimization
- Genetic algorithm optimization
- Walk-forward analysis
- Monte Carlo simulation

## Best Practices
- Test multiple timeframes
- Use sufficient historical data
- Consider transaction costs
- Validate on out-of-sample data
- Monitor overfitting

Converting a successful lab to a bot is seamless - just click "Deploy to Bot".
                """,
                keywords=["lab", "backtest", "strategy", "optimization", "testing"],
                related_topics=["bot_management", "script_editor", "analytics"]
            ),
            
            HelpTopic(
                id="workflow_designer",
                title="Workflow Designer",
                category=HelpCategory.USER_GUIDE,
                content="""
# Workflow Designer Guide

The Workflow Designer (F5) enables visual creation of complex trading workflows using node-based programming.

## Workflow Concepts
- **Nodes**: Individual processing units
- **Connections**: Data flow between nodes
- **Execution**: Sequential processing based on dependencies

## Node Types
- **Lab Nodes**: Execute backtests
- **Analysis Nodes**: Process results
- **Bot Nodes**: Manage bot operations
- **Data Nodes**: Market data and indicators
- **Logic Nodes**: Conditional processing
- **Output Nodes**: Notifications and actions

## Creating Workflows
1. Drag nodes from the library
2. Configure node parameters
3. Connect nodes with data flows
4. Validate workflow integrity
5. Execute and monitor progress

## Node Configuration
- Input/output port types
- Parameter settings
- Validation rules
- Error handling

## Execution
- Dependency resolution
- Parallel processing where possible
- Progress monitoring
- Error reporting and recovery

## Templates
- Pre-built workflow templates
- Strategy comparison workflows
- Optimization pipelines
- Risk management workflows

## Best Practices
- Start simple and build complexity
- Use descriptive node names
- Validate data types at connections
- Handle errors gracefully
- Document complex workflows

Workflows can be saved, shared, and scheduled for automatic execution.
                """,
                keywords=["workflow", "nodes", "visual", "automation", "pipeline"],
                related_topics=["lab_management", "bot_management", "script_editor"]
            ),
            
            HelpTopic(
                id="troubleshooting",
                title="Troubleshooting",
                category=HelpCategory.TROUBLESHOOTING,
                content="""
# Troubleshooting Guide

Common issues and solutions for the MCP TUI Client.

## Connection Issues

### MCP Server Connection Failed
- Check server URL in Settings (F8)
- Verify server is running
- Check network connectivity
- Confirm API credentials

### HaasOnline API Connection
- Verify API key and secret
- Check API permissions
- Confirm account access
- Test with HaasOnline web interface

## Performance Issues

### Slow Response Times
- Check network latency
- Reduce refresh intervals
- Limit concurrent operations
- Clear data cache

### High Memory Usage
- Restart application
- Reduce data retention periods
- Close unused views
- Check for memory leaks

## Bot Issues

### Bot Won't Start
- Check account balance
- Verify script compilation
- Confirm trading pair availability
- Review bot configuration

### Bot Stopped Unexpectedly
- Check bot logs
- Verify market connectivity
- Review error messages
- Check account status

## Lab Issues

### Backtest Fails
- Verify historical data availability
- Check script syntax
- Confirm parameter ranges
- Review error logs

### Slow Backtesting
- Reduce data range
- Optimize script performance
- Use fewer parameters
- Check system resources

## UI Issues

### Display Problems
- Resize terminal window
- Check color support
- Verify font compatibility
- Restart application

### Keyboard Shortcuts Not Working
- Check focus on correct element
- Verify shortcut conflicts
- Try alternative shortcuts
- Check terminal key mapping

## Getting Help
- Use Ctrl+H for contextual help
- Check application logs
- Contact support with error details
- Provide system information
                """,
                keywords=["troubleshooting", "problems", "issues", "errors", "help"],
                related_topics=["getting_started", "bot_management", "lab_management"]
            ),
        ]
    
    async def get_topics(self) -> List[HelpTopic]:
        """Get all help topics"""
        return self.topics
    
    async def get_topic_content(self, topic_id: str) -> Optional[str]:
        """Get content for specific topic"""
        topic = next((t for t in self.topics if t.id == topic_id), None)
        return topic.content if topic else None
    
    async def search_topics(self, query: str) -> List[HelpTopic]:
        """Search topics by query"""
        if not query.strip():
            return []
        
        query_lower = query.lower()
        matching_topics = []
        
        for topic in self.topics:
            # Search in title, keywords, and content
            if (query_lower in topic.title.lower() or
                any(query_lower in keyword for keyword in topic.keywords) or
                query_lower in topic.content.lower()):
                matching_topics.append(topic)
        
        return matching_topics


class KeyboardShortcuts(Container):
    """Keyboard shortcuts reference widget"""
    
    DEFAULT_CSS = """
    KeyboardShortcuts {
        height: 1fr;
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    KeyboardShortcuts .shortcuts-title {
        dock: top;
        height: 1;
        text-align: center;
        text-style: bold;
        background: $primary;
        color: $text;
    }
    
    KeyboardShortcuts .shortcuts-content {
        height: 1fr;
        padding: 1;
    }
    
    KeyboardShortcuts .shortcut-category {
        margin: 1 0;
        text-style: bold;
        color: $accent;
    }
    
    KeyboardShortcuts .shortcut-item {
        layout: horizontal;
        height: 1;
        margin: 0 0 0 2;
    }
    
    KeyboardShortcuts .shortcut-key {
        width: 20;
        color: $success;
        text-style: bold;
    }
    
    KeyboardShortcuts .shortcut-desc {
        width: 1fr;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shortcuts = self._get_shortcuts()
    
    def compose(self) -> ComposeResult:
        """Compose shortcuts display"""
        yield Label("Keyboard Shortcuts", classes="shortcuts-title")
        yield Container(classes="shortcuts-content", id="shortcuts-content")
    
    async def on_mount(self) -> None:
        """Build shortcuts display"""
        content = self.query_one("#shortcuts-content")
        
        for category, shortcuts in self.shortcuts.items():
            # Category header
            content.mount(Label(category, classes="shortcut-category"))
            
            # Shortcuts in category
            for key, description in shortcuts.items():
                shortcut_item = Horizontal(classes="shortcut-item")
                shortcut_item.mount(Label(key, classes="shortcut-key"))
                shortcut_item.mount(Label(description, classes="shortcut-desc"))
                content.mount(shortcut_item)
    
    def _get_shortcuts(self) -> Dict[str, Dict[str, str]]:
        """Get organized shortcuts"""
        return {
            "Navigation": {
                "F1": "Dashboard",
                "F2": "Bot Management",
                "F3": "Lab Management",
                "F4": "Script Editor",
                "F5": "Workflow Designer",
                "F6": "Market Data",
                "F7": "Analytics",
                "F8": "Settings",
            },
            "Global Actions": {
                "Ctrl+Q": "Quit application",
                "Ctrl+H": "Show help",
                "Ctrl+R": "Refresh current view",
                "Ctrl+F": "Global search",
                "Ctrl+S": "Save",
                "Ctrl+O": "Open",
                "Ctrl+N": "New",
                "Escape": "Cancel/Back",
            },
            "Quick Actions": {
                "Ctrl+Shift+B": "Quick bot action",
                "Ctrl+Shift+L": "Quick lab action",
                "Ctrl+Shift+W": "Quick workflow action",
            },
            "Menu System": {
                "F10": "Toggle menu bar",
                "Alt+F": "File menu",
                "Alt+E": "Edit menu",
                "Alt+V": "View menu",
                "Alt+H": "Help menu",
            },
        }


class ContextualHelp(Container):
    """Contextual help widget that shows relevant help for current context"""
    
    DEFAULT_CSS = """
    ContextualHelp {
        height: 1fr;
        width: 1fr;
        border: solid $accent;
        padding: 1;
    }
    
    ContextualHelp .help-title {
        dock: top;
        height: 1;
        text-style: bold;
        color: $accent;
    }
    
    ContextualHelp .help-content {
        height: 1fr;
        padding: 1 0;
    }
    """
    
    current_context = reactive("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_help = self._get_context_help()
    
    def compose(self) -> ComposeResult:
        """Compose contextual help"""
        yield Label("Context Help", classes="help-title")
        yield Container(classes="help-content", id="help-content")
    
    def set_context(self, context: str) -> None:
        """Set current context for help"""
        self.current_context = context
    
    def watch_current_context(self, context: str) -> None:
        """React to context changes"""
        self._update_help_content(context)
    
    def _update_help_content(self, context: str) -> None:
        """Update help content for context"""
        content_container = self.query_one("#help-content")
        content_container.remove_children()
        
        help_text = self.context_help.get(context, "No help available for this context.")
        help_widget = Static(help_text)
        content_container.mount(help_widget)
    
    def _get_context_help(self) -> Dict[str, str]:
        """Get context-specific help text"""
        return {
            "dashboard": """
Dashboard Overview:
- System status indicators
- Active bots summary
- Recent alerts and notifications
- Quick action buttons
- Performance overview

Use F1 to return to dashboard from any view.
            """,
            "bots": """
Bot Management:
- View all trading bots
- Start/stop/pause bots
- Monitor performance
- Configure settings
- View trade history

Double-click a bot to view details.
Use Ctrl+Shift+B for quick bot creation.
            """,
            "labs": """
Lab Management:
- Create and run backtests
- Optimize parameters
- Analyze results
- Deploy to bots
- Compare strategies

Use Ctrl+Shift+L for quick lab setup.
Click "Deploy to Bot" to go live.
            """,
            "scripts": """
Script Editor:
- Write HaasScript code
- Syntax highlighting
- Real-time validation
- Compile and test
- Manage script library

Use Ctrl+S to save scripts.
Use Ctrl+T to test compilation.
            """,
            "workflows": """
Workflow Designer:
- Visual node-based programming
- Drag and drop nodes
- Connect data flows
- Execute workflows
- Monitor progress

Use Ctrl+Shift+W for quick workflow creation.
Validate connections before execution.
            """,
            "markets": """
Market Data:
- Real-time price feeds
- Historical charts
- Technical indicators
- Market analysis
- Trading pairs

Use arrow keys to navigate charts.
Press 'R' to refresh data.
            """,
            "analytics": """
Analytics:
- Performance metrics
- Risk analysis
- Portfolio overview
- Comparative analysis
- Custom reports

Use filters to focus analysis.
Export reports with Ctrl+E.
            """,
            "settings": """
Settings:
- MCP server configuration
- API credentials
- UI preferences
- Notification settings
- Data management

Changes are saved automatically.
Restart may be required for some settings.
            """,
        }


class HelpSystem(Container):
    """Complete help system with topics, search, and contextual help"""
    
    DEFAULT_CSS = """
    HelpSystem {
        height: 1fr;
        width: 1fr;
    }
    
    HelpSystem .help-tabs {
        height: 1fr;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.providers: List[HelpProvider] = []
        self.all_topics: List[HelpTopic] = []
        self.current_topic: Optional[HelpTopic] = None
        
        # Add default provider
        self.add_provider(StaticHelpProvider())
    
    def compose(self) -> ComposeResult:
        """Compose help system"""
        with TabbedContent(classes="help-tabs"):
            with TabPane("Topics", id="topics-tab"):
                yield self._create_topics_view()
            
            with TabPane("Search", id="search-tab"):
                yield self._create_search_view()
            
            with TabPane("Shortcuts", id="shortcuts-tab"):
                yield KeyboardShortcuts()
            
            with TabPane("Context", id="context-tab"):
                yield ContextualHelp()
    
    def _create_topics_view(self) -> Widget:
        """Create topics browser view"""
        container = Horizontal()
        
        # Topic tree
        topic_tree = Tree("Help Topics", id="topic-tree")
        container.mount(topic_tree)
        
        # Topic content
        topic_content = Container(id="topic-content")
        container.mount(topic_content)
        
        return container
    
    def _create_search_view(self) -> Widget:
        """Create search view"""
        container = Vertical()
        
        # Search input
        search_container = Horizontal()
        search_input = Input(placeholder="Search help topics...", id="help-search")
        search_button = Button("Search", id="help-search-button")
        search_container.mount(search_input)
        search_container.mount(search_button)
        container.mount(search_container)
        
        # Search results
        search_results = Container(id="help-search-results")
        container.mount(search_results)
        
        return container
    
    def add_provider(self, provider: HelpProvider) -> None:
        """Add help content provider"""
        self.providers.append(provider)
        asyncio.create_task(self._refresh_topics())
    
    async def _refresh_topics(self) -> None:
        """Refresh topics from all providers"""
        all_topics = []
        for provider in self.providers:
            try:
                topics = await provider.get_topics()
                all_topics.extend(topics)
            except Exception:
                pass  # Handle provider errors gracefully
        
        self.all_topics = all_topics
        await self._build_topic_tree()
    
    async def _build_topic_tree(self) -> None:
        """Build topic tree"""
        try:
            topic_tree = self.query_one("#topic-tree", Tree)
            topic_tree.clear()
            
            # Group topics by category
            categories = {}
            for topic in self.all_topics:
                category = topic.category.value
                if category not in categories:
                    categories[category] = []
                categories[category].append(topic)
            
            # Add categories and topics to tree
            for category, topics in categories.items():
                category_node = topic_tree.root.add(category.replace("_", " ").title())
                for topic in topics:
                    category_node.add(topic.title, data=topic)
        except:
            pass  # Tree might not be mounted yet
    
    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle topic selection"""
        if event.tree.id == "topic-tree" and event.node.data:
            topic = event.node.data
            if isinstance(topic, HelpTopic):
                await self._show_topic_content(topic)
    
    async def _show_topic_content(self, topic: HelpTopic) -> None:
        """Show topic content"""
        try:
            content_container = self.query_one("#topic-content")
            content_container.remove_children()
            
            # Show topic content as markdown
            markdown_widget = Markdown(topic.content)
            content_container.mount(markdown_widget)
            
            self.current_topic = topic
        except:
            pass
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input"""
        if event.input.id == "help-search":
            query = event.value
            if len(query) >= 3:
                await self._search_help(query)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle search button"""
        if event.button.id == "help-search-button":
            search_input = self.query_one("#help-search", Input)
            await self._search_help(search_input.value)
    
    async def _search_help(self, query: str) -> None:
        """Search help topics"""
        results_container = self.query_one("#help-search-results")
        results_container.remove_children()
        
        if not query.strip():
            return
        
        # Search all providers
        all_results = []
        for provider in self.providers:
            try:
                results = await provider.search_topics(query)
                all_results.extend(results)
            except Exception:
                pass
        
        # Display results
        if all_results:
            results_list = ListView()
            for topic in all_results:
                item = ListItem(Label(f"{topic.title} ({topic.category.value})"))
                item.data = topic
                results_list.append(item)
            results_container.mount(results_list)
        else:
            results_container.mount(Label("No results found"))
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle search result selection"""
        if hasattr(event.item, 'data') and isinstance(event.item.data, HelpTopic):
            topic = event.item.data
            await self._show_topic_content(topic)
            
            # Switch to topics tab to show content
            tabbed_content = self.query_one(TabbedContent)
            tabbed_content.active = "topics-tab"


# Import asyncio for async operations
import asyncio