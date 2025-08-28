"""
Form Components

Form components for user input and configuration.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from enum import Enum

from textual.widget import Widget
from textual.widgets import (
    Input, Button, Label, Select, Checkbox, RadioButton, RadioSet,
    TextArea, Switch
)
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.validation import ValidationResult, Validator


class FieldType(Enum):
    """Form field types"""
    TEXT = "text"
    PASSWORD = "password"
    EMAIL = "email"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SWITCH = "switch"
    SLIDER = "slider"
    DATE = "date"
    TIME = "time"


class FormField:
    """Form field definition"""
    
    def __init__(
        self,
        name: str,
        field_type: FieldType,
        label: str,
        default_value: Any = None,
        required: bool = False,
        validator: Validator = None,
        options: List[Any] = None,
        placeholder: str = "",
        help_text: str = "",
        **kwargs
    ):
        self.name = name
        self.field_type = field_type
        self.label = label
        self.default_value = default_value
        self.required = required
        self.validator = validator
        self.options = options or []
        self.placeholder = placeholder
        self.help_text = help_text
        self.kwargs = kwargs


class BaseForm(Container):
    """Base form component with validation and data binding"""
    
    DEFAULT_CSS = """
    BaseForm {
        height: auto;
        padding: 1;
        border: solid $primary;
    }
    
    BaseForm .form-title {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        text-align: center;
        content-align: center middle;
    }
    
    BaseForm .form-content {
        padding: 1;
    }
    
    BaseForm .form-field {
        height: auto;
        margin: 1 0;
    }
    
    BaseForm .field-label {
        height: 1;
        margin: 0 0 1 0;
        text-style: bold;
    }
    
    BaseForm .field-input {
        height: auto;
        margin: 0 0 1 0;
    }
    
    BaseForm .field-help {
        height: 1;
        margin: 0 0 1 0;
        color: $text-muted;
        text-style: italic;
    }
    
    BaseForm .field-error {
        height: 1;
        margin: 0 0 1 0;
        color: $error;
        text-style: bold;
    }
    
    BaseForm .form-actions {
        dock: bottom;
        height: 3;
        background: $surface;
        layout: horizontal;
        align: center middle;
    }
    
    BaseForm Button {
        margin: 0 1;
        min-width: 12;
    }
    """
    
    def __init__(
        self,
        title: str = "Form",
        fields: List[FormField] = None,
        submit_callback: Callable = None,
        cancel_callback: Callable = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.fields = fields or []
        self.submit_callback = submit_callback
        self.cancel_callback = cancel_callback
        self.field_widgets: Dict[str, Widget] = {}
        self.field_errors: Dict[str, str] = {}
        self.form_data: Dict[str, Any] = {}
    
    def compose(self) -> ComposeResult:
        """Compose form layout"""
        yield Label(self.title, classes="form-title")
        yield Container(classes="form-content", id="form-content")
        yield Container(classes="form-actions", id="form-actions")
    
    async def on_mount(self) -> None:
        """Initialize form on mount"""
        await self._build_form()
        await self._setup_actions()
    
    async def _build_form(self) -> None:
        """Build form fields"""
        content_container = self.query_one("#form-content")
        
        for field in self.fields:
            field_container = Container(classes="form-field")
            
            # Field label
            label_text = field.label
            if field.required:
                label_text += " *"
            field_label = Label(label_text, classes="field-label")
            field_container.mount(field_label)
            
            # Field input
            field_widget = self._create_field_widget(field)
            self.field_widgets[field.name] = field_widget
            field_container.mount(field_widget)
            
            # Help text
            if field.help_text:
                help_label = Label(field.help_text, classes="field-help")
                field_container.mount(help_label)
            
            # Error placeholder
            error_label = Label("", classes="field-error", id=f"error-{field.name}")
            field_container.mount(error_label)
            
            content_container.mount(field_container)
    
    def _create_field_widget(self, field: FormField) -> Widget:
        """Create widget for form field"""
        widget_kwargs = field.kwargs.copy()
        
        if field.field_type == FieldType.TEXT:
            widget = Input(
                value=str(field.default_value or ""),
                placeholder=field.placeholder,
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.PASSWORD:
            widget = Input(
                value=str(field.default_value or ""),
                placeholder=field.placeholder,
                password=True,
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.EMAIL:
            widget = Input(
                value=str(field.default_value or ""),
                placeholder=field.placeholder,
                type="email",
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.NUMBER:
            widget = Input(
                value=str(field.default_value or ""),
                placeholder=field.placeholder,
                type="number",
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.TEXTAREA:
            widget = TextArea(
                text=str(field.default_value or ""),
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.SELECT:
            options = [(str(opt), opt) for opt in field.options]
            widget = Select(
                options=options,
                value=field.default_value,
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.CHECKBOX:
            widget = Checkbox(
                label=field.label,
                value=bool(field.default_value),
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.RADIO:
            widget = RadioSet(
                *[RadioButton(str(opt), value=opt) for opt in field.options],
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.SWITCH:
            widget = Switch(
                value=bool(field.default_value),
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        elif field.field_type == FieldType.SLIDER:
            # Slider not available in current Textual version, use Input instead
            widget = Input(
                value=str(field.default_value or 0),
                placeholder="Enter value...",
                type="number",
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        else:
            # Default to text input
            widget = Input(
                value=str(field.default_value or ""),
                placeholder=field.placeholder,
                id=f"field-{field.name}",
                **widget_kwargs
            )
        
        widget.add_class("field-input")
        return widget
    
    async def _setup_actions(self) -> None:
        """Set up form action buttons"""
        actions_container = self.query_one("#form-actions")
        
        # Submit button
        submit_button = Button(
            "Submit",
            variant="primary",
            id="submit-button"
        )
        actions_container.mount(submit_button)
        
        # Cancel button
        cancel_button = Button(
            "Cancel",
            variant="default",
            id="cancel-button"
        )
        actions_container.mount(cancel_button)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "submit-button":
            await self.submit_form()
        elif event.button.id == "cancel-button":
            await self.cancel_form()
    
    async def submit_form(self) -> None:
        """Submit form with validation"""
        # Collect form data
        self.form_data = {}
        self.field_errors = {}
        
        for field in self.fields:
            widget = self.field_widgets.get(field.name)
            if widget:
                value = self._get_widget_value(widget, field)
                self.form_data[field.name] = value
                
                # Validate field
                error = self._validate_field(field, value)
                if error:
                    self.field_errors[field.name] = error
        
        # Display errors
        await self._display_errors()
        
        # Submit if no errors
        if not self.field_errors:
            if self.submit_callback:
                await self.submit_callback(self.form_data)
    
    async def cancel_form(self) -> None:
        """Cancel form"""
        if self.cancel_callback:
            await self.cancel_callback()
    
    def _get_widget_value(self, widget: Widget, field: FormField) -> Any:
        """Get value from widget"""
        if isinstance(widget, Input):
            return widget.value
        elif isinstance(widget, TextArea):
            return widget.text
        elif isinstance(widget, Select):
            return widget.value
        elif isinstance(widget, (Checkbox, Switch)):
            return widget.value
        elif isinstance(widget, RadioSet):
            return widget.pressed_button.value if widget.pressed_button else None
        # Slider handling removed as not available in current Textual version
        else:
            return None
    
    def _validate_field(self, field: FormField, value: Any) -> Optional[str]:
        """Validate field value"""
        # Required field validation
        if field.required and (value is None or value == ""):
            return f"{field.label} is required"
        
        # Custom validator
        if field.validator and value:
            try:
                result = field.validator.validate(value)
                if not result.is_valid:
                    return result.failure_descriptions[0] if result.failure_descriptions else "Invalid value"
            except Exception as e:
                return str(e)
        
        return None
    
    async def _display_errors(self) -> None:
        """Display field errors"""
        for field_name, error in self.field_errors.items():
            try:
                error_label = self.query_one(f"#error-{field_name}", Label)
                error_label.update(error)
            except:
                pass
        
        # Clear errors for valid fields
        for field in self.fields:
            if field.name not in self.field_errors:
                try:
                    error_label = self.query_one(f"#error-{field.name}", Label)
                    error_label.update("")
                except:
                    pass
    
    def set_field_value(self, field_name: str, value: Any) -> None:
        """Set value for a specific field"""
        widget = self.field_widgets.get(field_name)
        if widget:
            if isinstance(widget, Input):
                widget.value = str(value)
            elif isinstance(widget, TextArea):
                widget.text = str(value)
            elif isinstance(widget, Select):
                widget.value = value
            elif isinstance(widget, (Checkbox, Switch)):
                widget.value = bool(value)
            # Slider handling removed as not available in current Textual version
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get current form data"""
        data = {}
        for field in self.fields:
            widget = self.field_widgets.get(field.name)
            if widget:
                data[field.name] = self._get_widget_value(widget, field)
        return data


