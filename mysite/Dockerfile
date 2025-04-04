FROM python:3.11

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Create SQLite database directory
RUN mkdir -p /data/db

# Set permissions
RUN chmod +x /app/entrypoint.sh

# Expose port for gunicorn
EXPOSE 8000

# Use entrypoint script to start the application
ENTRYPOINT ["/app/entrypoint.sh"]