"""
Settings View

Application settings and configuration interface.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static


class ConnectionSettingsPanel(Widget):
    """Panel with MCP connection settings"""
    
    def compose(self) -> ComposeResult:
        yield Static("MCP Connection", classes="panel-title")
        yield Static("Server Settings:")
        yield Static("• Host: localhost")
        yield Static("• Port: 3002")
        yield Static("• Timeout: 30s")
        yield Static("• Retry Attempts: 3")
        yield Static("• Use SSL: No")
        yield Static("")
        yield Static("Status: 🟢 Connected")
        yield Static("Last Connected: 2024-01-20 10:30:00")
        yield Static("Uptime: 2h 15m")
        yield Static("")
        yield Static("Actions:")
        yield Static("• [T]est Connection")
        yield Static("• [R]econnect")
        yield Static("• [E]dit Settings")


class UIPreferencesPanel(Widget):
    """Panel with UI preferences"""
    
    def compose(self) -> ComposeResult:
        yield Static("UI Preferences", classes="panel-title")
        yield Static("Theme Settings:")
        yield Static("• Theme: Dark")
        yield Static("• Color Scheme: Default")
        yield Static("• Chart Style: ASCII")
        yield Static("• Panel Layout: Default")
        yield Static("")
        yield Static("Behavior:")
        yield Static("• Auto Refresh: 5s")
        yield Static("• Show Help on Startup: Yes")
        yield Static("• Confirm Actions: Yes")
        yield Static("• Sound Alerts: No")
        yield Static("")
        yield Static("Keyboard Shortcuts:")
        yield Static("• F1-F8: View Navigation")
        yield Static("• Ctrl+Q: Quit")
        yield Static("• Ctrl+R: Refresh")
        yield Static("• Ctrl+H: Help")


class LoggingSettingsPanel(Widget):
    """Panel with logging settings"""
    
    def compose(self) -> ComposeResult:
        yield Static("Logging Configuration", classes="panel-title")
        yield Static("Log Level: INFO")
        yield Static("Log File: ~/.mcp-tui/logs/app.log")
        yield Static("Max File Size: 10MB")
        yield Static("Backup Count: 5")
        yield Static("")
        yield Static("Current Log Size: 2.3MB")
        yield Static("Last Rotation: 2024-01-18 09:00:00")
        yield Static("")
        yield Static("Log Categories:")
        yield Static("• Application: INFO")
        yield Static("• MCP Client: DEBUG")
        yield Static("• UI Events: WARNING")
        yield Static("• Performance: INFO")
        yield Static("")
        yield Static("Actions:")
        yield Static("• [V]iew Logs")
        yield Static("• [C]lear Logs")
        yield Static("• [R]otate Now")


class DataManagementPanel(Widget):
    """Panel with data management settings"""
    
    def compose(self) -> ComposeResult:
        yield Static("Data Management", classes="panel-title")
        yield Static("Cache Settings:")
        yield Static("• Cache Size: 1000 items")
        yield Static("• TTL: 5 minutes")
        yield Static("• Current Usage: 45%")
        yield Static("")
        yield Static("Data Storage:")
        yield Static("• Config Dir: ~/.mcp-tui/")
        yield Static("• Cache Dir: ~/.mcp-tui/cache/")
        yield Static("• Logs Dir: ~/.mcp-tui/logs/")
        yield Static("• Total Size: 15.7MB")
        yield Static("")
        yield Static("Backup & Restore:")
        yield Static("• Last Backup: 2024-01-19 20:00:00")
        yield Static("• Auto Backup: Daily")
        yield Static("• Backup Location: ~/.mcp-tui/backups/")
        yield Static("")
        yield Static("Actions:")
        yield Static("• [B]ackup Now")
        yield Static("• [R]estore")
        yield Static("• [C]lean Cache")


class SecuritySettingsPanel(Widget):
    """Panel with security settings"""
    
    def compose(self) -> ComposeResult:
        yield Static("Security Settings", classes="panel-title")
        yield Static("Credential Storage:")
        yield Static("• Method: System Keyring")
        yield Static("• Encryption: AES-256")
        yield Static("• Status: 🟢 Secure")
        yield Static("")
        yield Static("API Security:")
        yield Static("• Token Refresh: Auto")
        yield Static("• Session Timeout: 1 hour")
        yield Static("• Rate Limiting: Enabled")
        yield Static("")
        yield Static("Audit Log:")
        yield Static("• Login Events: Enabled")
        yield Static("• API Calls: Enabled")
        yield Static("• Configuration Changes: Enabled")
        yield Static("")
        yield Static("Actions:")
        yield Static("• [C]hange Credentials")
        yield Static("• [V]iew Audit Log")
        yield Static("• [R]eset Security")


class AboutPanel(Widget):
    """Panel with application information"""
    
    def compose(self) -> ComposeResult:
        yield Static("About MCP TUI Client", classes="panel-title")
        yield Static("Version: 0.1.0")
        yield Static("Build: 2024.01.20-dev")
        yield Static("Python: 3.11.5")
        yield Static("Textual: 0.48.2")
        yield Static("")
        yield Static("Components:")
        yield Static("• MCP Client: Connected")
        yield Static("• pyHaasAPI: 1.0.0")
        yield Static("• Rich/Textual: 0.48.2")
        yield Static("")
        yield Static("System Info:")
        yield Static("• OS: macOS 14.2")
        yield Static("• Terminal: iTerm2")
        yield Static("• Memory Usage: 45.2MB")
        yield Static("• CPU Usage: 2.1%")
        yield Static("")
        yield Static("Support:")
        yield Static("• Documentation: F1")
        yield Static("• GitHub: github.com/haasonline/mcp-tui")
        yield Static("• Issues: Report bugs online")


class SettingsView(Widget):
    """Application settings and configuration interface"""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            ConnectionSettingsPanel(classes="panel"),
            UIPreferencesPanel(classes="panel"),
            LoggingSettingsPanel(classes="panel"),
            classes="settings-top"
        )
        yield Horizontal(
            DataManagementPanel(classes="panel"),
            SecuritySettingsPanel(classes="panel"),
            AboutPanel(classes="panel"),
            classes="settings-bottom"
        )
    
    def set_mcp_client(self, mcp_client):
        """Set MCP client for data updates"""
        self.mcp_client = mcp_client
    
    async def refresh_data(self):
        """Refresh settings data"""
        # TODO: Implement data refresh
        pass