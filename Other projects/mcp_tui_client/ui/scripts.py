"""
Script Editor View

Script management and development environment with syntax highlighting.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, TextArea


class ScriptListPanel(Widget):
    """Panel with script list and organization"""
    
    def compose(self) -> ComposeResult:
        yield Static("HaasScripts", classes="panel-title")
        yield Static("📁 Strategies/")
        yield Static("  📄 RSI_Strategy_v2.haas")
        yield Static("  📄 MACD_Crossover.haas")
        yield Static("  📄 Grid_Trading.haas")
        yield Static("📁 Indicators/")
        yield Static("  📄 Custom_RSI.haas")
        yield Static("  📄 Bollinger_Bands.haas")
        yield Static("📁 Templates/")
        yield Static("  📄 Basic_Strategy.haas")
        yield Static("  📄 Advanced_Template.haas")


class ScriptEditorPanel(Widget):
    """Panel with script editor and syntax highlighting"""
    
    def compose(self) -> ComposeResult:
        yield Static("Script Editor: RSI_Strategy_v2.haas", classes="panel-title")
        editor = TextArea(
            text="""-- RSI Strategy v2
-- Advanced RSI-based trading strategy with dynamic parameters

local rsi_period = 14
local rsi_oversold = 30
local rsi_overbought = 70
local position_size = 0.1

-- Get price data
local prices = ClosePrices()
local rsi = RSI(prices, rsi_period)

-- Check if we have enough data
if #rsi > 0 then
    local current_rsi = tonumber(rsi[#rsi]) or 0
    local current_price = tonumber(prices[#prices]) or 0
    
    -- Buy signal
    if current_rsi < rsi_oversold then
        Log("RSI Oversold: " .. current_rsi .. " - BUY Signal")
        if GetBaseBalance() > position_size then
            PlaceBuyOrder(position_size, current_price)
        end
    
    -- Sell signal
    elseif current_rsi > rsi_overbought then
        Log("RSI Overbought: " .. current_rsi .. " - SELL Signal")
        if GetQuoteBalance() > 0 then
            PlaceSellOrder(GetQuoteBalance(), current_price)
        end
    end
end""",
            language="lua",
            theme="monokai"
        )
        yield editor


class ScriptValidationPanel(Widget):
    """Panel with script validation and compilation results"""
    
    def compose(self) -> ComposeResult:
        yield Static("Validation Results", classes="panel-title")
        yield Static("✅ Syntax: Valid")
        yield Static("✅ Compilation: Success")
        yield Static("⚠️ Warning: Line 15 - Consider null check")
        yield Static("💡 Suggestion: Add error handling for API calls")
        yield Static("")
        yield Static("Script Statistics:")
        yield Static("• Lines of Code: 28")
        yield Static("• Functions Used: 8")
        yield Static("• Variables: 6")
        yield Static("• Complexity Score: Medium")


class ScriptActionsPanel(Widget):
    """Panel with script actions and tools"""
    
    def compose(self) -> ComposeResult:
        yield Static("Script Actions", classes="panel-title")
        yield Static("File Operations:")
        yield Static("• [Ctrl+S] Save Script")
        yield Static("• [Ctrl+N] New Script")
        yield Static("• [Ctrl+O] Open Script")
        yield Static("")
        yield Static("Development:")
        yield Static("• [F5] Validate Script")
        yield Static("• [F6] Quick Test")
        yield Static("• [F7] Create Lab")
        yield Static("• [F8] Format Code")


class ScriptEditorView(Widget):
    """Script management and development environment"""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            ScriptListPanel(classes="panel"),
            ScriptEditorPanel(classes="panel editor"),
            classes="script-main"
        )
        yield Horizontal(
            ScriptValidationPanel(classes="panel"),
            ScriptActionsPanel(classes="panel"),
            classes="script-tools"
        )
    
    def set_mcp_client(self, mcp_client):
        """Set MCP client for data updates"""
        self.mcp_client = mcp_client
    
    async def refresh_data(self):
        """Refresh script data"""
        # TODO: Implement data refresh
        pass