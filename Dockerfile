# Multi-stage build for DEX Trades Extractor
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY *.py ./
COPY chains_config.py ./
COPY blockchain_interface.py ./
COPY known_tokens.py ./

# Copy shell scripts
COPY *.sh ./

# Make scripts executable
RUN chmod +x *.py *.sh

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

# Default command (can be overridden in Railway)
CMD ["python3", "--version"]

