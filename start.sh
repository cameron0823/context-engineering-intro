#!/bin/sh
# Start script for Railway deployment

# Railway provides PORT as an environment variable
# Ensure it's a valid integer
if [ -z "$PORT" ]; then
    PORT=8000
fi

# Validate PORT is a number
if ! echo "$PORT" | grep -qE '^[0-9]+$'; then
    echo "Error: PORT must be a number, got: $PORT"
    echo "Using default port 8000"
    PORT=8000
fi

# Validate PORT is in valid range
if [ "$PORT" -lt 0 ] || [ "$PORT" -gt 65535 ]; then
    echo "Error: PORT must be between 0 and 65535, got: $PORT"
    echo "Using default port 8000"
    PORT=8000
fi

echo "Starting server on port $PORT..."

# Run the application
exec uvicorn src.main:app --host 0.0.0.0 --port "$PORT"