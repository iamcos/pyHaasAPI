import sys
from pathlib import Path
# Add project root to path
sys.path.append(str(Path(__file__).parent))

from pyHaasAPI.core.logging import initialize_logging, get_logger
from pyHaasAPI.config.logging_config import LoggingConfig

def test():
    config = LoggingConfig(level="DEBUG", file_enabled=True, file_path="logs/test_pyhaas.log")
    initialize_logging(config)
    
    # Manually re-add with enqueue=False to be sure
    from loguru import logger
    import sys
    logger.remove()
    logger.add("logs/test_pyhaas.log", level="DEBUG", enqueue=False)
    logger.info("This is a test log message")
    logger.debug("This is a debug log message")
    logger.error("This is an error log message")
    
    # Check if file exists and has content
    log_file = Path("logs/test_pyhaas.log")
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"Log file created, size: {size} bytes")
    else:
        print("Log file NOT created")

if __name__ == "__main__":
    test()
