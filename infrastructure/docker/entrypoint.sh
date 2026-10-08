#!/bin/sh
set -e

echo "==> Amanus Learn AI: Checking environment..."

# In local / docker dev, wait for database if postgres host is specified
if [ -n "$POSTGRES_HOST" ]; then
    echo "==> Waiting for PostgreSQL on $POSTGRES_HOST:5432..."
    while ! nc -z "$POSTGRES_HOST" 5432; do
        sleep 0.5
    done
    echo "==> PostgreSQL is ready."
fi

# Run database migrations
echo "==> Running Django database migrations..."
python manage.py migrate --noinput || true

exec "$@"
