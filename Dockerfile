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
# Copy start script
COPY start.sh .

# Create necessary directories
RUN mkdir -p uploads logs

# Make start script executable
RUN chmod +x start.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Railway will set PORT env var
ENV PORT=8000

# Default command - use start script
CMD ["./start.sh"]