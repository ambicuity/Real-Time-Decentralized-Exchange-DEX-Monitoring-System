#!/bin/bash

# DEX Monitoring System Startup Script

echo "🚀 Starting DEX Monitoring System..."
echo "=================================="

# Create necessary directories
mkdir -p logs data

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Start the monitoring system
echo "🎯 Starting monitoring system..."
echo "Dashboard will be available at: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop the system"
echo ""

python main.py