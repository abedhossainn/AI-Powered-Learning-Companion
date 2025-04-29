#!/bin/bash

# This script serves as a wrapper around uvicorn to add CORS headers to all responses
# Usage: ./.cors.sh

# Environment variables
export PYTHONPATH=/webapps/ai-learning-companion/AI-Powered-Learning-Companion/backend

# Function to stop both uvicorn and cors-anywhere
cleanup() {
    echo "Stopping services..."
    kill $(pgrep -f "uvicorn app.main:app") 2>/dev/null || true
    echo "Cleanup complete"
}

# Set up trap to clean up on exit
trap cleanup EXIT INT TERM

# Start the backend with explicit permission for the Cloudflare domain
cd /webapps/ai-learning-companion/AI-Powered-Learning-Companion/backend
echo "Starting backend with enhanced CORS support..."
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Keep script running
wait
