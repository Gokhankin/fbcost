#!/bin/bash

# F&B Cost Dashboard - Startup Script
# Optimized for Ubuntu/Linux

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

echo "------------------------------------------------"
echo "Club Adakoy F&B Cost Dashboard - Starting Up"
echo "------------------------------------------------"

# 1. Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed. Please run: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Install Dependencies
echo "Checking and installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Check for ODBC Driver
if ! odbcinst -q -d -n "ODBC Driver 18 for SQL Server" &> /dev/null; then
    echo "WARNING: Microsoft ODBC Driver 18 for SQL Server not found."
    echo "Live database connection might fail. Please ensure the driver is installed."
fi

# 5. Start Dashboard
echo "Starting F&B Cost Dashboard on http://localhost:5005 ..."
python3 app.py
