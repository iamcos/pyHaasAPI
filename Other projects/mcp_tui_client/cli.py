"""
Command Line Interface for MCP TUI Client

This module provides the command-line interface and argument parsing
for the MCP TUI Client application.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

import click

from . import __version__, __description__
from .app import MCPTUIApp
from .services.config import ConfigurationService


@click.command()
@click.version_option(version=__version__, prog_name="mcp-tui-client")
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file"
)
@click.option(
    "--host", "-h",
    type=str,
    help="MCP server host (overrides config)"
)
@click.option(
    "--port", "-p",
    type=int,
    help="MCP server port (overrides config)"
)
@click.option(
    "--debug", "-d",
    is_flag=True,
    help="Enable debug logging"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set logging level"
)
@click.option(
    "--theme",
    type=click.Choice(["dark", "light", "auto"], case_sensitive=False),
    help="UI theme (overrides config)"
)
@click.option(
    "--no-connect",
    is_flag=True,
    help="Start without connecting to MCP server (demo mode)"
)
@click.option(
    "--check-config",
    is_flag=True,
    help="Validate configuration and exit"
)
def main(
    config: Optional[Path],
    host: Optional[str],
    port: Optional[int],
    debug: bool,
    log_level: str,
    theme: Optional[str],
    no_connect: bool,
    check_config: bool
) -> None:
    """
    MCP TUI Client - Terminal User Interface for HaasOnline MCP Server
    
    A comprehensive terminal-based interface for managing HaasOnline trading
    operations through the Model Context Protocol (MCP) server.
    """
    
    # Set up logging level
    if debug:
        log_level = "DEBUG"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting MCP TUI Client v{__version__}")
    
    try:
        # Load configuration
        config_service = ConfigurationService(str(config) if config else None)
        
        # Override config with command line arguments
        if host:
            config_service.config["mcp"]["host"] = host
        if port:
            config_service.config["mcp"]["port"] = port
        if theme:
            config_service.config["ui"]["theme"] = theme
        if no_connect:
            config_service.config["mcp"]["auto_connect"] = False
        
        # Validate configuration if requested
        if check_config:
            if config_service.validate_config(config_service.config):
                click.echo("✓ Configuration is valid")
                sys.exit(0)
            else:
                click.echo("✗ Configuration is invalid", err=True)
                sys.exit(1)
        
        # Create and run the application
        app = MCPTUIApp(str(config) if config else None)
        
        # Set debug mode if requested
        if debug:
            app.debug = True
        
        logger.info("Launching TUI application")
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        if debug:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
@click.version_option(version=__version__)
def cli():
    """MCP TUI Client command line tools."""
    pass


@cli.command()
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Output path for configuration file"
)
def init_config(output: Optional[Path]) -> None:
    """Initialize a new configuration file with default settings."""
    
    if output is None:
        output = Path.home() / ".mcp-tui" / "config.json"
    
    try:
        config_service = ConfigurationService()
        
        # Ensure directory exists
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Save default config to specified location
        config_service.config_path = output
        config_service.save_config()
        
        click.echo(f"✓ Configuration file created at: {output}")
        click.echo("You can now edit this file to customize your settings.")
        
    except Exception as e:
        click.echo(f"✗ Failed to create configuration file: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file to validate"
)
def validate_config(config: Optional[Path]) -> None:
    """Validate a configuration file."""
    
    try:
        config_service = ConfigurationService(str(config) if config else None)
        
        if config_service.validate_config(config_service.config):
            click.echo("✓ Configuration is valid")
            
            # Show configuration summary
            mcp_settings = config_service.get_mcp_settings()
            ui_prefs = config_service.get_ui_preferences()
            
            click.echo("\nConfiguration Summary:")
            click.echo(f"  MCP Host: {mcp_settings['host']}")
            click.echo(f"  MCP Port: {mcp_settings['port']}")
            click.echo(f"  UI Theme: {ui_prefs['theme']}")
            click.echo(f"  Auto Refresh: {ui_prefs['auto_refresh_interval']}s")
            
        else:
            click.echo("✗ Configuration is invalid", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ Error validating configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--host", "-h",
    required=True,
    help="MCP server host"
)
@click.option(
    "--port", "-p",
    type=int,
    required=True,
    help="MCP server port"
)
@click.option(
    "--timeout", "-t",
    type=int,
    default=30,
    help="Connection timeout in seconds"
)
def test_connection(host: str, port: int, timeout: int) -> None:
    """Test connection to MCP server."""
    
    import asyncio
    from .services.mcp_client import MCPClientService
    
    async def test_mcp_connection():
        config = {
            "host": host,
            "port": port,
            "timeout": timeout,
            "retry_attempts": 1,
            "use_ssl": False
        }
        
        client = MCPClientService(config)
        
        try:
            click.echo(f"Testing connection to {host}:{port}...")
            
            result = await client.connect()
            
            if result:
                click.echo("✓ Connection successful")
                
                # Test a simple tool call
                try:
                    status = await client.call_tool("get_haas_status", {})
                    click.echo(f"✓ MCP server is responding: {status.get('status', 'Unknown')}")
                except Exception as e:
                    click.echo(f"⚠ Connection established but tool call failed: {e}")
                
            else:
                click.echo("✗ Connection failed", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"✗ Connection error: {e}", err=True)
            sys.exit(1)
        finally:
            await client.disconnect()
    
    try:
        asyncio.run(test_mcp_connection())
    except KeyboardInterrupt:
        click.echo("\nConnection test interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()