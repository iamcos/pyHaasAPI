"""
Analytics View

Advanced analytics and reporting interface.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, DataTable


class PortfolioOverviewPanel(Widget):
    """Panel with portfolio overview"""
    
    def compose(self) -> ComposeResult:
        yield Static("Portfolio Overview", classes="panel-title")
        yield Static("Total Value: $125,450.00")
        yield Static("24h P&L: +$2,345.67 (+1.9%)")
        yield Static("7d P&L: +$8,234.12 (+7.0%)")
        yield Static("30d P&L: +$15,678.90 (+14.3%)")
        yield Static("")
        yield Static("Asset Allocation:")
        yield Static("• BTC: 45.2% ($56,743)")
        yield Static("• ETH: 28.5% ($35,753)")
        yield Static("• Alts: 20.1% ($25,215)")
        yield Static("• Cash: 6.2% ($7,739)")


class PerformanceMetricsPanel(Widget):
    """Panel with performance metrics"""
    
    def compose(self) -> ComposeResult:
        yield Static("Performance Metrics", classes="panel-title")
        yield Static("Risk-Adjusted Returns:")
        yield Static("• Sharpe Ratio: 1.85")
        yield Static("• Sortino Ratio: 2.34")
        yield Static("• Calmar Ratio: 1.67")
        yield Static("")
        yield Static("Risk Metrics:")
        yield Static("• Max Drawdown: -8.2%")
        yield Static("• VaR (95%): -$2,450")
        yield Static("• Beta: 0.78")
        yield Static("• Volatility: 15.6%")
        yield Static("")
        yield Static("Trade Statistics:")
        yield Static("• Win Rate: 68.5%")
        yield Static("• Profit Factor: 2.34")
        yield Static("• Avg Win: +$145.67")
        yield Static("• Avg Loss: -$62.34")


class StrategyComparisonPanel(Widget):
    """Panel with strategy comparison"""
    
    def compose(self) -> ComposeResult:
        yield Static("Strategy Comparison (30d)", classes="panel-title")
        table = DataTable()
        table.add_columns("Strategy", "Return", "Sharpe", "Drawdown", "Trades")
        table.add_rows([
            ("RSI_Strategy", "+12.5%", "1.85", "-3.2%", "45"),
            ("MACD_Cross", "+8.9%", "1.42", "-5.1%", "32"),
            ("Grid_Trading", "+6.7%", "1.23", "-2.8%", "78"),
            ("Arbitrage", "+4.2%", "2.15", "-1.5%", "156"),
        ])
        yield table


class EquityCurvePanel(Widget):
    """Panel with equity curve visualization"""
    
    def compose(self) -> ComposeResult:
        yield Static("Equity Curve (6 months)", classes="panel-title")
        yield Static("""
    $130k ┤                     ╭─╮
    $125k ┤                   ╭─╯ ╰╮
    $120k ┤                 ╭─╯    ╰─╮
    $115k ┤               ╭─╯        ╰╮
    $110k ┤             ╭─╯            ╰─╮
    $105k ┤           ╭─╯                ╰╮
    $100k ┼───────────╯                   ╰─
          Aug  Sep  Oct  Nov  Dec  Jan  Feb
        """)
        yield Static("")
        yield Static("Key Events:")
        yield Static("• Oct: Strategy optimization (+8%)")
        yield Static("• Nov: Market volatility (-3%)")
        yield Static("• Dec: Strong performance (+12%)")
        yield Static("• Jan: Consolidation (+2%)")


class RiskAnalysisPanel(Widget):
    """Panel with risk analysis"""
    
    def compose(self) -> ComposeResult:
        yield Static("Risk Analysis", classes="panel-title")
        yield Static("Correlation Matrix:")
        yield Static("        BTC   ETH   ALT")
        yield Static("BTC    1.00  0.85  0.72")
        yield Static("ETH    0.85  1.00  0.78")
        yield Static("ALT    0.72  0.78  1.00")
        yield Static("")
        yield Static("Risk Exposure:")
        yield Static("• Market Risk: Medium")
        yield Static("• Liquidity Risk: Low")
        yield Static("• Concentration Risk: Medium")
        yield Static("• Operational Risk: Low")
        yield Static("")
        yield Static("Recommendations:")
        yield Static("• Reduce BTC correlation")
        yield Static("• Increase diversification")
        yield Static("• Monitor drawdown levels")


class ReportGenerationPanel(Widget):
    """Panel with report generation options"""
    
    def compose(self) -> ComposeResult:
        yield Static("Report Generation", classes="panel-title")
        yield Static("Available Reports:")
        yield Static("• [1] Daily Performance")
        yield Static("• [2] Weekly Summary")
        yield Static("• [3] Monthly Analysis")
        yield Static("• [4] Risk Assessment")
        yield Static("• [5] Strategy Comparison")
        yield Static("• [6] Custom Report")
        yield Static("")
        yield Static("Export Formats:")
        yield Static("• JSON Data")
        yield Static("• CSV Tables")
        yield Static("• Text Report")
        yield Static("• PDF (External)")


class AnalyticsView(Widget):
    """Advanced analytics and reporting interface"""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            PortfolioOverviewPanel(classes="panel"),
            PerformanceMetricsPanel(classes="panel"),
            StrategyComparisonPanel(classes="panel"),
            classes="analytics-top"
        )
        yield Horizontal(
            EquityCurvePanel(classes="panel chart"),
            RiskAnalysisPanel(classes="panel"),
            ReportGenerationPanel(classes="panel"),
            classes="analytics-bottom"
        )
    
    def set_mcp_client(self, mcp_client):
        """Set MCP client for data updates"""
        self.mcp_client = mcp_client
    
    async def refresh_data(self):
        """Refresh analytics data"""
        # TODO: Implement data refresh
        pass