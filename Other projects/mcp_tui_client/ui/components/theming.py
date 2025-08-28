"""
Theming System

Advanced theming system with color schemes and component-specific themes.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from textual.app import App
from textual.widget import Widget
# Stylesheet import removed as not available in current Textual version


class ThemeType(Enum):
    """Theme types"""
    DARK = "dark"
    LIGHT = "light"
    HIGH_CONTRAST = "high_contrast"
    CUSTOM = "custom"


@dataclass
class ColorScheme:
    """Color scheme definition"""
    name: str
    primary: str
    secondary: str
    accent: str
    surface: str
    background: str
    text: str
    text_muted: str
    success: str
    warning: str
    error: str
    info: str
    
    def to_css_vars(self) -> Dict[str, str]:
        """Convert to CSS variables"""
        return {
            "--primary": self.primary,
            "--secondary": self.secondary,
            "--accent": self.accent,
            "--surface": self.surface,
            "--background": self.background,
            "--text": self.text,
            "--text-muted": self.text_muted,
            "--success": self.success,
            "--warning": self.warning,
            "--error": self.error,
            "--info": self.info,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "surface": self.surface,
            "background": self.background,
            "text": self.text,
            "text_muted": self.text_muted,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorScheme':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ComponentTheme:
    """Theme settings for specific components"""
    component_name: str
    styles: Dict[str, Any] = field(default_factory=dict)
    colors: Dict[str, str] = field(default_factory=dict)
    spacing: Dict[str, str] = field(default_factory=dict)
    typography: Dict[str, str] = field(default_factory=dict)
    
    def to_css(self) -> str:
        """Convert to CSS string"""
        css_rules = []
        
        # Component selector
        selector = f".{self.component_name}"
        rules = []
        
        # Add style rules
        for property_name, value in self.styles.items():
            rules.append(f"    {property_name}: {value};")
        
        # Add color rules
        for property_name, color in self.colors.items():
            rules.append(f"    {property_name}: {color};")
        
        # Add spacing rules
        for property_name, spacing in self.spacing.items():
            rules.append(f"    {property_name}: {spacing};")
        
        # Add typography rules
        for property_name, typography in self.typography.items():
            rules.append(f"    {property_name}: {typography};")
        
        if rules:
            css_rules.append(f"{selector} {{")
            css_rules.extend(rules)
            css_rules.append("}")
        
        return "\n".join(css_rules)


@dataclass
class Theme:
    """Complete theme definition"""
    name: str
    theme_type: ThemeType
    color_scheme: ColorScheme
    component_themes: Dict[str, ComponentTheme] = field(default_factory=dict)
    custom_css: str = ""
    
    def add_component_theme(self, component_theme: ComponentTheme) -> None:
        """Add component-specific theme"""
        self.component_themes[component_theme.component_name] = component_theme
    
    def get_component_theme(self, component_name: str) -> Optional[ComponentTheme]:
        """Get component-specific theme"""
        return self.component_themes.get(component_name)
    
    def to_css(self) -> str:
        """Generate complete CSS for theme"""
        css_parts = []
        
        # Root variables
        css_parts.append(":root {")
        for var_name, color in self.color_scheme.to_css_vars().items():
            css_parts.append(f"    {var_name}: {color};")
        css_parts.append("}")
        css_parts.append("")
        
        # Component themes
        for component_theme in self.component_themes.values():
            component_css = component_theme.to_css()
            if component_css:
                css_parts.append(component_css)
                css_parts.append("")
        
        # Custom CSS
        if self.custom_css:
            css_parts.append(self.custom_css)
        
        return "\n".join(css_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "theme_type": self.theme_type.value,
            "color_scheme": self.color_scheme.to_dict(),
            "component_themes": {
                name: {
                    "component_name": theme.component_name,
                    "styles": theme.styles,
                    "colors": theme.colors,
                    "spacing": theme.spacing,
                    "typography": theme.typography,
                }
                for name, theme in self.component_themes.items()
            },
            "custom_css": self.custom_css,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """Create from dictionary"""
        color_scheme = ColorScheme.from_dict(data["color_scheme"])
        theme = cls(
            name=data["name"],
            theme_type=ThemeType(data["theme_type"]),
            color_scheme=color_scheme,
            custom_css=data.get("custom_css", "")
        )
        
        # Add component themes
        for name, component_data in data.get("component_themes", {}).items():
            component_theme = ComponentTheme(
                component_name=component_data["component_name"],
                styles=component_data.get("styles", {}),
                colors=component_data.get("colors", {}),
                spacing=component_data.get("spacing", {}),
                typography=component_data.get("typography", {}),
            )
            theme.add_component_theme(component_theme)
        
        return theme


class ThemeManager:
    """Manages themes and theme switching"""
    
    def __init__(self, app: App = None):
        self.app = app
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None
        self.theme_change_callbacks: List[Callable[[Theme], None]] = []
        self.themes_directory = Path("~/.mcp-tui/themes").expanduser()
        self.themes_directory.mkdir(parents=True, exist_ok=True)
        
        # Load built-in themes
        self._load_builtin_themes()
        
        # Load custom themes
        self._load_custom_themes()
    
    def _load_builtin_themes(self) -> None:
        """Load built-in themes"""
        # Dark theme
        dark_colors = ColorScheme(
            name="Dark",
            primary="#00d4aa",
            secondary="#1f2937",
            accent="#ff6b35",
            surface="#1a1a1a",
            background="#0d1117",
            text="#f0f6fc",
            text_muted="#8b949e",
            success="#238636",
            warning="#d29922",
            error="#da3633",
            info="#0969da"
        )
        
        dark_theme = Theme(
            name="Dark",
            theme_type=ThemeType.DARK,
            color_scheme=dark_colors
        )
        
        # Add component themes for dark theme
        self._add_dark_component_themes(dark_theme)
        self.add_theme(dark_theme)
        
        # Light theme
        light_colors = ColorScheme(
            name="Light",
            primary="#0969da",
            secondary="#f6f8fa",
            accent="#d73a49",
            surface="#ffffff",
            background="#f6f8fa",
            text="#24292f",
            text_muted="#656d76",
            success="#28a745",
            warning="#ffc107",
            error="#dc3545",
            info="#17a2b8"
        )
        
        light_theme = Theme(
            name="Light",
            theme_type=ThemeType.LIGHT,
            color_scheme=light_colors
        )
        
        # Add component themes for light theme
        self._add_light_component_themes(light_theme)
        self.add_theme(light_theme)
        
        # High contrast theme
        high_contrast_colors = ColorScheme(
            name="High Contrast",
            primary="#ffffff",
            secondary="#000000",
            accent="#ffff00",
            surface="#000000",
            background="#000000",
            text="#ffffff",
            text_muted="#cccccc",
            success="#00ff00",
            warning="#ffff00",
            error="#ff0000",
            info="#00ffff"
        )
        
        high_contrast_theme = Theme(
            name="High Contrast",
            theme_type=ThemeType.HIGH_CONTRAST,
            color_scheme=high_contrast_colors
        )
        
        # Add component themes for high contrast theme
        self._add_high_contrast_component_themes(high_contrast_theme)
        self.add_theme(high_contrast_theme)
        
        # Set dark as default
        self.set_theme("Dark")
    
    def _add_dark_component_themes(self, theme: Theme) -> None:
        """Add component themes for dark theme"""
        # Panel theme
        panel_theme = ComponentTheme(
            component_name="BasePanel",
            styles={
                "border": "solid $primary",
                "background": "$surface",
                "padding": "1",
            },
            colors={
                "color": "$text",
            }
        )
        theme.add_component_theme(panel_theme)
        
        # Table theme
        table_theme = ComponentTheme(
            component_name="DataTable",
            styles={
                "background": "$surface",
                "border": "solid $primary",
            },
            colors={
                "color": "$text",
            }
        )
        theme.add_component_theme(table_theme)
        
        # Button theme
        button_theme = ComponentTheme(
            component_name="Button",
            styles={
                "background": "$primary",
                "border": "solid $primary",
                "padding": "0 2",
            },
            colors={
                "color": "$background",
            }
        )
        theme.add_component_theme(button_theme)
    
    def _add_light_component_themes(self, theme: Theme) -> None:
        """Add component themes for light theme"""
        # Panel theme
        panel_theme = ComponentTheme(
            component_name="BasePanel",
            styles={
                "border": "solid $primary",
                "background": "$surface",
                "padding": "1",
            },
            colors={
                "color": "$text",
            }
        )
        theme.add_component_theme(panel_theme)
        
        # Table theme
        table_theme = ComponentTheme(
            component_name="DataTable",
            styles={
                "background": "$surface",
                "border": "solid $primary",
            },
            colors={
                "color": "$text",
            }
        )
        theme.add_component_theme(table_theme)
        
        # Button theme
        button_theme = ComponentTheme(
            component_name="Button",
            styles={
                "background": "$primary",
                "border": "solid $primary",
                "padding": "0 2",
            },
            colors={
                "color": "$surface",
            }
        )
        theme.add_component_theme(button_theme)
    
    def _add_high_contrast_component_themes(self, theme: Theme) -> None:
        """Add component themes for high contrast theme"""
        # Panel theme
        panel_theme = ComponentTheme(
            component_name="BasePanel",
            styles={
                "border": "solid $primary",
                "background": "$surface",
                "padding": "1",
            },
            colors={
                "color": "$text",
            }
        )
        theme.add_component_theme(panel_theme)
        
        # Table theme
        table_theme = ComponentTheme(
            component_name="DataTable",
            styles={
                "background": "$surface",
                "border": "solid $primary",
            },
            colors={
                "color": "$text",
            }
        )
        theme.add_component_theme(table_theme)
        
        # Button theme
        button_theme = ComponentTheme(
            component_name="Button",
            styles={
                "background": "$accent",
                "border": "solid $primary",
                "padding": "0 2",
            },
            colors={
                "color": "$surface",
            }
        )
        theme.add_component_theme(button_theme)
    
    def _load_custom_themes(self) -> None:
        """Load custom themes from files"""
        for theme_file in self.themes_directory.glob("*.json"):
            try:
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)
                    theme = Theme.from_dict(theme_data)
                    self.add_theme(theme)
            except Exception as e:
                print(f"Error loading theme from {theme_file}: {e}")
    
    def add_theme(self, theme: Theme) -> None:
        """Add a theme to the manager"""
        self.themes[theme.name] = theme
    
    def remove_theme(self, theme_name: str) -> None:
        """Remove a theme"""
        if theme_name in self.themes:
            del self.themes[theme_name]
            
            # If this was the current theme, switch to default
            if self.current_theme and self.current_theme.name == theme_name:
                self.set_theme("Dark")
    
    def get_theme(self, theme_name: str) -> Optional[Theme]:
        """Get a theme by name"""
        return self.themes.get(theme_name)
    
    def get_theme_names(self) -> List[str]:
        """Get list of available theme names"""
        return list(self.themes.keys())
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme"""
        if theme_name not in self.themes:
            return False
        
        old_theme = self.current_theme
        self.current_theme = self.themes[theme_name]
        
        # Apply theme to app if available
        if self.app:
            self._apply_theme_to_app()
        
        # Notify callbacks
        for callback in self.theme_change_callbacks:
            try:
                callback(self.current_theme)
            except Exception as e:
                print(f"Error in theme change callback: {e}")
        
        return True
    
    def get_current_theme(self) -> Optional[Theme]:
        """Get the current theme"""
        return self.current_theme
    
    def _apply_theme_to_app(self) -> None:
        """Apply current theme to the app"""
        if not self.app or not self.current_theme:
            return
        
        try:
            # Generate CSS for the theme
            theme_css = self.current_theme.to_css()
            
            # Apply CSS to app (simplified approach)
            # In practice, you might need to reload stylesheets or use other methods
            # Note: Direct stylesheet manipulation not available in current Textual version
            # This would require a different approach in a real implementation
            if hasattr(self.app, 'refresh'):
                self.app.refresh()
        except Exception as e:
            print(f"Error applying theme to app: {e}")
    
    def save_theme(self, theme: Theme, filename: str = None) -> bool:
        """Save a theme to file"""
        if not filename:
            filename = f"{theme.name.lower().replace(' ', '_')}.json"
        
        theme_file = self.themes_directory / filename
        
        try:
            with open(theme_file, 'w') as f:
                json.dump(theme.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving theme: {e}")
            return False
    
    def create_custom_theme(
        self,
        name: str,
        base_theme_name: str = "Dark",
        color_overrides: Dict[str, str] = None,
        component_overrides: Dict[str, ComponentTheme] = None
    ) -> Optional[Theme]:
        """Create a custom theme based on an existing theme"""
        base_theme = self.get_theme(base_theme_name)
        if not base_theme:
            return None
        
        # Create new color scheme with overrides
        color_data = base_theme.color_scheme.to_dict()
        if color_overrides:
            color_data.update(color_overrides)
        
        custom_color_scheme = ColorScheme.from_dict(color_data)
        
        # Create custom theme
        custom_theme = Theme(
            name=name,
            theme_type=ThemeType.CUSTOM,
            color_scheme=custom_color_scheme,
            custom_css=base_theme.custom_css
        )
        
        # Copy component themes
        for component_name, component_theme in base_theme.component_themes.items():
            new_component_theme = ComponentTheme(
                component_name=component_theme.component_name,
                styles=component_theme.styles.copy(),
                colors=component_theme.colors.copy(),
                spacing=component_theme.spacing.copy(),
                typography=component_theme.typography.copy(),
            )
            custom_theme.add_component_theme(new_component_theme)
        
        # Apply component overrides
        if component_overrides:
            for component_name, override_theme in component_overrides.items():
                custom_theme.add_component_theme(override_theme)
        
        self.add_theme(custom_theme)
        return custom_theme
    
    def add_theme_change_callback(self, callback: Callable[[Theme], None]) -> None:
        """Add callback for theme changes"""
        self.theme_change_callbacks.append(callback)
    
    def remove_theme_change_callback(self, callback: Callable[[Theme], None]) -> None:
        """Remove theme change callback"""
        if callback in self.theme_change_callbacks:
            self.theme_change_callbacks.remove(callback)
    
    def get_component_style(self, component_name: str, property_name: str) -> Optional[str]:
        """Get a specific style property for a component"""
        if not self.current_theme:
            return None
        
        component_theme = self.current_theme.get_component_theme(component_name)
        if not component_theme:
            return None
        
        # Check in different style categories
        for style_dict in [component_theme.styles, component_theme.colors, 
                          component_theme.spacing, component_theme.typography]:
            if property_name in style_dict:
                return style_dict[property_name]
        
        return None
    
    def update_component_style(
        self,
        component_name: str,
        property_name: str,
        value: str,
        style_category: str = "styles"
    ) -> bool:
        """Update a component style property"""
        if not self.current_theme:
            return False
        
        component_theme = self.current_theme.get_component_theme(component_name)
        if not component_theme:
            # Create new component theme
            component_theme = ComponentTheme(component_name=component_name)
            self.current_theme.add_component_theme(component_theme)
        
        # Update the appropriate style category
        style_dict = getattr(component_theme, style_category, {})
        style_dict[property_name] = value
        
        # Apply changes if app is available
        if self.app:
            self._apply_theme_to_app()
        
        return True


# Utility functions for theme-aware widgets

def get_theme_color(theme_manager: ThemeManager, color_name: str) -> str:
    """Get a color from the current theme"""
    if not theme_manager.current_theme:
        return "#ffffff"  # Default fallback
    
    color_scheme = theme_manager.current_theme.color_scheme
    return getattr(color_scheme, color_name, "#ffffff")


def apply_theme_to_widget(widget: Widget, theme_manager: ThemeManager) -> None:
    """Apply current theme styles to a widget"""
    if not theme_manager.current_theme:
        return
    
    widget_class = widget.__class__.__name__
    component_theme = theme_manager.current_theme.get_component_theme(widget_class)
    
    if component_theme:
        # Apply styles (this is a simplified approach)
        # In practice, you'd need to map CSS properties to widget properties
        for property_name, value in component_theme.styles.items():
            if hasattr(widget, property_name):
                setattr(widget, property_name, value)


class ThemeAwareWidget(Widget):
    """Base class for theme-aware widgets"""
    
    def __init__(self, theme_manager: ThemeManager = None, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = theme_manager
        
        if self.theme_manager:
            self.theme_manager.add_theme_change_callback(self._on_theme_change)
            self._apply_current_theme()
    
    def _on_theme_change(self, new_theme: Theme) -> None:
        """Handle theme changes"""
        self._apply_current_theme()
    
    def _apply_current_theme(self) -> None:
        """Apply current theme to this widget"""
        if self.theme_manager:
            apply_theme_to_widget(self, self.theme_manager)
    
    def on_unmount(self) -> None:
        """Clean up theme callbacks"""
        if self.theme_manager:
            self.theme_manager.remove_theme_change_callback(self._on_theme_change)
        super().on_unmount()