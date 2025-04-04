#!/bin/bash

# Wait for database to be ready (if using external database)
# python manage.py wait_for_db

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
gunicorn mysite.wsgi:application --bind 0.0.0.0:8000