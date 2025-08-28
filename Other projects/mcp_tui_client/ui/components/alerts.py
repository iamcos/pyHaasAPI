"""
Alert and Notification UI Components

UI components for alert configuration, management, history viewing,
and real-time notification display.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, Label, Button, Input, Select, DataTable, 
    TabbedContent, TabPane, Checkbox, RadioSet, RadioButton
)
from textual.reactive import reactive
from textual.timer import Timer
from textual import events

from ..components.panels import BasePanel
from ..components.forms import FormField, BaseForm
from ..components.tables import EnhancedDataTable
from ...services.alert_service import (
    AlertService, Alert, AlertEvent, AlertType, AlertPriority, 
    AlertStatus, NotificationMethod, AlertCondition
)
from ...utils.logging import get_logger


class AlertConfigurationPanel(BasePanel):
    """Alert configuration and creation panel"""
    
    DEFAULT_CSS = """
    AlertConfigurationPanel {
        height: auto;
        min-height: 25;
    }
    
    .alert-form {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }
    
    .form-section {
        height: auto;
        margin: 1 0;
        border: solid $primary;
        padding: 1;
    }
    
    .section-title {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
        text-style: bold;
    }
    
    .form-row {
        height: 3;
        margin: 0 0 1 0;
    }
    
    .form-label {
        dock: left;
        width: 20;
        height: 1;
        color: $text;
        content-align: middle left;
    }
    
    .form-input {
        height: 1;
        margin: 0 1;
    }
    
    .form-buttons {
        dock: bottom;
        height: 3;
        background: $surface;
        padding: 1;
    }
    """
    
    def __init__(
        self, 
        alert_service: AlertService,
        on_alert_created: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(title="Alert Configuration", **kwargs)
        self.logger = get_logger(__name__)
        self.alert_service = alert_service
        self.on_alert_created = on_alert_created
        
        # Form state
        self.editing_alert_id: Optional[str] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize alert configuration when mounted"""
        self._setup_configuration_form()
    
    def _setup_configuration_form(self) -> None:
        """Set up alert configuration form"""
        container = ScrollableContainer(classes="alert-form")
        
        # Basic Information Section
        basic_section = Vertical(classes="form-section")
        basic_title = Label("Basic Information", classes="section-title")
        basic_section.mount(basic_title)
        
        # Alert Name
        name_row = Horizontal(classes="form-row")
        name_label = Label("Alert Name:", classes="form-label")
        name_input = Input(placeholder="Enter alert name", id="alert-name", classes="form-input")
        name_row.mount(name_label)
        name_row.mount(name_input)
        basic_section.mount(name_row)
        
        # Alert Type
        type_row = Horizontal(classes="form-row")
        type_label = Label("Alert Type:", classes="form-label")
        type_select = Select(
            options=[
                ("Price Above", AlertType.PRICE_ABOVE.value),
                ("Price Below", AlertType.PRICE_BELOW.value),
                ("Price Change %", AlertType.PRICE_CHANGE.value),
                ("Volume Spike", AlertType.VOLUME_SPIKE.value),
                ("Performance Threshold", AlertType.PERFORMANCE_THRESHOLD.value),
                ("Drawdown Limit", AlertType.DRAWDOWN_LIMIT.value),
                ("Custom", AlertType.CUSTOM.value)
            ],
            id="alert-type",
            classes="form-input"
        )
        type_row.mount(type_label)
        type_row.mount(type_select)
        basic_section.mount(type_row)
        
        # Symbol (for market alerts)
        symbol_row = Horizontal(classes="form-row")
        symbol_label = Label("Symbol:", classes="form-label")
        symbol_input = Input(placeholder="e.g., BTCUSD (optional)", id="alert-symbol", classes="form-input")
        symbol_row.mount(symbol_label)
        symbol_row.mount(symbol_input)
        basic_section.mount(symbol_row)
        
        container.mount(basic_section)
        
        # Condition Section
        condition_section = Vertical(classes="form-section")
        condition_title = Label("Alert Condition", classes="section-title")
        condition_section.mount(condition_title)
        
        # Field
        field_row = Horizontal(classes="form-row")
        field_label = Label("Field:", classes="form-label")
        field_select = Select(
            options=[
                ("Price", "price"),
                ("Volume", "volume"),
                ("P&L", "pnl"),
                ("Drawdown", "drawdown"),
                ("Portfolio Value", "portfolio_value"),
                ("Return %", "return_percent")
            ],
            id="condition-field",
            classes="form-input"
        )
        field_row.mount(field_label)
        field_row.mount(field_select)
        condition_section.mount(field_row)
        
        # Operator
        operator_row = Horizontal(classes="form-row")
        operator_label = Label("Operator:", classes="form-label")
        operator_select = Select(
            options=[
                ("Greater Than", "gt"),
                ("Less Than", "lt"),
                ("Greater or Equal", "gte"),
                ("Less or Equal", "lte"),
                ("Change %", "change_pct")
            ],
            id="condition-operator",
            classes="form-input"
        )
        operator_row.mount(operator_label)
        operator_row.mount(operator_select)
        condition_section.mount(operator_row)
        
        # Value
        value_row = Horizontal(classes="form-row")
        value_label = Label("Threshold Value:", classes="form-label")
        value_input = Input(placeholder="Enter threshold value", id="condition-value", classes="form-input")
        value_row.mount(value_label)
        value_row.mount(value_input)
        condition_section.mount(value_row)
        
        container.mount(condition_section)
        
        # Settings Section
        settings_section = Vertical(classes="form-section")
        settings_title = Label("Alert Settings", classes="section-title")
        settings_section.mount(settings_title)
        
        # Priority
        priority_row = Horizontal(classes="form-row")
        priority_label = Label("Priority:", classes="form-label")
        priority_select = Select(
            options=[
                ("Low", AlertPriority.LOW.value),
                ("Medium", AlertPriority.MEDIUM.value),
                ("High", AlertPriority.HIGH.value),
                ("Critical", AlertPriority.CRITICAL.value)
            ],
            value=AlertPriority.MEDIUM.value,
            id="alert-priority",
            classes="form-input"
        )
        priority_row.mount(priority_label)
        priority_row.mount(priority_select)
        settings_section.mount(priority_row)
        
        # Notification Methods
        notification_row = Vertical(classes="form-row")
        notification_label = Label("Notifications:", classes="form-label")
        notification_row.mount(notification_label)
        
        notification_checkboxes = Horizontal()
        visual_checkbox = Checkbox("Visual", value=True, id="notify-visual")
        audio_checkbox = Checkbox("Audio", id="notify-audio")
        log_checkbox = Checkbox("Log", id="notify-log")
        notification_checkboxes.mount(visual_checkbox)
        notification_checkboxes.mount(audio_checkbox)
        notification_checkboxes.mount(log_checkbox)
        notification_row.mount(notification_checkboxes)
        settings_section.mount(notification_row)
        
        # Cooldown
        cooldown_row = Horizontal(classes="form-row")
        cooldown_label = Label("Cooldown (min):", classes="form-label")
        cooldown_input = Input(value="5", id="alert-cooldown", classes="form-input")
        cooldown_row.mount(cooldown_label)
        cooldown_row.mount(cooldown_input)
        settings_section.mount(cooldown_row)
        
        container.mount(settings_section)
        
        # Buttons
        buttons = Horizontal(classes="form-buttons")
        create_button = Button("Create Alert", variant="primary", id="create-alert")
        update_button = Button("Update Alert", variant="success", id="update-alert")
        cancel_button = Button("Cancel", variant="default", id="cancel-alert")
        clear_button = Button("Clear Form", variant="warning", id="clear-form")
        
        buttons.mount(create_button)
        buttons.mount(update_button)
        buttons.mount(cancel_button)
        buttons.mount(clear_button)
        container.mount(buttons)
        
        self.update_content(container)
        
        # Initially hide update button
        update_button.display = False
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "create-alert":
            await self._create_alert()
        elif event.button.id == "update-alert":
            await self._update_alert()
        elif event.button.id == "cancel-alert":
            self._cancel_edit()
        elif event.button.id == "clear-form":
            self._clear_form()
    
    async def _create_alert(self) -> None:
        """Create new alert from form data"""
        try:
            form_data = self._get_form_data()
            if not form_data:
                return
            
            # Create alert condition
            condition = AlertCondition(
                field=form_data['condition_field'],
                operator=form_data['condition_operator'],
                value=float(form_data['condition_value'])
            )
            
            # Create alert
            alert_id = self.alert_service.create_alert(
                name=form_data['name'],
                alert_type=AlertType(form_data['type']),
                condition=condition,
                symbol=form_data['symbol'] if form_data['symbol'] else None,
                priority=AlertPriority(form_data['priority']),
                notification_methods=form_data['notification_methods'],
                cooldown_minutes=int(form_data['cooldown'])
            )
            
            self.set_status("success", f"Alert '{form_data['name']}' created successfully")
            self._clear_form()
            
            # Notify callback
            if self.on_alert_created:
                self.on_alert_created(alert_id)
                
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            self.set_status("error", f"Failed to create alert: {str(e)}")
    
    async def _update_alert(self) -> None:
        """Update existing alert"""
        try:
            if not self.editing_alert_id:
                return
            
            form_data = self._get_form_data()
            if not form_data:
                return
            
            # Update alert condition
            condition = AlertCondition(
                field=form_data['condition_field'],
                operator=form_data['condition_operator'],
                value=float(form_data['condition_value'])
            )
            
            # Update alert
            success = self.alert_service.update_alert(
                self.editing_alert_id,
                name=form_data['name'],
                alert_type=AlertType(form_data['type']),
                condition=condition,
                symbol=form_data['symbol'] if form_data['symbol'] else None,
                priority=AlertPriority(form_data['priority']),
                notification_methods=form_data['notification_methods'],
                cooldown_minutes=int(form_data['cooldown'])
            )
            
            if success:
                self.set_status("success", f"Alert '{form_data['name']}' updated successfully")
                self._cancel_edit()
            else:
                self.set_status("error", "Failed to update alert")
                
        except Exception as e:
            self.logger.error(f"Error updating alert: {e}")
            self.set_status("error", f"Failed to update alert: {str(e)}")
    
    def _get_form_data(self) -> Optional[Dict[str, Any]]:
        """Get form data"""
        try:
            # Get form values
            name = self.query_one("#alert-name", Input).value.strip()
            alert_type = self.query_one("#alert-type", Select).value
            symbol = self.query_one("#alert-symbol", Input).value.strip()
            
            condition_field = self.query_one("#condition-field", Select).value
            condition_operator = self.query_one("#condition-operator", Select).value
            condition_value = self.query_one("#condition-value", Input).value.strip()
            
            priority = self.query_one("#alert-priority", Select).value
            cooldown = self.query_one("#alert-cooldown", Input).value.strip()
            
            # Get notification methods
            notification_methods = []
            if self.query_one("#notify-visual", Checkbox).value:
                notification_methods.append(NotificationMethod.VISUAL)
            if self.query_one("#notify-audio", Checkbox).value:
                notification_methods.append(NotificationMethod.AUDIO)
            if self.query_one("#notify-log", Checkbox).value:
                notification_methods.append(NotificationMethod.LOG)
            
            # Validate required fields
            if not name:
                self.set_status("error", "Alert name is required")
                return None
            
            if not condition_value:
                self.set_status("error", "Threshold value is required")
                return None
            
            try:
                float(condition_value)
            except ValueError:
                self.set_status("error", "Threshold value must be a number")
                return None
            
            try:
                int(cooldown)
            except ValueError:
                self.set_status("error", "Cooldown must be a number")
                return None
            
            if not notification_methods:
                notification_methods = [NotificationMethod.VISUAL]
            
            return {
                'name': name,
                'type': alert_type,
                'symbol': symbol,
                'condition_field': condition_field,
                'condition_operator': condition_operator,
                'condition_value': condition_value,
                'priority': priority,
                'notification_methods': notification_methods,
                'cooldown': cooldown
            }
            
        except Exception as e:
            self.logger.error(f"Error getting form data: {e}")
            self.set_status("error", "Error reading form data")
            return None
    
    def _clear_form(self) -> None:
        """Clear form fields"""
        try:
            self.query_one("#alert-name", Input).value = ""
            self.query_one("#alert-symbol", Input).value = ""
            self.query_one("#condition-value", Input).value = ""
            self.query_one("#alert-cooldown", Input).value = "5"
            
            # Reset checkboxes
            self.query_one("#notify-visual", Checkbox).value = True
            self.query_one("#notify-audio", Checkbox).value = False
            self.query_one("#notify-log", Checkbox).value = False
            
            # Reset selects to default
            self.query_one("#alert-type", Select).value = AlertType.PRICE_ABOVE.value
            self.query_one("#condition-field", Select).value = "price"
            self.query_one("#condition-operator", Select).value = "gt"
            self.query_one("#alert-priority", Select).value = AlertPriority.MEDIUM.value
            
        except Exception as e:
            self.logger.error(f"Error clearing form: {e}")
    
    def edit_alert(self, alert: Alert) -> None:
        """Load alert data for editing"""
        try:
            self.editing_alert_id = alert.id
            
            # Fill form with alert data
            self.query_one("#alert-name", Input).value = alert.name
            self.query_one("#alert-type", Select).value = alert.alert_type.value
            self.query_one("#alert-symbol", Input).value = alert.symbol or ""
            
            self.query_one("#condition-field", Select).value = alert.condition.field
            self.query_one("#condition-operator", Select).value = alert.condition.operator
            self.query_one("#condition-value", Input).value = str(alert.condition.value)
            
            self.query_one("#alert-priority", Select).value = alert.priority.value
            self.query_one("#alert-cooldown", Input).value = str(alert.cooldown_minutes)
            
            # Set notification methods
            self.query_one("#notify-visual", Checkbox).value = NotificationMethod.VISUAL in alert.notification_methods
            self.query_one("#notify-audio", Checkbox).value = NotificationMethod.AUDIO in alert.notification_methods
            self.query_one("#notify-log", Checkbox).value = NotificationMethod.LOG in alert.notification_methods
            
            # Show update button, hide create button
            self.query_one("#create-alert", Button).display = False
            self.query_one("#update-alert", Button).display = True
            
            self.set_status("info", f"Editing alert: {alert.name}")
            
        except Exception as e:
            self.logger.error(f"Error loading alert for editing: {e}")
    
    def _cancel_edit(self) -> None:
        """Cancel editing mode"""
        self.editing_alert_id = None
        self._clear_form()
        
        # Show create button, hide update button
        self.query_one("#create-alert", Button).display = True
        self.query_one("#update-alert", Button).display = False
        
        self.set_status("info", "Edit cancelled")


