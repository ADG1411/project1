# Use Python 3.11 slim image for efficiency
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY train.py .

# Create directory for metrics output
RUN mkdir -p /tmp

# Create non-root user for security
RUN useradd -m -u 1000 mluser && chown -R mluser:mluser /app /tmp
USER mluser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_NAME=demo-model
ENV TRAINING_EPOCHS=10

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "train.py"]