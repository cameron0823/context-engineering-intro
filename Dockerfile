FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-prod.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .
# Copy .env.example if no .env exists
COPY .env.example .env.example

# Create necessary directories
RUN mkdir -p uploads logs

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Railway will set PORT env var
ENV PORT=8000

# Default command - use PORT from environment
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT