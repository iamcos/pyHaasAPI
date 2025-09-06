#!/bin/bash

# Start Complete AI Trading Interface System with Real Data
echo "🚀 Starting AI Trading Interface System with REAL HaasOnline Data..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Export environment variables
export $(grep -v '^#' .env | xargs)

# Create logs directory
mkdir -p logs

# Start API Bridge with REAL HaasOnline data
echo "🔗 Starting API Bridge with REAL HaasOnline API..."
.venv/bin/python mcp_server/working_api_bridge.py > logs/api_bridge.log 2>&1 &
API_BRIDGE_PID=$!
echo $API_BRIDGE_PID > logs/api_bridge.pid

# Wait for API bridge to start
sleep 5

# Test API bridge connection
echo "🧪 Testing API Bridge connection..."
curl -s http://localhost:3001/api/health | head -1

# Start the frontend development server
echo "🌐 Starting Frontend Development Server..."
cd ai-trading-interface
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

echo "✅ System started successfully!"
echo "📊 Frontend: http://localhost:3000"
echo "🔗 API Bridge: http://localhost:3001"
echo "📋 API Bridge Logs: tail -f logs/api_bridge.log"
echo "📋 Frontend Logs: tail -f logs/frontend.log"
echo ""
echo "🎯 The system is now running with REAL HaasOnline data!"
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