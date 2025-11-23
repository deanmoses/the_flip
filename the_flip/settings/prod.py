from .base import *  # noqa
import dj_database_url
import os
import sys

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Trust X-Forwarded-Proto header from hosting system's reverse proxy
# This is required when the proxy terminates SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Use Postgres database from DATABASE_URL environment variable
# Railway automatically provides this when you add a Postgres database
database_url = os.environ.get('DATABASE_URL', '')
if not database_url:
    print("ERROR: DATABASE_URL environment variable is not set.", file=sys.stderr)
    print("Please add a PostgreSQL database in Railway dashboard.", file=sys.stderr)
    sys.exit(1)

if not database_url.startswith('postgres'):
    print(f"ERROR: DATABASE_URL must be a PostgreSQL URL (got: {database_url[:20]}...)", file=sys.stderr)
    print("Please add a PostgreSQL database in Railway dashboard.", file=sys.stderr)
    sys.exit(1)

DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}
