from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Button, Static, Input, DataTable, Label, Log, Select
)
from textual.containers import Horizontal, Vertical, Container, Grid, ScrollView
from textual.reactive import reactive
from textual import events
import json
from rapidfuzz import process, fuzz

# Placeholder data
DEFAULT_PARAMETERS = {
    "Stop Loss": 2,
    "Take Profit": 0.8,
}
DEFAULT_MARKETS = [
    "BINANCE_BTC_USDT",
    "BINANCE_ETH_USDT",
    "BINANCE_SOL_BNB",
    "BINANCE_ETH_BTC",
    "BINANCE_BNB_USDT",
    "BINANCE_SOL_USDT",
    "BINANCE_ETH_SOL",
    "COINBASE_BTC_USDT",
    "COINBASE_ETH_USDT",
    "KRAKEN_BTC_USDT",
    "KRAKEN_ETH_USDT",
]
DEFAULT_PERIOD = {
    "start": "2024-01-01",
    "end": "2024-06-01"
}
DEFAULT_EXCHANGES = ["ALL", "BINANCE", "COINBASE", "KRAKEN"]
PARAMETER_PRESETS = ["Default", "Aggressive", "Conservative"]
PERIOD_PRESETS = ["YTD", "Last 3 Months", "Last Month"]

TIPS = (
    "[Tips]",
    "- Press 'm' to focus the market search box.",
    "- Type to filter markets (fuzzy search).",
    "- Use up/down arrows to move in the market list.",
    "- Press space or enter to select/deselect a market.",
    "- Press tab/shift+tab to move between sections.",
    "- Press 'q' to quit the app.",
)

# Helper to parse and display market info
MARKET_COLUMNS = ["Exchange", "Symbol", "Market"]
def parse_market(market_str):
    parts = market_str.split("_")
    if len(parts) == 3:
        return {"exchange": parts[0], "symbol": f"{parts[1]}/{parts[2]}", "market": market_str}
    return {"exchange": market_str, "symbol": "", "market": market_str}

def market_display_row(market_str):
    exch, base, quote = parse_market(market_str)["exchange"], parse_market(market_str)["symbol"].split("/")[0], parse_market(market_str)["symbol"].split("/")[1]
    return exch, f"{base}/{quote}", market_str

