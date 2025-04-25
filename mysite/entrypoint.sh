#!/bin/bash
set -e

# Function to wait for PostgreSQL
wait_for_postgres() {
  echo "Waiting for PostgreSQL..."
  if [ -z "$DATABASE_URL" ] || [[ "$DATABASE_URL" == sqlite* ]]; then
    echo "Not using PostgreSQL, skipping wait"
    return
  fi
  
  # Extract host and port from DATABASE_URL
  if [[ "$DATABASE_URL" =~ postgres://([^:]+):([^@]+)@([^:]+):([0-9]+)/([^?]+) ]]; then
    pg_host="${BASH_REMATCH[3]}"
    pg_port="${BASH_REMATCH[4]}"
    
    until pg_isready -h "$pg_host" -p "$pg_port" -U postgres; do
      echo "PostgreSQL is unavailable - sleeping"
      sleep 1
    done
    echo "PostgreSQL is up - continuing..."
  else
    echo "Unable to parse DATABASE_URL, skipping PostgreSQL check"
  fi
}

wait_for_postgres

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create necessary directories
echo "Ensuring static directories exist..."
mkdir -p /app/staticfiles /app/media

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

# Check S3 configuration if USE_S3 is enabled
if [ "$USE_S3" = "1" ]; then
  echo "Checking S3 configuration..."
  if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ] && [ -n "$AWS_STORAGE_BUCKET_NAME" ]; then
    echo "S3 environment variables detected, will use S3 for media storage"
    # You can add an S3 check command here if available
  else
    echo "WARNING: S3 is enabled but environment variables are missing. Using local storage as fallback."
  fi
fi

# Start gunicorn with production settings
echo "Starting Gunicorn..."
exec gunicorn mysite.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class gthread \
    --threads 3 \
    --worker-tmp-dir /dev/shm \
    --log-file=- \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    --timeout 120