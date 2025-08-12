#!/bin/bash
#
# This script starts the MCP server in the background.
# It automatically restarts when code changes are detected.
# Logs are written to logs/mcp_server.log and overwritten on each start.

LOG_FILE="/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/logs/mcp_server.log"

# Kill any existing server process
PGREP_OUTPUT=$(pgrep -f "uvicorn mcp_server.main:app")
if [ -n "$PGREP_OUTPUT" ]; then
    echo "Killing existing server process..."
    pkill -f "uvicorn mcp_server.main:app"
    sleep 2
fi

# Start the server in the background, redirecting output to the log file
echo "Starting MCP server..."
.venv/bin/python -m uvicorn mcp_server.server:main --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &

# Give the server a moment to start up
sleep 2

# Check if the process started successfully
if pgrep -f "uvicorn mcp_server.main:app" > /dev/null; then
    echo "Server started successfully. Logs are being written to $LOG_FILE"
else
    echo "Error: Server failed to start. Check the log file for details: $LOG_FILE"
fi
