from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container, Grid
from textual.widgets import Label, Button, DataTable, Static, ProgressBar, Sparkline
from textual.screen import Screen
from typing import List, Any
import numpy as np

from pyHaasAPI.analysis.metrics import RunMetrics

class LabVisualizationScreen(Vertical):
    def __init__(self, tui_app, server_name: str, lab_id: str, lab_name: str, metrics_list: List[RunMetrics]):
        super().__init__()
        self.tui_app = tui_app
        self.server_name = server_name
        self.lab_id = lab_id
        self.lab_name = lab_name
        self.metrics_list = metrics_list

    def compose(self) -> ComposeResult:
        yield Label(f"Lab Visualizations: [bold cyan]{self.lab_name}[/]", id="screen-title")
        
        with Container(id="viz-container"):
            with Vertical(classes="viz-card"):
                yield Label("📈 [bold]Aggregate Equity Curve (Top 10 Index)[/]", classes="card-header")
                self.equity_sparkline = Sparkline([], summary_function=max)
                yield self.equity_sparkline
            
            with Grid(id="viz-grid"):
                with Vertical(classes="viz-card"):
                    yield Label("📊 [bold]ROI Distribution[/]", classes="card-header")
                    self.roi_dist_static = Static("", classes="ascii-chart")
                    yield self.roi_dist_static
                
                with Vertical(classes="viz-card"):
                    yield Label("🎯 [bold]Win Rate vs ROI Scatter[/]", classes="card-header")
                    self.scatter_static = Static("", classes="ascii-chart")
                    yield self.scatter_static
                    
        with Horizontal(classes="button-bar"):
            yield Button("Back to Details", variant="error", id="back-btn")
            yield Button("Refresh Data", variant="primary", id="refresh-viz-btn")

    def on_mount(self) -> None:
        self.refresh_visuals()

    def refresh_visuals(self) -> None:
        if not self.metrics_list:
            self.roi_dist_static.update("[dim]No metrics available for visualization.[/]")
            return

        # 1. Equity Curve (Combined)
        combined_equity = self._compute_combined_equity()
        if combined_equity:
             self.equity_sparkline.data = combined_equity
        
        # 2. ROI Distribution
        self.roi_dist_static.update(self._render_roi_distribution())
        
        # 3. Scatter Plot (WR vs ROI)
        self.scatter_static.update(self._render_wr_roi_scatter())

    def _compute_combined_equity(self) -> List[float]:
        """Combine equity curves of top 10 performers."""
        top_10 = self.metrics_list[:10]
        if not top_10:
            return []
            
        # Simplistic combination: sum the curves (padded with last value)
        max_len = max(len(m.equity_curve or []) for m in top_10)
        if max_len == 0:
            return []
            
        combined = [0.0] * max_len
        for m in top_10:
            curve = m.equity_curve or [0.0]
            for i in range(max_len):
                val = curve[i] if i < len(curve) else curve[-1]
                combined[i] += val
        
        return combined

    def _render_roi_distribution(self) -> str:
        """Render a stunning ASCII histogram for ROI distribution with rich colors."""
        from rich.text import Text
        
        rois = [m.roi_pct for m in self.metrics_list]
        if not rois:
            return ""
        
        # Create bins
        min_roi, max_roi = min(rois), max(rois)
        if min_roi == max_roi:
            return f"[cyan]All backtests have ROI: {min_roi:.1f}%[/]"
        
        num_bins = min(15, len(rois))
        bins = []
        bin_width = (max_roi - min_roi) / num_bins
        
        for i in range(num_bins):
            bin_start = min_roi + i * bin_width
            bin_end = bin_start + bin_width
            count = sum(1 for roi in rois if bin_start <= roi < bin_end or (i == num_bins - 1 and roi == max_roi))
            bins.append((bin_start, bin_end, count))
        
        max_count = max(b[2] for b in bins) if bins else 1
        width = 50
        
        # Unicode block characters for smooth bars
        blocks = ['', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        lines = []
        lines.append("[bold cyan]ROI Distribution[/]")
        lines.append("─" * 60)
        
        for bin_start, bin_end, count in bins:
            # Calculate bar length
            bar_len = int((count / max_count) * width)
            full_blocks = bar_len // 1
            
            # Color based on ROI range
            if bin_end < 0:
                color = "red"
            elif bin_start > 10:
                color = "bright_green"
            elif bin_start > 0:
                color = "green"
            else:
                color = "yellow"
            
            bar = f"[{color}]{'█' * full_blocks}[/]"
            label = f"{bin_start:>6.1f}% - {bin_end:<6.1f}%"
            
            lines.append(f"{label} │ {bar} [{count}]")
        
        # Add statistics
        avg_roi = sum(rois) / len(rois)
        median_roi = sorted(rois)[len(rois) // 2]
        lines.append("─" * 60)
        lines.append(f"[cyan]Mean:[/] {avg_roi:.1f}%  [cyan]Median:[/] {median_roi:.1f}%  [cyan]Range:[/] {min_roi:.1f}% to {max_roi:.1f}%")
        
        return "\n".join(lines)

    def _render_wr_roi_scatter(self) -> str:
        """Render a color-coded scatter plot for Win Rate vs ROI."""
        from rich.text import Text
        
        data = [(m.win_rate_pct, m.roi_pct) for m in self.metrics_list]
        if not data:
            return ""
        
        wrs = [d[0] for d in data]
        rois = [d[1] for d in data]
        
        min_wr, max_wr = min(wrs), max(wrs)
        min_roi, max_roi = min(rois), max(rois)
        
        rows, cols = 20, 60
        
        # Create grid with background
        grid = [[' ' for _ in range(cols)] for _ in range(rows)]
        
        # Add quadrant lines
        mid_row = rows // 2
        mid_col = cols // 2
        
        # Plot points with color coding
        point_chars = []
        for wr, roi in data:
            if max_wr > min_wr:
                c = int(((wr - min_wr) / (max_wr - min_wr)) * (cols - 1))
            else:
                c = mid_col
            
            if max_roi > min_roi:
                r = int(((roi - min_roi) / (max_roi - min_roi)) * (rows - 1))
            else:
                r = mid_row
            
            # Flip rows for y-axis
            r = (rows - 1) - r
            
            # Determine color based on quadrant
            if wr >= 50 and roi >= 0:
                char = '[bright_green]●[/]'  # High WR, Positive ROI
            elif wr >= 50 and roi < 0:
                char = '[yellow]●[/]'  # High WR, Negative ROI
            elif wr < 50 and roi >= 0:
                char = '[cyan]●[/]'  # Low WR, Positive ROI
            else:
                char = '[red]●[/]'  # Low WR, Negative ROI
            
            point_chars.append((r, c, char))
        
        # Build output
        lines = []
        lines.append("[bold cyan]Win Rate vs ROI Scatter[/]")
        lines.append("─" * 65)
        
        # Y-axis label
        lines.append(f"[dim]ROI ({min_roi:.0f}% to {max_roi:.0f}%)[/]")
        
        for r in range(rows):
            row_chars = [' '] * cols
            
            # Add quadrant lines
            if r == mid_row:
                for c in range(cols):
                    if c == mid_col:
                        row_chars[c] = '[dim]┼[/]'
                    else:
                        row_chars[c] = '[dim]─[/]'
            elif r != mid_row:
                row_chars[mid_col] = '[dim]│[/]'
            
            # Add points
            for pr, pc, pchar in point_chars:
                if pr == r and 0 <= pc < cols:
                    row_chars[pc] = pchar
            
            lines.append(''.join(str(c) for c in row_chars))
        
        # X-axis
        lines.append("─" * cols)
        lines.append(f"[dim]Win Rate ({min_wr:.0f}% to {max_wr:.0f}%)[/]")
        
        # Legend
        lines.append("")
        lines.append("[bright_green]●[/] High WR + Positive ROI  [yellow]●[/] High WR + Negative ROI")
        lines.append("[cyan]●[/] Low WR + Positive ROI   [red]●[/] Low WR + Negative ROI")
        
        return "\n".join(lines)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            from .lab_detail_screen import LabDetailScreen
            content = self.tui_app.query_one("#main-content")
            for child in content.children:
                child.remove()
            content.mount(LabDetailScreen(self.tui_app, self.server_name, self.lab_id, self.lab_name))
        elif event.button.id == "refresh-viz-btn":
            self.refresh_visuals()
