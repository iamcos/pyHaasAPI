"""
Input nodes for workflow system.

This module provides nodes for inputting parameters and configuration data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..node_base import WorkflowNode, DataType, ValidationError
from ..node_registry import register_node, NodeCategory


@register_node(
    category=NodeCategory.INPUT,
    display_name="Parameter Input",
    description="Input parameters for workflow execution",
    icon="📝",
    tags=["input", "parameters", "configuration"]
)
class ParameterInputNode(WorkflowNode):
    """Node for inputting parameters into workflows."""
    
    _category = NodeCategory.INPUT
    _display_name = "Parameter Input"
    _description = "Input parameters for workflow execution"
    _icon = "📝"
    _tags = ["input", "parameters", "configuration"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # No input ports - this is a source node
        
        # Output ports
        self.add_output_port("parameters", DataType.DICT,
                            "Output parameters")
        self.add_output_port("parameter_count", DataType.INTEGER,
                            "Number of parameters")
        self.add_output_port("validation_status", DataType.STRING,
                            "Parameter validation status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "parameter_definitions": {},  # Dict of parameter name -> config
            "validate_types": True,
            "allow_empty": False,
            "default_values": {}
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute parameter input."""
        try:
            parameter_definitions = self.get_parameter("parameter_definitions", {})
            validate_types = self.get_parameter("validate_types", True)
            allow_empty = self.get_parameter("allow_empty", False)
            default_values = self.get_parameter("default_values", {})
            
            # Build output parameters
            output_parameters = {}
            validation_errors = []
            
            for param_name, param_config in parameter_definitions.items():
                # Get parameter value from various sources
                param_value = self._get_parameter_value(param_name, param_config, default_values, context)
                
                # Validate parameter if requested
                if validate_types:
                    validation_result = self._validate_parameter(param_name, param_value, param_config)
                    if not validation_result["valid"]:
                        validation_errors.append(validation_result["error"])
                        continue
                
                # Check for empty values
                if not allow_empty and self._is_empty_value(param_value):
                    if param_config.get("required", False):
                        validation_errors.append(f"Required parameter '{param_name}' is empty")
                        continue
                
                output_parameters[param_name] = param_value
            
            # Determine validation status
            if validation_errors:
                validation_status = f"validation_failed: {'; '.join(validation_errors)}"
            else:
                validation_status = "valid"
            
            return {
                "parameters": output_parameters,
                "parameter_count": len(output_parameters),
                "validation_status": validation_status
            }
            
        except Exception as e:
            return {
                "parameters": {},
                "parameter_count": 0,
                "validation_status": f"error: {str(e)}"
            }
    
    def _get_parameter_value(self, param_name: str, param_config: Dict[str, Any], 
                           default_values: Dict[str, Any], context) -> Any:
        """Get parameter value from various sources."""
        # Priority order:
        # 1. Context execution state (runtime values)
        # 2. Node parameters (configured values)
        # 3. Default values
        # 4. Parameter config default
        
        # Check execution context
        if hasattr(context, 'execution_state') and 'input_parameters' in context.execution_state:
            runtime_params = context.execution_state.get('input_parameters', {})
            if param_name in runtime_params:
                return runtime_params[param_name]
        
        # Check node parameters
        if param_name in self.parameters:
            return self.parameters[param_name]
        
        # Check default values
        if param_name in default_values:
            return default_values[param_name]
        
        # Check parameter config default
        return param_config.get("default", None)
    
    def _validate_parameter(self, param_name: str, param_value: Any, 
                          param_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a parameter value."""
        param_type = param_config.get("type", "string")
        
        try:
            # Type validation
            if param_type == "string" and not isinstance(param_value, str):
                if param_value is not None:
                    param_value = str(param_value)
            elif param_type == "integer":
                if not isinstance(param_value, int):
                    param_value = int(param_value)
            elif param_type == "float":
                if not isinstance(param_value, (int, float)):
                    param_value = float(param_value)
            elif param_type == "boolean":
                if not isinstance(param_value, bool):
                    param_value = bool(param_value)
            elif param_type == "list":
                if not isinstance(param_value, list):
                    return {"valid": False, "error": f"Parameter '{param_name}' must be a list"}
            elif param_type == "dict":
                if not isinstance(param_value, dict):
                    return {"valid": False, "error": f"Parameter '{param_name}' must be a dictionary"}
            
            # Range validation for numeric types
            if param_type in ["integer", "float"]:
                min_value = param_config.get("min")
                max_value = param_config.get("max")
                
                if min_value is not None and param_value < min_value:
                    return {"valid": False, "error": f"Parameter '{param_name}' must be >= {min_value}"}
                
                if max_value is not None and param_value > max_value:
                    return {"valid": False, "error": f"Parameter '{param_name}' must be <= {max_value}"}
            
            # String length validation
            if param_type == "string":
                min_length = param_config.get("min_length")
                max_length = param_config.get("max_length")
                
                if min_length is not None and len(param_value) < min_length:
                    return {"valid": False, "error": f"Parameter '{param_name}' must be at least {min_length} characters"}
                
                if max_length is not None and len(param_value) > max_length:
                    return {"valid": False, "error": f"Parameter '{param_name}' must be at most {max_length} characters"}
            
            # Choice validation
            choices = param_config.get("choices")
            if choices and param_value not in choices:
                return {"valid": False, "error": f"Parameter '{param_name}' must be one of: {choices}"}
            
            return {"valid": True, "value": param_value}
            
        except (ValueError, TypeError) as e:
            return {"valid": False, "error": f"Parameter '{param_name}' type conversion failed: {str(e)}"}
    
    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value is considered empty."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False
    
    def add_parameter_definition(self, name: str, param_type: str = "string", 
                               required: bool = False, default: Any = None,
                               description: str = "", **kwargs) -> None:
        """Add a parameter definition to this node."""
        if "parameter_definitions" not in self.parameters:
            self.parameters["parameter_definitions"] = {}
        
        self.parameters["parameter_definitions"][name] = {
            "type": param_type,
            "required": required,
            "default": default,
            "description": description,
            **kwargs
        }
    
    def set_default_value(self, name: str, value: Any) -> None:
        """Set a default value for a parameter."""
        if "default_values" not in self.parameters:
            self.parameters["default_values"] = {}
        
        self.parameters["default_values"][name] = value


@register_node(
    category=NodeCategory.INPUT,
    display_name="Configuration Input",
    description="Input configuration data from various sources",
    icon="⚙️",
    tags=["input", "configuration", "settings"]
)
class ConfigInputNode(WorkflowNode):
    """Node for inputting configuration data."""
    
    _category = NodeCategory.INPUT
    _display_name = "Configuration Input"
    _description = "Input configuration data from various sources"
    _icon = "⚙️"
    _tags = ["input", "configuration", "settings"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("config_source", DataType.STRING, False,
                           "Configuration source (file, env, inline)", "inline")
        self.add_input_port("config_path", DataType.STRING, False,
                           "Path to configuration file")
        
        # Output ports
        self.add_output_port("configuration", DataType.DICT,
                            "Loaded configuration")
        self.add_output_port("config_keys", DataType.LIST,
                            "List of configuration keys")
        self.add_output_port("load_status", DataType.STRING,
                            "Configuration load status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "inline_config": {},
            "environment_prefix": "WORKFLOW_",
            "config_format": "json",  # json, yaml, ini
            "merge_sources": True,
            "validate_schema": False,
            "config_schema": {}
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute configuration loading."""
        try:
            config_source = self.get_input_value("config_source", context)
            config_path = self.get_input_value("config_path", context)
            
            configuration = {}
            load_errors = []
            
            # Load configuration from different sources
            if config_source == "inline" or not config_source:
                inline_config = self.get_parameter("inline_config", {})
                configuration.update(inline_config)
            
            elif config_source == "file":
                if config_path:
                    file_config, file_error = await self._load_file_config(config_path)
                    if file_error:
                        load_errors.append(file_error)
                    else:
                        configuration.update(file_config)
                else:
                    load_errors.append("Config path required for file source")
            
            elif config_source == "env":
                env_config = self._load_environment_config()
                configuration.update(env_config)
            
            elif config_source == "all":
                # Load from all sources and merge
                inline_config = self.get_parameter("inline_config", {})
                configuration.update(inline_config)
                
                if config_path:
                    file_config, file_error = await self._load_file_config(config_path)
                    if not file_error:
                        configuration.update(file_config)
                
                env_config = self._load_environment_config()
                configuration.update(env_config)
            
            # Validate schema if requested
            if self.get_parameter("validate_schema", False):
                schema_validation = self._validate_config_schema(configuration)
                if not schema_validation["valid"]:
                    load_errors.append(f"Schema validation failed: {schema_validation['error']}")
            
            # Determine load status
            if load_errors:
                load_status = f"partial_success: {'; '.join(load_errors)}"
            else:
                load_status = "success"
            
            return {
                "configuration": configuration,
                "config_keys": list(configuration.keys()),
                "load_status": load_status
            }
            
        except Exception as e:
            return {
                "configuration": {},
                "config_keys": [],
                "load_status": f"error: {str(e)}"
            }
    
    async def _load_file_config(self, config_path: str) -> tuple[Dict[str, Any], Optional[str]]:
        """Load configuration from file."""
        try:
            import json
            import os
            
            if not os.path.exists(config_path):
                return {}, f"Configuration file not found: {config_path}"
            
            config_format = self.get_parameter("config_format", "json")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_format == "json":
                    config = json.load(f)
                elif config_format == "yaml":
                    import yaml
                    config = yaml.safe_load(f)
                elif config_format == "ini":
                    import configparser
                    parser = configparser.ConfigParser()
                    parser.read(config_path)
                    config = {section: dict(parser[section]) for section in parser.sections()}
                else:
                    return {}, f"Unsupported config format: {config_format}"
            
            return config, None
            
        except Exception as e:
            return {}, f"Failed to load config file: {str(e)}"
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        import os
        
        env_prefix = self.get_parameter("environment_prefix", "WORKFLOW_")
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                
                # Try to convert to appropriate type
                try:
                    # Try boolean
                    if value.lower() in ('true', 'false'):
                        config[config_key] = value.lower() == 'true'
                    # Try integer
                    elif value.isdigit():
                        config[config_key] = int(value)
                    # Try float
                    elif '.' in value and value.replace('.', '').isdigit():
                        config[config_key] = float(value)
                    # Keep as string
                    else:
                        config[config_key] = value
                except ValueError:
                    config[config_key] = value
        
        return config
    
    def _validate_config_schema(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration against schema."""
        config_schema = self.get_parameter("config_schema", {})
        
        if not config_schema:
            return {"valid": True}
        
        try:
            # Simple schema validation
            for key, schema_def in config_schema.items():
                if key not in configuration:
                    if schema_def.get("required", False):
                        return {"valid": False, "error": f"Required key '{key}' missing"}
                    continue
                
                value = configuration[key]
                expected_type = schema_def.get("type")
                
                if expected_type:
                    if expected_type == "string" and not isinstance(value, str):
                        return {"valid": False, "error": f"Key '{key}' must be string"}
                    elif expected_type == "integer" and not isinstance(value, int):
                        return {"valid": False, "error": f"Key '{key}' must be integer"}
                    elif expected_type == "float" and not isinstance(value, (int, float)):
                        return {"valid": False, "error": f"Key '{key}' must be number"}
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        return {"valid": False, "error": f"Key '{key}' must be boolean"}
                    elif expected_type == "list" and not isinstance(value, list):
                        return {"valid": False, "error": f"Key '{key}' must be list"}
                    elif expected_type == "dict" and not isinstance(value, dict):
                        return {"valid": False, "error": f"Key '{key}' must be dictionary"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Schema validation error: {str(e)}"}
    
    def set_inline_config(self, config: Dict[str, Any]) -> None:
        """Set inline configuration."""
        self.parameters["inline_config"] = config
    
    def add_config_item(self, key: str, value: Any) -> None:
        """Add a single configuration item."""
        if "inline_config" not in self.parameters:
            self.parameters["inline_config"] = {}
        
        self.parameters["inline_config"][key] = value
    
    def set_config_schema(self, schema: Dict[str, Any]) -> None:
        """Set configuration schema for validation."""
        self.parameters["config_schema"] = schema
        self.parameters["validate_schema"] = True