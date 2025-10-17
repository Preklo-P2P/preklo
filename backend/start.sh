#!/bin/bash

# Preklo Backend Startup Script
# Run this script from the backend directory to start the server

echo "Starting Preklo Backend..."

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    echo "Error: This script must be run from the backend directory"
    echo "Please run: cd /path/to/Preklo/backend && ./start.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "Error: Virtual environment not found at ../venv"
    echo "Please run the setup script from the project root first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source ../venv/bin/activate

# Debug: Check if Aptos SDK is available
echo "Checking Aptos SDK availability..."
python -c "try:
    from aptos_sdk.account import Account
    print('Aptos SDK is available')
except ImportError as e:
    print('Aptos SDK not available:', e)"

# Load environment variables from .env file
if [ -f "../.env" ]; then
    echo "Loading environment variables from .env..."
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo "No .env file found, using default configuration"
fi

# Set PYTHONPATH to backend directory
export PYTHONPATH=/home/davey/Desktop/davey/hackathon/AptosSend/backend

echo "Starting server on http://localhost:8000..."
echo "API documentation will be available at http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server
python -m app.main
