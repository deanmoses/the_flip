#!/usr/bin/env bash
# Build script for deployment on Railway

# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create directories if they don't exist
mkdir -p media
mkdir -p static_collected

# Run tests
echo "Running tests..."
DJANGO_SETTINGS_MODULE=the_flip.settings.test python manage.py test
echo "✓ All tests passed"

# Collect static files
# Note: Can't run migrations here because Railway doesn't provide DATABASE_URL during build.
# Migrations will run at startup via railway.toml startCommand.
echo "Collecting static files..."
DJANGO_SETTINGS_MODULE=the_flip.settings.prod python manage.py collectstatic --no-input
echo "✓ Static files collected"
