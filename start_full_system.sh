#!/bin/bash

# Start Full AI Trading Interface System
echo "🚀 Starting AI Trading Interface System..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Export environment variables
export $(grep -v '^#' .env | xargs)

# Start Simple API Bridge in background
echo "🔗 Starting HaasOnline API Bridge..."
cd mcp_server
./../.venv/bin/python simple_api_bridge.py &
API_BRIDGE_PID=$!
cd ..

# Wait a moment for the bridge to start
sleep 3

# Start the frontend development server
echo "🌐 Starting Frontend Development Server..."
cd ai-trading-interface
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ System started successfully!"
echo "📊 Frontend: http://localhost:5173"
echo "🔗 API Bridge: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $API_BRIDGE_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait