#!/bin/bash

# Start MCP server using local venv and environment variables from .env file
source .venv/bin/activate && export $(grep -v '^#' .env | xargs) && cd mcp_server && python server.py