class AlertManagementPanel(BasePanel):
    """Alert management and monitoring panel"""
    
    DEFAULT_CSS = """
    AlertManagementPanel {
        height: auto;
        min-height: 20;
    }
    
    .alerts-table {
        height: 1fr;
        border: solid $accent;
    }
    
    .alert-controls {
        dock: bottom;
        height: 3;
        background: $surface;
        padding: 1;
    }
    """
    
    def __init__(
        self, 
        alert_service: AlertService,
        on_edit_alert: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(title="Alert Management", **kwargs)
        self.logger = get_logger(__name__)
        self.alert_service = alert_service
        self.on_edit_alert = on_edit_alert
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize alert management when mounted"""
        self._setup_management_interface()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_management_interface(self) -> None:
        """Set up alert management interface"""
        container = Vertical()
        
        # Alerts table
        self.alerts_table = EnhancedDataTable(
            title="Active Alerts",
            show_header=True,
            show_row_labels=False,
            classes="alerts-table"
        )
        
        self.alerts_table.add_column("Name", width=20)
        self.alerts_table.add_column("Type", width=15)
        self.alerts_table.add_column("Symbol", width=10)
        self.alerts_table.add_column("Condition", width=25)
        self.alerts_table.add_column("Priority", width=10)
        self.alerts_table.add_column("Status", width=12)
        self.alerts_table.add_column("Triggers", width=8)
        self.alerts_table.add_column("Created", width=12)
        
        container.mount(self.alerts_table)
        
        # Controls
        controls = Horizontal(classes="alert-controls")
        
        edit_button = Button("Edit", variant="primary", id="edit-alert")
        delete_button = Button("Delete", variant="error", id="delete-alert")
        acknowledge_button = Button("Acknowledge", variant="success", id="acknowledge-alert")
        refresh_button = Button("Refresh", variant="default", id="refresh-alerts")
        
        controls.mount(edit_button)
        controls.mount(delete_button)
        controls.mount(acknowledge_button)
        controls.mount(refresh_button)
        
        container.mount(controls)
        self.update_content(container)
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        self.update_timer = self.set_interval(5.0, self._update_alerts_display)
        self._update_alerts_display()  # Initial update
    
    def _update_alerts_display(self) -> None:
        """Update alerts display"""
        try:
            # Clear existing rows
            self.alerts_table.clear()
            
            # Get all alerts
            alerts = self.alert_service.list_alerts()
            
            for alert in alerts:
                # Format condition
                condition_text = f"{alert.condition.field} {alert.condition.operator} {alert.condition.value}"
                
                # Format status with color indicators
                status_text = alert.status.value.upper()
                if alert.status == AlertStatus.ACTIVE:
                    status_text = "🟢 " + status_text
                elif alert.status == AlertStatus.TRIGGERED:
                    status_text = "🔴 " + status_text
                elif alert.status == AlertStatus.ACKNOWLEDGED:
                    status_text = "🟡 " + status_text
                elif alert.status == AlertStatus.DISABLED:
                    status_text = "⚫ " + status_text
                
                self.alerts_table.add_row(
                    alert.name,
                    alert.alert_type.value.replace('_', ' ').title(),
                    alert.symbol or "N/A",
                    condition_text,
                    alert.priority.value.upper(),
                    status_text,
                    str(alert.trigger_count),
                    alert.created_at.strftime("%Y-%m-%d")
                )
                
        except Exception as e:
            self.logger.error(f"Error updating alerts display: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "edit-alert":
            await self._edit_selected_alert()
        elif event.button.id == "delete-alert":
            await self._delete_selected_alert()
        elif event.button.id == "acknowledge-alert":
            await self._acknowledge_selected_alert()
        elif event.button.id == "refresh-alerts":
            self._update_alerts_display()
    
    async def _edit_selected_alert(self) -> None:
        """Edit selected alert"""
        try:
            # Get selected row
            if not self.alerts_table.cursor_row:
                self.set_status("warning", "Please select an alert to edit")
                return
            
            row_index = self.alerts_table.cursor_row
            alerts = self.alert_service.list_alerts()
            
            if row_index < len(alerts):
                alert = alerts[row_index]
                
                if self.on_edit_alert:
                    self.on_edit_alert(alert)
                else:
                    self.set_status("info", f"Edit alert: {alert.name}")
                    
        except Exception as e:
            self.logger.error(f"Error editing alert: {e}")
            self.set_status("error", "Failed to edit alert")
    
    async def _delete_selected_alert(self) -> None:
        """Delete selected alert"""
        try:
            # Get selected row
            if not self.alerts_table.cursor_row:
                self.set_status("warning", "Please select an alert to delete")
                return
            
            row_index = self.alerts_table.cursor_row
            alerts = self.alert_service.list_alerts()
            
            if row_index < len(alerts):
                alert = alerts[row_index]
                
                # Delete alert
                success = self.alert_service.delete_alert(alert.id)
                
                if success:
                    self.set_status("success", f"Alert '{alert.name}' deleted")
                    self._update_alerts_display()
                else:
                    self.set_status("error", "Failed to delete alert")
                    
        except Exception as e:
            self.logger.error(f"Error deleting alert: {e}")
            self.set_status("error", "Failed to delete alert")
    
    async def _acknowledge_selected_alert(self) -> None:
        """Acknowledge selected alert"""
        try:
            # Get selected row
            if not self.alerts_table.cursor_row:
                self.set_status("warning", "Please select an alert to acknowledge")
                return
            
            row_index = self.alerts_table.cursor_row
            alerts = self.alert_service.list_alerts()
            
            if row_index < len(alerts):
                alert = alerts[row_index]
                
                # Acknowledge alert
                success = self.alert_service.acknowledge_alert(alert.id)
                
                if success:
                    self.set_status("success", f"Alert '{alert.name}' acknowledged")
                    self._update_alerts_display()
                else:
                    self.set_status("error", "Failed to acknowledge alert")
                    
        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {e}")
            self.set_status("error", "Failed to acknowledge alert")


class AlertHistoryPanel(BasePanel):
    """Alert history display panel"""
    
    DEFAULT_CSS = """
    AlertHistoryPanel {
        height: auto;
        min-height: 15;
    }
    
    .history-table {
        height: 1fr;
        border: solid $accent;
    }
    """
    
    def __init__(
        self, 
        alert_service: AlertService,
        **kwargs
    ):
        super().__init__(title="Alert History", **kwargs)
        self.logger = get_logger(__name__)
        self.alert_service = alert_service
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize alert history when mounted"""
        self._setup_history_interface()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_history_interface(self) -> None:
        """Set up alert history interface"""
        self.history_table = EnhancedDataTable(
            title="Recent Alert Events",
            show_header=True,
            show_row_labels=False,
            classes="history-table"
        )
        
        self.history_table.add_column("Time", width=12)
        self.history_table.add_column("Alert", width=20)
        self.history_table.add_column("Priority", width=10)
        self.history_table.add_column("Symbol", width=10)
        self.history_table.add_column("Message", width=40)
        self.history_table.add_column("Value", width=12)
        self.history_table.add_column("Status", width=12)
        
        self.update_content(self.history_table)
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        self.update_timer = self.set_interval(10.0, self._update_history_display)
        self._update_history_display()  # Initial update
    
    def _update_history_display(self) -> None:
        """Update history display"""
        try:
            # Clear existing rows
            self.history_table.clear()
            
            # Get recent alert events
            events = self.alert_service.get_alert_history(50)  # Last 50 events
            
            for event in events:
                # Format priority with color indicators
                priority_text = event.priority.value.upper()
                if event.priority == AlertPriority.CRITICAL:
                    priority_text = "🚨 " + priority_text
                elif event.priority == AlertPriority.HIGH:
                    priority_text = "🔴 " + priority_text
                elif event.priority == AlertPriority.MEDIUM:
                    priority_text = "🟡 " + priority_text
                else:
                    priority_text = "🔵 " + priority_text
                
                # Format status
                status_text = "✅ ACK" if event.acknowledged_at else "⏳ PENDING"
                
                self.history_table.add_row(
                    event.triggered_at.strftime("%H:%M:%S"),
                    event.alert_name,
                    priority_text,
                    event.symbol or "N/A",
                    event.message[:40] + "..." if len(event.message) > 40 else event.message,
                    f"{event.current_value:.4f}",
                    status_text
                )
                
        except Exception as e:
            self.logger.error(f"Error updating history display: {e}")


class AlertDashboard(BasePanel):
    """Comprehensive alert dashboard"""
    
    def __init__(
        self, 
        alert_service: AlertService,
        **kwargs
    ):
        super().__init__(title="Alert Dashboard", **kwargs)
        self.logger = get_logger(__name__)
        self.alert_service = alert_service
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize alert dashboard when mounted"""
        self._setup_dashboard()
    
    def _setup_dashboard(self) -> None:
        """Set up alert dashboard with tabs"""
        dashboard = TabbedContent()
        
        # Configuration Tab
        with dashboard.add_pane("config", "Configuration"):
            config_panel = AlertConfigurationPanel(
                self.alert_service,
                on_alert_created=self._on_alert_created
            )
            yield config_panel
        
        # Management Tab
        with dashboard.add_pane("manage", "Management"):
            management_panel = AlertManagementPanel(
                self.alert_service,
                on_edit_alert=self._on_edit_alert
            )
            yield management_panel
        
        # History Tab
        with dashboard.add_pane("history", "History"):
            history_panel = AlertHistoryPanel(self.alert_service)
            yield history_panel
        
        self.update_content(dashboard)
    
    def _on_alert_created(self, alert_id: str) -> None:
        """Handle alert creation"""
        # Switch to management tab to show the new alert
        try:
            dashboard = self.query_one(TabbedContent)
            dashboard.active = "manage"
        except Exception as e:
            self.logger.error(f"Error switching to management tab: {e}")
    
    def _on_edit_alert(self, alert: Alert) -> None:
        """Handle alert editing"""
        # Switch to configuration tab and load alert for editing
        try:
            dashboard = self.query_one(TabbedContent)
            dashboard.active = "config"
            
            # Find configuration panel and load alert
            config_panel = self.query_one(AlertConfigurationPanel)
            config_panel.edit_alert(alert)
            
        except Exception as e:
            self.logger.error(f"Error switching to configuration tab: {e}")