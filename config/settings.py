"""
Configuration settings for pyHaasAPI
"""

import os
from typing import Dict, Any

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8090))
API_EMAIL = os.getenv("API_EMAIL", "your_email@example.com")
API_PASSWORD = os.getenv("API_PASSWORD", "your_password")

# Authentication settings
AUTH_RETRY_ATTEMPTS = 3
AUTH_RETRY_DELAY = 10  # seconds

# Market Data settings
DEFAULT_EXCHANGES = ["BINANCE", "COINBASE", "KRAKEN"]
DEFAULT_TRADING_PAIRS = ["BTC/USDT", "ETH/BTC", "ETH/USDT"]

# Backtesting settings
DEFAULT_BACKTEST_HOURS = 24
DEFAULT_TIMEOUT_MINUTES = 60
DEFAULT_PAGE_LENGTH = 1000

# Parameter optimization settings
DEFAULT_PARAM_RANGE_START = 0.5
DEFAULT_PARAM_RANGE_END = 2.0
DEFAULT_PARAM_STEP = 0.1
MAX_PARAM_VALUES = 10

# Bot configuration
BOT_SCRIPTS = {
    "MadHatter": "MadHatter Bot",
    "Scalper": "Scalper Bot"
}

# Parameters to disable during optimization
DISABLED_PARAMETERS = [
    'stoploss', 'gainprofit', 'deviation', 'signalconsensus'
]

DISABLED_KEYWORDS = [
    'stop', 'gain', 'profit', 'deviation', 'consensus'
]

# Parameter type mappings
PARAM_TYPES = {
    0: "INTEGER",
    1: "DECIMAL", 
    2: "BOOLEAN",
    3: "STRING",
    4: "SELECTION"
}

# Status mappings
LAB_STATUS = {
    '0': 'CREATED',
    '1': 'QUEUED', 
    '2': 'RUNNING',
    '3': 'COMPLETED',
    '4': 'CANCELLED',
    '5': 'ERROR'
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File paths
DATA_DIR = "data"
LOGS_DIR = "logs"
RESULTS_DIR = "results"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, RESULTS_DIR]:
    os.makedirs(directory, exist_ok=True) 