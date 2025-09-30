"""
Data dumper-related exceptions
"""

from .base import NonRetryableError


class DataDumperError(NonRetryableError):
    """Base class for data dumper-related errors"""
    
    def __init__(self, message: str = "Data dumper operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="DATA_DUMPER_ERROR",
            recovery_suggestion="Check data dumper configuration and try again",
            **kwargs
        )


class DataDumperConfigurationError(DataDumperError):
    """Raised when data dumper configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid data dumper configuration '{config_field}': {value}",
            error_code="DATA_DUMPER_CONFIG_ERROR",
            context={"config_field": config_field, "value": str(value)},
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class DataDumperExportError(DataDumperError):
    """Raised when data export fails"""
    
    def __init__(self, export_type: str, **kwargs):
        super().__init__(
            message=f"Data export failed for type: {export_type}",
            error_code="DATA_DUMPER_EXPORT_ERROR",
            context={"export_type": export_type},
            recovery_suggestion="Check export parameters and try again",
            **kwargs
        )
        self.export_type = export_type


class DataDumperImportError(DataDumperError):
    """Raised when data import fails"""
    
    def __init__(self, import_type: str, **kwargs):
        super().__init__(
            message=f"Data import failed for type: {import_type}",
            error_code="DATA_DUMPER_IMPORT_ERROR",
            context={"import_type": import_type},
            recovery_suggestion="Check import file and try again",
            **kwargs
        )
        self.import_type = import_type



