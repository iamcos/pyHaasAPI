"""
Workflow Designer View

Node-based workflow designer for creating modular trading workflows.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static


class NodeLibraryPanel(Widget):
    """Panel with available workflow nodes"""
    
    def compose(self) -> ComposeResult:
        yield Static("Node Library", classes="panel-title")
        yield Static("📊 Data Sources:")
        yield Static("  • Market Data")
        yield Static("  • Account Info")
        yield Static("  • Historical Data")
        yield Static("")
        yield Static("🧪 Lab Operations:")
        yield Static("  • Create Lab")
        yield Static("  • Run Backtest")
        yield Static("  • Optimize Parameters")
        yield Static("")
        yield Static("🤖 Bot Operations:")
        yield Static("  • Deploy Bot")
        yield Static("  • Manage Bot")
        yield Static("  • Monitor Performance")
        yield Static("")
        yield Static("📈 Analysis:")
        yield Static("  • Performance Metrics")
        yield Static("  • Risk Analysis")
        yield Static("  • Chart Generator")


class WorkflowCanvasPanel(Widget):
    """Panel with workflow design canvas"""
    
    def compose(self) -> ComposeResult:
        yield Static("Workflow Canvas: Multi-Strategy Backtest", classes="panel-title")
        yield Static("""
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ Market Data │───▶│ Create Lab  │───▶│ Run Backtest│
    │   BTC/USDT  │    │ RSI Strategy│    │   2023-2024 │
    └─────────────┘    └─────────────┘    └─────────────┘
                                                 │
                                                 ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ Performance │◀───│   Analysis  │◀───│   Results   │
    │   Report    │    │   Engine    │    │   Parser    │
    └─────────────┘    └─────────────┘    └─────────────┘
                                                 │
                                                 ▼
                       ┌─────────────┐    ┌─────────────┐
                       │ Deploy Bot  │◀───│ Validation  │
                       │  (if good)  │    │   Check     │
                       └─────────────┘    └─────────────┘
        """)


class WorkflowPropertiesPanel(Widget):
    """Panel with workflow and node properties"""
    
    def compose(self) -> ComposeResult:
        yield Static("Node Properties", classes="panel-title")
        yield Static("Selected: Create Lab")
        yield Static("")
        yield Static("Configuration:")
        yield Static("• Script: RSI_Strategy_v2")
        yield Static("• Account: Test_Account")
        yield Static("• Market: BTC/USDT")
        yield Static("• Parameters:")
        yield Static("  - RSI Period: 14")
        yield Static("  - Oversold: 30")
        yield Static("  - Overbought: 70")
        yield Static("")
        yield Static("Connections:")
        yield Static("• Input: Market Data")
        yield Static("• Output: Lab Instance")


class WorkflowExecutionPanel(Widget):
    """Panel with workflow execution status"""
    
    def compose(self) -> ComposeResult:
        yield Static("Execution Status", classes="panel-title")
        yield Static("Workflow: Multi-Strategy Backtest")
        yield Static("Status: 🟢 Running")
        yield Static("Progress: 3/6 nodes completed")
        yield Static("")
        yield Static("Node Status:")
        yield Static("✅ Market Data - Complete")
        yield Static("✅ Create Lab - Complete")
        yield Static("🟡 Run Backtest - Running (75%)")
        yield Static("⏳ Results Parser - Waiting")
        yield Static("⏳ Analysis Engine - Waiting")
        yield Static("⏳ Performance Report - Waiting")
        yield Static("")
        yield Static("ETA: ~45 minutes")


class WorkflowDesignerView(Widget):
    """Node-based workflow designer interface"""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            NodeLibraryPanel(classes="panel"),
            WorkflowCanvasPanel(classes="panel canvas"),
            classes="workflow-main"
        )
        yield Horizontal(
            WorkflowPropertiesPanel(classes="panel"),
            WorkflowExecutionPanel(classes="panel"),
            classes="workflow-tools"
        )
    
    def set_mcp_client(self, mcp_client):
        """Set MCP client for data updates"""
        self.mcp_client = mcp_client
    
    async def refresh_data(self):
        """Refresh workflow data"""
        # TODO: Implement data refresh
        pass