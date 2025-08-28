"""
Market Data View

Real-time market data visualization and analysis.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, DataTable


class MarketListPanel(Widget):
    """Panel with market list and prices"""
    
    def compose(self) -> ComposeResult:
        yield Static("Market Data", classes="panel-title")
        table = DataTable()
        table.add_columns("Symbol", "Price", "24h Change", "Volume", "Status")
        table.add_rows([
            ("BTC/USDT", "$43,250.00", "+2.1%", "1.2B", "🟢"),
            ("ETH/USDT", "$2,680.50", "+1.8%", "850M", "🟢"),
            ("BNB/USDT", "$315.20", "-0.5%", "120M", "🟡"),
            ("ADA/USDT", "$0.485", "+3.2%", "95M", "🟢"),
            ("SOL/USDT", "$98.75", "+0.8%", "180M", "🟢"),
        ])
        yield table


class PriceChartPanel(Widget):
    """Panel with ASCII price chart"""
    
    def compose(self) -> ComposeResult:
        yield Static("BTC/USDT - 1H Chart", classes="panel-title")
        yield Static("""
    $43,500 ┤           ╭─╮
    $43,400 ┤         ╭─╯ ╰╮
    $43,300 ┤       ╭─╯    ╰─╮
    $43,200 ┤     ╭─╯        ╰╮
    $43,100 ┤   ╭─╯            ╰─╮
    $43,000 ┼───╯                ╰─
            12:00  14:00  16:00  18:00  20:00
        """)
        yield Static("")
        yield Static("Technical Indicators:")
        yield Static("• RSI(14): 65.2 (Neutral)")
        yield Static("• MACD: Bullish Crossover")
        yield Static("• BB: Price near upper band")
        yield Static("• Volume: Above average")


class OrderBookPanel(Widget):
    """Panel with order book visualization"""
    
    def compose(self) -> ComposeResult:
        yield Static("Order Book - BTC/USDT", classes="panel-title")
        yield Static("Asks (Sell Orders):")
        yield Static("$43,255.00  ████████░░  0.245 BTC")
        yield Static("$43,252.50  ██████░░░░  0.180 BTC")
        yield Static("$43,251.00  ████░░░░░░  0.125 BTC")
        yield Static("$43,250.50  ██░░░░░░░░  0.089 BTC")
        yield Static("")
        yield Static("Spread: $0.50 (0.001%)")
        yield Static("")
        yield Static("Bids (Buy Orders):")
        yield Static("$43,250.00  ██████████  0.320 BTC")
        yield Static("$43,249.50  ████████░░  0.275 BTC")
        yield Static("$43,248.00  ██████░░░░  0.195 BTC")
        yield Static("$43,247.50  ████░░░░░░  0.150 BTC")


class MarketStatsPanel(Widget):
    """Panel with market statistics"""
    
    def compose(self) -> ComposeResult:
        yield Static("Market Statistics", classes="panel-title")
        yield Static("24h Statistics:")
        yield Static("• High: $43,850.00")
        yield Static("• Low: $42,100.00")
        yield Static("• Volume: 1.2B USDT")
        yield Static("• Trades: 245,678")
        yield Static("")
        yield Static("Market Cap: $847.5B")
        yield Static("Dominance: 52.3%")
        yield Static("Fear & Greed: 68 (Greed)")
        yield Static("")
        yield Static("Exchange Status:")
        yield Static("🟢 Binance: Online")
        yield Static("🟢 Coinbase: Online")
        yield Static("🟡 Kraken: Maintenance")


class MarketDataView(Widget):
    """Real-time market data visualization interface"""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            MarketListPanel(classes="panel"),
            PriceChartPanel(classes="panel chart"),
            classes="market-main"
        )
        yield Horizontal(
            OrderBookPanel(classes="panel"),
            MarketStatsPanel(classes="panel"),
            classes="market-details"
        )
    
    def set_mcp_client(self, mcp_client):
        """Set MCP client for data updates"""
        self.mcp_client = mcp_client
    
    async def refresh_data(self):
        """Refresh market data"""
        # TODO: Implement real-time data refresh
        pass