class ConfigForm(BaseForm):
    """Configuration form with predefined common fields"""
    
    def __init__(self, config_data: Dict[str, Any] = None, **kwargs):
        # Define common configuration fields
        fields = [
            FormField(
                name="mcp_server_url",
                field_type=FieldType.TEXT,
                label="MCP Server URL",
                default_value="http://localhost:8000",
                required=True,
                placeholder="http://localhost:8000",
                help_text="URL of the MCP server"
            ),
            FormField(
                name="api_key",
                field_type=FieldType.PASSWORD,
                label="API Key",
                required=True,
                help_text="Your HaasOnline API key"
            ),
            FormField(
                name="refresh_interval",
                field_type=FieldType.NUMBER,
                label="Refresh Interval (seconds)",
                default_value=30,
                help_text="How often to refresh data"
            ),
            FormField(
                name="enable_notifications",
                field_type=FieldType.SWITCH,
                label="Enable Notifications",
                default_value=True,
                help_text="Show system notifications"
            ),
            FormField(
                name="theme",
                field_type=FieldType.SELECT,
                label="Theme",
                options=["dark", "light", "auto"],
                default_value="dark",
                help_text="UI color theme"
            ),
        ]
        
        super().__init__(title="Configuration", fields=fields, **kwargs)
        
        # Set values from config data
        if config_data:
            for field in self.fields:
                if field.name in config_data:
                    field.default_value = config_data[field.name]


