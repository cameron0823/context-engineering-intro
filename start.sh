#!/bin/sh
# Start script for Railway deployment

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "Starting server on port $PORT..."

# Run the application
exec uvicorn src.main:app --host 0.0.0.0 --port $PORT