#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Change to the Django project directory
cd the_flip

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Populate sample games
python manage.py populate_sample_games

# Populate sample problem reports
python manage.py populate_sample_problem_reports
