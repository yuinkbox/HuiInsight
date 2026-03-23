#!/bin/bash
# ============================================================================
# AHDUNYI Terminal PRO - Backend Development Startup Script
# ============================================================================
# Starts the backend server in development mode
# ============================================================================

set -e

echo "🚀 Starting AHDUNYI Terminal PRO Backend (Development Mode)..."
echo "📊 Environment: DEVELOPMENT"
echo "=" * 60

# Set environment
export ENVIRONMENT=development

# Change to server directory
cd "$(dirname "$0")/../server"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check if dependencies are installed
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking Python dependencies..."
python -m pip install -r requirements.txt --quiet

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "=" * 60

python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload