#!/bin/bash
# Fresh start script - clears all Python cache and starts server

echo "Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "Starting server with bytecode generation disabled..."
export PYTHONDONTWRITEBYTECODE=1
python main.py

