FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DOCKER_CONTAINER=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for static and media files
RUN mkdir -p /app/static /app/media

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Copy project files
COPY --chown=appuser:appuser . .

# Create SQLite database directory with correct permissions
USER root
RUN mkdir -p /data/db && chown -R appuser:appuser /data/db
USER appuser

# Set execute permissions for entrypoint
RUN chmod +x /app/entrypoint.sh

# Expose port for gunicorn
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]