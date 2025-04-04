#!/bin/bash
set -e

echo "Waiting for database directory..."
while [ ! -d "/data/db" ]; do
    sleep 1
done

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

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