class SearchForm(BaseForm):
    """Search form with filters"""
    
    def __init__(self, search_callback: Callable = None, **kwargs):
        fields = [
            FormField(
                name="query",
                field_type=FieldType.TEXT,
                label="Search Query",
                placeholder="Enter search terms...",
                help_text="Search across bots, labs, scripts, and workflows"
            ),
            FormField(
                name="category",
                field_type=FieldType.SELECT,
                label="Category",
                options=["all", "bots", "labs", "scripts", "workflows"],
                default_value="all",
                help_text="Filter by category"
            ),
            FormField(
                name="status",
                field_type=FieldType.SELECT,
                label="Status",
                options=["all", "active", "inactive", "error"],
                default_value="all",
                help_text="Filter by status"
            ),
            FormField(
                name="date_range",
                field_type=FieldType.SELECT,
                label="Date Range",
                options=["all", "today", "week", "month", "year"],
                default_value="all",
                help_text="Filter by date range"
            ),
        ]
        
        super().__init__(
            title="Search & Filter",
            fields=fields,
            submit_callback=search_callback,
            **kwargs
        )


class FilterForm(BaseForm):
    """Generic filter form"""
    
    def __init__(
        self,
        filter_fields: List[FormField],
        filter_callback: Callable = None,
        **kwargs
    ):
        super().__init__(
            title="Filters",
            fields=filter_fields,
            submit_callback=filter_callback,
            **kwargs
        )
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Auto-apply filters on input change"""
        if self.submit_callback:
            form_data = self.get_form_data()
            await self.submit_callback(form_data)


class QuickActionForm(BaseForm):
    """Quick action form for common operations"""
    
    def __init__(self, action_type: str, **kwargs):
        self.action_type = action_type
        fields = self._get_action_fields(action_type)
        
        super().__init__(
            title=f"Quick {action_type.title()}",
            fields=fields,
            **kwargs
        )
    
    def _get_action_fields(self, action_type: str) -> List[FormField]:
        """Get fields based on action type"""
        if action_type == "bot":
            return [
                FormField(
                    name="bot_name",
                    field_type=FieldType.TEXT,
                    label="Bot Name",
                    required=True,
                    placeholder="My Trading Bot"
                ),
                FormField(
                    name="trading_pair",
                    field_type=FieldType.SELECT,
                    label="Trading Pair",
                    options=["BTC_USD", "ETH_USD", "ADA_USD"],
                    required=True
                ),
                FormField(
                    name="script_id",
                    field_type=FieldType.SELECT,
                    label="Script",
                    options=[],  # To be populated dynamically
                    required=True
                ),
            ]
        
        elif action_type == "lab":
            return [
                FormField(
                    name="lab_name",
                    field_type=FieldType.TEXT,
                    label="Lab Name",
                    required=True,
                    placeholder="Backtest Lab"
                ),
                FormField(
                    name="trading_pair",
                    field_type=FieldType.SELECT,
                    label="Trading Pair",
                    options=["BTC_USD", "ETH_USD", "ADA_USD"],
                    required=True
                ),
                FormField(
                    name="start_date",
                    field_type=FieldType.DATE,
                    label="Start Date",
                    required=True
                ),
                FormField(
                    name="end_date",
                    field_type=FieldType.DATE,
                    label="End Date",
                    required=True
                ),
            ]
        
        elif action_type == "workflow":
            return [
                FormField(
                    name="workflow_name",
                    field_type=FieldType.TEXT,
                    label="Workflow Name",
                    required=True,
                    placeholder="My Workflow"
                ),
                FormField(
                    name="description",
                    field_type=FieldType.TEXTAREA,
                    label="Description",
                    placeholder="Describe your workflow..."
                ),
            ]
        
        return []