class BacktesterApp(App):
    CSS_PATH = None
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "focus_market_selector", "Focus Market Selector"),
    ]

    parameters = reactive(DEFAULT_PARAMETERS.copy())
    markets = reactive(DEFAULT_MARKETS.copy())
    selected_markets = reactive(set(DEFAULT_MARKETS))
    period = reactive(DEFAULT_PERIOD.copy())
    results = reactive([])
    market_search = reactive("")
    filtered_markets = reactive(DEFAULT_MARKETS.copy())
    exchange_filter = reactive("ALL")
    parameter_preset = reactive("Default")
    period_preset = reactive("YTD")

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollView():
            with Vertical():
                with Horizontal():
                    yield Static("[Parameters]", id="params_label")
                    yield Select([(p, p) for p in PARAMETER_PRESETS], prompt="Preset", id="param_preset")
                    yield Button("Load", id="load_params")
                    yield Button("Save", id="save_params")
                    yield Button("Edit", id="edit_params")
                yield DataTable(id="params_table")
                with Horizontal():
                    yield Static("[Markets]", id="markets_label")
                    yield Input(placeholder="Search markets...", id="market_search")
                    yield Select([(e, e) for e in DEFAULT_EXCHANGES], prompt="Exchange", id="exchange_filter")
                    yield Button("Load", id="load_markets")
                    yield Button("Save", id="save_markets")
                yield DataTable(id="markets_table", max_height=10)
                with Horizontal():
                    yield Static("[Backtest Period]", id="period_label")
                    yield Select([(p, p) for p in PERIOD_PRESETS], prompt="Preset", id="period_preset")
                    yield Button("Load", id="load_period")
                    yield Button("Save", id="save_period")
                    yield Button("Edit", id="edit_period")
                yield DataTable(id="period_table")
                yield Button("Run Backtests", id="run_backtests")
                yield Log(id="results_log", highlight=True, min_height=5)
                yield Static("\n".join(TIPS), id="tips_box")
        yield Footer()

    def on_mount(self):
        self.refresh_tables()
        input_widget = self.query_one("#market_search", Input)
        input_widget.visible = True
        input_widget.focus()

    def refresh_tables(self):
        log = self.query_one("#results_log", Log)
        params_table = self.query_one("#params_table", DataTable)
        # Remove all columns and rows before adding
        params_table.clear(columns=True)
        params_table.add_columns("Parameter", "Value")
        for k, v in self.parameters.items():
            params_table.add_row(k, str(v))

        # --- Market Table Logic ---
        all_market_dicts = [parse_market(m) for m in self.markets]
        exch_filter = self.exchange_filter
        if exch_filter != "ALL":
            all_market_dicts = [d for d in all_market_dicts if d["exchange"] == exch_filter]
        search = self.market_search.lower().strip()
        filtered_dicts = all_market_dicts
        if search:
            def join_row(d):
                if not isinstance(d, dict):
                    return ""
                return f"{d.get('exchange', '')} {d.get('symbol', '')} {d.get('market', '')}".lower()
            try:
                matches = process.extract(
                    search,
                    all_market_dicts,
                    processor=join_row,
                    scorer=fuzz.token_set_ratio,
                    limit=30
                )
                filtered_dicts = [d for d, score, _ in matches if isinstance(d, dict) and score > 10]
            except Exception:
                filtered_dicts = []
        self.filtered_markets = [d["market"] for d in filtered_dicts]

        markets_table = self.query_one("#markets_table", DataTable)
        # Remove all columns and rows before adding
        markets_table.clear(columns=True)
        markets_table.add_columns(" ", *MARKET_COLUMNS, "Selected")
        if filtered_dicts:
            for i, d in enumerate(filtered_dicts):
                selected = "[x]" if d["market"] in self.selected_markets else "[ ]"
                indicator = ""  # Will be set below for the highlighted row
                log.write(f"Adding row: {indicator}, {d['exchange']}, {d['symbol']}, {d['market']}, {selected}")
                markets_table.add_row(indicator, d["exchange"], d["symbol"], d["market"], selected)
        else:
            log.write("Adding row: '', 'No results', '', '', ''")
            markets_table.add_row("", "No results", "", "", "")
        # Set highlight to previous row if possible
        if filtered_dicts:
            prev_row = 0
            if markets_table.cursor_coordinate:
                prev_row = markets_table.cursor_coordinate[0]
            row_idx = min(prev_row, len(filtered_dicts) - 1)
            markets_table.cursor_coordinate = (row_idx, 0)
            markets_table.update_cell_at((row_idx, 0), ">")
        # else: do not set cursor_coordinate at all

        period_table = self.query_one("#period_table", DataTable)
        period_table.clear(columns=True)
        period_table.add_columns("Field", "Value")
        for k, v in self.period.items():
            period_table.add_row(k, str(v))

        # Debug output to Log widget
        log.write(f"[b]Initial markets:[/b] {len(self.markets)}")
        log.write(f"[b]All market dicts:[/b] {len(all_market_dicts)}")
        log.write(f"[b]Filtered dicts:[/b] {len(filtered_dicts)}")
        log.write(f"[b]Search:[/b] '{self.market_search}' | [b]Exchange:[/b] {self.exchange_filter}")
        log.write(f"[b]Filtered Markets:[/b] {self.filtered_markets}")

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "market_search":
            self.market_search = event.value
            self.refresh_tables()

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "exchange_filter":
            self.exchange_filter = event.value
            self.refresh_tables()
        elif event.select.id == "param_preset":
            self.parameter_preset = event.value
            # Stub: apply preset logic here
            self.refresh_tables()
        elif event.select.id == "period_preset":
            self.period_preset = event.value
            # Stub: apply period preset logic here
            self.refresh_tables()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.data_table.id == "markets_table" and self.filtered_markets:
            markets_table = event.data_table
            # Remove all indicators
            for i in range(len(self.filtered_markets)):
                markets_table.update_cell_at((i, 0), "")
            # Set indicator for highlighted row
            if markets_table.cursor_coordinate:
                row_idx = markets_table.cursor_coordinate[0]
                if 0 <= row_idx < len(self.filtered_markets):
                    markets_table.update_cell_at((row_idx, 0), ">")

    def on_key(self, event: events.Key):
        market_search = self.query_one("#market_search", Input)
        markets_table = self.query_one("#markets_table", DataTable)
        if (market_search.has_focus or markets_table.has_focus) and self.filtered_markets:
            if event.key in ("enter", "space"):
                if self.filtered_markets and markets_table.cursor_coordinate:
                    row_idx = markets_table.cursor_coordinate[0]
                    if 0 <= row_idx < len(self.filtered_markets):
                        m = self.filtered_markets[row_idx]
                        if m in self.selected_markets:
                            self.selected_markets.remove(m)
                        else:
                            self.selected_markets.add(m)
                        self.refresh_tables()
            # elif event.key == "tab":
            #     self.focus_next()
            # elif event.key == "shift+tab":
            #     self.focus_previous()
            elif event.key in ("left", "right"):
                # Prevent left/right movement in market list
                if markets_table.has_focus and markets_table.cursor_coordinate:
                    row, _ = markets_table.cursor_coordinate
                    markets_table.cursor_coordinate = (row, 0)

    def action_focus_market_selector(self):
        self.query_one("#market_search", Input).focus()
        self.refresh_tables()

    def on_button_pressed(self, event):
        btn_id = event.button.id
        log = self.query_one("#results_log", Log)
        if btn_id == "run_backtests":
            log.write("[b green]Running backtests... (placeholder)[/b green]")
            for m in self.selected_markets:
                log.write(f"Backtesting {m} with params {self.parameters} and period {self.period}")
            log.write("[b green]Done! (placeholder)[/b green]")
        elif btn_id == "edit_params":
            log.write("[yellow]Edit parameters not implemented yet.[/yellow]")
        elif btn_id == "edit_period":
            log.write("[yellow]Edit period not implemented yet.[/yellow]")
        elif btn_id == "load_params":
            log.write("[yellow]Load parameters not implemented yet.[/yellow]")
        elif btn_id == "save_params":
            log.write("[yellow]Save parameters not implemented yet.[/yellow]")
        elif btn_id == "load_markets":
            log.write("[yellow]Load markets not implemented yet.[/yellow]")
        elif btn_id == "save_markets":
            log.write("[yellow]Save markets not implemented yet.[/yellow]")
        elif btn_id == "load_period":
            log.write("[yellow]Load period not implemented yet.[/yellow]")
        elif btn_id == "save_period":
            log.write("[yellow]Save period not implemented yet.[/yellow]")
        self.refresh_tables()

if __name__ == "__main__":
    app = BacktesterApp()
    app.run() 