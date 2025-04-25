#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# --- TEMPORARILY CREATE SUPERUSER ---
# Set credentials via environment variables in Render UI FIRST!
echo "Creating superuser (if DJANGO_SUPERUSER_USERNAME is set)..."
python manage.py createsuperuser --noinput || echo "Superuser already exists or DJANGO_SUPERUSER_USERNAME not set."
# The '|| echo ...' part prevents the build failing if the user already exists
# --- END TEMPORARY ---